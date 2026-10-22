"""Forensic audio inspection and visualization service."""

import logging
from typing import Optional
from backend.app.analysis.decoder import verify_and_load_audio
from backend.app.analysis.metadata import extract_audio_metadata
from backend.app.analysis.spectrogram import generate_spectrogram_data
from backend.app.analysis.spectrum import generate_spectrum_data
from backend.app.analysis.waveform import generate_waveform_data
from backend.app.core.errors import EvidenceNotFoundError
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.schemas.audio import (
    AudioMetadataResponse,
    SpectrogramResponse,
    SpectrumResponse,
    WaveformResponse,
)
from backend.app.services.audit_service import AuditService

logger = logging.getLogger("audiosleuth.services.inspection")


class AudioInspectionService:
    """Orchestrates non-destructive decoding, metadata extraction, and signal visualization."""

    def __init__(
        self,
        evidence_repo: Optional[EvidenceRepository] = None,
        audit_service: Optional[AuditService] = None,
    ):
        self.evidence_repo = evidence_repo or EvidenceRepository()
        self.audit_service = audit_service or AuditService()

    def get_metadata(self, evidence_id: str) -> AudioMetadataResponse:
        """Verifies evidence integrity and extracts audio and embedded metadata."""
        item = self.evidence_repo.get_by_id(evidence_id)
        if not item:
            raise EvidenceNotFoundError(evidence_id=evidence_id)

        meta = extract_audio_metadata(item)

        # Record durable audit trail entry
        self.audit_service.record_event(
            action="metadata_inspected",
            outcome="success",
            case_id=item.case_id,
            evidence_id=item.id,
            details={
                "format": meta.encoded_properties.format,
                "channels": meta.decoded_properties.channels,
                "sample_rate": meta.decoded_properties.sample_rate_hz,
                "duration_seconds": meta.decoded_properties.duration_seconds,
            },
        )

        return meta


    def get_waveform(
        self,
        evidence_id: str,
        point_budget: int = 1000,
    ) -> WaveformResponse:
        """Verifies evidence integrity and generates a deterministic downsampled waveform envelope."""
        item = self.evidence_repo.get_by_id(evidence_id)
        if not item:
            raise EvidenceNotFoundError(evidence_id=evidence_id)

        samples, sample_rate, _ = verify_and_load_audio(item)
        return generate_waveform_data(
            samples=samples,
            sample_rate=sample_rate,
            evidence_id=item.id,
            source_sha256=item.sha256_hash,
            point_budget=point_budget,
        )

    def get_spectrogram(
        self,
        evidence_id: str,
        n_fft: int = 1024,
        hop_length: int = 512,
        max_time_frames: int = 250,
        max_freq_bins: int = 128,
    ) -> SpectrogramResponse:
        """Verifies evidence integrity and generates an STFT magnitude spectrogram in decibels."""
        item = self.evidence_repo.get_by_id(evidence_id)
        if not item:
            raise EvidenceNotFoundError(evidence_id=evidence_id)

        samples, sample_rate, _ = verify_and_load_audio(item)
        return generate_spectrogram_data(
            samples=samples,
            sample_rate=sample_rate,
            evidence_id=item.id,
            source_sha256=item.sha256_hash,
            n_fft=n_fft,
            hop_length=hop_length,
            max_time_frames=max_time_frames,
            max_freq_bins=max_freq_bins,
        )

    def get_spectrum(
        self,
        evidence_id: str,
        max_bins: int = 512,
        max_frequency: Optional[float] = None,
    ) -> SpectrumResponse:
        """Verifies evidence integrity and generates an FFT power spectrum with peak frequency detection."""
        item = self.evidence_repo.get_by_id(evidence_id)
        if not item:
            raise EvidenceNotFoundError(evidence_id=evidence_id)

        samples, sample_rate, _ = verify_and_load_audio(item)
        return generate_spectrum_data(
            samples=samples,
            sample_rate=sample_rate,
            evidence_id=item.id,
            source_sha256=item.sha256_hash,
            max_bins=max_bins,
            max_frequency=max_frequency,
        )
