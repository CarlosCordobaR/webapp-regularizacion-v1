"""Outbound WhatsApp API endpoints."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.adapters.factory import get_repository, get_whatsapp_client
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


class SendTextRequest(BaseModel):
    """Request body for outbound text message."""
    client_id: UUID
    text: str = Field(..., min_length=1, max_length=4096)


class SendTemplateRequest(BaseModel):
    """Request body for outbound template message."""
    client_id: UUID
    template_name: str = Field(..., min_length=1, max_length=128)
    language_code: str = Field(default="es", min_length=2, max_length=16)
    body_parameters: list[str] = Field(default_factory=list, max_length=20)


class SendTextResponse(BaseModel):
    """Response for outbound text message."""
    status: str
    client_id: UUID
    phone_number: str
    whatsapp_message_id: str
    conversation_id: UUID


class MessageStatusResponse(BaseModel):
    """Status details for an outbound message tracked in conversations."""
    message_id: str
    found: bool
    client_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    whatsapp_status: Optional[str] = None
    whatsapp_status_timestamp: Optional[str] = None
    status_history: list[dict] = Field(default_factory=list)


def _extract_message_id(provider_response: dict) -> Optional[str]:
    messages = (provider_response or {}).get("messages") if provider_response else None
    return messages[0].get("id") if messages and isinstance(messages, list) and messages[0] else None


def _persist_outbound_conversation(
    repository,
    client_id: UUID,
    message_id: str,
    content: str,
    source: str,
):
    return repository.create_conversation(
        {
            "client_id": str(client_id),
            "message_id": message_id,
            "direction": "outbound",
            "content": content,
            "message_type": "text",
            "metadata": {
                "source": source,
                "provider": "meta_whatsapp",
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "whatsapp_status": "sent",
            },
        }
    )


@router.post("/send-text", response_model=SendTextResponse)
async def send_text_message(request: SendTextRequest):
    """Send a WhatsApp text message to an existing client and persist it as outbound conversation."""
    repository = get_repository()
    whatsapp = get_whatsapp_client()

    client = repository.get_client_by_id(request.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    phone_number = (client.get("phone_number") or "").strip()
    if not phone_number:
        raise HTTPException(status_code=400, detail="Client has no phone number")

    try:
        provider_response = await whatsapp.send_text_message(phone_number, request.text.strip())
    except Exception as e:
        logger.error(f"Error sending outbound WhatsApp message for client {request.client_id}: {e}")
        raise HTTPException(status_code=502, detail="Failed to send WhatsApp message")

    message_id = _extract_message_id(provider_response)
    if not message_id:
        raise HTTPException(status_code=502, detail="WhatsApp provider did not return a message ID")

    try:
        conversation = _persist_outbound_conversation(
            repository=repository,
            client_id=request.client_id,
            message_id=message_id,
            content=request.text.strip(),
            source="api_whatsapp_send_text",
        )
    except Exception as e:
        logger.error(f"Error storing outbound conversation {message_id}: {e}")
        raise HTTPException(status_code=500, detail="Message sent but failed to persist conversation")

    return SendTextResponse(
        status="sent",
        client_id=request.client_id,
        phone_number=phone_number,
        whatsapp_message_id=message_id,
        conversation_id=UUID(conversation["id"]),
    )


@router.post("/send-template", response_model=SendTextResponse)
async def send_template_message(request: SendTemplateRequest):
    """Send an approved WhatsApp template to an existing client and persist it as outbound conversation."""
    repository = get_repository()
    whatsapp = get_whatsapp_client()

    client = repository.get_client_by_id(request.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    phone_number = (client.get("phone_number") or "").strip()
    if not phone_number:
        raise HTTPException(status_code=400, detail="Client has no phone number")

    try:
        provider_response = await whatsapp.send_template_message(
            phone_number,
            request.template_name.strip(),
            request.language_code.strip(),
            request.body_parameters,
        )
    except Exception as e:
        logger.error(f"Error sending outbound template for client {request.client_id}: {e}")
        raise HTTPException(status_code=502, detail="Failed to send WhatsApp template")

    message_id = _extract_message_id(provider_response)
    if not message_id:
        raise HTTPException(status_code=502, detail="WhatsApp provider did not return a message ID")

    content = f"[template:{request.template_name.strip()}:{request.language_code.strip()}]"

    try:
        conversation = _persist_outbound_conversation(
            repository=repository,
            client_id=request.client_id,
            message_id=message_id,
            content=content,
            source="api_whatsapp_send_template",
        )
    except Exception as e:
        logger.error(f"Error storing outbound template conversation {message_id}: {e}")
        raise HTTPException(status_code=500, detail="Template sent but failed to persist conversation")

    return SendTextResponse(
        status="sent",
        client_id=request.client_id,
        phone_number=phone_number,
        whatsapp_message_id=message_id,
        conversation_id=UUID(conversation["id"]),
    )


@router.get("/message-status/{message_id}", response_model=MessageStatusResponse)
async def get_message_status(message_id: str):
    """Get current WhatsApp delivery/read status for an outbound message_id."""
    repository = get_repository()
    conversation = repository.get_conversation_by_message_id(message_id)
    if not conversation:
        return MessageStatusResponse(message_id=message_id, found=False)

    metadata = conversation.get("metadata", {}) or {}
    return MessageStatusResponse(
        message_id=message_id,
        found=True,
        client_id=UUID(conversation["client_id"]) if conversation.get("client_id") else None,
        conversation_id=UUID(conversation["id"]) if conversation.get("id") else None,
        whatsapp_status=metadata.get("whatsapp_status"),
        whatsapp_status_timestamp=metadata.get("whatsapp_status_timestamp"),
        status_history=metadata.get("status_history", []),
    )
