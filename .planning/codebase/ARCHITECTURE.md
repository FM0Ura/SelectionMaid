<!-- refreshed: 2026-05-27 -->
# Architecture

**Analysis Date:** 2026-05-27

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                    Browser Vue 3 SPA                         │
├──────────────────┬──────────────────┬───────────────────────┤
│ Upload workflow  │ API client/types │ Result presentation    │
│ `frontend/src/`  │ `frontend/src/`  │ `frontend/src/`        │
└────────┬─────────┴──────────────────┴───────────────────────┘
         │ POST `/api/ingest` (Vite proxy rewrites to `/ingest`)
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI HTTP Adapter                      │
│ `src/selection_maid/adapters/http/app.py`                    │
│ `src/selection_maid/adapters/http/router.py`                 │
└────────┬────────────────────────────────────────────────────┘
         │ `RawInput`
         ▼
┌─────────────────────────────────────────────────────────────┐
│               Application Service / Pipeline Core            │
│ `src/selection_maid/service.py`                              │
│ extract -> filter -> chunk -> enrich                         │
└──┬──────────────┬──────────────┬──────────────┬─────────────┘
   │              │              │              │
   ▼              ▼              ▼              ▼
┌───────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐
│ Extractor │ │ Filter     │ │ Chunker    │ │ Enricher       │
│ Port      │ │ Port       │ │ Port       │ │ Port           │
│ `domain/` │ │ `domain/`  │ │ `domain/`  │ │ `domain/`      │
└─────┬─────┘ └──────┬─────┘ └──────┬─────┘ └───────┬────────┘
      ▼              ▼              ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Concrete Adapters                         │
