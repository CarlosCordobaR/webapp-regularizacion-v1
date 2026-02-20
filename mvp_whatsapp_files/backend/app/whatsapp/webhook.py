"""WhatsApp webhook handler module."""
from datetime import datetime, timezone
from typing import Optional

from app.adapters.factory import get_repository
from app.core.logging import get_logger
from app.models.dto import WhatsAppWebhook, WhatsAppMessage, WhatsAppMediaMessage
from app.models.enums import MessageDirection
from app.services.ingest import IngestService

logger = get_logger(__name__)


class WebhookHandler:
    """Handle incoming WhatsApp webhooks."""

    def __init__(self):
        """Initialize webhook handler."""
        self.repository = get_repository()
        self.ingest_service = IngestService()

    async def process_webhook(self, webhook: WhatsAppWebhook) -> dict:
        """
        Process incoming WhatsApp webhook.
        
        Args:
            webhook: Parsed webhook payload
            
        Returns:
            Processing result summary
        """
        results = []
        
        for entry in webhook.entry:
            for change in entry.changes:
                if change.field != "messages":
                    continue
                
                value = change.value
                
                # Process messages
                if value.messages:
                    for message in value.messages:
                        try:
                            # Get contact info
                            contact_name = None
                            if value.contacts:
                                contact = next(
                                    (c for c in value.contacts if c.wa_id == message.from_),
                                    None
                                )
                                if contact:
                                    contact_name = contact.profile.name
                            
                            # Process message
                            result = await self._process_message(
                                message=message,
                                phone_number=message.from_,
                                contact_name=contact_name
                            )
                            results.append(result)
                        except Exception as e:
                            logger.error(f"Error processing message {message.id}: {e}")
                            results.append({"error": str(e), "message_id": message.id})

                # Process outbound statuses
                if value.statuses:
                    for status in value.statuses:
                        try:
                            result = await self._process_status(status.id, status.status, status.timestamp)
                            results.append(result)
                        except Exception as e:
                            logger.error(f"Error processing status for {status.id}: {e}")
                            results.append({"error": str(e), "message_id": status.id, "status": status.status})
        
        return {
            "processed": len(results),
            "results": results
        }

    async def _process_status(
        self,
        message_id: str,
        status: str,
        timestamp: Optional[str],
    ) -> dict:
        """Process outbound status update and persist it on conversation metadata."""
        conversation = self.repository.get_conversation_by_message_id(message_id)
        if not conversation:
            logger.info(f"Status received for unknown message_id={message_id}, status={status}")
            return {"status": "ignored", "message_id": message_id, "reason": "conversation_not_found"}

        metadata = conversation.get("metadata", {}) or {}
        metadata["whatsapp_status"] = status
        metadata["whatsapp_status_timestamp"] = timestamp or datetime.now(timezone.utc).isoformat()
        status_history = metadata.get("status_history", [])
        status_history.append(
            {
                "status": status,
                "timestamp": metadata["whatsapp_status_timestamp"],
            }
        )
        metadata["status_history"] = status_history[-20:]

        updated = self.repository.update_conversation(conversation_id=conversation["id"], update_data={"metadata": metadata})
        return {
            "status": "status_updated",
            "message_id": message_id,
            "conversation_id": updated["id"],
            "whatsapp_status": status,
        }

    async def _process_message(
        self,
        message: WhatsAppMessage,
        phone_number: str,
        contact_name: Optional[str]
    ) -> dict:
        """
        Process individual WhatsApp message.
        
        Args:
            message: WhatsApp message object
            phone_number: Sender phone number
            contact_name: Sender name from contact profile
            
        Returns:
            Processing result
        """
        # Check if message already processed
        existing = self.repository.get_conversation_by_message_id(message.id)
        if existing:
            logger.info(f"Message {message.id} already processed")
            return {"status": "duplicate", "message_id": message.id}
        
        # Get or create client
        client = await self.ingest_service.get_or_create_client(
            phone_number=phone_number,
            name=contact_name
        )
        
        # Extract message content
        content = None
        if message.text:
            content = message.text.body
        elif message.document and message.document.caption:
            content = message.document.caption
        
        # Store conversation
        conversation = await self.ingest_service.store_conversation(
            client_id=client["id"],
            message_id=message.id,
            direction=MessageDirection.INBOUND,
            content=content,
            message_type=message.type,
            timestamp=message.timestamp
        )
        
        # Classify profile if text message with content
        if content:
            await self.ingest_service.classify_and_update_profile(
                client_id=client["id"],
                text=content
            )
        
        # Handle media if present
        media_result = None
        media: Optional[WhatsAppMediaMessage] = None
        
        if message.type == "document" and message.document:
            media = message.document
        elif message.type == "image" and message.image:
            media = message.image
        elif message.type == "audio" and message.audio:
            media = message.audio
        elif message.type == "video" and message.video:
            media = message.video
        
        if media:
            try:
                media_result = await self.ingest_service.process_and_store_media(
                    client_id=client["id"],
                    conversation_id=conversation["id"],
                    media_id=media.id,
                    mime_type=media.mime_type,
                    filename=media.filename
                )
            except Exception as e:
                logger.error(f"Error processing media for message {message.id}: {e}")
                media_result = {"error": str(e)}
        
        return {
            "status": "success",
            "message_id": message.id,
            "client_id": client["id"],
            "conversation_id": conversation["id"],
            "media_processed": media_result is not None
        }
