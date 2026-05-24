"""Tests for the HTTP router factory.

These are unit tests — the ExtractionService is mocked so no Docling models
load during this test suite. Full integration tests live in Phase 7.

Test coverage:
- GET /health returns HTTP 200 with valid HealthResponse schema
- HealthResponse contains required fields: status, rss_mb, uptime_seconds, version
- POST /ingest validation: file size (413), MIME type (415), magic bytes (422)
- POST /ingest success: 200 with ExtractionResponse JSON (mocked service)
- POST /ingest error mapping: domain SelectionMaidError -> HTTP status
- POST /ingest concurrency: multiple simultaneous requests don't block event loop
"""
from __future__ import annotations

import asyncio
import io
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from selection_maid.domain.models import (
    DocumentChunk,
    DocumentMetadata,
    ExtractionResult,
)
from selection_maid.errors import ExtractionError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_extraction_result() -> ExtractionResult:
    """Build a minimal ExtractionResult for mock return values."""
    metadata = DocumentMetadata(
        doc_id="test-doc-001",
        source_filename="test.pdf",
        title="Test Document",
        author="Test Author",
        language="en",
        doc_type="pdf",
        page_count=1,
        chunk_count=1,
        ingested_at=datetime(2026, 5, 24, 12, 0, 0, tzinfo=timezone.utc),
    )
    chunk = DocumentChunk(
        chunk_id="chunk-001",
        content="Hello world.",
        page_start=1,
        page_end=1,
        section_title="Introduction",
        chunk_index=0,
        total_chunks=1,
        word_count=2,
    )
    return ExtractionResult(metadata=metadata, chunks=(chunk,))


