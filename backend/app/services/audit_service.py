"""Audit trail service for durable forensic chain-of-custody logging."""

import logging
from typing import Any, Dict, List, Optional
from backend.app.models.audit import AuditEventModel
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.schemas.audit import AuditEventResponse, AuditListResponse

logger = logging.getLogger("audiosleuth.audit.service")


class AuditService:
    """Service to record and query durable forensic audit events."""

    def __init__(self, audit_repo: Optional[AuditRepository] = None):
        self.audit_repo = audit_repo or AuditRepository()

    def record_event(
        self,
        action: str,
        outcome: str,
        case_id: Optional[str] = None,
        evidence_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEventResponse:
        """Records a durable forensic audit event in SQLite persistence.

        Args:
            action: Descriptive action key (e.g., case_created, evidence_uploaded, integrity_verified).
            outcome: Structured outcome (e.g., success, failure, verified_match, integrity_mismatch).
            case_id: Associated case ID, if applicable.
            evidence_id: Associated evidence item ID, if applicable.
            details: Contextual parameters, omitting raw audio bytes or credentials.

        Returns:
            AuditEventResponse representing the recorded event.
        """
        # Sanitize details: strip raw binary buffers or sensitive items
        sanitized_details = self._sanitize_details(details or {})

        model = AuditEventModel.create(
            action=action,
            outcome=outcome,
            case_id=case_id,
            evidence_id=evidence_id,
            details=sanitized_details,
        )

        saved = self.audit_repo.create(model)

        logger.info(
            "AUDIT [%s] action='%s' outcome='%s' case='%s' evidence='%s'",
            saved.id,
            saved.action,
            saved.outcome,
            saved.case_id or "-",
            saved.evidence_id or "-",
        )

        return AuditEventResponse(
            id=saved.id,
            timestamp=saved.timestamp,
            action=saved.action,
            outcome=saved.outcome,
            case_id=saved.case_id,
            evidence_id=saved.evidence_id,
            details=saved.details,
        )

    def list_events(
        self,
        case_id: Optional[str] = None,
        evidence_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AuditListResponse:
        """Lists chronological audit trail records with optional filters."""
        events = self.audit_repo.list_events(
            case_id=case_id,
            evidence_id=evidence_id,
            action=action,
            limit=limit,
            offset=offset,
        )
        total = self.audit_repo.count_events(
            case_id=case_id,
            evidence_id=evidence_id,
            action=action,
        )

        items = [
            AuditEventResponse(
                id=e.id,
                timestamp=e.timestamp,
                action=e.action,
                outcome=e.outcome,
                case_id=e.case_id,
                evidence_id=e.evidence_id,
                details=e.details,
            )
            for e in events
        ]

        return AuditListResponse(
            items=items,
            total=total,
            case_id=case_id,
        )

    def get_event(self, event_id: str) -> Optional[AuditEventResponse]:
        """Retrieves a single audit record by event ID."""
        event = self.audit_repo.get_by_id(event_id)
        if not event:
            return None
        return AuditEventResponse(
            id=event.id,
            timestamp=event.timestamp,
            action=event.action,
            outcome=event.outcome,
            case_id=event.case_id,
            evidence_id=event.evidence_id,
            details=event.details,
        )

    @staticmethod
    def _sanitize_details(details: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures large binary buffers or secrets are never persisted in the audit trail."""
        sanitized: Dict[str, Any] = {}
        for k, v in details.items():
            if isinstance(v, (bytes, bytearray)):
                sanitized[k] = f"<binary data: {len(v)} bytes>"
            elif isinstance(v, (list, tuple)) and len(v) > 50:
                sanitized[k] = f"<list with {len(v)} elements>"
            elif isinstance(v, dict):
                sanitized[k] = AuditService._sanitize_details(v)
            else:
                sanitized[k] = v
        return sanitized
