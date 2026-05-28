<!-- generated-by: gsd-doc-writer -->
# Architecture

SelectionMaid is a document curation and normalisation service built on the
**Hexagonal (Ports & Adapters)** pattern. Raw files enter in any supported
format (PDF, DOCX, HTML), pass through a four-stage pipeline, and exit as
structured Markdown chunks ready for a vector database. Every stage is
implemented as an interchangeable adapter — the domain core holds zero
references to infrastructure libraries.

A completely separate **Vue 3 SPA** frontend (`frontend/`) provides a
browser-based interface. The SPA is a static application that communicates
with the backend exclusively over HTTP — it is not imported by, compiled
with, or otherwise coupled to the Python backend.

## System Overview

The backend accepts a single file per request via its HTTP input adapter,
runs it through the `extract → filter → chunk → enrich` pipeline, and
returns an `ExtractionResponse` containing enriched document metadata and an
ordered list of `DocumentChunk` objects. All pipeline stages communicate
exclusively through frozen domain value objects; no adapter ever passes a
library-specific type into the domain core. The primary deployment target is
a single-process FastAPI/uvicorn server suitable for low-traffic, on-demand
document ingestion.

The frontend SPA runs in the browser and communicates with the backend
through a single endpoint (`POST /ingest`). During development, Vite's dev
server proxies `/api/*` requests to `http://localhost:8000`, stripping the
`/api` prefix before forwarding. In production the SPA is served as a static
build; the backend must be reachable at the same origin or configured via a
reverse proxy. CORS is enabled on the backend for `http://localhost:5173`
(the Vite dev server origin).

## Component Diagram

```text
  Browser
  ┌────────────────────────────────────────────────────────────┐
  │                    Vue 3 SPA (frontend/)                   │
  │                                                            │
  │  App.vue                                                   │
  │   └─ useUpload (composable — discriminated union FSM)      │
  │       ├─ DropZone ──── drag/drop + file picker             │
  │       │   ├─ ProcessingCard (spinner + elapsed timer)      │
  │       │   ├─ ErrorBanner                                   │
  │       │   └─ DropOverlay                                   │
  │       └─ ResultView ── success screen                      │
  │           ├─ MetadataCard (doc metadata summary)           │
  │           └─ ChunkCard × N (copy + per-chunk download)     │
  │               └─ MarkdownRenderer (markdown-it + DOMPurify)│
  │                                                            │
  │  src/api/ingest.ts ──── fetch POST /api/ingest             │
  │  src/types/api.ts  ──── TypeScript types mirroring backend │
  └───────────────────────────┬────────────────────────────────┘
                              │ HTTP  (JSON response)
                    Vite proxy /api → :8000 (dev)
                              │
  ┌───────────────────────────▼────────────────────────────────┐
  │                  HTTP Adapter (FastAPI)                     │
  │   POST /ingest              GET /health                    │
  │   3-layer validation        CORS: localhost:5173           │
  │   run_in_threadpool (CPU offload)                          │
  └───────────────────────────┬────────────────────────────────┘
                              │ RawInput
                              ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                   ExtractionService                         │
  │             (application / orchestration)                   │
  │         extract → filter → chunk → enrich                  │
  └──┬──────────┬──────────┬──────────┬──────────────────────┘
     │          │          │          │
     ▼          ▼          ▼          ▼
  ┌──────────┐  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │Extractor │  │  Filter  │ │ Chunker  │ │ Enricher │
  │  (Port)  │  │  (Port)  │ │  (Port)  │ │  (Port)  │
  └─────┬────┘  └─────┬────┘ └─────┬────┘ └─────┬────┘
        │             │            │             │
  DoclingAdapter  Heuristic-   Markdown-   Metadata-
  (Docling lib)   Filter       Chunker     Enricher
                  (stdlib)     (tiktoken)  (langdetect)
```

