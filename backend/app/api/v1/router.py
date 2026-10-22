"""API v1 router registry."""

from fastapi import APIRouter
from backend.app.api.routes import audit, cases, comparison, evidence, health, reports

api_v1_router = APIRouter()

# Mount health routes under /api/v1/health
api_v1_router.include_router(health.router)

# Mount cases routes (includes POST /cases, GET /cases, PATCH /cases/{id}, POST /cases/{id}/status, POST /cases/{case_id}/evidence)
api_v1_router.include_router(cases.router)

# Mount cross-recording comparison routes first (includes POST /evidence/compare, GET /comparisons/{id}, POST /evidence/compare/report)
api_v1_router.include_router(comparison.router)

# Mount evidence routes (includes GET /evidence, GET /evidence/{id}, POST /evidence/{id}/verify-integrity)
api_v1_router.include_router(evidence.router)

# Mount forensic audit trail routes (includes GET /audit, GET /audit/{id})
api_v1_router.include_router(audit.router)

# Mount forensic PDF report routes (includes GET /evidence/{id}/report, POST /evidence/{id}/report, GET /cases/{id}/evidence/{id}/report)
api_v1_router.include_router(reports.router)

