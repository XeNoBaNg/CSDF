"""Audio file validation and magic number verification."""

from pathlib import Path
import re
from typing import Optional, Tuple
from backend.app.core.errors import CorruptEvidenceError, UnsupportedFormatError

SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".flac"}
SUPPORTED_FORMATS = ["wav", "mp3", "flac"]

MIME_TYPE_MAP = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "flac": "audio/flac",
}


def sanitize_filename(raw_filename: Optional[str]) -> str:
    """Sanitizes user-provided filename to prevent path traversal or unsafe characters."""
    if not raw_filename or not raw_filename.strip():
        return "unnamed_evidence.bin"

    # 1. Strip directory traversal separators (both POSIX and Windows)
    basename = Path(raw_filename).name

    # 2. Strip null bytes and control characters
    cleaned = basename.replace("\x00", "").strip()

    # 3. Restrict characters to alphanumeric, dashes, underscores, and dots
    sanitized = re.sub(r"[^\w\.\-]", "_", cleaned)

    # 4. Collapse multiple dots or underscores
    sanitized = re.sub(r"\.{2,}", ".", sanitized)
    sanitized = re.sub(r"_{2,}", "_", sanitized)

    # 5. Prevent leading dot (hidden file) or empty result
    sanitized = sanitized.lstrip(".")
    if not sanitized:
        sanitized = "unnamed_evidence.bin"

    # 6. Limit max length to 128 chars while preserving extension
    if len(sanitized) > 128:
        ext = Path(sanitized).suffix
        sanitized = sanitized[: 128 - len(ext)] + ext

    return sanitized


def validate_extension(filename: str) -> str:
    """Validates that filename has a supported audio extension."""
    ext = Path(filename).suffix.lower()
    if not ext or ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFormatError(
            format_name=ext if ext else "unknown",
            supported=SUPPORTED_FORMATS,
            message=f"File extension '{ext or 'none'}' is not supported. AudioSleuth currently accepts: WAV, MP3, FLAC.",
        )
    return ext


def detect_audio_signature(header: bytes) -> Optional[str]:
    """Detects audio format based on binary magic signatures.

    Inspects:
    - WAV: RIFF container with WAVE format
    - FLAC: 'fLaC' stream marker
    - MP3: ID3v2 container or MPEG Layer III audio frame sync
    """
    if len(header) < 4:
        return None

    # 1. WAV Check: Starts with 'RIFF' and bytes 8..12 contain 'WAVE'
    if header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WAVE":
        return "wav"

    # 2. FLAC Check: Starts with 'fLaC'
    if header.startswith(b"fLaC"):
        return "flac"

    # 3. MP3 Check:
    # Option A: ID3v2 tag (bytes 0..3: 'ID3', followed by version bytes < 255)
    if header.startswith(b"ID3") and len(header) >= 5:
        if header[3] < 0xFF and header[4] < 0xFF:
            return "mp3"

    # Option B: Raw MPEG Frame Sync (11 bits set: 0xFF followed by 0xE0 mask)
    if len(header) >= 2 and header[0] == 0xFF:
        second_byte = header[1]
        # Check if first 3 bits of second byte are 111 (0xE0)
        if (second_byte & 0xE0) == 0xE0:
            # Check Layer III (bits 1 & 2 of second byte == 01)
            layer = (second_byte & 0x06) >> 1
            if layer == 0x01:
                return "mp3"

    return None


def validate_audio_content(header: bytes, filename: str) -> Tuple[str, str]:
    """Validates actual binary content against expected audio extension.

    Returns:
        (detected_format, mime_type)
    """
    expected_ext = validate_extension(filename)
    detected_format = detect_audio_signature(header)

    if not detected_format:
        raise CorruptEvidenceError(
            reason=f"File content does not contain a recognized audio signature for '{expected_ext}'.",
            details={
                "filename": filename,
                "expected_extension": expected_ext,
                "header_hex": header[:16].hex() if header else "",
            },
        )

    # Map expected extension to format name
    expected_format = expected_ext.lstrip(".")

    # Ensure detected binary signature matches the file extension
    if detected_format != expected_format:
        raise CorruptEvidenceError(
            reason=f"File signature mismatch: header indicates '{detected_format.upper()}' but extension is '{expected_ext}'.",
            details={
                "expected_extension": expected_ext,
                "detected_format": detected_format,
            },
        )

    mime_type = MIME_TYPE_MAP.get(detected_format, "application/octet-stream")
    return detected_format, mime_type
