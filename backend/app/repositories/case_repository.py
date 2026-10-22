"""Repository for Case persistence operations."""

from typing import List, Optional
from backend.app.models.case import CaseModel
from backend.app.repositories.database import get_db_connection


class CaseRepository:
    """Manages Case storage in SQLite."""

    def __init__(self, db_path_override: Optional[str] = None):
        self.db_path_override = db_path_override

    def create(self, case: CaseModel) -> CaseModel:
        """Persists a new investigation case."""
        with get_db_connection(self.db_path_override) as conn:
            conn.execute(
                """
                INSERT INTO cases (id, title, investigator_name, notes, description, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case.id,
                    case.title,
                    case.investigator_name,
                    case.notes,
                    case.description,
                    case.status,
                    case.created_at,
                    case.updated_at,
                ),
            )
            conn.commit()
        return case

    def get_by_id(self, case_id: str) -> Optional[CaseModel]:
        """Retrieves a case by unique ID."""
        with get_db_connection(self.db_path_override) as conn:
            cursor = conn.execute(
                "SELECT id, title, investigator_name, notes, description, status, created_at, updated_at FROM cases WHERE id = ?",
                (case_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return CaseModel(
                id=row["id"],
                title=row["title"],
                investigator_name=row["investigator_name"],
                notes=row["notes"],
                description=row["description"],
                status=row["status"] or "active",
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def list_all(self, status: Optional[str] = None) -> List[CaseModel]:
        """Lists cases ordered by creation date descending, optionally filtered by status."""
        with get_db_connection(self.db_path_override) as conn:
            if status and status.lower() != "all":
                cursor = conn.execute(
                    "SELECT id, title, investigator_name, notes, description, status, created_at, updated_at FROM cases WHERE status = ? ORDER BY created_at DESC",
                    (status.lower(),),
                )
            else:
                cursor = conn.execute(
                    "SELECT id, title, investigator_name, notes, description, status, created_at, updated_at FROM cases ORDER BY created_at DESC"
                )
            rows = cursor.fetchall()
            return [
                CaseModel(
                    id=row["id"],
                    title=row["title"],
                    investigator_name=row["investigator_name"],
                    notes=row["notes"],
                    description=row["description"],
                    status=row["status"] or "active",
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    def update(self, case: CaseModel) -> Optional[CaseModel]:
        """Updates editable metadata on an existing investigation case."""
        with get_db_connection(self.db_path_override) as conn:
            cursor = conn.execute(
                """
                UPDATE cases
                SET title = ?, investigator_name = ?, notes = ?, description = ?, status = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    case.title,
                    case.investigator_name,
                    case.notes,
                    case.description,
                    case.status,
                    case.updated_at,
                    case.id,
                ),
            )
            conn.commit()
            if cursor.rowcount == 0:
                return None
            return case

    def update_status(self, case_id: str, status: str, updated_at: str) -> bool:
        """Updates the status and updated_at timestamp of a case."""
        with get_db_connection(self.db_path_override) as conn:
            cursor = conn.execute(
                "UPDATE cases SET status = ?, updated_at = ? WHERE id = ?",
                (status, updated_at, case_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def count_evidence(self, case_id: str) -> int:
        """Returns the count of evidence items attached to a case."""
        with get_db_connection(self.db_path_override) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM evidence_items WHERE case_id = ?",
                (case_id,),
            )
            row = cursor.fetchone()
            return row["count"] if row else 0

    def delete(self, case_id: str) -> bool:
        """Deletes a case and cascades to associated evidence."""
        with get_db_connection(self.db_path_override) as conn:
            cursor = conn.execute("DELETE FROM cases WHERE id = ?", (case_id,))
            conn.commit()
            return cursor.rowcount > 0

