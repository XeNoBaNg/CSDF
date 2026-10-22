"""Forensic PDF examination report download and generation routes."""

from typing import Optional
from fastapi import APIRouter, Path, Query, Response, status
from backend.app.reports.report_service import ForensicReportService
from backend.app.schemas.report import ReportGenerateRequest

router = APIRouter(tags=["Forensic Reports"])

report_service = ForensicReportService()


@router.get(
    "/evidence/{evidence_id}/report",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Download Evidence Forensic PDF Report",
    description=(
        "Compiles and downloads an evidence-based forensic PDF report for the specified audio recording. "
        "Includes case metadata, cryptographic SHA-256 integrity verification, acoustic properties, "
        "explainable signal anomaly findings, embedded waveform and spectrogram visualizations, "
        "chronological audit trail, and ISO/IEC 27037 forensic disclaimers."
    ),
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Compiled forensic PDF report document.",
        },
    },
)
async def download_evidence_report(
    evidence_id: str = Path(..., description="Unique evidence identifier"),
    include_visualizations: bool = Query(True, description="Render and embed waveform & spectrogram charts"),
    include_audit: bool = Query(True, description="Include chronological chain-of-custody audit log"),
    run_analysis: bool = Query(True, description="Execute explainable signal anomaly detectors if not yet run"),
    notes: Optional[str] = Query(None, description="Optional supplementary examiner notes"),
) -> Response:
    pdf_bytes, filename, report_id = report_service.generate_evidence_report(
        evidence_id=evidence_id,
        include_visualizations=include_visualizations,
        include_audit=include_audit,
        run_analysis_if_missing=run_analysis,
        examiner_notes=notes,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Report-Id": report_id,
            "Access-Control-Expose-Headers": "Content-Disposition, X-Report-Id",
        },
    )


@router.post(
    "/evidence/{evidence_id}/report",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Generate Evidence Forensic PDF Report (POST)",
    description=(
        "Compiles and downloads an evidence-based forensic PDF report with custom configuration payload. "
        "Evidence integrity is strictly re-verified prior to document generation."
    ),
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Compiled forensic PDF report document.",
        },
    },
)
async def generate_evidence_report_post(
    evidence_id: str = Path(..., description="Unique evidence identifier"),
    request: Optional[ReportGenerateRequest] = None,
) -> Response:
    opts = request or ReportGenerateRequest()
    pdf_bytes, filename, report_id = report_service.generate_evidence_report(
        evidence_id=evidence_id,
        include_visualizations=opts.include_visualizations,
        include_audit=opts.include_audit,
        run_analysis_if_missing=opts.run_analysis_if_missing,
        examiner_notes=opts.examiner_notes,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Report-Id": report_id,
            "Access-Control-Expose-Headers": "Content-Disposition, X-Report-Id",
        },
    )


@router.get(
    "/cases/{case_id}/evidence/{evidence_id}/report",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Download Evidence Report with Case Relationship Validation",
    description=(
        "Validates that the evidence strictly belongs to the specified investigation case, "
        "re-verifies cryptographic integrity, and compiles the forensic PDF report."
    ),
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Compiled forensic PDF report document.",
        },
    },
)
async def download_case_evidence_report(
    case_id: str = Path(..., description="Unique case identifier"),
    evidence_id: str = Path(..., description="Unique evidence identifier"),
    include_visualizations: bool = Query(True, description="Render and embed waveform & spectrogram charts"),
    include_audit: bool = Query(True, description="Include chronological chain-of-custody audit log"),
    run_analysis: bool = Query(True, description="Execute explainable signal anomaly detectors"),
    notes: Optional[str] = Query(None, description="Optional supplementary examiner notes"),
) -> Response:
    pdf_bytes, filename, report_id = report_service.generate_evidence_report(
        evidence_id=evidence_id,
        case_id=case_id,
        include_visualizations=include_visualizations,
        include_audit=include_audit,
        run_analysis_if_missing=run_analysis,
        examiner_notes=notes,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Report-Id": report_id,
            "Access-Control-Expose-Headers": "Content-Disposition, X-Report-Id",
        },
    )
