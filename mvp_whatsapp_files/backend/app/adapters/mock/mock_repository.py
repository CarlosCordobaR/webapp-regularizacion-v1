"""Mock repository implementation using SQLite."""
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from app.adapters.repository_base import RepositoryBase
from app.core.logging import get_logger

logger = get_logger(__name__)


class MockRepository(RepositoryBase):
    """SQLite-based mock repository for local development."""

    def __init__(self, db_path: str = "backend/.local_storage/mock_db.sqlite"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cursor = self.conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                phone_number TEXT UNIQUE NOT NULL,
                name TEXT,
                email TEXT,
                notes TEXT,
                passport_or_nie TEXT NOT NULL DEFAULT 'PENDING',
                profile_type TEXT DEFAULT 'OTHER',
                status TEXT DEFAULT 'active',
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                message_id TEXT UNIQUE NOT NULL,
                direction TEXT NOT NULL,
                content TEXT,
                message_type TEXT NOT NULL,
                dedupe_key TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                conversation_id TEXT,
                storage_path TEXT UNIQUE NOT NULL,
                original_filename TEXT,
                mime_type TEXT,
                file_size INTEGER,
                profile_type TEXT,
                document_type TEXT,
                metadata TEXT DEFAULT '{}',
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS document_versions (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                document_type TEXT NOT NULL,
                document_id TEXT,
                version_number INTEGER NOT NULL,
                content_sha256 TEXT NOT NULL,
                storage_path TEXT NOT NULL,
                original_filename TEXT,
                mime_type TEXT,
                file_size INTEGER,
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor TEXT,
                details TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS export_jobs (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                storage_path TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                accepted_only INTEGER NOT NULL DEFAULT 1,
                file_size INTEGER,
                expires_at TEXT NOT NULL,
                requested_by TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        self.conn.commit()
        logger.info(f"Mock database initialized at {self.db_path}")

    def _row_to_dict(self, row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        data = dict(row)
        for json_field in ("metadata", "details"):
            if json_field in data:
                raw = data.get(json_field)
                data[json_field] = json.loads(raw) if raw else {}
        return data

    def _rows_to_dicts(self, rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
        return [self._row_to_dict(row) for row in rows if row is not None]

    def get_client_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE phone_number = ?", (phone_number,))
        return self._row_to_dict(cursor.fetchone())

    def create_client(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        client_id = str(uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO clients (
                id, phone_number, name, email, notes, passport_or_nie, profile_type, status, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                client_id,
                client_data["phone_number"],
                client_data.get("name"),
                client_data.get("email"),
                client_data.get("notes"),
                client_data.get("passport_or_nie", "PENDING"),
                client_data.get("profile_type", "OTHER"),
                client_data.get("status", "active"),
                json.dumps(client_data.get("metadata", {})),
            ),
        )
        self.conn.commit()
        return self.get_client_by_id(UUID(client_id))

    def update_client(self, client_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        allowed = {"name", "email", "notes", "passport_or_nie", "profile_type", "status", "metadata", "phone_number"}
        set_clauses = []
        params: List[Any] = []

        for key, value in update_data.items():
            if key not in allowed:
                continue
            set_clauses.append(f"{key} = ?")
            if key == "metadata":
                params.append(json.dumps(value or {}))
            else:
                params.append(value)

        if not set_clauses:
            return self.get_client_by_id(client_id)

        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.append(str(client_id))

        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE clients SET {', '.join(set_clauses)} WHERE id = ?", params)
        self.conn.commit()
        return self.get_client_by_id(client_id)

    def get_clients(self, page: int = 1, page_size: int = 50) -> Tuple[List[Dict[str, Any]], int]:
        offset = (page - 1) * page_size
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM clients")
        total = cursor.fetchone()[0]
        cursor.execute(
            "SELECT * FROM clients ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (page_size, offset),
        )
        return self._rows_to_dicts(cursor.fetchall()), total

    def get_client_by_id(self, client_id: UUID) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE id = ?", (str(client_id),))
        return self._row_to_dict(cursor.fetchone())

    def create_conversation(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        conversation_id = str(uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO conversations (
                id, client_id, message_id, direction, content, message_type, dedupe_key, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                conversation_data["client_id"],
                conversation_data["message_id"],
                conversation_data["direction"],
                conversation_data.get("content"),
                conversation_data["message_type"],
                conversation_data.get("dedupe_key"),
                json.dumps(conversation_data.get("metadata", {})),
            ),
        )
        self.conn.commit()
        cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
        return self._row_to_dict(cursor.fetchone())

    def get_conversations_by_client(
        self, client_id: UUID, page: int = 1, page_size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        offset = (page - 1) * page_size
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM conversations WHERE client_id = ?", (str(client_id),))
        total = cursor.fetchone()[0]
        cursor.execute(
            """
            SELECT * FROM conversations
            WHERE client_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (str(client_id), page_size, offset),
        )
        return self._rows_to_dicts(cursor.fetchall()), total

    def get_conversation_by_message_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM conversations WHERE message_id = ?", (message_id,))
        return self._row_to_dict(cursor.fetchone())

    def update_conversation(self, conversation_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        allowed = {"content", "message_type", "metadata", "dedupe_key", "direction"}
        set_clauses = []
        params: List[Any] = []
        for key, value in update_data.items():
            if key not in allowed:
                continue
            set_clauses.append(f"{key} = ?")
            if key == "metadata":
                params.append(json.dumps(value or {}))
            else:
                params.append(value)

        if not set_clauses:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM conversations WHERE id = ?", (str(conversation_id),))
            return self._row_to_dict(cursor.fetchone())

        params.append(str(conversation_id))
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE conversations SET {', '.join(set_clauses)} WHERE id = ?", params)
        self.conn.commit()
        cursor.execute("SELECT * FROM conversations WHERE id = ?", (str(conversation_id),))
        return self._row_to_dict(cursor.fetchone())

    def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        document_id = str(uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO documents (
                id, client_id, conversation_id, storage_path, original_filename,
                mime_type, file_size, profile_type, document_type, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                document_data["client_id"],
                document_data.get("conversation_id"),
                document_data["storage_path"],
                document_data.get("original_filename"),
                document_data.get("mime_type"),
                document_data.get("file_size"),
                document_data.get("profile_type"),
                document_data.get("document_type"),
                json.dumps(document_data.get("metadata", {})),
            ),
        )
        self.conn.commit()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
        return self._row_to_dict(cursor.fetchone())

    def update_document(self, document_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        allowed = {
            "conversation_id",
            "storage_path",
            "original_filename",
            "mime_type",
            "file_size",
            "profile_type",
            "document_type",
            "metadata",
        }
        set_clauses = []
        params: List[Any] = []
        for key, value in update_data.items():
            if key not in allowed:
                continue
            set_clauses.append(f"{key} = ?")
            if key == "metadata":
                params.append(json.dumps(value or {}))
            else:
                params.append(value)

        if not set_clauses:
            return self.get_document_by_id(document_id)

        params.append(str(document_id))
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE documents SET {', '.join(set_clauses)} WHERE id = ?", params)
        self.conn.commit()
        return self.get_document_by_id(document_id)

    def get_documents_by_client(
        self, client_id: UUID, page: int = 1, page_size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        offset = (page - 1) * page_size
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents WHERE client_id = ?", (str(client_id),))
        total = cursor.fetchone()[0]
        cursor.execute(
            """
            SELECT * FROM documents
            WHERE client_id = ?
            ORDER BY uploaded_at DESC
            LIMIT ? OFFSET ?
            """,
            (str(client_id), page_size, offset),
        )
        return self._rows_to_dicts(cursor.fetchall()), total

    def get_document_by_id(self, document_id: UUID) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (str(document_id),))
        return self._row_to_dict(cursor.fetchone())

    def get_client_documents(self, client_id: UUID) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM documents WHERE client_id = ? ORDER BY uploaded_at DESC",
            (str(client_id),),
        )
        return self._rows_to_dicts(cursor.fetchall())

    def get_document_by_client_and_type(
        self, client_id: UUID, document_type: str
    ) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM documents
            WHERE client_id = ? AND document_type = ?
            ORDER BY uploaded_at DESC
            LIMIT 1
            """,
            (str(client_id), document_type),
        )
        return self._row_to_dict(cursor.fetchone())

    def delete_document(self, document_id: UUID) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM documents WHERE id = ?", (str(document_id),))
        self.conn.commit()
        return cursor.rowcount > 0

    def create_document_version(self, version_data: Dict[str, Any]) -> Dict[str, Any]:
        version_id = str(uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO document_versions (
                id, client_id, document_type, document_id, version_number, content_sha256,
                storage_path, original_filename, mime_type, file_size, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_id,
                version_data["client_id"],
                version_data["document_type"],
                version_data.get("document_id"),
                version_data["version_number"],
                version_data["content_sha256"],
                version_data["storage_path"],
                version_data.get("original_filename"),
                version_data.get("mime_type"),
                version_data.get("file_size"),
                json.dumps(version_data.get("metadata", {})),
            ),
        )
        self.conn.commit()
        cursor.execute("SELECT * FROM document_versions WHERE id = ?", (version_id,))
        return self._row_to_dict(cursor.fetchone())

    def get_latest_document_version(
        self, client_id: UUID, document_type: str
    ) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM document_versions
            WHERE client_id = ? AND document_type = ?
            ORDER BY version_number DESC
            LIMIT 1
            """,
            (str(client_id), document_type),
        )
        return self._row_to_dict(cursor.fetchone())

    def create_audit_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        event_id = str(uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO audit_events (id, client_id, event_type, actor, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                event_id,
                event_data["client_id"],
                event_data["event_type"],
                event_data.get("actor"),
                json.dumps(event_data.get("details", {})),
            ),
        )
        self.conn.commit()
        cursor.execute("SELECT * FROM audit_events WHERE id = ?", (event_id,))
        return self._row_to_dict(cursor.fetchone())

    def create_export_job(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        export_id = str(uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO export_jobs (
                id, client_id, storage_path, status, accepted_only, file_size,
                expires_at, requested_by, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                export_id,
                export_data["client_id"],
                export_data["storage_path"],
                export_data.get("status", "ready"),
                1 if export_data.get("accepted_only", True) else 0,
                export_data.get("file_size"),
                export_data["expires_at"],
                export_data.get("requested_by"),
                json.dumps(export_data.get("metadata", {})),
            ),
        )
        self.conn.commit()
        cursor.execute("SELECT * FROM export_jobs WHERE id = ?", (export_id,))
        row = self._row_to_dict(cursor.fetchone())
        if row is not None:
            row["accepted_only"] = bool(row.get("accepted_only", 1))
        return row

    def close(self) -> None:
        if self.conn:
            self.conn.close()
