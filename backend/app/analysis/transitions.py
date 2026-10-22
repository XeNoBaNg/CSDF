"""Abrupt amplitude transition detector.

Measures adjacent-sample or short-window amplitude discontinuities:
    Delta x[n] = |x[n] - x[n-1]|
Flags sharp step transitions exceeding the configured threshold while enforcing a
minimum temporal separation to prevent duplicate findings from a single transient.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np
from backend.app.schemas.analysis import (
    FindingCategory,
    ForensicFinding,
    ReviewPriority,
    TransitionDetectionParams,
)

ALGORITHM_VERSION = "1.0.0"
DETECTOR_NAME = "amplitude_transition_detector"


def detect_amplitude_transitions(
    samples: np.ndarray,
    sample_rate: int,
    evidence_id: str,
    source_sha256: str,
    params: Optional[TransitionDetectionParams] = None,
) -> List[ForensicFinding]:
    """Detects unusually large adjacent-sample amplitude transitions in decoded audio.

    Args:
        samples: Decoded floating-point audio array (1D mono or 2D multichannel).
        sample_rate: Sampling frequency in Hertz.
        evidence_id: Unique evidence identifier.
        source_sha256: Intake cryptographic hash.
        params: Configurable detection thresholds and separation options.

    Returns:
        List of ForensicFinding instances detailing flagged amplitude discontinuities.
    """
    if params is None:
        params = TransitionDetectionParams()

    if samples.size < 2 or sample_rate <= 0:
        return []

    # Handle multichannel audio: evaluate maximum absolute difference across all channels
    if samples.ndim > 1:
        if samples.shape[0] < samples.shape[1] and samples.shape[0] <= 8:
            samples = samples.T  # Transpose to (samples, channels)
        diff = np.max(np.abs(np.diff(samples, axis=0)), axis=-1)
        total_samples = samples.shape[0]
    else:
        diff = np.abs(np.diff(samples))
        total_samples = samples.shape[0]

    audio_duration = total_samples / float(sample_rate)
    min_separation_samples = max(1, int(round(params.min_separation_seconds * sample_rate)))

    # Find sample indices exceeding threshold
    candidate_indices = np.where(diff >= params.threshold)[0]
    if len(candidate_indices) == 0:
        return []

    # Non-maximum suppression / temporal separation clustering:
    # Group candidates within min_separation_samples and pick the peak spike
    clustered_peaks: List[int] = []
    current_cluster: List[int] = [candidate_indices[0]]

    for idx in candidate_indices[1:]:
        if idx - current_cluster[-1] <= min_separation_samples:
            current_cluster.append(idx)
        else:
            # Pick the index with the maximum difference in current cluster
            best_idx = current_cluster[int(np.argmax(diff[current_cluster]))]
            clustered_peaks.append(best_idx)
            current_cluster = [idx]

    if current_cluster:
        best_idx = current_cluster[int(np.argmax(diff[current_cluster]))]
        clustered_peaks.append(best_idx)

    # Convert peak indices into ForensicFinding objects
    findings: List[ForensicFinding] = []
    for peak_idx in clustered_peaks:
        event_time = (peak_idx + 1) / float(sample_rate)
        measured_val = float(diff[peak_idx])

        start_time = max(0.0, event_time - params.context_window_seconds)
        end_time = min(audio_duration, event_time + params.context_window_seconds)
        duration = end_time - start_time

        finding = _create_transition_finding(
            evidence_id=evidence_id,
            source_sha256=source_sha256,
            event_time=round(event_time, 4),
            start_time=round(start_time, 4),
            end_time=round(end_time, 4),
            duration=round(duration, 4),
            measured_diff=round(measured_val, 4),
            threshold=params.threshold,
            params=params.model_dump(),
        )
        findings.append(finding)

    return findings


def _create_transition_finding(
    evidence_id: str,
    source_sha256: str,
    event_time: float,
    start_time: float,
    end_time: float,
    duration: float,
    measured_diff: float,
    threshold: float,
    params: Dict[str, Any],
) -> ForensicFinding:
    """Creates a validated ForensicFinding for an amplitude transition."""
    finding_id = f"FIND-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

    if measured_diff >= 0.70:
        priority = ReviewPriority.HIGH
        explanation = (
            f"Severe instantaneous amplitude step of {measured_diff:.4f} detected at T={event_time:.3f}s "
            f"(threshold: {threshold:.2f}). A discontinuity of this magnitude strongly suggests an abrupt edit splice, "
            f"recording start/stop glitch, or violent signal clipping."
        )
    elif measured_diff >= 0.45:
        priority = ReviewPriority.MEDIUM
        explanation = (
            f"Moderate amplitude step of {measured_diff:.4f} detected at T={event_time:.3f}s "
            f"(threshold: {threshold:.2f}). Exceeds typical continuous speech gradients; may indicate a splice, pop, or transient onset."
        )
    else:
        priority = ReviewPriority.LOW
        explanation = (
            f"Mild amplitude transition of {measured_diff:.4f} detected at T={event_time:.3f}s "
            f"(threshold: {threshold:.2f}). Likely consistent with sharp plosive consonants (p/t/k), drum transients, or mic handling."
        )

    suggested_action = (
        "Inspect the waveform at the exact timestamp under high zoom to verify whether sample values "
        "step abruptly across the zero axis without a natural sinusoidal curve."
    )

    return ForensicFinding(
        id=finding_id,
        evidence_id=evidence_id,
        source_sha256=source_sha256,
        detector_name=DETECTOR_NAME,
        algorithm_version=ALGORITHM_VERSION,
        category=FindingCategory.TRANSITION,
        priority=priority,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration,
        event_time=event_time,
        metric_name="adjacent_amplitude_difference",
        measured_value=measured_diff,
        applied_threshold=threshold,
        units="delta_amplitude",
        parameters=params,
        explanation=explanation,
        suggested_action=suggested_action,
    )
