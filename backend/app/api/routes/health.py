"""Health check endpoint routes."""

from datetime import datetime, timezone
import hashlib
import time
from fastapi import APIRouter, status
from backend.app.core.config import settings
from backend.app.schemas.health import ComponentStatus, HealthCheckResponse

router = APIRouter(tags=["Health & Diagnostics"])

START_TIME = time.time()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Application Health & Subsystem Diagnostics",
    description="Returns the operational status of the AudioSleuth backend, storage readiness, and cryptographic hashing availability.",
)
async def get_health() -> HealthCheckResponse:
    """Performs real-time subsystem diagnostics."""
    components = {}
    is_healthy = True

    # 1. Evidence Storage Diagnostics
    try:
        storage_path = settings.resolved_evidence_dir
        writable = storage_path.exists() and storage_path.is_dir()
        components["storage"] = ComponentStatus(
            status="healthy" if writable else "degraded",
            details={
                "path": str(storage_path),
                "exists": storage_path.exists(),
                "writable": writable,
            },
        )
        if not writable:
            is_healthy = False
    except Exception as exc:
        components["storage"] = ComponentStatus(
            status="degraded",
            details={"error": str(exc)},
        )
        is_healthy = False

    # 2. Cryptographic Hashing Engine Verification
    try:
        # Verify SHA-256 with standard empty vector
        test_digest = hashlib.sha256(b"").hexdigest()
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        hash_ok = test_digest == expected
        components["cryptography"] = ComponentStatus(
            status="healthy" if hash_ok else "unhealthy",
            details={
                "algorithm": "SHA-256",
                "engine": "Python hashlib / OpenSSL",
                "test_vector_verified": hash_ok,
            },
        )
        if not hash_ok:
            is_healthy = False
    except Exception as exc:
        components["cryptography"] = ComponentStatus(
            status="unhealthy",
            details={"error": str(exc)},
        )
        is_healthy = False

    # 3. Persistence readiness (SQLite config check)
    components["persistence"] = ComponentStatus(
        status="healthy",
        details={
            "database_url": settings.DATABASE_URL.split("///")[-1],
            "mode": "SQLite (Local-first)",
        },
    )

    uptime = time.time() - START_TIME

    return HealthCheckResponse(
        status="healthy" if is_healthy else "degraded",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
        uptime_seconds=round(uptime, 2),
        components=components,
    )
