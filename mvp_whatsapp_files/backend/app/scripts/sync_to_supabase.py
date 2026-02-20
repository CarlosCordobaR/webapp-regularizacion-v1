"""
Sync mock data to Supabase production.

This script reads data from the local SQLite mock database and uploads it
to Supabase, including copying files from local storage to Supabase Storage.

Usage:
    python -m app.scripts.sync_to_supabase

Prerequisites:
    - SUPABASE_URL and SUPABASE_KEY must be set in .env
    - Mock database must exist at backend/.local_storage/mock.db
"""
import os
import sys
from pathlib import Path
from typing import Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.adapters.mock.mock_repository import MockRepository
from app.adapters.mock.mock_storage import MockStorage
from app.adapters.real.supabase_repository import SupabaseRepository
from app.adapters.real.supabase_storage import SupabaseStorage
from app.core.logging import get_logger
from app.db.supabase import get_supabase_client

logger = get_logger(__name__)


class SyncService:
    """Service for syncing mock data to Supabase."""

    def __init__(self):
        """Initialize sync service."""
        # Mock sources
        self.mock_repo = MockRepository()
        self.mock_storage = MockStorage()
        
        # Real destinations
        supabase_client = get_supabase_client()
        self.real_repo = SupabaseRepository(supabase_client)
        self.real_storage = SupabaseStorage(supabase_client)
        
        # Track mappings for ID conversion
        self.client_id_map: Dict[str, str] = {}
        self.conversation_id_map: Dict[str, str] = {}
        
    def sync_clients(self) -> int:
        """
        Sync all clients from mock to Supabase.
        
        Returns:
            Number of clients synced
        """
        logger.info("Syncing clients...")
        clients = self.mock_repo.get_clients()
        
        for mock_client in clients:
            # Check if client already exists by phone number
            existing = self.real_repo.get_client_by_phone(mock_client["phone_number"])
            
            if existing:
                logger.info(f"Client {mock_client['phone_number']} already exists, skipping")
                self.client_id_map[mock_client["id"]] = existing["id"]
                continue
            
            # Create new client (without ID, let Supabase generate it)
            client_data = {
                "phone_number": mock_client["phone_number"],
                "name": mock_client["name"],
                "profile_type": mock_client["profile_type"],
                "status": mock_client["status"],
                "metadata": mock_client["metadata"]
            }
            
            new_client = self.real_repo.create_client(client_data)
            self.client_id_map[mock_client["id"]] = new_client["id"]
            logger.info(f"Created client: {mock_client['name']} ({new_client['id']})")
        
        return len(clients)
    
    def sync_conversations(self) -> int:
        """
        Sync all conversations from mock to Supabase.
        
        Returns:
            Number of conversations synced
        """
        logger.info("Syncing conversations...")
        count = 0
        
        for mock_client_id, real_client_id in self.client_id_map.items():
            # Get all conversations for this client
            conversations = self.mock_repo.get_conversations_by_client(mock_client_id)
            
            for conv in conversations:
                # Check if conversation already exists by message_id
                existing = self.real_repo.get_conversation_by_message_id(conv["message_id"])
                
                if existing:
                    self.conversation_id_map[conv["id"]] = existing["id"]
                    continue
                
                # Create new conversation
                conv_data = {
                    "client_id": real_client_id,
                    "message_id": conv["message_id"],
                    "direction": conv["direction"],
                    "content": conv["content"],
                    "message_type": conv["message_type"],
                    "metadata": conv["metadata"]
                }
                
                new_conv = self.real_repo.create_conversation(conv_data)
                self.conversation_id_map[conv["id"]] = new_conv["id"]
                count += 1
        
        logger.info(f"Created {count} conversations")
        return count
    
    def sync_documents(self) -> int:
        """
        Sync all documents from mock to Supabase, including file uploads.
        
        Returns:
            Number of documents synced
        """
        logger.info("Syncing documents...")
        count = 0
        
        for mock_client_id, real_client_id in self.client_id_map.items():
            # Get all documents for this client
            documents = self.mock_repo.get_documents_by_client(mock_client_id)
            
            for doc in documents:
                # Check if document already exists by storage_path
                existing_docs = self.real_repo.get_documents_by_client(real_client_id)
                existing = next(
                    (d for d in existing_docs if d["storage_path"] == doc["storage_path"]),
                    None
                )
                
                if existing:
                    logger.info(f"Document {doc['storage_path']} already exists, skipping")
                    continue
                
                # Read file from mock storage
                try:
                    file_data = self.mock_storage.download_file(doc["storage_path"])
                except Exception as e:
                    logger.error(f"Failed to read file {doc['storage_path']}: {e}")
                    continue
                
                # Upload to Supabase Storage
                try:
                    self.real_storage.upload_file(
                        file_path=doc["storage_path"],
                        file_data=file_data,
                        content_type=doc["mime_type"] or "application/octet-stream"
                    )
                    logger.info(f"Uploaded file: {doc['storage_path']}")
                except Exception as e:
                    logger.error(f"Failed to upload file {doc['storage_path']}: {e}")
                    continue
                
                # Create document record
                doc_data = {
                    "client_id": real_client_id,
                    "conversation_id": self.conversation_id_map.get(doc["conversation_id"]) if doc["conversation_id"] else None,
                    "storage_path": doc["storage_path"],
                    "original_filename": doc["original_filename"],
                    "mime_type": doc["mime_type"],
                    "file_size": doc["file_size"],
                    "profile_type": doc["profile_type"],
                    "metadata": doc["metadata"]
                }
                
                self.real_repo.create_document(doc_data)
                count += 1
        
        logger.info(f"Created {count} documents")
        return count
    
    def run(self):
        """Execute full sync process."""
        logger.info("=" * 50)
        logger.info("Starting sync from mock to Supabase")
        logger.info("=" * 50)
        
        try:
            # Verify Supabase credentials are set
            if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
            
            # Sync in order (clients -> conversations -> documents)
            clients_count = self.sync_clients()
            conversations_count = self.sync_conversations()
            documents_count = self.sync_documents()
            
            logger.info("=" * 50)
            logger.info("Sync completed successfully!")
            logger.info(f"  Clients: {clients_count}")
            logger.info(f"  Conversations: {conversations_count}")
            logger.info(f"  Documents: {documents_count}")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            raise


def main():
    """Main entry point."""
    sync_service = SyncService()
    sync_service.run()


if __name__ == "__main__":
    main()
