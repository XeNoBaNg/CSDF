"""Case endpoints and case evidence intake routes."""

from typing import Optional
from fastapi import APIRouter, File, Path, Query, UploadFile, status
from backend.app.schemas.audit import AuditListResponse
from backend.app.schemas.case import (
    CaseCreateRequest,
    CaseListResponse,
    CaseResponse,
    CaseStatusUpdateRequest,
    CaseUpdateRequest,
)
from backend.app.schemas.evidence import EvidenceListResponse, EvidenceResponse
from backend.app.services.audit_service import AuditService
from backend.app.services.case_service import CaseService
from backend.app.services.evidence_service import EvidenceService

router = APIRouter(tags=["Cases & Evidence Intake"])

case_service = CaseService()
evidence_service = EvidenceService()
audit_service = AuditService()


@router.post(
    "/cases",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize New Forensic Case",
    description="Registers a new forensic investigation case record in the local database.",
)
async def create_case(payload: CaseCreateRequest) -> CaseResponse:
    return case_service.create_case(payload)


@router.get(
    "/cases",
    response_model=CaseListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Investigation Cases",
    description="Lists registered forensic investigation cases, optionally filtered by status ('active', 'closed', 'all').",
)
async def list_cases(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by case status ('active', 'closed', 'all')"),
) -> CaseListResponse:
    return case_service.list_cases(status=status_filter)


@router.get(
    "/cases/{case_id}",
    response_model=CaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Case Details",
    description="Retrieves metadata for a specific investigation case.",
)
async def get_case(
    case_id: str = Path(..., description="Unique case identifier"),
) -> CaseResponse:
    return case_service.get_case(case_id)


@router.patch(
    "/cases/{case_id}",
    response_model=CaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Case Metadata",
    description="Updates editable metadata fields (title, investigator_name, description, notes, status) on an existing case.",
)
async def update_case(
    case_id: str = Path(..., description="Unique case identifier"),
    payload: CaseUpdateRequest = ...,
) -> CaseResponse:
    return case_service.update_case(case_id, payload)


@router.post(
    "/cases/{case_id}/status",
    response_model=CaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Case Workflow Status",
    description="Explicitly transitions case status between 'active' and 'closed'.",
)
async def update_case_status(
    case_id: str = Path(..., description="Unique case identifier"),
    payload: CaseStatusUpdateRequest = ...,
) -> CaseResponse:
    return case_service.set_case_status(case_id, payload.status, payload.reason)


@router.get(
    "/cases/{case_id}/audit",
    response_model=AuditListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Case Audit Trail",
    description="Retrieves the chronological audit log of all forensic operations executed for a specific case.",
)
async def list_case_audit_trail(
    case_id: str = Path(..., description="Unique case identifier"),
    limit: int = Query(100, ge=1, le=500, description="Maximum audit events to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> AuditListResponse:
    # Enforce case existence check
    case_service.get_case(case_id)
    return audit_service.list_events(case_id=case_id, limit=limit, offset=offset)


@router.post(
    "/cases/{case_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Digital Audio Evidence",
    description=(
        "Uploads a digital audio file (WAV, MP3, FLAC) into isolated evidence storage. "
        "Calculates cryptographic SHA-256 digest, validates binary signatures, and registers the evidence item. "
        "Rejects upload if target case is closed."
    ),
)
async def upload_case_evidence(
    case_id: str = Path(..., description="Target investigation case ID"),
    file: UploadFile = File(..., description="Audio evidence recording (WAV, MP3, FLAC)"),
) -> EvidenceResponse:
    return await evidence_service.acquire_evidence(case_id=case_id, upload_file=file)


@router.get(
    "/cases/{case_id}/evidence",
    response_model=EvidenceListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Case Evidence Items",
    description="Retrieves all digital audio evidence items registered under the specified case.",
)
async def list_case_evidence(
    case_id: str = Path(..., description="Investigation case ID"),
) -> EvidenceListResponse:
    return evidence_service.list_evidence_by_case(case_id=case_id)

