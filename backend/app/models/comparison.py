"""Comparison model entity for AudioSleuth."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ComparisonRecordModel:
    """Represents a persisted cross-recording forensic comparison record."""

    id: str
    evidence_id_a: str
    evidence_id_b: str
    case_id_a: Optional[str]
    case_id_b: Optional[str]
    hash_a: str
    hash_b: str
    metrics_summary_json: str
    created_at: str