│ `adapters/extractor/docling.py`                              │
│ `adapters/filter/heuristic.py`                               │
│ `adapters/chunker/markdown.py`                               │
│ `adapters/enricher/default.py`                               │
└─────────────────────────────────────────────────────────────┘
```

SelectionMaid is a document ingestion and normalization application with two independent runtimes: a Python backend under `src/selection_maid/` and a Vue 3 frontend under `frontend/`. The backend uses hexagonal architecture: `src/selection_maid/domain/models.py` and `src/selection_maid/domain/ports.py` define pure domain contracts, `src/selection_maid/service.py` orchestrates the use case, and `src/selection_maid/adapters/` contains infrastructure implementations. The frontend is a separate Vite SPA that communicates with the backend only through HTTP.

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Vue bootstrap | Mount the SPA and load global CSS | `frontend/src/main.ts` |
| Root UI shell | Switch between upload and result views with motion transitions | `frontend/src/App.vue` |
| Upload state machine | Own upload statuses, elapsed timer, file validation, API dispatch, and reset/error transitions | `frontend/src/composables/useUpload.ts` |
| API client | Send multipart uploads to `POST /api/ingest` and parse structured error responses | `frontend/src/api/ingest.ts` |
| Frontend API contract | Mirror backend JSON response shape and upload state union | `frontend/src/types/api.ts` |
| FastAPI app factory | Configure app metadata, CORS, lifespan startup, and module-level uvicorn target | `src/selection_maid/adapters/http/app.py` |
| HTTP router | Define `GET /health` and `POST /ingest`, perform upload validation, tempfile handling, threadpool dispatch, and response conversion | `src/selection_maid/adapters/http/router.py` |
| HTTP schemas | Define Pydantic v2 response schemas that mirror domain dataclasses | `src/selection_maid/adapters/http/schemas.py` |
| HTTP error mapping | Map domain/upload error codes to HTTP status codes | `src/selection_maid/adapters/http/error_map.py` |
| Application service | Run the extraction pipeline and wrap non-domain adapter exceptions | `src/selection_maid/service.py` |
| Domain models | Define frozen dataclasses for `RawInput`, `RawDocument`, `DocumentChunk`, `DocumentMetadata`, and `ExtractionResult` | `src/selection_maid/domain/models.py` |
| Domain ports | Define structural `Protocol` contracts for extractor, filter, chunker, and metadata enricher | `src/selection_maid/domain/ports.py` |
| Error taxonomy | Define `SelectionMaidError` and typed domain error subclasses with stable error codes | `src/selection_maid/errors.py` |
| Config loader | Read `config.toml` via `tomllib`, apply defaults, and expose typed config dataclasses | `src/selection_maid/config.py` |
| Docling extractor | Convert supported files to Markdown-backed `RawDocument` values | `src/selection_maid/adapters/extractor/docling.py` |
| Heuristic filter | Remove repeated headers/footers, page numbers, and excessive whitespace | `src/selection_maid/adapters/filter/heuristic.py` |
| Markdown chunker | Split Markdown by H1/H2 headings or token-budget fallback and emit `DocumentChunk` values | `src/selection_maid/adapters/chunker/markdown.py` |
| Metadata enricher | Derive title, language, document type, counts, UUID, and ingestion timestamp | `src/selection_maid/adapters/enricher/default.py` |

## Pattern Overview

**Overall:** Hexagonal architecture for the backend plus a decoupled Vue SPA frontend.

**Key Characteristics:**
- Keep domain code free of infrastructure dependencies: `src/selection_maid/domain/models.py` uses stdlib dataclasses and `src/selection_maid/domain/ports.py` uses `typing.Protocol`.
- Inject concrete adapters into `ExtractionService` from a single startup wiring point in `src/selection_maid/adapters/http/app.py`.
- Use factory functions for infrastructure construction: `build_docling_adapter`, `build_heuristic_filter`, `build_markdown_chunker`, `build_metadata_enricher`, and `build_router`.
- Keep frontend/backend coupling at the JSON HTTP contract: `frontend/src/types/api.ts` mirrors `src/selection_maid/adapters/http/schemas.py`.
- Use closure injection for FastAPI handlers: `build_router(service, config)` captures dependencies instead of relying on globals or `Depends`.

## Layers

**Frontend Presentation Layer:**
- Purpose: Render upload, processing, error, and result views.
- Location: `frontend/src/App.vue`, `frontend/src/components/upload/`, `frontend/src/components/result/`, `frontend/src/components/ui/`.
- Contains: Vue single-file components, shadcn-vue style primitives, motion-v transitions, Markdown rendering, download actions.
- Depends on: `frontend/src/composables/useUpload.ts`, `frontend/src/types/api.ts`, `frontend/src/lib/`.
- Used by: Browser users through `frontend/src/main.ts`.

**Frontend Application State Layer:**
- Purpose: Coordinate upload workflow as a discriminated-union state machine.
- Location: `frontend/src/composables/useUpload.ts`.
- Contains: `useUpload()`, elapsed timer, state transitions, validation and API orchestration.
- Depends on: `frontend/src/api/ingest.ts`, `frontend/src/api/errors.ts`, `frontend/src/lib/validators.ts`, `frontend/src/types/api.ts`.
- Used by: `frontend/src/App.vue` and `frontend/src/components/upload/DropZone.vue`.

**Frontend API Boundary:**
- Purpose: Translate browser `File` objects into backend requests and backend errors into application errors.
- Location: `frontend/src/api/ingest.ts`, `frontend/src/api/errors.ts`, `frontend/src/types/api.ts`.
- Contains: `postIngest()`, `ApiResponseError`, `mapApiError()`, response interfaces.
- Depends on: Browser `fetch`, `FormData`, and `AbortSignal.timeout`.
- Used by: `frontend/src/composables/useUpload.ts`.

**HTTP Adapter Layer:**
- Purpose: Expose backend use cases over HTTP and isolate FastAPI/Pydantic concerns.
- Location: `src/selection_maid/adapters/http/`.
- Contains: app factory, lifespan, router factory, upload validation, temporary file handling, response schemas, HTTP status mapping.
- Depends on: `fastapi`, `python-magic`, `psutil`, Pydantic schemas, `src/selection_maid/service.py`, and config.
- Used by: uvicorn via `selection_maid.adapters.http.app:app`.

**Application Core Layer:**
- Purpose: Orchestrate the use case without knowing concrete infrastructure.
- Location: `src/selection_maid/service.py`.
- Contains: `ExtractionService.process()` pipeline and adapter exception wrapping.
- Depends on: domain models, domain ports, domain errors.
- Used by: `src/selection_maid/adapters/http/router.py` and tests under `tests/domain/`.

**Domain Layer:**
- Purpose: Define stable data and port contracts.
- Location: `src/selection_maid/domain/`, `src/selection_maid/errors.py`.
- Contains: frozen dataclasses, port `Protocol`s, domain error taxonomy.
- Depends on: Python stdlib only for models/ports; no adapter imports.
- Used by: all backend layers and backend tests.

**Infrastructure Adapter Layer:**
- Purpose: Implement extraction, filtering, chunking, and enrichment behind domain ports.
- Location: `src/selection_maid/adapters/extractor/`, `src/selection_maid/adapters/filter/`, `src/selection_maid/adapters/chunker/`, `src/selection_maid/adapters/enricher/`.
- Contains: concrete adapter classes plus `build_*` factories.
- Depends on: domain models/errors and selected external libraries (`docling`, `tiktoken`, `langdetect`).
- Used by: lifespan wiring in `src/selection_maid/adapters/http/app.py`.

**Configuration Layer:**
- Purpose: Resolve runtime settings from `config.toml` with safe defaults.
- Location: `src/selection_maid/config.py`, `config.toml`.
- Contains: `GlobalConfig`, `FilterConfig`, `ChunkerConfig`, `EnricherConfig`, `HttpConfig`, `get_config()`.
- Depends on: stdlib `tomllib`, `dataclasses`, and `pathlib`.
- Used by: app startup, adapter factories, and tests under `tests/test_config.py`.

## Data Flow

### Primary Request Path

1. The browser renders `frontend/src/App.vue:11` and creates the shared upload controller with `useUpload()` at `frontend/src/App.vue:8`.
2. `frontend/src/components/upload/DropZone.vue` receives a single `File`, rejects multi-file drops, and calls `upload.startUpload(files[0])`.
3. `frontend/src/composables/useUpload.ts:46` validates the `File`, transitions through `uploading` and `processing`, then awaits `postIngest(file)`.
4. `frontend/src/api/ingest.ts` posts multipart form data to `POST /api/ingest`; in development `frontend/vite.config.ts:16` proxies `/api` to `http://localhost:8000` and strips the prefix.
5. FastAPI serves the request through `build_router()` in `src/selection_maid/adapters/http/router.py:86`, where `POST /ingest` is registered at `src/selection_maid/adapters/http/router.py:128`.
6. The HTTP handler validates content length, declared MIME type, and magic bytes at `src/selection_maid/adapters/http/router.py:157`, `src/selection_maid/adapters/http/router.py:171`, and `src/selection_maid/adapters/http/router.py:180`.
7. The handler writes the upload to a restricted temporary file and builds `RawInput` at `src/selection_maid/adapters/http/router.py:217` and `src/selection_maid/adapters/http/router.py:226`.
8. The handler dispatches CPU-bound work via `run_in_threadpool(service.process, raw_input)` at `src/selection_maid/adapters/http/router.py:234`.
9. `ExtractionService.process()` runs extract, filter, chunk, and enrich in sequence at `src/selection_maid/service.py:78`, `src/selection_maid/service.py:86`, `src/selection_maid/service.py:94`, and `src/selection_maid/service.py:102`.
10. The router converts the domain result to `ExtractionResponse` with Pydantic from-attributes validation at `src/selection_maid/adapters/http/router.py:236`.
11. The frontend stores `{ status: 'success', data }` at `frontend/src/composables/useUpload.ts:59`, then `frontend/src/App.vue:51` renders `ResultView`.

