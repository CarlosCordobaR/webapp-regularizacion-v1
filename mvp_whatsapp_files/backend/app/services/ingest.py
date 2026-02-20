"""Message ingestion service."""
from typing import Any, Dict, Optional
from uuid import UUID

from app.adapters.factory import get_repository
from app.core.logging import get_logger
from app.models.enums import ClientStatus, MessageDirection, ProfileType
from app.services.classifier import classify_profile
from app.services.storage import StorageService
from app.whatsapp.media import download_and_prepare_media

logger = get_logger(__name__)


class IngestService:
    """Service for ingesting WhatsApp messages and media."""

    def __init__(self):
        """Initialize ingest service."""
        self.repository = get_repository()
        self.storage = StorageService()

    async def get_or_create_client(
        self,
        phone_number: str,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get existing client or create new one.
        
        Args:
            phone_number: Client phone number
            name: Optional client name
            
        Returns:
            Client record
        """
        # Try to get existing client
        client = self.repository.get_client_by_phone(phone_number)
        
        if client:
            # Update name if provided and different
            if name and client.get("name") != name:
                client = self.repository.update_client(
                    client_id=UUID(client["id"]),
                    update_data={"name": name}
                )
            return client
        
        # Create new client
        client_data = {
            "phone_number": phone_number,
            "name": name,
            "profile_type": ProfileType.OTHER.value,
            "status": ClientStatus.ACTIVE.value,
            "metadata": {}
        }
        
        client = self.repository.create_client(client_data)
        logger.info(f"Created new client: {client['id']}")
        
        return client

    async def store_conversation(
        self,
        client_id: str,
        message_id: str,
        direction: MessageDirection,
        content: Optional[str],
        message_type: str,
        timestamp: str
    ) -> Dict[str, Any]:
        """
        Store conversation message.
        
        Args:
            client_id: Client UUID
            message_id: WhatsApp message ID
            direction: Message direction (inbound/outbound)
            content: Message text content
            message_type: WhatsApp message type
            timestamp: Message timestamp
            
        Returns:
            Conversation record
        """
        conversation_data = {
            "client_id": client_id,
            "message_id": message_id,
            "direction": direction.value,
            "content": content,
            "message_type": message_type,
            "metadata": {"timestamp": timestamp}
        }
        
        conversation = self.repository.create_conversation(conversation_data)
        logger.info(f"Stored conversation: {conversation['id']}")
        
        return conversation

    async def classify_and_update_profile(
        self,
        client_id: str,
        text: str
    ) -> Optional[ProfileType]:
        """
        Classify text and update client profile if needed.
        
        Args:
            client_id: Client UUID
            text: Text to classify
            
        Returns:
            New profile type if updated, None otherwise
        """
        # Get current client
        client = self.repository.get_client_by_id(UUID(client_id))
        if not client:
            logger.error(f"Client {client_id} not found")
            return None
        
        # Classify text
        new_profile_type = classify_profile(text)
        
        # Update if classification is more specific than OTHER
        # and current profile is OTHER or classification changed
        current_profile = ProfileType(client.get("profile_type", "OTHER"))
        
        if new_profile_type != ProfileType.OTHER:
            if current_profile == ProfileType.OTHER or new_profile_type != current_profile:
                self.repository.update_client(
                    client_id=UUID(client_id),
                    update_data={"profile_type": new_profile_type.value}
                )
                logger.info(f"Updated client {client_id} profile to {new_profile_type.value}")
                return new_profile_type
        
        return None

    async def process_and_store_media(
        self,
        client_id: str,
        conversation_id: str,
        media_id: str,
        mime_type: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Download media from WhatsApp and store in storage.
        
        Args:
            client_id: Client UUID
            conversation_id: Conversation UUID
            media_id: WhatsApp media ID
            mime_type: Optional MIME type
            filename: Optional original filename
            
        Returns:
            Document record
        """
        # Get client info
        client = self.repository.get_client_by_id(UUID(client_id))
        if not client:
            raise ValueError(f"Client {client_id} not found")
        
        # Download media
        media_result = await download_and_prepare_media(
            media_id=media_id,
            mime_type=mime_type,
            filename=filename
        )
        
        if not media_result:
            raise Exception(f"Failed to download media {media_id}")
        
        content, final_mime_type, final_filename = media_result
        
        # Upload to storage
        storage_path = await self.storage.upload_file(
            file_content=content,
            client_id=UUID(client_id),
            client_name=client.get("name"),
            profile_type=ProfileType(client.get("profile_type", "OTHER")),
            filename=final_filename,
            mime_type=final_mime_type
        )
        
        # Create document record
        document_data = {
            "client_id": client_id,
            "conversation_id": conversation_id,
            "storage_path": storage_path,
            "original_filename": final_filename,
            "mime_type": final_mime_type,
            "file_size": len(content),
            "profile_type": client.get("profile_type"),
            "metadata": {"media_id": media_id}
        }
        
        document = self.repository.create_document(document_data)
        logger.info(f"Created document record: {document['id']}")
        
        return document
