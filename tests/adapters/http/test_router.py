"""Tests for the HTTP router factory.

These are unit tests — the ExtractionService is mocked so no Docling models
load during this test suite. Full integration tests live in Phase 7.

Test coverage:
- GET /health returns HTTP 200 with valid HealthResponse schema
- HealthResponse contains required fields: status, rss_mb, uptime_seconds, version
- POST /ingest validation: file size (413), MIME type (415), magic bytes (422)
"""
from __future__ import annotations

import io

from fastapi.testclient import TestClient


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

    def test_validation_magic_real_pdf_passes_magic_check(
        self, client: TestClient
    ) -> None:
        """A real PDF (with correct magic bytes %PDF) passes Layer 3.

        After passing all 3 validation layers the request proceeds to the
        (not-yet-implemented) dispatch step and returns 501 (stub).
        """
        # Minimal valid PDF magic header
        pdf_magic = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
        response = client.post(
            "/ingest",
            files={"file": ("real.pdf", io.BytesIO(pdf_magic), "application/pdf")},
        )
        # Validation passes → stub returns 501 (dispatch not implemented yet)
        assert response.status_code == 501
