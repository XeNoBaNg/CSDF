"""Schemas for case creation and retrieval."""

from typing import List, Optional
from pydantic import BaseModel, Field


class CaseCreateRequest(BaseModel):
    """Payload to initialize a new investigation case."""

    title: str = Field(..., min_length=2, max_length=200, description="Investigation case title")
    investigator_name: str = Field(..., min_length=2, max_length=100, description="Lead investigator name")
    notes: Optional[str] = Field(None, max_length=2000, description="Case background or investigation notes")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed case description")


class CaseUpdateRequest(BaseModel):
    """Payload to update editable metadata on an existing investigation case."""

    title: Optional[str] = Field(None, min_length=2, max_length=200, description="Updated case title")
    investigator_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Updated lead investigator name")
    notes: Optional[str] = Field(None, max_length=2000, description="Updated investigation notes")
    description: Optional[str] = Field(None, max_length=2000, description="Updated case description")
    status: Optional[str] = Field(None, pattern="^(active|closed)$", description="Updated case workflow status")


class CaseStatusUpdateRequest(BaseModel):
    """Payload to explicitly close or reopen an investigation case."""

    status: str = Field(..., pattern="^(active|closed)$", description="Explicit case status ('active' or 'closed')")
    reason: Optional[str] = Field(None, max_length=500, description="Investigator rationale for status transition")


class CaseResponse(BaseModel):
    """Case representation returned to clients."""

    id: str
    title: str
    investigator_name: str
    notes: Optional[str] = None
    description: Optional[str] = None
    status: str = "active"
    created_at: str
    updated_at: str
    evidence_count: int = 0


class CaseListResponse(BaseModel):
    """List of all registered investigation cases."""

    cases: List[CaseResponse]
    total: int

