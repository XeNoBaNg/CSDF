"""API routes for cross-recording forensic comparison and comparative PDF reports."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Path, Response, status
from fastapi.responses import StreamingResponse
import io
from backend.app.reports.comparison_pdf_generator import ComparisonPdfReportGenerator
from backend.app.schemas.comparison import ComparisonRequest, ComparisonResponse
from backend.app.services.comparison_service import ComparisonService

router = APIRouter(tags=["Cross-Recording Comparison"])

comparison_service = ComparisonService()
pdf_generator = ComparisonPdfReportGenerator()


@router.post(
    "/evidence/compare",
    response_model=ComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Cross-Recording Forensic Comparison",
    description=(
        "Performs deterministic cross-recording forensic comparison between two registered evidence recordings. "
        "Verifies cryptographic integrity of both files, compares metadata, calculates signal-level statistics, "
        "evaluates STFT spectral cosine similarity, and optionally analyzes Phase 4 anomaly temporal distributions."
    ),
)
async def compare_recordings(request: ComparisonRequest) -> ComparisonResponse:
    """Executes a forensic comparison between two evidence recordings."""
    return comparison_service.compare_evidence(request)


@router.get(
    "/comparisons/{comparison_id}",
    response_model=ComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Persisted Comparison Result",
    description="Fetches a historical cross-recording comparison result by its unique identifier.",
)
async def get_comparison_result(
    comparison_id: str = Path(..., description="Unique comparison identifier"),
) -> ComparisonResponse:
    """Retrieves a persisted comparison record."""
    result = comparison_service.get_comparison(comparison_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "COMPARISON_NOT_FOUND",
                    "message": f"Comparison record '{comparison_id}' was not found.",
                }
            },
        )
    return result


@router.post(
    "/evidence/compare/report",
    status_code=status.HTTP_200_OK,
    summary="Generate & Download Cross-Recording Comparison PDF Report",
    description=(
        "Executes cross-recording forensic comparison and compiles a downloadable, evidence-based "
        "PDF comparison report in memory without saving temporary files to disk."
    ),
)
async def generate_comparison_report_post(request: ComparisonRequest):
    """Executes comparison and streams the generated PDF report."""
    comparison = comparison_service.compare_evidence(request)
    pdf_bytes = pdf_generator.generate_pdf(comparison)

    filename = f"AudioSleuth_Comparison_{comparison.id}.pdf"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "application/pdf",
        "X-Comparison-ID": comparison.id,
    }

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers=headers,
    )


@router.get(
    "/comparisons/{comparison_id}/report",
    status_code=status.HTTP_200_OK,
    summary="Download Persisted Comparison PDF Report",
    description="Generates and streams a downloadable PDF report for a previously saved comparison record.",
)
async def get_comparison_report_by_id(
    comparison_id: str = Path(..., description="Unique comparison identifier"),
):
    """Generates and downloads PDF report from a stored comparison."""
    comparison = comparison_service.get_comparison(comparison_id)
    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "COMPARISON_NOT_FOUND",
                    "message": f"Comparison record '{comparison_id}' was not found.",
                }
            },
        )

    pdf_bytes = pdf_generator.generate_pdf(comparison)
    filename = f"AudioSleuth_Comparison_{comparison.id}.pdf"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "application/pdf",
        "X-Comparison-ID": comparison.id,
    }

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers=headers,
    )
