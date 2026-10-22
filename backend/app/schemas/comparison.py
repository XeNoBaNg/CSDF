"""Pydantic schemas for cross-recording forensic comparison."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ComparisonRequest(BaseModel):
    """Request payload for executing a cross-recording forensic comparison."""

    evidence_id_a: str = Field(..., description="Primary evidence identifier")
    evidence_id_b: str = Field(..., description="Secondary evidence identifier to compare against")
    include_anomaly_comparison: bool = Field(
        True,
        description="Whether to run Phase 4 anomaly detectors and compare findings timelines",
    )
    envelope_points: int = Field(
        500,
        ge=50,
        le=2000,
        description="Number of envelope points for macro-amplitude correlation",
    )
    spectral_bins: int = Field(
        128,
        ge=32,
        le=512,
        description="Number of frequency bins for spectral cosine similarity evaluation",
    )
    notes: Optional[str] = Field(
        None,
        description="Optional examiner investigation notes regarding the comparison rationale",
    )


class MetadataComparison(BaseModel):
    """Side-by-side metadata and container properties comparison."""

    filename_a: str
    filename_b: str
    format_a: str
    format_b: str
    format_match: bool
    file_size_bytes_a: int
    file_size_bytes_b: int
    file_size_diff_bytes: int
    sha256_a: str
    sha256_b: str
    sha256_match: bool
    duration_seconds_a: float
    duration_seconds_b: float
    duration_diff_seconds: float
    duration_match: bool
    sample_rate_hz_a: int
    sample_rate_hz_b: int
    sample_rate_match: bool
    channels_a: int
    channels_b: int
    channels_match: bool
    bit_depth_a: Optional[int] = None
    bit_depth_b: Optional[int] = None
    bit_depth_match: bool


class SignalComparison(BaseModel):
    """Signal energy, dynamic range, and amplitude envelope statistics."""

    peak_amplitude_a: float
    peak_amplitude_b: float
    peak_amplitude_diff: float
    rms_energy_a: float
    rms_energy_b: float
    rms_energy_diff: float
    rms_ratio_db: float
    crest_factor_a: float
    crest_factor_b: float
    zero_crossing_rate_a: float
    zero_crossing_rate_b: float
    zero_crossing_rate_diff: float
    envelope_correlation: float
    channel_mixdown_policy: str


class SpectralComparison(BaseModel):
    """STFT spectral distribution and similarity metrics."""

    centroid_hz_a: float
    centroid_hz_b: float
    centroid_diff_hz: float
    rolloff_hz_a: float
    rolloff_hz_b: float
    rolloff_diff_hz: float
    flatness_a: float
    flatness_b: float
    flatness_diff: float
    spectral_cosine_similarity: float
    spectral_euclidean_distance: float
    evaluated_frequency_ceiling_hz: float


class AnomalyComparison(BaseModel):
    """Comparison of Phase 4 signal anomaly findings counts and temporal distribution."""

    total_findings_a: int
    total_findings_b: int
    silence_findings_a: int
    silence_findings_b: int
    transition_findings_a: int
    transition_findings_b: int
    spectral_findings_a: int
    spectral_findings_b: int
    findings_density_per_min_a: float
    findings_density_per_min_b: float
    binned_distribution_a: List[int]
    binned_distribution_b: List[int]
    timeline_bins: int


class ComparisonSummary(BaseModel):
    """High-level forensic findings summary, similarity index, warnings, and explanation."""

    byte_match: bool
    duration_match: bool
    acoustic_similarity_label: str
    transparent_similarity_score: float
    scoring_formula_explanation: str
    warnings: List[str]
    explanation: str


class ComparisonResponse(BaseModel):
    """Comprehensive forensic comparison result payload."""

    id: str
    timestamp: str
    evidence_id_a: str
    evidence_id_b: str
    case_id_a: Optional[str] = None
    case_id_b: Optional[str] = None
    metadata_comparison: MetadataComparison
    signal_comparison: SignalComparison
    spectral_comparison: SpectralComparison
    anomaly_comparison: Optional[AnomalyComparison] = None
    summary: ComparisonSummary
    disclaimer: str
