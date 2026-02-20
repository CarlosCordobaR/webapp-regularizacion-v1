"""WhatsApp webhook verification module."""
import hashlib
import hmac
from typing import Optional

from fastapi import HTTPException, Query

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
) -> str:
    """
    Verify WhatsApp webhook.
    
    This endpoint is called by Meta to verify the webhook URL.
    It must return the challenge value if the verify token matches.
    """
    settings = get_settings()
    
    logger.info(f"Webhook verification request: mode={mode}")
    
    if mode == "subscribe" and token == settings.verify_token:
        logger.info("Webhook verification successful")
        return challenge
    
    logger.warning("Webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


def verify_webhook_signature(
    payload: bytes,
    signature_header: Optional[str],
) -> None:
    """
    Validate X-Hub-Signature-256 for webhook payload integrity.

    If WHATSAPP_APP_SECRET is not configured, signature validation is skipped.
    """
    settings = get_settings()
    app_secret = settings.whatsapp_app_secret

    if not app_secret:
        return

    if not signature_header:
        raise HTTPException(status_code=401, detail="Missing X-Hub-Signature-256 header")

    if not signature_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Invalid X-Hub-Signature-256 format")

    provided_signature = signature_header.split("=", 1)[1].strip().lower()
    expected_signature = hmac.new(
        app_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(provided_signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
