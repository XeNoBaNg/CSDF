"""Durable forensic audit trail query routes."""

from typing import Optional
from fastapi import APIRouter, Path, Query, status
from backend.app.core.errors import NotFoundError
from backend.app.schemas.audit import AuditEventResponse, AuditListResponse
from backend.app.services.audit_service import AuditService

router = APIRouter(tags=["Forensic Audit Trail"])

audit_service = AuditService()


@router.get(
    "/audit",
    response_model=AuditListResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Forensic Audit Trail",
    description=(
        "Retrieves a chronological list of forensic audit events with optional filtering by case, "
        "evidence, or action key."
    ),
)
async def query_audit_trail(
    case_id: Optional[str] = Query(None, description="Filter by case ID"),
    evidence_id: Optional[str] = Query(None, description="Filter by evidence ID"),
    action: Optional[str] = Query(None, description="Filter by action type (e.g. evidence_uploaded, integrity_verified)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum events to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> AuditListResponse:
    return audit_service.list_events(
        case_id=case_id,
        evidence_id=evidence_id,
        action=action,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/audit/{event_id}",
    response_model=AuditEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Audit Event Details",
    description="Retrieves a single durable audit record by event ID.",
)
async def get_audit_event(
    event_id: str = Path(..., description="Unique audit event identifier"),
) -> AuditEventResponse:
    event = audit_service.get_event(event_id)
    if not event:
        raise NotFoundError(message=f"Audit event '{event_id}' was not found.")
    return event
