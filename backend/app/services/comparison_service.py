"""Service layer for cross-recording forensic comparison."""

import hmac
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np
from backend.app.analysis.comparison import (
    compare_anomaly_timelines,
    compare_spectral_distributions,
    compute_envelope_correlation,
    compute_signal_statistics,
    compute_spectral_profile,
)
from backend.app.analysis.decoder import verify_and_load_audio
from backend.app.analysis.silence import detect_silence_intervals
from backend.app.analysis.spectral import detect_spectral_inconsistencies
from backend.app.analysis.transitions import detect_amplitude_transitions
from backend.app.services.audit_service import AuditService
from backend.app.core.errors import EvidenceNotFoundError
from backend.app.models.comparison import ComparisonRecordModel
from backend.app.repositories.comparison_repository import ComparisonRepository
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.schemas.comparison import (
    AnomalyComparison,
    ComparisonRequest,
    ComparisonResponse,
    ComparisonSummary,
    MetadataComparison,
    SignalComparison,
    SpectralComparison,
)

logger = logging.getLogger("audiosleuth.services.comparison")

DISCLAIMER_TEXT = (
    "Forensic Disclaimer: Cross-recording comparisons evaluate objective signal metrics, frequency distributions, "
    "and anomaly temporal profiles. Matching SHA-256 hashes confirm byte-for-byte identity of the compared files, "
    "but do not establish historical authenticity. Differing hashes may result from re-encoding, format conversion, "
    "or metadata edits of identical audible content. High spectral similarity does not establish common acoustic source, "
    "microphone attribution, or speaker identity. Algorithmic comparisons are investigative screening aids and do not "
    "constitute automated forensic determinations of authenticity or manipulation."
)


