"""Audio property and embedded metadata extraction."""

import logging
from typing import Dict, Optional
import mutagen
import soundfile as sf
from backend.app.analysis.decoder import verify_and_load_audio
from backend.app.evidence.storage import get_evidence_file_path
from backend.app.models.evidence import EvidenceModel
from backend.app.schemas.audio import (
    AudioMetadataResponse,
    DecodedProperties,
    EncodedProperties,
)

logger = logging.getLogger("audiosleuth.analysis.metadata")


def extract_embedded_tags(file_path: str) -> Dict[str, Optional[str]]:
    """Extracts available ID3, RIFF, or Vorbis metadata tags without modifying the file."""
    tags: Dict[str, Optional[str]] = {}
    try:
        audio = mutagen.File(file_path, easy=True)
        if audio and audio.tags:
            for key, val in audio.tags.items():
                if isinstance(val, (list, tuple)) and len(val) > 0:
                    tags[key] = str(val[0])
                else:
                    tags[key] = str(val)
    except Exception as exc:
        logger.debug("Mutagen could not read tags from %s: %s", file_path, exc)

    return tags


def extract_audio_metadata(item: EvidenceModel) -> AudioMetadataResponse:
    """Extracts comprehensive metadata, verifying storage integrity and clearly distinguishing
    encoded container properties from decoded acoustic properties.
    """
    # 1. Verify integrity and decode header properties
    path = get_evidence_file_path(item.stored_filename)
    _, _, decoded_info = verify_and_load_audio(item)

    # 2. Extract embedded tags via Mutagen
    embedded_tags = extract_embedded_tags(str(path))

    # 3. Calculate nominal bitrate if duration > 0
    duration = float(decoded_info["duration"])
    bitrate_kbps = None
    if duration > 0 and item.file_size_bytes > 0:
        # Approximate encoded bitrate in kbps
        bitrate_kbps = round((item.file_size_bytes * 8) / (duration * 1000), 2)

    # Codec / subtype label
    codec_label = decoded_info.get("subtype") or decoded_info.get("format") or item.format.upper()

    encoded_props = EncodedProperties(
        format=item.format,
        file_size_bytes=item.file_size_bytes,
        sha256_hash=item.sha256_hash,
        codec=codec_label,
        bitrate_kbps=bitrate_kbps,
    )

    decoded_props = DecodedProperties(
        duration_seconds=round(duration, 4),
        sample_rate_hz=int(decoded_info["sample_rate"]),
        channels=int(decoded_info["channels"]),
        total_samples=int(decoded_info["frames"]),
        sample_format=decoded_info.get("subtype"),
        bit_depth=decoded_info.get("bit_depth"),
    )

    return AudioMetadataResponse(
        evidence_id=item.id,
        case_id=item.case_id,
        original_filename=item.original_filename,
        integrity_verified=True,
        encoded_properties=encoded_props,
        decoded_properties=decoded_props,
        embedded_metadata=embedded_tags,
    )
