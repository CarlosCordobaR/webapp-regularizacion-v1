"""Storage service for file operations."""
from typing import Optional
from uuid import UUID

from app.adapters.factory import get_storage
from app.core.logging import get_logger
from app.models.enums import ProfileType
from app.whatsapp.media import generate_storage_path

logger = get_logger(__name__)


class StorageService:
    """Handle file storage operations."""

    def __init__(self):
        """Initialize storage service."""
        self.storage = get_storage()

    async def upload_file(
        self,
        file_content: bytes,
        client_id: UUID,
        client_name: Optional[str],
        profile_type: ProfileType,
        filename: str,
        mime_type: str
    ) -> str:
        """
        Upload file to storage.
        
        Args:
            file_content: File bytes
            client_id: Client UUID
            client_name: Client name
            profile_type: Client profile type
            filename: Original filename
            mime_type: File MIME type
            
        Returns:
            Storage path where file was uploaded
        """
        # Generate storage path
        storage_path = generate_storage_path(
            profile_type=profile_type,
            client_name=client_name,
            client_id=client_id,
            filename=filename
        )
        
        try:
            # Upload to storage
            self.storage.upload_file(
                file_path=storage_path,
                file_data=file_content,
                content_type=mime_type
            )
            
            logger.info(f"Uploaded file to {storage_path}")
            return storage_path
            
        except Exception as e:
            logger.error(f"Error uploading file to {storage_path}: {e}")
            raise

    def get_file_url(self, storage_path: str, signed: bool = False, expires_in: int = 3600) -> str:
        """
        Get URL for accessing a stored file.
        
        Args:
            storage_path: Path in storage bucket
            signed: Whether to generate signed URL for private access
            expires_in: Expiration time in seconds (for signed URLs)
            
        Returns:
            File URL
        """
        return self.storage.get_file_url(storage_path, signed, expires_in)
