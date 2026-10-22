"""Domain model for digital audio evidence items."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class EvidenceModel:
    """Represents an ingested digital audio evidence recording."""

    id: str
    case_id: str
    original_filename: str
    stored_filename: str
    file_size_bytes: int
    sha256_hash: str
    format: str
    mime_type: str
    ingested_at: str
    integrity_status: str

    @classmethod
    def create(
        cls,
        evidence_id: str,
        case_id: str,
        original_filename: str,
        stored_filename: str,
        file_size_bytes: int,
        sha256_hash: str,
        format_name: str,
        mime_type: str,
        integrity_status: str = "verified",
        ingested_at: Optional[str] = None,
    ) -> "EvidenceModel":
        now = ingested_at or datetime.now(timezone.utc).isoformat()
        return cls(
            id=evidence_id,
            case_id=case_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_size_bytes=file_size_bytes,
            sha256_hash=sha256_hash.lower(),
            format=format_name.lower(),
            mime_type=mime_type,
            ingested_at=now,
            integrity_status=integrity_status,
        )