### Backend Startup Flow

1. Uvicorn imports the module-level `app` from `src/selection_maid/adapters/http/app.py:123`.
2. `create_app()` configures FastAPI and CORS at `src/selection_maid/adapters/http/app.py:92` and `src/selection_maid/adapters/http/app.py:112`.
3. The lifespan records `app.state.start_time` at `src/selection_maid/adapters/http/app.py:52`.
4. The lifespan imports and constructs Docling's `DocumentConverter` lazily at `src/selection_maid/adapters/http/app.py:59`.
5. `get_config()` resolves `config.toml` at `src/selection_maid/adapters/http/app.py:64`.
6. The lifespan constructs concrete adapters at `src/selection_maid/adapters/http/app.py:67`.
7. The lifespan injects adapters into `ExtractionService` at `src/selection_maid/adapters/http/app.py:73`.
8. The lifespan builds and includes the router at `src/selection_maid/adapters/http/app.py:81`.

**State Management:**
- Backend request state is local to each request except `app.state.start_time` in `src/selection_maid/adapters/http/app.py` and the startup-created adapter/service instances captured by the router closure.
- The Docling adapter serializes converter access with an instance-level `threading.Lock` in `src/selection_maid/adapters/extractor/docling.py`.
- Frontend state is local to `useUpload()` as a readonly Vue `ref` exposed from `frontend/src/composables/useUpload.ts`.

