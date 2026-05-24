from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from selection_maid.adapters.chunker.markdown import build_markdown_chunker
from selection_maid.adapters.filter import HeuristicFilter
from selection_maid.config import ChunkerConfig
from selection_maid.domain.models import (
    DocumentChunk,
    ExtractionResult,
    RawDocument,
    RawInput,
)
from selection_maid.errors import ChunkingError, ExtractionError, SelectionMaidError
from selection_maid.service import ExtractionService
from tests.stubs.adapters import StubChunker, StubEnricher, StubExtractor, StubFilter


@pytest.fixture(scope="session")
def stub_service() -> ExtractionService:
    return ExtractionService(StubExtractor(), StubFilter(), StubChunker(), StubEnricher())


@pytest.fixture(scope="session")
def raw_input() -> RawInput:
    return RawInput(path=Path("/tmp/test.pdf"), filename="test.pdf", mime_type="application/pdf")


class TestPipeline:
    def test_process_returns_extraction_result(
        self, stub_service: ExtractionService, raw_input: RawInput
    ) -> None:
        result = stub_service.process(raw_input)
        assert isinstance(result, ExtractionResult)

    def test_result_chunks_is_tuple(
        self, stub_service: ExtractionService, raw_input: RawInput
    ) -> None:
        result = stub_service.process(raw_input)
        assert isinstance(result.chunks, tuple)

    def test_result_has_one_chunk(
        self, stub_service: ExtractionService, raw_input: RawInput
    ) -> None:
        result = stub_service.process(raw_input)
        assert len(result.chunks) == 1

    def test_chunk_has_all_required_fields(
        self, stub_service: ExtractionService, raw_input: RawInput
    ) -> None:
        result = stub_service.process(raw_input)
        chunk = result.chunks[0]
        assert chunk.chunk_id
        assert chunk.content
        assert chunk.page_start >= 1
        assert chunk.page_end >= 1
        assert chunk.section_title
        assert chunk.chunk_index == 0
        assert chunk.total_chunks == 1
        assert chunk.word_count > 0

    def test_metadata_has_all_required_fields(
        self, stub_service: ExtractionService, raw_input: RawInput
    ) -> None:
        result = stub_service.process(raw_input)
        meta = result.metadata
        assert meta.doc_id
        assert meta.source_filename
        assert meta.title
        assert meta.author
        assert meta.language == "en"
        assert meta.doc_type
        assert meta.page_count >= 0
        assert meta.chunk_count == 1
        assert meta.ingested_at is not None

    def test_metadata_chunk_count_matches(
        self, stub_service: ExtractionService, raw_input: RawInput
    ) -> None:
        result = stub_service.process(raw_input)
        assert result.metadata.chunk_count == len(result.chunks)


class TestHeuristicFilterIntegration:
    """Integration: ExtractionService correctly invokes HeuristicFilter (ARCH-02, D-39)."""

    def test_service_filters_noise_via_heuristic_filter(self, raw_input: RawInput) -> None:
        """HeuristicFilter removes noise when wired into ExtractionService.process()."""
        from selection_maid.adapters.filter import HeuristicFilter

        header = "Confidential"

        class NoisyExtractor:
            def extract(self, document: RawInput) -> RawDocument:
                noisy_content = (
                    f"{header}\n\n"
                    "## Section 1\n\nUseful content here.\n\n"
                    f"{header}\n\n"
                    "## Section 2\n\nMore useful content.\n\n"
                    f"{header}"
                )
                return RawDocument(
                    content=noisy_content,
                    filename=document.filename,
                    page_count=3,
                    format="pdf",
                )

        class PassthroughChunker:
            def chunk(self, content: str) -> list[DocumentChunk]:
                return [
                    DocumentChunk(
                        chunk_id="chunk-0",
                        content=content,
                        page_start=1,
                        page_end=1,
                        section_title="Section 1",
                        chunk_index=0,
                        total_chunks=1,
                        word_count=len(content.split()),
                    )
                ]

        service = ExtractionService(
            NoisyExtractor(),
            HeuristicFilter(min_repeat=3),
            PassthroughChunker(),
            StubEnricher(),
        )
        result = service.process(raw_input)
        chunk_content = result.chunks[0].content
        assert header not in chunk_content
        assert "Useful content here." in chunk_content
        assert "More useful content." in chunk_content


