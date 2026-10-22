"""Common API response and payload schemas for AudioSleuth."""

from datetime import datetime, timezone
from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class APIResponseEnvelope(BaseModel, Generic[DataT]):
    """Standard envelope for successful API responses."""

    success: bool = True
    message: Optional[str] = None
    data: DataT
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ErrorDetail(BaseModel):
    """Detailed error object representation."""

    code: str
    message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


class APIErrorResponseEnvelope(BaseModel):
    """Standard envelope for failed API responses."""

    success: bool = False
    error: ErrorDetail
