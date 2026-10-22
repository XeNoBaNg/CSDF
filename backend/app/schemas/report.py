"""Pydantic schemas for forensic PDF report generation."""

from typing import Optional
from pydantic import BaseModel, Field


class ReportGenerateRequest(BaseModel):
    """Configuration options for forensic PDF report generation."""

    include_visualizations: bool = Field(
        default=True,
        description="Whether to render and embed peak-preserving waveform and STFT spectrogram charts.",
    )
    include_audit: bool = Field(
        default=True,
        description="Whether to query and include the chronological chain-of-custody audit log.",
    )
    run_analysis_if_missing: bool = Field(
        default=True,
        description="Whether to execute explainable signal anomaly detectors to populate the findings table.",
    )
    examiner_notes: Optional[str] = Field(
        default=None,
        description="Optional supplementary notes or investigative hypothesis from the forensic examiner.",
    )


class ReportMetadataResponse(BaseModel):
    """Metadata response describing a generated forensic report."""

    report_id: str = Field(..., description="Unique forensic report identifier")
    evidence_id: str = Field(..., description="Subject evidence identifier")
    case_id: str = Field(..., description="Owning investigation case identifier")
    generated_at: str = Field(..., description="UTC timestamp of report compilation")
    file_size_bytes: int = Field(..., description="Size of compiled PDF document in bytes")
    download_url: str = Field(..., description="URL to download the compiled PDF")