class TestMarkdownChunkerIntegration:
    """Integration: ExtractionService correctly processes documents with the real MarkdownChunker.

    Verifies end-to-end pipeline behaviour using build_markdown_chunker with default
    ChunkerConfig. Stubs are used for extractor and enricher so the test focuses
    exclusively on the service + chunker interaction.
    """

    @pytest.fixture()
    def markdown_service(self) -> ExtractionService:
        """ExtractionService wired with real HeuristicFilter and real MarkdownChunker."""
        chunker = build_markdown_chunker(ChunkerConfig())
        return ExtractionService(
            StubExtractor(),
            HeuristicFilter(),
            chunker,
            StubEnricher(),
        )

    @pytest.fixture()
    def raw_input(self) -> RawInput:
        return RawInput(path=Path("/tmp/test.pdf"), filename="test.pdf", mime_type="application/pdf")

    def test_service_returns_extraction_result(
        self, markdown_service: ExtractionService, raw_input: RawInput
    ) -> None:
        """ExtractionService.process() returns an ExtractionResult with the real chunker."""
        result = markdown_service.process(raw_input)
        assert isinstance(result, ExtractionResult)

    def test_chunks_are_returned(
        self, markdown_service: ExtractionService, raw_input: RawInput
    ) -> None:
        """The result contains at least one chunk from the real MarkdownChunker."""
        result = markdown_service.process(raw_input)
        assert len(result.chunks) >= 1

    def test_each_chunk_has_valid_chunk_id(
        self, markdown_service: ExtractionService, raw_input: RawInput
    ) -> None:
        """Each chunk carries a valid UUID v4 chunk_id (D-54)."""
        result = markdown_service.process(raw_input)
        for chunk in result.chunks:
            assert chunk.chunk_id, "chunk_id must not be empty"
            parsed = uuid.UUID(chunk.chunk_id)
            assert parsed.version == 4

    def test_each_chunk_has_positive_word_count(
        self, markdown_service: ExtractionService, raw_input: RawInput
    ) -> None:
        """Each chunk has word_count > 0 (D-55)."""
        result = markdown_service.process(raw_input)
        for chunk in result.chunks:
            assert chunk.word_count > 0

    def test_each_chunk_has_page_start_zero(
        self, markdown_service: ExtractionService, raw_input: RawInput
    ) -> None:
        """page_start is 0 for all chunks — no page info in Markdown string (D-53)."""
        result = markdown_service.process(raw_input)
        for chunk in result.chunks:
            assert chunk.page_start == 0

    def test_chunk_index_and_total_chunks_consistent(
        self, markdown_service: ExtractionService, raw_input: RawInput
    ) -> None:
        """chunk_index and total_chunks are consistent across the final chunk list."""
        result = markdown_service.process(raw_input)
        total = len(result.chunks)
        for i, chunk in enumerate(result.chunks):
            assert chunk.chunk_index == i, (
                f"chunk_index mismatch at position {i}: got {chunk.chunk_index}"
            )
            assert chunk.total_chunks == total, (
                f"total_chunks mismatch at position {i}: got {chunk.total_chunks}, expected {total}"
            )

    def test_service_with_headings_document_splits_correctly(
        self, raw_input: RawInput
    ) -> None:
        """ExtractionService with MarkdownChunker produces separate chunks per heading."""
        class HeadedExtractor:
            def extract(self, document: RawInput) -> RawDocument:
                return RawDocument(
                    content=(
                        "# Introduction\n\nIntro content here.\n\n"
                        "# Methods\n\nMethods content here."
                    ),
                    filename=document.filename,
                    page_count=1,
                    format="pdf",
                )

        chunker = build_markdown_chunker(ChunkerConfig())
        service = ExtractionService(
            HeadedExtractor(),
            HeuristicFilter(),
            chunker,
            StubEnricher(),
        )
        result = service.process(raw_input)
        assert len(result.chunks) == 2
        assert result.chunks[0].section_title == "Introduction"
        assert result.chunks[1].section_title == "Methods"
        assert result.chunks[0].chunk_index == 0
        assert result.chunks[1].chunk_index == 1
        assert result.chunks[0].total_chunks == 2
        assert result.chunks[1].total_chunks == 2

    def test_service_with_no_headings_uses_fallback(
        self, raw_input: RawInput
    ) -> None:
        """ExtractionService uses fixed-size fallback when document has no H1/H2 (D-49)."""
        class PlainExtractor:
            def extract(self, document: RawInput) -> RawDocument:
                return RawDocument(
                    content="Plain prose paragraph without headings.",
                    filename=document.filename,
                    page_count=1,
                    format="pdf",
                )

        chunker = build_markdown_chunker(ChunkerConfig())
        service = ExtractionService(
            PlainExtractor(),
            HeuristicFilter(),
            chunker,
            StubEnricher(),
        )
        result = service.process(raw_input)
        assert len(result.chunks) >= 1
        for chunk in result.chunks:
            assert chunk.section_title == ""


