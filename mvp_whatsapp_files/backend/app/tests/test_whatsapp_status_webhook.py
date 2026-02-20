"""Tests for outbound status processing from WhatsApp webhooks."""
from unittest.mock import Mock, patch

import pytest

from app.models.dto import WhatsAppWebhook
from app.whatsapp.webhook import WebhookHandler


def _status_webhook_payload(message_id: str, status: str = "delivered"):
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "entry-1",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551234567",
                                "phone_number_id": "1234567890",
                            },
                            "statuses": [
                                {
                                    "id": message_id,
                                    "status": status,
                                    "timestamp": "1739980000",
                                    "recipient_id": "34600111222",
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


@pytest.mark.asyncio
async def test_process_status_updates_conversation_metadata():
    repo = Mock()
    repo.get_conversation_by_message_id.return_value = {
        "id": "880e8400-e29b-41d4-a716-446655440000",
        "metadata": {"source": "api_whatsapp_send_text"},
    }
    repo.update_conversation.return_value = {
        "id": "880e8400-e29b-41d4-a716-446655440000",
    }

    with patch("app.whatsapp.webhook.get_repository", return_value=repo):
        handler = WebhookHandler()
        webhook = WhatsAppWebhook.model_validate(_status_webhook_payload("wamid.test.status", "read"))
        result = await handler.process_webhook(webhook)

    assert result["processed"] == 1
    assert result["results"][0]["status"] == "status_updated"
    assert result["results"][0]["whatsapp_status"] == "read"
    repo.update_conversation.assert_called_once()


@pytest.mark.asyncio
async def test_process_status_ignores_unknown_message_id():
    repo = Mock()
    repo.get_conversation_by_message_id.return_value = None

    with patch("app.whatsapp.webhook.get_repository", return_value=repo):
        handler = WebhookHandler()
        webhook = WhatsAppWebhook.model_validate(_status_webhook_payload("wamid.unknown", "delivered"))
        result = await handler.process_webhook(webhook)

    assert result["processed"] == 1
    assert result["results"][0]["status"] == "ignored"
    assert result["results"][0]["reason"] == "conversation_not_found"

