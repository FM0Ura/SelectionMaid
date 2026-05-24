"""Session-scoped fixtures for DoclingAdapter integration tests.

Fixtures in this file:
  real_converter  -- single DocumentConverter for the entire test session (D-26)
  real_pdf_path   -- path to a downloaded sample PDF (None if unavailable)
  real_docx_path  -- path to a downloaded sample DOCX (None if unavailable)
  real_html_path  -- path to a downloaded sample HTML (None if unavailable)

Download behaviour (D-27):
  Files are downloaded from public URLs on first run and cached in tests/fixtures/.
  If a download fails (no internet, URL unavailable), the fixture returns None and
  integration tests that depend on it should call pytest.skip().

Import note:
  All `from docling.*` imports live inside fixture bodies, not at module top level.
  This mirrors the TYPE_CHECKING guard in docling.py — conftest collection does not
  trigger torch model loading (Pitfall 3 in RESEARCH.md).
"""

from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Any

import pytest

# tests/fixtures/ is .gitignored; populated on first integration test run.
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"

FIXTURE_URLS: dict[str, str] = {
    "sample.pdf": "https://www.orimi.com/pdf-test.pdf",
    "sample.docx": "https://calibre-ebook.com/downloads/demos/demo.docx",
    "sample.html": "https://www.w3.org/TR/WCAG20/",
}


def _ensure_fixture(filename: str) -> Path | None:
    """Return the cached fixture path, downloading it if necessary.

    Returns None (instead of raising) if the download fails so that tests can
    use pytest.skip() rather than erroring out on connectivity issues (D-27).
    """
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    target = FIXTURES_DIR / filename
    if target.exists():
        return target
    url = FIXTURE_URLS[filename]
    try:
        urllib.request.urlretrieve(url, target)
        return target
    except Exception:
        return None


@pytest.fixture(scope="session")
def real_converter() -> Any:
    """Single DocumentConverter shared across all integration tests (D-26).

    Constructed once per pytest session — expensive AI model initialisation
    only happens once regardless of how many integration tests run.

    Docling imports are inside this fixture body so that conftest collection
    does not trigger torch loading when only unit tests are executed.

    Return type is Any because DocumentConverter is a Docling type that must
    not appear in non-adapter module-level annotations (T-02-02 mitigate).
    """
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import (
        DocumentConverter,
        PdfFormatOption,
        WordFormatOption,
    )
    from docling.pipeline.simple_pipeline import SimplePipeline
    from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

    pdf_options = PdfPipelineOptions(
        do_ocr=False,  # digital text PDF — no OCR needed
        do_table_structure=True,  # GFM table output (EXT-05)
    )

    return DocumentConverter(
        allowed_formats=[
            InputFormat.PDF,
            InputFormat.DOCX,
            InputFormat.HTML,
        ],
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=StandardPdfPipeline,
                pipeline_options=pdf_options,
            ),
            InputFormat.DOCX: WordFormatOption(
                pipeline_cls=SimplePipeline,
            ),
            # HTML: no FormatOption needed — default SimplePipeline handles it
        },
    )


@pytest.fixture(scope="session")
def real_pdf_path() -> Path | None:
    """Return the path to a real PDF fixture file, or None if unavailable."""
    return _ensure_fixture("sample.pdf")


@pytest.fixture(scope="session")
def real_docx_path() -> Path | None:
    """Return the path to a real DOCX fixture file, or None if unavailable."""
    return _ensure_fixture("sample.docx")


@pytest.fixture(scope="session")
def real_html_path() -> Path | None:
    """Return the path to a real HTML fixture file, or None if unavailable."""
    return _ensure_fixture("sample.html")
