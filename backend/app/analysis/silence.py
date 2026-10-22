"""Silence and low-energy interval detector.

Calculates short-time Root Mean Square (RMS) energy across configurable sliding windows:
    RMS = sqrt((1/N) * sum(x_i^2))
Identifies contiguous segments where energy drops below the specified threshold for at
least the minimum interval duration.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np
from backend.app.schemas.analysis import (
    FindingCategory,
    ForensicFinding,
    ReviewPriority,
    SilenceDetectionParams,
)

ALGORITHM_VERSION = "1.0.0"
DETECTOR_NAME = "silence_interval_detector"


def detect_silence_intervals(
    samples: np.ndarray,
    sample_rate: int,
    evidence_id: str,
    source_sha256: str,
    params: Optional[SilenceDetectionParams] = None,
) -> List[ForensicFinding]:
    """Detects contiguous silence or low-energy intervals in the decoded audio signal.

    Args:
        samples: Decoded floating-point audio array (1D mono or 2D multichannel).
        sample_rate: Sampling frequency in Hertz.
        evidence_id: Unique evidence identifier.
        source_sha256: Intake cryptographic hash.
        params: Configurable detection thresholds and windowing options.

    Returns:
        List of ForensicFinding instances detailing flagged low-energy intervals.
    """
    if params is None:
        params = SilenceDetectionParams()

    if samples.size == 0 or sample_rate <= 0:
        return []

    # Handle multichannel audio by averaging squared amplitude across channels
    if samples.ndim > 1:
        # Expected shape (samples, channels) or (channels, samples)
        if samples.shape[0] < samples.shape[1] and samples.shape[0] <= 8:
            samples = samples.T  # Transpose to (samples, channels)
        squared = np.mean(samples**2, axis=-1)
        total_samples = samples.shape[0]
    else:
        squared = samples**2
        total_samples = samples.shape[0]

    audio_duration = total_samples / float(sample_rate)

    window_len = max(1, int(round(params.window_duration_seconds * sample_rate)))
    hop_len = max(1, int(round(params.hop_duration_seconds * sample_rate)))

    if total_samples < window_len:
        # Audio is shorter than a single window: evaluate whole file
        rms = float(np.sqrt(np.mean(squared)))
        if rms < params.rms_threshold and audio_duration >= params.min_silence_duration_seconds:
            return [
                _create_silence_finding(
                    evidence_id=evidence_id,
                    source_sha256=source_sha256,
                    start_time=0.0,
                    end_time=audio_duration,
                    min_rms=rms,
                    mean_rms=rms,
                    threshold=params.rms_threshold,
                    params=params.model_dump(),
                )
            ]
        return []

    # Calculate short-time RMS energy across sliding frames
    num_frames = max(1, int(np.ceil((total_samples - window_len) / hop_len)) + 1)
    frame_rms = np.zeros(num_frames, dtype=np.float32)

    for i in range(num_frames):
        start_idx = i * hop_len
        end_idx = min(start_idx + window_len, total_samples)
        if start_idx >= total_samples:
            break
        frame_squared = squared[start_idx:end_idx]
        if frame_squared.size > 0:
            frame_rms[i] = np.sqrt(np.mean(frame_squared))

    # Identify frames below threshold
    is_silent = frame_rms < params.rms_threshold

    findings: List[ForensicFinding] = []
    in_interval = False
    start_frame = 0

    for i in range(num_frames):
        if is_silent[i] and not in_interval:
            in_interval = True
            start_frame = i
        elif not is_silent[i] and in_interval:
            in_interval = False
            end_frame = i - 1
            interval_findings = _evaluate_interval(
                start_frame=start_frame,
                end_frame=end_frame,
                frame_rms=frame_rms,
                hop_len=hop_len,
                window_len=window_len,
                sample_rate=sample_rate,
                audio_duration=audio_duration,
                evidence_id=evidence_id,
                source_sha256=source_sha256,
                params=params,
            )
            if interval_findings:
                findings.append(interval_findings)

    # Handle trailing interval reaching end of audio
    if in_interval:
        end_frame = num_frames - 1
        interval_findings = _evaluate_interval(
            start_frame=start_frame,
            end_frame=end_frame,
            frame_rms=frame_rms,
            hop_len=hop_len,
            window_len=window_len,
            sample_rate=sample_rate,
            audio_duration=audio_duration,
            evidence_id=evidence_id,
            source_sha256=source_sha256,
            params=params,
        )
        if interval_findings:
            findings.append(interval_findings)

    return findings


def _evaluate_interval(
    start_frame: int,
    end_frame: int,
    frame_rms: np.ndarray,
    hop_len: int,
    window_len: int,
    sample_rate: int,
    audio_duration: float,
    evidence_id: str,
    source_sha256: str,
    params: SilenceDetectionParams,
) -> Optional[ForensicFinding]:
    """Helper to convert contiguous silent frames into a validated ForensicFinding."""
    start_time = max(0.0, (start_frame * hop_len) / float(sample_rate))
    end_time = min(audio_duration, ((end_frame * hop_len) + window_len) / float(sample_rate))
    duration = end_time - start_time

    if duration < params.min_silence_duration_seconds:
        return None

    interval_rms = frame_rms[start_frame : end_frame + 1]
    min_rms = float(np.min(interval_rms)) if interval_rms.size > 0 else 0.0
    mean_rms = float(np.mean(interval_rms)) if interval_rms.size > 0 else 0.0

    return _create_silence_finding(
        evidence_id=evidence_id,
        source_sha256=source_sha256,
        start_time=round(start_time, 4),
        end_time=round(end_time, 4),
        min_rms=round(min_rms, 6),
        mean_rms=round(mean_rms, 6),
        threshold=params.rms_threshold,
        params=params.model_dump(),
    )


def _create_silence_finding(
    evidence_id: str,
    source_sha256: str,
    start_time: float,
    end_time: float,
    min_rms: float,
    mean_rms: float,
    threshold: float,
    params: Dict[str, Any],
) -> ForensicFinding:
    """Creates a validated ForensicFinding object for a silence interval."""
    duration = max(0.0, end_time - start_time)
    finding_id = f"FIND-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

    # Prioritization: True digital zero (RMS < 1e-6) or long silence (> 2.0s) warrants higher review priority
    if min_rms < 1e-6 and duration >= 1.0:
        priority = ReviewPriority.MEDIUM
        explanation = (
            f"True digital silence detected ({duration:.2f}s, min RMS: {min_rms:.6f}). "
            f"Exact zero-amplitude intervals rarely occur naturally in acoustic microphone recordings and may indicate "
            f"digital muting, cutting, or padding."
        )
    elif duration >= 3.0:
        priority = ReviewPriority.MEDIUM
        explanation = (
            f"Extended low-energy interval detected ({duration:.2f}s, mean RMS: {mean_rms:.6f} below threshold {threshold}). "
            f"Prolonged acoustic pause warrants review for missing ambient background room tone."
        )
    else:
        priority = ReviewPriority.LOW
        explanation = (
            f"Low-energy acoustic segment detected ({duration:.2f}s, mean RMS: {mean_rms:.6f} below threshold {threshold}). "
            f"Consistent with natural speech pauses, ambient dropouts, or sentence boundaries."
        )

    suggested_action = (
        "Inspect interval in waveform view to determine whether ambient background noise drops to absolute zero "
        "or transitions abruptly at boundary timestamps."
    )

    return ForensicFinding(
        id=finding_id,
        evidence_id=evidence_id,
        source_sha256=source_sha256,
        detector_name=DETECTOR_NAME,
        algorithm_version=ALGORITHM_VERSION,
        category=FindingCategory.SILENCE,
        priority=priority,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=round(duration, 4),
        event_time=round(start_time, 4),
        metric_name="rms_energy",
        measured_value=round(mean_rms, 6),
        applied_threshold=threshold,
        units="linear_rms",
        parameters=params,
        explanation=explanation,
        suggested_action=suggested_action,
    )
