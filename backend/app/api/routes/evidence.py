"""Evidence inspection, audio visualization, and cryptographic integrity verification routes."""

from typing import Optional
from fastapi import APIRouter, Path, Query, status
from fastapi.responses import FileResponse
from backend.app.core.errors import EvidenceNotFoundError, MissingEvidenceFileError
from backend.app.evidence.storage import get_evidence_file_path
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.schemas.audio import (
    AudioMetadataResponse,
    SpectrogramResponse,
    SpectrumResponse,
    WaveformResponse,
)
from backend.app.schemas.analysis import AnalysisRequest, AnalysisResponse
from backend.app.schemas.evidence import (
    EvidenceResponse,
    GlobalEvidenceListResponse,
    IntegrityVerificationResponse,
)
from backend.app.services.analysis_service import SignalAnalysisService
from backend.app.services.evidence_service import EvidenceService
from backend.app.services.inspection_service import AudioInspectionService

router = APIRouter(tags=["Evidence & Audio Inspection"])

evidence_service = EvidenceService()
inspection_service = AudioInspectionService()
analysis_service = SignalAnalysisService()
evidence_repo = EvidenceRepository()


@router.get(
    "/evidence",
    response_model=GlobalEvidenceListResponse,
    status_code=status.HTTP_200_OK,
    summary="List All Registered Evidence Items",
    description="Lists registered audio evidence items across cases with optional case_id filtering.",
)
async def list_all_evidence(
    case_id: Optional[str] = Query(None, description="Optional case ID to filter by"),
) -> GlobalEvidenceListResponse:
    items = evidence_repo.list_all(case_id=case_id)
    return GlobalEvidenceListResponse(
        items=[
            EvidenceResponse(
                id=item.id,
                case_id=item.case_id,
                original_filename=item.original_filename,
                file_size_bytes=item.file_size_bytes,
                sha256_hash=item.sha256_hash,
                format=item.format,
                mime_type=item.mime_type,
                ingested_at=item.ingested_at,
                integrity_status=item.integrity_status,
            )
            for item in items
        ],
        total=len(items),
    )


@router.get(
    "/evidence/{evidence_id}",
    response_model=EvidenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Evidence Item Details",
    description="Retrieves metadata, file format, and registered SHA-256 digest for an evidence item.",
)
async def get_evidence_details(
    evidence_id: str = Path(..., description="Unique evidence identifier"),
) -> EvidenceResponse:
    return evidence_service.get_evidence(evidence_id)


@router.post(
    "/evidence/{evidence_id}/verify-integrity",
    response_model=IntegrityVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Stored Evidence Integrity",
    description=(
        "Streams the physical evidence file from storage, recalculates its cryptographic SHA-256 digest, "
        "and performs a constant-time comparison against the intake hash to confirm byte-for-byte integrity."
    ),
)
async def verify_evidence_integrity(
    evidence_id: str = Path(..., description="Unique evidence identifier"),
) -> IntegrityVerificationResponse:
    return evidence_service.verify_integrity(evidence_id)


# =========================================================================
# Phase 3: Forensic Audio Inspection Endpoints
# =========================================================================


@router.get(
    "/evidence/{evidence_id}/metadata",
    response_model=AudioMetadataResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract Comprehensive Audio Metadata",
    description=(
        "Extracts container properties, decoded acoustic characteristics, and embedded ID3/RIFF metadata tags. "
        "Integrity is verified against the registered SHA-256 hash prior to extraction."
    ),
)
async def get_evidence_metadata(
    evidence_id: str = Path(..., description="Unique evidence identifier"),
) -> AudioMetadataResponse:
    return inspection_service.get_metadata(evidence_id)


