"""
Integration tests for Supabase sync functionality.

These tests are OPT-IN via ENABLE_INTEGRATION_TESTS environment variable.
They require a real Supabase instance with proper credentials.

Run with:
    ENABLE_INTEGRATION_TESTS=1 SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... pytest app/tests/test_sync_integration.py -v
"""
import os
import pytest
from uuid import uuid4

from app.db.supabase import get_supabase_client


# Skip all tests unless explicitly enabled
pytestmark = pytest.mark.skipif(
    not os.getenv("ENABLE_INTEGRATION_TESTS"),
    reason="Integration tests disabled. Set ENABLE_INTEGRATION_TESTS=1 to run."
)


@pytest.fixture
def supabase_client():
    """Get Supabase client for testing."""
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        pytest.skip("Supabase credentials not configured")
    
    return get_supabase_client()


@pytest.fixture
def test_client_data():
    """Generate unique test client data."""
    unique_id = str(uuid4())[:8]
    return {
        "phone_number": f"+34900{unique_id}",
        "name": f"Test Client {unique_id}",
        "profile_type": "OTHER",
        "status": "active",
        "metadata": {"test": True}
    }


class TestSupabaseIntegration:
    """Integration tests for Supabase operations."""
    
    def test_client_upsert_creates_new(self, supabase_client, test_client_data):
        """Test that upsert creates a new client."""
        result = supabase_client.upsert_client(test_client_data)
        
        assert result is not None
        assert result["phone_number"] == test_client_data["phone_number"]
        assert result["name"] == test_client_data["name"]
        assert "id" in result
        
        # Cleanup
        try:
            supabase_client.client.table("clients").delete().eq(
                "phone_number", test_client_data["phone_number"]
            ).execute()
        except Exception:
            pass  # Best effort cleanup
    
    def test_client_upsert_updates_existing(self, supabase_client, test_client_data):
        """Test that upsert updates an existing client."""
        # Create initial client
        result1 = supabase_client.upsert_client(test_client_data)
        client_id = result1["id"]
        
        # Update with same phone number
        updated_data = test_client_data.copy()
        updated_data["name"] = "Updated Name"
        result2 = supabase_client.upsert_client(updated_data)
        
        assert result2["id"] == client_id  # Same ID
        assert result2["name"] == "Updated Name"  # Updated name
        
        # Cleanup
        try:
            supabase_client.client.table("clients").delete().eq(
                "phone_number", test_client_data["phone_number"]
            ).execute()
        except Exception:
            pass
    
    def test_dedupe_key_generation(self, supabase_client):
        """Test dedupe key generation for idempotency."""
        # Same inputs should produce same key
        key1 = supabase_client.generate_dedupe_key(
            client_id="test-id",
            direction="INBOUND",
            created_at="2024-01-01T00:00:00",
            message_type="text",
            content="Hello world"
        )
        
        key2 = supabase_client.generate_dedupe_key(
            client_id="test-id",
            direction="INBOUND",
            created_at="2024-01-01T00:00:00",
            message_type="text",
            content="Hello world"
        )
        
        assert key1 == key2
        assert len(key1) <= 64  # Fits in VARCHAR(64)
        
        # Different content should produce different key
        key3 = supabase_client.generate_dedupe_key(
            client_id="test-id",
            direction="INBOUND",
            created_at="2024-01-01T00:00:00",
            message_type="text",
            content="Different message"
        )
        
        assert key3 != key1
    
    def test_bucket_exists_check(self, supabase_client):
        """Test that storage bucket exists check works."""
        # This will raise if bucket doesn't exist
        result = supabase_client.ensure_bucket_exists()
        assert result is True


class TestSyncIdempotency:
    """Tests for sync script idempotency."""
    
    def test_conversation_dedupe(self, supabase_client, test_client_data):
        """Test that conversations with same dedupe_key are not duplicated."""
        # Create test client
        client = supabase_client.upsert_client(test_client_data)
        client_id = client["id"]
        
        # Create conversation data
        dedupe_key = supabase_client.generate_dedupe_key(
            client_id=client_id,
            direction="INBOUND",
            created_at="2024-01-01T00:00:00",
            message_type="text",
            content="Test message"
        )
        
        conv_data = {
            "client_id": client_id,
            "message_id": f"test_{uuid4()}",
            "direction": "INBOUND",
            "content": "Test message",
            "message_type": "text",
            "dedupe_key": dedupe_key
        }
        
        # Insert first time
        result1 = supabase_client.upsert_conversation(conv_data)
        conv_id = result1["id"]
        
        # Try to insert again with same dedupe_key
        result2 = supabase_client.upsert_conversation(conv_data)
        
        # Should return existing conversation
        assert result2["id"] == conv_id
        
        # Cleanup
        try:
            supabase_client.client.table("conversations").delete().eq("id", conv_id).execute()
            supabase_client.client.table("clients").delete().eq("id", client_id).execute()
        except Exception:
            pass


@pytest.mark.skipif(
    not os.getenv("ENABLE_INTEGRATION_TESTS"),
    reason="Integration tests disabled"
)
def test_integration_environment_check():
    """Verify integration test environment is properly configured."""
    assert os.getenv("SUPABASE_URL"), "SUPABASE_URL not set"
    assert os.getenv("SUPABASE_SERVICE_ROLE_KEY"), "SUPABASE_SERVICE_ROLE_KEY not set"
    assert os.getenv("STORAGE_BUCKET"), "STORAGE_BUCKET not set"
