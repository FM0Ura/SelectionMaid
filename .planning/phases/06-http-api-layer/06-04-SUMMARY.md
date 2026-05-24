---
phase: 06-http-api-layer
plan: "04"
subsystem: http-adapter
tags: [fastapi, threadpool, tempfile, run_in_threadpool, concurrency, tdd, integration-tests]
dependency_graph:
  requires:
    - src/selection_maid/adapters/http/router.py (06-02, 06-03)
    - src/selection_maid/adapters/http/error_map.py (06-03)
    - src/selection_maid/adapters/http/schemas.py (06-01)
    - src/selection_maid/domain/models.py (RawInput, ExtractionResult)
    - src/selection_maid/service.py (ExtractionService.process)
    - tests/fixtures/sample.pdf (real PDF for integration tests)
  provides:
    - Fully wired POST /ingest endpoint (threadpool + tempfile + error mapping)
    - Comprehensive test suite: success, error mapping, concurrency (20 tests total)
  affects:
    - tests/adapters/http/test_router.py (final test suite for phase 6)

tech-stack:
  added: []
  patterns:
    - run_in_threadpool(service.process, raw_input) offloads CPU-bound Docling to thread executor
    - NamedTemporaryFile(delete=False, suffix=ext, mode='wb') for 0o600 permissions (T-06-05)
    - os.unlink(tmp_path) in finally block — guaranteed cleanup even on SelectionMaidError
    - ExtractionResponse.model_validate(result, from_attributes=True) for domain->schema conversion
    - httpx.AsyncClient + asyncio.gather for concurrency verification in tests

key-files:
  modified:
    - src/selection_maid/adapters/http/router.py (Task 1: threadpool dispatch + tempfile cleanup)
    - tests/adapters/http/test_router.py (Task 2: 20 tests — success, error mapping, concurrency)

key-decisions:
  - "D-87 implemented: NamedTemporaryFile(delete=False, suffix=ext, mode='wb') with os.unlink() in finally block"
  - "D-88 implemented: await run_in_threadpool(service.process, raw_input) offloads Docling to thread executor"
  - "_MIME_TO_EXT dict defined at module level (not per-request) — avoids re-creation on every call"
  - "Non-domain exceptions caught by bare except clause -> mapped to 500/EXT-001 to prevent unhandled 500s leaking"
  - "Concurrency test uses httpx.AsyncClient + ASGITransport with routes included before app start (not inside lifespan)"
  - "test_validation_magic_real_pdf_passes_all_layers updated from 501 stub expectation to 200 with mock service return"

requirements-completed: [API-01, API-02, API-03, ARCH-05]

duration: 8min
completed: 2026-05-24
---

# Phase 6 Plan 04: Threading, Tempfiles, and Integration Tests Summary

POST /ingest fully wired with `run_in_threadpool` dispatch (D-88), `NamedTemporaryFile` lifecycle with guaranteed `os.unlink()` cleanup (D-87, T-06-05), and a 20-test suite covering success path, error mapping, and concurrent request handling.

## Performance

- **Duration:** ~8 min
- **Completed:** 2026-05-24
- **Tasks:** 2
- **Files modified:** 2
- **Tests:** 20 (HTTP adapter suite) / 165 (full suite excl. Docling integration)

## Accomplishments

- `POST /ingest` dispatch fully implemented: `ExtractionService.process()` runs in the asyncio thread executor via `run_in_threadpool`, keeping the event loop unblocked for concurrent requests
- Upload bytes written to `tempfile.NamedTemporaryFile(delete=False, suffix=ext, mode='wb')` — `mode='wb'` ensures `0o600` permissions on Linux (T-06-05 mitigated); `delete=False` + `finally`-block `os.unlink()` guarantees cleanup even on `SelectionMaidError`
- `ExtractionResult` converted to `ExtractionResponse` via `model_validate(result, from_attributes=True)` — no manual field mapping
- MIME-to-extension mapping (`_MIME_TO_EXT`) defined at module level so it is not re-created on every request
- 20 tests covering: 4 health, 2 size validation, 3 MIME validation, 3 magic bytes, 4 success path, 3 error mapping, 1 concurrency

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement /ingest with Threading and Tempfiles** - `9a8a2e0` (feat)
2. **Task 2: Expand Integration and Concurrency Tests** - `d891724` (feat)

## Files Created/Modified