@router.get(
    "/evidence/{evidence_id}/waveform",
    response_model=WaveformResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Waveform Visualization Data",
    description=(
        "Decodes audio into memory and generates deterministic min/max envelope points for interactive visualization. "
        "Supports mono and multichannel audio with accurate time axes."
    ),
)
async def get_evidence_waveform(
    evidence_id: str = Path(..., description="Unique evidence identifier"),
    point_budget: int = Query(
        1000,
        ge=10,
        le=10000,
        description="Target number of envelope visualization points",
    ),
) -> WaveformResponse:
    return inspection_service.get_waveform(evidence_id, point_budget=point_budget)


@router.get(
    "/evidence/{evidence_id}/spectrogram",
    response_model=SpectrogramResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate STFT Spectrogram Heatmap",
    description=(
        "Computes a short-time Fourier transform (STFT) magnitude spectrogram in decibels (dB). "
        "Provides calibrated time and frequency axes suitable for heatmap visualization."
    ),
)
async def get_evidence_spectrogram(
    evidence_id: str = Path(..., description="Unique evidence identifier"),
    n_fft: int = Query(
        1024,
        ge=128,
        le=4096,
        description="STFT FFT window size in samples",
    ),
    hop_length: int = Query(
        512,
        ge=32,
        le=2048,
        description="STFT hop size in samples",
    ),
    max_time_frames: int = Query(
        250,
        ge=10,
        le=1000,
        description="Maximum time resolution frames",
    ),
    max_freq_bins: int = Query(
        128,
        ge=16,
        le=512,
        description="Maximum frequency resolution bins",
    ),
) -> SpectrogramResponse:
    return inspection_service.get_spectrogram(
        evidence_id,
        n_fft=n_fft,
        hop_length=hop_length,
        max_time_frames=max_time_frames,
        max_freq_bins=max_freq_bins,
    )


@router.get(
    "/evidence/{evidence_id}/spectrum",
    response_model=SpectrumResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate FFT Frequency Spectrum",
    description=(
        "Computes an FFT-based amplitude/power spectrum in dB across the audio signal, "
        "including dominant frequency peak detection and calibrated frequency axis in Hz."
    ),
)
async def get_evidence_spectrum(
    evidence_id: str = Path(..., description="Unique evidence identifier"),
    max_bins: int = Query(
        512,
        ge=32,
        le=2048,
        description="Maximum frequency bins to return",
    ),
    max_frequency: Optional[float] = Query(
        None,
        ge=10.0,
        description="Optional upper frequency cutoff in Hz (defaults to Nyquist)",
    ),
) -> SpectrumResponse:
    return inspection_service.get_spectrum(
        evidence_id,
        max_bins=max_bins,
        max_frequency=max_frequency,
    )


@router.get(
    "/evidence/{evidence_id}/audio",
    summary="Safe Audio Playback Stream",
    description=(
        "Streams the stored audio file for browser playback with HTTP Range request support. "
        "Resolves exclusively through registered evidence ID."
    ),
)
async def stream_evidence_audio(
    evidence_id: str = Path(..., description="Unique evidence identifier"),
):
    item = evidence_repo.get_by_id(evidence_id)
    if not item:
        raise EvidenceNotFoundError(evidence_id=evidence_id)

    path = get_evidence_file_path(item.stored_filename)
    if not path.exists() or not path.is_file():
        raise MissingEvidenceFileError(evidence_id=evidence_id)

    return FileResponse(
        path=str(path),
        media_type=item.mime_type,
        filename=item.original_filename,
    )


# =========================================================================
# Phase 4: Forensic Signal Anomaly Analysis Endpoints
# =========================================================================


@router.post(
    "/evidence/{evidence_id}/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Explainable Forensic Signal Analysis",
    description=(
        "Executes selected explainable forensic anomaly detectors (silence intervals, abrupt transitions, "
        "and spectral flux inconsistencies) on non-destructively decoded audio. "
        "Evidence integrity is verified against registered SHA-256 prior to analysis."
    ),
)
async def analyze_evidence_signal(
    evidence_id: str = Path(..., description="Unique evidence identifier"),
    request: Optional[AnalysisRequest] = None,
) -> AnalysisResponse:
    return analysis_service.analyze_evidence(evidence_id, request=request)

