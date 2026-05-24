"""HTTP router factory for SelectionMaid.

Implements the FastAPI router using the closure pattern (D-85): build_router()
captures ExtractionService via closure so handlers have no global state and
no FastAPI Depends injection.

Decision references:
- D-83: app lives in app.py; router is separate for testability
- D-85: build_router(service) closure pattern — no globals, no Depends
- D-86: uptime_seconds via request.app.state.start_time (set in lifespan)
- D-78: HealthResponse fields: status, rss_mb, uptime_seconds, version
- D-82: structured error body {"error": {"code": "...", "message": "..."}}
"""
from __future__ import annotations

import importlib.metadata
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import psutil
from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import JSONResponse

from selection_maid.adapters.http.schemas import ExtractionResponse, HealthResponse
from selection_maid.errors import (
    ExtractionTimeoutError,
    SelectionMaidError,
    UnsupportedFormatError,
)

if TYPE_CHECKING:
    from selection_maid.service import ExtractionService

logger = logging.getLogger(__name__)

# D-82: Map domain error codes to HTTP status codes.
# Claude's discretion (06-CONTEXT.md): ExtractionTimeoutError → 504,
# UnsupportedFormatError → 415, all other SelectionMaidErrors → 500.
_ERROR_CODE_TO_HTTP: dict[str, int] = {
    "EXT-001": 500,  # ExtractionError — generic extraction failure
    "EXT-002": 415,  # UnsupportedFormatError — unsupported MIME type
    "EXT-003": 504,  # ExtractionTimeoutError — conversion timed out
    "FILT-001": 500,  # FilterError
    "CHUNK-001": 500,  # ChunkingError
    "ENRICH-001": 500,  # EnrichmentError
    "UPLOAD-001": 413,  # File too large
    "UPLOAD-002": 422,  # Magic bytes mismatch
}


def _error_response(code: str, message: str) -> JSONResponse:
    """Build a structured error response body (D-82).

    Args:
        code: Machine-readable error code from the domain taxonomy.
        message: Human-readable error description.

    Returns:
        JSONResponse with status from _ERROR_CODE_TO_HTTP and body
        {"error": {"code": code, "message": message}}.
    """
    status_code = _ERROR_CODE_TO_HTTP.get(code, 500)
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


def build_router(service: ExtractionService) -> APIRouter:
    """Build an APIRouter with all HTTP endpoints (D-85).

    Handlers capture ``service`` via closure — no globals, no FastAPI Depends,
    no mutable state. The router is isolated from app.py so tests can import
    and test it independently (ARCH-05).

    Args:
        service: Fully configured ExtractionService to dispatch to.

    Returns:
        APIRouter with GET /health and POST /ingest mounted.
    """
    router = APIRouter()

    @router.get("/health", response_model=HealthResponse)
    async def health(request: Request) -> HealthResponse:
        """GET /health — system liveness check (API-02, D-78).

        Returns current RSS memory in MB, uptime in seconds, and package version.
        start_time is read from request.app.state (D-86) — set by the lifespan
        manager in app.py.
        """
        process = psutil.Process()
        rss_mb = process.memory_info().rss / (1024 * 1024)

        start_time: datetime = request.app.state.start_time
        uptime_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()

        try:
            version = importlib.metadata.version("selectionmaid")
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"

        return HealthResponse(
            status="ok",
            rss_mb=rss_mb,
            uptime_seconds=uptime_seconds,
            version=version,
        )

    @router.post("/ingest", response_model=ExtractionResponse)
    async def ingest(file: UploadFile) -> ExtractionResponse | JSONResponse:
        """POST /ingest — main document ingestion endpoint (API-01).

        Skeleton implementation. Full validation (file size, MIME type, magic bytes)
        and ExtractionService dispatch are implemented in plans 06-03 and 06-04.

        Args:
            file: Uploaded document file via multipart/form-data.

        Returns:
            ExtractionResponse on success, or a structured error JSONResponse.
        """
        # Skeleton — full implementation in 06-03/06-04
        # This stub satisfies the router factory pattern requirement (ARCH-05)
        # and provides the signature for test infrastructure wiring.
        try:
            # Full pipeline wiring deferred to plan 06-03 (file validation)
            # and plan 06-04 (ExtractionService dispatch + run_in_threadpool).
            # For now we raise a NotImplementedError that tests can detect.
            raise NotImplementedError("POST /ingest is implemented in plan 06-03/06-04")
        except SelectionMaidError as exc:
            logger.error("Domain error during ingest: %s (%s)", exc.message, exc.code)
            return _error_response(exc.code, exc.message)
        except NotImplementedError as exc:
            return JSONResponse(
                status_code=501,
                content={"error": {"code": "NOT-IMPL", "message": str(exc)}},
            )

    return router
