"""Base storage interface for file operations."""
from abc import ABC, abstractmethod


class StorageBase(ABC):
    """Abstract base class for file storage operations."""

    @abstractmethod
    def upload_file(self, file_path: str, file_data: bytes, content_type: str) -> str:
        """
        Upload file to storage.
        
        Args:
            file_path: Storage path for the file
            file_data: File content as bytes
            content_type: MIME type
            
        Returns:
            Storage path where file was saved
        """
        pass

    @abstractmethod
    def get_file_url(self, file_path: str, signed: bool = False, expires_in: int = 3600) -> str:
        """
        Get URL to access a stored file.
        
        Args:
            file_path: Storage path
            signed: Whether to generate signed URL
            expires_in: Expiration time for signed URLs (seconds)
            
        Returns:
            Accessible URL
        """
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists in storage."""
        pass
    
    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            file_path: Storage path of the file to delete
            
        Returns:
            True if file was deleted, False otherwise
        """
        pass
