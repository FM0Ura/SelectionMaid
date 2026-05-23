"""Domain error taxonomy for SelectionMaid.

All domain errors inherit from SelectionMaidError. The HTTP adapter (Phase 6)
maps error codes to HTTP status via ERROR_CODE_TO_HTTP — no HTTP coupling here.
"""
from __future__ import annotations


class SelectionMaidError(Exception):
    """Base exception for all SelectionMaid domain errors.

    Attributes:
        code: Machine-readable error code (fixed class attribute per subclass).
        message: Human-readable error description.
        cause: Original exception that triggered this domain error, if any.
    """

    code: str = ""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        self.message = message
        self.cause = cause
        super().__init__(message)


class ExtractionError(SelectionMaidError):
    """Raised when document extraction fails.

    Covers generic extractor failures (corrupt file, unsupported pipeline, etc.).
    """

    code = "EXT-001"


class UnsupportedFormatError(SelectionMaidError):
    """Raised when the input document format is not supported by the extractor.

    Attributes:
        format: The unsupported MIME type or file extension that was rejected.
    """

    code = "EXT-002"

    def __init__(
        self, message: str, format: str, cause: Exception | None = None
    ) -> None:
        self.format = format
        super().__init__(message, cause)


class ExtractionTimeoutError(SelectionMaidError):
    """Raised when extraction exceeds the configured time limit.

    Defined in Phase 1; raised by DoclingAdapter in Phase 2.
    """

    code = "EXT-003"


class FilterError(SelectionMaidError):
    """Raised when the filter port fails to clean the raw document."""

    code = "FILT-001"


class ChunkingError(SelectionMaidError):
    """Raised when the chunker port fails to segment document content."""

    code = "CHUNK-001"


class EnrichmentError(SelectionMaidError):
    """Raised when the metadata enricher port fails."""

    code = "ENRICH-001"
