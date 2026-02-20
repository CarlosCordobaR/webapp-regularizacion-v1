"""Tests for expediente export accepted-only behavior."""
import io
import zipfile
from uuid import uuid4

import pytest

from app.services.expediente import MissingDocumentsError, generate_expediente_zip


class _RepoStub:
    def __init__(self, docs):
        self.docs = docs

    def get_client_by_id(self, _client_id):
        return {
            "id": str(_client_id),
            "name": "Carlos Smoke",
            "passport_or_nie": "X1234567A",
        }

    def get_client_documents(self, _client_id):
        return self.docs


def test_generate_expediente_zip_accepted_only_missing(monkeypatch):
    client_id = uuid4()
    docs = [
        {"document_type": "TASA", "storage_path": "a.pdf", "metadata": {"review_status": "uploaded"}},
        {"document_type": "PASSPORT_NIE", "storage_path": "b.pdf", "metadata": {"review_status": "rejected"}},
    ]
    monkeypatch.setattr("app.services.expediente.get_repository", lambda: _RepoStub(docs))
    monkeypatch.setattr("app.services.expediente.get_storage", lambda: object())

    with pytest.raises(MissingDocumentsError) as exc:
        generate_expediente_zip(client_id, accepted_only=True)

    assert "TASA_ACCEPTED" in exc.value.missing
    assert "PASSPORT_NIE_ACCEPTED" in exc.value.missing


def test_generate_expediente_zip_accepted_only_success(monkeypatch):
    client_id = uuid4()
    docs = [
        {"document_type": "TASA", "storage_path": "a.pdf", "metadata": {"review_status": "accepted"}},
        {"document_type": "PASSPORT_NIE", "storage_path": "b.pdf", "metadata": {"review_status": "accepted"}},
    ]
    monkeypatch.setattr("app.services.expediente.get_repository", lambda: _RepoStub(docs))
    monkeypatch.setattr("app.services.expediente.get_storage", lambda: object())
    monkeypatch.setattr(
        "app.services.expediente._download_file_from_storage",
        lambda _storage, _path: b"%PDF-1.4\n%%EOF",
    )

    zip_bytes, folder_name = generate_expediente_zip(client_id, accepted_only=True)
    assert folder_name.startswith("carlos_smoke_")
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        names = zf.namelist()
    assert any(name.endswith("/Tasa_carlos_smoke.pdf") for name in names)
    assert any(name.endswith("/NIE_carlos_smoke.pdf") for name in names)

