"""Tests for outbound WhatsApp send API."""
from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_send_text_success():
    repo = Mock()
    wa = Mock()

    repo.get_client_by_id.return_value = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "phone_number": "+34600111222",
    }
    wa.send_text_message = AsyncMock(return_value={"messages": [{"id": "wamid.test.123"}]})
    repo.create_conversation.return_value = {
        "id": "660e8400-e29b-41d4-a716-446655440000",
    }

    with patch("app.api.whatsapp.get_repository", return_value=repo), patch(
        "app.api.whatsapp.get_whatsapp_client", return_value=wa
    ):
        response = client.post(
            "/whatsapp/send-text",
            json={
                "client_id": "550e8400-e29b-41d4-a716-446655440000",
                "text": "Hola Carlos",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sent"
    assert data["phone_number"] == "+34600111222"
    assert data["whatsapp_message_id"] == "wamid.test.123"
    repo.create_conversation.assert_called_once()


def test_send_text_client_not_found():
    repo = Mock()
    wa = Mock()
    repo.get_client_by_id.return_value = None

    with patch("app.api.whatsapp.get_repository", return_value=repo), patch(
        "app.api.whatsapp.get_whatsapp_client", return_value=wa
    ):
        response = client.post(
            "/whatsapp/send-text",
            json={
                "client_id": "550e8400-e29b-41d4-a716-446655440000",
                "text": "Hola Carlos",
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found"


def test_send_text_provider_missing_message_id():
    repo = Mock()
    wa = Mock()
    repo.get_client_by_id.return_value = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "phone_number": "+34600111222",
    }
    wa.send_text_message = AsyncMock(return_value={"messages": []})

    with patch("app.api.whatsapp.get_repository", return_value=repo), patch(
        "app.api.whatsapp.get_whatsapp_client", return_value=wa
    ):
        response = client.post(
            "/whatsapp/send-text",
            json={
                "client_id": "550e8400-e29b-41d4-a716-446655440000",
                "text": "Hola Carlos",
            },
        )

    assert response.status_code == 502
    assert "message ID" in response.json()["detail"]


def test_send_template_success():
    repo = Mock()
    wa = Mock()

    repo.get_client_by_id.return_value = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "phone_number": "+34600111222",
    }
    wa.send_template_message = AsyncMock(return_value={"messages": [{"id": "wamid.tpl.123"}]})
    repo.create_conversation.return_value = {
        "id": "770e8400-e29b-41d4-a716-446655440000",
    }

    with patch("app.api.whatsapp.get_repository", return_value=repo), patch(
        "app.api.whatsapp.get_whatsapp_client", return_value=wa
    ):
        response = client.post(
            "/whatsapp/send-template",
            json={
                "client_id": "550e8400-e29b-41d4-a716-446655440000",
                "template_name": "recordatorio_documentos",
                "language_code": "es",
                "body_parameters": ["Carlos", "mañana 10:00"],
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sent"
    assert data["whatsapp_message_id"] == "wamid.tpl.123"
    repo.create_conversation.assert_called_once()
    wa.send_template_message.assert_called_once_with(
        "+34600111222",
        "recordatorio_documentos",
        "es",
        ["Carlos", "mañana 10:00"],
    )


def test_get_message_status_found():
    repo = Mock()
    repo.get_conversation_by_message_id.return_value = {
        "id": "880e8400-e29b-41d4-a716-446655440000",
        "client_id": "550e8400-e29b-41d4-a716-446655440000",
        "metadata": {
            "whatsapp_status": "read",
            "whatsapp_status_timestamp": "2026-02-20T20:00:00Z",
            "status_history": [{"status": "sent"}, {"status": "delivered"}, {"status": "read"}],
        },
    }
    wa = Mock()

    with patch("app.api.whatsapp.get_repository", return_value=repo), patch(
        "app.api.whatsapp.get_whatsapp_client", return_value=wa
    ):
        response = client.get("/whatsapp/message-status/wamid.test.status")

    assert response.status_code == 200
    data = response.json()
    assert data["found"] is True
    assert data["whatsapp_status"] == "read"
    assert len(data["status_history"]) == 3


def test_get_message_status_not_found():
    repo = Mock()
    repo.get_conversation_by_message_id.return_value = None
    wa = Mock()

    with patch("app.api.whatsapp.get_repository", return_value=repo), patch(
        "app.api.whatsapp.get_whatsapp_client", return_value=wa
    ):
        response = client.get("/whatsapp/message-status/wamid.unknown")

    assert response.status_code == 200
    data = response.json()
    assert data["found"] is False
    assert data["message_id"] == "wamid.unknown"
