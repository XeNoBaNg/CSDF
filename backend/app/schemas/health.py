"""Health and diagnostic schemas for AudioSleuth."""

from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, Field


class ComponentStatus(BaseModel):
    """Status of an individual backend subsystem."""

    status: str = Field(..., description="Component state: healthy, degraded, or offline")
    details: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic details")


class HealthCheckResponse(BaseModel):
    """Payload returned by GET /api/health and GET /api/v1/health."""

    status: str = Field(..., description="Overall service status: healthy or degraded")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Current environment mode")
    timestamp: datetime = Field(..., description="UTC timestamp of the health check")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    components: Dict[str, ComponentStatus] = Field(
        default_factory=dict,
        description="Subsystem health statuses (storage, hashing, persistence)",
    )
