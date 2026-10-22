"""Schemas for Phase 4 forensic signal analysis, anomaly detectors, and findings."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FindingCategory(str, Enum):
    SILENCE = "silence"
    TRANSITION = "transition"
    SPECTRAL = "spectral"


class ReviewPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    INFORMATIONAL = "informational"


class ForensicFinding(BaseModel):
    """Common forensic finding model representing an explainable signal anomaly."""

    id: str = Field(..., description="Unique finding identifier (e.g., FIND-20261022180000-xxxx)")
    evidence_id: str = Field(..., description="Evidence ID inspected")
    source_sha256: str = Field(..., description="Cryptographic SHA-256 digest of original evidence")
    detector_name: str = Field(..., description="Name of the detector module that produced this finding")
    algorithm_version: str = Field("1.0.0", description="Detector algorithm version")
    category: FindingCategory = Field(..., description="Anomaly classification category")
    priority: ReviewPriority = Field(..., description="Suggested manual review priority")
    start_time: float = Field(..., ge=0.0, description="Start timestamp of flagged interval in seconds")
    end_time: float = Field(..., ge=0.0, description="End timestamp of flagged interval in seconds")
    duration_seconds: float = Field(..., ge=0.0, description="Duration of flagged interval in seconds")
    event_time: Optional[float] = Field(None, ge=0.0, description="Exact peak/event timestamp if localized point")
    metric_name: str = Field(..., description="Mathematical metric measured (e.g. rms_energy, delta_amplitude)")
    measured_value: float = Field(..., description="Calculated metric value")
    applied_threshold: float = Field(..., description="Configured decision threshold")
    units: str = Field(..., description="Units of measurement (e.g. linear_rms, delta_amplitude, normalized_flux)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters active during detection")
    explanation: str = Field(..., description="Clear human-readable forensic explanation of why this was flagged")
    suggested_action: str = Field(..., description="Actionable manual review guidance for the examiner")
    disclaimer: str = Field(
        default=(
            "Finding represents an explainable acoustic signal indicator for manual forensic review, "
            "not definitive proof of tampering, synthesis, or editing."
        ),
        description="Forensic evidentiary limitation notice",
    )


class SilenceDetectionParams(BaseModel):
    """Parameters for silence and low-energy interval detection."""

    window_duration_seconds: float = Field(0.05, ge=0.01, le=1.0, description="Analysis window length in seconds (10ms-1s)")
    hop_duration_seconds: float = Field(0.025, ge=0.005, le=0.5, description="Window hop step in seconds (5ms-500ms)")
    rms_threshold: float = Field(0.01, ge=0.00001, le=0.5, description="RMS energy threshold (linear scale, 0.01 ~= -40 dB)")
    min_silence_duration_seconds: float = Field(0.25, ge=0.05, le=10.0, description="Minimum duration to report as an interval")


class TransitionDetectionParams(BaseModel):
    """Parameters for abrupt amplitude transition detection."""

    threshold: float = Field(0.35, ge=0.05, le=1.5, description="Adjacent-sample amplitude difference threshold")
    min_separation_seconds: float = Field(0.05, ge=0.01, le=2.0, description="Minimum temporal separation between reported events")
    context_window_seconds: float = Field(0.05, ge=0.01, le=0.5, description="Review window radius around detected event")


class SpectralDetectionParams(BaseModel):
    """Parameters for spectral inconsistency / spectral flux detection."""

    n_fft: int = Field(1024, ge=128, le=4096, description="STFT window size in samples")
    hop_length: int = Field(256, ge=32, le=2048, description="STFT hop size in samples")
    threshold: float = Field(0.40, ge=0.05, le=1.5, description="Normalized spectral flux peak threshold")
    min_separation_seconds: float = Field(0.1, ge=0.02, le=2.0, description="Minimum temporal separation between flux peaks")
    context_window_seconds: float = Field(0.1, ge=0.02, le=0.5, description="Review window radius around detected peak")


class AnalysisRequest(BaseModel):
    """Request payload to initiate explainable signal analysis."""

    enable_silence: bool = Field(True, description="Enable silence and low-energy interval detector")
    enable_transitions: bool = Field(True, description="Enable abrupt amplitude transition detector")
    enable_spectral_flux: bool = Field(True, description="Enable spectral flux inconsistency detector")
    silence_params: Optional[SilenceDetectionParams] = None
    transition_params: Optional[TransitionDetectionParams] = None
    spectral_params: Optional[SpectralDetectionParams] = None


class AnalysisSummary(BaseModel):
    """Aggregate summary counts of findings produced by analysis."""

    total_findings: int = Field(..., ge=0, description="Total number of findings flagged across all detectors")
    by_category: Dict[str, int] = Field(default_factory=dict, description="Finding counts grouped by category")
    by_priority: Dict[str, int] = Field(default_factory=dict, description="Finding counts grouped by review priority")
    execution_time_ms: float = Field(..., ge=0.0, description="Total execution time in milliseconds")


class AnalysisResponse(BaseModel):
    """Comprehensive response containing all timestamped forensic findings."""

    analysis_id: str = Field(..., description="Unique analysis execution identifier")
    evidence_id: str = Field(..., description="Evidence ID analyzed")
    source_sha256: str = Field(..., description="SHA-256 hash verified prior to execution")
    created_at: str = Field(..., description="UTC timestamp when analysis completed")
    execution_status: str = Field("completed", description="Status of the analysis run ('completed')")
    summary: AnalysisSummary = Field(..., description="Aggregated telemetry and counts")
    findings: List[ForensicFinding] = Field(default_factory=list, description="Ordered list of timestamped findings")
    parameters_applied: Dict[str, Any] = Field(default_factory=dict, description="Actual parameters utilized by detectors")
