"""CORS policy tests for the FastAPI application."""
from __future__ import annotations

from fastapi.testclient import TestClient

from selection_maid.adapters.http.app import app


def test_preflight_allows_local_vite_origin() -> None:
    """OPTIONS preflight from the Vite dev server is allowed."""
    response = TestClient(app).options(
        "/",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:5173"
    )
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "OPTIONS" in response.headers["access-control-allow-methods"]


def test_preflight_rejects_untrusted_origin() -> None:
    """OPTIONS preflight from an untrusted origin is not granted CORS access."""
    response = TestClient(app).options(
        "/",
        headers={
            "Origin": "http://malicious.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code in {400, 404}
    assert "access-control-allow-origin" not in response.headers


def test_actual_post_includes_cors_header_for_local_vite_origin() -> None:
    """Actual POST responses include the allowed origin header."""
    response = TestClient(app).post(
        "/ingest",
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:5173"
    )
