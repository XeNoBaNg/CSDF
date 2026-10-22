"""Evidence file storage, streaming upload handling, and SHA-256 verification."""

from datetime import datetime, timezone
import hashlib
import hmac
import logging
import os
from pathlib import Path
import shutil
import tempfile
from typing import Dict, Optional, Tuple
from fastapi import UploadFile
from backend.app.core.config import settings
from backend.app.core.errors import (
    CorruptEvidenceError,
    MissingEvidenceFileError,
    OversizedFileError,
)
from backend.app.evidence.validator import (
    sanitize_filename,
    validate_audio_content,
    validate_extension,
)

logger = logging.getLogger("audiosleuth.evidence.storage")

import uuid

CHUNK_SIZE = 64 * 1024  # 64 KB streaming buffer


def generate_evidence_id(sha256_hash: str) -> str:
    """Generates a standardized server-controlled evidence ID."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    rand_token = uuid.uuid4().hex[:4]
    hash_prefix = sha256_hash[:8]
    return f"EVD-{ts}-{rand_token}-{hash_prefix}"


def generate_storage_filename(evidence_id: str, format_name: str) -> str:
    """Generates an internal storage filename (never using original client name)."""
    return f"{evidence_id}.{format_name}.bin"


def get_evidence_file_path(stored_filename: str) -> Path:
    """Safely resolves physical storage path and validates against path traversal."""
    evidence_dir = settings.resolved_evidence_dir
    # Normalize and ensure stored_filename contains no directory components
    safe_name = Path(stored_filename).name
    target_path = (evidence_dir / safe_name).resolve()

    # Enforce path containment inside evidence directory
    try:
        target_path.relative_to(evidence_dir.resolve())
    except ValueError:
        raise CorruptEvidenceError("Unsafe evidence path traversal detected.")

    return target_path


async def save_uploaded_evidence(
    upload_file: UploadFile,
    case_id: str,
) -> Dict[str, object]:
    """Streams uploaded evidence to temporary storage while calculating SHA-256 digest,
    validates binary content and size, then atomically moves it to isolated evidence storage.
    """
    raw_filename = upload_file.filename or "evidence.bin"
    sanitized_name = sanitize_filename(raw_filename)

    # 1. Pre-validate extension before streaming
    validate_extension(sanitized_name)

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    hasher = hashlib.sha256()
    total_bytes = 0
    header_bytes = bytearray()

    # 2. Prepare temporary file
    temp_dir = settings.resolved_evidence_dir / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_fd, temp_path_str = tempfile.mkstemp(dir=str(temp_dir), prefix="sleuth_upload_")
    temp_path = Path(temp_path_str)

    try:
        with os.fdopen(temp_fd, "wb") as temp_file:
            while True:
                chunk = await upload_file.read(CHUNK_SIZE)
                if not chunk:
                    break

                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    logger.warning(
                        "Upload rejected: size exceeded %d bytes for '%s'",
                        max_bytes,
                        sanitized_name,
                    )
                    raise OversizedFileError(max_mb=settings.MAX_UPLOAD_SIZE_MB)

                hasher.update(chunk)
                temp_file.write(chunk)

                # Capture header up to 128 bytes for signature inspection
                if len(header_bytes) < 128:
                    needed = 128 - len(header_bytes)
                    header_bytes.extend(chunk[:needed])

        # 3. Check for empty upload
        if total_bytes == 0:
            raise CorruptEvidenceError("Evidence file is empty (0 bytes).")

        # 4. Validate binary magic signature against extension
        detected_format, mime_type = validate_audio_content(bytes(header_bytes), sanitized_name)

        sha256_digest = hasher.hexdigest().lower()
        evidence_id = generate_evidence_id(sha256_digest)
        stored_filename = generate_storage_filename(evidence_id, detected_format)
        final_path = get_evidence_file_path(stored_filename)

        # 5. Atomically move validated file to evidence vault
        shutil.move(str(temp_path), str(final_path))
        logger.info(
            "Evidence '%s' successfully ingested: %d bytes, SHA-256=%s, format=%s",
            evidence_id,
            total_bytes,
            sha256_digest,
            detected_format,
        )

        return {
            "evidence_id": evidence_id,
            "case_id": case_id,
            "original_filename": sanitized_name,
            "stored_filename": stored_filename,
            "file_size_bytes": total_bytes,
            "sha256_hash": sha256_digest,
            "format": detected_format,
            "mime_type": mime_type,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "integrity_status": "verified",
        }

    except Exception:
        # Guarantee temp file cleanup on any failure
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError as cleanup_err:
                logger.error("Failed to clean up temp file '%s': %s", temp_path, cleanup_err)
        raise


def recalculate_stored_hash(stored_filename: str) -> str:
    """Streams stored original file to compute its current SHA-256 digest."""
    path = get_evidence_file_path(stored_filename)
    if not path.exists() or not path.is_file():
        raise MissingEvidenceFileError(
            evidence_id=stored_filename,
            message="Evidence file does not exist on disk or cannot be read.",
        )

    hasher = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                hasher.update(chunk)
    except OSError as err:
        raise MissingEvidenceFileError(
            evidence_id=stored_filename,
            message=f"Evidence file read error: {err}",
        )

    return hasher.hexdigest().lower()


def verify_evidence_integrity(
    expected_hash: str,
    stored_filename: str,
) -> Tuple[str, str, str]:
    """Verifies evidence integrity using constant-time comparison.

    Returns:
        (status, calculated_hash, explanation)
        status is one of: 'match', 'mismatch', 'unverifiable'
    """
    try:
        calculated_hash = recalculate_stored_hash(stored_filename)
    except MissingEvidenceFileError:
        return (
            "unverifiable",
            "",
            "The physical evidence file could not be located in storage. Integrity is unverifiable.",
        )

    # Constant-time comparison to prevent timing attacks
    is_match = hmac.compare_digest(expected_hash.lower(), calculated_hash.lower())

    if is_match:
        status_str = "match"
        explanation = (
            "Cryptographic SHA-256 digest matches registered intake state exactly. "
            "Evidence has remained byte-for-byte unchanged in local storage. "
            "(Note: File integrity confirms storage consistency; it does not prove original recording authenticity)."
        )
    else:
        status_str = "mismatch"
        explanation = (
            "CRITICAL INTEGRITY FAILURE: Recalculated SHA-256 digest does not match registered intake hash. "
            "The stored evidence bytes have been altered, truncated, or tampered with on disk."
        )

    return status_str, calculated_hash, explanation
