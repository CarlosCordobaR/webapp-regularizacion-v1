"""Real Meta WhatsApp client adapter wrapping existing implementation."""
from typing import Dict, Any, List, Optional

from app.adapters.whatsapp_base import WhatsAppBase
from app.whatsapp.client import WhatsAppClient


class MetaWhatsAppClient(WhatsAppBase):
    """Meta WhatsApp API client adapter wrapping existing implementation."""

    def __init__(self, whatsapp_client: WhatsAppClient):
        """Initialize with existing WhatsApp client."""
        self.client = whatsapp_client

    async def send_text_message(self, to_phone: str, text: str) -> Optional[Dict[str, Any]]:
        """Send outbound text message through Meta WhatsApp API."""
        return await self.client.send_text_message(to_phone, text)

    async def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        language_code: str = "es",
        body_parameters: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Send outbound template message through Meta WhatsApp API."""
        return await self.client.send_template_message(
            to_phone,
            template_name,
            language_code,
            body_parameters,
        )

    async def get_media_url(self, media_id: str) -> Optional[str]:
        """Get media download URL from WhatsApp."""
        return await self.client.get_media_url(media_id)

    async def download_media(self, media_url: str) -> Optional[bytes]:
        """Download media content from WhatsApp."""
        return await self.client.download_media(media_url)

    async def get_media_metadata(self, media_id: str) -> Optional[Dict[str, Any]]:
        """Get media metadata from WhatsApp."""
        return await self.client.get_media_metadata(media_id)
