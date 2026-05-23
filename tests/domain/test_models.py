"""Tests for domain frozen dataclasses — TDD RED phase."""
from __future__ import annotations

import dataclasses
from datetime import datetime
from pathlib import Path

import pytest

from selection_maid.domain.models import DocumentChunk, DocumentMetadata


class TestRawInput:
    """RawInput frozen dataclass tests."""

    def test_raw_input_creation(self) -> None:
        from selection_maid.domain.models import RawInput

        raw = RawInput(
            path=Path("/tmp/doc.pdf"),
            filename="doc.pdf",
            mime_type="application/pdf",
        )
        assert raw.path == Path("/tmp/doc.pdf")
        assert raw.filename == "doc.pdf"
        assert raw.mime_type == "application/pdf"

    def test_raw_input_is_frozen(self) -> None:
        from selection_maid.domain.models import RawInput

        raw = RawInput(
            path=Path("/tmp/doc.pdf"),
            filename="doc.pdf",
            mime_type="application/pdf",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            raw.filename = "other.pdf"  # type: ignore[misc]

    def test_raw_input_path_mutation_raises(self) -> None:
        from selection_maid.domain.models import RawInput

        raw = RawInput(
            path=Path("/tmp/doc.pdf"),
            filename="doc.pdf",
            mime_type="application/pdf",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            raw.path = Path("/tmp/other.pdf")  # type: ignore[misc]


class TestRawDocument:
    """RawDocument frozen dataclass tests."""

    def test_raw_document_creation(self) -> None:
        from selection_maid.domain.models import RawDocument

        doc = RawDocument(
            content="# Hello\n\nContent here.",
            filename="doc.pdf",
            page_count=5,
            format="pdf",
        )
        assert doc.content == "# Hello\n\nContent here."
        assert doc.page_count == 5
        assert doc.format == "pdf"

    def test_raw_document_page_count_zero_valid(self) -> None:
        from selection_maid.domain.models import RawDocument

        doc = RawDocument(
            content="",
            filename="unknown.pdf",
            page_count=0,
            format="pdf",
        )
        assert doc.page_count == 0

    def test_raw_document_is_frozen(self) -> None:
        from selection_maid.domain.models import RawDocument

        doc = RawDocument(
            content="content",
            filename="doc.pdf",
            page_count=1,
            format="pdf",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            doc.content = "changed"  # type: ignore[misc]


class TestDocumentChunk:
    """DocumentChunk frozen dataclass tests — CHUNK-03 field compliance."""

    def test_document_chunk_has_all_eight_fields(self) -> None:
        from selection_maid.domain.models import DocumentChunk

        chunk = DocumentChunk(
            chunk_id="chunk-001",
            content="This is chunk content.",
            page_start=1,
            page_end=2,
            section_title="Introduction",
            chunk_index=0,
            total_chunks=5,
            word_count=4,
        )
        assert chunk.chunk_id == "chunk-001"
        assert chunk.content == "This is chunk content."
        assert chunk.page_start == 1
        assert chunk.page_end == 2
        assert chunk.section_title == "Introduction"
        assert chunk.chunk_index == 0
        assert chunk.total_chunks == 5
        assert chunk.word_count == 4

    def test_document_chunk_field_count_is_exactly_eight(self) -> None:
        from selection_maid.domain.models import DocumentChunk

        fields = dataclasses.fields(DocumentChunk)
        assert len(fields) == 8, f"Expected 8 fields per CHUNK-03, got {len(fields)}"

    def test_document_chunk_is_frozen(self) -> None:
        from selection_maid.domain.models import DocumentChunk

        chunk = DocumentChunk(
            chunk_id="c1",
            content="content",
            page_start=1,
            page_end=1,
            section_title="Sec",
            chunk_index=0,
            total_chunks=1,
            word_count=1,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            chunk.content = "changed"  # type: ignore[misc]


class TestDocumentMetadata:
    """DocumentMetadata frozen dataclass tests — META-01 field compliance."""

    def test_document_metadata_has_all_seven_fields(self) -> None:
        from selection_maid.domain.models import DocumentMetadata

        meta = DocumentMetadata(
            title="My Document",
            author="John Doe",
            language="pt",
            document_type="report",
            page_count=10,
            chunk_count=20,
            ingestion_date=datetime(2026, 5, 23, 12, 0, 0),
        )
        assert meta.title == "My Document"
        assert meta.author == "John Doe"
        assert meta.language == "pt"
        assert meta.document_type == "report"
        assert meta.page_count == 10
        assert meta.chunk_count == 20
        assert isinstance(meta.ingestion_date, datetime)

    def test_document_metadata_field_count_is_exactly_seven(self) -> None:
        from selection_maid.domain.models import DocumentMetadata

        fields = dataclasses.fields(DocumentMetadata)
        assert len(fields) == 7, f"Expected 7 fields per META-01, got {len(fields)}"

    def test_document_metadata_is_frozen(self) -> None:
        from selection_maid.domain.models import DocumentMetadata

        meta = DocumentMetadata(
            title="Title",
            author="Author",
            language="en",
            document_type="report",
            page_count=1,
            chunk_count=1,
            ingestion_date=datetime(2026, 1, 1),
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            meta.title = "Changed"  # type: ignore[misc]


class TestExtractionResult:
    """ExtractionResult frozen dataclass tests."""

    def _make_chunk(self, idx: int) -> DocumentChunk:
        return DocumentChunk(
            chunk_id=f"chunk-{idx:03d}",
            content=f"Chunk {idx} content.",
            page_start=idx,
            page_end=idx,
            section_title="Section",
            chunk_index=idx,
            total_chunks=3,
            word_count=3,
        )

    def _make_metadata(self) -> DocumentMetadata:
        return DocumentMetadata(
            title="Title",
            author="Author",
            language="en",
            document_type="report",
            page_count=3,
            chunk_count=3,
            ingestion_date=datetime(2026, 5, 23),
        )

    def test_extraction_result_chunks_is_tuple(self) -> None:
        from selection_maid.domain.models import ExtractionResult

        chunks = tuple(self._make_chunk(i) for i in range(3))
        meta = self._make_metadata()
        result = ExtractionResult(metadata=meta, chunks=chunks)
        assert isinstance(result.chunks, tuple)
        assert len(result.chunks) == 3

    def test_extraction_result_is_frozen(self) -> None:
        from selection_maid.domain.models import ExtractionResult

        chunks = tuple(self._make_chunk(i) for i in range(2))
        meta = self._make_metadata()
        result = ExtractionResult(metadata=meta, chunks=chunks)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.metadata = meta  # type: ignore[misc]

    def test_extraction_result_chunks_immutable(self) -> None:
        """Reassignment of result.chunks raises FrozenInstanceError."""
        from selection_maid.domain.models import ExtractionResult

        chunks = tuple(self._make_chunk(i) for i in range(2))
        meta = self._make_metadata()
        result = ExtractionResult(metadata=meta, chunks=chunks)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.chunks = ()  # type: ignore[misc]


class TestNoThirdPartyImports:
    """Verify models.py has zero third-party imports."""

    def test_models_module_imports_only_stdlib(self) -> None:
        """Import models and check that only stdlib modules are used."""
        import importlib
        import sys

        # Ensure models is loaded
        import selection_maid.domain.models  # noqa: F401

        # All imports in models.py should be from stdlib only
        # We verify by checking the module's globals for non-stdlib modules
        models_module = importlib.import_module("selection_maid.domain.models")
        stdlib_modules = {
            "__future__",
            "dataclasses",
            "datetime",
            "pathlib",
            "typing",
            "builtins",
            "abc",
            "collections",
        }
        for name, obj in vars(models_module).items():
            if hasattr(obj, "__module__") and isinstance(obj.__module__, str):
                module_root = obj.__module__.split(".")[0]
                # Skip internal names and known stdlib
                if (
                    not name.startswith("_")
                    and module_root not in stdlib_modules
                    and module_root != "selection_maid"
                ):
                    # Check if it's in stdlib
                    assert (
                        module_root in sys.stdlib_module_names
                        or module_root in stdlib_modules
                    ), f"Non-stdlib import found: {name} from {obj.__module__}"
