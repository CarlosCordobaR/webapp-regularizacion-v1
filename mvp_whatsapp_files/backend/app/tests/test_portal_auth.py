"""Tests for portal token helpers."""
from types import SimpleNamespace
from uuid import uuid4

from app.services.portal_auth import create_portal_token, verify_portal_token


def test_portal_token_roundtrip(monkeypatch):
    monkeypatch.setattr(
        "app.services.portal_auth.get_settings",
        lambda: SimpleNamespace(verify_token="test-secret", dev_token="dev"),
    )
    client_id = uuid4()
    token = create_portal_token(client_id, ttl_seconds=60)
    assert verify_portal_token(token, client_id) is True


def test_portal_token_rejects_wrong_client(monkeypatch):
    monkeypatch.setattr(
        "app.services.portal_auth.get_settings",
        lambda: SimpleNamespace(verify_token="test-secret", dev_token="dev"),
    )
    token = create_portal_token(uuid4(), ttl_seconds=60)
    assert verify_portal_token(token, uuid4()) is False

