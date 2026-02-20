"""Portal token creation/validation for client-facing expediente route."""
import base64
import hashlib
import hmac
import json
import time
from typing import Optional
from uuid import UUID

from app.core.config import get_settings


def _token_secret() -> str:
    settings = get_settings()
    # Reuse existing secrets to avoid introducing extra env configuration for MVP.
    return settings.verify_token or settings.dev_token or "portal-secret-change-me"


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + padding)


def create_portal_token(client_id: UUID, ttl_seconds: int = 3600) -> str:
    """Create a signed portal token bound to a specific client ID."""
    payload = {
        "client_id": str(client_id),
        "exp": int(time.time()) + ttl_seconds,
    }
    encoded_payload = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(
        _token_secret().encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{encoded_payload}.{signature}"


def verify_portal_token(token: str, expected_client_id: UUID) -> bool:
    """Verify portal token integrity, expiration and client binding."""
    try:
        payload_b64, provided_signature = token.split(".", 1)
        expected_signature = hmac.new(
            _token_secret().encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(provided_signature, expected_signature):
            return False

        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        if payload.get("client_id") != str(expected_client_id):
            return False

        exp = payload.get("exp")
        if not isinstance(exp, int) or exp < int(time.time()):
            return False
        return True
    except Exception:
        return False


def token_expiration(token: str) -> Optional[int]:
    """Return UNIX expiration for a token when parseable."""
    try:
        payload_b64, _ = token.split(".", 1)
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        exp = payload.get("exp")
        return exp if isinstance(exp, int) else None
    except Exception:
        return None

