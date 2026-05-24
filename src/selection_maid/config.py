"""Central configuration management for SelectionMaid.

Reads config.toml from the project root using tomllib (stdlib, Python 3.11+).
Falls back to hardcoded defaults if the file is missing or keys are absent.
No startup failure on missing config — per decision D-38.

Usage:
    from selection_maid.config import get_config

    cfg = get_config()
    threshold = cfg.filter.min_repeat  # int, default 3
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


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
class GlobalConfig:
    """Top-level configuration container.

    Holds per-adapter configuration sections. Future phases (chunker, enricher)
    will add their own nested dataclasses here.

    Attributes:
        filter: Filter adapter thresholds.
    """

    filter: FilterConfig = field(default_factory=FilterConfig)


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
        min_repeat=int(filter_raw.get("min_repeat", FilterConfig.min_repeat)),  # type: ignore[arg-type]
        max_line_len=int(filter_raw.get("max_line_len", FilterConfig.max_line_len)),  # type: ignore[arg-type]
    )

    return GlobalConfig(filter=filter_cfg)
