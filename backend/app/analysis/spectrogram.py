"""Time-frequency STFT spectrogram generation."""

import logging
from typing import List
import numpy as np
import scipy.signal
from backend.app.core.config import settings
from backend.app.schemas.audio import SpectrogramResponse

logger = logging.getLogger("audiosleuth.analysis.spectrogram")


def generate_spectrogram_data(
    samples: np.ndarray,
    sample_rate: int,
    evidence_id: str,
    source_sha256: str,
    n_fft: int = 1024,
    hop_length: int = 512,
    max_time_frames: int = 250,
    max_freq_bins: int = 128,
) -> SpectrogramResponse:
    """Computes a short-time Fourier transform (STFT) magnitude spectrogram in decibels (dB),
    guaranteeing finite values and bounded dimensions for browser visualization.
    """
    # 1. Parameter clamping & bounds
    n_fft = max(128, min(n_fft, 4096))
    hop_length = max(32, min(hop_length, 2048))
    max_time_frames = max(10, min(max_time_frames, settings.MAX_SPECTROGRAM_TIME_FRAMES))
    max_freq_bins = max(16, min(max_freq_bins, settings.MAX_SPECTROGRAM_FREQ_BINS))

    # 2. Channel mixdown strategy: average all channels to mono
    if samples.ndim > 1:
        mono = np.mean(samples, axis=1)
    else:
        mono = samples

    total_samples = len(mono)
    duration = float(total_samples / sample_rate) if sample_rate > 0 else 0.0

    if total_samples == 0:
        return SpectrogramResponse(
            evidence_id=evidence_id,
            source_sha256=source_sha256,
            duration_seconds=0.0,
            sample_rate_hz=sample_rate,
            n_fft=n_fft,
            hop_length=hop_length,
            min_db=-100.0,
            max_db=0.0,
            time_axis=[],
            freq_axis=[],
            magnitudes_db=[],
        )

    # 3. Handle very short signals by padding or adapting n_fft
    effective_n_fft = n_fft
    if total_samples < n_fft:
        pad_width = n_fft - total_samples
        mono = np.pad(mono, (0, pad_width), mode="constant")

    noverlap = max(0, effective_n_fft - hop_length)

    # 4. Compute STFT via SciPy
    freqs, times, Zxx = scipy.signal.stft(
        mono,
        fs=sample_rate,
        window="hann",
        nperseg=effective_n_fft,
        noverlap=noverlap,
        boundary=None,
        padded=True,
    )

    # 5. Convert to magnitude and compute decibels (dB) safely
    # Use floor of 1e-6 (-120 dB) to prevent log10(0) or -inf on silence
    mag = np.abs(Zxx)
    mag_db = 20.0 * np.log10(np.maximum(mag, 1e-6))

    # Replace any non-finite numbers
    mag_db = np.nan_to_num(mag_db, nan=-100.0, posinf=0.0, neginf=-100.0)

    # Peak normalization & dynamic range floor (-80 dB relative to peak)
    peak_db = float(np.max(mag_db))
    min_db = peak_db - 80.0
    mag_db = np.clip(mag_db, min_db, peak_db)

    # 6. Bounded grid reduction along time and frequency axes
    num_freqs = len(freqs)
    num_times = len(times)

    if num_times > max_time_frames:
        t_indices = np.linspace(0, num_times - 1, max_time_frames, dtype=int)
        times = times[t_indices]
        mag_db = mag_db[:, t_indices]

    if num_freqs > max_freq_bins:
        f_indices = np.linspace(0, num_freqs - 1, max_freq_bins, dtype=int)
        freqs = freqs[f_indices]
        mag_db = mag_db[f_indices, :]

    # 7. Format clean numeric matrix for JSON serialization
    clean_time_axis = [round(float(t), 4) for t in times]
    clean_freq_axis = [round(float(f), 1) for f in freqs]
    clean_matrix: List[List[float]] = [
        [round(float(val), 2) for val in row] for row in mag_db
    ]

    return SpectrogramResponse(
        evidence_id=evidence_id,
        source_sha256=source_sha256,
        duration_seconds=round(duration, 4),
        sample_rate_hz=sample_rate,
        n_fft=effective_n_fft,
        hop_length=hop_length,
        window_type="hann",
        unit="dB",
        min_db=round(float(np.min(mag_db)), 2),
        max_db=round(float(np.max(mag_db)), 2),
        time_axis=clean_time_axis,
        freq_axis=clean_freq_axis,
        magnitudes_db=clean_matrix,
    )
