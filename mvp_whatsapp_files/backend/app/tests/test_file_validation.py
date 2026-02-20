"""Unit tests for PDF upload validation."""
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app.services.file_validation import MAX_PDF_SIZE_BYTES, sanitize_filename, validate_pdf_upload


def _upload(filename: str, content_type: str = "application/pdf") -> UploadFile:
    return UploadFile(
        filename=filename,
        file=BytesIO(b""),
        headers=Headers({"content-type": content_type}),
    )


def test_validate_pdf_upload_valid_pdf():
    upload = _upload("documento_final.pdf")
    content = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF"

    sanitized = validate_pdf_upload(upload, content)

    assert sanitized == "documento_final.pdf"


def test_validate_pdf_upload_invalid_mime():
    upload = _upload("doc.pdf", "image/png")
    content = b"%PDF-1.7\ncontent"

    with pytest.raises(HTTPException) as exc:
        validate_pdf_upload(upload, content)

    assert exc.value.status_code == 400
    assert "Invalid MIME type" in str(exc.value.detail)


def test_validate_pdf_upload_size_exceeded():
    upload = _upload("big.pdf")
    content = b"%PDF-" + (b"A" * MAX_PDF_SIZE_BYTES)

    with pytest.raises(HTTPException) as exc:
        validate_pdf_upload(upload, content)

    assert exc.value.status_code == 400
    assert "exceeds max size" in str(exc.value.detail)


def test_sanitize_filename_blocks_path_traversal():
    sanitized = sanitize_filename("../../etc/passwd")
    assert sanitized == "passwd.pdf"
