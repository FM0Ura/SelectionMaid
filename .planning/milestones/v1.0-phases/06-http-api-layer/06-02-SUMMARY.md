---
phase: 06-http-api-layer
plan: "02"
subsystem: http-adapter
tags: [fastapi, router, lifespan, psutil, health-endpoint, test-infrastructure]
dependency_graph:
  requires:
    - src/selection_maid/adapters/http/schemas.py (06-01)
    - src/selection_maid/service.py
    - src/selection_maid/adapters/extractor/docling.py
    - src/selection_maid/adapters/filter/heuristic.py
    - src/selection_maid/adapters/chunker/markdown.py
    - src/selection_maid/adapters/enricher/default.py
  provides:
    - src/selection_maid/adapters/http/router.py
    - src/selection_maid/adapters/http/app.py
    - tests/adapters/http/conftest.py
  affects:
    - src/selection_maid/adapters/http/router.py (06-03 adds file validation)
    - src/selection_maid/adapters/http/router.py (06-04 adds dispatch logic)
tech_stack:
  added:
    - fastapi>=0.136.3
    - uvicorn>=0.48.0
    - python-multipart>=0.0.29
    - psutil>=7.2.2
    - python-magic>=0.4.27
  patterns:
    - asynccontextmanager lifespan pattern (NOT deprecated on_event)
    - build_router(service) closure pattern — no globals, no Depends
    - Deferred Docling import inside lifespan to avoid eager torch model loading
    - TestClient fixture with lightweight test lifespan (no Docling loading in unit tests)
    - MagicMock(spec=ExtractionService) for unit test isolation
key_files:
  created:
    - src/selection_maid/adapters/http/router.py
    - src/selection_maid/adapters/http/app.py
    - tests/adapters/http/conftest.py
    - tests/adapters/http/test_router.py
  modified:
    - pyproject.toml (added 5 HTTP dependencies)
    - uv.lock (updated)
decisions:
  - "D-83: app.py contains create_app() -> FastAPI and module-level app = create_app() for uvicorn"
  - "D-84: asynccontextmanager lifespan builds DocumentConverter singleton and wires all adapters"
  - "D-85: build_router(service) closure pattern — handlers capture service without globals or Depends"
  - "D-86: app.state.start_time set in lifespan; GET /health reads it for uptime_seconds"
  - "D-78: HealthResponse fields verified: status='ok', rss_mb (psutil), uptime_seconds, version (importlib.metadata)"
  - "Test lifespan skips Docling loading for fast unit tests; integration tests deferred to Phase 7"
requirements_completed: [API-01, API-02, ARCH-05]
metrics:
  duration: "~2 minutes"
  start_time: "2026-05-24T23:32:23Z"
  completed_date: "2026-05-24"
  completed_time: "2026-05-24T23:35:00Z"
  tasks_completed: 4
  files_created: 4
  files_modified: 2
  tests_added: 4
  tests_passing: 17
---

# Phase 6 Plan 02: FastAPI Router Factory and App Wiring Summary

FastAPI HTTP adapter wired with `build_router(service)` closure factory, `create_app()` with asynccontextmanager lifespan that bootstraps DocumentConverter singleton and all port adapters, plus TestClient fixture with mocked service for fast unit tests.

## What Was Built

### Task 1: Dependencies installed
Added to `pyproject.toml` and `uv.lock`:
- `fastapi>=0.136.3` — HTTP framework
- `uvicorn>=0.48.0` — ASGI server
- `python-multipart>=0.0.29` — multipart form parsing for UploadFile
- `psutil>=7.2.2` — RSS memory metrics for /health
- `python-magic>=0.4.27` — magic bytes MIME detection (used in 06-03)

### Task 2: Router factory (`router.py`)
`build_router(service: ExtractionService) -> APIRouter` using closure pattern (D-85):
- `GET /health` — returns `HealthResponse` with `rss_mb` (psutil), `uptime_seconds` (from `request.app.state.start_time`), `version` (importlib.metadata)
- `POST /ingest` — skeleton with HTTP 501 stub (full implementation in 06-03/06-04)
- `_ERROR_CODE_TO_HTTP` dict mapping domain error codes to HTTP status codes (D-82)

### Task 3: App factory (`app.py`)
`create_app() -> FastAPI` with `_lifespan` asynccontextmanager (D-84):
- Sets `app.state.start_time = datetime.now(timezone.utc)` (D-86)
- Deferred `from docling.document_converter import DocumentConverter` inside lifespan to avoid eager torch model loading at import time
- Wires `DoclingAdapter`, `HeuristicFilter`, `MarkdownChunker`, `MetadataEnricher`
- Calls `build_router(service)` and `app.include_router(router)` inside lifespan
- Module-level `app = create_app()` for uvicorn entry point

### Task 4: Test infrastructure
- `tests/adapters/http/conftest.py` — `client` fixture with lightweight test lifespan (sets `start_time`, wires mock router — no Docling loading)
- `tests/adapters/http/test_router.py` — 4 tests for `GET /health`: HTTP 200, schema fields (status/rss_mb/uptime_seconds/version), content-type, no extra fields

## Verification Results

```
$ pytest tests/adapters/http/test_router.py -v
4 passed in 0.06s

$ curl http://127.0.0.1:8001/health
{"status":"ok","rss_mb":864.703125,"uptime_seconds":7.671579,"version":"0.1.0"}
```

All success criteria met:
- `router.py` and `app.py` implemented
- 5 HTTP dependencies installed
- `GET /health` returns valid JSON with rss_mb and version (confirmed live + via tests)
- `pytest tests/adapters/http/test_router.py` passes (4/4)

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Install dependencies | 2b9e2b2 | pyproject.toml, uv.lock |
| 2 | Router factory with endpoints | 2ddbdad | router.py |
| 3 | App factory and lifespan | fc5cd8b | app.py |
| 4 | Test infrastructure | 08aaabe | conftest.py, test_router.py |

## Deviations from Plan

None — plan executed exactly as written.

All four tasks completed without auto-fixes. The test lifespan approach (fixture creates a lightweight FastAPI app with mocked service instead of using the real `app` from `app.py`) was the natural implementation of the plan's intent — no deviation.

## Known Stubs

**POST /ingest** in `router.py` returns HTTP 501 with `{"error": {"code": "NOT-IMPL", "message": "..."}}`. This is intentional — the plan states "skeleton accepting `file: UploadFile`. Implementation details follow in later plans." Plans 06-03 (file validation) and 06-04 (service dispatch) will complete this endpoint.

## Threat Flags

No new threat surface introduced beyond what the plan's threat model describes. T-06-02 (DoS on /health via expensive psutil calls) is mitigated: the health handler uses a single `psutil.Process().memory_info().rss` call which is O(1) and reads from `/proc/self/status` on Linux — negligible overhead per request.

## Self-Check: PASSED

Files verified:
- `src/selection_maid/adapters/http/router.py` — FOUND
- `src/selection_maid/adapters/http/app.py` — FOUND
- `tests/adapters/http/conftest.py` — FOUND
- `tests/adapters/http/test_router.py` — FOUND

Commits verified:
- `2b9e2b2` (chore) — FOUND (dependencies)
- `2ddbdad` (feat) — FOUND (router.py)
- `fc5cd8b` (feat) — FOUND (app.py)
- `08aaabe` (feat) — FOUND (test infrastructure)
