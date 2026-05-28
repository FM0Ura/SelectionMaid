---
phase: 02-docling-extraction-adapter
plan: "04"
subsystem: extraction
tags: [docling, threadpoolexecutor, timeout, mypy, pytest, hexagonal-architecture]

# Dependency graph
requires:
  - phase: 02-docling-extraction-adapter
    plan: "02"
    provides: DoclingAdapter.extract() with ThreadPoolExecutor timeout and exception ordering

provides:
  - Unit test: test_timeout_raises_extraction_timeout_error (D-24/D-25 verified)
  - Unit test: test_domain_error_propagates_unchanged (SelectionMaidError pass-through verified)
  - mypy --strict boundary confirmation: no docling.* types outside adapters/extractor/

affects:
  - 02-05 (error wrapping tests build on same exception patterns proven here)
  - 06-http-adapter (relies on ExtractionTimeoutError being the correct error type for 504 mapping)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Timeout test pattern (D-25): timeout_seconds=1 + convert.side_effect=lambda path: time.sleep(2)"
    - "Domain error propagation assertion: exc_info.value.message == original message (no double-wrap)"
    - "mypy --strict as ARCH-01 enforcement gate: no docling.* types allowed outside adapters/extractor/"

key-files:
  created: []
  modified:
    - tests/adapters/extractor/test_docling_adapter.py

key-decisions:
  - "D-25 applied: timeout_seconds=1 for unit test — avoids 120s wait; 2s sleep guarantees timeout fires"
  - "Mock side_effect=lambda path: time.sleep(2) preferred over patching Future.result — tests the real ThreadPoolExecutor code path end-to-end"
  - "ExtractionError.message checked (not str(exc)) — validates no double-wrapping by the SelectionMaidError re-raise branch"
  - "mypy --strict exits 0 confirms TYPE_CHECKING guard in docling.py is sufficient for ARCH-01"

patterns-established:
  - "Timeout unit test pattern: small timeout_seconds + sleeping side_effect; wall time = timeout + executor shutdown"
  - "Domain error propagation assertion: check .message attribute to confirm no re-wrapping occurred"

requirements-completed:
  - EXT-01
  - EXT-02
  - EXT-03

# Metrics
duration: 2min
completed: "2026-05-24"
---

# Phase 02 Plan 04: Timeout and Domain Error Unit Tests; mypy Boundary Check Summary

**Timeout mechanism verified: ExtractionTimeoutError raised after 1s via ThreadPoolExecutor; SelectionMaidError pass-through confirmed; mypy --strict exits 0 with ARCH-01 boundary intact**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-24T12:40:09Z
- **Completed:** 2026-05-24T12:42:22Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Added `test_timeout_raises_extraction_timeout_error` to TestDoclingAdapterUnit: converter.convert() sleeps 2s with timeout_seconds=1; asserts ExtractionTimeoutError (not the raw concurrent.futures.TimeoutError) is raised — proves the translation in extract() works end-to-end through the real ThreadPoolExecutor code path
- Added `test_domain_error_propagates_unchanged` to TestDoclingAdapterUnit: converter.convert() raises ExtractionError("already a domain error"); asserts exc_info.value.message == "already a domain error" — proves SelectionMaidError subclasses are re-raised without double-wrapping
- Confirmed `uv run mypy src/ --strict` exits 0 with zero errors — the TYPE_CHECKING guard on `from docling.document_converter import DocumentConverter` in docling.py is sufficient; no docling.* type escapes to domain or service layers (ARCH-01 / T-02-09 mitigated)
- Full test suite: 34 passed, 1 skipped (PDF fixture, expected per D-27)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add timeout and domain-error-propagation unit tests; verify mypy boundary** - `dcde993` (test)

**Plan metadata:** *(committed with SUMMARY.md below)*

## Files Created/Modified

- `tests/adapters/extractor/test_docling_adapter.py` — Added two test methods to TestDoclingAdapterUnit: test_timeout_raises_extraction_timeout_error and test_domain_error_propagates_unchanged; added `import time` and `ExtractionTimeoutError` to imports

## Decisions Made

- Used `mock_converter.convert.side_effect = lambda path: time.sleep(2)` with `timeout_seconds=1` rather than patching `concurrent.futures.Future.result` directly. The lambda approach tests the real ThreadPoolExecutor submit/result code path end-to-end, which is more meaningful than bypassing the executor machinery.
- Checked `exc_info.value.message` (the domain error attribute) rather than `str(exc_info.value)` to verify no double-wrapping. The `.message` attribute comes from SelectionMaidError.__init__ and is preserved exactly by the `raise` in the `except SelectionMaidError:` branch.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ruff I001/E501 in imports**
- **Found during:** Task 1 (ruff verification before commit)
- **Issue:** Adding `import time` and `ExtractionTimeoutError` to imports created an un-sorted import block (I001) and a line longer than 88 chars (E501)
- **Fix:** Reformatted the `from selection_maid.errors import ...` as a parenthesized multi-line block; ruff I001 and E501 both resolved
- **Files modified:** `tests/adapters/extractor/test_docling_adapter.py`
- **Verification:** `uv run ruff check tests/adapters/extractor/test_docling_adapter.py` exits 0
- **Committed in:** `dcde993` (fix applied before commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — import ordering and line length from new imports)
**Impact on plan:** Trivial formatting fix, no logic change. Import block now correctly sorted and within line limit.

## Known Stubs

None — all test methods are fully implemented and asserting real behavior.

## Threat Flags

None — this plan adds no new network endpoints, auth paths, file access patterns, or schema changes. The mypy check positively confirms no new Docling type surface leaked to the domain layer.

## Issues Encountered

None — plan executed as specified aside from the ruff import formatting auto-fix.

## User Setup Required

None — no external service configuration required. Tests run without internet connectivity (unit tests only).

## Next Phase Readiness

- Plan 02-05 (error wrapping / exception taxonomy tests) can begin: the exception translation chain is fully proven by this plan's tests
- ARCH-01 boundary is enforced and verified by mypy --strict; no additional boundary work needed in Phase 2
- EXT-01, EXT-02, EXT-03 requirements are closed across plans 02-01 through 02-04

---
*Phase: 02-docling-extraction-adapter*
*Completed: 2026-05-24*
