"""Tests for DoclingAdapter.

Test class organisation:
  TestDoclingAdapterUnit        -- unit tests with mock converter (always run)
  TestDoclingAdapterIntegration -- integration tests with real Docling (skip if
                                   fixtures unavailable per D-27)

Plans that populate these classes:
  02-02 (extract() implementation) -> both unit and integration tests
  02-03 (EXT-04/05/06/07 format fidelity) -> integration tests
  02-04 (timeout mechanism) -> unit tests
  02-05 (error wrapping) -> unit + integration tests
"""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import Mock

import pytest

from selection_maid.adapters.extractor.docling import DoclingAdapter
from selection_maid.domain.models import RawDocument, RawInput
from selection_maid.errors import (
    ExtractionError,
    ExtractionTimeoutError,
    UnsupportedFormatError,
)


class TestDoclingAdapterUnit:
    """Unit tests -- mock converter, no real Docling, always run."""

    def test_unsupported_format_raises(self) -> None:
        """UnsupportedFormatError raised for unsupported MIME types (D-30)."""
        mock_converter = Mock()
        adapter = DoclingAdapter(converter=mock_converter, timeout_seconds=5)
        raw_input = RawInput(
            path=Path("/tmp/x.zip"),
            filename="x.zip",
            mime_type="application/zip",
        )
        with pytest.raises(UnsupportedFormatError):
            adapter.extract(raw_input)

    def test_extraction_error_wraps_converter_exception(self) -> None:
        """RuntimeError from converter.convert() is wrapped as ExtractionError."""
        mock_converter = Mock()
        mock_converter.convert.side_effect = RuntimeError("docling internal error")
        adapter = DoclingAdapter(converter=mock_converter, timeout_seconds=5)
        raw_input = RawInput(
            path=Path("/tmp/test.pdf"),
            filename="test.pdf",
            mime_type="application/pdf",
        )
        with pytest.raises(ExtractionError):
            adapter.extract(raw_input)

    def test_raw_document_filename_matches_input(self) -> None:
        """filename in returned RawDocument equals the filename in RawInput."""
        mock_converter = Mock()
        mock_result = Mock()
        mock_result.document.export_to_markdown.return_value = "# Hello"
        mock_result.document.pages = [1]
        mock_converter.convert.return_value = mock_result

        adapter = DoclingAdapter(converter=mock_converter, timeout_seconds=5)
        raw_input = RawInput(
            path=Path("/tmp/t.pdf"),
            filename="myfile.pdf",
            mime_type="application/pdf",
        )
        result = adapter.extract(raw_input)

        assert isinstance(result, RawDocument)
        assert result.filename == "myfile.pdf"
        assert result.content == "# Hello"
        assert result.format == "pdf"
        assert result.page_count == 1

    def test_timeout_raises_extraction_timeout_error(self) -> None:
        """ExtractionTimeoutError raised when converter.convert() exceeds timeout.

        Strategy (D-25): use timeout_seconds=1 and a convert() that sleeps 2s
        so the ThreadPoolExecutor future.result(timeout=1) fires TimeoutError,
        which DoclingAdapter translates to ExtractionTimeoutError.
        Wall time is ~2s (1s timeout + ~1s executor shutdown(wait=True)).
        """
        mock_converter = Mock()
        mock_converter.convert.side_effect = lambda path: time.sleep(2)

        adapter = DoclingAdapter(converter=mock_converter, timeout_seconds=1)
        raw_input = RawInput(
            path=Path("/tmp/test.pdf"),
            filename="test.pdf",
            mime_type="application/pdf",
        )
        with pytest.raises(ExtractionTimeoutError):
            adapter.extract(raw_input)

    def test_domain_error_propagates_unchanged(self) -> None:
        """ExtractionError raised inside convert() passes through unwrapped.

        The SelectionMaidError branch in extract() re-raises unchanged. Asserting
        the message value confirms no double-wrapping occurred.
        """
        mock_converter = Mock()
        mock_converter.convert.side_effect = ExtractionError("already a domain error")

        adapter = DoclingAdapter(converter=mock_converter, timeout_seconds=5)
        raw_input = RawInput(
            path=Path("/tmp/test.pdf"),
            filename="test.pdf",
            mime_type="application/pdf",
        )
        with pytest.raises(ExtractionError) as exc_info:
            adapter.extract(raw_input)
        assert exc_info.value.message == "already a domain error"


class TestDoclingAdapterIntegration:
    """Integration tests -- real Docling converter, real fixture files.

    Each test must check if its fixture is None and call pytest.skip() if so
    (D-27: graceful skip on connectivity failure, no CI block).
    """

    def test_pdf_extraction(
        self, real_converter: object, real_pdf_path: Path | None
    ) -> None:
        """PDF fixture converts to RawDocument with non-empty Markdown (EXT-01)."""
        if real_pdf_path is None:
            pytest.skip("Integration fixtures unavailable — skipping")

        adapter = DoclingAdapter(converter=real_converter)
        raw_input = RawInput(
            path=real_pdf_path,
            filename="sample.pdf",
            mime_type="application/pdf",
        )
        result = adapter.extract(raw_input)

        assert isinstance(result, RawDocument)
        assert result.content  # non-empty Markdown
        assert result.format == "pdf"
        assert result.page_count >= 1

    def test_docx_extraction(
        self, real_converter: object, real_docx_path: Path | None
    ) -> None:
        """DOCX fixture converts to RawDocument with non-empty Markdown (EXT-02)."""
        if real_docx_path is None:
            pytest.skip("Integration fixtures unavailable — skipping")

        adapter = DoclingAdapter(converter=real_converter)
        raw_input = RawInput(
            path=real_docx_path,
            filename="sample.docx",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        result = adapter.extract(raw_input)

        assert isinstance(result, RawDocument)
        assert result.content  # non-empty Markdown
        assert result.format == "docx"
        # A3 assumption: use >= 0 not >= 1 — WordFormatOption+SimplePipeline
        # may return 0 pages for some DOCX files; D-29 only mandates 0 for HTML.
        assert result.page_count >= 0

    def test_html_extraction(
        self, real_converter: object, real_html_path: Path | None
    ) -> None:
        """HTML fixture converts to RawDocument with page_count==0 (EXT-03, D-29)."""
        if real_html_path is None:
            pytest.skip("Integration fixtures unavailable — skipping")

        adapter = DoclingAdapter(converter=real_converter)
        raw_input = RawInput(
            path=real_html_path,
            filename="sample.html",
            mime_type="text/html",
        )
        result = adapter.extract(raw_input)

        assert isinstance(result, RawDocument)
        assert result.content  # non-empty Markdown
        assert result.format == "html"
        assert result.page_count == 0  # D-29: HTML has no page concept
