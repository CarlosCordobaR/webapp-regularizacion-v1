"""Test health endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint returns ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data


def test_health_check_structure():
    """Test health check response structure."""
    response = client.get("/health")
    data = response.json()
    assert isinstance(data, dict)
    assert "status" in data
    assert "service" in data
