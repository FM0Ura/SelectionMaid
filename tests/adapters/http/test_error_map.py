"""Tests for HTTP error-code mapping."""
from __future__ import annotations

import pytest

from selection_maid.adapters.http.error_map import ERROR_CODE_TO_HTTP, get_http_status


@pytest.mark.parametrize(
    ("error_code", "expected_status"),
    [
        ("EXT-001", 500),
        ("EXT-002", 415),
        ("EXT-003", 504),
        ("FILT-001", 500),
        ("CHUNK-001", 500),
        ("ENRICH-001", 500),
        ("UPLOAD-001", 413),
        ("UPLOAD-002", 422),
    ],
)
def test_error_code_to_http_status_mapping(
    error_code: str, expected_status: int
) -> None:
    """All domain and upload validation errors map to explicit HTTP statuses."""
    assert ERROR_CODE_TO_HTTP[error_code] == expected_status
    assert get_http_status(error_code) == expected_status


def test_unknown_error_code_defaults_to_500() -> None:
    """Unknown error codes fail closed as internal server errors."""
    assert get_http_status("UNKNOWN-999") == 500
