"""Main entry point for AudioSleuth FastAPI backend application."""

from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from backend.app.api.routes import health
from backend.app.api.v1.router import api_v1_router
from backend.app.core.config import settings
from backend.app.core.errors import register_exception_handlers
from backend.app.core.logging import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs incoming HTTP requests, status codes, and execution duration."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        logger.info("--> %s %s from %s", request.method, request.url.path, client_ip)

        response = await call_next(request)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            "<-- %s %s [%d %s] completed in %0.2fms",
            request.method,
            request.url.path,
            response.status_code,
            response.headers.get("content-type", ""),
            duration_ms,
        )
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        return response


from backend.app.repositories.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle events."""
    logger.info("Initializing %s v%s in %s mode", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)
    # 1. Ensure evidence storage directory is initialized safely
    evidence_dir = settings.resolved_evidence_dir
    logger.info("Evidence storage directory prepared at: %s", evidence_dir)
    # 2. Ensure SQLite database tables are initialized
    init_db()
    yield
    logger.info("Shutting down %s backend service", settings.APP_NAME)


def create_app() -> FastAPI:
    """Application factory for AudioSleuth."""
    app = FastAPI(
        title=f"{settings.APP_NAME} — Digital Audio Forensics Toolkit",
        description="Local-first forensic analysis backend for audio integrity verification, signal anomaly detection, and forensic reporting.",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. Logging Middleware
    app.add_middleware(RequestLoggingMiddleware)

    # 2. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. Global Exception Handlers
    register_exception_handlers(app)

    # 4. Mount Health Route directly at /api/health and /health
    app.include_router(health.router, prefix=settings.API_PREFIX)
    app.include_router(health.router)

    # 5. Mount API Version 1
    app.include_router(api_v1_router, prefix=f"{settings.API_PREFIX}/v1")

    @app.get("/", tags=["Root"])
    async def root_index():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "online",
            "documentation": "/docs",
            "health_check": f"{settings.API_PREFIX}/health",
            "academic_context": "PICT CSDF Lab Mini-Project",
        }

    return app


app = create_app()