class TestExceptionWrapping:
    def test_non_domain_extractor_exception_becomes_extraction_error(
        self, raw_input: RawInput
    ) -> None:
        class ExtractorThatRaises:
            def extract(self, document: RawInput) -> RawDocument:
                raise ValueError("raw error")

        service = ExtractionService(
            ExtractorThatRaises(), StubFilter(), StubChunker(), StubEnricher()
        )
        with pytest.raises(ExtractionError):
            service.process(raw_input)

    def test_domain_error_propagates_unchanged(self, raw_input: RawInput) -> None:
        class ExtractorThatRaisesDomain:
            def extract(self, document: RawInput) -> RawDocument:
                raise ExtractionError("domain error")

        service = ExtractionService(
            ExtractorThatRaisesDomain(), StubFilter(), StubChunker(), StubEnricher()
        )
        with pytest.raises(ExtractionError):
            service.process(raw_input)

    def test_chunker_exception_becomes_chunking_error(self, raw_input: RawInput) -> None:
        class ChunkerThatRaises:
            def chunk(self, content: str) -> list[DocumentChunk]:
                raise RuntimeError("chunk fail")

        service = ExtractionService(
            StubExtractor(), StubFilter(), ChunkerThatRaises(), StubEnricher()
        )
        with pytest.raises(ChunkingError):
            service.process(raw_input)

    def test_non_domain_filter_exception_becomes_filter_error(
        self, raw_input: RawInput
    ) -> None:
        from selection_maid.errors import FilterError

        class FilterThatRaises:
            def filter(self, document: RawDocument) -> RawDocument:
                raise IOError("filter fail")

        service = ExtractionService(
            StubExtractor(), FilterThatRaises(), StubChunker(), StubEnricher()
        )
        with pytest.raises(FilterError):
            service.process(raw_input)

    def test_non_domain_enricher_exception_becomes_enrichment_error(
        self, raw_input: RawInput
    ) -> None:
        from selection_maid.domain.models import DocumentMetadata
        from selection_maid.errors import EnrichmentError

        class EnricherThatRaises:
            def enrich(
                self, raw: RawDocument, chunks: list[DocumentChunk]
            ) -> DocumentMetadata:
                raise RuntimeError("enrichment fail")

        service = ExtractionService(
            StubExtractor(), StubFilter(), StubChunker(), EnricherThatRaises()
        )
        with pytest.raises(EnrichmentError):
            service.process(raw_input)
