"""
Sync Mock Dataset to Supabase

This script syncs the mock dataset (10 clients, conversations, PDFs) to real Supabase.
Idempotent: Can be run multiple times without duplicating data.

Usage:
    python -m app.scripts.sync_mock_to_supabase
    
Environment variables required:
    SUPABASE_URL
    SUPABASE_SERVICE_ROLE_KEY
    STORAGE_BUCKET (default: client-documents)
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.logging import get_logger
from app.db.supabase import get_supabase_client
from app.adapters.mock.mock_repository import MockRepository
from app.adapters.mock.mock_storage import MockStorage
import unicodedata

logger = get_logger(__name__)


def sanitize_storage_path(path: str) -> str:
    """
    Sanitize storage path to be URL-safe for Supabase Storage.
    
    - Removes accents/tildes from characters (á -> a, ñ -> n)
    - Replaces spaces with underscores
    - Keeps only alphanumeric, underscores, hyphens, dots, and forward slashes
    
    Example:
        "profiles/ASYLUM/María_González_844a7e46/carta_asilo.pdf"
        -> "profiles/ASYLUM/Maria_Gonzalez_844a7e46/carta_asilo.pdf"
    """
    # Decompose unicode characters and remove combining marks (tildes, accents)
    nfkd_form = unicodedata.normalize('NFKD', path)
    path_no_accents = ''.join([c for c in nfkd_form if not unicodedata.combining(c)])
    
    # Replace spaces with underscores
    path_sanitized = path_no_accents.replace(' ', '_')
    
    # Keep only safe characters: alphanumeric, _, -, ., /
    safe_chars = []
    for c in path_sanitized:
        if c.isalnum() or c in ('_', '-', '.', '/'):
            safe_chars.append(c)
        else:
            safe_chars.append('_')  # Replace any other character with underscore
    
    return ''.join(safe_chars)


class SyncStats:
    """Track sync statistics."""
    
    def __init__(self):
        self.clients_inserted = 0
        self.clients_updated = 0
        self.clients_skipped = 0
        self.conversations_inserted = 0
        self.conversations_skipped = 0
        self.documents_inserted = 0
        self.documents_skipped = 0
        self.files_uploaded = 0
        self.files_skipped = 0
        self.errors: List[str] = []
        self.mappings: Dict[str, Dict[str, str]] = {
            "clients": {},
            "conversations": {},
            "documents": {}
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "summary": {
                "clients": {
                    "inserted": self.clients_inserted,
                    "updated": self.clients_updated,
                    "skipped": self.clients_skipped,
                    "total": self.clients_inserted + self.clients_updated + self.clients_skipped
                },
                "conversations": {
                    "inserted": self.conversations_inserted,
                    "skipped": self.conversations_skipped,
                    "total": self.conversations_inserted + self.conversations_skipped
                },
                "documents": {
                    "inserted": self.documents_inserted,
                    "skipped": self.documents_skipped,
                    "total": self.documents_inserted + self.documents_skipped
                },
                "files": {
                    "uploaded": self.files_uploaded,
                    "skipped": self.files_skipped,
                    "total": self.files_uploaded + self.files_skipped
                }
            },
            "errors": self.errors,
            "mappings": self.mappings
        }


def sync_clients(
    mock_repo: MockRepository,
    supabase_client,
    stats: SyncStats
) -> Dict[str, str]:
    """Sync clients from mock to Supabase. Returns mock_id -> supabase_id mapping."""
    logger.info("=== Syncing Clients ===")
    
    # Get all mock clients (using large page size to get all at once)
    mock_clients_data, total = mock_repo.get_clients(page=1, page_size=1000)
    logger.info(f"Found {len(mock_clients_data)} clients in mock database")
    
    client_id_map = {}
    
    for mock_client_dict in mock_clients_data:
        try:
            # Prepare client data
            client_data = {
                "phone_number": mock_client_dict["phone_number"],
                "name": mock_client_dict.get("name"),
                "profile_type": mock_client_dict.get("profile_type", "OTHER"),
                "status": mock_client_dict.get("status", "active"),
                "metadata": mock_client_dict.get("metadata", {}),
                "created_at": mock_client_dict.get("created_at"),
            }
            
            # Check if client exists
            existing = supabase_client.get_client_by_phone(mock_client_dict["phone_number"])
            
            if existing:
                # Update existing
                result = supabase_client.update_client(UUID(existing["id"]), client_data)
                stats.clients_updated += 1
                logger.info(f"Updated client: {mock_client_dict.get('name')} ({mock_client_dict['phone_number']})")
            else:
                # Create new
                result = supabase_client.create_client(client_data)
                stats.clients_inserted += 1
                logger.info(f"Inserted client: {mock_client_dict.get('name')} ({mock_client_dict['phone_number']})")
            
            # Map IDs
            supabase_id = result["id"]
            mock_client_id = mock_client_dict["id"]
            client_id_map[mock_client_id] = supabase_id
            stats.mappings["clients"][mock_client_id] = supabase_id
            
            # Store mapping in Supabase
            supabase_client.create_sync_mapping(
                UUID(mock_client_id),
                UUID(supabase_id),
                "client"
            )
            
        except Exception as e:
            error_msg = f"Error syncing client {mock_client_dict.get('phone_number')}: {e}"
            logger.error(error_msg)
            stats.errors.append(error_msg)
            stats.clients_skipped += 1
    
    logger.info(f"Clients sync complete: {stats.clients_inserted} inserted, {stats.clients_updated} updated, {stats.clients_skipped} skipped")
    return client_id_map


def sync_conversations(
    mock_repo: MockRepository,
    supabase_client,
    client_id_map: Dict[str, str],
    stats: SyncStats
) -> None:
    """Sync conversations from mock to Supabase."""
    logger.info("=== Syncing Conversations ===")
    
    for mock_client_id, supabase_client_id in client_id_map.items():
        try:
            # Get mock conversations (returns list of dicts)
            mock_conversations, _ = mock_repo.get_conversations_by_client(UUID(mock_client_id), page=1, page_size=1000)
            logger.info(f"Found {len(mock_conversations)} conversations for client {mock_client_id}")
            
            for conv in mock_conversations:
                try:
                    # Generate dedupe key
                    dedupe_key = supabase_client.generate_dedupe_key(
                        client_id=supabase_client_id,
                        direction=conv.get("direction", "INBOUND"),
                        created_at=conv.get("created_at", ""),
                        message_type=conv.get("message_type", "text"),
                        content=conv.get("content", "")
                    )
                    
                    # Prepare conversation data
                    conv_data = {
                        "client_id": supabase_client_id,
                        "message_id": conv.get("message_id") or f"mock_{conv['id']}",
                        "direction": conv.get("direction", "INBOUND"),
                        "content": conv.get("content"),
                        "message_type": conv.get("message_type", "text"),
                        "dedupe_key": dedupe_key,
                        "metadata": conv.get("metadata", {}),
                        "created_at": conv.get("created_at")
                    }
                    
                    # Upsert conversation
                    result = supabase_client.upsert_conversation(conv_data)
                    
                    if result.get("id"):
                        # Check if it was just created or already existed
                        if "Creating new conversation" in str(logger.handlers):
                            stats.conversations_inserted += 1
                        else:
                            stats.conversations_skipped += 1
                        
                        stats.mappings["conversations"][conv["id"]] = result["id"]
                    
                except Exception as e:
                    error_msg = f"Error syncing conversation {conv.get('id')}: {e}"
                    logger.debug(error_msg)
                    stats.conversations_skipped += 1
            
        except Exception as e:
            error_msg = f"Error syncing conversations for client {mock_client_id}: {e}"
            logger.error(error_msg)
            stats.errors.append(error_msg)
    
    logger.info(f"Conversations sync complete: {stats.conversations_inserted} inserted, {stats.conversations_skipped} skipped")


def sync_documents(
    mock_repo: MockRepository,
    mock_storage: MockStorage,
    supabase_client,
    client_id_map: Dict[str, str],
    stats: SyncStats
) -> None:
    """Sync documents and files from mock to Supabase."""
    logger.info("=== Syncing Documents ===")
    
    for mock_client_id, supabase_client_id in client_id_map.items():
        try:
            # Get mock documents (returns list of dicts)
            mock_documents, _ = mock_repo.get_documents_by_client(UUID(mock_client_id), page=1, page_size=1000)
            logger.info(f"Found {len(mock_documents)} documents for client {mock_client_id}")
            
            for doc in mock_documents:
                try:
                    # Get local file path
                    original_storage_path = doc.get("storage_path", "")
                    # Sanitize storage path to be URL-safe for Supabase
                    storage_path = sanitize_storage_path(original_storage_path)
                    local_file_path = mock_storage.base_path / original_storage_path  # Use original path for local file
                    
                    if not local_file_path.exists():
                        error_msg = f"Local file not found: {local_file_path}"
                        logger.warning(error_msg)
                        stats.documents_skipped += 1
                        stats.files_skipped += 1
                        continue
                    
                    # Upload file to Supabase Storage (using sanitized path)
                    file_uploaded = supabase_client.upload_file_to_storage(
                        local_file_path=local_file_path,
                        storage_path=storage_path,
                        content_type=doc.get("mime_type", "application/pdf")
                    )
                    
                    if file_uploaded:
                        stats.files_uploaded += 1
                    else:
                        stats.files_skipped += 1
                    
                    # Prepare document metadata (using sanitized path for storage reference)
                    doc_data = {
                        "client_id": supabase_client_id,
                        "storage_path": storage_path,  # Use sanitized path in database
                        "original_filename": doc.get("original_filename"),
                        "mime_type": doc.get("mime_type"),
                        "file_size": doc.get("file_size"),
                        "profile_type": doc.get("profile_type"),
                        "metadata": doc.get("metadata", {}),
                        "uploaded_at": doc.get("uploaded_at")
                    }
                    
                    # Upsert document record
                    result = supabase_client.upsert_document(doc_data)
                    
                    if "Creating new document" in str(result):
                        stats.documents_inserted += 1
                    else:
                        stats.documents_skipped += 1
                    
                    stats.mappings["documents"][doc["id"]] = result["id"]
                    
                except Exception as e:
                    error_msg = f"Error syncing document {doc.get('id')}: {e}"
                    logger.error(error_msg)
                    stats.errors.append(error_msg)
                    stats.documents_skipped += 1
            
        except Exception as e:
            error_msg = f"Error syncing documents for client {mock_client_id}: {e}"
            logger.error(error_msg)
            stats.errors.append(error_msg)
    
    logger.info(f"Documents sync complete: {stats.documents_inserted} inserted, {stats.documents_skipped} skipped")
    logger.info(f"Files: {stats.files_uploaded} uploaded, {stats.files_skipped} skipped")


def generate_report(stats: SyncStats) -> Path:
    """Generate JSON report file."""
    # Create reports directory
    reports_dir = Path(__file__).parent.parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = reports_dir / f"sync_report_{timestamp}.json"
    
    # Write report
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "script": "sync_mock_to_supabase",
        **stats.to_dict()
    }
    
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Report written to: {report_path}")
    return report_path


def main():
    """Main sync function."""
    logger.info("=" * 80)
    logger.info("Starting Mock Data -> Supabase Sync")
    logger.info("=" * 80)
    
    # Check environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these in your .env file or export them before running this script")
        sys.exit(1)
    
    # Initialize clients
    try:
        supabase_client = get_supabase_client()
        mock_repo = MockRepository()
        mock_storage = MockStorage()
        stats = SyncStats()
        
        logger.info(f"Supabase URL: {os.getenv('SUPABASE_URL')}")
        logger.info(f"Storage Bucket: {supabase_client.bucket_name}")
        
        # Check bucket exists
        supabase_client.ensure_bucket_exists()
        
    except Exception as e:
        logger.error(f"Failed to initialize clients: {e}")
        sys.exit(1)
    
    # Run sync
    try:
        # Step 1: Sync clients
        client_id_map = sync_clients(mock_repo, supabase_client, stats)
        
        if not client_id_map:
            logger.error("No clients were synced. Aborting.")
            sys.exit(1)
        
        # Step 2: Sync conversations
        sync_conversations(mock_repo, supabase_client, client_id_map, stats)
        
        # Step 3: Sync documents
        sync_documents(mock_repo, mock_storage, supabase_client, client_id_map, stats)
        
    except Exception as e:
        logger.error(f"Sync failed with error: {e}")
        stats.errors.append(f"Fatal error: {e}")
        raise
    
    finally:
        # Always generate report
        report_path = generate_report(stats)
        
        # Print summary
        logger.info("=" * 80)
        logger.info("SYNC COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Clients: {stats.clients_inserted} inserted, {stats.clients_updated} updated, {stats.clients_skipped} skipped")
        logger.info(f"Conversations: {stats.conversations_inserted} inserted, {stats.conversations_skipped} skipped")
        logger.info(f"Documents: {stats.documents_inserted} inserted, {stats.documents_skipped} skipped")
        logger.info(f"Files: {stats.files_uploaded} uploaded, {stats.files_skipped} skipped")
        
        if stats.errors:
            logger.warning(f"Errors encountered: {len(stats.errors)}")
            for error in stats.errors[:5]:  # Show first 5 errors
                logger.warning(f"  - {error}")
        
        logger.info(f"Full report: {report_path}")
        logger.info("=" * 80)


if __name__ == "__main__":
    main()