Arrows indicate data flow direction (caller → callee). Each adapter below
`ExtractionService` is a concrete implementation injected at startup.

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
| --- | --- | --- |
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
| --- | --- | --- | --- |
| `EXT-001` | `ExtractionError` | 500 | Generic Docling conversion failure |
| `EXT-002` | `UnsupportedFormatError` | 415 | MIME type not in `SUPPORTED_MIME_TYPES` |
| `EXT-003` | `ExtractionTimeoutError` | 504 | Conversion exceeded 120-second timeout |
| `FILT-001` | `FilterError` | 500 | Unexpected error inside HeuristicFilter |
| `CHUNK-001` | `ChunkingError` | 500 | Unexpected error inside MarkdownChunker |
| `ENRICH-001` | `EnrichmentError` | 500 | Unexpected error inside MetadataEnricher |
| `UPLOAD-001` | _(HTTP only)_ | 413 | `Content-Length` exceeds `max_file_bytes` |
| `UPLOAD-002` | _(HTTP only)_ | 422 | Magic bytes mismatch — declared MIME ≠ detected |

## Directory Structure Rationale

```text
SelectionMaid/
├── src/selection_maid/         # Python backend (hexagonal architecture)
│   ├── domain/                 # Pure domain — zero third-party imports
│   │   ├── models.py           # Frozen dataclasses (value objects)
│   │   └── ports.py            # Protocol definitions (port contracts)
│   ├── adapters/               # All infrastructure implementations
│   │   ├── extractor/
│   │   │   └── docling.py      # DoclingAdapter — only place Docling is imported at runtime
│   │   ├── filter/
│   │   │   └── heuristic.py    # HeuristicFilter — stdlib only
│   │   ├── chunker/
│   │   │   └── markdown.py     # MarkdownChunker — tiktoken
│   │   ├── enricher/
│   │   │   └── default.py      # MetadataEnricher — langdetect
│   │   └── http/
│   │       ├── app.py          # FastAPI app factory + asynccontextmanager lifespan
│   │       ├── router.py       # build_router() closure; GET /health + POST /ingest
│   │       ├── schemas.py      # Pydantic v2 response schemas
│   │       └── error_map.py    # ERROR_CODE_TO_HTTP mapping
│   ├── errors.py               # SelectionMaidError hierarchy
│   ├── service.py              # ExtractionService — pipeline orchestration
│   └── config.py               # get_config(); reads config.toml; never raises on missing file
│
├── frontend/                   # Vue 3 SPA — completely decoupled from backend
│   ├── src/
│   │   ├── types/
│   │   │   └── api.ts          # TypeScript types mirroring backend JSON schema
│   │   ├── api/
│   │   │   ├── ingest.ts       # postIngest() — fetch wrapper with 130s AbortSignal
│   │   │   └── errors.ts       # ApiResponseError class + mapApiError()
│   │   ├── composables/
│   │   │   └── useUpload.ts    # Discriminated-union state machine (FSM)
│   │   ├── components/
│   │   │   ├── upload/         # DropZone, ProcessingCard, SkeletonChunk, ErrorBanner, DropOverlay
│   │   │   └── result/         # ResultView, MetadataCard, ChunkCard, MarkdownRenderer
│   │   ├── lib/
│   │   │   ├── formatters.ts   # formatDate, formatDuration, slugifyFilename, formatPageRange
│   │   │   └── validators.ts   # validateFile — client-side pre-upload checks
│   │   ├── App.vue             # Root component — AnimatePresence view transitions
│   │   └── main.ts             # Vue app bootstrap
│   └── vite.config.ts          # Dev proxy: /api → http://localhost:8000
│
├── tests/                      # Backend test suite (pytest)
└── config.toml                 # Backend runtime configuration
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
- `frontend/` is a fully independent Node.js project (`package.json`, `vite.config.ts`).
  It shares no build tooling, no runtime, and no import graph with the Python backend.
  The only contract between them is the JSON shape returned by `POST /ingest`.

## Adapter Wiring (Startup Sequence)

The `_lifespan` context manager in `adapters/http/app.py` performs all
one-time initialisation in this order:

```text
1. Record app.state.start_time (UTC) for /health uptime
2. Import and construct DocumentConverter (triggers Docling/torch model loading)
3. Call get_config() → GlobalConfig
4. build_docling_adapter(converter)    → DoclingAdapter
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

## Frontend Architecture

The Vue 3 SPA is a single-page application with no server-side rendering.
Its internal design follows a layered pattern: types → API layer →
composable state machine → components.

### Type Contract (`src/types/api.ts`)

