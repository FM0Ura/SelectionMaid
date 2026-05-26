---
phase: 08-backend-cors-project-scaffold
plan: 01
subsystem: api
tags: [fastapi, cors, testing]

requires: []
provides:
  - Restricted FastAPI CORS policy for the local Vite dev origin.
  - Integration tests covering allowed and rejected browser origins.
affects: [frontend, http-api]

tech-stack:
  added: []
  patterns:
    - FastAPI CORSMiddleware configured in create_app().
    - TestClient-based CORS integration tests avoid Docling startup.

key-files:
  created:
    - tests/adapters/http/test_cors.py
  modified:
    - src/selection_maid/adapters/http/app.py

key-decisions:
  - "Allowed only http://localhost:5173 for local frontend development."
  - "Allowed methods are restricted to POST and OPTIONS."

patterns-established:
  - "CORS policy lives at the app factory boundary, outside the hexagonal core."

requirements-completed: [INT-01]

duration: 13min
completed: 2026-05-26
---

# Phase 08: Backend CORS Summary

**Restricted FastAPI CORS policy for the Vue/Vite dev server with integration coverage for allowed and untrusted origins**

## Performance

- **Duration:** 13 min
- **Started:** 2026-05-26T01:56:00Z
- **Completed:** 2026-05-26T02:08:55Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added CORS tests for allowed local Vite preflight, rejected untrusted origin, and actual POST response headers.
- Configured `CORSMiddleware` in `create_app()` with `allow_origins=["http://localhost:5173"]`.
- Restricted CORS methods to `POST` and `OPTIONS` with wildcard request headers and credentials enabled.

## Task Commits

1. **Task 1: Create CORS integration test** - `a6371b0` (test)
2. **Task 2: Implement CORSMiddleware in create_app** - `966be1d` (feat)

## Files Created/Modified

- `tests/adapters/http/test_cors.py` - CORS policy integration tests.
- `src/selection_maid/adapters/http/app.py` - FastAPI app factory with restricted CORS middleware.

## Decisions Made

- CORS is configured in the HTTP adapter layer, keeping the domain/service layers untouched.
- The tests instantiate the app without entering lifespan so Docling model startup is not required for CORS verification.

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope changes.

## Issues Encountered

None.

## Verification

- `uv run pytest tests/adapters/http/test_cors.py` - passed, 3 tests.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

The backend now accepts browser requests from the local Vite dev server, so the frontend scaffold can call `/api/ingest` during development.

## Self-Check: PASSED

- Key files exist.
- Required CORS headers and method restrictions are covered by tests.
- Requirement `INT-01` is complete.

---
*Phase: 08-backend-cors-project-scaffold*
*Completed: 2026-05-26*
