"""Domain error code to HTTP status mapping for SelectionMaid.

Maps the machine-readable error codes from ``selection_maid.errors`` to the
appropriate HTTP status codes for the ``POST /ingest`` endpoint (D-82).

Upload validation errors that never become ``SelectionMaidError`` instances
(size, magic bytes) are also mapped here so that ``_error_response()`` in
``router.py`` is the single place to convert any error code to a status code.

Mapping decisions (Claude's discretion — 06-CONTEXT.md §Claude's Discretion):
    EXT-001  ExtractionError          500  Generic extraction failure
    EXT-002  UnsupportedFormatError   415  Unsupported MIME type → Unsupported Media Type
    EXT-003  ExtractionTimeoutError   504  Timed out → Gateway Timeout
    FILT-001 FilterError              500  Internal filter failure
    CHUNK-001 ChunkingError           500  Internal chunking failure
    ENRICH-001 EnrichmentError        500  Internal enrichment failure
    UPLOAD-001 (file too large)       413  Content Too Large
    UPLOAD-002 (magic bytes mismatch) 422  Unprocessable Entity
"""
from __future__ import annotations

#: Mapping from domain error codes to HTTP status codes (D-82).
ERROR_CODE_TO_HTTP: dict[str, int] = {
    # Extraction adapter errors
    "EXT-001": 500,  # ExtractionError — generic extraction failure
    "EXT-002": 415,  # UnsupportedFormatError — unsupported MIME type
    "EXT-003": 504,  # ExtractionTimeoutError — extraction timed out
    # Content processing errors
    "FILT-001": 500,  # FilterError — heuristic filter failure
    "CHUNK-001": 500,  # ChunkingError — document chunking failure
    "ENRICH-001": 500,  # EnrichmentError — metadata enrichment failure
    # Upload validation errors (raised before domain processing)
    "UPLOAD-001": 413,  # File too large (Content-Length or real size)
    "UPLOAD-002": 422,  # Magic bytes mismatch (declared MIME ≠ detected MIME)
}

#: Fallback HTTP status for unknown or unmapped error codes.
_DEFAULT_HTTP_STATUS: int = 500


def get_http_status(error_code: str) -> int:
    """Return the HTTP status code for a given domain error code.

    Falls back to 500 (Internal Server Error) for any code not in
    ``ERROR_CODE_TO_HTTP``.

    Args:
        error_code: Machine-readable code from a ``SelectionMaidError``
            subclass or an upload validation constant (UPLOAD-001, UPLOAD-002).

    Returns:
        HTTP status code as an integer.
    """
    return ERROR_CODE_TO_HTTP.get(error_code, _DEFAULT_HTTP_STATUS)
