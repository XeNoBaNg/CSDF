"""Domain model for durable forensic audit events."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid


@dataclass
class AuditEventModel:
    """Represents a durable audit log event recording an investigative action."""

    id: str
    timestamp: str
    action: str
    outcome: str
    case_id: Optional[str] = None
    evidence_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        action: str,
        outcome: str,
        case_id: Optional[str] = None,
        evidence_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        event_id: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> "AuditEventModel":
        now = timestamp or datetime.now(timezone.utc).isoformat()
        uid = event_id or f"AUD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        return cls(
            id=uid,
            timestamp=now,
            action=action.strip(),
            outcome=outcome.strip(),
            case_id=case_id.strip() if case_id else None,
            evidence_id=evidence_id.strip() if evidence_id else None,
            details=details or {},
        )
