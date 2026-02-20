"""Conversation management endpoints."""
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query

from app.adapters.factory import get_repository
from app.core.logging import get_logger
from app.models.dto import ConversationListResponse, ConversationResponse

logger = get_logger(__name__)
router = APIRouter(tags=["conversations"])


@router.get("/clients/{client_id}/conversations", response_model=ConversationListResponse)
async def list_client_conversations(
    client_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    List conversations for a specific client.
    
    Args:
        client_id: Client UUID
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        Paginated list of conversations
    """
    repository = get_repository()
    
    # Verify client exists
    client = repository.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    try:
        conversations, total = repository.get_conversations_by_client(
            client_id=client_id,
            page=page,
            page_size=page_size
        )
        
        return ConversationListResponse(
            data=[ConversationResponse(**conv) for conv in conversations],
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error listing conversations for client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversations")
