"""Spectral inconsistency detector using STFT Spectral Flux.

Measures the Euclidean distance between consecutive L2-normalized STFT magnitude frames:
    SF(t) = sqrt( sum_k ( X_norm(t, k) - X_norm(t-1, k) )^2 )
where X_norm(t, k) = X(t, k) / ( ||X(t)||_2 + eps )

Detects abrupt redistributions of frequency energy between adjacent time frames
while enforcing non-maximum suppression to report discrete spectral anomaly events.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np
from scipy import signal
from backend.app.schemas.analysis import (
    FindingCategory,
    ForensicFinding,
    ReviewPriority,
    SpectralDetectionParams,
)

ALGORITHM_VERSION = "1.0.0"
DETECTOR_NAME = "spectral_flux_detector"


def detect_spectral_inconsistencies(
    samples: np.ndarray,
    sample_rate: int,
    evidence_id: str,
    source_sha256: str,
    params: Optional[SpectralDetectionParams] = None,
) -> List[ForensicFinding]:
    """Detects spectral inconsistency events using short-time Fourier transform spectral flux.

    Args:
        samples: Decoded floating-point audio array (1D mono or 2D multichannel).
        sample_rate: Sampling frequency in Hertz.
        evidence_id: Unique evidence identifier.
        source_sha256: Intake cryptographic hash.
        params: Configurable STFT parameters, detection threshold, and temporal suppression.

    Returns:
        List of ForensicFinding instances detailing flagged spectral flux peaks.
    """
    if params is None:
        params = SpectralDetectionParams()

    if samples.size == 0 or sample_rate <= 0:
        return []

    # Downmix multichannel audio to mono for joint spectral evaluation
    if samples.ndim > 1:
        if samples.shape[0] < samples.shape[1] and samples.shape[0] <= 8:
            samples = samples.T
        mono_samples = np.mean(samples, axis=-1)
        total_samples = samples.shape[0]
    else:
        mono_samples = samples
        total_samples = samples.shape[0]

    audio_duration = total_samples / float(sample_rate)

    n_fft = params.n_fft
    hop_length = params.hop_length

    # Require at least two STFT analysis windows
    if total_samples < n_fft + hop_length:
        return []

    # Compute STFT magnitude spectrogram using SciPy
    _, time_bins, zxx = signal.stft(
        mono_samples,
        fs=sample_rate,
        window="hann",
        nperseg=n_fft,
        noverlap=n_fft - hop_length,
        boundary=None,
        padded=False,
    )

    magnitudes = np.abs(zxx)  # Shape: (freq_bins, time_frames)
    num_frames = magnitudes.shape[1]

    if num_frames < 2:
        return []

    # L2-normalize each time frame to make flux invariant to absolute audio volume
    eps = 1e-8
    norms = np.linalg.norm(magnitudes, axis=0, keepdims=True)  # Shape: (1, time_frames)

    # If a frame has near-zero energy (pure silence), leave it as zero vector
    is_silent_frame = norms < 1e-6
    normalized_mag = np.where(is_silent_frame, 0.0, magnitudes / (norms + eps))

    # Compute Euclidean distance between adjacent normalized frames
    diff = np.diff(normalized_mag, axis=1)  # Shape: (freq_bins, num_frames - 1)
    spectral_flux = np.sqrt(np.sum(diff**2, axis=0))  # Shape: (num_frames - 1,)

    # Frame times corresponding to flux transitions (frame t to t+1)
    flux_times = time_bins[1:]

    # Candidate frame indices exceeding configured threshold
    candidate_indices = np.where(spectral_flux >= params.threshold)[0]
    if len(candidate_indices) == 0:
        return []

    # Temporal non-maximum suppression: cluster candidate frames within min_separation
    min_separation_frames = max(1, int(round((params.min_separation_seconds * sample_rate) / hop_length)))

    clustered_peaks: List[int] = []
    current_cluster: List[int] = [candidate_indices[0]]

    for idx in candidate_indices[1:]:
        if idx - current_cluster[-1] <= min_separation_frames:
            current_cluster.append(idx)
        else:
            best_idx = current_cluster[int(np.argmax(spectral_flux[current_cluster]))]
            clustered_peaks.append(best_idx)
            current_cluster = [idx]

    if current_cluster:
        best_idx = current_cluster[int(np.argmax(spectral_flux[current_cluster]))]
        clustered_peaks.append(best_idx)

    # Create ForensicFinding instances
    findings: List[ForensicFinding] = []
    for peak_idx in clustered_peaks:
        event_time = float(flux_times[peak_idx])
        measured_flux = float(spectral_flux[peak_idx])

        start_time = max(0.0, event_time - params.context_window_seconds)
        end_time = min(audio_duration, event_time + params.context_window_seconds)
        duration = end_time - start_time

        finding = _create_spectral_finding(
            evidence_id=evidence_id,
            source_sha256=source_sha256,
            event_time=round(event_time, 4),
            start_time=round(start_time, 4),
            end_time=round(end_time, 4),
            duration=round(duration, 4),
            measured_flux=round(measured_flux, 4),
            threshold=params.threshold,
            params=params.model_dump(),
        )
        findings.append(finding)

    return findings


def _create_spectral_finding(
    evidence_id: str,
    source_sha256: str,
    event_time: float,
    start_time: float,
    end_time: float,
    duration: float,
    measured_flux: float,
    threshold: float,
    params: Dict[str, Any],
) -> ForensicFinding:
    """Creates a validated ForensicFinding for a spectral flux inconsistency."""
    finding_id = f"FIND-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

    if measured_flux >= 0.85:
        priority = ReviewPriority.HIGH
        explanation = (
            f"Severe spectral flux peak of {measured_flux:.4f} detected at T={event_time:.3f}s "
            f"(threshold: {threshold:.2f}). Indicates a sudden, drastic reallocation of frequency spectrum energy "
            f"between adjacent frames, characteristic of spliced recordings or acoustic scene changes."
        )
    elif measured_flux >= 0.60:
        priority = ReviewPriority.MEDIUM
        explanation = (
            f"Moderate spectral flux peak of {measured_flux:.4f} detected at T={event_time:.3f}s "
            f"(threshold: {threshold:.2f}). Exceeds typical smooth acoustic speech transitions; warrants manual examination."
        )
    else:
        priority = ReviewPriority.LOW
        explanation = (
            f"Mild spectral flux transition of {measured_flux:.4f} detected at T={event_time:.3f}s "
            f"(threshold: {threshold:.2f}). Consistent with natural acoustic onsets, consonant attacks, or musical chord changes."
        )

    suggested_action = (
        "Inspect the STFT spectrogram heatmap before and after the timestamp to verify whether harmonic tracks "
        "and ambient background noise profiles show an unnatural discontinuity."
    )

    return ForensicFinding(
        id=finding_id,
        evidence_id=evidence_id,
        source_sha256=source_sha256,
        detector_name=DETECTOR_NAME,
        algorithm_version=ALGORITHM_VERSION,
        category=FindingCategory.SPECTRAL,
        priority=priority,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration,
        event_time=event_time,
        metric_name="normalized_spectral_flux",
        measured_value=measured_flux,
        applied_threshold=threshold,
        units="normalized_flux",
        parameters=params,
        explanation=explanation,
        suggested_action=suggested_action,
    )
