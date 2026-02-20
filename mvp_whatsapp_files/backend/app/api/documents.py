"""Document management endpoints."""
from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.adapters.factory import get_repository, get_storage
from app.core.logging import get_logger
from app.models.dto import DocumentListResponse, DocumentResponse, SignedUrlResponse
from app.models.enums import DocumentType

logger = get_logger(__name__)
router = APIRouter(tags=["documents"])


class UpdateDocumentRequest(BaseModel):
    """Request model for updating document."""
    document_type: Optional[DocumentType] = None


class ReviewDocumentRequest(BaseModel):
    """Request model for document review action."""
    action: Literal["accepted", "rejected"]
    note: Optional[str] = None


@router.get("/clients/{client_id}/documents", response_model=DocumentListResponse)
async def list_client_documents(
    client_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    List documents for a specific client.
    
    Args:
        client_id: Client UUID
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        Paginated list of documents
    """
    repository = get_repository()
    storage = get_storage()
    
    # Verify client exists
    client = repository.get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    try:
        documents, total = repository.get_documents_by_client(
            client_id=client_id,
            page=page,
            page_size=page_size
        )
        
        # Add signed URLs to documents (works for both public and private buckets)
        for doc in documents:
            try:
                doc["public_url"] = storage.get_file_url(doc["storage_path"], signed=True, expires_in=3600)
            except Exception as url_error:
                logger.warning(f"Failed to generate URL for {doc['storage_path']}: {url_error}")
                doc["public_url"] = None
        
        return DocumentListResponse(
            data=[DocumentResponse(**doc) for doc in documents],
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error listing documents for client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch documents")


@router.get("/documents/{document_id}/signed-url", response_model=SignedUrlResponse)
async def get_document_signed_url(
    document_id: UUID,
    expires_in: int = Query(3600, ge=60, le=86400)
):
    """
    Get signed URL for a document (for private bucket access).
    
    Note: For MVP with public bucket, this returns public URL.
    For private bucket, this would return time-limited signed URL.
    
    Args:
        document_id: Document UUID
        expires_in: URL expiration time in seconds
        
    Returns:
        Signed URL and expiration info
    """
    repository = get_repository()
    storage = get_storage()
    
    # Get document
    document = repository.get_document_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Use signed URL for security (works for both public and private buckets)
        url = storage.get_file_url(
            document["storage_path"],
            signed=True,
            expires_in=expires_in
        )
        
        return SignedUrlResponse(
            url=url,
            expires_in=expires_in
        )
    except Exception as e:
        logger.error(f"Error generating URL for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate document URL")


@router.patch("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(document_id: UUID, request: UpdateDocumentRequest):
    """
    Update document properties (mainly document_type).
    
    Args:
        document_id: Document UUID
        request: Update request with fields to modify
        
    Returns:
        Updated document
    """
    repository = get_repository()
    
    # Get document
    document = repository.get_document_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get client to check for unique constraint
    client_id = document['client_id']
    
    try:
        # Check if updating document_type would violate unique constraint
        if request.document_type:
            existing_docs, _ = repository.get_documents_by_client(
                client_id=UUID(client_id),
                page=1,
                page_size=100
            )
            
            # Check if another document already has this type
            for doc in existing_docs:
                if doc['id'] != str(document_id) and doc.get('document_type') == request.document_type.value:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Client already has a document with type {request.document_type.value}"
                    )
        
        # Update document in database
        from app.db.supabase import get_supabase_client
        supabase_client = get_supabase_client()
        
        update_data = {}
        if request.document_type is not None:
            update_data['document_type'] = request.document_type.value
        
        result = supabase_client.client.table('documents').update(update_data).eq('id', str(document_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update document")
        
        updated_doc = result.data[0]
        logger.info(f"Updated document {document_id}: document_type={request.document_type}")
        
        return DocumentResponse(**updated_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")


@router.post("/documents/{document_id}/review", response_model=DocumentResponse)
async def review_document(document_id: UUID, request: ReviewDocumentRequest):
    """
    Review a document by accepting or rejecting it.

    Rejecting requires a non-empty note.
    """
    repository = get_repository()

    document = repository.get_document_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if request.action == "rejected" and not (request.note or "").strip():
        raise HTTPException(
            status_code=400,
            detail="Rejection note is required when action is 'rejected'",
        )

    try:
        metadata = document.get("metadata", {}) or {}
        metadata["review_status"] = request.action
        metadata["reviewed_at"] = datetime.now(timezone.utc).isoformat()
        metadata["review_note"] = request.note.strip() if request.action == "rejected" else None

        updated = repository.update_document(document_id, {"metadata": metadata})

        try:
            repository.create_audit_event(
                {
                    "client_id": updated["client_id"],
                    "event_type": "DOC_ACCEPTED" if request.action == "accepted" else "DOC_REJECTED",
                    "actor": "staff",
                    "details": {
                        "document_id": str(document_id),
                        "action": request.action,
                        "note": metadata.get("review_note"),
                        "document_type": updated.get("document_type"),
                    },
                }
            )
        except Exception as audit_error:
            logger.warning(f"Audit event not persisted for document review {document_id}: {audit_error}")

        return DocumentResponse(**updated)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to review document: {str(e)}")
