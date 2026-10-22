"""Case management business logic and audit integration."""

from datetime import datetime, timezone
import logging
from typing import Optional
import uuid
from backend.app.core.errors import CaseNotFoundError
from backend.app.models.case import CaseModel
from backend.app.repositories.case_repository import CaseRepository
from backend.app.schemas.case import (
    CaseCreateRequest,
    CaseListResponse,
    CaseResponse,
    CaseUpdateRequest,
)
from backend.app.services.audit_service import AuditService

logger = logging.getLogger("audiosleuth.services.case")


class CaseService:
    """Orchestrates case lifecycle, metadata persistence, and audit logging."""

    def __init__(
        self,
        case_repo: Optional[CaseRepository] = None,
        audit_service: Optional[AuditService] = None,
    ):
        self.case_repo = case_repo or CaseRepository()
        self.audit_service = audit_service or AuditService()

    def create_case(self, payload: CaseCreateRequest) -> CaseResponse:
        """Initializes and registers a new investigation case."""
        case_id = f"CASE-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
        model = CaseModel.create(
            case_id=case_id,
            title=payload.title,
            investigator_name=payload.investigator_name,
            notes=payload.notes,
            description=payload.description or payload.notes,
            status="active",
        )
        saved = self.case_repo.create(model)

        # Record durable audit trail entry
        self.audit_service.record_event(
            action="case_created",
            outcome="success",
            case_id=saved.id,
            details={
                "title": saved.title,
                "investigator_name": saved.investigator_name,
                "status": saved.status,
            },
        )

        return self._to_response(saved, evidence_count=0)

    def get_case(self, case_id: str) -> CaseResponse:
        """Retrieves a case by ID or raises CaseNotFoundError."""
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise CaseNotFoundError(case_id=case_id)
        evidence_count = self.case_repo.count_evidence(case_id)
        return self._to_response(case, evidence_count=evidence_count)

    def list_cases(self, status: Optional[str] = None) -> CaseListResponse:
        """Lists registered cases, optionally filtered by status ('active' | 'closed' | 'all')."""
        filter_status = None if (not status or status.lower() == "all") else status.lower()
        cases = self.case_repo.list_all(status=filter_status)
        result = []
        for c in cases:
            count = self.case_repo.count_evidence(c.id)
            result.append(self._to_response(c, evidence_count=count))
        return CaseListResponse(cases=result, total=len(result))

    def update_case(self, case_id: str, payload: CaseUpdateRequest) -> CaseResponse:
        """Updates editable metadata fields on an existing investigation case."""
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise CaseNotFoundError(case_id=case_id)

        now = datetime.now(timezone.utc).isoformat()
        updated_fields = []

        if payload.title is not None and payload.title.strip():
            case.title = payload.title.strip()
            updated_fields.append("title")

        if payload.investigator_name is not None and payload.investigator_name.strip():
            case.investigator_name = payload.investigator_name.strip()
            updated_fields.append("investigator_name")

        if payload.description is not None:
            case.description = payload.description.strip() if payload.description else None
            updated_fields.append("description")

        if payload.notes is not None:
            case.notes = payload.notes.strip() if payload.notes else None
            updated_fields.append("notes")

        if payload.status is not None:
            case.status = payload.status.strip().lower()
            updated_fields.append("status")

        case.updated_at = now
        saved = self.case_repo.update(case)
        if not saved:
            raise CaseNotFoundError(case_id=case_id)

        evidence_count = self.case_repo.count_evidence(case_id)

        # Record durable audit trail entry
        self.audit_service.record_event(
            action="case_updated",
            outcome="success",
            case_id=case_id,
            details={"updated_fields": updated_fields},
        )

        return self._to_response(saved, evidence_count=evidence_count)

    def set_case_status(
        self,
        case_id: str,
        status: str,
        reason: Optional[str] = None,
    ) -> CaseResponse:
        """Explicitly transitions a case status between 'active' and 'closed'."""
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise CaseNotFoundError(case_id=case_id)

        target_status = status.strip().lower()
        if target_status not in ("active", "closed"):
            raise ValueError(f"Invalid case status '{status}'. Must be 'active' or 'closed'.")

        old_status = case.status
        now = datetime.now(timezone.utc).isoformat()
        case.status = target_status
        case.updated_at = now

        self.case_repo.update_status(case_id, target_status, now)
        evidence_count = self.case_repo.count_evidence(case_id)

        action = "case_closed" if target_status == "closed" else "case_reopened"
        self.audit_service.record_event(
            action=action,
            outcome="success",
            case_id=case_id,
            details={
                "previous_status": old_status,
                "new_status": target_status,
                "reason": reason or "Investigator status transition",
            },
        )

        return self._to_response(case, evidence_count=evidence_count)

    @staticmethod
    def _to_response(model: CaseModel, evidence_count: int = 0) -> CaseResponse:
        return CaseResponse(
            id=model.id,
            title=model.title,
            investigator_name=model.investigator_name,
            notes=model.notes,
            description=model.description or model.notes,
            status=model.status or "active",
            created_at=model.created_at,
            updated_at=model.updated_at,
            evidence_count=evidence_count,
        )

