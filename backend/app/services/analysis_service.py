"""Forensic signal analysis orchestration service.

Coordinates explainable anomaly detectors (silence intervals, abrupt transitions,
and spectral flux inconsistencies) on verified, non-destructively decoded evidence audio.
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.app.analysis.decoder import verify_and_load_audio
from backend.app.analysis.silence import detect_silence_intervals
from backend.app.analysis.spectral import detect_spectral_inconsistencies
from backend.app.analysis.transitions import detect_amplitude_transitions
from backend.app.core.errors import EvidenceNotFoundError
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisSummary,
    ForensicFinding,
)
from backend.app.services.audit_service import AuditService

logger = logging.getLogger("audiosleuth.services.analysis")


class SignalAnalysisService:
    """Service to orchestrate signal processing anomaly detectors on evidence items."""

    def __init__(
        self,
        evidence_repo: Optional[EvidenceRepository] = None,
        audit_service: Optional[AuditService] = None,
    ):
        self.evidence_repo = evidence_repo or EvidenceRepository()
        self.audit_service = audit_service or AuditService()


    def analyze_evidence(
        self,
        evidence_id: str,
        request: Optional[AnalysisRequest] = None,
    ) -> AnalysisResponse:
        """Executes selected signal-processing anomaly detectors on registered evidence.

        1. Verifies physical evidence integrity against registered intake SHA-256.
        2. Non-destructively decodes samples into working floating-point array.
        3. Executes requested explainable detectors.
        4. Compiles chronological findings and summary metrics.

        Args:
            evidence_id: Server-assigned evidence identifier.
            request: Detector selection flags and custom parameters.

        Returns:
            AnalysisResponse containing structured timestamped findings and execution metrics.
        """
        if request is None:
            request = AnalysisRequest()

        item = self.evidence_repo.get_by_id(evidence_id)
        if not item:
            raise EvidenceNotFoundError(evidence_id=evidence_id)

        # 1. Non-destructive decoding with cryptographic SHA-256 pre-check verification
        samples, sample_rate, _ = verify_and_load_audio(item)

        start_time_perf = time.perf_counter()
        all_findings: List[ForensicFinding] = []
        applied_params: Dict[str, Any] = {}

        # 2. Detector A: Silence and low-energy intervals
        if request.enable_silence:
            silence_findings = detect_silence_intervals(
                samples=samples,
                sample_rate=sample_rate,
                evidence_id=item.id,
                source_sha256=item.sha256_hash,
                params=request.silence_params,
            )
            all_findings.extend(silence_findings)
            applied_params["silence"] = (
                request.silence_params.model_dump()
                if request.silence_params
                else "default"
            )

        # 3. Detector B: Abrupt amplitude transitions
        if request.enable_transitions:
            transition_findings = detect_amplitude_transitions(
                samples=samples,
                sample_rate=sample_rate,
                evidence_id=item.id,
                source_sha256=item.sha256_hash,
                params=request.transition_params,
            )
            all_findings.extend(transition_findings)
            applied_params["transitions"] = (
                request.transition_params.model_dump()
                if request.transition_params
                else "default"
            )

        # 4. Detector C: Spectral flux inconsistency
        if request.enable_spectral_flux:
            spectral_findings = detect_spectral_inconsistencies(
                samples=samples,
                sample_rate=sample_rate,
                evidence_id=item.id,
                source_sha256=item.sha256_hash,
                params=request.spectral_params,
            )
            all_findings.extend(spectral_findings)
            applied_params["spectral_flux"] = (
                request.spectral_params.model_dump()
                if request.spectral_params
                else "default"
            )

        # Sort all findings chronologically by start timestamp
        all_findings.sort(key=lambda f: (f.start_time, f.event_time or f.start_time))

        execution_duration_ms = (time.perf_counter() - start_time_perf) * 1000.0

        # Compile category & priority summary counts
        by_category: Dict[str, int] = {}
        by_priority: Dict[str, int] = {}

        for finding in all_findings:
            cat = finding.category.value
            prio = finding.priority.value
            by_category[cat] = by_category.get(cat, 0) + 1
            by_priority[prio] = by_priority.get(prio, 0) + 1

        summary = AnalysisSummary(
            total_findings=len(all_findings),
            by_category=by_category,
            by_priority=by_priority,
            execution_time_ms=round(execution_duration_ms, 2),
        )

        analysis_id = f"ANL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

        # Record durable audit trail entry
        self.audit_service.record_event(
            action="signal_analyzed",
            outcome="success",
            case_id=item.case_id,
            evidence_id=item.id,
            details={
                "analysis_id": analysis_id,
                "total_findings": len(all_findings),
                "by_category": by_category,
                "by_priority": by_priority,
                "execution_time_ms": round(execution_duration_ms, 2),
            },
        )

        logger.info(
            "Completed signal analysis for evidence '%s' in %.2f ms. Total findings: %d",
            evidence_id,
            execution_duration_ms,
            len(all_findings),
        )

        return AnalysisResponse(
            analysis_id=analysis_id,
            evidence_id=item.id,
            source_sha256=item.sha256_hash,
            created_at=datetime.now(timezone.utc).isoformat(),
            execution_status="completed",
            summary=summary,
            findings=all_findings,
            parameters_applied=applied_params,
        )
