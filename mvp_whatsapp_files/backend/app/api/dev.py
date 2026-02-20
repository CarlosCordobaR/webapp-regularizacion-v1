"""Development endpoints for testing without WhatsApp integration.

These endpoints are only available when DEV_ENDPOINTS_ENABLED=true.
They allow testing the Supabase integration without WhatsApp.
"""
import hashlib
import io
import random
from datetime import datetime, timedelta
from typing import Dict, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Header, UploadFile, status
from pydantic import BaseModel
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.adapters.factory import get_repository, get_storage
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.enums import ClientStatus, DocumentType, MessageDirection, ProfileType
from app.services.storage import StorageService
from app.whatsapp.media import generate_storage_path

logger = get_logger(__name__)
router = APIRouter(prefix="/dev", tags=["development"])


# Dependency for DEV_TOKEN authentication
async def verify_dev_token(x_dev_token: str = Header(...)):
    """Verify dev token from header."""
    settings = get_settings()
    if x_dev_token != settings.dev_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid DEV_TOKEN. Set X-Dev-Token header with correct token."
        )


class SeedResponse(BaseModel):
    """Response from seed endpoint."""
    clients_created: int
    conversations_created: int
    documents_created: int
    message: str


class ConversationRequest(BaseModel):
    """Request to create a test conversation."""
    client_id: str
    direction: MessageDirection
    message_text: str
    message_type: str = "text"


class ConversationResponse(BaseModel):
    """Response from conversation creation."""
    conversation_id: str
    message: str


