from __future__ import annotations

from datetime import datetime
from pathlib import Path

from selection_maid.domain.models import (
    DocumentChunk,
    DocumentMetadata,
    RawDocument,
    RawInput,
)


class StubExtractor:
    def extract(self, document: RawInput) -> RawDocument:
        return RawDocument(
            content="# Hello\nContent.",
            filename=document.filename,
            page_count=1,
            format="pdf",
        )


class StubFilter:
    def filter(self, document: RawDocument) -> RawDocument:
        return document


class StubChunker:
    def chunk(self, content: str) -> list[DocumentChunk]:
        return [
            DocumentChunk(
                chunk_id="chunk-0",
                content=content,
                page_start=1,
                page_end=1,
                section_title="Hello",
                chunk_index=0,
                total_chunks=1,
                word_count=2,
            )
        ]


class StubEnricher:
    def enrich(self, raw: RawDocument, chunks: list[DocumentChunk]) -> DocumentMetadata:
        return DocumentMetadata(
            doc_id="stub-id",
            source_filename="test.pdf",
            title="Test Doc",
            author="Author",
            language="en",
            doc_type="article",
            page_count=raw.page_count,
            chunk_count=len(chunks),
            ingested_at=datetime.now(),
        )
