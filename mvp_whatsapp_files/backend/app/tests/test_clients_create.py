"""Tests for client creation endpoint."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app

client = TestClient(app)


# Mock repository for testing
@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    with patch('app.api.clients.get_repository') as mock:
        repo = Mock()
        mock.return_value = repo
        yield repo


class TestCreateClient:
    """Test cases for POST /clients endpoint."""

    def test_create_client_success(self, mock_repository):
        """Test successful client creation."""
        # Mock repository response
        mock_repository.create_client.return_value = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Juan Perez",
            "phone_number": "+34600111222",
            "profile_type": "ARRAIGO",
            "status": "active",
            "metadata": {},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        # Make request
        response = client.post(
            "/clients",
            json={
                "full_name": "Juan Perez",
                "phone_number": "+34600111222",
                "profile_type": "ARRAIGO"
            }
        )
        
        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Juan Perez"
        assert data["phone_number"] == "+34600111222"
        assert data["profile_type"] == "ARRAIGO"
        
        # Verify repository was called correctly
        mock_repository.create_client.assert_called_once()
        call_args = mock_repository.create_client.call_args[0][0]
        assert call_args["name"] == "Juan Perez"
        assert call_args["phone_number"] == "+34600111222"

    def test_create_client_duplicate_phone(self, mock_repository):
        """Test client creation with duplicate phone number returns 409."""
        # Mock repository to raise ValueError for duplicate
        mock_repository.create_client.side_effect = ValueError(
            "Phone number +34600111222 already exists"
        )
        
        # Make request
        response = client.post(
            "/clients",
            json={
                "full_name": "Juan Perez",
                "phone_number": "+34600111222",
                "profile_type": "ASYLUM"
            }
        )
        
        # Assertions
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_create_client_invalid_phone_format(self):
        """Test client creation with invalid phone format returns 400."""
        # Make request with invalid phone (too short)
        response = client.post(
            "/clients",
            json={
                "full_name": "Juan Perez",
                "phone_number": "123",  # Too short
                "profile_type": "OTHER"
            }
        )
        
        # Assertions
        assert response.status_code == 422  # Pydantic validation error
        
    def test_create_client_invalid_phone_characters(self):
        """Test client creation with invalid phone characters returns 400."""
        # Make request with invalid phone (letters)
        response = client.post(
            "/clients",
            json={
                "full_name": "Juan Perez",
                "phone_number": "ABC123DEF456",
                "profile_type": "OTHER"
            }
        )
        
        # Assertions
        assert response.status_code == 422  # Pydantic validation error

    def test_create_client_missing_required_fields(self):
        """Test client creation without required fields returns 422."""
        # Missing full_name
        response = client.post(
            "/clients",
            json={
                "phone_number": "+34600111222"
            }
        )
        
        assert response.status_code == 422
        
    def test_create_client_with_notes(self, mock_repository):
        """Test client creation with optional notes."""
        mock_repository.create_client.return_value = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Maria Lopez",
            "phone_number": "+34611222333",
            "profile_type": "STUDENT",
            "status": "active",
            "metadata": {"notes": "Referred by existing client"},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        response = client.post(
            "/clients",
            json={
                "full_name": "Maria Lopez",
                "phone_number": "+34611222333",
                "profile_type": "STUDENT",
                "notes": "Referred by existing client"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["metadata"].get("notes") == "Referred by existing client"

    def test_create_client_phone_normalization(self, mock_repository):
        """Test that phone numbers are normalized (spaces removed)."""
        mock_repository.create_client.return_value = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Test User",
            "phone_number": "+34600111222",
            "profile_type": "OTHER",
            "status": "active",
            "metadata": {},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        # Send phone with spaces
        response = client.post(
            "/clients",
            json={
                "full_name": "Test User",
                "phone_number": "+34 600 111 222",  # Spaces
                "profile_type": "OTHER"
            }
        )
        
        assert response.status_code == 201
        # Verify normalized phone was sent to repository
        call_args = mock_repository.create_client.call_args[0][0]
        assert call_args["phone_number"] == "+34600111222"

    def test_create_client_default_values(self, mock_repository):
        """Test that default values are applied correctly."""
        mock_repository.create_client.return_value = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Default User",
            "phone_number": "+34622333444",
            "profile_type": "OTHER",
            "status": "active",
            "metadata": {},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        # Only send required fields
        response = client.post(
            "/clients",
            json={
                "full_name": "Default User",
                "phone_number": "+34622333444"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["profile_type"] == "OTHER"  # Default
        assert data["status"] == "active"  # Default

    def test_create_client_trim_whitespace(self, mock_repository):
        """Test that full_name whitespace is trimmed."""
        mock_repository.create_client.return_value = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Trimmed Name",
            "phone_number": "+34633444555",
            "profile_type": "OTHER",
            "status": "active",
            "metadata": {},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        response = client.post(
            "/clients",
            json={
                "full_name": "  Trimmed Name  ",  # Extra whitespace
                "phone_number": "+34633444555"
            }
        )
        
        assert response.status_code == 201
        # Verify trimmed name was sent to repository
        call_args = mock_repository.create_client.call_args[0][0]
        assert call_args["name"] == "Trimmed Name"