- `src/selection_maid/adapters/http/router.py` — Replaced `NotImplementedError` stub with threadpool dispatch, tempfile lifecycle, `ExtractionResponse` serialization, and error catch-all; added `_MIME_TO_EXT` module constant; added imports: `os`, `tempfile`, `Path`, `run_in_threadpool`, `RawInput`
- `tests/adapters/http/test_router.py` — Full rewrite expanding from 12 to 20 tests; added `_make_extraction_result()` and `_real_pdf_bytes()` helpers; updated `test_validation_magic_real_pdf_passes_all_layers` to use mock service; added `TestIngestSuccess` (4 tests), `TestIngestErrorMapping` (3 tests), `TestIngestConcurrency` (1 test)

## Decisions Made

- `_MIME_TO_EXT` dict at module level rather than inside the handler closure — avoids dict construction on every request
- Non-`SelectionMaidError` exceptions caught by `except Exception` in the dispatch block and re-mapped to `EXT-001 / 500` — prevents raw Python tracebacks from leaking to clients while still logging the original exception via `logger.exception`
- Concurrency test builds the router before `FastAPI()` instantiation and calls `app.include_router()` at app creation time — routes must be registered before `ASGITransport` resolves them, not inside lifespan
- `NamedTemporaryFile(mode='wb')` chosen over `mode='w+b'` (default) for clarity of write-only intent; `os.unlink()` in `finally` is separated from the `with` block so the file is already closed (and flushed) when the path is passed to `service.process()`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test stub expectation from 501 to 200 with mock**
- **Found during:** Task 2 test run
- **Issue:** `test_validation_magic_real_pdf_passes_magic_check` (from plan 06-03) expected HTTP 501 (the stub) but after Task 1 implementation the real dispatch runs and requires a properly configured mock service
- **Fix:** Renamed test to `test_validation_magic_real_pdf_passes_all_layers`; added `mock_service.process.return_value = _make_extraction_result()` and changed assertion to `200`
- **Files modified:** `tests/adapters/http/test_router.py`
- **Commit:** `d891724`

**2. [Rule 1 - Bug] Fixed concurrency test 404 — routes must be registered before app start**
- **Found during:** Task 2 initial write
- **Issue:** First version of `test_ingest_concurrency_two_requests` called `app.include_router(router)` inside the lifespan `yield` block. FastAPI's ASGI routing layer is frozen at transport init; routes added in lifespan startup are too late, causing 404 for all `/ingest` requests
- **Fix:** Moved `router = build_router(...)` and `app.include_router(router)` before `FastAPI(lifespan=...)` instantiation; lifespan only sets `app.state.start_time`
- **Files modified:** `tests/adapters/http/test_router.py`
- **Commit:** `d891724`

## TDD Gate Compliance

The plan's Task 2 had `tdd="true"`. Due to the plan structure (Task 1 = implementation, Task 2 = tests), tests were written after the implementation was committed in Task 1. When the tests were first run, all 20 passed immediately (GREEN without a RED gate).

This is an acceptable deviation for integration/behavioral tests written against an already-complete implementation — the tests still provide regression coverage. A strict RED-GREEN cycle would require writing tests before Task 1, which contradicts the plan's sequential task ordering.

No separate RED commit was made because there was no failing state to capture — the implementation was already correct.

## Known Stubs

None. All stubs from prior plans have been resolved:
- `POST /ingest` no longer returns 501; it dispatches to `ExtractionService` via `run_in_threadpool` and returns `ExtractionResponse` with full chunk and metadata content.

## Threat Flags

No new threat surface beyond the plan's threat model:
- T-06-05 (Information Disclosure via tempfiles): Mitigated — `NamedTemporaryFile(mode='wb')` creates files with `0o600` permissions; `os.unlink()` in `finally` block guarantees deletion; verified by `test_ingest_success_tempfile_cleaned_up` and post-test check of `/tmp/tmp*.pdf` (0 files remaining).

## Self-Check: PASSED

Files verified:
- `src/selection_maid/adapters/http/router.py` (threadpool dispatch) — FOUND
- `tests/adapters/http/test_router.py` (20 tests) — FOUND

Commits verified:
- `9a8a2e0` (feat threadpool + tempfile) — FOUND
- `d891724` (feat expanded tests) — FOUND

Test results: 165 passed, 0 failed (full suite excluding Docling integration tests)
No tempfiles left in /tmp after test run: verified (0 matches for /tmp/tmp*.pdf)
