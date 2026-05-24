"""Test fixtures for the HTTP adapter layer.

Provides a TestClient fixture backed by a minimal FastAPI app that:
- Skips the full Docling lifespan (avoids expensive model loading in unit tests)
- Wires the router with a mock ExtractionService
- Sets app.state.start_time for /health uptime calculation (D-86)

For integration tests that require the real DocumentConverter, use a separate
fixture at a higher scope (see CLAUDE.md §Testing Patterns).
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncIterator
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from selection_maid.adapters.http.router import build_router
from selection_maid.service import ExtractionService


@pytest.fixture
def mock_service() -> MagicMock:
    """Return a MagicMock that satisfies the ExtractionService interface."""
    return MagicMock(spec=ExtractionService)


@pytest.fixture
def client(mock_service: MagicMock) -> TestClient:
    """Synchronous TestClient backed by a minimal FastAPI app.

    The app uses a lightweight lifespan that:
    - Sets app.state.start_time (required by GET /health — D-86)
    - Includes the router built from the mock_service

    No Docling model loading occurs — suitable for fast unit tests.
    """

    @asynccontextmanager
    async def _test_lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.start_time = datetime.now(timezone.utc)
        router = build_router(mock_service)
        app.include_router(router)
        yield

    test_app = FastAPI(lifespan=_test_lifespan)

    with TestClient(test_app) as c:
        yield c