## Key Abstractions

**Domain Value Objects:**
- Purpose: Carry backend data between layers without framework/library coupling.
- Examples: `src/selection_maid/domain/models.py`.
- Pattern: Frozen dataclasses; use `ExtractionResult.chunks` as a tuple for immutable output.

**Port Protocols:**
- Purpose: Define the shape concrete adapters must satisfy.
- Examples: `src/selection_maid/domain/ports.py`.
- Pattern: `typing.Protocol` structural typing; do not require inheritance or runtime `isinstance()` checks.

**Application Service:**
- Purpose: Own the backend use case and protect callers from raw adapter exceptions.
- Examples: `src/selection_maid/service.py`.
- Pattern: Constructor injection of ports; sequential pipeline; wrap unexpected exceptions into `SelectionMaidError` subclasses.

**Adapter Factories:**
- Purpose: Centralize concrete adapter construction and keep app startup readable.
- Examples: `src/selection_maid/adapters/extractor/docling.py`, `src/selection_maid/adapters/filter/heuristic.py`, `src/selection_maid/adapters/chunker/markdown.py`, `src/selection_maid/adapters/enricher/default.py`.
- Pattern: Export `build_*` functions and wire them only from `src/selection_maid/adapters/http/app.py`.

**HTTP Router Closure:**
- Purpose: Keep route handlers testable and free of module-level service/config globals.
- Examples: `src/selection_maid/adapters/http/router.py`.
- Pattern: `build_router(service, config)` returns `APIRouter`; tests can pass mocks or test configs directly.

**Frontend Upload Composable:**
- Purpose: Encapsulate the browser upload state machine away from UI components.
- Examples: `frontend/src/composables/useUpload.ts`.
- Pattern: Return readonly state plus command methods (`startUpload`, `setDragging`, `setError`, `reset`).

## Entry Points

**Backend HTTP Server:**
- Location: `src/selection_maid/adapters/http/app.py`.
- Triggers: `uv run uvicorn selection_maid.adapters.http.app:app --reload`.
- Responsibilities: Create FastAPI app, configure CORS, initialize adapters and service in lifespan, expose module-level `app`.

**Backend Health Endpoint:**
- Location: `src/selection_maid/adapters/http/router.py`.
- Triggers: `GET /health`.
- Responsibilities: Report status, RSS memory, uptime, and package version.

**Backend Ingest Endpoint:**
- Location: `src/selection_maid/adapters/http/router.py`.
- Triggers: `POST /ingest`.
- Responsibilities: Validate upload, save a temporary file, call the extraction service in a threadpool, map errors, clean up tempfiles.

**Frontend SPA:**
- Location: `frontend/src/main.ts`.
- Triggers: Browser loading `frontend/index.html` through Vite or a static build.
- Responsibilities: Mount `frontend/src/App.vue`.

**Frontend API Call:**
- Location: `frontend/src/api/ingest.ts`.
- Triggers: `useUpload().startUpload(file)` from `frontend/src/composables/useUpload.ts`.
- Responsibilities: POST a single file to `/api/ingest`, enforce a 130-second browser timeout, throw `ApiResponseError` for non-2xx responses.

## Architectural Constraints

- **Threading:** FastAPI request handlers are async, but extraction is CPU-bound and must run through `run_in_threadpool` in `src/selection_maid/adapters/http/router.py`. `DoclingAdapter` additionally serializes converter access with a lock in `src/selection_maid/adapters/extractor/docling.py`.
- **Global state:** Backend global state is limited to `app = create_app()` in `src/selection_maid/adapters/http/app.py`, module constants, `app.state.start_time`, and route-closure captures created during lifespan. Frontend module state is limited to constants and component-local/composable-local refs.
- **Circular imports:** Avoid importing `selection_maid.config` at module import time from `src/selection_maid/adapters/filter/heuristic.py`; its factory performs local imports to avoid cycles. Keep new adapter factories cycle-conscious.
- **Domain purity:** Do not import FastAPI, Pydantic, Docling, tiktoken, langdetect, Vue, or frontend code from `src/selection_maid/domain/` or `src/selection_maid/service.py`.
- **Frontend/backend contract:** Keep `frontend/src/types/api.ts`, `src/selection_maid/adapters/http/schemas.py`, and `src/selection_maid/domain/models.py` aligned whenever response fields change.
- **Secrets:** `.env`-style files are not part of the current architecture map. Do not read or quote their contents if added.

