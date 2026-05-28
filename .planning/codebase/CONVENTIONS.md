# Coding Conventions

**Analysis Date:** 2026-05-27

## Naming Patterns

**Files:**
- Backend source uses lowercase snake_case module files under `src/selection_maid/`, for example `src/selection_maid/service.py`, `src/selection_maid/config.py`, and `src/selection_maid/adapters/http/error_map.py`.
- Backend tests use `test_*.py` names and mirror package layers under `tests/`, for example `tests/domain/test_service.py`, `tests/adapters/http/test_router.py`, and `tests/adapters/chunker/test_markdown_chunker.py`.
- Frontend source uses PascalCase for Vue components (`frontend/src/components/upload/DropZone.vue`, `frontend/src/components/result/MarkdownRenderer.vue`), camelCase composables/utilities (`frontend/src/composables/useUpload.ts`, `frontend/src/lib/validators.ts`), and `.spec.ts` tests (`frontend/src/api/ingest.spec.ts`).
- Component-local frontend tests are either colocated beside the component (`frontend/src/components/result/ChunkCard.spec.ts`) or placed in `__tests__/` for upload components (`frontend/src/components/upload/__tests__/DropZone.spec.ts`).

**Functions:**
- Backend functions and methods use snake_case, for example `process()` in `src/selection_maid/service.py`, `get_config()` in `src/selection_maid/config.py`, and `build_router()` in `src/selection_maid/adapters/http/router.py`.
- Backend private helpers use a leading underscore, for example `_as_int()` and `_as_list_str()` in `src/selection_maid/config.py`, `_error_response()` in `src/selection_maid/adapters/http/router.py`, and `_ensure_fixture()` in `tests/conftest.py`.
- Frontend exported functions use camelCase, for example `useUpload()` in `frontend/src/composables/useUpload.ts`, `postIngest()` in `frontend/src/api/ingest.ts`, and `validateFile()` in `frontend/src/lib/validators.ts`.
- Vue composables use the `use*` prefix and return readonly reactive state plus command functions, as in `frontend/src/composables/useUpload.ts`.

**Variables:**
- Backend constants use uppercase snake_case at module scope, for example `_MAGIC_READ_BYTES`, `_MIME_TO_EXT`, and `_ERROR_CODE_TO_HTTP` in `src/selection_maid/adapters/http/router.py`.
- Backend instance attributes that hold injected dependencies use a leading underscore, for example `self._extractor`, `self._filter`, `self._chunker`, and `self._enricher` in `src/selection_maid/service.py`.
- Frontend constants use uppercase snake_case for module-level invariants, for example `MAX_FILE_BYTES` and `ALLOWED_MIME_TYPES` in `frontend/src/lib/validators.ts`.
- Frontend reactive values use direct domain names (`state`, `elapsedSeconds`, `isOverDropZone`) and mocked function variables end in `Mock` (`postIngestMock`, `mapApiErrorMock`) in `frontend/src/composables/useUpload.spec.ts`.

**Types:**
- Backend domain data structures use PascalCase dataclasses, for example `RawInput`, `RawDocument`, `DocumentChunk`, `DocumentMetadata`, and `ExtractionResult` in `src/selection_maid/domain/models.py`.
- Backend port contracts use PascalCase names ending in `Port`, for example `ExtractorPort`, `FilterPort`, `ChunkerPort`, and `MetadataEnricherPort` in `src/selection_maid/domain/ports.py`.
- Backend errors use PascalCase names ending in `Error`, for example `SelectionMaidError`, `ExtractionError`, and `UnsupportedFormatError` in `src/selection_maid/errors.py`.
- Frontend domain API types use PascalCase and live in `frontend/src/types/api.ts`; import them with `import type`, as in `frontend/src/api/ingest.ts` and `frontend/src/composables/useUpload.ts`.

## Code Style

**Formatting:**
- Backend formatting is managed by ruff with `line-length = 88` and `target-version = "py313"` in `pyproject.toml`.
- Use `uv run ruff format src tests` for backend formatting; this is documented in `README.md` and `docs/DEVELOPMENT.md`.
- Frontend code uses the existing Vite/Vue style: 2-space indentation, single quotes, no semicolons, trailing commas in multiline calls/objects, and `<script setup lang="ts">` before `<template>` in Vue SFCs such as `frontend/src/App.vue`.
- No `.prettierrc`, `.eslintrc*`, `eslint.config.*`, or `biome.json` file is present. Preserve existing TypeScript/Vue formatting when editing frontend files.

**Linting:**
- Backend linting uses ruff configured in `pyproject.toml`.
- Ruff selected rule groups are `E`, `F`, `I`, `UP`, `B`, and `SIM`; imports are sorted with `known-first-party = ["selection_maid"]`.
- Backend type checking uses mypy `strict = true` with `python_version = "3.13"` in `pyproject.toml`; `tests/` is excluded from mypy.
- Frontend linting is not configured. Frontend verification relies on `npm run build` for `vue-tsc -b` plus Vite build, and `npm run test:unit` for Vitest tests in `frontend/package.json`.

## Import Organization

**Order:**
1. Future annotations first in Python modules: `from __future__ import annotations` appears in files such as `src/selection_maid/service.py`, `src/selection_maid/config.py`, and `tests/domain/test_service.py`.
2. Python stdlib imports follow, then third-party imports, then first-party `selection_maid` imports, then test helpers. Example: `tests/domain/test_service.py` imports `uuid`/`Path`, then `pytest`, then `selection_maid.*`, then `tests.stubs.adapters`.
3. TypeScript imports place framework/external imports first, then `@/` alias imports, then relative imports. Example: `frontend/src/composables/useUpload.spec.ts` imports Vitest/Vue, then `@/api/*` and `@/types/*`, then `./useUpload`.
4. Use type-only imports for types in TypeScript, for example `import type { ExtractionResponse } from '@/types/api'` in `frontend/src/api/ingest.spec.ts`.

