"""FastAPI application factory for SelectionMaid.

Creates and wires the FastAPI application with all port adapters.

Decision references:
- D-83: app lives here as create_app() -> FastAPI; module-level app = create_app()
         for uvicorn; separated from router.py for testability
- D-84: DocumentConverter singleton created in @asynccontextmanager lifespan;
        lifespan wires all adapters + ExtractionService, then includes router
        (NOT @app.on_event which is deprecated since FastAPI 0.95.0)
- D-85: build_router(service, config) closure pattern — router included after lifespan wiring
- D-86: app.state.start_time = datetime.now(UTC) set in lifespan for /health uptime

Uvicorn entry point:
    uvicorn selection_maid.adapters.http.app:app
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from selection_maid.adapters.chunker.markdown import build_markdown_chunker
from selection_maid.adapters.enricher.default import build_metadata_enricher
from selection_maid.adapters.extractor.docling import build_docling_adapter
from selection_maid.adapters.filter.heuristic import build_heuristic_filter
from selection_maid.adapters.http.router import build_router
from selection_maid.config import get_config
from selection_maid.service import ExtractionService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan context manager (D-84).

    Startup duties:
    - Record start_time for /health uptime calculation (D-86)
    - Build DocumentConverter singleton (expensive — model loading)
    - Wire all port adapters and ExtractionService
    - Build router via closure and include it in the app

    Shutdown duties:
    - No explicit cleanup needed for v1 (DocumentConverter has no teardown)
    """
    # D-86: record start time for uptime calculation in GET /health
    app.state.start_time = datetime.now(timezone.utc)

    logger.info("SelectionMaid starting up — loading DocumentConverter...")

    # Import Docling here (not at module top level) to avoid triggering
    # torch model loading on import of selection_maid.adapters.http.app.
    # This matches the TYPE_CHECKING guard pattern in adapters/extractor/docling.py.
    from docling.document_converter import DocumentConverter  # noqa: PLC0415

    converter = DocumentConverter()

    # Load configuration (falls back to defaults if config.toml missing — D-38)
    config = get_config()

    # Wire all port adapters (D-84)
    extractor = build_docling_adapter(converter)
    filter_ = build_heuristic_filter(config.filter)
    chunker = build_markdown_chunker(config.chunker)
    enricher = build_metadata_enricher(config.enricher)

    # Assemble ExtractionService with injected ports
    service = ExtractionService(
        extractor=extractor,
        filter_=filter_,
        chunker=chunker,
        enricher=enricher,
    )

    # Build router with closure capturing service and config (D-85) and include in app
    router = build_router(service, config)
    app.include_router(router)

    logger.info("SelectionMaid ready.")

    yield

    # Shutdown — no teardown needed for v1
    logger.info("SelectionMaid shutting down.")


def create_app() -> FastAPI:
    """Create and return a configured FastAPI application instance (D-83).

    The application is wired via the lifespan context manager so that all
    expensive initialisation (DocumentConverter, model loading) happens at
    startup, not at module import time.

    Returns:
        A FastAPI application ready to be served by uvicorn.
    """
    app = FastAPI(
        title="SelectionMaid",
        description=(
            "Document curation and normalisation service. "
            "Accepts raw files (PDF, DOCX, HTML) and returns structured "
            "Markdown chunks ready for vector database ingestion."
        ),
        version="0.1.0",
        lifespan=_lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["POST", "OPTIONS"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    return app


# Module-level instance for uvicorn: selection_maid.adapters.http.app:app (D-83)
app = create_app()
