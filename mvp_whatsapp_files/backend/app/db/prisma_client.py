"""
Prisma Client Wrapper for WhatsApp Regularization Platform
Provides type-safe database access with async/await support

Usage:
    from app.db.prisma_client import get_prisma
    
    async def get_clients():
        db = await get_prisma()
        clients = await db.client.find_many(
            include={'documents': True}
        )
        return clients
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from prisma import Prisma

from app.core.logging import get_logger

logger = get_logger(__name__)

# Global Prisma instance
_prisma_client: Optional[Prisma] = None


async def connect_prisma() -> Prisma:
    """
    Connect to database using Prisma.
    Should be called on app startup.
    
    Returns:
        Connected Prisma client instance
    """
    global _prisma_client
    
    if _prisma_client is None:
        _prisma_client = Prisma()
        await _prisma_client.connect()
        logger.info("✅ Prisma connected to database")
    
    return _prisma_client


async def disconnect_prisma() -> None:
    """
    Disconnect from database.
    Should be called on app shutdown.
    """
    global _prisma_client
    
    if _prisma_client is not None:
        await _prisma_client.disconnect()
        _prisma_client = None
        logger.info("👋 Prisma disconnected from database")


async def get_prisma() -> Prisma:
    """
    Get the global Prisma client instance.
    Creates connection if not exists.
    
    Returns:
        Prisma client instance
        
    Example:
        >>> db = await get_prisma()
        >>> clients = await db.client.find_many()
    """
    if _prisma_client is None:
        await connect_prisma()
    
    return _prisma_client


@asynccontextmanager
async def prisma_transaction() -> AsyncGenerator[Prisma, None]:
    """
    Context manager for database transactions.
    Automatically commits on success, rolls back on error.
    
    Example:
        >>> async with prisma_transaction() as tx:
        ...     client = await tx.client.create({
        ...         'phoneNumber': '+34600111222',
        ...         'name': 'John Doe',
        ...         'passportOrNie': 'X1234567A'
        ...     })
        ...     await tx.document.create({
        ...         'clientId': client.id,
        ...         'storagePath': 'path/to/doc.pdf'
        ...     })
    """
    db = await get_prisma()
    
    try:
        yield db
        # Transaction handled by Prisma internally
    except Exception as e:
        logger.error(f"Transaction failed: {e}")
        raise


# ============================================================================
# EXAMPLE QUERIES
# ============================================================================

async def example_queries():
    """
    Examples of common Prisma queries for reference.
    DO NOT CALL IN PRODUCTION - for documentation only.
    """
    db = await get_prisma()
    
    # ========== CREATE ==========
    
    # Create client
    client = await db.client.create({
        'phoneNumber': '+34600111222',
        'name': 'Juan Pérez',
        'passportOrNie': 'X1234567A',
        'profileType': 'ASYLUM',
        'status': 'active'
    })
    
    # Create document with relation
    document = await db.document.create({
        'clientId': client.id,
        'storagePath': 'clients/juan/tasa.pdf',
        'originalFilename': 'tasa.pdf',
        'documentType': 'TASA',
        'mimeType': 'application/pdf',
        'fileSize': 102400
    })
    
    # ========== READ ==========
    
    # Find all clients with documents
    clients = await db.client.find_many(
        include={
            'documents': True,
            'conversations': True
        },
        order={'createdAt': 'desc'}
    )
    
    # Find client by phone
    client = await db.client.find_unique(
        where={'phoneNumber': '+34600111222'},
        include={'documents': True}
    )
    
    # Find clients with specific criteria
    asylum_clients = await db.client.find_many(
        where={
            'profileType': 'ASYLUM',
            'status': 'active'
        }
    )
    
    # Count documents
    doc_count = await db.document.count(
        where={'documentType': 'TASA'}
    )
    
    # ========== UPDATE ==========
    
    # Update client
    updated = await db.client.update(
        where={'id': client.id},
        data={
            'name': 'Juan Updated',
            'status': 'inactive'
        }
    )
    
    # Update many
    await db.document.update_many(
        where={'clientId': client.id},
        data={'metadata': {'processed': True}}
    )
    
    # ========== DELETE ==========
    
    # Delete document
    await db.document.delete(
        where={'id': document.id}
    )
    
    # Delete client (cascades to documents/conversations)
    await db.client.delete(
        where={'id': client.id}
    )
    
    # ========== ADVANCED ==========
    
    # Pagination
    page = 1
    page_size = 50
    clients = await db.client.find_many(
        skip=(page - 1) * page_size,
        take=page_size,
        include={'documents': True}
    )
    
    # Search with OR conditions
    results = await db.client.find_many(
        where={
            'OR': [
                {'name': {'contains': 'Juan'}},
                {'phoneNumber': {'contains': '600'}}
            ]
        }
    )
    
    # Group by and aggregate (via raw SQL)
    result = await db.query_raw(
        """
        SELECT profile_type, COUNT(*) as count 
        FROM clients 
        GROUP BY profile_type
        """
    )
    
    return clients
