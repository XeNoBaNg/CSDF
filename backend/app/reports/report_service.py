"""Forensic PDF report generation service."""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid
from backend.app.analysis.decoder import verify_and_load_audio
from backend.app.core.errors import (
    CaseEvidenceMismatchError,
    CaseNotFoundError,
    EvidenceIntegrityError,
    EvidenceNotFoundError,
    MissingEvidenceFileError,
)
from backend.app.models.case import CaseModel
from backend.app.models.evidence import EvidenceModel
from backend.app.reports.chart_generator import render_spectrogram_image, render_waveform_image
from backend.app.reports.pdf_generator import ForensicPdfReportGenerator
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.repositories.case_repository import CaseRepository
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.services.analysis_service import SignalAnalysisService
from backend.app.services.audit_service import AuditService
from backend.app.services.evidence_service import EvidenceService
from backend.app.services.inspection_service import AudioInspectionService

logger = logging.getLogger("audiosleuth.services.reports")


class ForensicReportService:
    """Orchestrates forensic data gathering and in-memory PDF generation."""

    def __init__(
        self,
        case_repo: Optional[CaseRepository] = None,
        evidence_repo: Optional[EvidenceRepository] = None,
        audit_repo: Optional[AuditRepository] = None,
        evidence_service: Optional[EvidenceService] = None,
        inspection_service: Optional[AudioInspectionService] = None,
        analysis_service: Optional[SignalAnalysisService] = None,
        audit_service: Optional[AuditService] = None,
    ):
        self.case_repo = case_repo or CaseRepository()
        self.evidence_repo = evidence_repo or EvidenceRepository()
        self.audit_repo = audit_repo or AuditRepository()
        self.evidence_service = evidence_service or EvidenceService()
        self.inspection_service = inspection_service or AudioInspectionService()
        self.analysis_service = analysis_service or SignalAnalysisService()
        self.audit_service = audit_service or AuditService()
        self.pdf_generator = ForensicPdfReportGenerator()

    def generate_evidence_report(
        self,
        evidence_id: str,
        case_id: Optional[str] = None,
        include_visualizations: bool = True,
        include_audit: bool = True,
        run_analysis_if_missing: bool = True,
        examiner_notes: Optional[str] = None,
    ) -> Tuple[bytes, str, str]:
        """Generates an evidence-based forensic PDF report.

        Args:
            evidence_id: Target evidence identifier.
            case_id: Optional case identifier for relationship validation.
            include_visualizations: Whether to generate and embed waveform and spectrogram.
            include_audit: Whether to query and embed chronological audit events.
            run_analysis_if_missing: Whether to run explainable signal analysis detectors.
            examiner_notes: Optional supplementary notes from the investigator.

        Returns:
            Tuple of (pdf_bytes, filename, report_id).

        Raises:
            EvidenceNotFoundError: If evidence ID does not exist.
            CaseEvidenceMismatchError: If evidence does not belong to specified case_id.
            CaseNotFoundError: If owning case is missing.
            EvidenceIntegrityError: If stored bytes fail cryptographic SHA-256 pre-check.
            MissingEvidenceFileError: If physical file is missing from vault.
        """
        # 1. Fetch Evidence Record
        item = self.evidence_repo.get_by_id(evidence_id)
        if not item:
            raise EvidenceNotFoundError(evidence_id=evidence_id)

        # 2. Case Relationship Validation
        if case_id and item.case_id != case_id:
            raise CaseEvidenceMismatchError(case_id=case_id, evidence_id=evidence_id)

        # 3. Fetch Case Record
        case = self.case_repo.get_by_id(item.case_id)
        if not case:
            raise CaseNotFoundError(case_id=item.case_id)

        # 4. Mandatory Cryptographic Integrity Re-Verification
        verification = self.evidence_service.verify_integrity(item.id)
        if verification.status == "mismatch":
            logger.error("Report generation aborted: Integrity failure on evidence '%s'", item.id)
            raise EvidenceIntegrityError(
                message="CRITICAL INTEGRITY FAILURE: Stored evidence bytes have been altered or corrupted on disk. Cannot generate report for compromised evidence.",
                details={
                    "evidence_id": item.id,
                    "expected_sha256": verification.expected_sha256,
                    "calculated_sha256": verification.calculated_sha256,
                },
            )
        elif verification.status == "unverifiable":
            logger.error("Report generation aborted: Physical evidence missing for '%s'", item.id)
            raise MissingEvidenceFileError(evidence_id=item.id)

        # 5. Extract Audio Metadata & Decode Samples Non-Destructively
        metadata = self.inspection_service.get_metadata(item.id)
        samples, sample_rate, _ = verify_and_load_audio(item)

        # 6. Execute Explainable Signal Anomaly Analysis
        findings = []
        summary = None
        applied_params = None

        if run_analysis_if_missing:
            analysis = self.analysis_service.analyze_evidence(item.id)
            findings = analysis.findings
            summary = analysis.summary
            applied_params = analysis.parameters_applied

        # 7. Render Acoustic Visualizations (In-Memory PNGs)
        waveform_png = None
        spectrogram_png = None
        if include_visualizations:
            try:
                waveform_png = render_waveform_image(samples, sample_rate)
                spectrogram_png = render_spectrogram_image(samples, sample_rate)
            except Exception as e:
                logger.warning("Failed to render visualization graphics for report: %s", e)

        # 8. Query Chronological Audit Trail
        audit_events = []
        if include_audit:
            audit_events = self.audit_repo.list_events(case_id=case.id, limit=50)

        # 9. Generate Unique Report Identifier & Build PDF
        now_utc = datetime.now(timezone.utc)
        report_id = f"REP-{now_utc.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        timestamp_str = now_utc.strftime("%Y-%m-%d %H:%M:%S")

        pdf_bytes = self.pdf_generator.generate_report(
            report_id=report_id,
            generated_at=timestamp_str,
            case=case,
            evidence=item,
            metadata=metadata,
            integrity_status=verification.status,
            calculated_sha256=verification.calculated_sha256 or item.sha256_hash,
            findings=findings,
            analysis_summary=summary,
            applied_parameters=applied_params,
            waveform_png=waveform_png,
            spectrogram_png=spectrogram_png,
            audit_events=audit_events,
            examiner_notes=examiner_notes,
        )

        # 10. Record Durable Audit Trail Entry
        self.audit_service.record_event(
            action="report_generated",
            outcome="success",
            case_id=case.id,
            evidence_id=item.id,
            details={
                "report_id": report_id,
                "size_bytes": len(pdf_bytes),
                "include_visualizations": include_visualizations,
                "include_audit": include_audit,
                "total_findings": len(findings),
            },
        )

        filename = f"AudioSleuth_Forensic_Report_{item.id}_{now_utc.strftime('%Y%m%d')}.pdf"
        logger.info(
            "Successfully generated forensic PDF report '%s' (%d bytes) for evidence '%s'",
            report_id,
            len(pdf_bytes),
            item.id,
        )
        return pdf_bytes, filename, report_id
