"""Repository for durable forensic audit event persistence in SQLite."""

import json
import logging
from typing import Any, Dict, List, Optional
from backend.app.models.audit import AuditEventModel
from backend.app.repositories.database import get_db_connection

logger = logging.getLogger("audiosleuth.audit.repository")


class AuditRepository:
    """Manages durable audit trail persistence in SQLite."""

    def __init__(self, db_path_override: Optional[str] = None):
        self.db_path_override = db_path_override

    def create(self, event: AuditEventModel) -> AuditEventModel:
        """Persists a new forensic audit event."""
        details_json = json.dumps(event.details or {})
        with get_db_connection(self.db_path_override) as conn:
            conn.execute(
                """
                INSERT INTO audit_events (id, timestamp, action, outcome, case_id, evidence_id, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.timestamp,
                    event.action,
                    event.outcome,
                    event.case_id,
                    event.evidence_id,
                    details_json,
                ),
            )
            conn.commit()
        return event

    def get_by_id(self, event_id: str) -> Optional[AuditEventModel]:
        """Retrieves an audit event by its unique identifier."""
        with get_db_connection(self.db_path_override) as conn:
            cursor = conn.execute(
                """
                SELECT id, timestamp, action, outcome, case_id, evidence_id, details
                FROM audit_events WHERE id = ?
                """,
                (event_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_model(row)

    def list_events(
        self,
        case_id: Optional[str] = None,
        evidence_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEventModel]:
        """Lists audit events with optional filtering, ordered chronologically descending."""
        query = "SELECT id, timestamp, action, outcome, case_id, evidence_id, details FROM audit_events WHERE 1=1"
        params: List[Any] = []

        if case_id:
            query += " AND case_id = ?"
            params.append(case_id)

        if evidence_id:
            query += " AND evidence_id = ?"
            params.append(evidence_id)

        if action:
            query += " AND action = ?"
            params.append(action)

        query += " ORDER BY timestamp DESC, id DESC LIMIT ? OFFSET ?"
        params.extend([max(1, min(limit, 500)), max(0, offset)])

        with get_db_connection(self.db_path_override) as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_model(row) for row in rows]

    def count_events(
        self,
        case_id: Optional[str] = None,
        evidence_id: Optional[str] = None,
        action: Optional[str] = None,
    ) -> int:
        """Counts matching audit events."""
        query = "SELECT COUNT(*) as total FROM audit_events WHERE 1=1"
        params: List[Any] = []

        if case_id:
            query += " AND case_id = ?"
            params.append(case_id)

        if evidence_id:
            query += " AND evidence_id = ?"
            params.append(evidence_id)

        if action:
            query += " AND action = ?"
            params.append(action)

        with get_db_connection(self.db_path_override) as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            return int(row["total"]) if row else 0

    @staticmethod
    def _row_to_model(row: Any) -> AuditEventModel:
        raw_details = row["details"]
        try:
            details_dict = json.loads(raw_details) if raw_details else {}
        except Exception:
            details_dict = {"raw": str(raw_details)}

        return AuditEventModel(
            id=row["id"],
            timestamp=row["timestamp"],
            action=row["action"],
            outcome=row["outcome"],
            case_id=row["case_id"],
            evidence_id=row["evidence_id"],
            details=details_dict,
        )
