---
phase: 06-http-api-layer
verified: 2026-05-24T23:59:00Z
status: human_needed
score: 5/5
overrides_applied: 0
human_verification:
  - test: "Run the live server with `uv run uvicorn selection_maid.adapters.http.app:app` and send `POST /ingest` with a real PDF file via curl or Postman"
    expected: "HTTP 200 with ExtractionResponse JSON containing non-empty metadata (doc_id, language, doc_type, etc.) and at least one chunk with content"
    why_human: "Unit tests use a mocked ExtractionService. The full pipeline (Docling -> Filter -> Chunker -> Enricher -> HTTP) is only exercised via live server. Integration tests with real documents are deferred to Phase 7."
  - test: "Run `GET /health` against the live server after it has been up for at least 5 seconds"
    expected: "JSON body `{status: 'ok', rss_mb: <float > 0>, uptime_seconds: <float >= 5>, version: '0.1.0'}` — rss_mb must reflect actual process memory, not zero"
    why_human: "Unit tests mock app.state.start_time; psutil RSS reading from a real process is not exercised. Need to confirm the health endpoint works end-to-end with a live server loading Docling models."
---

# Phase 6: HTTP API Layer — Verification Report

**Phase Goal:** O serviço é acessível via HTTP com endpoint de ingestão que valida uploads e retorna ExtractionResponse, e endpoint de health com RSS do processo
**Verified:** 2026-05-24T23:59:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `POST /ingest` with valid PDF returns HTTP 200 with ExtractionResponse (metadata + non-empty chunks) | VERIFIED | `TestIngestSuccess` (4 tests) pass; `test_ingest_success_response_schema` confirms all 9 metadata fields and all 8 chunk fields in JSON output; `mock_service.process.return_value = _make_extraction_result()` produces non-empty chunks |
| 2 | `GET /health` returns HTTP 200 with `{status, rss_mb, uptime_seconds, version}` | VERIFIED | `TestHealthEndpoint` (4 tests) pass; tests confirm status="ok", rss_mb is float > 0, uptime_seconds >= 0, version is non-empty string; psutil.Process().memory_info().rss reads real RSS in router.py:103-104 |
| 3 | Files >50MB → HTTP 413; unsupported MIME → HTTP 415; spoofed magic bytes → HTTP 422 | VERIFIED | `TestIngestValidationSize` (2 tests), `TestIngestValidationMime` (3 tests), `TestIngestValidationMagic` (3 tests) all pass; error codes UPLOAD-001 / EXT-002 / UPLOAD-002 map to 413/415/422 respectively in error_map.py |
| 4 | Router wired via `build_router(service, config)` factory + closure pattern; no business logic in HTTP adapter | VERIFIED | `router.py:79` defines `def build_router(service: ExtractionService, config: GlobalConfig) -> APIRouter`; handlers capture `service` and `config` via closure; no Pydantic imports in `domain/` or `service.py` (grep confirmed clean) |
| 5 | `POST /ingest` with heavy document does not block event loop — confirmed via two simultaneous requests | VERIFIED | `TestIngestConcurrency.test_ingest_concurrency_two_requests` passes; uses `httpx.AsyncClient + asyncio.gather`; `router.py:224` confirms `await run_in_threadpool(service.process, raw_input)`; both concurrent requests return HTTP 200 and `mock_service.process.call_count == 2` |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/selection_maid/adapters/http/schemas.py` | Pydantic schemas: ChunkSchema (8 fields), MetadataSchema (9 fields), ExtractionResponse, HealthResponse | VERIFIED | File exists, 98 lines, all 4 schemas present with correct fields and `ConfigDict(from_attributes=True)` |
| `src/selection_maid/adapters/http/router.py` | `build_router(service, config)` factory with GET /health and POST /ingest | VERIFIED | File exists, 244 lines, full implementation with 3-layer validation, tempfile lifecycle, run_in_threadpool dispatch, error mapping |
| `src/selection_maid/adapters/http/app.py` | `create_app()` factory + asynccontextmanager lifespan + module-level `app` | VERIFIED | File exists, 114 lines, lifespan builds DocumentConverter singleton, wires all adapters, calls `build_router(service, config)` |
| `src/selection_maid/adapters/http/error_map.py` | `ERROR_CODE_TO_HTTP` dict + `get_http_status()` helper | VERIFIED | File exists, 55 lines, all 8 error codes mapped correctly including UPLOAD-001 (413), UPLOAD-002 (422), EXT-002 (415) |
| `tests/adapters/http/conftest.py` | TestClient fixture with lightweight test lifespan and mock service | VERIFIED | File exists, 54 lines, uses MagicMock(spec=ExtractionService) and minimal lifespan — no Docling loading |
| `tests/adapters/http/test_router.py` | 20 tests covering health, validation, success, error mapping, concurrency | VERIFIED | File exists, 557 lines, 20 test methods in 6 test classes; all 20 pass (confirmed by test run) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `app.py` | `router.py` | `build_router(service, config)` called in lifespan | WIRED | `app.py:80` calls `build_router(service, config)`; `app.py:81` calls `app.include_router(router)` |
| `router.py` | `service.py` | `run_in_threadpool(service.process, raw_input)` | WIRED | `router.py:224`; `service` captured by closure from `build_router` parameter |
| `router.py` | `schemas.py` | `ExtractionResponse.model_validate(result, from_attributes=True)` | WIRED | `router.py:226` imports and uses `ExtractionResponse` for response serialization |
| `router.py` | `error_map.py` | `from selection_maid.adapters.http.error_map import ERROR_CODE_TO_HTTP` | WIRED | `router.py:35` import; `router.py:72` usage in `_error_response()` |
| `app.py` | `config.py` | `config = get_config()` in lifespan | WIRED | `app.py:63` calls `get_config()`; `config` passed to `build_router(service, config)` |
| `conftest.py` | `router.py` | `build_router(mock_service, get_config())` in test lifespan | WIRED | `conftest.py:47` confirms test isolation pattern |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `router.py` (health) | `rss_mb` | `psutil.Process().memory_info().rss` | Yes — reads real process RSS from OS | FLOWING |
| `router.py` (health) | `uptime_seconds` | `datetime.now(UTC) - request.app.state.start_time` | Yes — wall-clock delta from lifespan start | FLOWING |
| `router.py` (health) | `version` | `importlib.metadata.version("selectionmaid")` | Yes — reads installed package metadata; falls back to "unknown" | FLOWING |
| `router.py` (ingest) | `result` | `await run_in_threadpool(service.process, raw_input)` | Yes — real ExtractionService call (mocked in unit tests, real in production) | FLOWING |
| `router.py` (ingest) | `ExtractionResponse` | `model_validate(result, from_attributes=True)` | Yes — converts domain dataclass to response schema | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All HTTP adapter tests pass | `uv run pytest tests/adapters/http/ -v` | 33 passed, 0 failed in 0.28s | PASS |
| Full suite (excl. Docling integration) passes | `uv run pytest tests/ --ignore=tests/adapters/extractor/ -q` | 165 passed, 0 failed in 1.00s | PASS |
| No regressions in prior phases | Same full suite run | All domain, filter, chunker, enricher, HTTP tests pass | PASS |

### Probe Execution

No probes defined for Phase 6. Step 7c: SKIPPED (no `scripts/*/tests/probe-*.sh` files found for this phase).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| API-01 | 06-02, 06-04 | POST /ingest accepts multipart/form-data upload, returns ExtractionResponse | SATISFIED | `test_ingest_success_response_schema` confirms all metadata and chunk fields; `run_in_threadpool` dispatch implemented |
| API-02 | 06-02 | GET /health returns service status including process RSS | SATISFIED | `TestHealthEndpoint` (4 tests) pass; `rss_mb` via psutil, `uptime_seconds` via app.state.start_time, `version` via importlib.metadata |
| API-03 | 06-03 | 3-layer file validation: size (413), MIME type (415), magic bytes (422) | SATISFIED | 8 validation tests pass; error codes map to correct HTTP statuses in error_map.py |
| ARCH-05 | 06-02, 06-03 | FastAPI adapter isolated from domain; router via factory function; no business logic in HTTP layer | SATISFIED | `build_router(service, config)` closure pattern confirmed; no Pydantic in domain/service.py; domain logic stays in ExtractionService |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | No TBD/FIXME/XXX markers found | — | — |
| None | — | No empty implementations | — | — |
| None | — | No placeholder returns | — | — |

No anti-patterns detected in any Phase 6 file.

### Human Verification Required

#### 1. Live Server: POST /ingest Full Pipeline

**Test:** Start the server with `uv run uvicorn selection_maid.adapters.http.app:app --port 8000`. Send a real PDF via `curl -F "file=@/path/to/real.pdf;type=application/pdf" http://localhost:8000/ingest`.
**Expected:** HTTP 200 with ExtractionResponse JSON containing non-empty `metadata` (including detected `language`, inferred `doc_type`, populated `title`) and at least one `chunk` with real content (not empty string).
**Why human:** All unit tests mock ExtractionService. The integration path Docling → HeuristicFilter → MarkdownChunker → MetadataEnricher → HTTP serialization is not exercised in this phase's test suite. Integration tests with real documents are deferred to Phase 7.

#### 2. Live Server: GET /health with Real Process Memory

**Test:** Start the live server, wait at least 5 seconds, then `curl http://localhost:8000/health`.
**Expected:** JSON `{"status":"ok","rss_mb":<float>,"uptime_seconds":<float>,"version":"0.1.0"}` where `rss_mb > 0` (should be several hundred MB after Docling model loading) and `uptime_seconds >= 5`.
**Why human:** Unit tests set `app.state.start_time` in a test lifespan; the real lifespan with Docling model loading is never exercised in the test suite. Need to confirm `rss_mb` reflects actual RSS after model loading, not just process baseline.

### Gaps Summary

No gaps found. All 5 success criteria are VERIFIED by automated checks. The 2 human verification items cover the integration path between the HTTP adapter and the real Docling pipeline — this is expected at this phase because Phase 7 (Integration Hardening) is explicitly designed to test the full pipeline with real documents.

---

_Verified: 2026-05-24T23:59:00Z_
_Verifier: Claude (gsd-verifier)_
