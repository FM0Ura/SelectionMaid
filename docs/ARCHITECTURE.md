<!-- generated-by: gsd-doc-writer -->
# Architecture

SelectionMaid is a document curation and normalisation service built on the
**Hexagonal (Ports & Adapters)** pattern. Raw files enter in any supported
format (PDF, DOCX, HTML), pass through a four-stage pipeline, and exit as
structured Markdown chunks ready for a vector database. Every stage is
implemented as an interchangeable adapter — the domain core holds zero
references to infrastructure libraries.

## System Overview

The service accepts a single file per request via its HTTP input adapter,
runs it through the `extract → filter → chunk → enrich` pipeline, and
returns an `ExtractionResponse` containing enriched document metadata and an
ordered list of `DocumentChunk` objects. All pipeline stages communicate
exclusively through frozen domain value objects; no adapter ever passes a
library-specific type into the domain core. The primary deployment target is
a single-process FastAPI/uvicorn server suitable for low-traffic, on-demand
document ingestion.

## Component Diagram

```
                      ┌─────────────────────────────────────┐
                      │          HTTP Adapter (FastAPI)      │
                      │  POST /ingest      GET /health       │
                      │  3-layer validation                  │
                      │  run_in_threadpool (CPU offload)     │
                      └────────────────┬────────────────────┘
                                       │ RawInput
                                       ▼
                      ┌─────────────────────────────────────┐
                      │         ExtractionService            │
                      │    (application / orchestration)     │
                      │  extract → filter → chunk → enrich  │
                      └──┬──────────┬──────────┬──────────┬─┘
               RawInput  │          │RawDoc    │content   │raw+chunks
                         ▼          ▼          ▼          ▼
               ┌──────────┐  ┌──────────┐ ┌──────────┐ ┌──────────┐
               │ Extractor │  │  Filter  │ │ Chunker  │ │ Enricher │
               │  (Port)   │  │  (Port)  │ │  (Port)  │ │  (Port)  │
               └─────┬─────┘  └─────┬────┘ └─────┬────┘ └─────┬────┘
                     │              │             │             │
               DoclingAdapter  HeuristicFilter  Markdown-   Metadata-
               (Docling lib)   (stdlib only)    Chunker     Enricher
                                               (tiktoken)  (langdetect)
```

Arrows indicate data flow direction (caller → callee). Each box below
`ExtractionService` is a concrete adapter injected at startup.

## Data Flow

A typical request follows this path:

1. **HTTP layer** — `POST /ingest` receives a multipart file upload. Three
   validation layers run in sequence before any domain processing:
   (a) `Content-Length` header check (fail-fast, HTTP 413 / `UPLOAD-001`),
   (b) declared MIME type check against `allowed_mime_types` (HTTP 415 / `EXT-002`),
   (c) magic bytes detection via `python-magic` (HTTP 422 / `UPLOAD-002`).
   The file is written to a `NamedTemporaryFile` (`delete=False`, `mode="wb"`,
   with a `selectionmaid_` prefix) so Docling receives a real filesystem path.
   The tempfile is always deleted in a `finally` block after processing.

2. **Dispatch** — The handler calls `service.process(raw_input)` via
   `run_in_threadpool`, keeping the asyncio event loop unblocked for the
   duration of CPU-bound extraction.

3. **Extract** — `DoclingAdapter.extract()` acquires a `threading.Lock`,
   submits `DocumentConverter.convert(path)` to a single-worker
   `ThreadPoolExecutor` with a 120-second timeout, and maps the result to a
   `RawDocument` (Markdown string, filename, page count, format). `gc.collect()`
   runs after every extraction to mitigate memory growth.

4. **Filter** — `HeuristicFilter.filter()` applies three rules in order:
   frequency-based header/footer removal (lines appearing ≥ 3 times, length ≤ 80),
   isolated page-number removal (Arabic, Roman, hyphenated), and whitespace
   compression (3+ consecutive newlines → 2). Returns a new `RawDocument` via
   `dataclasses.replace`.

5. **Chunk** — `MarkdownChunker.chunk()` selects a strategy based on document
   structure: if H1/H2 headings are present, splits on heading boundaries and
   further subdivides oversized sections by paragraph; otherwise uses a
   token-budget fallback via tiktoken (`cl100k_base`, 512 tokens max). Every
   `DocumentChunk` carries a UUID v4 `chunk_id`, `section_title`, word count,
   and chunk position fields.

6. **Enrich** — `MetadataEnricher.enrich()` derives nine metadata fields:
   language (langdetect, ≥ 0.8 confidence, fallback `"und"`), doc_type
   (keyword heuristic: legal > presentation > form > report > other), title
   (first H1 heading or `""`), author (always `""`), and structural counts.

7. **Response** — `ExtractionService.process()` wraps the chunks in an
   immutable `tuple` inside `ExtractionResult`. The HTTP handler validates
   the domain object into an `ExtractionResponse` via
   `ExtractionResponse.model_validate(result, from_attributes=True)` and
   returns it as JSON.

8. **Cleanup** — The tempfile is unconditionally deleted in the `finally`
   block, even when processing fails.

## Key Abstractions