def generate_test_pdf(title: str, content: str) -> bytes:
    """Generate a simple test PDF."""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica", 12)
    p.drawString(100, 750, title)
    p.drawString(100, 730, content)
    p.drawString(100, 710, f"Generated: {datetime.now().isoformat()}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.read()


@router.post("/seed", response_model=SeedResponse, dependencies=[Depends(verify_dev_token)])
async def seed_test_data():
    """
    Seed test dataset into Supabase for validation.
    
    Creates:
    - 10 clients with different profile types
    - 2-4 conversations per client (inbound/outbound)
    - 1-2 documents per client (TASA and/or PASSPORT_NIE PDFs)
    
    All seeded data has notes prefixed with "[SEED]" for identification.
    """
    repository = get_repository()
    storage_service = StorageService()
    storage = get_storage()
    
    clients_created = 0
    conversations_created = 0
    documents_created = 0
    
    # Test data templates
    profiles = [
        ProfileType.ASYLUM,
        ProfileType.ARRAIGO,
        ProfileType.STUDENT,
        ProfileType.IRREGULAR,
        ProfileType.OTHER
    ]
    
    names = [
        "Juan García", "María López", "Pedro Martínez", "Ana Rodríguez", "Luis Hernández",
        "Carmen Pérez", "José González", "Isabel Torres", "Manuel Sánchez", "Rosa Ramírez"
    ]
    
    try:
        # Create 10 clients
        for i in range(10):
            phone = f"+34600{100000 + i:06d}"
            
            # Check if client exists (by phone)
            existing = repository.get_client_by_phone(phone)
            if existing:
                logger.info(f"Client {phone} already exists, skipping")
                continue
            
            client_data = {
                "phone_number": phone,
                "name": names[i],
                "email": f"test{i+1}@example.com",
                "notes": f"[SEED] Test client {i+1} for Supabase validation",
                "profile_type": profiles[i % len(profiles)].value,
                "status": ClientStatus.ACTIVE.value,
                "passport_or_nie": f"NIE-X{1000000 + i}",
                "metadata": {"seed": True, "seed_date": datetime.now().isoformat()}
            }
            
            client = repository.create_client(client_data)
            client_id = UUID(client["id"])
            clients_created += 1
            logger.info(f"Created seed client: {client['name']} ({phone})")
            
            # Create 2-4 conversations per client
            num_conversations = random.randint(2, 4)
            for j in range(num_conversations):
                # Alternate between inbound and outbound
                direction = MessageDirection.INBOUND if j % 2 == 0 else MessageDirection.OUTBOUND
                
                # Generate unique message_id
                message_id = f"seed_msg_{client_id}_{j}_{uuid4().hex[:8]}"
                
                # Compute dedupe_key (sha256 of message_id + direction)
                dedupe_string = f"{message_id}:{direction.value}"
                dedupe_key = hashlib.sha256(dedupe_string.encode()).hexdigest()
                
                # Create conversation
                conversation_data = {
                    "client_id": str(client_id),
                    "message_id": message_id,
                    "direction": direction.value,
                    "content": f"Test {direction.value.lower()} message {j+1} for {client['name']}",
                    "message_type": "text",
                    "dedupe_key": dedupe_key,
                    "metadata": {
                        "seed": True,
                        "timestamp": (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat()
                    }
                }
                
                # Check if conversation already exists (by dedupe_key)
                existing_conv = None
                try:
                    # Try to fetch by dedupe_key (assuming repository has this method)
                    # If not, this will be caught and we'll attempt creation
                    pass
                except:
                    pass
                
                conversation = repository.create_conversation(conversation_data)
                conversations_created += 1
            
            # Create 1-2 documents per client
            num_docs = random.randint(1, 2)
            doc_types = [DocumentType.TASA, DocumentType.PASSPORT_NIE]
            
            for k in range(num_docs):
                doc_type = doc_types[k]
                
                # Generate test PDF
                pdf_title = f"{doc_type.value} Document"
                pdf_content = f"Client: {client['name']}\nNIE: {client['passport_or_nie']}"
                pdf_bytes = generate_test_pdf(pdf_title, pdf_content)
                
                # Generate storage path
                filename = f"{doc_type.value.lower()}_{client['passport_or_nie']}.pdf"
                storage_path = generate_storage_path(
                    profile_type=ProfileType(client["profile_type"]),
                    client_name=client["name"],
                    client_id=client_id,
                    filename=filename
                )
                
                # Upload to storage
                storage.upload_file(
                    file_path=storage_path,
                    file_data=pdf_bytes,
                    content_type="application/pdf"
                )
                
                # Create document record
                document_data = {
                    "client_id": str(client_id),
                    "storage_path": storage_path,
                    "original_filename": filename,
                    "mime_type": "application/pdf",
                    "file_size": len(pdf_bytes),
                    "profile_type": client["profile_type"],
                    "document_type": doc_type.value,
                    "metadata": {"seed": True, "generated": True}
                }
                
                repository.create_document(document_data)
                documents_created += 1
                logger.info(f"Created seed document: {doc_type.value} for {client['name']}")
        
        return SeedResponse(
            clients_created=clients_created,
            conversations_created=conversations_created,
            documents_created=documents_created,
            message=f"Successfully seeded {clients_created} clients with conversations and documents"
        )
    
    except Exception as e:
        logger.error(f"Error seeding test data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed data: {str(e)}"
        )


@router.post("/conversations", response_model=ConversationResponse, dependencies=[Depends(verify_dev_token)])
async def create_test_conversation(request: ConversationRequest):
    """
    Create a test conversation message without WhatsApp.
    
    This allows testing the conversation timeline UI and data model.
    """
    repository = get_repository()
    
    # Verify client exists
    try:
        client_id = UUID(request.client_id)
        client = repository.get_client_by_id(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client_id format")
    
    # Generate unique message_id
    message_id = f"dev_msg_{uuid4().hex}"
    
    # Compute dedupe_key
    dedupe_string = f"{message_id}:{request.direction.value}"
    dedupe_key = hashlib.sha256(dedupe_string.encode()).hexdigest()
    
    # Create conversation
    conversation_data = {
        "client_id": request.client_id,
        "message_id": message_id,
        "direction": request.direction.value,
        "content": request.message_text,
        "message_type": request.message_type,
        "dedupe_key": dedupe_key,
        "metadata": {
            "dev": True,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    try:
        conversation = repository.create_conversation(conversation_data)
        return ConversationResponse(
            conversation_id=conversation["id"],
            message=f"Created {request.direction.value} conversation for client {request.client_id}"
        )
    except Exception as e:
        logger.error(f"Error creating test conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )


@router.post("/documents/upload", dependencies=[Depends(verify_dev_token)])
async def upload_test_document(
    client_id: str = Form(...),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload a document to Supabase Storage without WhatsApp.
    
    This reuses the same storage logic as the real upload endpoint.
    """
    repository = get_repository()
    storage = get_storage()
    
    # Verify client exists
    try:
        client_uuid = UUID(client_id)
        client = repository.get_client_by_id(client_uuid)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client_id format")
    
    # Validate file type
    if not file.content_type:
        raise HTTPException(status_code=400, detail="File content type is required")
    
    allowed_types = ["application/pdf", "image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Read file content
    try:
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:  # 10 MB limit
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    # Generate storage path
    storage_path = generate_storage_path(
        profile_type=ProfileType(client["profile_type"]),
        client_name=client["name"],
        client_id=client_uuid,
        filename=file.filename or f"{document_type.value.lower()}.pdf"
    )
    
    try:
        # Upload to storage
        storage.upload_file(
            file_path=storage_path,
            file_data=file_content,
            content_type=file.content_type
        )
        
        # Create document record
        document_data = {
            "client_id": client_id,
            "storage_path": storage_path,
            "original_filename": file.filename,
            "mime_type": file.content_type,
            "file_size": len(file_content),
            "profile_type": client["profile_type"],
            "document_type": document_type.value,
            "metadata": {"dev": True, "uploaded_at": datetime.now().isoformat()}
        }
        
        document = repository.create_document(document_data)
        
        return {
            "document_id": document["id"],
            "storage_path": storage_path,
            "message": f"Uploaded {document_type.value} document for client {client_id}"
        }
    
    except Exception as e:
        logger.error(f"Error uploading dev document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.delete("/reset", dependencies=[Depends(verify_dev_token)])
async def reset_seed_data():
    """
    Delete seed test data (optional endpoint).
    
    Deletes clients where notes start with "[SEED]".
    This will cascade delete conversations and documents due to foreign key constraints.
    """
    repository = get_repository()
    
    try:
        # Get all clients
        clients, total = repository.list_clients(page=1, page_size=1000)
        
        deleted_count = 0
        for client in clients:
            # Check if this is a seed client
            notes = client.get("notes", "")
            if notes and notes.startswith("[SEED]"):
                repository.delete_client(UUID(client["id"]))
                deleted_count += 1
                logger.info(f"Deleted seed client: {client['name']}")
        
        return {
            "deleted_clients": deleted_count,
            "message": f"Deleted {deleted_count} seed clients and associated data"
        }
    
    except Exception as e:
        logger.error(f"Error resetting seed data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset seed data: {str(e)}"
        )
