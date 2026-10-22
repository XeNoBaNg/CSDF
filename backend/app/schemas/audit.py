"""Schemas for forensic audit events and chain-of-custody tracking."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AuditEventResponse(BaseModel):
    """Structured representation of a single forensic audit event."""

    id: str = Field(..., description="Unique audit event identifier (e.g. AUD-20261023120000-xxxx)")
    timestamp: str = Field(..., description="UTC ISO 8601 timestamp when action was recorded")
    action: str = Field(..., description="Action performed (e.g. case_created, evidence_uploaded, integrity_verified)")
    outcome: str = Field(..., description="Action outcome (e.g. success, failure, verified_match, integrity_mismatch)")
    case_id: Optional[str] = Field(None, description="Owning case identifier if applicable")
    evidence_id: Optional[str] = Field(None, description="Associated evidence identifier if applicable")
    details: Dict[str, Any] = Field(default_factory=dict, description="Contextual parameters, filenames, or metrics")


class AuditListResponse(BaseModel):
    """Paginated collection of durable forensic audit log records."""

    items: List[AuditEventResponse] = Field(..., description="List of audit events ordered chronologically")
    total: int = Field(..., ge=0, description="Total matching audit records")
    case_id: Optional[str] = Field(None, description="Filtered case identifier if scoped")
    disclaimer: str = Field(
        default=(
            "Audit records are stored in local SQLite persistence for investigative tracking and compliance reporting. "
            "Local SQLite records provide an operational audit trail but do not by themselves constitute a certified "
            "tamper-proof hardware timestamp (ISO/IEC 27037 disclosure)."
        ),
        description="Evidentiary disclosure regarding audit trail storage",
    )
