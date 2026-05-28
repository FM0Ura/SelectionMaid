<!-- generated-by: gsd-doc-writer -->
# Development Guide

This document covers the local development workflow for SelectionMaid: setup, build commands, code style enforcement, and the conventions that govern contributions.

See [GETTING-STARTED.md](GETTING-STARTED.md) for prerequisites and first-run instructions.

---

## Local Setup

1. Clone the repository and enter the project directory:

```bash
git clone <repository-url>
cd SelectionMaid
```

2. Install all dependencies (runtime + dev group) using uv:

```bash
uv sync
```

`uv sync` reads `pyproject.toml` and installs the `[dependency-groups] dev` group automatically. This includes ruff, mypy, pytest, pytest-asyncio, httpx, and anyio.

3. Copy the sample configuration file so the service has its defaults:

```bash
cp config.toml config.toml  # config.toml is already present; no .env.example needed
```

The service reads `config.toml` from the current working directory at startup. If the file is absent, all adapters fall back to their hardcoded defaults — startup does not fail.

4. Start the development server:

```bash
uv run uvicorn selection_maid.adapters.http.app:app --reload
```

The `--reload` flag watches `src/` for changes. On startup, the lifespan context manager loads the Docling `DocumentConverter` and wires all adapters; this takes several seconds on first run due to AI model initialisation.

