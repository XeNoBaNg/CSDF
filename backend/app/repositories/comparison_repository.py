"""Repository for Cross-Recording Comparison persistence operations."""

from typing import List, Optional
from backend.app.models.comparison import ComparisonRecordModel
from backend.app.repositories.database import get_db_connection


class ComparisonRepository:
    """Manages Cross-Recording Comparison records in SQLite."""

    def __init__(self, db_path_override: Optional[str] = None):
        self.db_path_override = db_path_override

    def create(self, record: ComparisonRecordModel) -> ComparisonRecordModel:
        """Persists a new comparison record."""
        with get_db_connection(self.db_path_override) as conn:
            conn.execute(
                """
                INSERT INTO comparisons (
                    id, evidence_id_a, evidence_id_b, case_id_a, case_id_b,
                    hash_a, hash_b, metrics_summary, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.evidence_id_a,
                    record.evidence_id_b,
                    record.case_id_a,
                    record.case_id_b,
                    record.hash_a,
                    record.hash_b,
                    record.metrics_summary_json,
                    record.created_at,
                ),
            )
            conn.commit()
        return record

    def get_by_id(self, comparison_id: str) -> Optional[ComparisonRecordModel]:
        """Retrieves a comparison record by its unique identifier."""
        with get_db_connection(self.db_path_override) as conn:
            cursor = conn.execute(
                """
                SELECT id, evidence_id_a, evidence_id_b, case_id_a, case_id_b,
                       hash_a, hash_b, metrics_summary, created_at
                FROM comparisons WHERE id = ?
                """,
                (comparison_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return ComparisonRecordModel(
                id=row["id"],
                evidence_id_a=row["evidence_id_a"],
                evidence_id_b=row["evidence_id_b"],
                case_id_a=row["case_id_a"],
                case_id_b=row["case_id_b"],
                hash_a=row["hash_a"],
                hash_b=row["hash_b"],
                metrics_summary_json=row["metrics_summary"],
                created_at=row["created_at"],
            )

    def list_by_evidence(self, evidence_id: str) -> List[ComparisonRecordModel]:
        """Lists all comparisons involving a specific evidence ID (either as item A or item B)."""
        with get_db_connection(self.db_path_override) as conn:
            cursor = conn.execute(
                """
                SELECT id, evidence_id_a, evidence_id_b, case_id_a, case_id_b,
                       hash_a, hash_b, metrics_summary, created_at
                FROM comparisons
                WHERE evidence_id_a = ? OR evidence_id_b = ?
                ORDER BY created_at DESC
                """,
                (evidence_id, evidence_id),
            )
            rows = cursor.fetchall()
            return [
                ComparisonRecordModel(
                    id=row["id"],
                    evidence_id_a=row["evidence_id_a"],
                    evidence_id_b=row["evidence_id_b"],
                    case_id_a=row["case_id_a"],
                    case_id_b=row["case_id_b"],
                    hash_a=row["hash_a"],
                    hash_b=row["hash_b"],
                    metrics_summary_json=row["metrics_summary"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]
