"""Real Supabase storage adapter wrapping existing implementation."""
from app.adapters.storage_base import StorageBase
from app.db.supabase import SupabaseClient


class SupabaseStorage(StorageBase):
    """Supabase storage adapter wrapping existing client."""

    def __init__(self, supabase_client: SupabaseClient):
        """Initialize with existing Supabase client."""
        self.client = supabase_client

    def upload_file(self, file_path: str, file_data: bytes, content_type: str) -> str:
        """Upload file to Supabase Storage."""
        return self.client.upload_file(file_path, file_data, content_type)

    def get_file_url(self, file_path: str, signed: bool = False, expires_in: int = 3600) -> str:
        """Get URL to access a stored file."""
        if signed:
            return self.client.get_signed_url(file_path, expires_in)
        else:
            return self.client.get_public_url(file_path)

    def file_exists(self, file_path: str) -> bool:
        """Check if file exists in storage."""
        # Supabase doesn't have a direct exists method, so we try to get the URL
        try:
            self.client.get_public_url(file_path)
            return True
        except Exception:
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from Supabase Storage."""
        try:
            self.client.storage.from_(self.client.bucket_name).remove([file_path])
            return True
        except Exception as e:
            # Log error but don't fail the operation
            return False