class ComparisonService:
    """Orchestrates cross-recording forensic comparison analysis, persistence, and audit logging."""

    def __init__(
        self,
        evidence_repo: Optional[EvidenceRepository] = None,
        comparison_repo: Optional[ComparisonRepository] = None,
        audit_service: Optional[AuditService] = None,
    ):
        self.evidence_repo = evidence_repo or EvidenceRepository()
        self.comparison_repo = comparison_repo or ComparisonRepository()
        self.audit_service = audit_service or AuditService()

    def compare_evidence(self, request: ComparisonRequest) -> ComparisonResponse:
        """Executes a forensic comparison between two registered evidence recordings."""
        logger.info(
            "Initiating forensic comparison: Item A='%s' vs Item B='%s'",
            request.evidence_id_a,
            request.evidence_id_b,
        )

        # 1. Validate both evidence records exist
        item_a = self.evidence_repo.get_by_id(request.evidence_id_a)
        if not item_a:
            raise EvidenceNotFoundError(
                evidence_id=request.evidence_id_a,
                message=f"Primary evidence item '{request.evidence_id_a}' was not found.",
            )

        item_b = self.evidence_repo.get_by_id(request.evidence_id_b)
        if not item_b:
            raise EvidenceNotFoundError(
                evidence_id=request.evidence_id_b,
                message=f"Secondary evidence item '{request.evidence_id_b}' was not found.",
            )

        # 2. Re-verify cryptographic integrity and decode both audio files non-destructively
        # verify_and_load_audio automatically raises EvidenceIntegrityError if hashes mismatch
        samples_a, sr_a, meta_a = verify_and_load_audio(item_a)
        samples_b, sr_b, meta_b = verify_and_load_audio(item_b)

        # 3. Metadata Comparison
        dur_a = float(meta_a["duration"])
        dur_b = float(meta_b["duration"])
        dur_diff = abs(dur_a - dur_b)
        sha256_match = bool(hmac.compare_digest(item_a.sha256_hash.lower(), item_b.sha256_hash.lower()))

        metadata_comp = MetadataComparison(
            filename_a=item_a.original_filename,
            filename_b=item_b.original_filename,
            format_a=item_a.format,
            format_b=item_b.format,
            format_match=(item_a.format.lower() == item_b.format.lower()),
            file_size_bytes_a=item_a.file_size_bytes,
            file_size_bytes_b=item_b.file_size_bytes,
            file_size_diff_bytes=abs(item_a.file_size_bytes - item_b.file_size_bytes),
            sha256_a=item_a.sha256_hash,
            sha256_b=item_b.sha256_hash,
            sha256_match=sha256_match,
            duration_seconds_a=round(dur_a, 4),
            duration_seconds_b=round(dur_b, 4),
            duration_diff_seconds=round(dur_diff, 4),
            duration_match=(dur_diff <= 0.05),
            sample_rate_hz_a=sr_a,
            sample_rate_hz_b=sr_b,
            sample_rate_match=(sr_a == sr_b),
            channels_a=meta_a["channels"],
            channels_b=meta_b["channels"],
            channels_match=(meta_a["channels"] == meta_b["channels"]),
            bit_depth_a=meta_a.get("bit_depth"),
            bit_depth_b=meta_b.get("bit_depth"),
            bit_depth_match=(meta_a.get("bit_depth") == meta_b.get("bit_depth")),
        )

        # 4. Signal-Level Comparison
        stats_a = compute_signal_statistics(samples_a, sr_a)
        stats_b = compute_signal_statistics(samples_b, sr_b)

        peak_diff = abs(stats_a["peak_amplitude"] - stats_b["peak_amplitude"])
        rms_diff = abs(stats_a["rms_energy"] - stats_b["rms_energy"])
        zcr_diff = abs(stats_a["zero_crossing_rate"] - stats_b["zero_crossing_rate"])

        # RMS ratio in dB
        eps = 1e-8
        rms_ratio_db = round(float(20.0 * np.log10((stats_a["rms_energy"] + eps) / (stats_b["rms_energy"] + eps))), 2)

        # Macro-amplitude envelope correlation
        env_corr = compute_envelope_correlation(samples_a, samples_b, num_points=request.envelope_points)

        signal_comp = SignalComparison(
            peak_amplitude_a=stats_a["peak_amplitude"],
            peak_amplitude_b=stats_b["peak_amplitude"],
            peak_amplitude_diff=round(peak_diff, 5),
            rms_energy_a=stats_a["rms_energy"],
            rms_energy_b=stats_b["rms_energy"],
            rms_energy_diff=round(rms_diff, 5),
            rms_ratio_db=rms_ratio_db,
            crest_factor_a=stats_a["crest_factor"],
            crest_factor_b=stats_b["crest_factor"],
            zero_crossing_rate_a=stats_a["zero_crossing_rate"],
            zero_crossing_rate_b=stats_b["zero_crossing_rate"],
            zero_crossing_rate_diff=round(zcr_diff, 2),
            envelope_correlation=env_corr,
            channel_mixdown_policy="mean_across_channels",
        )

        # 5. Spectral Comparison
        # Evaluate up to the minimum shared Nyquist ceiling
        max_shared_nyquist = min(sr_a / 2.0, sr_b / 2.0)
        profile_a = compute_spectral_profile(samples_a, sr_a, max_freq_hz=max_shared_nyquist)
        profile_b = compute_spectral_profile(samples_b, sr_b, max_freq_hz=max_shared_nyquist)

        spectral_diffs = compare_spectral_distributions(profile_a, profile_b, num_eval_bins=request.spectral_bins)

        spectral_comp = SpectralComparison(
            centroid_hz_a=profile_a["spectral_centroid_hz"],
            centroid_hz_b=profile_b["spectral_centroid_hz"],
            centroid_diff_hz=spectral_diffs["centroid_diff_hz"],
            rolloff_hz_a=profile_a["spectral_rolloff_hz"],
            rolloff_hz_b=profile_b["spectral_rolloff_hz"],
            rolloff_diff_hz=spectral_diffs["rolloff_diff_hz"],
            flatness_a=profile_a["spectral_flatness"],
            flatness_b=profile_b["spectral_flatness"],
            flatness_diff=spectral_diffs["flatness_diff"],
            spectral_cosine_similarity=spectral_diffs["cosine_similarity"],
            spectral_euclidean_distance=spectral_diffs["euclidean_distance"],
            evaluated_frequency_ceiling_hz=round(max_shared_nyquist, 1),
        )

        # 6. Optional Anomaly Timeline Comparison
        anomaly_comp: Optional[AnomalyComparison] = None
        if request.include_anomaly_comparison:
            findings_a = (
                detect_silence_intervals(samples_a, sr_a, item_a.id, item_a.sha256_hash)
                + detect_amplitude_transitions(samples_a, sr_a, item_a.id, item_a.sha256_hash)
                + detect_spectral_inconsistencies(samples_a, sr_a, item_a.id, item_a.sha256_hash)
            )
            findings_b = (
                detect_silence_intervals(samples_b, sr_b, item_b.id, item_b.sha256_hash)
                + detect_amplitude_transitions(samples_b, sr_b, item_b.id, item_b.sha256_hash)
                + detect_spectral_inconsistencies(samples_b, sr_b, item_b.id, item_b.sha256_hash)
            )

            anomaly_data = compare_anomaly_timelines(findings_a, dur_a, findings_b, dur_b, num_bins=10)

            anomaly_comp = AnomalyComparison(
                total_findings_a=anomaly_data["counts_a"]["total"],
                total_findings_b=anomaly_data["counts_b"]["total"],
                silence_findings_a=anomaly_data["counts_a"]["silence"],
                silence_findings_b=anomaly_data["counts_b"]["silence"],
                transition_findings_a=anomaly_data["counts_a"]["transition"],
                transition_findings_b=anomaly_data["counts_b"]["transition"],
                spectral_findings_a=anomaly_data["counts_a"]["spectral"],
                spectral_findings_b=anomaly_data["counts_b"]["spectral"],
                findings_density_per_min_a=anomaly_data["density_per_minute_a"],
                findings_density_per_min_b=anomaly_data["density_per_minute_b"],
                binned_distribution_a=anomaly_data["binned_distribution_a"],
                binned_distribution_b=anomaly_data["binned_distribution_b"],
                timeline_bins=anomaly_data["distribution_bins"],
            )

        # 7. Summary & Transparent Scoring
        warnings: List[str] = []
        if sr_a != sr_b:
            warnings.append(
                f"Sampling rates differ ({sr_a} Hz vs {sr_b} Hz). Comparison evaluated up to shared Nyquist ceiling of {max_shared_nyquist:.0f} Hz."
            )
        if meta_a["channels"] != meta_b["channels"]:
            warnings.append(
                f"Channel counts differ ({meta_a['channels']} vs {meta_b['channels']}). Both downmixed to mono for analysis."
            )
        if dur_diff > 1.0:
            warnings.append(
                f"Significant duration disparity ({dur_a:.2f}s vs {dur_b:.2f}s, delta={dur_diff:.2f}s). Macro-envelope correlation may be skewed."
            )
        if not sha256_match and spectral_diffs["cosine_similarity"] >= 0.98 and metadata_comp.duration_match:
            warnings.append(
                "High spectral and duration alignment despite different hashes: consistent with re-encoding, tag editing, or container format conversion."
            )

        # Transparent similarity index calculation
        # Formula: 0.50 * SpectralCosine + 0.30 * max(0, EnvCorr) + 0.20 * max(0, 1 - (dur_diff / max(dur_a, dur_b)))
        max_dur = max(dur_a, dur_b, 1e-4)
        dur_term = max(0.0, 1.0 - (dur_diff / max_dur))
        spec_term = spectral_diffs["cosine_similarity"]
        env_term = max(0.0, env_corr)
        score = (0.50 * spec_term) + (0.30 * env_term) + (0.20 * dur_term)
        score = round(float(np.clip(score, 0.0, 1.0)), 4)

        if sha256_match:
            label = "Byte-Identical Duplicate"
            explanation = (
                "Cryptographic SHA-256 hashes match identically. The two recordings represent byte-for-byte exact copies. "
                "All acoustic, spectral, and metadata parameters are identical."
            )
        elif score >= 0.92 and metadata_comp.duration_match:
            label = "Very High Acoustic Similarity"
            explanation = (
                f"Recordings exhibit very high spectral similarity ({spec_term:.4f}) and envelope correlation ({env_term:.4f}) "
                f"with minimal duration difference ({dur_diff:.3f}s). Typical of identical audio stored under different container formats or re-encoded."
            )
        elif score >= 0.70:
            label = "Moderate Similarity"
            explanation = (
                f"Recordings share moderate spectral characteristics ({spec_term:.4f}) with some acoustic or duration divergence "
                f"(delta={dur_diff:.3f}s). May represent different takes, partial edits, or different background environments."
            )
        else:
            label = "Divergent Acoustic Profiles"
            explanation = (
                f"Recordings exhibit divergent spectral ({spec_term:.4f}) and amplitude characteristics. "
                f"Signal parameters and anomaly distributions indicate distinct acoustic contents."
            )

        formula_expl = (
            "Similarity Score = 0.50 × SpectralCosineSimilarity + 0.30 × max(0, EnvelopeCorrelation) + 0.20 × max(0, 1 - DurationDelta/MaxDuration). "
            "All components normalized to [0, 1]. Provides transparent heuristic indication of macro-acoustic alignment."
        )

        summary = ComparisonSummary(
            byte_match=sha256_match,
            duration_match=metadata_comp.duration_match,
            acoustic_similarity_label=label,
            transparent_similarity_score=score,
            scoring_formula_explanation=formula_expl,
            warnings=warnings,
            explanation=explanation,
        )

        comparison_id = f"COMP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        response = ComparisonResponse(
            id=comparison_id,
            timestamp=timestamp,
            evidence_id_a=item_a.id,
            evidence_id_b=item_b.id,
            case_id_a=item_a.case_id,
            case_id_b=item_b.case_id,
            metadata_comparison=metadata_comp,
            signal_comparison=signal_comp,
            spectral_comparison=spectral_comp,
            anomaly_comparison=anomaly_comp,
            summary=summary,
            disclaimer=DISCLAIMER_TEXT,
        )

        # 8. Persist comparison record in database
        try:
            record = ComparisonRecordModel(
                id=comparison_id,
                evidence_id_a=item_a.id,
                evidence_id_b=item_b.id,
                case_id_a=item_a.case_id,
                case_id_b=item_b.case_id,
                hash_a=item_a.sha256_hash,
                hash_b=item_b.sha256_hash,
                metrics_summary_json=response.model_dump_json(),
                created_at=timestamp,
            )
            self.comparison_repo.create(record)
        except Exception as exc:
            logger.warning("Failed to persist comparison record in SQLite: %s", exc)

        # 9. Emit durable audit event
        try:
            self.audit_service.record_event(
                action="evidence_compared",
                outcome="success",
                case_id=item_a.case_id if item_a.case_id == item_b.case_id else None,
                evidence_id=item_a.id,
                details={
                    "comparison_id": comparison_id,
                    "evidence_id_a": item_a.id,
                    "evidence_id_b": item_b.id,
                    "hash_a": item_a.sha256_hash,
                    "hash_b": item_b.sha256_hash,
                    "byte_match": sha256_match,
                    "spectral_similarity": spectral_comp.spectral_cosine_similarity,
                    "envelope_correlation": signal_comp.envelope_correlation,
                    "similarity_score": score,
                    "similarity_label": label,
                },
            )
        except Exception as exc:
            logger.warning("Failed to log audit event for comparison: %s", exc)

        logger.info(
            "Forensic comparison completed: ID=%s, Score=%.4f (%s)",
            comparison_id,
            score,
            label,
        )
        return response

    def get_comparison(self, comparison_id: str) -> Optional[ComparisonResponse]:
        """Retrieves a persisted comparison result by ID."""
        record = self.comparison_repo.get_by_id(comparison_id)
        if not record:
            return None
        try:
            data = json.loads(record.metrics_summary_json)
            return ComparisonResponse.model_validate(data)
        except Exception as exc:
            logger.error("Failed to parse stored comparison summary JSON: %s", exc)
            return None
