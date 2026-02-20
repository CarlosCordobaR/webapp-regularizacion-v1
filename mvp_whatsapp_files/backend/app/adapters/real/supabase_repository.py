"""Real Supabase repository adapter wrapping existing implementation."""
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.adapters.repository_base import RepositoryBase
from app.db.supabase import SupabaseClient


class SupabaseRepository(RepositoryBase):
    """Supabase repository adapter wrapping existing client."""

    def __init__(self, supabase_client: SupabaseClient):
        """Initialize with existing Supabase client."""
        self.client = supabase_client

    def get_client_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get client by phone number."""
        return self.client.get_client_by_phone(phone_number)

    def create_client(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new client."""
        return self.client.create_client(client_data)

    def update_client(self, client_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update client information."""
        return self.client.update_client(client_id, update_data)

    def get_clients(self, page: int = 1, page_size: int = 50) -> Tuple[List[Dict[str, Any]], int]:
        """Get paginated list of clients."""
        return self.client.get_clients(page, page_size)

    def get_client_by_id(self, client_id: UUID) -> Optional[Dict[str, Any]]:
        """Get client by ID."""
        return self.client.get_client_by_id(client_id)

    def create_conversation(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new conversation entry."""
        return self.client.create_conversation(conversation_data)

    def get_conversations_by_client(
        self, 
        client_id: UUID, 
        page: int = 1, 
        page_size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get paginated conversations for a client."""
        return self.client.get_conversations_by_client(client_id, page, page_size)

    def get_conversation_by_message_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by WhatsApp message ID."""
        return self.client.get_conversation_by_message_id(message_id)

    def update_conversation(self, conversation_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing conversation entry."""
        return self.client.update_conversation(conversation_id, update_data)

    def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document entry."""
        return self.client.create_document(document_data)

    def update_document(self, document_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing document entry."""
        return self.client.update_document(document_id, update_data)

    def get_documents_by_client(
        self, 
        client_id: UUID, 
        page: int = 1, 
        page_size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get paginated documents for a client."""
        return self.client.get_documents_by_client(client_id, page, page_size)

    def get_document_by_id(self, document_id: UUID) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        return self.client.get_document_by_id(document_id)
    
    def get_client_documents(self, client_id: UUID) -> List[Dict[str, Any]]:
        """Get all documents for a client (no pagination)."""
        return self.client.get_client_documents(client_id)

    def get_document_by_client_and_type(
        self, client_id: UUID, document_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get latest document by client and document_type."""
        return self.client.get_document_by_client_and_type(client_id, document_type)
    
    def delete_document(self, document_id: UUID) -> bool:
        """Delete a document by ID."""
        return self.client.delete_document(document_id)

    def create_document_version(self, version_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a version entry for a typed document."""
        return self.client.create_document_version(version_data)

    def get_latest_document_version(
        self, client_id: UUID, document_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get latest version by client and document_type."""
        return self.client.get_latest_document_version(client_id, document_type)

    def create_audit_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an audit event entry."""
        return self.client.create_audit_event(event_data)

    def create_export_job(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an export job entry."""
        return self.client.create_export_job(export_data)
