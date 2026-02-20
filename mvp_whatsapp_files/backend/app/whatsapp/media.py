"""WhatsApp media handling module."""
import re
from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.enums import ProfileType
from app.whatsapp.client import WhatsAppClient

logger = get_logger(__name__)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other issues.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for storage
    """
    # Remove path separators and dangerous characters
    filename = re.sub(r'[/\\:*?"<>|]', '_', filename)
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    # Limit length
    if len(filename) > 200:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:195] + ('.' + ext if ext else '')
    return filename or 'unknown'


def generate_storage_path(
    profile_type: ProfileType,
    client_name: Optional[str],
    client_id: UUID,
    filename: str
) -> str:
    """
    Generate deterministic storage path for media file.
    
    Format: profiles/{profile_type}/{client_name}_{client_id}/{timestamp}_{filename}
    
    Args:
        profile_type: Client profile type
        client_name: Client name (or 'unknown')
        client_id: Client UUID
        filename: Original filename
        
    Returns:
        Storage path string
    """
    # Sanitize inputs
    safe_filename = sanitize_filename(filename)
    safe_client_name = sanitize_filename(client_name) if client_name else "unknown"
    
    # Generate timestamp prefix
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    # Build path
    path = f"profiles/{profile_type.value}/{safe_client_name}_{client_id}/{timestamp}_{safe_filename}"
    
    return path


async def download_and_prepare_media(
    media_id: str,
    mime_type: Optional[str] = None,
    filename: Optional[str] = None
) -> Optional[Tuple[bytes, str, Optional[str]]]:
    """
    Download media from WhatsApp and prepare for storage.
    
    Args:
        media_id: WhatsApp media ID
        mime_type: Optional MIME type
        filename: Optional original filename
        
    Returns:
        Tuple of (content bytes, mime_type, filename) or None if failed
    """
    settings = get_settings()
    client = WhatsAppClient()
    
    # Retry logic
    for attempt in range(settings.media_download_retries):
        try:
            # Get media URL
            media_url = await client.get_media_url(media_id)
            if not media_url:
                logger.warning(f"Could not get media URL for {media_id}, attempt {attempt + 1}")
                continue
            
            # Download media content
            content = await client.download_media(media_url)
            if not content:
                logger.warning(f"Could not download media {media_id}, attempt {attempt + 1}")
                continue
            
            # Get metadata if needed
            if not mime_type or not filename:
                metadata = await client.get_media_metadata(media_id)
                if metadata:
                    mime_type = mime_type or metadata.get("mime_type")
                    filename = filename or metadata.get("filename", "document")
            
            # Ensure we have at least basic info
            mime_type = mime_type or "application/octet-stream"
            filename = filename or f"document_{media_id}"
            
            logger.info(f"Successfully downloaded media {media_id}")
            return content, mime_type, filename
            
        except Exception as e:
            logger.error(f"Error downloading media {media_id}, attempt {attempt + 1}: {e}")
            if attempt == settings.media_download_retries - 1:
                return None
    
    return None
