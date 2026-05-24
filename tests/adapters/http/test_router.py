"""Tests for the HTTP router factory.

These are unit tests — the ExtractionService is mocked so no Docling models
load during this test suite. Full integration tests live in Phase 7.

Test coverage:
- GET /health returns HTTP 200 with valid HealthResponse schema
- HealthResponse contains required fields: status, rss_mb, uptime_seconds, version
"""
from __future__ import annotations

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
