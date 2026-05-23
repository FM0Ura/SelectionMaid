from __future__ import annotations

from pathlib import Path

import pytest

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
        assert meta.title
        assert meta.author
        assert meta.language == "en"
        assert meta.document_type
        assert meta.page_count >= 0
        assert meta.chunk_count == 1
        assert meta.ingestion_date is not None

    def test_metadata_chunk_count_matches(
        self, stub_service: ExtractionService, raw_input: RawInput
    ) -> None:
        result = stub_service.process(raw_input)
        assert result.metadata.chunk_count == len(result.chunks)


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
