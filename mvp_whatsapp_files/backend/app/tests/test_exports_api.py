"""Tests for /clients/{id}/exports endpoint."""
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_export_job_staff_success():
    repo = Mock()
    storage = Mock()
    repo.create_export_job.return_value = {
        "id": "11111111-1111-1111-1111-111111111111",
        "status": "ready",
    }
    storage.get_file_url.return_value = "http://mock.local/signed.zip"

    with patch("app.api.clients.get_repository", return_value=repo), patch(
        "app.api.clients.get_storage", return_value=storage
    ), patch(
        "app.api.clients.generate_expediente_zip",
        return_value=(b"zip-bytes", "expediente_mock"),
    ), patch(
        "app.core.config.get_settings",
        return_value=SimpleNamespace(app_mode="mock"),
    ):
        response = client.post(
            "/clients/550e8400-e29b-41d4-a716-446655440000/exports",
            json={"accepted_only": True, "expires_in": 1200, "requested_by": "staff"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["accepted_only"] is True
    assert data["signed_url"]
    repo.create_export_job.assert_called_once()


def test_create_export_job_client_requires_portal_token():
    repo = Mock()
    storage = Mock()

    with patch("app.api.clients.get_repository", return_value=repo), patch(
        "app.api.clients.get_storage", return_value=storage
    ), patch(
        "app.api.clients.verify_portal_token", return_value=False
    ):
        response = client.post(
            "/clients/550e8400-e29b-41d4-a716-446655440000/exports",
            json={"accepted_only": True, "expires_in": 1200, "requested_by": "client"},
        )

    assert response.status_code == 401
    assert "portal token" in response.json()["detail"].lower()

