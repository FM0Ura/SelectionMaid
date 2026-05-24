"""Pydantic v2 schemas for the HTTP API layer.

These schemas live in the HTTP adapter — not in the domain. The domain must
never import Pydantic (D-74).

Decision references:
- D-74: schemas belong to the HTTP adapter, not the domain
- D-75: ExtractionResponse mirrors ExtractionResult exactly (all 8 chunk fields,
        all 9 metadata fields) — no omission
- D-76: ingested_at (datetime) is serialized as ISO 8601 string automatically
        by Pydantic v2
- D-77: ConfigDict(from_attributes=True) enables model_validate() on frozen
        dataclasses without manual mapping
- D-78: HealthResponse fields: status, rss_mb, uptime_seconds, version
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChunkSchema(BaseModel):
    """Pydantic schema mirroring DocumentChunk (8 fields, D-75).

    All field names and types match domain/models.py:DocumentChunk exactly.
    ConfigDict(from_attributes=True) allows model_validate() on frozen
    dataclasses (D-77).
    """

    model_config = ConfigDict(from_attributes=True)

    chunk_id: str
    content: str
    page_start: int
    page_end: int
    section_title: str
    chunk_index: int
    total_chunks: int
    word_count: int


class MetadataSchema(BaseModel):
    """Pydantic schema mirroring DocumentMetadata (9 fields, D-75).

    ingested_at is declared as datetime; Pydantic v2 serializes it to an
    ISO 8601 string in JSON output automatically (D-76).
    ConfigDict(from_attributes=True) allows model_validate() on frozen
    dataclasses (D-77).
    """

    model_config = ConfigDict(from_attributes=True)

    doc_id: str
    source_filename: str
    title: str
    author: str
    language: str
    doc_type: str
    page_count: int
    chunk_count: int
    ingested_at: datetime


class ExtractionResponse(BaseModel):
    """Top-level response schema for POST /ingest.

    Mirrors ExtractionResult from the domain.

    Note: ExtractionResult.chunks is tuple[DocumentChunk, ...] but this schema
    uses list[ChunkSchema] — Pydantic v2 converts tuple to list automatically
    when from_attributes=True is used (D-77).

    Usage in router:
        response = ExtractionResponse.model_validate(result, from_attributes=True)
    """

    model_config = ConfigDict(from_attributes=True)

    metadata: MetadataSchema
    chunks: list[ChunkSchema]


class HealthResponse(BaseModel):
    """Response schema for GET /health (D-78).

    Fields:
    - status: always "ok" when the service is healthy
    - rss_mb: resident set size of the process in megabytes (via psutil)
    - uptime_seconds: seconds since the server started (from app.state.start_time)
    - version: package version (via importlib.metadata.version)
    """

    status: str = "ok"
    rss_mb: float
    uptime_seconds: float
    version: str
