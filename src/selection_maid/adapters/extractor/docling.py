"""DoclingAdapter -- concrete ExtractorPort implementation using Docling.

This module is the sole location in the project where Docling types may exist at
runtime. No docling.* import appears at module top level; the TYPE_CHECKING guard
ensures that importing selection_maid (or any sub-package) does not trigger
Docling/torch model loading (Pitfall 3 -- see RESEARCH.md).

Decision references:
  D-21: Constructor injection -- adapter receives pre-built DocumentConverter.
  D-22: SUPPORTED_MIME_TYPES constant -- hardcoded, not configurable via constructor.
  D-23: Factory function build_docling_adapter -- consistent with build_router pattern.
  D-24: Timeout via ThreadPoolExecutor -- lingering thread accepted for v1.
  D-30: UnsupportedFormatError raised before Docling call.
"""

from __future__ import annotations

import concurrent.futures  # noqa: F401  (used in Plan 02-02 extract() implementation)
from pathlib import Path  # noqa: F401  (used in Plan 02-02 extract() implementation)
from typing import TYPE_CHECKING

from selection_maid.domain.models import RawDocument, RawInput
from selection_maid.errors import (
    ExtractionError,  # noqa: F401  (used in Plan 02-02 extract() implementation)
    ExtractionTimeoutError,  # noqa: F401  (used in Plan 02-02 extract() implementation)
    SelectionMaidError,  # noqa: F401  (used in Plan 02-02 extract() implementation)
    UnsupportedFormatError,
)

if TYPE_CHECKING:
    # Keep Docling types out of the runtime import graph for non-extractor modules.
    # This import is used for type annotations only; the real import happens inside
    # the functions/modules that physically construct DocumentConverter (Phase 6
    # lifespan, integration test conftest).
    from docling.document_converter import DocumentConverter

# D-22: Supported MIME types hardcoded as a module-level frozenset constant.
# v2 formats (PPTX, XLSX) will be added here when EXT-V2-02/EXT-V2-03 land.
SUPPORTED_MIME_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/html",
    }
)

_MIME_TO_FORMAT: dict[str, str] = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/html": "html",
}


class DoclingAdapter:
    """Concrete ExtractorPort implementation backed by Docling DocumentConverter.

    The adapter is the only module in the project that may import docling.* at
    runtime. All Docling types stop at this boundary -- the return value is always
    a plain RawDocument (a domain type with no Docling dependency).

    Constructor injection (D-21): the caller is responsible for building and
    configuring the DocumentConverter singleton (Phase 6 FastAPI lifespan). Tests
    pass a real instance (integration) or a mock (unit).
    """

    def __init__(
        self,
        converter: DocumentConverter,
        timeout_seconds: int = 120,
    ) -> None:
        """Initialise the adapter with an already-constructed DocumentConverter.

        Args:
            converter: Pre-built Docling DocumentConverter. Must be configured
                with the target formats (PDF, DOCX, HTML) before being passed.
            timeout_seconds: Maximum seconds allowed for a single conversion.
                Defaults to 120. Tests may use a smaller value (D-25).
        """
        self._converter = converter
        self._timeout_seconds = timeout_seconds

    def extract(self, document: RawInput) -> RawDocument:
        """Extract content from a document file and return structured Markdown.

        Args:
            document: RawInput identifying the file to process. The path must
                point to a readable file on the local filesystem.

        Returns:
            RawDocument with Markdown content, original filename, page count
            (0 for HTML per D-29), and format string ("pdf"/"docx"/"html").

        Raises:
            UnsupportedFormatError: document.mime_type not in SUPPORTED_MIME_TYPES.
                Raised before any Docling call (D-30).
            ExtractionTimeoutError: conversion exceeded timeout_seconds (D-24).
            ExtractionError: Docling conversion failed for any other reason.
        """
        # D-30: validate MIME type before calling Docling
        if document.mime_type not in SUPPORTED_MIME_TYPES:
            raise UnsupportedFormatError(
                f"Unsupported format: {document.mime_type}",
                format=document.mime_type,
            )
        # Stub: full implementation (threading + conversion + mapping) in Plan 02-02.
        raise NotImplementedError("extract() not yet implemented")


def build_docling_adapter(
    converter: DocumentConverter,
    timeout_seconds: int = 120,
) -> DoclingAdapter:
    """Factory function for DoclingAdapter (D-23).

    Consistent with the build_router(service) pattern that Phase 6 will define.
    Callers (Phase 6 lifespan, integration tests) use this factory rather than
    constructing DoclingAdapter directly.

    Args:
        converter: Pre-built Docling DocumentConverter.
        timeout_seconds: Timeout for each extraction call. Defaults to 120.

    Returns:
        A fully configured DoclingAdapter instance.
    """
    return DoclingAdapter(converter=converter, timeout_seconds=timeout_seconds)
