"""Mock WhatsApp client for development."""
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import uuid4

from app.adapters.whatsapp_base import WhatsAppBase
from app.core.logging import get_logger

logger = get_logger(__name__)


class MockWhatsAppClient(WhatsAppBase):
    """Mock WhatsApp client that reads from local fixtures."""

    def __init__(self, fixtures_path: str = "backend/app/fixtures/pdfs"):
        """Initialize mock WhatsApp client."""
        self.fixtures_path = Path(fixtures_path)
        self.fixtures_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Mock WhatsApp client initialized with fixtures at {self.fixtures_path}")

    async def send_text_message(self, to_phone: str, text: str) -> Optional[Dict[str, Any]]:
        """Return a deterministic mock response for outbound text messages."""
        message_id = f"mock_wamid_{uuid4().hex}"
        return {
            "messaging_product": "whatsapp",
            "contacts": [{"input": to_phone, "wa_id": to_phone}],
            "messages": [{"id": message_id}],
            "mock": True,
            "echo": text,
        }

    async def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        language_code: str = "es",
        body_parameters: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Return a deterministic mock response for outbound template messages."""
        message_id = f"mock_wamid_tpl_{uuid4().hex}"
        return {
            "messaging_product": "whatsapp",
            "contacts": [{"input": to_phone, "wa_id": to_phone}],
            "messages": [{"id": message_id}],
            "mock": True,
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "body_parameters": body_parameters or [],
            },
        }

    async def get_media_url(self, media_id: str) -> Optional[str]:
        """
        Get media download URL (mock returns a local file path).
        
        In mock mode, media_id is expected to be a filename in fixtures.
        """
        return f"mock://fixtures/{media_id}"

    async def download_media(self, media_url: str) -> Optional[bytes]:
        """
        Download media content from fixtures.
        
        Args:
            media_url: Expected format "mock://fixtures/{filename}"
        """
        try:
            # Extract filename from mock URL
            if media_url.startswith("mock://fixtures/"):
                filename = media_url.replace("mock://fixtures/", "")
                file_path = self.fixtures_path / filename
                
                if file_path.exists():
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    logger.info(f"Downloaded mock media: {filename} ({len(content)} bytes)")
                    return content
                else:
                    logger.warning(f"Mock media file not found: {file_path}")
                    return None
            else:
                logger.warning(f"Invalid mock media URL: {media_url}")
                return None
        except Exception as e:
            logger.error(f"Error downloading mock media: {e}")
            return None

    async def get_media_metadata(self, media_id: str) -> Optional[Dict[str, Any]]:
        """Get media metadata (mock returns basic info)."""
        # In mock mode, media_id is the filename
        file_path = self.fixtures_path / media_id
        
        if file_path.exists():
            file_size = file_path.stat().st_size
            mime_type = "application/pdf" if media_id.endswith('.pdf') else "application/octet-stream"
            
            return {
                "id": media_id,
                "mime_type": mime_type,
                "file_size": file_size,
                "filename": media_id
            }
        
        return None