**Optional — Frontend SPA:** Install and start the Vite dev server (port 5173) alongside the backend:

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api/*` requests to `http://localhost:8000`, so the backend must also be running.

---

## Build Commands

### Backend

| Command | Description |
|---|---|
| `uv sync` | Install all dependencies including the dev group |
| `uv run uvicorn selection_maid.adapters.http.app:app --reload` | Start the development server with hot reload |
| `uv run pytest` | Run the full test suite |
| `uv run pytest -m "not slow"` | Run tests excluding slow (Docling model-loading) tests |
| `uv run ruff check src/ tests/` | Lint source and test files |
| `uv run ruff format src/ tests/` | Auto-format source and test files |
| `uv run mypy src/` | Run static type checking (strict mode) |

### Frontend

All frontend commands are run from the `frontend/` directory.

| Command | Description |
|---|---|
| `npm install` | Install frontend dependencies |
| `npm run dev` | Start the Vite dev server on port 5173 (with API proxy) |
| `npm run build` | Type-check with vue-tsc then produce a production build in `frontend/dist/` |
| `npm run preview` | Preview the production build locally |
| `npm run test:unit` | Run unit tests with Vitest (jsdom environment) |
| `npm run test:ui` | Run Vitest with the browser-based UI |

---

## Code Style

### Backend (ruff + mypy)

**Linter and formatter:** [ruff](https://docs.astral.sh/ruff/) — replaces black, isort, and flake8 in a single tool. Configuration lives in `pyproject.toml` under `[tool.ruff]` and `[tool.ruff.lint]`.

Active rule sets:

| Code | Ruleset |
|---|---|
| `E` | pycodestyle errors |
| `F` | Pyflakes |
| `I` | isort (import ordering) |
| `UP` | pyupgrade |
| `B` | flake8-bugbear |
| `SIM` | flake8-simplify |

Line length is 88 characters, target version is `py313`.

**Type checker:** [mypy](https://mypy.readthedocs.io/) in `strict = true` mode. Configuration is in `[tool.mypy]`. Tests are excluded from mypy (`exclude = ["tests/"]`). The `langdetect` module has `ignore_missing_imports = true` because it lacks type stubs.

Run both before submitting a pull request:

```bash
uv run ruff check src/ tests/
uv run mypy src/
```

**Editor config:** No `.editorconfig` is present. Rely on ruff for all formatting.

### Frontend (vue-tsc)

**Type checker:** `vue-tsc` is the TypeScript compiler for Vue SFCs. The `build` script runs a full type-check as part of the build (`vue-tsc -b && vite build`). To check types without building:

```bash
cd frontend
npx vue-tsc --noEmit
```

There is no separate ESLint configuration file present in `frontend/`. TypeScript strict mode (configured in `tsconfig.app.json`) is the primary correctness gate; `vue-tsc` catches type errors in both `.ts` files and `<script setup>` blocks.

---

## Architecture Conventions

### Backend (Hexagonal Architecture)

SelectionMaid uses hexagonal architecture (Ports & Adapters). The following rules are not negotiable:

#### Domain isolation

The `src/selection_maid/domain/` package (`models.py`, `ports.py`) must have **zero imports** from infrastructure, adapters, or any third-party library. Only stdlib and other domain modules are allowed.

#### Structural typing — no inheritance

Port adapters satisfy their Protocol via **structural typing** — duck typing, not subclassing. An adapter that implements the correct method signature automatically satisfies the Protocol. Do not inherit from `ExtractorPort`, `FilterPort`, `ChunkerPort`, or `MetadataEnricherPort`.

#### Factory functions

Every adapter must expose a factory function named `build_<adapter>(config) -> <AdapterClass>`. Existing factories:

| Factory | Module |
|---|---|
| `build_docling_adapter(converter)` | `adapters/extractor/docling.py` |
| `build_heuristic_filter(config)` | `adapters/filter/heuristic.py` |
| `build_markdown_chunker(config)` | `adapters/chunker/markdown.py` |
| `build_metadata_enricher(config)` | `adapters/enricher/default.py` |
| `build_router(service, config)` | `adapters/http/router.py` |

#### Docling import isolation

`docling.*` imports may only appear inside `adapters/extractor/docling.py`. All other modules that reference Docling types must use a `TYPE_CHECKING` guard:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from docling.document_converter import DocumentConverter
```

This prevents torch model loading on module import.

#### Configuration injection

Configuration values are injected into adapters via their constructors. Adapter classes must never call `get_config()` internally. `get_config()` is called once in the lifespan context manager in `app.py` and the resulting `GlobalConfig` sections are passed to each factory.

#### Value objects

All domain value objects (`RawInput`, `RawDocument`, `DocumentChunk`, `DocumentMetadata`, `ExtractionResult`) are frozen dataclasses. Do not add mutable fields.

#### Exception wrapping

- Adapters raise `SelectionMaidError` subclasses (`ExtractionError`, `FilterError`, `ChunkingError`, `EnrichmentError`, `UnsupportedFormatError`, `ExtractionTimeoutError`).
- `ExtractionService.process()` wraps any non-domain exception raised by an adapter in the appropriate domain error subclass (decision D-16). Callers of `process()` only ever see `SelectionMaidError` subclasses.

### Frontend (Vue 3 SPA)

#### Component authoring

All components use the Vue 3 Composition API with `<script setup>` SFCs. The Options API and the `defineComponent()` wrapper form are not used.

#### State management

The application uses a single `useUpload` composable (`src/composables/useUpload.ts`) as the central state owner. **No Pinia** — the composable's `readonly` refs are passed as props or provided via Vue's `provide/inject` where needed.

#### HTTP requests

All API calls go through the `src/api/` module using the **native `fetch` API**. No Axios or any other HTTP client library is used. The Vite dev server proxies `/api/*` to the backend at `http://localhost:8000`.

#### Animations

[motion-v](https://motion.dev/vue) is used exclusively for **transform and opacity transitions** (enter/leave, layout shifts). Do not use it for color, size, or other CSS property animations — use Tailwind CSS transitions for those.

#### shadcn-vue and UI primitives

Base UI components (`Button`, `Card`, `Alert`, `Skeleton`) are sourced from [shadcn-vue](https://www.shadcn-vue.com/) and live in `src/components/ui/`. Do not modify these files directly; re-generate them with the shadcn-vue CLI if an upstream update is needed.

---

## Source Layout

### Backend source tree

```
src/selection_maid/
  domain/          # models.py, ports.py — zero infrastructure imports
  adapters/
    extractor/     # DoclingAdapter — sole location for docling.* runtime imports
    filter/        # HeuristicFilter — stdlib-only, no docling dependency
    chunker/       # MarkdownChunker — tiktoken-based; cl100k_base encoding
    enricher/      # MetadataEnricher — langdetect-based language detection
    http/          # app.py, router.py, schemas.py, error_map.py
  config.py        # GlobalConfig, get_config() — reads config.toml
  service.py       # ExtractionService — pipeline orchestration
  errors.py        # SelectionMaidError hierarchy
```

### Frontend source tree

```
frontend/src/
  api/             # ingest.ts — fetch wrapper for POST /api/ingest; errors.ts — ApiResponseError
  composables/     # useUpload.ts — upload state machine (idle → uploading → processing → success/error)
  components/
    upload/        # DropZone, DropOverlay, ProcessingCard, ErrorBanner, SkeletonChunk
    result/        # ResultView, ChunkCard, MetadataCard, MarkdownRenderer
    ui/            # shadcn-vue primitives: Button, Card, Alert, Skeleton
  types/           # api.ts — TypeScript interfaces for ExtractionResponse, Chunk, DocumentMetadata, UploadState
  lib/             # utils.ts — shadcn cn() helper; formatters.ts — date/size formatting; validators.ts — file validation
  assets/          # Static assets (CSS, images)
  main.ts          # Vue app entry point
  App.vue          # Root component
```

---

## Adding a New Adapter

1. Identify the relevant Port protocol in `src/selection_maid/domain/ports.py`:
   - `ExtractorPort` — `extract(document: RawInput) -> RawDocument`
   - `FilterPort` — `filter(document: RawDocument) -> RawDocument`
   - `ChunkerPort` — `chunk(content: str) -> list[DocumentChunk]`
   - `MetadataEnricherPort` — `enrich(raw: RawDocument, chunks: list[DocumentChunk]) -> DocumentMetadata`

2. Implement the method signature exactly. No inheritance required.

3. Create a factory function `build_<name>(config) -> <AdapterClass>` in the same module.

4. Wire it in `app.py` lifespan: pass the factory result into `ExtractionService(...)` in place of the adapter being replaced.

5. No changes to `domain/` are required.

---

## Branch Conventions

No branch naming convention is documented. A conventional approach is:

- `feat/<short-description>` for new features
- `fix/<short-description>` for bug fixes
- `chore/<short-description>` for maintenance tasks

The default branch is `master`.

---

## PR Process

No pull request template is present. Follow these steps when submitting a PR:

- Ensure `uv run ruff check src/ tests/` passes with no errors.
- Ensure `uv run mypy src/` passes with no errors.
- Ensure `uv run pytest` passes in full.
- For frontend changes, ensure `npm run build` (which includes vue-tsc) passes without errors and `npm run test:unit` passes.
- Keep PRs focused on a single concern. Reference relevant decision records (D-XX) in the PR description when changing architecture decisions.
- New adapters must be covered by unit tests that mock the port boundary. Integration tests that invoke real Docling are marked `@pytest.mark.slow`.
