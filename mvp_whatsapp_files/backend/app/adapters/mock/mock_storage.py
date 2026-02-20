"""Mock storage implementation using local filesystem."""
from pathlib import Path
from typing import Optional

from app.adapters.storage_base import StorageBase
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MockStorage(StorageBase):
    """Local filesystem-based mock storage for development."""

    def __init__(self, base_path: str = "backend/.local_storage/files"):
        """Initialize mock storage with local directory."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Mock storage initialized at {self.base_path}")

    def upload_file(self, file_path: str, file_data: bytes, content_type: str) -> str:
        """Upload file to local storage."""
        full_path = self.base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'wb') as f:
            f.write(file_data)
        
        logger.info(f"Uploaded file to {full_path}")
        return file_path

    def get_file_url(self, file_path: str, signed: bool = False, expires_in: int = 3600) -> str:
        """Get URL to access a stored file."""
        settings = get_settings()
        # Return mock storage endpoint URL
        return f"{settings.app_base_url}/mock-storage/{file_path}"

    def file_exists(self, file_path: str) -> bool:
        """Check if file exists in storage."""
        full_path = self.base_path / file_path
        return full_path.exists()

    def read_file(self, file_path: str) -> Optional[bytes]:
        """Read file from local storage."""
        full_path = self.base_path / file_path
        if not full_path.exists():
            return None
        
        with open(full_path, 'rb') as f:
            return f.read()