| Abstraction | File | Description |
|---|---|---|
| `ExtractorPort` | `domain/ports.py` | Protocol: `extract(RawInput) -> RawDocument` |
| `FilterPort` | `domain/ports.py` | Protocol: `filter(RawDocument) -> RawDocument` |
| `ChunkerPort` | `domain/ports.py` | Protocol: `chunk(str) -> list[DocumentChunk]` |
| `MetadataEnricherPort` | `domain/ports.py` | Protocol: `enrich(RawDocument, list[DocumentChunk]) -> DocumentMetadata` |
| `RawInput` | `domain/models.py` | Frozen dataclass: `path`, `filename`, `mime_type` |
| `RawDocument` | `domain/models.py` | Frozen dataclass: `content`, `filename`, `page_count`, `format` |
| `DocumentChunk` | `domain/models.py` | Frozen dataclass with 8 CHUNK-03 fields |
| `DocumentMetadata` | `domain/models.py` | Frozen dataclass with 9 META-01 fields |
| `ExtractionResult` | `domain/models.py` | Frozen dataclass: `metadata`, `chunks: tuple[DocumentChunk, ...]` |
| `ExtractionService` | `service.py` | Orchestrates pipeline; wraps non-domain exceptions in domain errors (D-16) |
| `SelectionMaidError` | `errors.py` | Base exception with `code` and `cause`; all domain errors inherit from it |
| `GlobalConfig` | `config.py` | Aggregates `FilterConfig`, `ChunkerConfig`, `EnricherConfig`, `HttpConfig` |

All four port Protocols use **structural typing** (no inheritance required).
`isinstance()` checks against port types are intentionally unsupported.

## Error Taxonomy

All domain errors inherit from `SelectionMaidError` (`errors.py`). The HTTP
adapter maps error codes to HTTP status via `ERROR_CODE_TO_HTTP`
(`adapters/http/error_map.py`). Non-domain exceptions raised by adapters are
wrapped by `ExtractionService` before they reach any caller.

| Code | Class | HTTP Status | When Raised |
|---|---|---|---|
| `EXT-001` | `ExtractionError` | 500 | Generic Docling conversion failure |
| `EXT-002` | `UnsupportedFormatError` | 415 | MIME type not in `SUPPORTED_MIME_TYPES` |
| `EXT-003` | `ExtractionTimeoutError` | 504 | Conversion exceeded 120-second timeout |
| `FILT-001` | `FilterError` | 500 | Unexpected error inside HeuristicFilter |
| `CHUNK-001` | `ChunkingError` | 500 | Unexpected error inside MarkdownChunker |
| `ENRICH-001` | `EnrichmentError` | 500 | Unexpected error inside MetadataEnricher |
| `UPLOAD-001` | _(HTTP only)_ | 413 | `Content-Length` exceeds `max_file_bytes` |
| `UPLOAD-002` | _(HTTP only)_ | 422 | Magic bytes mismatch — declared MIME ≠ detected |

## Directory Structure Rationale

```
src/selection_maid/
├── domain/             # Pure domain — zero third-party imports
│   ├── models.py       # Frozen dataclasses (value objects)
│   └── ports.py        # Protocol definitions (port contracts)
├── adapters/           # All infrastructure implementations
│   ├── extractor/
│   │   └── docling.py  # DoclingAdapter — only place Docling is imported at runtime
│   ├── filter/
│   │   └── heuristic.py # HeuristicFilter — stdlib only
│   ├── chunker/
│   │   └── markdown.py  # MarkdownChunker — tiktoken
│   ├── enricher/
│   │   └── default.py   # MetadataEnricher — langdetect
│   └── http/
│       ├── app.py        # FastAPI app factory + asynccontextmanager lifespan
│       ├── router.py     # build_router() closure; GET /health + POST /ingest
│       ├── schemas.py    # Pydantic v2 response schemas
│       └── error_map.py  # ERROR_CODE_TO_HTTP mapping
├── errors.py           # SelectionMaidError hierarchy
├── service.py          # ExtractionService — pipeline orchestration
└── config.py           # get_config(); reads config.toml; never raises on missing file
```

**Design principles reflected in this layout:**

- `domain/` has no dependencies on `adapters/` or any third-party library.
  The dependency arrow always points inward: adapters → domain, never the reverse.
- Each adapter subdirectory contains exactly one concrete implementation.
  Replacing an adapter means swapping one file and updating the factory call
  in `app.py`; the domain and service layers are untouched.
- All adapters expose a `build_*` factory function (e.g., `build_docling_adapter`,
  `build_heuristic_filter`, `build_markdown_chunker`, `build_metadata_enricher`,
  `build_router`). The lifespan in `app.py` is the single wiring point.
- Docling is imported only inside `adapters/extractor/docling.py` at runtime.
  All other modules use `TYPE_CHECKING` guards for Docling type annotations,
  preventing torch model loading on import of any other module.
- `config.py` uses `tomllib` (stdlib, Python 3.11+) to read `config.toml`.
  Missing files and missing keys silently fall back to hardcoded defaults (D-38).

## Adapter Wiring (Startup Sequence)

The `_lifespan` context manager in `adapters/http/app.py` performs all
one-time initialisation in this order:

```
1. Record app.state.start_time (UTC) for /health uptime
2. Import and construct DocumentConverter (triggers Docling/torch model loading)
3. Call get_config() → GlobalConfig
4. build_docling_adapter(converter)   → DoclingAdapter
5. build_heuristic_filter(config.filter) → HeuristicFilter
6. build_markdown_chunker(config.chunker) → MarkdownChunker
7. build_metadata_enricher(config.enricher) → MetadataEnricher
8. ExtractionService(extractor, filter_, chunker, enricher)
9. build_router(service, config) → APIRouter (included in app)
10. yield  ← server begins accepting requests
```

The `DocumentConverter` singleton is shared across all requests. A
`threading.Lock` inside `DoclingAdapter` serialises concurrent extractions
because `DocumentConverter` mutates internal model state and is not
thread-safe.

## Uvicorn Entry Point

```
uvicorn selection_maid.adapters.http.app:app
```

The module-level `app = create_app()` in `adapters/http/app.py` is the
uvicorn target. `create_app()` returns a `FastAPI` instance configured with
the `_lifespan` context manager; no adapter is constructed at import time.
