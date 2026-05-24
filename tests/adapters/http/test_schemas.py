"""Tests for HTTP adapter Pydantic schemas.

Verifies that:
- ChunkSchema has all 8 DocumentChunk fields (D-75)
- MetadataSchema has all 9 DocumentMetadata fields (D-75)
- ExtractionResponse mirrors ExtractionResult (D-75, D-77)
- HealthResponse has the required 4 fields (D-78)
- from_attributes=True enables model_validate on frozen dataclasses (D-77)
- ingested_at is serialized as ISO 8601 string (D-76)
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from selection_maid.domain.models import (
    DocumentChunk,
    DocumentMetadata,
    ExtractionResult,
)


# ---------------------------------------------------------------------------
# ChunkSchema field coverage
# ---------------------------------------------------------------------------


def test_chunk_schema_has_all_eight_fields() -> None:
    """ChunkSchema must expose all 8 DocumentChunk fields (D-75)."""
    from selection_maid.adapters.http.schemas import ChunkSchema

    fields = set(ChunkSchema.model_fields.keys())
    expected = {
        "chunk_id",
        "content",
        "page_start",
        "page_end",
        "section_title",
        "chunk_index",
        "total_chunks",
        "word_count",
    }
    assert fields == expected, f"Missing or extra fields: {fields.symmetric_difference(expected)}"


def test_chunk_schema_from_attributes_enabled() -> None:
    """ChunkSchema must have from_attributes=True (D-77)."""
    from selection_maid.adapters.http.schemas import ChunkSchema

    assert ChunkSchema.model_config.get("from_attributes") is True


def test_chunk_schema_model_validate_from_dataclass() -> None:
    """model_validate must work directly on a DocumentChunk frozen dataclass."""
    from selection_maid.adapters.http.schemas import ChunkSchema

    chunk = DocumentChunk(
        chunk_id=str(uuid4()),
        content="Hello world chunk.",
        page_start=1,
        page_end=2,
        section_title="Introduction",
        chunk_index=0,
        total_chunks=3,
        word_count=3,
    )
    result = ChunkSchema.model_validate(chunk, from_attributes=True)
    assert result.chunk_id == chunk.chunk_id
    assert result.content == chunk.content
    assert result.page_start == chunk.page_start
    assert result.page_end == chunk.page_end
    assert result.section_title == chunk.section_title
    assert result.chunk_index == chunk.chunk_index
    assert result.total_chunks == chunk.total_chunks
    assert result.word_count == chunk.word_count


# ---------------------------------------------------------------------------
# MetadataSchema field coverage
# ---------------------------------------------------------------------------


def test_metadata_schema_has_all_nine_fields() -> None:
    """MetadataSchema must expose all 9 DocumentMetadata fields (D-75)."""
    from selection_maid.adapters.http.schemas import MetadataSchema

    fields = set(MetadataSchema.model_fields.keys())
    expected = {
        "doc_id",
        "source_filename",
        "title",
        "author",
        "language",
        "doc_type",
        "page_count",
        "chunk_count",
        "ingested_at",
    }
    assert fields == expected, f"Missing or extra fields: {fields.symmetric_difference(expected)}"


def test_metadata_schema_from_attributes_enabled() -> None:
    """MetadataSchema must have from_attributes=True (D-77)."""
    from selection_maid.adapters.http.schemas import MetadataSchema

    assert MetadataSchema.model_config.get("from_attributes") is True


def test_metadata_schema_model_validate_from_dataclass() -> None:
    """model_validate must work directly on a DocumentMetadata frozen dataclass."""
    from selection_maid.adapters.http.schemas import MetadataSchema

    now = datetime.now(timezone.utc)
    meta = DocumentMetadata(
        doc_id=str(uuid4()),
        source_filename="report.pdf",
        title="Annual Report",
        author="Acme Corp",
        language="en",
        doc_type="pdf",
        page_count=10,
        chunk_count=5,
        ingested_at=now,
    )
    result = MetadataSchema.model_validate(meta, from_attributes=True)
    assert result.doc_id == meta.doc_id
    assert result.source_filename == meta.source_filename
    assert result.title == meta.title
    assert result.author == meta.author
    assert result.language == meta.language
    assert result.doc_type == meta.doc_type
    assert result.page_count == meta.page_count
    assert result.chunk_count == meta.chunk_count
    assert result.ingested_at == meta.ingested_at


def test_metadata_schema_ingested_at_serialized_as_iso8601() -> None:
    """ingested_at datetime must be serialized as ISO 8601 string (D-76)."""
    from selection_maid.adapters.http.schemas import MetadataSchema

    now = datetime(2026, 5, 24, 20, 15, 0, tzinfo=timezone.utc)
    meta = DocumentMetadata(
        doc_id=str(uuid4()),
        source_filename="doc.pdf",
        title="Test",
        author="Author",
        language="en",
        doc_type="pdf",
        page_count=1,
        chunk_count=1,
        ingested_at=now,
    )
    schema_instance = MetadataSchema.model_validate(meta, from_attributes=True)
    serialized = schema_instance.model_dump(mode="json")
    # Pydantic v2 serializes datetime to ISO 8601 string
    assert isinstance(serialized["ingested_at"], str)
    assert "2026-05-24" in serialized["ingested_at"]


# ---------------------------------------------------------------------------
# ExtractionResponse
# ---------------------------------------------------------------------------


def test_extraction_response_has_metadata_and_chunks_fields() -> None:
    """ExtractionResponse must have metadata and chunks fields."""
    from selection_maid.adapters.http.schemas import ExtractionResponse

    fields = set(ExtractionResponse.model_fields.keys())
    assert "metadata" in fields
    assert "chunks" in fields


def test_extraction_response_from_attributes_enabled() -> None:
    """ExtractionResponse must have from_attributes=True (D-77)."""
    from selection_maid.adapters.http.schemas import ExtractionResponse

    assert ExtractionResponse.model_config.get("from_attributes") is True


def test_extraction_response_model_validate_from_extraction_result() -> None:
    """ExtractionResponse.model_validate must handle ExtractionResult (D-77).

    ExtractionResult.chunks is tuple[DocumentChunk, ...] — Pydantic converts
    to list automatically.
    """
    from selection_maid.adapters.http.schemas import ExtractionResponse

    now = datetime.now(timezone.utc)
    meta = DocumentMetadata(
        doc_id=str(uuid4()),
        source_filename="doc.pdf",
        title="Test Document",
        author="Test Author",
        language="en",
        doc_type="pdf",
        page_count=2,
        chunk_count=1,
        ingested_at=now,
    )
    chunk = DocumentChunk(
        chunk_id=str(uuid4()),
        content="Some content here.",
        page_start=1,
        page_end=1,
        section_title="Overview",
        chunk_index=0,
        total_chunks=1,
        word_count=3,
    )
    result = ExtractionResult(metadata=meta, chunks=(chunk,))

    response = ExtractionResponse.model_validate(result, from_attributes=True)
    assert response.metadata.doc_id == meta.doc_id
    assert len(response.chunks) == 1
    assert response.chunks[0].chunk_id == chunk.chunk_id


# ---------------------------------------------------------------------------
# HealthResponse
# ---------------------------------------------------------------------------


def test_health_response_has_all_four_fields() -> None:
    """HealthResponse must have status, rss_mb, uptime_seconds, version (D-78)."""
    from selection_maid.adapters.http.schemas import HealthResponse

    fields = set(HealthResponse.model_fields.keys())
    expected = {"status", "rss_mb", "uptime_seconds", "version"}
    assert fields == expected, f"Missing or extra fields: {fields.symmetric_difference(expected)}"


def test_health_response_status_default_is_ok() -> None:
    """HealthResponse.status defaults to 'ok' (D-78)."""
    from selection_maid.adapters.http.schemas import HealthResponse

    health = HealthResponse(rss_mb=128.5, uptime_seconds=3600.0, version="0.1.0")
    assert health.status == "ok"


def test_health_response_instantiation() -> None:
    """HealthResponse must be instantiable with required fields."""
    from selection_maid.adapters.http.schemas import HealthResponse

    health = HealthResponse(
        status="ok",
        rss_mb=256.0,
        uptime_seconds=7200.0,
        version="0.1.0",
    )
    assert health.rss_mb == 256.0
    assert health.uptime_seconds == 7200.0
    assert health.version == "0.1.0"
