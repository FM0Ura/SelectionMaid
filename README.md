<!-- generated-by: gsd-doc-writer -->
# SelectionMaid

Document curation and normalisation service. Accepts raw files (PDF, DOCX, HTML) and returns structured Markdown chunks ready for vector database ingestion.

SelectionMaid is the intake layer of a RAG pipeline. It receives unstructured documents, extracts their content via [Docling](https://github.com/docling-project/docling), removes noise (headers, footers, repetitive lines), segments the result into token-bounded Markdown chunks, and enriches each chunk with document-level metadata. The output is a stable JSON envelope that any vector store can consume without knowing anything about the source format or extraction library used.

The service is built on a **hexagonal (Ports & Adapters) architecture**: every adapter — extractor, filter, chunker, enricher, HTTP interface — is replaceable without touching the domain core.

---

## Features

- Accepts PDF, DOCX, and HTML via multipart file upload
- Three-layer upload validation: Content-Length, declared MIME type, magic bytes
- Extraction powered by Docling (DocLayNet + TableFormer AI models)
- Heuristic header/footer filter removes document noise before chunking
- Token-aware Markdown chunker respects heading boundaries (default 512 tokens/chunk)
- Metadata enrichment: language detection (ISO 639-1), doc type classification, page count, ingestion timestamp
- Asynchronous FastAPI service — Docling processing offloaded to thread executor so the event loop is never blocked
- Configuration via optional `config.toml`; all keys fall back to hardcoded defaults

---

## Quick Start

**Prerequisites:** Python 3.13+, [`uv`](https://docs.astral.sh/uv/)

```bash
# 1. Clone the repository
git clone <repository-url>
cd SelectionMaid

# 2. Install dependencies (CPU-only torch is pinned in pyproject.toml)
uv sync

# 3. Start the service
uv run uvicorn selection_maid.adapters.http.app:app --reload
```

The service starts on `http://127.0.0.1:8000` by default. Interactive API docs are available at `http://127.0.0.1:8000/docs`.

---

## API Overview

### `POST /ingest`

Upload a document for processing. Returns structured Markdown chunks with metadata.

**Request** — `multipart/form-data`. Field: `file` (PDF, DOCX, or HTML; max 50 MB).

**Response** — `200 OK`

```json
{
  "metadata": {
    "doc_id": "a1b2c3d4-...",
    "source_filename": "report.pdf",
    "title": "Annual Report 2024",
    "author": "",
    "language": "en",
    "doc_type": "report",
    "page_count": 12,
    "chunk_count": 34,
    "ingested_at": "2025-05-25T14:30:00.000000+00:00"
  },
  "chunks": [
    {
      "chunk_id": "a1b2c3d4-...-0",
      "content": "## Executive Summary\n\nThis report covers...",
      "page_start": 1,
      "page_end": 1,
      "section_title": "Executive Summary",
      "chunk_index": 0,
      "total_chunks": 34,
      "word_count": 87
    }
  ]
}
```

**Error responses** use a structured body:

```json
{"error": {"code": "UPLOAD-001", "message": "File size exceeds maximum allowed size."}}
```

| HTTP Status | Error Code   | Condition                                   |
|-------------|--------------|---------------------------------------------|
| 413         | `UPLOAD-001` | File exceeds 50 MB limit                    |
| 415         | `EXT-002`    | Unsupported MIME type                       |
| 422         | `UPLOAD-002` | Magic bytes do not match declared MIME type |
| 500         | `EXT-001`    | Extraction or processing failure            |

### `GET /health`

Liveness check. Returns process memory, uptime, and package version.

```json
{
  "status": "ok",
  "rss_mb": 412.3,
  "uptime_seconds": 183.7,
  "version": "0.1.0"
}
```

---

## Configuration

Configuration is read from `config.toml` in the working directory at startup. All keys are optional — omitting a key or the entire file uses the hardcoded default.

```toml
# config.toml — all keys optional

[filter]
# Minimum repetitions for a line to be treated as header/footer (default: 3)
min_repeat = 3
# Maximum character length for a header/footer candidate line (default: 80)
max_line_len = 80

[chunker]
# Maximum token budget per chunk (default: 512)
max_tokens = 512

[http]
# Maximum accepted file size in bytes (default: 52428800 = 50 MB)
max_file_bytes = 52428800
# Accepted MIME types (default: PDF, DOCX, HTML)
allowed_mime_types = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/html",
]
```

---

## Project Structure

```text
src/selection_maid/
├── domain/
│   ├── models.py       # Frozen dataclasses: RawInput, RawDocument, DocumentChunk,
│   │                   # DocumentMetadata, ExtractionResult
│   └── ports.py        # Protocol interfaces: ExtractorPort, FilterPort,
│                       # ChunkerPort, MetadataEnricherPort
├── adapters/
│   ├── extractor/
│   │   └── docling.py  # DoclingAdapter — wraps DocumentConverter (ExtractorPort)
│   ├── filter/
│   │   └── heuristic.py # HeuristicFilter — removes repeated header/footer lines
│   ├── chunker/
│   │   └── markdown.py  # MarkdownChunker — heading-based, token-bounded splitting
│   ├── enricher/
│   │   └── default.py   # MetadataEnricher — language detection, doc type, timestamps
│   └── http/
│       ├── app.py       # FastAPI app factory + lifespan wiring
│       ├── router.py    # build_router() — GET /health, POST /ingest
│       └── schemas.py   # Pydantic v2 request/response schemas
├── service.py           # ExtractionService — orchestrates extract → filter → chunk → enrich
├── config.py            # get_config() — reads config.toml, falls back to defaults
└── errors.py            # Domain error taxonomy (SelectionMaidError subclasses)
```

### Pipeline

```text
POST /ingest (file upload)
    │
    ├─ Layer 1: Content-Length check (HTTP 413 if exceeded)
    ├─ Layer 2: Declared MIME type check (HTTP 415 if unsupported)
    └─ Layer 3: Magic bytes verification (HTTP 422 if mismatch)
          │
          ▼
    ExtractionService.process()
          │
          ├─ ExtractorPort  →  DoclingAdapter     (Markdown extraction)
          ├─ FilterPort     →  HeuristicFilter    (noise removal)
          ├─ ChunkerPort    →  MarkdownChunker    (token-bounded segments)
          └─ MetadataEnricherPort → MetadataEnricher (language, type, timestamps)
          │
          ▼
    ExtractionResponse (JSON)
```

---

## Running Tests

```bash
# Run the full test suite
uv run pytest

# Exclude slow integration tests (those that load Docling models)
uv run pytest -m "not slow"

# Run a specific test file
uv run pytest tests/domain/test_service.py

# With coverage report (requires pytest-cov: uv add --dev pytest-cov)
# uv run pytest --cov=src --cov-report=term-missing
```

Test fixtures (minimal PDF, DOCX, HTML) live in `tests/fixtures/`.

---

## Development

```bash
# Lint and format
uv run ruff check src tests
uv run ruff format src tests

# Type checking
uv run mypy src
```

Ruff is configured with rules `E, F, I, UP, B, SIM` at line length 88. Mypy runs in `strict` mode.

---

## License

<!-- VERIFY: LICENSE file presence and license type -->
See LICENSE for details.
