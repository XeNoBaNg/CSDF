"""Non-destructive audio decoder and evidence integrity pre-check."""

import hmac
import logging
from pathlib import Path
from typing import Any, Dict, Tuple
import numpy as np
import soundfile as sf
from backend.app.core.config import settings
from backend.app.core.errors import (
    CorruptEvidenceError,
    EvidenceIntegrityError,
    MissingEvidenceFileError,
    ResourceLimitExceededError,
)
from backend.app.evidence.storage import get_evidence_file_path, recalculate_stored_hash
from backend.app.models.evidence import EvidenceModel

logger = logging.getLogger("audiosleuth.analysis.decoder")


def verify_and_load_audio(
    item: EvidenceModel,
) -> Tuple[np.ndarray, int, Dict[str, Any]]:
    """Verifies evidence integrity against its registered intake hash, checks resource
    limits, and safely decodes audio into a temporary working NumPy representation.

    The original evidence file on disk is never altered, transcoded, or modified.
    """
    path = get_evidence_file_path(item.stored_filename)
    if not path.exists() or not path.is_file():
        raise MissingEvidenceFileError(
            evidence_id=item.id,
            message="Evidence recording could not be located in physical vault storage.",
        )

    # 1. Mandatory Cryptographic Integrity Verification before inspection
    calculated_hash = recalculate_stored_hash(item.stored_filename)
    if not hmac.compare_digest(calculated_hash.lower(), item.sha256_hash.lower()):
        logger.error(
            "Evidence inspection rejected for '%s': integrity mismatch (expected %s, got %s)",
            item.id,
            item.sha256_hash,
            calculated_hash,
        )
        raise EvidenceIntegrityError(
            message=(
                "CRITICAL INTEGRITY FAILURE: Stored evidence bytes have been altered or corrupted on disk. "
                "Audio inspection refused to preserve forensic chain-of-custody."
            ),
            details={
                "evidence_id": item.id,
                "expected_sha256": item.sha256_hash,
                "calculated_sha256": calculated_hash,
            },
        )

    # 2. Extract container and stream header info using soundfile
    try:
        info = sf.info(str(path))
    except Exception as exc:
        raise CorruptEvidenceError(
            reason=f"Failed to decode audio headers: {exc}",
            details={"evidence_id": item.id, "error": str(exc)},
        )

    # 3. Resource Limit Enforcement
    if info.duration > settings.MAX_DECODED_DURATION_SECONDS:
        raise ResourceLimitExceededError(
            message=(
                f"Audio duration ({info.duration:.1f}s) exceeds maximum permitted inspection "
                f"limit of {settings.MAX_DECODED_DURATION_SECONDS}s."
            ),
            details={
                "duration_seconds": info.duration,
                "max_duration_seconds": settings.MAX_DECODED_DURATION_SECONDS,
            },
        )

    # 4. Non-destructive decoding into memory
    try:
        samples, sample_rate = sf.read(str(path), dtype="float32", always_2d=False)
    except Exception as exc:
        raise CorruptEvidenceError(
            reason=f"Failed to decode audio samples: {exc}",
            details={"evidence_id": item.id, "error": str(exc)},
        )

    # 5. Sanitize numeric values (replace non-finite values if corrupted)
    if not np.all(np.isfinite(samples)):
        samples = np.nan_to_num(samples, nan=0.0, posinf=1.0, neginf=-1.0)

    # Determine bit depth from subtype where available
    bit_depth = None
    if info.subtype:
        sub = info.subtype.upper()
        if "PCM_16" in sub or "16" in sub:
            bit_depth = 16
        elif "PCM_24" in sub or "24" in sub:
            bit_depth = 24
        elif "PCM_32" in sub or "32" in sub:
            bit_depth = 32
        elif "PCM_U8" in sub or "PCM_S8" in sub:
            bit_depth = 8

    metadata_info = {
        "format": info.format,
        "subtype": info.subtype,
        "channels": info.channels,
        "sample_rate": info.samplerate,
        "duration": info.duration,
        "frames": info.frames,
        "bit_depth": bit_depth,
    }

    return samples, sample_rate, metadata_info
