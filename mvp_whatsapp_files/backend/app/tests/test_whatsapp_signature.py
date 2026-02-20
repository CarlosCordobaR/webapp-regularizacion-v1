"""Tests for WhatsApp webhook signature verification."""
import hashlib
import hmac
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.whatsapp.verify import verify_webhook_signature


def _signature(secret: str, payload: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_verify_signature_skips_when_secret_not_configured(monkeypatch):
    payload = b'{"object":"whatsapp_business_account"}'
    monkeypatch.setattr(
        "app.whatsapp.verify.get_settings",
        lambda: SimpleNamespace(whatsapp_app_secret=None),
    )

    # No exception expected when secret is missing.
    verify_webhook_signature(payload, None)


def test_verify_signature_rejects_missing_header(monkeypatch):
    payload = b'{"object":"whatsapp_business_account"}'
    monkeypatch.setattr(
        "app.whatsapp.verify.get_settings",
        lambda: SimpleNamespace(whatsapp_app_secret="top-secret"),
    )

    with pytest.raises(HTTPException) as exc:
        verify_webhook_signature(payload, None)

    assert exc.value.status_code == 401
    assert "Missing X-Hub-Signature-256" in exc.value.detail


def test_verify_signature_rejects_invalid_header_format(monkeypatch):
    payload = b'{"object":"whatsapp_business_account"}'
    monkeypatch.setattr(
        "app.whatsapp.verify.get_settings",
        lambda: SimpleNamespace(whatsapp_app_secret="top-secret"),
    )

    with pytest.raises(HTTPException) as exc:
        verify_webhook_signature(payload, "bad-header")

    assert exc.value.status_code == 401
    assert "Invalid X-Hub-Signature-256 format" in exc.value.detail


def test_verify_signature_rejects_invalid_signature(monkeypatch):
    payload = b'{"object":"whatsapp_business_account"}'
    monkeypatch.setattr(
        "app.whatsapp.verify.get_settings",
        lambda: SimpleNamespace(whatsapp_app_secret="top-secret"),
    )

    with pytest.raises(HTTPException) as exc:
        verify_webhook_signature(payload, "sha256=deadbeef")

    assert exc.value.status_code == 401
    assert "Invalid webhook signature" in exc.value.detail


def test_verify_signature_accepts_valid_signature(monkeypatch):
    payload = b'{"object":"whatsapp_business_account"}'
    secret = "top-secret"
    monkeypatch.setattr(
        "app.whatsapp.verify.get_settings",
        lambda: SimpleNamespace(whatsapp_app_secret=secret),
    )

    verify_webhook_signature(payload, _signature(secret, payload))

