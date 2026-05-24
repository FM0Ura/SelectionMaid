---
phase: 06-http-api-layer
plan: "03"
subsystem: http-adapter
tags: [fastapi, validation, python-magic, config, error-mapping, tdd]
dependency_graph:
  requires:
    - src/selection_maid/adapters/http/router.py (06-02)
    - src/selection_maid/config.py (03-content-filtering pattern)
    - src/selection_maid/errors.py (domain error taxonomy)
  provides:
    - src/selection_maid/adapters/http/error_map.py
    - HttpConfig dataclass in config.py
    - 3-layer file validation in POST /ingest
  affects:
    - src/selection_maid/adapters/http/router.py (06-04 adds threadpool dispatch)
tech-stack:
  added: []
  patterns:
    - _as_list_str() helper for type-safe TOML list[str] parsing (extends _as_int() pattern)
    - error_map.py as single source of truth for domain-code-to-HTTP-status mapping
    - build_router(service, config) closure pattern with config injected (no globals)
    - Content-Length header checked first (fail fast D-79), then magic bytes after read

key-files:
  created:
    - src/selection_maid/adapters/http/error_map.py
  modified:
    - src/selection_maid/config.py (HttpConfig, _as_list_str, get_config [http] parsing)
    - config.toml ([http] section)
    - src/selection_maid/adapters/http/router.py (3-layer validation, config parameter)
    - src/selection_maid/adapters/http/app.py (pass config to build_router)
    - tests/adapters/http/conftest.py (pass get_config() to build_router)
    - tests/adapters/http/test_router.py (8 new validation tests)

key-decisions:
  - "D-89/D-90: HttpConfig with max_file_bytes=52_428_800 and allowed_mime_types list added to GlobalConfig following same dataclass pattern as FilterConfig/ChunkerConfig"
  - "error_map.py as dedicated module for ERROR_CODE_TO_HTTP dict; router.py imports and re-exports it for backward compat"
  - "build_router() signature extended to (service, config) — config is captured by closure like service, no globals"
  - "Content-Length checked first before reading bytes; magic check uses first 2048 bytes; file.seek(0) resets position for downstream use"
  - "Spoofed file detection: python-magic detects real MIME from bytes; if detected != declared -> 422/UPLOAD-002"

patterns-established:
  - "_as_list_str(value, default): type-safe TOML list[str] helper matching _as_int() pattern"
  - "Validation order in ingest: header check -> declared MIME -> magic bytes -> dispatch (plan 06-04)"
  - "error_map module: single dict + get_http_status() helper; router imports, never re-defines"

requirements-completed: [API-03]

duration: 5min
completed: 2026-05-24
---

# Phase 6 Plan 03: File Validation and HTTP Config Summary

3-layer upload validation (Content-Length / declared MIME type / python-magic bytes) wired into POST /ingest with configurable HttpConfig dataclass, a standalone error_map module, and TDD-verified tests covering all three rejection paths.

## Performance

- **Duration:** ~5 min
- **Started:** 2026-05-24T23:37:19Z
- **Completed:** 2026-05-24T23:42:00Z
- **Tasks:** 3 (Task 3 has RED + GREEN commits)
- **Files modified:** 6

## Accomplishments

- `HttpConfig` dataclass added to `GlobalConfig` with `max_file_bytes=52_428_800` (50MB) and `allowed_mime_types` for PDF/DOCX/HTML; parsed from `[http]` section in `config.toml`
- `error_map.py` created as the single source of truth for all domain error code → HTTP status mappings; router imports from it instead of maintaining a duplicate dict
- 3-layer validation in `POST /ingest`: Content-Length header (413/UPLOAD-001) → declared MIME type (415/EXT-002) → python-magic bytes (422/UPLOAD-002); validation fails fast before any domain processing

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend GlobalConfig with HttpConfig** - `5c997b7` (feat)
2. **Task 2: Implement Error Mapping** - `cce05a4` (feat)
3. **Task 3 RED: Failing validation tests** - `ca4e063` (test)
4. **Task 3 GREEN: 3-layer validation implementation** - `ab81fe4` (feat)

