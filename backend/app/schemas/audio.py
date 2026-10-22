"""Pydantic schemas for audio inspection metadata and visualizations."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class EncodedProperties(BaseModel):
    """File-level container and compression properties."""

    format: str = Field(..., description="Container/format identifier (wav, mp3, flac)")
    file_size_bytes: int = Field(..., description="Physical file size in bytes")
    sha256_hash: str = Field(..., description="Registered SHA-256 evidence digest")
    codec: Optional[str] = Field(None, description="Audio codec identifier (e.g. PCM, MPEG, FLAC)")
    bitrate_kbps: Optional[float] = Field(None, description="Nominal/average bitrate in kilobits/second")


class DecodedProperties(BaseModel):
    """Acoustic properties of the decoded audio signal."""

    duration_seconds: float = Field(..., description="Duration in seconds")
    sample_rate_hz: int = Field(..., description="Sampling rate in Hz")
    channels: int = Field(..., description="Number of audio channels (1=mono, 2=stereo)")
    total_samples: int = Field(..., description="Total decoded sample frames")
    sample_format: Optional[str] = Field(None, description="Decoded sample format (e.g. PCM_16, FLOAT)")
    bit_depth: Optional[int] = Field(None, description="Bits per sample, only when reliably established")


class AudioMetadataResponse(BaseModel):
    """Full forensic audio metadata response distinguishing container from decoded properties."""

    evidence_id: str = Field(..., description="Evidence identifier")
    case_id: str = Field(..., description="Case identifier")
    original_filename: str = Field(..., description="Sanitized client filename")
    integrity_verified: bool = Field(..., description="Whether SHA-256 integrity was confirmed prior to extraction")
    encoded_properties: EncodedProperties
    decoded_properties: DecodedProperties
    embedded_metadata: Dict[str, Optional[str]] = Field(
        default_factory=dict,
        description="Available ID3, RIFF, or Vorbis metadata tags (artist, title, year, etc.)",
    )


class ChannelWaveform(BaseModel):
    """Downsampled waveform envelope for an individual channel."""

    channel_index: int = Field(..., description="0-indexed channel index")
    min_amplitudes: List[float] = Field(..., description="Lower envelope bounds per window")
    max_amplitudes: List[float] = Field(..., description="Upper envelope bounds per window")


class WaveformResponse(BaseModel):
    """Waveform visualization payload with deterministic time axis and envelope data."""

    evidence_id: str = Field(..., description="Evidence identifier")
    source_sha256: str = Field(..., description="SHA-256 digest of inspected evidence")
    sample_rate_hz: int = Field(..., description="Audio sampling rate in Hz")
    duration_seconds: float = Field(..., description="Total audio duration in seconds")
    total_samples: int = Field(..., description="Total decoded audio samples")
    point_budget: int = Field(..., description="Configured or applied visualization points")
    downsampled: bool = Field(..., description="Whether deterministic aggregation was applied")
    aggregation_method: str = Field(
        default="min_max_windowed",
        description="Aggregation method applied for visualization (e.g. min_max_windowed)",
    )
    time_axis: List[float] = Field(..., description="Timestamp in seconds for each window center")
    channels: List[ChannelWaveform] = Field(..., description="Per-channel waveform envelopes")
    peak_amplitude: float = Field(..., description="Maximum absolute amplitude detected [0.0 .. 1.0]")
    rms_energy: float = Field(..., description="Overall root-mean-square energy level")


class SpectrogramResponse(BaseModel):
    """STFT time-frequency magnitude spectrogram payload."""

    evidence_id: str = Field(..., description="Evidence identifier")
    source_sha256: str = Field(..., description="SHA-256 digest of inspected evidence")
    duration_seconds: float = Field(..., description="Total duration in seconds")
    sample_rate_hz: int = Field(..., description="Sampling rate in Hz")
    n_fft: int = Field(..., description="STFT FFT window size in samples")
    hop_length: int = Field(..., description="STFT hop/stride size in samples")
    window_type: str = Field(default="hann", description="Windowing function applied")
    unit: str = Field(default="dB", description="Magnitude measurement unit (decibels relative to full scale)")
    min_db: float = Field(..., description="Lower clamp threshold in dB")
    max_db: float = Field(..., description="Upper peak threshold in dB")
    time_axis: List[float] = Field(..., description="Time axis bins in seconds")
    freq_axis: List[float] = Field(..., description="Frequency axis bins in Hz")
    magnitudes_db: List[List[float]] = Field(
        ...,
        description="2D magnitude matrix [frequency_bins][time_frames] in dB",
    )


class SpectrumResponse(BaseModel):
    """Frequency spectrum (FFT magnitude / power) across the signal."""

    evidence_id: str = Field(..., description="Evidence identifier")
    source_sha256: str = Field(..., description="SHA-256 digest of inspected evidence")
    sample_rate_hz: int = Field(..., description="Sampling rate in Hz")
    nyquist_hz: float = Field(..., description="Nyquist frequency (sample_rate / 2)")
    window_type: str = Field(default="hann", description="Window function applied to mitigate spectral leakage")
    num_bins: int = Field(..., description="Number of frequency bins returned")
    frequencies_hz: List[float] = Field(..., description="Frequency points in Hz")
    magnitudes_db: List[float] = Field(..., description="Spectral magnitude in dB")
    dominant_frequency_hz: Optional[float] = Field(None, description="Detected dominant spectral frequency peak in Hz")
    dominant_magnitude_db: Optional[float] = Field(None, description="Magnitude of dominant peak in dB")
