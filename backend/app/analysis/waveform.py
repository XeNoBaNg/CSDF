"""Waveform envelope generation from decoded audio."""

import logging
from typing import List
import numpy as np
from backend.app.core.config import settings
from backend.app.schemas.audio import ChannelWaveform, WaveformResponse

logger = logging.getLogger("audiosleuth.analysis.waveform")


def generate_waveform_data(
    samples: np.ndarray,
    sample_rate: int,
    evidence_id: str,
    source_sha256: str,
    point_budget: int = 1000,
) -> WaveformResponse:
    """Generates downsampled min/max envelope waveform data from decoded audio,
    preserving transient peaks and accurate timestamps.
    """
    # 1. Enforce parameter budget limits
    point_budget = max(10, min(point_budget, settings.MAX_WAVEFORM_POINTS))

    # 2. Reshape to (N, C)
    if samples.ndim == 1:
        samples_2d = samples.reshape(-1, 1)
    else:
        samples_2d = samples

    total_samples, num_channels = samples_2d.shape
    duration = float(total_samples / sample_rate) if sample_rate > 0 else 0.0

    # 3. Overall audio statistics
    peak_amplitude = float(np.max(np.abs(samples_2d))) if total_samples > 0 else 0.0
    rms_energy = float(np.sqrt(np.mean(samples_2d**2))) if total_samples > 0 else 0.0

    time_axis: List[float] = []
    channels: List[ChannelWaveform] = []

    if total_samples == 0:
        return WaveformResponse(
            evidence_id=evidence_id,
            source_sha256=source_sha256,
            sample_rate_hz=sample_rate,
            duration_seconds=0.0,
            total_samples=0,
            point_budget=point_budget,
            downsampled=False,
            time_axis=[],
            channels=[],
            peak_amplitude=0.0,
            rms_energy=0.0,
        )

    # 4. Deterministic downsampling & aggregation
    if total_samples <= point_budget:
        # Audio is shorter than the point budget: return raw sample envelope
        downsampled = False
        time_axis = [round(float(i / sample_rate), 6) for i in range(total_samples)]
        for c in range(num_channels):
            ch_data = samples_2d[:, c]
            channels.append(
                ChannelWaveform(
                    channel_index=c,
                    min_amplitudes=[round(float(v), 5) for v in ch_data],
                    max_amplitudes=[round(float(v), 5) for v in ch_data],
                )
            )
    else:
        # Bounded aggregation: split into point_budget windows and calculate min/max
        downsampled = True
        splits = np.array_split(np.arange(total_samples), point_budget)
        time_axis = [
            round(float((split[0] + split[-1]) / (2.0 * sample_rate)), 6)
            for split in splits
        ]

        for c in range(num_channels):
            ch_data = samples_2d[:, c]
            min_vals = []
            max_vals = []
            for split in splits:
                segment = ch_data[split]
                min_vals.append(round(float(np.min(segment)), 5))
                max_vals.append(round(float(np.max(segment)), 5))

            channels.append(
                ChannelWaveform(
                    channel_index=c,
                    min_amplitudes=min_vals,
                    max_amplitudes=max_vals,
                )
            )

    return WaveformResponse(
        evidence_id=evidence_id,
        source_sha256=source_sha256,
        sample_rate_hz=sample_rate,
        duration_seconds=round(duration, 4),
        total_samples=total_samples,
        point_budget=point_budget,
        downsampled=downsampled,
        aggregation_method="min_max_windowed",
        time_axis=time_axis,
        channels=channels,
        peak_amplitude=round(peak_amplitude, 5),
        rms_energy=round(rms_energy, 5),
    )