All TypeScript interfaces in `src/types/api.ts` mirror the backend's Pydantic
schemas exactly. This file is the single source of truth for the frontend's
understanding of the API contract:

- `Chunk` — mirrors `DocumentChunk` (8 fields: `chunk_id`, `content`,
  `page_start`, `page_end`, `section_title`, `chunk_index`, `total_chunks`,
  `word_count`)
- `DocumentMetadata` — mirrors `DocumentMetadata` (9 fields)
- `ExtractionResponse` — top-level response: `{ metadata, chunks }`
- `UploadState` — discriminated union used by the state machine (see below)

### API Layer (`src/api/ingest.ts`, `src/api/errors.ts`)

`postIngest(file: File): Promise<ExtractionResponse>` is the single function
that calls the backend. It:

- Constructs a `FormData` and `POST`s to `/api/ingest` via native `fetch`
- Attaches `AbortSignal.timeout(130_000)` — matches the backend's 120-second
  extraction timeout plus a buffer
- On a non-2xx response, parses the error body and throws `ApiResponseError`
  (carrying `status` and optional `code`)

`mapApiError(error)` in `src/api/errors.ts` translates any thrown value into a
user-facing Portuguese string, with specific messages for HTTP 413, 415, 422,
504, and `AbortError` (timeout).

### State Machine (`src/composables/useUpload.ts`)

`useUpload()` is the central composable. It owns all upload state as a single
`ref<UploadState>` whose type is a discriminated union:

| Status | Shape | When |
| --- | --- | --- |
| `idle` | `{ status: 'idle' }` | Initial state and after reset |
| `dragging` | `{ status: 'dragging' }` | File dragged over the drop zone |
| `uploading` | `{ status: 'uploading'; progress: number }` | `fetch` initiated (brief — transitions immediately to `processing`) |
| `processing` | `{ status: 'processing' }` | Awaiting the backend response; elapsed timer ticking |
| `success` | `{ status: 'success'; data: ExtractionResponse }` | Response received |
| `error` | `{ status: 'error'; message: string; code?: string }` | Validation failure or API error |

A `useIntervalFn` (VueUse) drives the elapsed-seconds counter while status
is `processing`. The composable also runs `validateFile()` (from
`src/lib/validators.ts`) before initiating any network call, catching
client-side errors (wrong MIME type, multiple files) without a round trip.

### Component Tree

```text
App.vue  (AnimatePresence — cross-fades between upload and result views)
├─ DropZone.vue           drag-drop zone + file input button
│   ├─ DropOverlay.vue    full-area overlay shown during drag
│   ├─ ProcessingCard.vue spinner + elapsed timer (uploading / processing states)
│   ├─ SkeletonChunk.vue  shimmer skeleton placeholders (processing state; rendered in App.vue)
│   └─ ErrorBanner.vue    inline error with retry action
└─ ResultView.vue         success view; download-all button
    ├─ MetadataCard.vue   document summary: type, language, pages, chunks, timing
    └─ ChunkCard.vue × N  per-chunk: copy-to-clipboard + individual Markdown download
        └─ MarkdownRenderer.vue  markdown-it + DOMPurify + highlight.js
```

- **Animations** — `motion-v` v2.2 (Motion for Vue) handles all transitions:
  `AnimatePresence` for view-level cross-fades in `App.vue`, spring-physics
  `layout-id` shared element transition between `ProcessingCard` and
  `MetadataCard`, and staggered `ChunkCard` reveal on the result screen.
- **UI primitives** — shadcn-vue components (`Card`, `Button`, `Skeleton`) with
  a purple/black dark theme using OKLCH color tokens via Tailwind CSS v4.
- **Markdown rendering** — `MarkdownRenderer.vue` uses a module-scope
  `MarkdownIt` instance (not recreated per render), applies `highlight.js`
  syntax highlighting, forces `target="_blank" rel="noopener noreferrer"` on
  all links, wraps tables in `overflow-x-auto`, and sanitises the final HTML
  with `DOMPurify`.

## Uvicorn Entry Point

```bash
uvicorn selection_maid.adapters.http.app:app
```

The module-level `app = create_app()` in `adapters/http/app.py` is the
uvicorn target. `create_app()` returns a `FastAPI` instance configured with
the `_lifespan` context manager; no adapter is constructed at import time.