## Files Created/Modified

- `src/selection_maid/config.py` — Added `_as_list_str()` helper, `HttpConfig` dataclass, `GlobalConfig.http` field, `[http]` TOML parsing in `get_config()`
- `config.toml` — Added `[http]` section with `max_file_bytes` and `allowed_mime_types`
- `src/selection_maid/adapters/http/error_map.py` — New: `ERROR_CODE_TO_HTTP` dict + `get_http_status()` helper
- `src/selection_maid/adapters/http/router.py` — 3-layer validation logic; `build_router(service, config)` signature; imports `error_map`
- `src/selection_maid/adapters/http/app.py` — Updated `build_router(service, config)` call
- `tests/adapters/http/conftest.py` — Updated fixture to pass `get_config()` to `build_router()`
- `tests/adapters/http/test_router.py` — Added `TestIngestValidationSize`, `TestIngestValidationMime`, `TestIngestValidationMagic` (8 new tests)

## Decisions Made

- `error_map.py` as a separate file (not inline in `router.py`) per plan spec; router imports and re-exports `_ERROR_CODE_TO_HTTP` as a module-level alias for backward compatibility with any future code referencing it from `router`.
- `build_router()` extended with `config: GlobalConfig` second parameter — config is captured by the `ingest()` closure just like `service`, avoiding globals.
- `file.seek(0)` called after reading magic bytes so the full file is available to the dispatch step in plan 06-04.
- `service` parameter lint hint (unused-parameter) left as-is — it's a hint not an error, and `service` will be used in plan 06-04.

## Deviations from Plan

None — plan executed exactly as written.

The TDD cycle was followed: RED commit (`ca4e063`) with 7 failing + 1 passing test, GREEN commit (`ab81fe4`) with all 12 tests passing. No refactor step needed.

## Issues Encountered

Two pre-existing mypy hints found during type checking (out-of-scope per deviation rules, not caused by this plan's changes):
- `conftest.py:34` — `@asynccontextmanager` generator return type annotation (`AsyncIterator[None]` vs `Generator`) — pre-existing from plan 06-02
- `app.py:67` — `build_heuristic_filter` argument type mismatch — pre-existing from plan 06-02

These are logged in `deferred-items.md` for Phase 6 cleanup.

## TDD Gate Compliance

- RED gate: `ca4e063` — `test(06-03): add failing validation tests for POST /ingest (RED)`
- GREEN gate: `ab81fe4` — `feat(06-03): implement 3-layer validation in POST /ingest (GREEN)`
- REFACTOR: Not needed — implementation was clean from the start.

## Known Stubs

**POST /ingest** still returns 501 after passing all 3 validation layers. The dispatch to `ExtractionService` via `run_in_threadpool` is deferred to plan 06-04. This is intentional — the stub is preserved so plan 06-04 can implement only the dispatch step without touching validation logic.

## Threat Flags

No new threat surface beyond what the plan's threat model describes:
- T-06-03 (DoS via large file): Mitigated — Content-Length header checked before reading bytes; 50MB hard cap enforced.
- T-06-04 (Tampering via spoofed extension): Mitigated — libmagic detects real MIME from bytes regardless of declared content_type.

## Self-Check: PASSED

Files verified:
- `src/selection_maid/adapters/http/error_map.py` — FOUND
- `src/selection_maid/config.py` (HttpConfig) — FOUND
- `config.toml` ([http] section) — FOUND
- `src/selection_maid/adapters/http/router.py` (validation) — FOUND
- `tests/adapters/http/test_router.py` (12 tests) — FOUND

Commits verified:
- `5c997b7` (feat HttpConfig) — FOUND
- `cce05a4` (feat error_map) — FOUND
- `ca4e063` (test RED) — FOUND
- `ab81fe4` (feat GREEN) — FOUND

Test results: 157 passed, 0 failed (full suite excluding Docling integration tests)
