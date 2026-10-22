"""Domain model for investigation cases."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class CaseModel:
    """Represents an investigative case file."""

    id: str
    title: str
    investigator_name: str
    notes: Optional[str]
    created_at: str
    updated_at: str
    description: Optional[str] = None
    status: str = "active"

    @classmethod
    def create(
        cls,
        case_id: str,
        title: str,
        investigator_name: str,
        notes: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "active",
    ) -> "CaseModel":
        now = datetime.now(timezone.utc).isoformat()
        desc = description.strip() if description else (notes.strip() if notes else None)
        return cls(
            id=case_id,
            title=title.strip(),
            investigator_name=investigator_name.strip(),
            notes=notes.strip() if notes else desc,
            description=desc,
            created_at=now,
            updated_at=now,
            status=status.strip().lower() if status else "active",
        )
