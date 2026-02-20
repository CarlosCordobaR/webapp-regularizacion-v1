"""Base repository interface for client/conversation/document operations."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID


class RepositoryBase(ABC):
    """Abstract base class for data repository operations."""

    # Client operations
    @abstractmethod
    def get_client_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get client by phone number."""
        pass

    @abstractmethod
    def create_client(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new client."""
        pass

    @abstractmethod
    def update_client(self, client_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update client information."""
        pass

    @abstractmethod
    def get_clients(self, page: int = 1, page_size: int = 50) -> Tuple[List[Dict[str, Any]], int]:
        """Get paginated list of clients."""
        pass

    @abstractmethod
    def get_client_by_id(self, client_id: UUID) -> Optional[Dict[str, Any]]:
        """Get client by ID."""
        pass

    # Conversation operations
    @abstractmethod
    def create_conversation(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new conversation entry."""
        pass

    @abstractmethod
    def get_conversations_by_client(
        self, 
        client_id: UUID, 
        page: int = 1, 
        page_size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get paginated conversations for a client."""
        pass

    @abstractmethod
    def get_conversation_by_message_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by WhatsApp message ID."""
        pass

    @abstractmethod
    def update_conversation(self, conversation_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing conversation entry."""
        pass

    # Document operations
    @abstractmethod
    def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document entry."""
        pass

    @abstractmethod
    def update_document(self, document_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing document entry."""
        pass

    @abstractmethod
    def get_documents_by_client(
        self, 
        client_id: UUID, 
        page: int = 1, 
        page_size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get paginated documents for a client."""
        pass

    @abstractmethod
    def get_document_by_id(self, document_id: UUID) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        pass
    
    @abstractmethod
    def get_client_documents(self, client_id: UUID) -> List[Dict[str, Any]]:
        """Get all documents for a client (no pagination)."""
        pass

    @abstractmethod
    def get_document_by_client_and_type(
        self, client_id: UUID, document_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get latest document by client and document_type."""
        pass
    
    @abstractmethod
    def delete_document(self, document_id: UUID) -> bool:
        """Delete a document by ID."""
        pass

    @abstractmethod
    def create_document_version(self, version_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a version entry for a typed document."""
        pass

    @abstractmethod
    def get_latest_document_version(
        self, client_id: UUID, document_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get latest version by client and document_type."""
        pass

    @abstractmethod
    def create_audit_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an audit event entry."""
        pass

    @abstractmethod
    def create_export_job(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an export job entry."""
        pass