def _real_pdf_bytes() -> bytes:
    """Read the minimal sample PDF fixture from tests/fixtures/."""
    fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "sample.pdf"
    return fixture_path.read_bytes()


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    """Tests for GET /health (API-02, D-78)."""

    def test_health_returns_200(self, client: TestClient) -> None:
        """GET /health responds with HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_schema(self, client: TestClient) -> None:
        """GET /health returns a valid HealthResponse JSON body (D-78).

        All four required fields must be present and have the correct types:
        - status: str equal to "ok"
        - rss_mb: float > 0 (current process RSS)
        - uptime_seconds: float >= 0
        - version: str (package version or "unknown")
        """
        response = client.get("/health")
        body = response.json()

        assert body["status"] == "ok"
        assert isinstance(body["rss_mb"], float)
        assert body["rss_mb"] > 0
        assert isinstance(body["uptime_seconds"], float)
        assert body["uptime_seconds"] >= 0
        assert isinstance(body["version"], str)
        assert len(body["version"]) > 0

    def test_health_content_type(self, client: TestClient) -> None:
        """GET /health returns application/json content type."""
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]

    def test_health_no_extra_fields(self, client: TestClient) -> None:
        """GET /health response contains exactly the four expected fields."""
        response = client.get("/health")
        body = response.json()
        expected_fields = {"status", "rss_mb", "uptime_seconds", "version"}
        assert set(body.keys()) == expected_fields


# ---------------------------------------------------------------------------
# POST /ingest — Layer 1: size validation
# ---------------------------------------------------------------------------


class TestIngestValidationSize:
    """Tests for POST /ingest Layer 1: file size validation (D-79, T-06-03)."""

    def test_validation_size_content_length_too_large(
        self, client: TestClient
    ) -> None:
        """Reject upload when Content-Length header exceeds max_file_bytes (413).

        A request declaring a Content-Length larger than 50MB must be rejected
        immediately — before reading any file bytes (fail fast, D-79).
        """
        response = client.post(
            "/ingest",
            files={"file": ("big.pdf", io.BytesIO(b"x"), "application/pdf")},
            headers={"Content-Length": str(52_428_801)},  # 50MB + 1 byte
        )
        assert response.status_code == 413
        body = response.json()
        assert body["error"]["code"] == "UPLOAD-001"
        assert "error" in body

    def test_validation_size_error_body_structure(
        self, client: TestClient
    ) -> None:
        """413 response body must match structured error format (D-82)."""
        response = client.post(
            "/ingest",
            files={"file": ("big.pdf", io.BytesIO(b"x"), "application/pdf")},
            headers={"Content-Length": str(100_000_000)},  # 100MB
        )
        assert response.status_code == 413
        body = response.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]
        assert body["error"]["code"] == "UPLOAD-001"


# ---------------------------------------------------------------------------
# POST /ingest — Layer 2: declared MIME validation
# ---------------------------------------------------------------------------


class TestIngestValidationMime:
    """Tests for POST /ingest Layer 2: declared MIME type validation (D-80)."""

    def test_validation_mime_unsupported_type_returns_415(
        self, client: TestClient
    ) -> None:
        """Reject upload when declared content_type is not in allowed list (415).

        text/plain is not in [application/pdf, application/vnd...docx, text/html].
        """
        response = client.post(
            "/ingest",
            files={"file": ("doc.txt", io.BytesIO(b"hello"), "text/plain")},
        )
        assert response.status_code == 415
        body = response.json()
        assert body["error"]["code"] == "EXT-002"

    def test_validation_mime_octet_stream_returns_415(
        self, client: TestClient
    ) -> None:
        """Reject upload when content_type is application/octet-stream (415)."""
        response = client.post(
            "/ingest",
            files={
                "file": (
                    "doc.bin",
                    io.BytesIO(b"binary data"),
                    "application/octet-stream",
                )
            },
        )
        assert response.status_code == 415
        body = response.json()
        assert body["error"]["code"] == "EXT-002"

    def test_validation_mime_error_body_structure(
        self, client: TestClient
    ) -> None:
        """415 response body must match structured error format (D-82)."""
        response = client.post(
            "/ingest",
            files={"file": ("doc.txt", io.BytesIO(b"hello"), "text/plain")},
        )
        assert response.status_code == 415
        body = response.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]


# ---------------------------------------------------------------------------
# POST /ingest — Layer 3: magic bytes validation
# ---------------------------------------------------------------------------


class TestIngestValidationMagic:
    """Tests for POST /ingest Layer 3: magic bytes validation (D-81, T-06-04)."""

    def test_validation_magic_spoofed_pdf_returns_422(
        self, client: TestClient
    ) -> None:
        """Reject upload when magic bytes don't match declared MIME type (422).

        A plain text file uploaded with content_type=application/pdf must be
        detected as a mismatch and rejected.
        """
        # Plain text bytes masquerading as PDF
        fake_pdf_content = b"This is just plain text, not a real PDF file at all."
        response = client.post(
            "/ingest",
            files={
                "file": ("fake.pdf", io.BytesIO(fake_pdf_content), "application/pdf")
            },
        )
        assert response.status_code == 422
        body = response.json()
        assert body["error"]["code"] == "UPLOAD-002"

    def test_validation_magic_error_body_structure(
        self, client: TestClient
    ) -> None:
        """422 response body must match structured error format (D-82)."""
        fake_pdf_content = b"Not a PDF file at all."
        response = client.post(
            "/ingest",
            files={
                "file": ("fake.pdf", io.BytesIO(fake_pdf_content), "application/pdf")
            },
        )
        assert response.status_code == 422
        body = response.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]
        assert body["error"]["code"] == "UPLOAD-002"

    def test_validation_magic_real_pdf_passes_all_layers(
        self, client: TestClient, mock_service: MagicMock
    ) -> None:
        """A real PDF (with correct magic bytes %PDF) passes all 3 validation layers.

        After passing all 3 layers the request is dispatched to the service.
        The mock service returns a complete ExtractionResult; the router converts
        it to ExtractionResponse and returns HTTP 200.
        """
        mock_service.process.return_value = _make_extraction_result()

        pdf_bytes = _real_pdf_bytes()
        response = client.post(
            "/ingest",
            files={"file": ("real.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )
        # Validation passes and mock service returns successfully -> 200
        assert response.status_code == 200
        body = response.json()
        assert "metadata" in body
        assert "chunks" in body


# ---------------------------------------------------------------------------
# POST /ingest — success path (E2E with mocked service)
# ---------------------------------------------------------------------------


class TestIngestSuccess:
    """Tests for POST /ingest happy path (API-01)."""

    def test_ingest_success_returns_200(
        self, client: TestClient, mock_service: MagicMock
    ) -> None:
        """Upload a valid PDF; mock service returns ExtractionResult; expect HTTP 200.

        Verifies the full request lifecycle:
        validation -> threadpool dispatch -> ExtractionResponse serialization.
        """
        mock_service.process.return_value = _make_extraction_result()

        pdf_bytes = _real_pdf_bytes()
        response = client.post(
            "/ingest",
            files={"file": ("sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )
        assert response.status_code == 200

    def test_ingest_success_response_schema(
        self, client: TestClient, mock_service: MagicMock
    ) -> None:
        """POST /ingest returns ExtractionResponse with metadata and chunks (API-01, D-75).

        Verifies that ExtractionResult is correctly serialized to ExtractionResponse
        via model_validate(from_attributes=True) — all 9 metadata fields and 8 chunk
        fields are present in the JSON output.
        """
        result = _make_extraction_result()
        mock_service.process.return_value = result

        pdf_bytes = _real_pdf_bytes()
        response = client.post(
            "/ingest",
            files={"file": ("sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )
        assert response.status_code == 200
        body = response.json()

        # Verify top-level keys
        assert set(body.keys()) == {"metadata", "chunks"}

        # Verify metadata fields (all 9 per META-01)
        meta = body["metadata"]
        assert meta["doc_id"] == "test-doc-001"
        assert meta["source_filename"] == "test.pdf"
        assert meta["title"] == "Test Document"
        assert meta["author"] == "Test Author"
        assert meta["language"] == "en"
        assert meta["doc_type"] == "pdf"
        assert meta["page_count"] == 1
        assert meta["chunk_count"] == 1
        assert "ingested_at" in meta  # datetime serialized as ISO 8601 string

        # Verify chunks (all 8 fields per CHUNK-03)
        chunks = body["chunks"]
        assert len(chunks) == 1
        chunk = chunks[0]
        assert chunk["chunk_id"] == "chunk-001"
        assert chunk["content"] == "Hello world."
        assert chunk["page_start"] == 1
        assert chunk["page_end"] == 1
        assert chunk["section_title"] == "Introduction"
        assert chunk["chunk_index"] == 0
        assert chunk["total_chunks"] == 1
        assert chunk["word_count"] == 2

    def test_ingest_success_content_type(
        self, client: TestClient, mock_service: MagicMock
    ) -> None:
        """POST /ingest response has application/json content type."""
        mock_service.process.return_value = _make_extraction_result()

        pdf_bytes = _real_pdf_bytes()
        response = client.post(
            "/ingest",
            files={"file": ("sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_ingest_success_tempfile_cleaned_up(
        self, client: TestClient, mock_service: MagicMock
    ) -> None:
        """Tempfile created during ingest is deleted after processing (D-87, T-06-05).

        Monkeypatches tempfile.NamedTemporaryFile to track the created path,
        then verifies it no longer exists after the request completes.
        """
        import tempfile as _tempfile

        created_paths: list[Path] = []
        original_ntf = _tempfile.NamedTemporaryFile

        def _tracking_ntf(*args: object, **kwargs: object) -> object:
            ntf = original_ntf(*args, **kwargs)  # type: ignore[call-overload]
            created_paths.append(Path(ntf.name))
            return ntf

        mock_service.process.return_value = _make_extraction_result()

        import selection_maid.adapters.http.router as _router_module

        original_ntf_in_module = _router_module.tempfile.NamedTemporaryFile  # type: ignore[attr-defined]
        _router_module.tempfile.NamedTemporaryFile = _tracking_ntf  # type: ignore[attr-defined]
        try:
            pdf_bytes = _real_pdf_bytes()
            response = client.post(
                "/ingest",
                files={
                    "file": ("sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")
                },
            )
        finally:
            _router_module.tempfile.NamedTemporaryFile = original_ntf_in_module  # type: ignore[attr-defined]

        assert response.status_code == 200
        # All tempfiles must be deleted
        for p in created_paths:
            assert not p.exists(), f"Tempfile {p} was not cleaned up"


# ---------------------------------------------------------------------------
# POST /ingest — error mapping
# ---------------------------------------------------------------------------


class TestIngestErrorMapping:
    """Tests for POST /ingest domain error -> HTTP status mapping (D-82)."""

    def test_ingest_extraction_error_returns_500(
        self, client: TestClient, mock_service: MagicMock
    ) -> None:
        """ExtractionError (EXT-001) from service maps to HTTP 500.

        Verifies that SelectionMaidError subclasses raised by the service are
        caught by the router and converted to structured JSON error responses.
        """
        mock_service.process.side_effect = ExtractionError(
            message="Docling could not parse the document."
        )

        pdf_bytes = _real_pdf_bytes()
        response = client.post(
            "/ingest",
            files={"file": ("sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )
        assert response.status_code == 500
        body = response.json()
        assert body["error"]["code"] == "EXT-001"
        assert "Docling could not parse" in body["error"]["message"]

    def test_ingest_error_body_structure(
        self, client: TestClient, mock_service: MagicMock
    ) -> None:
        """Domain errors produce structured error body (D-82)."""
        mock_service.process.side_effect = ExtractionError(
            message="Extraction failed."
        )

        pdf_bytes = _real_pdf_bytes()
        response = client.post(
            "/ingest",
            files={"file": ("sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )
        assert response.status_code == 500
        body = response.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]

    def test_ingest_unexpected_error_returns_500(
        self, client: TestClient, mock_service: MagicMock
    ) -> None:
        """Non-domain exceptions from the service map to HTTP 500 / EXT-001."""
        mock_service.process.side_effect = RuntimeError("Unexpected crash")

        pdf_bytes = _real_pdf_bytes()
        response = client.post(
            "/ingest",
            files={"file": ("sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )
        assert response.status_code == 500
        body = response.json()
        assert body["error"]["code"] == "EXT-001"


# ---------------------------------------------------------------------------
# POST /ingest — concurrency
# ---------------------------------------------------------------------------


class TestIngestConcurrency:
    """Tests for POST /ingest non-blocking concurrency (D-88, Success Criteria #5)."""

    def test_ingest_concurrency_two_requests(
        self, mock_service: MagicMock
    ) -> None:
        """Two simultaneous POST /ingest requests complete without blocking.

        Sends two requests concurrently via asyncio.gather using an AsyncClient.
        Both must complete successfully — verifying that run_in_threadpool does
        not hold the event loop while Docling processes the first request.

        Uses httpx.AsyncClient (not TestClient) because TestClient is synchronous
        and cannot perform concurrent requests in the same thread.

        Routes are included at app creation time (not inside lifespan) so that
        FastAPI's routing layer is ready before any request arrives.
        """
        import httpx
        from contextlib import asynccontextmanager
        from datetime import datetime, timezone
        from typing import AsyncIterator

        from fastapi import FastAPI
        from selection_maid.adapters.http.router import build_router
        from selection_maid.config import get_config

        mock_service.process.return_value = _make_extraction_result()

        # Build the router and include it *before* starting the app so routes
        # are registered at construction time, not inside the lifespan.
        router = build_router(mock_service, get_config())

        @asynccontextmanager
        async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
            app.state.start_time = datetime.now(timezone.utc)
            yield

        app = FastAPI(lifespan=_lifespan)
        app.include_router(router)

        pdf_bytes = _real_pdf_bytes()

        async def _run_concurrent() -> tuple[int, int]:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as ac:
                r1, r2 = await asyncio.gather(
                    ac.post(
                        "/ingest",
                        files={
                            "file": (
                                "a.pdf",
                                io.BytesIO(pdf_bytes),
                                "application/pdf",
                            )
                        },
                    ),
                    ac.post(
                        "/ingest",
                        files={
                            "file": (
                                "b.pdf",
                                io.BytesIO(pdf_bytes),
                                "application/pdf",
                            )
                        },
                    ),
                )
            return r1.status_code, r2.status_code

        status1, status2 = asyncio.run(_run_concurrent())
        assert status1 == 200, f"First concurrent request returned {status1}"
        assert status2 == 200, f"Second concurrent request returned {status2}"
        # Both requests must have called service.process (once each)
        assert mock_service.process.call_count == 2
