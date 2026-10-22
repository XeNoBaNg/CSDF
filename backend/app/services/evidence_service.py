"""Evidence intake, registration, and integrity verification business logic."""

from datetime import datetime, timezone
import logging
from typing import Optional
from fastapi import UploadFile
from backend.app.core.errors import CaseClosedError, CaseNotFoundError, EvidenceNotFoundError
from backend.app.evidence.storage import (
    save_uploaded_evidence,
    verify_evidence_integrity,
)
from backend.app.models.evidence import EvidenceModel
from backend.app.repositories.case_repository import CaseRepository
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.schemas.evidence import (
    EvidenceListResponse,
    EvidenceResponse,
    IntegrityVerificationResponse,
)
from backend.app.services.audit_service import AuditService

logger = logging.getLogger("audiosleuth.services.evidence")


class EvidenceService:
    """Orchestrates evidence intake, metadata persistence, and cryptographic verification."""

    def __init__(
        self,
        case_repo: Optional[CaseRepository] = None,
        evidence_repo: Optional[EvidenceRepository] = None,
        audit_service: Optional[AuditService] = None,
    ):
        self.case_repo = case_repo or CaseRepository()
        self.evidence_repo = evidence_repo or EvidenceRepository()
        self.audit_service = audit_service or AuditService()

    async def acquire_evidence(
        self,
        case_id: str,
        upload_file: UploadFile,
    ) -> EvidenceResponse:
        """Validates case existence and active status, streams upload, verifies signature,
        stores file, and registers the immutable evidence record with an audit entry.
        """
        # 1. Enforce that case exists prior to intake
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise CaseNotFoundError(
                case_id=case_id,
                message=f"Cannot ingest evidence: Investigation case '{case_id}' does not exist.",
            )

        # 2. Enforce that case is active and not closed
        if case.status == "closed":
            raise CaseClosedError(case_id=case_id)

        # 3. Stream, calculate SHA-256, validate magic signature, and store atomically
        meta = await save_uploaded_evidence(upload_file, case_id)

        # 4. Create persistent evidence entity
        model = EvidenceModel.create(
            evidence_id=str(meta["evidence_id"]),
            case_id=case_id,
            original_filename=str(meta["original_filename"]),
            stored_filename=str(meta["stored_filename"]),
            file_size_bytes=int(meta["file_size_bytes"]),
            sha256_hash=str(meta["sha256_hash"]),
            format_name=str(meta["format"]),
            mime_type=str(meta["mime_type"]),
            integrity_status="verified",
            ingested_at=str(meta["ingested_at"]),
        )

        saved = self.evidence_repo.create(model)

        # Record durable audit trail entry
        self.audit_service.record_event(
            action="evidence_uploaded",
            outcome="success",
            case_id=case_id,
            evidence_id=saved.id,
            details={
                "original_filename": saved.original_filename,
                "stored_filename": saved.stored_filename,
                "file_size_bytes": saved.file_size_bytes,
                "sha256_hash": saved.sha256_hash,
                "format": saved.format,
                "mime_type": saved.mime_type,
            },
        )

        return EvidenceResponse(
            id=saved.id,
            case_id=saved.case_id,
            original_filename=saved.original_filename,
            file_size_bytes=saved.file_size_bytes,
            sha256_hash=saved.sha256_hash,
            format=saved.format,
            mime_type=saved.mime_type,
            ingested_at=saved.ingested_at,
            integrity_status=saved.integrity_status,
        )

    def get_evidence(self, evidence_id: str) -> EvidenceResponse:
        """Retrieves evidence record by ID or raises EvidenceNotFoundError."""
        item = self.evidence_repo.get_by_id(evidence_id)
        if not item:
            raise EvidenceNotFoundError(evidence_id=evidence_id)
        return EvidenceResponse(
            id=item.id,
            case_id=item.case_id,
            original_filename=item.original_filename,
            file_size_bytes=item.file_size_bytes,
            sha256_hash=item.sha256_hash,
            format=item.format,
            mime_type=item.mime_type,
            ingested_at=item.ingested_at,
            integrity_status=item.integrity_status,
        )

    def list_evidence_by_case(self, case_id: str) -> EvidenceListResponse:
        """Lists all evidence records registered under a given case."""
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise CaseNotFoundError(case_id=case_id)

        items = self.evidence_repo.list_by_case(case_id)
        results = [
            EvidenceResponse(
                id=item.id,
                case_id=item.case_id,
                original_filename=item.original_filename,
                file_size_bytes=item.file_size_bytes,
                sha256_hash=item.sha256_hash,
                format=item.format,
                mime_type=item.mime_type,
                ingested_at=item.ingested_at,
                integrity_status=item.integrity_status,
            )
            for item in items
        ]
        return EvidenceListResponse(case_id=case_id, items=results, total=len(results))

    def verify_integrity(self, evidence_id: str) -> IntegrityVerificationResponse:
        """Recalculates SHA-256 of stored evidence and compares against original intake digest."""
        item = self.evidence_repo.get_by_id(evidence_id)
        if not item:
            raise EvidenceNotFoundError(evidence_id=evidence_id)

        status_str, calculated_hash, explanation = verify_evidence_integrity(
            expected_hash=item.sha256_hash,
            stored_filename=item.stored_filename,
        )

        # Update integrity status in repository without ever altering the expected original digest
        self.evidence_repo.update_integrity_status(evidence_id, status_str)

        # Record durable audit trail entry
        outcome = "verified_match" if status_str == "match" else "integrity_mismatch"
        self.audit_service.record_event(
            action="integrity_verified",
            outcome=outcome,
            case_id=item.case_id,
            evidence_id=item.id,
            details={
                "status": status_str,
                "expected_sha256": item.sha256_hash,
                "calculated_sha256": calculated_hash,
                "explanation": explanation,
            },
        )

        return IntegrityVerificationResponse(
            evidence_id=item.id,
            case_id=item.case_id,
            expected_sha256=item.sha256_hash,
            calculated_sha256=calculated_hash,
            status=status_str,
            verified_at=datetime.now(timezone.utc).isoformat(),
            explanation=explanation,
        )