## Anti-Patterns

### Infrastructure Imports In The Domain

**What happens:** New domain models or ports import FastAPI, Pydantic, Docling, tiktoken, langdetect, or adapter classes.
**Why it's wrong:** It breaks the dependency direction used by `src/selection_maid/service.py` and makes pure domain tests load infrastructure.
**Do this instead:** Keep contracts in `src/selection_maid/domain/models.py` and `src/selection_maid/domain/ports.py`; put library-specific mapping in `src/selection_maid/adapters/`.

### Route Handlers With Module-Level Services

**What happens:** New routes instantiate or import a concrete `ExtractionService` globally.
**Why it's wrong:** It bypasses the testable closure pattern in `src/selection_maid/adapters/http/router.py` and can trigger heavy adapter startup at import time.
**Do this instead:** Extend `build_router(service, config)` in `src/selection_maid/adapters/http/router.py` or add another router factory that receives dependencies explicitly.

### Frontend Components Owning API Details

**What happens:** Vue components call `fetch()` directly or duplicate backend error handling.
**Why it's wrong:** It spreads API contract logic across presentation files and bypasses `frontend/src/composables/useUpload.ts`.
**Do this instead:** Put request code in `frontend/src/api/`, state transitions in `frontend/src/composables/`, and keep components focused on rendering and user events.

### Import-Time Docling Loading

**What happens:** A backend module imports `docling.document_converter.DocumentConverter` at top level outside the extractor boundary.
**Why it's wrong:** It can load heavy model dependencies when tests or lightweight modules import the package.
**Do this instead:** Keep runtime Docling construction in the lifespan path in `src/selection_maid/adapters/http/app.py` and extractor-specific logic in `src/selection_maid/adapters/extractor/docling.py`.

## Error Handling

**Strategy:** Domain errors carry stable machine-readable codes; HTTP code mapping happens only at the HTTP adapter boundary.

**Patterns:**
- Raise `SelectionMaidError` subclasses from domain/application/adapter code using classes in `src/selection_maid/errors.py`.
- Let existing `SelectionMaidError` instances propagate unchanged in `src/selection_maid/service.py`.
- Wrap unexpected adapter exceptions at each pipeline boundary in `src/selection_maid/service.py`.
- Return structured HTTP errors shaped as `{"error": {"code": "...", "message": "..."}}` from `src/selection_maid/adapters/http/router.py`.
- Map codes to statuses in `src/selection_maid/adapters/http/error_map.py`; do not scatter status-code decisions in adapters.
- Map frontend display messages in `frontend/src/api/errors.ts`; do not surface backend internals directly in UI components.

## Cross-Cutting Concerns

**Logging:** Backend modules use stdlib `logging`, currently in `src/selection_maid/adapters/http/app.py` and `src/selection_maid/adapters/http/router.py`. Log backend operational events and unexpected exceptions at adapter boundaries.

**Validation:** Backend upload validation lives in `src/selection_maid/adapters/http/router.py`; frontend preflight validation lives in `frontend/src/lib/validators.ts`. Keep backend validation authoritative.

**Authentication:** Not detected. `src/selection_maid/adapters/http/router.py` exposes unauthenticated `GET /health` and `POST /ingest`.

**Configuration:** Backend runtime configuration is resolved by `src/selection_maid/config.py` from `config.toml`. Frontend dev proxy configuration is in `frontend/vite.config.ts`.

**Testing Surface:** Backend tests are under `tests/` and mirror domain/adapter layers. Frontend tests are co-located under `frontend/src/**/*.spec.ts` and `frontend/src/components/upload/__tests__/`.

**Project Skills:** Local GSD skills live under `.codex/skills/`. Architecture mapping follows the GSD requirement to keep generated codebase intelligence in `.planning/codebase/` and include actionable file paths for downstream planning/execution.

---

*Architecture analysis: 2026-05-27*
