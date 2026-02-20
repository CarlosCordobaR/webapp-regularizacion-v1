"""
Prisma-based client endpoints (parallel implementation)
These endpoints demonstrate Prisma usage alongside existing Supabase endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.logging import get_logger
from app.db.prisma_client import get_prisma
from app.models.dto import ClientResponse, ClientListResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/prisma/clients", tags=["prisma", "clients"])


@router.get("", response_model=ClientListResponse)
async def list_clients_prisma(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status"),
    profile_type: Optional[str] = Query(None, description="Filter by profile type")
):
    """
    List clients using Prisma ORM with type-safe queries.
    
    Features:
    - Pagination
    - Status filtering
    - Profile type filtering
    - Includes document count
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        status: Filter by client status (active, inactive, archived)
        profile_type: Filter by profile type
        
    Returns:
        Paginated list of clients with document counts
    """
    try:
        db = await get_prisma()
        
        # Build filter conditions
        where = {}
        if status:
            where['status'] = status
        if profile_type:
            where['profileType'] = profile_type
        
        # Get total count
        total = await db.client.count(where=where)
        
        # Get paginated clients with documents included
        clients = await db.client.find_many(
            where=where,
            skip=(page - 1) * page_size,
            take=page_size,
            include={
                'documents': True,
                'conversations': {'take': 1, 'order_by': {'createdAt': 'desc'}}
            },
            order={'createdAt': 'desc'}
        )
        
        # Transform to response format
        client_responses = []
        for client in clients:
            client_data = {
                'id': client.id,
                'phone_number': client.phoneNumber,
                'name': client.name,
                'passport_or_nie': client.passportOrNie,
                'profile_type': client.profileType,
                'status': client.status,
                'email': client.email,
                'notes': client.notes,
                'metadata': client.metadata or {},
                'created_at': client.createdAt.isoformat(),
                'updated_at': client.updatedAt.isoformat(),
                'document_count': len(client.documents),
                'has_recent_conversation': len(client.conversations) > 0
            }
            client_responses.append(ClientResponse(**client_data))
        
        return ClientListResponse(
            data=client_responses,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error listing clients with Prisma: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch clients: {str(e)}"
        )


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client_prisma(client_id: str):
    """
    Get client details by ID using Prisma.
    
    Includes:
    - All client fields
    - Document count
    - Recent conversation indicator
    
    Args:
        client_id: Client UUID
        
    Returns:
        Client details with related data counts
    """
    try:
        db = await get_prisma()
        
        client = await db.client.find_unique(
            where={'id': client_id},
            include={
                'documents': True,
                'conversations': {'take': 1, 'order_by': {'createdAt': 'desc'}}
            }
        )
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        return ClientResponse(
            id=client.id,
            phone_number=client.phoneNumber,
            name=client.name,
            passport_or_nie=client.passportOrNie,
            profile_type=client.profileType,
            status=client.status,
            email=client.email,
            notes=client.notes,
            metadata=client.metadata or {},
            created_at=client.createdAt.isoformat(),
            updated_at=client.updatedAt.isoformat(),
            document_count=len(client.documents),
            has_recent_conversation=len(client.conversations) > 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client with Prisma: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch client: {str(e)}"
        )


@router.get("/stats/summary")
async def get_stats_summary():
    """
    Get database statistics using Prisma aggregations.
    
    Returns:
        Summary statistics for clients, documents, and conversations
    """
    try:
        db = await get_prisma()
        
        # Parallel queries for better performance
        client_count = await db.client.count()
        document_count = await db.document.count()
        conversation_count = await db.conversation.count()
        
        # Count by status
        active_clients = await db.client.count(where={'status': 'active'})
        inactive_clients = await db.client.count(where={'status': 'inactive'})
        
        # Count by document type
        tasa_docs = await db.document.count(where={'documentType': 'TASA'})
        nie_docs = await db.document.count(where={'documentType': 'PASSPORT_NIE'})
        
        return {
            'clients': {
                'total': client_count,
                'active': active_clients,
                'inactive': inactive_clients
            },
            'documents': {
                'total': document_count,
                'by_type': {
                    'TASA': tasa_docs,
                    'PASSPORT_NIE': nie_docs
                }
            },
            'conversations': {
                'total': conversation_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting stats with Prisma: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch statistics: {str(e)}"
        )


@router.get("/search/by-phone")
async def search_by_phone(phone: str = Query(..., description="Phone number to search")):
    """
    Search client by phone number using Prisma.
    
    Args:
        phone: Phone number (partial match supported)
        
    Returns:
        Matching clients
    """
    try:
        db = await get_prisma()
        
        clients = await db.client.find_many(
            where={
                'phoneNumber': {'contains': phone}
            },
            include={'documents': True},
            take=10
        )
        
        return {
            'count': len(clients),
            'clients': [
                {
                    'id': c.id,
                    'phone_number': c.phoneNumber,
                    'name': c.name,
                    'profile_type': c.profileType,
                    'document_count': len(c.documents)
                }
                for c in clients
            ]
        }
        
    except Exception as e:
        logger.error(f"Error searching clients with Prisma: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
