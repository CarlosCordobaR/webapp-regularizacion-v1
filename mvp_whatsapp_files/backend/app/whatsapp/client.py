"""WhatsApp Graph API client module."""
from typing import Dict, Any, List, Optional
import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class WhatsAppClient:
    """WhatsApp Graph API client."""

    def __init__(self):
        """Initialize WhatsApp client."""
        self.settings = get_settings()
        self.base_url = "https://graph.facebook.com/v18.0"
        self.headers = {
            "Authorization": f"Bearer {self.settings.whatsapp_token}"
        }

    async def send_text_message(self, to_phone: str, text: str) -> Optional[Dict[str, Any]]:
        """
        Send outbound text message via WhatsApp Cloud API.

        Args:
            to_phone: Recipient phone number in E.164 format
            text: Message body

        Returns:
            Provider response JSON or None on failure
        """
        if not self.settings.whatsapp_phone_number_id:
            logger.error("WHATSAPP_PHONE_NUMBER_ID is not configured")
            return None

        url = f"{self.base_url}/{self.settings.whatsapp_phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": text},
        }
        headers = {
            **self.headers,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.media_download_timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error sending WhatsApp text to {to_phone}: {e}")
            return None

    async def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        language_code: str = "es",
        body_parameters: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Send outbound template message via WhatsApp Cloud API.
        """
        if not self.settings.whatsapp_phone_number_id:
            logger.error("WHATSAPP_PHONE_NUMBER_ID is not configured")
            return None

        url = f"{self.base_url}/{self.settings.whatsapp_phone_number_id}/messages"
        template_payload: Dict[str, Any] = {
            "name": template_name,
            "language": {"code": language_code},
        }
        if body_parameters:
            template_payload["components"] = [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": value} for value in body_parameters],
                }
            ]

        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": template_payload,
        }
        headers = {
            **self.headers,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.media_download_timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error sending WhatsApp template '{template_name}' to {to_phone}: {e}")
            return None

    async def get_media_url(self, media_id: str) -> Optional[str]:
        """
        Get media download URL from WhatsApp.
        
        Args:
            media_id: WhatsApp media ID
            
        Returns:
            Media download URL or None if failed
        """
        url = f"{self.base_url}/{media_id}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                return data.get("url")
        except Exception as e:
            logger.error(f"Error getting media URL for {media_id}: {e}")
            return None

    async def download_media(self, media_url: str) -> Optional[bytes]:
        """
        Download media content from WhatsApp.
        
        Args:
            media_url: Media download URL from WhatsApp
            
        Returns:
            Media content as bytes or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=self.settings.media_download_timeout) as client:
                response = await client.get(media_url, headers=self.headers)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Error downloading media from {media_url}: {e}")
            return None

    async def get_media_metadata(self, media_id: str) -> Optional[Dict[str, Any]]:
        """
        Get media metadata from WhatsApp.
        
        Args:
            media_id: WhatsApp media ID
            
        Returns:
            Media metadata dictionary or None if failed
        """
        url = f"{self.base_url}/{media_id}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting media metadata for {media_id}: {e}")
            return None
