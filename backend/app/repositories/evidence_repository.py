"""Repository for Evidence persistence operations."""

from typing import List, Optional
from backend.app.models.evidence import EvidenceModel
from backend.app.repositories.database import get_db_connection


class EvidenceRepository:
    """Manages Evidence metadata storage in SQLite."""

    def __init__(self, db_path_override: Optional[str] = None):
        self.db_path_override = db_path_override

    def create(self, item: EvidenceModel) -> EvidenceModel:
        """Persists a new evidence registration record."""
        with get_db_connection(self.db_path_override) as conn:
            conn.execute(
                """
                INSERT INTO evidence_items (
                    id, case_id, original_filename, stored_filename,
                    file_size_bytes, sha256_hash, format, mime_type,
                    ingested_at, integrity_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.id,
                    item.case_id,
                    item.original_filename,
                    item.stored_filename,
                    item.file_size_bytes,
                    item.sha256_hash,
                    item.format,
                    item.mime_type,
                    item.ingested_at,
                    item.integrity_status,
                ),
            )
            conn.commit()
        return item

    def get_by_id(self, evidence_id: str) -> Optional[EvidenceModel]:
        """Retrieves an evidence record by unique ID."""
        with get_db_connection(self.db_path_override) as conn:
            cursor = conn.execute(
                """
                SELECT id, case_id, original_filename, stored_filename,
                       file_size_bytes, sha256_hash, format, mime_type,
                       ingested_at, integrity_status
                FROM evidence_items WHERE id = ?
                """,
                (evidence_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return EvidenceModel(
                id=row["id"],
                case_id=row["case_id"],
                original_filename=row["original_filename"],
                stored_filename=row["stored_filename"],
                file_size_bytes=row["file_size_bytes"],
                sha256_hash=row["sha256_hash"],
                format=row["format"],
                mime_type=row["mime_type"],
                ingested_at=row["ingested_at"],
                integrity_status=row["integrity_status"],
            )

    def list_by_case(self, case_id: str) -> List[EvidenceModel]:
        """Lists all evidence items registered under a case."""
        with get_db_connection(self.db_path_override) as conn:
            cursor = conn.execute(
                """
                SELECT id, case_id, original_filename, stored_filename,
                       file_size_bytes, sha256_hash, format, mime_type,
                       ingested_at, integrity_status
                FROM evidence_items WHERE case_id = ?
                ORDER BY ingested_at DESC
                """,
                (case_id,),
            )
            rows = cursor.fetchall()
            return [
                EvidenceModel(
                    id=row["id"],
                    case_id=row["case_id"],
                    original_filename=row["original_filename"],
                    stored_filename=row["stored_filename"],
                    file_size_bytes=row["file_size_bytes"],
                    sha256_hash=row["sha256_hash"],
                    format=row["format"],
                    mime_type=row["mime_type"],
                    ingested_at=row["ingested_at"],
                    integrity_status=row["integrity_status"],
                )
                for row in rows
            ]

    def list_all(self, case_id: Optional[str] = None) -> List[EvidenceModel]:
        """Lists all evidence items across all cases or filtered by case_id."""
        with get_db_connection(self.db_path_override) as conn:
            if case_id:
                cursor = conn.execute(
                    """
                    SELECT id, case_id, original_filename, stored_filename,
                           file_size_bytes, sha256_hash, format, mime_type,
                           ingested_at, integrity_status
                    FROM evidence_items WHERE case_id = ?
                    ORDER BY ingested_at DESC
                    """,
                    (case_id,),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT id, case_id, original_filename, stored_filename,
                           file_size_bytes, sha256_hash, format, mime_type,
                           ingested_at, integrity_status
                    FROM evidence_items
                    ORDER BY ingested_at DESC
                    """
                )
            rows = cursor.fetchall()
            return [
                EvidenceModel(
                    id=row["id"],
                    case_id=row["case_id"],
                    original_filename=row["original_filename"],
                    stored_filename=row["stored_filename"],
                    file_size_bytes=row["file_size_bytes"],
                    sha256_hash=row["sha256_hash"],
                    format=row["format"],
                    mime_type=row["mime_type"],
                    ingested_at=row["ingested_at"],
                    integrity_status=row["integrity_status"],
                )
                for row in rows
            ]

    def update_integrity_status(self, evidence_id: str, status: str) -> bool:
        """Updates the recorded integrity verification status without modifying original hashes."""
        with get_db_connection(self.db_path_override) as conn:
            cursor = conn.execute(
                "UPDATE evidence_items SET integrity_status = ? WHERE id = ?",
                (status, evidence_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete(self, evidence_id: str) -> bool:
        """Deletes an evidence metadata record."""
        with get_db_connection(self.db_path_override) as conn:
            cursor = conn.execute("DELETE FROM evidence_items WHERE id = ?", (evidence_id,))
            conn.commit()
            return cursor.rowcount > 0
