---
phase: 07-integration-hardening
plan: 02
subsystem: testing
tags: [pytest, httpx, fastapi, integration-tests, concurrency, tempfile-audit, adversarial-fixtures]

# Dependency graph
requires:
  - phase: 07-01
    provides: adversarial fixture generator, selectionmaid_ tempfile prefix, DoclingAdapter threading lock
  - phase: 06-http-api-layer
    provides: FastAPI router with /ingest and /health endpoints
provides:
  - E2E integration test suite covering adversarial inputs, liveness, concurrency, and tempfile audit
affects: [future phases consuming test infrastructure, CI hardening]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "asyncio.gather for concurrency stress testing against real ASGI app"
    - "glob-based tempfile audit to verify zero /tmp/selectionmaid_* leaks post-request"
    - "Session-scoped real DocumentConverter fixture for integration tests without mocking"

key-files:
  created:
    - tests/adapters/http/test_integration.py
  modified:
    - src/selection_maid/adapters/filter/heuristic.py

key-decisions:
  - "Use httpx.AsyncClient with real app (no mocks) to exercise full stack from HTTP to Docling"
  - "corrupt.pdf, empty.pdf, spoofed.pdf -> 422 (MIME magic fails); protected.pdf -> 500 (Docling decrypt error)"
  - "large_sample.pdf accepted as 200 or 500 depending on Docling success — below 50MB limit, so not rejected at ingress"
  - "Tempfile audit uses glob on /tmp/selectionmaid_* baseline vs post-request count"

patterns-established:
  - "Integration tests import app from router module and wrap in fresh lifespan per test session"
  - "Adversarial fixture generation is idempotent (generate_adversarial.py run once per session)"

requirements-completed: ["HARD-01", "HARD-03", "HARD-04", "API-01", "API-03"]

# Metrics
duration: ~45min
completed: 2026-05-24
---

# Phase 07 Plan 02: Integration Tests Summary

**E2E integration test suite with adversarial fixtures, 5-request concurrency stress, and /tmp/selectionmaid_* tempfile audit via httpx.AsyncClient against the real FastAPI stack**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-05-24T00:00:00Z
- **Completed:** 2026-05-24T00:45:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Implemented 9 integration tests covering all adversarial fixture cases (corrupt, empty, spoofed, protected, large, valid), liveness after failure, 5-request concurrency, and tempfile cleanup audit
- Fixed `build_heuristic_filter` signature bug in `heuristic.py` that was preventing test imports from resolving correctly
- All STRIDE threats T-07-04 (concurrent DoS) and T-07-05 (tempfile exhaustion) are now verifiably mitigated by passing tests

## Task Commits

Each task was committed atomically:

1. **Task 1 + Task 2: E2E Integration, Liveness, Concurrency, and Tempfile Audit** - `4c688cd` (test)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified

- `tests/adapters/http/test_integration.py` - Full integration test suite: adversarial E2E, liveness, concurrency stress, tempfile audit
- `src/selection_maid/adapters/filter/heuristic.py` - Bug fix: corrected `build_heuristic_filter` function signature

## Decisions Made

- Used `httpx.AsyncClient` with real `app` instance (no mocks) so tests exercise the full hexagonal stack from HTTP transport through DoclingAdapter to real Docling models
- Accepted that `large_sample.pdf` may return 200 or 500 depending on Docling success — the test verifies it is NOT rejected at ingress (not a 422), which is the correct behavior for a ~40MB file under the 50MB cap
- Tempfile audit uses a glob baseline taken before the request batch and verifies the count returns to baseline after — robust against pre-existing unrelated /tmp files

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed `build_heuristic_filter` signature in `heuristic.py`**
- **Found during:** Task 1 (importing app for integration test setup)
- **Issue:** `build_heuristic_filter` had an incorrect signature that caused an import error when the test module tried to resolve the filter adapter
- **Fix:** Corrected the function signature to match the expected interface used by the router
- **Files modified:** `src/selection_maid/adapters/filter/heuristic.py`
- **Verification:** Test module imports resolved cleanly; all 9 tests pass
- **Committed in:** `4c688cd` (task commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug)
**Impact on plan:** Fix was necessary for correctness — tests cannot run without correct import chain. No scope creep.

## Issues Encountered

- `build_heuristic_filter` signature mismatch blocked test collection until fixed; resolved under Rule 1 auto-fix

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Integration test suite is in place and covers the primary risk surface (adversarial inputs, concurrency, resource leaks)
- Phase 07-03 and beyond can build additional hardening on top of this verified baseline
- No blockers for downstream phases

---
*Phase: 07-integration-hardening*
*Completed: 2026-05-24*
