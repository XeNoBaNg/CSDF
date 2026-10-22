"""FFT frequency spectrum generation."""

import logging
from typing import List, Optional
import numpy as np
from backend.app.core.config import settings
from backend.app.schemas.audio import SpectrumResponse

logger = logging.getLogger("audiosleuth.analysis.spectrum")


def generate_spectrum_data(
    samples: np.ndarray,
    sample_rate: int,
    evidence_id: str,
    source_sha256: str,
    max_bins: int = 512,
    max_frequency: Optional[float] = None,
) -> SpectrumResponse:
    """Computes an FFT-based amplitude/power spectrum in decibels across the audio signal,
    providing calibrated frequency axes and dominant peak detection.
    """
    max_bins = max(32, min(max_bins, settings.MAX_SPECTRUM_BINS))
    nyquist = float(sample_rate / 2.0) if sample_rate > 0 else 0.0

    # 1. Mixdown to mono
    if samples.ndim > 1:
        mono = np.mean(samples, axis=1)
    else:
        mono = samples

    total_samples = len(mono)

    if total_samples == 0 or sample_rate <= 0:
        return SpectrumResponse(
            evidence_id=evidence_id,
            source_sha256=source_sha256,
            sample_rate_hz=sample_rate,
            nyquist_hz=nyquist,
            num_bins=0,
            frequencies_hz=[],
            magnitudes_db=[],
            dominant_frequency_hz=None,
            dominant_magnitude_db=None,
        )

    # 2. Windowing to reduce spectral leakage
    window = np.hanning(total_samples)
    windowed = mono * window

    # 3. One-sided Real FFT
    fft_vals = np.fft.rfft(windowed)
    freqs = np.fft.rfftfreq(total_samples, d=1.0 / sample_rate)

    # Scale magnitude: normalize by effective window coherent gain (0.5 for Hann)
    coherent_gain = np.sum(window) if np.sum(window) > 0 else 1.0
    linear_mag = (2.0 * np.abs(fft_vals)) / coherent_gain
    mag_db = 20.0 * np.log10(np.maximum(linear_mag, 1e-9))
    mag_db = np.nan_to_num(mag_db, nan=-120.0, posinf=0.0, neginf=-120.0)

    # 4. Restrict to specified max frequency (or Nyquist)
    cutoff = min(max_frequency, nyquist) if max_frequency and max_frequency > 0 else nyquist
    valid_mask = freqs <= cutoff
    freqs = freqs[valid_mask]
    mag_db = mag_db[valid_mask]

    # 5. Dominant Peak Frequency Detection (ignoring DC at index 0)
    dominant_freq = None
    dominant_db = None
    if len(freqs) > 1:
        # Search above 10 Hz to ignore DC offset
        search_start = np.searchsorted(freqs, 10.0)
        if search_start < len(freqs):
            peak_offset = np.argmax(mag_db[search_start:])
            peak_idx = search_start + peak_offset
            dominant_freq = round(float(freqs[peak_idx]), 2)
            dominant_db = round(float(mag_db[peak_idx]), 2)

    # 6. Downsample if number of bins exceeds max_bins budget
    if len(freqs) > max_bins:
        indices = np.linspace(0, len(freqs) - 1, max_bins, dtype=int)
        freqs = freqs[indices]
        mag_db = mag_db[indices]

    clean_freqs = [round(float(f), 2) for f in freqs]
    clean_mags = [round(float(m), 2) for m in mag_db]

    return SpectrumResponse(
        evidence_id=evidence_id,
        source_sha256=source_sha256,
        sample_rate_hz=sample_rate,
        nyquist_hz=round(nyquist, 2),
        window_type="hann",
        num_bins=len(clean_freqs),
        frequencies_hz=clean_freqs,
        magnitudes_db=clean_mags,
        dominant_frequency_hz=dominant_freq,
        dominant_magnitude_db=dominant_db,
    )
