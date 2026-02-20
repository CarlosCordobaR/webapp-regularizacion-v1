"""Base WhatsApp client interface."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class WhatsAppBase(ABC):
    """Abstract base class for WhatsApp API operations."""

    @abstractmethod
    async def send_text_message(self, to_phone: str, text: str) -> Optional[Dict[str, Any]]:
        """
        Send a text message through WhatsApp API.

        Args:
            to_phone: Destination phone number in E.164 format
            text: Message body

        Returns:
            Provider response dictionary or None if failed
        """
        pass

    @abstractmethod
    async def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        language_code: str = "es",
        body_parameters: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Send a template message through WhatsApp API.

        Args:
            to_phone: Destination phone number in E.164 format
            template_name: Template name approved in Meta
            language_code: Template language code (e.g. es, en_US)
            body_parameters: Optional text parameters for template body

        Returns:
            Provider response dictionary or None if failed
        """
        pass

    @abstractmethod
    async def get_media_url(self, media_id: str) -> Optional[str]:
        """
        Get media download URL from WhatsApp.
        
        Args:
            media_id: WhatsApp media ID
            
        Returns:
            Media download URL or None if failed
        """
        pass

    @abstractmethod
    async def download_media(self, media_url: str) -> Optional[bytes]:
        """
        Download media content.
        
        Args:
            media_url: Media download URL
            
        Returns:
            Media content as bytes or None if failed
        """
        pass

    @abstractmethod
    async def get_media_metadata(self, media_id: str) -> Optional[Dict[str, Any]]:
        """
        Get media metadata.
        
        Args:
            media_id: WhatsApp media ID
            
        Returns:
            Media metadata dictionary or None if failed
        """
        pass
