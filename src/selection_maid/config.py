"""Central configuration management for SelectionMaid.

Reads config.toml from the project root using tomllib (stdlib, Python 3.11+).
Falls back to hardcoded defaults if the file is missing or keys are absent.
No startup failure on missing config — per decision D-38.

Usage:
    from selection_maid.config import get_config

    cfg = get_config()
    threshold = cfg.filter.min_repeat  # int, default 3
    max_bytes = cfg.http.max_file_bytes  # int, default 52_428_800 (50MB)
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


def _as_int(value: object, default: int) -> int:
    """Safely cast a TOML value to int, falling back to default.

    TOML integers are represented as Python ``int`` objects by tomllib.
    This helper avoids the mypy strict ``call-overload`` error that arises
    from passing ``object`` (the return type of ``dict[str, object].get()``)
    directly to ``int()``.

    Args:
        value: Raw value from the TOML dict (type is ``object``).
        default: Fallback value when ``value`` is not a valid ``int``.

    Returns:
        ``int(value)`` if ``value`` is an instance of ``int``, else ``default``.
    """
    if isinstance(value, int):
        return value
    return default


def _as_list_str(value: object, default: list[str]) -> list[str]:
    """Safely cast a TOML value to list[str], falling back to default.

    TOML arrays of strings are represented as Python ``list[str]`` by tomllib.
    This helper ensures type safety for mypy strict mode when the raw dict
    value has type ``object``.

    Args:
        value: Raw value from the TOML dict (type is ``object``).
        default: Fallback value when ``value`` is not a valid ``list[str]``.

    Returns:
        The value cast to ``list[str]`` if it is a list of strings, else
        ``default``.
    """
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)  # narrow type for mypy
    return default


@dataclass
class FilterConfig:
    """Configuration for the HeuristicFilter adapter (D-39, D-40).

    Attributes:
        min_repeat: Minimum number of times a short line must appear in the
            document to be treated as a header/footer candidate (default 3).
        max_line_len: Maximum character length for a line to be considered a
            header/footer candidate (default 80).
    """

    min_repeat: int = 3
    max_line_len: int = 80


@dataclass
class ChunkerConfig:
    """Configuration for the MarkdownChunker adapter (D-51, D-57, D-58).

    Attributes:
        max_tokens: Maximum token budget per chunk for the fixed-size fallback
            strategy (D-51). Also used as the section-subdivision limit for
            heading-based chunking (D-48). Default 512.
    """

    max_tokens: int = 512


@dataclass
class EnricherConfig:
    """Configuration for the MetadataEnricher adapter (D-72, D-73).

    Empty for v1 — all enricher parameters (language confidence threshold,
    doc_type keywords) are module-level constants. This dataclass is
    defined here to establish the config pattern for future extensibility
    (e.g., language_confidence_threshold in v2).
    """


#: Default allowed MIME types for the HTTP upload endpoint (D-80, D-90).
_DEFAULT_ALLOWED_MIME_TYPES: list[str] = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/html",
]


@dataclass
class HttpConfig:
    """Configuration for the FastAPI HTTP adapter (D-89, D-90).

    Controls file upload validation at the HTTP boundary.

    Attributes:
        max_file_bytes: Maximum accepted file size in bytes.  Requests whose
            ``Content-Length`` header or actual body exceeds this limit are
            rejected with HTTP 413.  Defaults to 52_428_800 (50 MB).
        allowed_mime_types: MIME types accepted by ``POST /ingest``.  Requests
            declaring a MIME type outside this list are rejected with HTTP 415.
            Defaults to PDF, DOCX, and HTML only (v1 scope per D-80).
    """

    max_file_bytes: int = 52_428_800  # 50 MB (D-79, D-90)
    allowed_mime_types: list[str] = field(
        default_factory=lambda: list(_DEFAULT_ALLOWED_MIME_TYPES)
    )


@dataclass
class GlobalConfig:
    """Top-level configuration container.

    Holds per-adapter configuration sections.

    Attributes:
        filter: Filter adapter thresholds.
        chunker: Chunker adapter parameters.
        enricher: Enricher adapter parameters.
        http: HTTP adapter upload validation parameters.
    """

    filter: FilterConfig = field(default_factory=FilterConfig)
    chunker: ChunkerConfig = field(default_factory=ChunkerConfig)
    enricher: EnricherConfig = field(default_factory=EnricherConfig)
    http: HttpConfig = field(default_factory=HttpConfig)


def get_config(config_path: Path | None = None) -> GlobalConfig:
    """Read config.toml and return a GlobalConfig with resolved values.

    Attempts to open ``config_path`` (or ``config.toml`` in the current working
    directory if not specified) in binary mode and parse it as TOML.  If the
    file is missing, unreadable, or lacks expected keys, hardcoded defaults
    are used — no exception is raised (D-38).

    Args:
        config_path: Optional explicit path to the TOML file.  Defaults to
            ``config.toml`` relative to the current working directory.

    Returns:
        A :class:`GlobalConfig` instance with values from the file or defaults.
    """
    resolved_path = config_path if config_path is not None else Path("config.toml")

    raw: dict[str, object] = {}
    try:
        with open(resolved_path, "rb") as fh:
            raw = tomllib.load(fh)
    except FileNotFoundError:
        pass  # No config file — use defaults (D-38)
    except OSError:
        pass  # Unreadable file — use defaults

    filter_raw: dict[str, object] = {}
    if isinstance(raw.get("filter"), dict):
        filter_raw = raw["filter"]  # type: ignore[assignment]

    filter_cfg = FilterConfig(
        min_repeat=_as_int(filter_raw.get("min_repeat"), FilterConfig.min_repeat),
        max_line_len=_as_int(filter_raw.get("max_line_len"), FilterConfig.max_line_len),
    )

    chunker_raw: dict[str, object] = {}
    if isinstance(raw.get("chunker"), dict):
        chunker_raw = raw["chunker"]  # type: ignore[assignment]

    chunker_cfg = ChunkerConfig(
        max_tokens=_as_int(chunker_raw.get("max_tokens"), ChunkerConfig.max_tokens),
    )

    # EnricherConfig has no configurable fields in v1; read [enricher] section
    # to allow future extensions without changing the call site.
    enricher_cfg = EnricherConfig()

    http_raw: dict[str, object] = {}
    if isinstance(raw.get("http"), dict):
        http_raw = raw["http"]  # type: ignore[assignment]

    http_cfg = HttpConfig(
        max_file_bytes=_as_int(
            http_raw.get("max_file_bytes"), HttpConfig.max_file_bytes
        ),
        allowed_mime_types=_as_list_str(
            http_raw.get("allowed_mime_types"),
            list(_DEFAULT_ALLOWED_MIME_TYPES),
        ),
    )

    return GlobalConfig(
        filter=filter_cfg,
        chunker=chunker_cfg,
        enricher=enricher_cfg,
        http=http_cfg,
    )
