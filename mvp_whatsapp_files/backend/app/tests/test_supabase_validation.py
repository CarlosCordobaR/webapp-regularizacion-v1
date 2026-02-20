"""
Integration tests for Supabase validation mode.

These tests are OPTIONAL and only run when:
  RUN_SUPABASE_INTEGRATION_TESTS=true

They require a configured Supabase instance and are designed to run
against a real Supabase database/storage.

To run:
  export RUN_SUPABASE_INTEGRATION_TESTS=true
  export APP_MODE=real
  export SUPABASE_URL=https://your-project.supabase.co
  export SUPABASE_SERVICE_ROLE_KEY=your-key
  export DEV_ENDPOINTS_ENABLED=true
  export DEV_TOKEN=test-token
  pytest app/tests/test_supabase_validation.py -v
"""
import os
import pytest
from uuid import uuid4

# Skip all tests in this module if environment flag not set
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_SUPABASE_INTEGRATION_TESTS") != "true",
    reason="Supabase integration tests are opt-in. Set RUN_SUPABASE_INTEGRATION_TESTS=true to run."
)


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


@pytest.fixture
def dev_headers():
    """Get dev endpoint authentication headers."""
    return {"X-Dev-Token": os.getenv("DEV_TOKEN", "test-token")}


class TestSupabaseValidation:
    """Integration tests for Supabase-only validation mode."""
    
    def test_health_check(self, test_client):
        """Test that the API is running."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_seed_endpoint_creates_clients(self, test_client, dev_headers):
        """Test /dev/seed endpoint creates test data in Supabase."""
        response = test_client.post("/dev/seed", headers=dev_headers)
        
        assert response.status_code == 200, f"Seed failed: {response.text}"
        
        data = response.json()
        assert data["clients_created"] >= 0  # May be 0 if already seeded
        assert "conversations_created" in data
        assert "documents_created" in data
        assert "message" in data
    
    def test_list_clients_after_seed(self, test_client):
        """Test that we can list clients after seeding."""
        # First seed data
        dev_headers = {"X-Dev-Token": os.getenv("DEV_TOKEN", "test-token")}
        test_client.post("/dev/seed", headers=dev_headers)
        
        # Then list clients
        response = test_client.get("/clients?page=1&page_size=20")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert data["total"] > 0, "No clients found after seeding"
    
    def test_create_and_fetch_client(self, test_client):
        """Test creating a client and fetching it back."""
        # Create a unique client
        phone = f"+34600{uuid4().hex[:6]}"
        client_data = {
            "phone_number": phone,
            "name": "Test Client Integration",
            "email": f"integration-{uuid4().hex[:6]}@test.com",
            "profile_type": "OTHER",
            "passport_or_nie": f"TEST-{uuid4().hex[:8].upper()}"
        }
        
        response = test_client.post("/clients", json=client_data)
        assert response.status_code == 201, f"Create client failed: {response.text}"
        
        created = response.json()
        assert created["phone_number"] == phone
        assert created["name"] == client_data["name"]
        client_id = created["id"]
        
        # Fetch the client back
        response = test_client.get(f"/clients/{client_id}")
        assert response.status_code == 200
        fetched = response.json()
        assert fetched["id"] == client_id
        assert fetched["phone_number"] == phone
    
    def test_create_conversation_via_dev_endpoint(self, test_client, dev_headers):
        """Test creating a conversation without WhatsApp."""
        # First, create a client
        phone = f"+34600{uuid4().hex[:6]}"
        client_data = {
            "phone_number": phone,
            "name": "Test Conversation Client",
            "profile_type": "OTHER",
            "passport_or_nie": "TEST-CONV"
        }
        
        response = test_client.post("/clients", json=client_data)
        assert response.status_code == 201
        client_id = response.json()["id"]
        
        # Create a test conversation
        conversation_data = {
            "client_id": client_id,
            "direction": "inbound",
            "message_text": "This is a test inbound message",
            "message_type": "text"
        }
        
        response = test_client.post("/dev/conversations", json=conversation_data, headers=dev_headers)
        assert response.status_code == 200, f"Create conversation failed: {response.text}"
        
        data = response.json()
        assert "conversation_id" in data
        assert "message" in data
        
        # Verify we can fetch conversations for this client
        response = test_client.get(f"/clients/{client_id}/conversations")
        assert response.status_code == 200
        conversations = response.json()
        assert len(conversations["data"]) > 0
        assert any(c["content"] == "This is a test inbound message" for c in conversations["data"])
    
    def test_upload_document_via_dev_endpoint(self, test_client, dev_headers):
        """Test uploading a document without WhatsApp."""
        # Create a client first
        phone = f"+34600{uuid4().hex[:6]}"
        client_data = {
            "phone_number": phone,
            "name": "Test Document Client",
            "profile_type": "ASYLUM",
            "passport_or_nie": "TEST-DOC"
        }
        
        response = test_client.post("/clients", json=client_data)
        assert response.status_code == 201
        client_id = response.json()["id"]
        
        # Create a test PDF file
        pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n149\n%%EOF"
        
        files = {"file": ("test_tasa.pdf", pdf_content, "application/pdf")}
        data = {"client_id": client_id, "document_type": "TASA"}
        
        response = test_client.post("/dev/documents/upload", files=files, data=data, headers=dev_headers)
        assert response.status_code == 200, f"Upload document failed: {response.text}"
        
        upload_result = response.json()
        assert "document_id" in upload_result
        assert "storage_path" in upload_result
        
        # Verify document appears in client's documents
        response = test_client.get(f"/clients/{client_id}/documents")
        assert response.status_code == 200
        documents = response.json()
        assert documents["total"] > 0
        assert any(d["document_type"] == "TASA" for d in documents["data"])
    
    def test_document_signed_url(self, test_client, dev_headers):
        """Test that we can get a signed URL for a document."""
        # Create client and upload document
        phone = f"+34600{uuid4().hex[:6]}"
        client_data = {
            "phone_number": phone,
            "name": "Test Signed URL Client",
            "profile_type": "OTHER",
            "passport_or_nie": "TEST-SIGNED"
        }
        
        response = test_client.post("/clients", json=client_data)
        assert response.status_code == 201
        client_id = response.json()["id"]
        
        # Upload a document
        pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n149\n%%EOF"
        files = {"file": ("test_passport.pdf", pdf_content, "application/pdf")}
        data = {"client_id": client_id, "document_type": "PASSPORT_NIE"}
        
        response = test_client.post("/dev/documents/upload", files=files, data=data, headers=dev_headers)
        assert response.status_code == 200
        document_id = response.json()["document_id"]
        
        # Get signed URL
        response = test_client.get(f"/documents/{document_id}/signed-url?expires_in=3600")
        assert response.status_code == 200
        
        signed_url_data = response.json()
        assert "url" in signed_url_data
        assert "expires_in" in signed_url_data
        assert signed_url_data["url"].startswith("http")
    
    def test_dev_token_protection(self, test_client):
        """Test that dev endpoints require correct DEV_TOKEN."""
        # Try without token
        response = test_client.post("/dev/seed")
        assert response.status_code == 422  # Missing header
        
        # Try with wrong token
        bad_headers = {"X-Dev-Token": "wrong-token"}
        response = test_client.post("/dev/seed", headers=bad_headers)
        assert response.status_code == 401


@pytest.mark.skipif(
    os.getenv("RUN_SUPABASE_INTEGRATION_TESTS") != "true",
    reason="Supabase integration tests are opt-in"
)
def test_environment_configuration():
    """Test that required environment variables are configured."""
    assert os.getenv("APP_MODE") == "real", "APP_MODE must be 'real' for integration tests"
    assert os.getenv("SUPABASE_URL"), "SUPABASE_URL must be set"
    assert os.getenv("SUPABASE_SERVICE_ROLE_KEY"), "SUPABASE_SERVICE_ROLE_KEY must be set"
    assert os.getenv("DEV_ENDPOINTS_ENABLED") == "true", "DEV_ENDPOINTS_ENABLED must be 'true'"
    assert os.getenv("DEV_TOKEN"), "DEV_TOKEN must be set"
