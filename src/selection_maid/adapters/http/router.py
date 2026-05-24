"""HTTP router factory for SelectionMaid.

Implements the FastAPI router using the closure pattern (D-85): build_router()
captures ExtractionService and GlobalConfig via closure so handlers have no
global state and no FastAPI Depends injection.

Decision references:
- D-83: app lives in app.py; router is separate for testability
- D-85: build_router(service, config) closure pattern — no globals, no Depends
- D-86: uptime_seconds via request.app.state.start_time (set in lifespan)
- D-78: HealthResponse fields: status, rss_mb, uptime_seconds, version
- D-79: Content-Length header checked first (fail fast without reading bytes)
- D-80: Declared MIME type checked against allowed_mime_types list
- D-81: Magic bytes verified with python-magic before domain processing
- D-82: structured error body {"error": {"code": "...", "message": "..."}}
- D-87: UploadFile written to NamedTemporaryFile(delete=False), deleted in finally
- D-88: service.process() dispatched via run_in_threadpool (CPU-bound, non-blocking)
"""
from __future__ import annotations

import importlib.metadata
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import magic
import psutil
from fastapi import APIRouter, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from selection_maid.adapters.http.error_map import ERROR_CODE_TO_HTTP
from selection_maid.adapters.http.schemas import ExtractionResponse, HealthResponse
from selection_maid.domain.models import RawInput
from selection_maid.errors import SelectionMaidError

if TYPE_CHECKING:
    from selection_maid.config import GlobalConfig
    from selection_maid.service import ExtractionService

logger = logging.getLogger(__name__)

#: Number of bytes to read for magic bytes detection (D-81).
_MAGIC_READ_BYTES: int = 2048

#: MIME type to file extension mapping for tempfile suffix derivation (D-87).
_MIME_TO_EXT: dict[str, str] = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/html": ".html",
}

#: Mapping used by _error_response() to look up HTTP status from error code.
#: Re-exported here for backward compatibility (tests importing from router.py).
_ERROR_CODE_TO_HTTP = ERROR_CODE_TO_HTTP


def _error_response(code: str, message: str) -> JSONResponse:
    """Build a structured error response body (D-82).

    Args:
        code: Machine-readable error code from the domain taxonomy.
        message: Human-readable error description.

    Returns:
        JSONResponse with status from ERROR_CODE_TO_HTTP and body
        {"error": {"code": code, "message": message}}.
    """
    status_code = ERROR_CODE_TO_HTTP.get(code, 500)
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


def build_router(service: ExtractionService, config: GlobalConfig) -> APIRouter:
    """Build an APIRouter with all HTTP endpoints (D-85).

    Handlers capture ``service`` and ``config`` via closure — no globals, no
    FastAPI Depends, no mutable state. The router is isolated from app.py so
    tests can import and test it independently (ARCH-05).

    Args:
        service: Fully configured ExtractionService to dispatch to.
        config: GlobalConfig with HttpConfig for upload validation parameters.

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
    async def ingest(
        request: Request, file: UploadFile
    ) -> ExtractionResponse | JSONResponse:
        """POST /ingest — main document ingestion endpoint (API-01, API-03).

        3-layer validation (D-79, D-80, D-81) occurs before any domain processing
        (fail fast):

        1. Layer 1 — Size: Check Content-Length header; reject if > max_file_bytes
           with HTTP 413 / UPLOAD-001.
        2. Layer 2 — MIME: Check UploadFile.content_type; reject if not in
           allowed_mime_types with HTTP 415 / EXT-002.
        3. Layer 3 — Magic bytes: Read first _MAGIC_READ_BYTES bytes and detect
           real MIME type via libmagic; reject if detected != declared with
           HTTP 422 / UPLOAD-002.

        After validation passes, dispatch to ExtractionService via
        run_in_threadpool (implemented in plan 06-04).

        Args:
            request: FastAPI Request (for Content-Length header access).
            file: Uploaded document file via multipart/form-data.

        Returns:
            ExtractionResponse on success, or a structured error JSONResponse.
        """
        http_cfg = config.http

        # ---- Layer 1: Content-Length header check (fail fast, D-79) ----
        content_length_str = request.headers.get("content-length")
        if content_length_str is not None:
            try:
                content_length = int(content_length_str)
            except ValueError:
                content_length = 0
            if content_length > http_cfg.max_file_bytes:
                return _error_response(
                    "UPLOAD-001",
                    f"File size declared in Content-Length ({content_length} bytes) "
                    f"exceeds maximum allowed size ({http_cfg.max_file_bytes} bytes).",
                )

        # ---- Layer 2: Declared MIME type check (D-80) ----
        declared_mime = (file.content_type or "").split(";")[0].strip().lower()
        if declared_mime not in http_cfg.allowed_mime_types:
            return _error_response(
                "EXT-002",
                f"MIME type '{declared_mime}' is not supported. "
                f"Accepted types: {', '.join(http_cfg.allowed_mime_types)}.",
            )

        # ---- Layer 3: Magic bytes verification (D-81) ----
        try:
            header_bytes = await file.read(_MAGIC_READ_BYTES)
        except Exception as exc:
            logger.error("Failed to read file bytes for magic check: %s", exc)
            return _error_response(
                "EXT-001",
                "Failed to read uploaded file for validation.",
            )

        # Reset file position so downstream processing can re-read from start
        await file.seek(0)

        detected_mime: str = magic.from_buffer(header_bytes, mime=True)
        # Normalize: libmagic may return "text/x-c" or similar for plain text
        # content. We do an exact match against the declared MIME type.
        if detected_mime != declared_mime:
            return _error_response(
                "UPLOAD-002",
                f"Magic bytes indicate MIME type '{detected_mime}' but "
                f"'{declared_mime}' was declared. Upload rejected.",
            )

        # ---- Validation passed — dispatch to ExtractionService (D-87, D-88) ----
        #
        # Write the upload to a NamedTemporaryFile so Docling receives a real
        # filesystem path. delete=False lets us control deletion ourselves in
        # the finally block — guaranteed even when processing fails (D-87).
        ext = _MIME_TO_EXT.get(declared_mime, "")

        tmp_path: Path | None = None
        try:
            # Write UploadFile contents to tempfile with restricted permissions
            # (mode=0o600 — readable only by the owning process, T-06-05).
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=ext, mode="wb"
            ) as tmp:
                tmp_path = Path(tmp.name)
                # Read the file in chunks to avoid loading the entire body into
                # memory at once. UploadFile.read() without size reads all bytes.
                content_bytes = await file.read()
                tmp.write(content_bytes)

            raw_input = RawInput(
                path=tmp_path,
                filename=file.filename or "upload",
                mime_type=declared_mime,
            )

            # Offload CPU-bound Docling processing to the thread executor so the
            # event loop is never blocked (D-88).
            result = await run_in_threadpool(service.process, raw_input)

            return ExtractionResponse.model_validate(result, from_attributes=True)

        except SelectionMaidError as exc:
            logger.error("Domain error during ingest: %s (%s)", exc.message, exc.code)
            return _error_response(exc.code, exc.message)
        except Exception as exc:
            logger.exception("Unexpected error during ingest: %s", exc)
            return _error_response("EXT-001", f"Unexpected error during processing: {exc}")
        finally:
            # Always clean up the tempfile — even on error (D-87, T-06-05).
            if tmp_path is not None and tmp_path.exists():
                try:
                    os.unlink(tmp_path)
                except OSError as unlink_err:
                    logger.warning(
                        "Failed to delete tempfile %s: %s", tmp_path, unlink_err
                    )

    return router
