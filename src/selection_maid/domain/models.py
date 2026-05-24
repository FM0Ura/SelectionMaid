"""Domain value objects for SelectionMaid.

All dataclasses are frozen (immutable after construction). No third-party
imports — only stdlib modules are used here.

Defined in dependency order (no forward references needed):
  1. RawInput       — entry object for ExtractorPort.extract()
  2. RawDocument    — Markdown blob returned by extractor / filter
  3. DocumentChunk  — single chunk with all CHUNK-03 required fields
  4. DocumentMetadata — enriched metadata with all META-01 required fields (9 fields)
  5. ExtractionResult — final pipeline output
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class RawInput:
    """Entry value object passed to ExtractorPort.extract().

    Decision D-05: path, filename, mime_type. mime_type is detected by the
    HTTP adapter from magic bytes; the domain never detects it.
    """

    path: Path
    filename: str
    mime_type: str


@dataclass(frozen=True)
class RawDocument:
    """Markdown blob returned by the extractor and passed through the filter.

    Decision D-06: content is a single Markdown string; page_count=0 is valid
    when unknown; format is lowercase ("pdf", "docx", "html", ...).
    """

    content: str
    filename: str
    page_count: int
    format: str


@dataclass(frozen=True)
class DocumentChunk:
    """Single text chunk with structural metadata.

    Fields per CHUNK-03 requirement (exactly 8):
      chunk_id, content, page_start, page_end, section_title,
      chunk_index, total_chunks, word_count.
    """

    chunk_id: str
    content: str
    page_start: int
    page_end: int
    section_title: str
    chunk_index: int
    total_chunks: int
    word_count: int


@dataclass(frozen=True)
class DocumentMetadata:
    """Enriched document-level metadata.

    Fields per META-01 requirement (exactly 9):
      doc_id, source_filename, title, author, language (ISO 639-1),
      doc_type, page_count, chunk_count, ingested_at.
    """

    doc_id: str
    source_filename: str
    title: str
    author: str
    language: str
    doc_type: str
    page_count: int
    chunk_count: int
    ingested_at: datetime


@dataclass(frozen=True)
class ExtractionResult:
    """Final output of the ExtractionService pipeline.

    Decision D-07: chunks uses tuple[DocumentChunk, ...] (not list) so the
    collection is immutable and consistent with the frozen-domain design.
    No warnings field in v1 (deferred to v2).
    """

    metadata: DocumentMetadata
    chunks: tuple[DocumentChunk, ...]
