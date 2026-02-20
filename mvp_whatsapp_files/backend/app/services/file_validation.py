"""File validation helpers for secure PDF uploads."""
import re
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status

MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_PDF_MIME_TYPES = {"application/pdf"}
SAFE_FILENAME_PATTERN = re.compile(r"[^a-zA-Z0-9._-]")


def sanitize_filename(filename: Optional[str]) -> str:
    """Return a safe filename without directory traversal or unsafe chars."""
    raw_name = (filename or "").strip()
    base_name = Path(raw_name).name

    if not base_name:
        return "document.pdf"

    sanitized = SAFE_FILENAME_PATTERN.sub("_", base_name)

    # Keep expected extension for typed PDF uploads.
    if not sanitized.lower().endswith(".pdf"):
        sanitized = f"{sanitized}.pdf"

    return sanitized


def _is_pdf_signature(file_content: bytes) -> bool:
    """Check PDF signature allowing an optional binary preamble."""
    if not file_content:
        return False
    # PDF header can appear after a short preamble in some producers.
    return b"%PDF-" in file_content[:1024]


def validate_pdf_upload(
    upload_file: UploadFile,
    file_content: bytes,
    *,
    max_size_bytes: int = MAX_PDF_SIZE_BYTES
) -> str:
    """
    Validate uploaded file as a safe PDF.

    Returns:
        Sanitized filename
    """
    sanitized_name = sanitize_filename(upload_file.filename)

    if len(file_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{sanitized_name}: Empty file"
        )

    if len(file_content) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{sanitized_name}: File exceeds max size ({max_size_bytes // (1024 * 1024)}MB)"
        )

    if upload_file.content_type not in ALLOWED_PDF_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{sanitized_name}: Invalid MIME type '{upload_file.content_type}'"
        )

    if not _is_pdf_signature(file_content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{sanitized_name}: Invalid PDF signature"
        )

    return sanitized_name
