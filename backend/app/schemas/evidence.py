"""Schemas for evidence upload and integrity verification."""

from typing import List, Optional
from pydantic import BaseModel, Field


class EvidenceResponse(BaseModel):
    """Registered digital audio evidence item."""

    id: str = Field(..., description="Server-generated unique evidence ID")
    case_id: str = Field(..., description="Associated case ID")
    original_filename: str = Field(..., description="Sanitized client filename")
    file_size_bytes: int = Field(..., description="Raw evidence file size in bytes")
    sha256_hash: str = Field(..., description="Cryptographic SHA-256 digest")
    format: str = Field(..., description="Detected audio format: wav, mp3, flac")
    mime_type: str = Field(..., description="MIME media type")
    ingested_at: str = Field(..., description="UTC ISO-8601 ingestion timestamp")
    integrity_status: str = Field(..., description="Initial verification status: verified")


class EvidenceListResponse(BaseModel):
    """List of evidence items for a case."""

    case_id: str
    items: List[EvidenceResponse]
    total: int


class GlobalEvidenceListResponse(BaseModel):
    """List of all registered evidence items across cases."""

    items: List[EvidenceResponse]
    total: int


class IntegrityVerificationResponse(BaseModel):
    """Result of recalculating and verifying stored evidence hash."""

    evidence_id: str = Field(..., description="Evidence identifier")
    case_id: str = Field(..., description="Case identifier")
    expected_sha256: str = Field(..., description="Original SHA-256 computed at intake")
    calculated_sha256: str = Field(..., description="Current SHA-256 calculated from stored disk file")
    status: str = Field(..., description="Verification result: 'match', 'mismatch', or 'unverifiable'")
    verified_at: str = Field(..., description="UTC timestamp of the verification run")
    explanation: str = Field(..., description="Detailed diagnostic description of the result")
    disclaimer: str = Field(
        default="Hash match establishes byte-for-byte storage integrity; it does not determine pre-acquisition authenticity or verify recording origin.",
        description="Forensic evidentiary disclaimer",
    )
