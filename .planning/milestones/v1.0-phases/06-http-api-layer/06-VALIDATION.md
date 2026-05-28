---
phase: 06-http-api-layer
slug: http-api-layer
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-24
updated: 2026-05-25
---

# Phase 6: HTTP API Layer - Validation Strategy

Phase 6 validates the FastAPI HTTP adapter boundary: response schemas, app and
router wiring, upload validation, error mapping, tempfile cleanup, and
non-blocking dispatch to `ExtractionService`.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | pytest 9.x |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run pytest tests/adapters/http/test_router.py tests/adapters/http/test_schemas.py` |
| Full phase command | `uv run pytest tests/test_config.py tests/adapters/http/test_error_map.py tests/adapters/http/test_schemas.py tests/adapters/http/test_router.py` |
| Extended integration command | `uv run pytest tests/adapters/http/` |
| Estimated runtime | < 1 second for full phase command |

## Sampling Rate

- After every HTTP adapter task commit: run the quick command.
- After config or error mapping changes: run the full phase command.
- Before `$gsd-verify-work`: run `uv run pytest tests/adapters/http/`.
- Max feedback latency: < 5 seconds for the fast validation slice.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | API-01 | T-06-01 | Response schemas expose only the domain contract fields | Unit | `uv run pytest tests/adapters/http/test_schemas.py` | yes | green |
| 06-01-02 | 01 | 1 | API-02 | T-06-01 | `HealthResponse` exposes only status, RSS, uptime, and version | Unit | `uv run pytest tests/adapters/http/test_schemas.py` | yes | green |
| 06-02-01 | 02 | 2 | API-02 | T-06-02 | `/health` returns live RSS and uptime in a stable JSON contract | Unit | `uv run pytest tests/adapters/http/test_router.py -k health` | yes | green |
| 06-02-02 | 02 | 2 | ARCH-05 | - | Router is built through `build_router(service, config)` and testable with a mocked service | Unit | `uv run pytest tests/adapters/http/test_router.py` | yes | green |
| 06-03-01 | 03 | 3 | API-03 | T-06-03 | Oversized uploads fail fast with 413 / `UPLOAD-001` | Unit/integration | `uv run pytest tests/adapters/http/test_router.py -k size` | yes | green |
| 06-03-02 | 03 | 3 | API-03 | T-06-04 | Unsupported declared MIME types return 415 / `EXT-002` | Unit/integration | `uv run pytest tests/adapters/http/test_router.py -k mime` | yes | green |
| 06-03-03 | 03 | 3 | API-03 | T-06-04 | Magic-byte spoofing returns 422 / `UPLOAD-002` before domain processing | Unit/integration | `uv run pytest tests/adapters/http/test_router.py -k magic` | yes | green |
| 06-03-04 | 03 | 3 | API-03 | - | `HttpConfig` defaults, TOML overrides, and invalid-value fallback are verified | Unit | `uv run pytest tests/test_config.py` | yes | green |
| 06-03-05 | 03 | 3 | API-03 | - | All domain/upload error codes map to intended HTTP statuses with fallback 500 | Unit | `uv run pytest tests/adapters/http/test_error_map.py` | yes | green |
| 06-04-01 | 04 | 4 | API-01 | T-06-05 | Successful ingest serializes full `ExtractionResponse` and cleans tempfiles | Unit/integration | `uv run pytest tests/adapters/http/test_router.py -k ingest_success` | yes | green |
| 06-04-02 | 04 | 4 | API-01 | - | Domain and unexpected service errors return structured JSON responses | Unit/integration | `uv run pytest tests/adapters/http/test_router.py -k error` | yes | green |
| 06-04-03 | 04 | 4 | ARCH-05 | - | Concurrent `/ingest` requests complete via threadpool dispatch | Integration | `uv run pytest tests/adapters/http/test_router.py -k concurrency` | yes | green |

## Gap Audit

| Gap | Resolution | Test File | Status |
|-----|------------|-----------|--------|
| `HttpConfig` parsing and safe fallback had no direct automated coverage | Added focused config tests for missing config, TOML overrides, and invalid type fallback | `tests/test_config.py` | resolved |
| Complete HTTP error-map contract had no direct automated coverage | Added parametrized mapping test for all known codes plus fallback behavior | `tests/adapters/http/test_error_map.py` | resolved |

## Automated Verification

### Suite 1: API Contracts and Health

- Location: `tests/adapters/http/test_schemas.py`, `tests/adapters/http/test_router.py`
- Command: `uv run pytest tests/adapters/http/test_schemas.py tests/adapters/http/test_router.py -k "schema or health"`
- Success: response schemas match domain dataclasses; `/health` returns the expected JSON contract.

### Suite 2: Upload Validation

- Location: `tests/adapters/http/test_router.py`
- Command: `uv run pytest tests/adapters/http/test_router.py -k "size or mime or magic"`
- Success: size, declared MIME, and magic-byte failures map to 413, 415, and 422.

### Suite 3: Config and Error Mapping

- Location: `tests/test_config.py`, `tests/adapters/http/test_error_map.py`
- Command: `uv run pytest tests/test_config.py tests/adapters/http/test_error_map.py`
- Success: HTTP config values are safely resolved and all error codes map to expected statuses.

### Suite 4: Ingest Dispatch, Cleanup, and Concurrency

- Location: `tests/adapters/http/test_router.py`
- Command: `uv run pytest tests/adapters/http/test_router.py -k "ingest or concurrency"`
- Success: successful ingest returns `ExtractionResponse`, tempfiles are deleted, and concurrent requests return 200.

## Latest Validation Run

Command:

```bash
uv run pytest tests/test_config.py tests/adapters/http/test_error_map.py tests/adapters/http/test_schemas.py tests/adapters/http/test_router.py
```

Result: 45 passed in 0.28s.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live server with real Docling pipeline returns non-empty extraction output | API-01 | Fast phase-6 tests mock `ExtractionService`; real Docling E2E is deferred to phase 7 integration hardening | Run `uv run uvicorn selection_maid.adapters.http.app:app --port 8000`, then `curl -F "file=@/path/to/real.pdf;type=application/pdf" http://localhost:8000/ingest` and inspect metadata/chunks |
| Live `/health` after server uptime reflects increasing uptime | API-02 | TestClient verifies shape and non-negative value; live timing check is operational smoke coverage | Start uvicorn, wait at least 5 seconds, then call `curl http://localhost:8000/health` |

## Validation Audit 2026-05-25

| Metric | Count |
|--------|-------|
| Gaps found | 2 |
| Resolved | 2 |
| Escalated | 0 |

## Validation Sign-Off

- [x] All tasks have automated verification or an explicit manual-only rationale.
- [x] Sampling continuity has no 3 consecutive tasks without automated verification.
- [x] Wave 0/test infrastructure covers all missing references.
- [x] No watch-mode flags.
- [x] Feedback latency < 5 seconds for the phase validation slice.
- [x] `nyquist_compliant: true` set in frontmatter.

Approval: approved 2026-05-25
