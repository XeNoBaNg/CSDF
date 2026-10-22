"""Standard error handlers and exception types for AudioSleuth."""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("audiosleuth.errors")


class AudioSleuthError(Exception):
    """Base exception for all domain-specific AudioSleuth errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AudioSleuthError):
    """Resource not found error."""

    def __init__(self, message: str = "Requested resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class EvidenceIntegrityError(AudioSleuthError):
    """Cryptographic integrity mismatch or failure."""

    def __init__(self, message: str = "Evidence integrity verification failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="INTEGRITY_MISMATCH",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class CaseNotFoundError(AudioSleuthError):
    """Specified investigation case does not exist."""

    def __init__(self, case_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Investigation case '{case_id}' was not found.",
            code="CASE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"case_id": case_id},
        )


class CaseClosedError(AudioSleuthError):
    """Attempted operation on a closed investigation case."""

    def __init__(self, case_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Investigation case '{case_id}' is closed. Reopen the case to ingest additional evidence.",
            code="CASE_CLOSED",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"case_id": case_id},
        )


class CaseEvidenceMismatchError(AudioSleuthError):
    """Evidence item does not belong to the specified case."""

    def __init__(self, case_id: str, evidence_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Evidence item '{evidence_id}' does not belong to case '{case_id}'.",
            code="CASE_EVIDENCE_MISMATCH",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"case_id": case_id, "evidence_id": evidence_id},
        )


class EvidenceNotFoundError(AudioSleuthError):
    """Specified evidence item does not exist."""

    def __init__(self, evidence_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Evidence item '{evidence_id}' was not found.",
            code="EVIDENCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"evidence_id": evidence_id},
        )


class OversizedFileError(AudioSleuthError):
    """Uploaded file exceeds server-configured maximum size."""

    def __init__(self, max_mb: int, message: Optional[str] = None):
        super().__init__(
            message=message or f"Evidence file exceeds the maximum permitted limit of {max_mb} MB.",
            code="PAYLOAD_TOO_LARGE",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            details={"max_size_mb": max_mb},
        )


class UnsupportedFormatError(AudioSleuthError):
    """File extension or audio format is not supported."""

    def __init__(self, format_name: str, supported: list[str], message: Optional[str] = None):
        super().__init__(
            message=message or f"Format '{format_name}' is not supported. Accepted formats: {', '.join(supported)}.",
            code="UNSUPPORTED_MEDIA_TYPE",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            details={"detected_format": format_name, "supported_formats": supported},
        )


class CorruptEvidenceError(AudioSleuthError):
    """Uploaded file is empty, truncated, or has a mismatched magic signature."""

    def __init__(self, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Evidence validation rejected: {reason}",
            code="MALFORMED_EVIDENCE",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details or {"reason": reason},
        )


class MissingEvidenceFileError(AudioSleuthError):
    """Evidence record exists but physical file on disk is missing or unreadable."""

    def __init__(self, evidence_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Stored evidence file for '{evidence_id}' is missing or unreadable on disk.",
            code="EVIDENCE_FILE_MISSING",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"evidence_id": evidence_id},
        )


class ResourceLimitExceededError(AudioSleuthError):
    """Inspection or analysis request exceeds configured resource limits."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="RESOURCE_LIMIT_EXCEEDED",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            details=details or {},
        )


def make_error_response(
    code: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Creates a consistent, unified JSON error payload without leaking internal traces."""
    content = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        },
    }
    return JSONResponse(status_code=status_code, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    """Registers standard exception handlers across the application."""

    @app.exception_handler(AudioSleuthError)
    async def handle_audiosleuth_error(request: Request, exc: AudioSleuthError) -> JSONResponse:
        logger.warning(
            "Application error on %s %s: [%s] %s",
            request.method,
            request.url.path,
            exc.code,
            exc.message,
        )
        return make_error_response(
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning("Request validation error on %s %s: %s", request.method, request.url.path, exc.errors())
        # Format errors cleanly without raw internal python representations
        clean_errors = []
        for err in exc.errors():
            clean_errors.append({
                "loc": " -> ".join(str(item) for item in err.get("loc", [])),
                "msg": err.get("msg", "Invalid value"),
                "type": err.get("type", "value_error"),
            })
        return make_error_response(
            code="REQUEST_VALIDATION_ERROR",
            message="The request payload failed schema validation.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"validation_errors": clean_errors},
        )

    from starlette.exceptions import HTTPException as StarletteHTTPException

    @app.exception_handler(StarletteHTTPException)
    async def handle_starlette_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        logger.info("HTTP %d on %s %s: %s", exc.status_code, request.method, request.url.path, exc.detail)
        return make_error_response(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            status_code=exc.status_code,
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        logger.info("HTTP %d on %s %s: %s", exc.status_code, request.method, request.url.path, exc.detail)
        return make_error_response(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            status_code=exc.status_code,
        )

    @app.exception_handler(Exception)
    async def handle_uncaught_exception(request: Request, exc: Exception) -> JSONResponse:
        # Log full traceback internally for investigator troubleshooting
        logger.error(
            "Unhandled server exception on %s %s: %s",
            request.method,
            request.url.path,
            exc,
            exc_info=True,
        )
        # Return sanitized response to client
        return make_error_response(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred while processing the forensic request.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
