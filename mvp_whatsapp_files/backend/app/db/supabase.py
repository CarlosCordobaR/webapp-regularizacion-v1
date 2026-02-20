"""Supabase client module."""
import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import create_client, Client

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SupabaseClient:
    """Supabase database client wrapper."""

    def __init__(self):
        """Initialize Supabase client."""
        settings = get_settings()
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
        self.bucket_name = settings.storage_bucket

    # Client operations
    def get_client_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get client by phone number."""
        try:
            response = self.client.table("clients").select("*").eq("phone_number", phone_number).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching client by phone: {e}")
            return None

    def create_client(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new client.
        
        Args:
            client_data: Client data to insert
            
        Returns:
            Created client data
            
        Raises:
            ValueError: If phone_number already exists (duplicate)
            Exception: For other database errors
        """
        try:
            response = self.client.table("clients").insert(client_data).execute()
            return response.data[0]
        except Exception as e:
            error_msg = str(e).lower()
            # Check for unique constraint violation on phone_number
            if "duplicate" in error_msg or "unique" in error_msg or "already exists" in error_msg:
                raise ValueError(f"Phone number {client_data.get('phone_number')} already exists")
            # Re-raise other errors
            logger.error(f"Error creating client: {e}")
            raise

    def update_client(self, client_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update client information."""
        response = self.client.table("clients").update(update_data).eq("id", str(client_id)).execute()
        return response.data[0]

    def get_clients(self, page: int = 1, page_size: int = 50) -> tuple[List[Dict[str, Any]], int]:
        """Get paginated list of clients."""
        offset = (page - 1) * page_size
        
        # Get total count
        count_response = self.client.table("clients").select("*", count="exact").execute()
        total = count_response.count or 0
        
        # Get paginated data
        response = self.client.table("clients").select("*").range(offset, offset + page_size - 1).order("created_at", desc=True).execute()
        
        return response.data, total

    def get_client_by_id(self, client_id: UUID) -> Optional[Dict[str, Any]]:
        """Get client by ID."""
        try:
            response = self.client.table("clients").select("*").eq("id", str(client_id)).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching client by ID: {e}")
            return None

    # Conversation operations
    def create_conversation(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new conversation entry."""
        response = self.client.table("conversations").insert(conversation_data).execute()
        return response.data[0]

    def get_conversations_by_client(
        self, 
        client_id: UUID, 
        page: int = 1, 
        page_size: int = 50
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get paginated conversations for a client."""
        offset = (page - 1) * page_size
        
        # Get total count
        count_response = self.client.table("conversations").select("*", count="exact").eq("client_id", str(client_id)).execute()
        total = count_response.count or 0
        
        # Get paginated data
        response = (
            self.client.table("conversations")
            .select("*")
            .eq("client_id", str(client_id))
            .range(offset, offset + page_size - 1)
            .order("created_at", desc=True)
            .execute()
        )
        
        return response.data, total

    def get_conversation_by_message_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by WhatsApp message ID."""
        try:
            response = self.client.table("conversations").select("*").eq("message_id", message_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching conversation by message ID: {e}")
            return None

    def update_conversation(self, conversation_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update conversation entry."""
        response = (
            self.client.table("conversations")
            .update(update_data)
            .eq("id", str(conversation_id))
            .execute()
        )
        return response.data[0]

    # Document operations
    def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document entry."""
        response = self.client.table("documents").insert(document_data).execute()
        return response.data[0]

    def update_document(self, document_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing document entry."""
        response = self.client.table("documents").update(update_data).eq("id", str(document_id)).execute()
        return response.data[0]

    def get_documents_by_client(
        self, 
        client_id: UUID, 
        page: int = 1, 
        page_size: int = 50
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get paginated documents for a client."""
        offset = (page - 1) * page_size
        
        # Get total count
        count_response = self.client.table("documents").select("*", count="exact").eq("client_id", str(client_id)).execute()
        total = count_response.count or 0
        
        # Get paginated data
        response = (
            self.client.table("documents")
            .select("*")
            .eq("client_id", str(client_id))
            .range(offset, offset + page_size - 1)
            .order("uploaded_at", desc=True)
            .execute()
        )
        
        return response.data, total

    def get_document_by_id(self, document_id: UUID) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        try:
            response = self.client.table("documents").select("*").eq("id", str(document_id)).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching document by ID: {e}")
            return None
    
    def get_client_documents(self, client_id: UUID) -> List[Dict[str, Any]]:
        """Get all documents for a client (no pagination)."""
        try:
            response = (
                self.client.table("documents")
                .select("*")
                .eq("client_id", str(client_id))
                .order("uploaded_at", desc=True)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching client documents: {e}")
            return []

    def get_document_by_client_and_type(
        self, client_id: UUID, document_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get latest document by client and document_type."""
        try:
            response = (
                self.client.table("documents")
                .select("*")
                .eq("client_id", str(client_id))
                .eq("document_type", document_type)
                .order("uploaded_at", desc=True)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching document by client/type: {e}")
            return None
    
    def delete_document(self, document_id: UUID) -> bool:
        """Delete a document by ID.
        
        Returns:
            True if document was deleted, False otherwise
        """
        try:
            response = self.client.table("documents").delete().eq("id", str(document_id)).execute()
            logger.info(f"Deleted document: {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False

    def create_document_version(self, version_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a version entry for a typed document."""
        response = self.client.table("document_versions").insert(version_data).execute()
        return response.data[0]

    def get_latest_document_version(
        self, client_id: UUID, document_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get latest version by client and document_type."""
        try:
            response = (
                self.client.table("document_versions")
                .select("*")
                .eq("client_id", str(client_id))
                .eq("document_type", document_type)
                .order("version_number", desc=True)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching latest document version: {e}")
            return None

    def create_audit_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an audit event entry."""
        response = self.client.table("audit_events").insert(event_data).execute()
        return response.data[0]

    def create_export_job(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an export job entry."""
        response = self.client.table("export_jobs").insert(export_data).execute()
        return response.data[0]

    # Upsert operations for sync
    def upsert_client(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert client by phone_number (creates or updates)."""
        phone_number = client_data.get("phone_number")
        if not phone_number:
            raise ValueError("phone_number is required for upsert")
        
        existing = self.get_client_by_phone(phone_number)
        if existing:
            # Update existing client
            logger.info(f"Updating existing client: {phone_number}")
            return self.update_client(UUID(existing["id"]), client_data)
        else:
            # Create new client
            logger.info(f"Creating new client: {phone_number}")
            return self.create_client(client_data)

    def upsert_conversation(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert conversation by dedupe_key or message_id."""
        dedupe_key = conversation_data.get("dedupe_key")
        message_id = conversation_data.get("message_id")
        
        # Try to find existing conversation
        existing = None
        if dedupe_key:
            try:
                response = self.client.table("conversations").select("*").eq("dedupe_key", dedupe_key).execute()
                if response.data:
                    existing = response.data[0]
            except Exception as e:
                logger.debug(f"Dedupe key lookup failed (might not exist yet): {e}")
        
        if not existing and message_id:
            existing = self.get_conversation_by_message_id(message_id)
        
        if existing:
            logger.debug(f"Conversation already exists, skipping: {dedupe_key or message_id}")
            return existing
        else:
            logger.info(f"Creating new conversation: {dedupe_key or message_id}")
            return self.create_conversation(conversation_data)

    def upsert_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert document by storage_path."""
        storage_path = document_data.get("storage_path")
        if not storage_path:
            raise ValueError("storage_path is required for upsert")
        
        # Check if document exists by storage_path
        try:
            response = self.client.table("documents").select("*").eq("storage_path", storage_path).execute()
            existing = response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error checking existing document: {e}")
            existing = None
        
        if existing:
            logger.debug(f"Document already exists: {storage_path}")
            return existing
        else:
            logger.info(f"Creating new document: {storage_path}")
            return self.create_document(document_data)

    def create_sync_mapping(self, mock_id: UUID, supabase_id: UUID, entity_type: str) -> None:
        """Record mock->supabase ID mapping."""
        try:
            self.client.table("sync_mappings").insert({
                "mock_id": str(mock_id),
                "supabase_id": str(supabase_id),
                "entity_type": entity_type
            }).execute()
        except Exception as e:
            logger.debug(f"Sync mapping might already exist: {e}")

    @staticmethod
    def generate_dedupe_key(
        client_id: str,
        direction: str,
        created_at: str,
        message_type: str,
        content: str
    ) -> str:
        """Generate dedupe_key for conversation idempotency."""
        raw = f"{client_id}|{direction}|{created_at}|{message_type}|{content or ''}"
        return hashlib.sha256(raw.encode()).hexdigest()[:64]

    # Storage operations
    def upload_file(self, file_path: str, file_data: bytes, content_type: str = "application/pdf") -> str:
        """Upload file to Supabase Storage."""
        self.client.storage.from_(self.bucket_name).upload(
            file_path,
            file_data,
            file_options={"content-type": content_type}
        )
        return file_path

    def upload_file_to_storage(
        self, 
        local_file_path: Path, 
        storage_path: str, 
        content_type: str = "application/pdf"
    ) -> bool:
        """Upload file to Supabase Storage with idempotency check."""
        # Check if file already exists
        if self.file_exists_in_storage(storage_path):
            logger.debug(f"File already exists in storage: {storage_path}")
            return False  # Already exists, skipped
        
        # Read and upload file
        with open(local_file_path, "rb") as f:
            file_data = f.read()
        
        try:
            self.upload_file(storage_path, file_data, content_type)
            logger.info(f"Uploaded file to storage: {storage_path}")
            return True  # Newly uploaded
        except Exception as e:
            logger.error(f"Error uploading file {storage_path}: {e}")
            raise

    def file_exists_in_storage(self, file_path: str) -> bool:
        """Check if file exists in Supabase Storage."""
        try:
            # Try to list the specific file
            response = self.client.storage.from_(self.bucket_name).list(path=str(Path(file_path).parent))
            if response:
                file_name = Path(file_path).name
                return any(item.get("name") == file_name for item in response)
            return False
        except Exception as e:
            logger.debug(f"File existence check failed (might not exist): {e}")
            return False

    def ensure_bucket_exists(self) -> bool:
        """Check if storage bucket exists. Returns True if exists, raises error if not."""
        try:
            buckets = self.client.storage.list_buckets()
            bucket_names = [b.name for b in buckets]
            
            if self.bucket_name in bucket_names:
                logger.info(f"Storage bucket '{self.bucket_name}' exists")
                return True
            else:
                error_msg = f"""
Storage bucket '{self.bucket_name}' does not exist!

MANUAL SETUP REQUIRED:
1. Go to Supabase Dashboard → Storage
2. Create a new bucket named '{self.bucket_name}'
3. Set bucket as PUBLIC (for MVP) or PRIVATE (use signed URLs)
4. Set file size limits if needed (e.g., 10MB for PDFs)
5. Re-run this script

Alternatively, use the Supabase CLI or API to create the bucket programmatically.
"""
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        except Exception as e:
            if "does not exist" in str(e):
                raise
            logger.error(f"Error checking bucket existence: {e}")
            raise

    def get_public_url(self, file_path: str) -> str:
        """Get public URL for a file."""
        response = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
        return response

    def get_signed_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Get signed URL for a private file."""
        response = self.client.storage.from_(self.bucket_name).create_signed_url(
            file_path,
            expires_in
        )
        return response.get("signedURL", "")


@lru_cache()
def get_supabase_client() -> SupabaseClient:
    """Get cached Supabase client instance."""
    return SupabaseClient()