**Path Aliases:**
- Frontend uses `@/*` for `frontend/src/*`, configured in `frontend/tsconfig.json`, `frontend/vite.config.ts`, and `frontend/vitest.config.ts`.
- Backend imports use installed-package absolute imports from `selection_maid.*`, for example `from selection_maid.domain.models import RawInput` in `src/selection_maid/adapters/http/router.py`.
- Tests import reusable backend stubs from `tests.stubs.adapters`, for example `tests/domain/test_service.py`.

## Error Handling

**Patterns:**
- Domain-level errors inherit from `SelectionMaidError` in `src/selection_maid/errors.py` and expose a stable `code`, `message`, and optional `cause`.
- Application service boundaries catch `SelectionMaidError` and re-raise unchanged, then wrap unknown adapter exceptions in typed domain errors with `raise ... from e`, as in `src/selection_maid/service.py`.
- Adapter code should translate infrastructure failures into domain errors. Examples include `src/selection_maid/adapters/extractor/docling.py`, `src/selection_maid/adapters/filter/heuristic.py`, and `src/selection_maid/adapters/chunker/markdown.py`.
- HTTP handlers return structured JSON errors through `_error_response()` with `{"error": {"code": code, "message": message}}` in `src/selection_maid/adapters/http/router.py`.
- Frontend API calls throw `ApiResponseError` for non-2xx responses and parse either structured `error.message` or FastAPI `detail`, as in `frontend/src/api/ingest.ts`.
- Frontend UI state converts thrown values into display text through `mapApiError()` before setting `{ status: 'error', message }` in `frontend/src/composables/useUpload.ts`.

## Logging

**Framework:** Python `logging`; frontend uses minimal `console.warn`.

**Patterns:**
- Backend modules create module loggers with `logging.getLogger(__name__)`, as in `src/selection_maid/adapters/http/router.py` and `src/selection_maid/adapters/http/app.py`.
- Use `logger.info()` for app lifecycle events in `src/selection_maid/adapters/http/app.py`.
- Use `logger.error()` for expected domain or validation failures and `logger.exception()` for unexpected exceptions in `src/selection_maid/adapters/http/router.py`.
- Use `logger.warning()` for non-fatal cleanup failures, for example tempfile deletion failures in `src/selection_maid/adapters/http/router.py`.
- Frontend logging is limited; `frontend/src/components/result/ChunkCard.vue` uses `console.warn('Clipboard copy failed')` for a non-fatal browser API failure.

## Comments

**When to Comment:**
- Backend modules commonly include module docstrings that state architectural decisions and behavior, for example `src/selection_maid/service.py`, `src/selection_maid/domain/models.py`, and `src/selection_maid/adapters/http/router.py`.
- Use comments to mark non-obvious decision constraints, validation layers, compatibility aliases, and resource cleanup requirements, as in `_MAGIC_MIME_ALIASES` and the upload tempfile block in `src/selection_maid/adapters/http/router.py`.
- Keep short inline comments when they clarify type narrowing or intentional fallbacks, for example `return list(value)  # narrow type for mypy` in `src/selection_maid/config.py`.
- Avoid comments for ordinary assignments or simple control flow; most straightforward functions in `frontend/src/lib/validators.ts` and `frontend/src/api/ingest.ts` are self-explanatory without comments.

**JSDoc/TSDoc:**
- Backend uses Python docstrings for public classes, methods, dataclasses, fixtures, and helpers. Follow the Args/Returns/Raises style used in `src/selection_maid/service.py` and `src/selection_maid/config.py`.
- Frontend does not use JSDoc/TSDoc in current source. Prefer explicit TypeScript types and readable names over adding documentation comments unless behavior is non-obvious.

## Function Design

**Size:** Keep domain value objects and pure helpers small. Larger orchestrators are acceptable where they encode a full boundary workflow, for example `build_router()` in `src/selection_maid/adapters/http/router.py` and `useUpload()` in `frontend/src/composables/useUpload.ts`.

**Parameters:** Backend service and router construction uses dependency injection through constructor/factory parameters (`ExtractionService.__init__()` in `src/selection_maid/service.py`, `build_router(service, config)` in `src/selection_maid/adapters/http/router.py`). Vue components use typed `defineProps`/`defineEmits`, as in `frontend/src/components/result/MarkdownRenderer.vue` and `frontend/src/components/upload/ErrorBanner.vue`.

**Return Values:** Backend domain transformations return dataclasses or typed domain errors, not raw dicts. HTTP adapters return Pydantic schema responses or `JSONResponse` at the boundary. Frontend composables return readonly refs and action functions; API clients return typed promises such as `Promise<ExtractionResponse>` in `frontend/src/api/ingest.ts`.

## Module Design

**Exports:** Backend modules export named classes/functions directly; use explicit imports from concrete module paths such as `selection_maid.service.ExtractionService`. Frontend modules use named exports for utilities/composables (`validateFile`, `postIngest`, `useUpload`) and default Vue component exports via SFCs.

**Barrel Files:** Backend and frontend use small barrel files for package/component surfaces. Examples include `src/selection_maid/adapters/filter/__init__.py`, `src/selection_maid/adapters/chunker/__init__.py`, `frontend/src/components/ui/button/index.ts`, and `frontend/src/components/ui/card/index.ts`. Keep barrels narrow and avoid routing substantial logic through them.

---

*Convention analysis: 2026-05-27*
