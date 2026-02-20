"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.adapters.factory import get_repository, get_storage
from app.adapters.mock.seed import seed_mock_data, get_seed_summary
from app.adapters.mock.mock_repository import MockRepository
from app.adapters.mock.mock_storage import MockStorage
from app.api import clients, conversations, documents, health, prisma_clients, whatsapp
from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.db.prisma_client import connect_prisma, disconnect_prisma
from app.models.dto import WhatsAppWebhook
from app.whatsapp.verify import verify_webhook, verify_webhook_signature
from app.whatsapp.webhook import WebhookHandler

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    setup_logging()
    settings = get_settings()
    
    logger.info(f"Starting application in {settings.app_mode} mode")
    logger.info(f"DB mode: {settings.db_mode}, Storage mode: {settings.storage_mode}")
    
    # Connect Prisma ORM
    try:
        await connect_prisma()
    except Exception as e:
        logger.warning(f"Prisma connection failed (non-critical): {e}")
    
    # Initialize adapters
    repository = get_repository()
    storage = get_storage()
    
    # Seed mock data if configured
    if settings.app_mode == "mock" and settings.mock_seed_on_start:
        if isinstance(repository, MockRepository) and isinstance(storage, MockStorage):
            logger.info("Seeding mock data...")
            seed_mock_data(repository, storage)
            summary = get_seed_summary(repository)
            logger.info(f"Mock data ready: {summary['clients']} clients, "
                       f"{summary['conversations']} conversations, "
                       f"{summary['documents']} documents")
    
    yield
    
    # Shutdown
    await disconnect_prisma()
    
    if isinstance(repository, MockRepository):
        repository.close()


app = FastAPI(
    title="WhatsApp Business Webhook API",
    description="MVP for ingesting WhatsApp Business Cloud API webhooks",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(clients.router)
app.include_router(conversations.router)
app.include_router(documents.router)
app.include_router(prisma_clients.router)  # Prisma-based endpoints
app.include_router(whatsapp.router)

# Include dev router if enabled (for Supabase validation without WhatsApp)
settings = get_settings()
if settings.dev_endpoints_enabled:
    from app.api import dev
    app.include_router(dev.router)
    logger.info("Dev endpoints enabled at /dev/*")


# WhatsApp webhook endpoints
@app.get("/webhook")
async def webhook_verify(
    hub_mode: str,
    hub_verify_token: str,
    hub_challenge: str
):
    """WhatsApp webhook verification endpoint."""
    return verify_webhook(
        mode=hub_mode,
        token=hub_verify_token,
        challenge=hub_challenge
    )


@app.post("/webhook")
async def webhook_handler(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(default=None),
):
    """WhatsApp webhook message handler."""
    raw_payload = await request.body()
    verify_webhook_signature(raw_payload, x_hub_signature_256)

    try:
        webhook = WhatsAppWebhook.model_validate_json(raw_payload)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    handler = WebhookHandler()
    result = await handler.process_webhook(webhook)
    return result


@app.get("/mock-storage/{path:path}")
async def mock_storage_download(path: str):
    """
    Download files from mock storage.
    Only available in mock mode.
    """
    settings = get_settings()
    
    if settings.storage_mode != "local":
        return Response(content="Not available in current storage mode", status_code=404)
    
    storage = get_storage()
    if not isinstance(storage, MockStorage):
        return Response(content="Not available", status_code=404)
    
    file_content = storage.read_file(path)
    if file_content is None:
        return Response(content="File not found", status_code=404)
    
    # Determine content type
    content_type = "application/pdf" if path.endswith('.pdf') else "application/octet-stream"
    filename = Path(path).name
    
    return Response(
        content=file_content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


# Mock auth endpoints for development
@app.get("/mock-auth/users")
async def mock_auth_users():
    """Get list of mock users for development login."""
    settings = get_settings()
    
    if settings.app_mode != "mock":
        return Response(content="Not available in current mode", status_code=404)
    
    return {
        "users": [
            {"email": "admin@local.test", "password": "Admin123!", "role": "admin"},
            {"email": "ops1@local.test", "password": "Ops123!", "role": "operator"},
            {"email": "ops2@local.test", "password": "Ops123!", "role": "operator"},
            {"email": "reviewer@local.test", "password": "Review123!", "role": "reviewer"},
            {"email": "readonly@local.test", "password": "Read123!", "role": "readonly"},
        ]
    }


@app.post("/mock-auth/login")
async def mock_auth_login(credentials: dict):
    """Mock authentication endpoint for development."""
    settings = get_settings()
    
    if settings.app_mode != "mock":
        return Response(content="Not available in current mode", status_code=404)
    
    email = credentials.get("email")
    password = credentials.get("password")
    
    # Simple validation
    valid_users = {
        "admin@local.test": "Admin123!",
        "ops1@local.test": "Ops123!",
        "ops2@local.test": "Ops123!",
        "reviewer@local.test": "Review123!",
        "readonly@local.test": "Read123!",
    }
    
    if email in valid_users and valid_users[email] == password:
        return {
            "token": f"mock_jwt_{email}",
            "user": {"email": email}
        }
    
    return Response(content="Invalid credentials", status_code=401)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
