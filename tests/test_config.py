"""Tests for central configuration loading."""
from __future__ import annotations

from pathlib import Path

from selection_maid.config import get_config


def test_http_config_defaults_when_config_file_missing(tmp_path: Path) -> None:
    """HTTP upload validation uses safe defaults when config.toml is absent."""
    cfg = get_config(tmp_path / "missing.toml")

    assert cfg.http.max_file_bytes == 52_428_800
    assert cfg.http.allowed_mime_types == [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/html",
    ]


def test_http_config_reads_toml_section(tmp_path: Path) -> None:
    """[http] TOML values override the upload validation defaults."""
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[http]
max_file_bytes = 1024
allowed_mime_types = ["application/pdf"]
""".strip(),
        encoding="utf-8",
    )

    cfg = get_config(config_path)

    assert cfg.http.max_file_bytes == 1024
    assert cfg.http.allowed_mime_types == ["application/pdf"]


def test_http_config_invalid_toml_values_fall_back_to_defaults(
    tmp_path: Path,
) -> None:
    """Invalid [http] value types do not leak unsafe config into the app."""
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[http]
max_file_bytes = "large"
allowed_mime_types = ["application/pdf", 123]
""".strip(),
        encoding="utf-8",
    )

    cfg = get_config(config_path)

    assert cfg.http.max_file_bytes == 52_428_800
    assert cfg.http.allowed_mime_types == [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/html",
    ]
