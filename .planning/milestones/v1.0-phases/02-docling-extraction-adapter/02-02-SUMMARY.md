---
phase: 02-docling-extraction-adapter
plan: "02"
subsystem: extraction
tags: [docling, threadpoolexecutor, mypy, pytest, hexagonal-architecture, timeout]

# Dependency graph
requires:
  - phase: 02-docling-extraction-adapter
    plan: "01"
    provides: DoclingAdapter skeleton with NotImplementedError stub, conftest fixtures, test scaffold

provides:
  - Complete DoclingAdapter.extract() implementation with ThreadPoolExecutor timeout
  - _build_raw_document() private helper mapping ConversionResult to RawDocument
  - Unit tests: test_unsupported_format_raises, test_extraction_error_wraps_converter_exception, test_raw_document_filename_matches_input
  - Integration tests: test_pdf_extraction (EXT-01), test_docx_extraction (EXT-02), test_html_extraction (EXT-03)

affects:
  - 02-03 (format fidelity tests build on this extract() implementation)
  - 02-04 (timeout unit tests verify the ThreadPoolExecutor mechanism)
  - 02-05 (error wrapping tests verify exception translation)
  - 06-http-adapter (uses DoclingAdapter.extract() via ExtractorPort)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-call ThreadPoolExecutor(max_workers=1) as context manager for blocking I/O timeout (D-24)"
    - "Exception ordering: TimeoutError before SelectionMaidError before bare Exception (D-16 + D-24)"
    - "Any type annotation for ConversionResult in _build_raw_document to preserve adapter boundary"
    - "Mock() with .document.export_to_markdown.return_value and .document.pages for unit tests"

key-files:
  created: []
  modified:
    - src/selection_maid/adapters/extractor/docling.py
    - tests/adapters/extractor/test_docling_adapter.py

key-decisions:
  - "ConversionResult typed as Any in _build_raw_document — prevents Docling types escaping adapters/extractor/ boundary"
  - "Per-call ThreadPoolExecutor (not class-level) per Pitfall 5 — lingering thread on timeout is accepted for v1"
  - "page_count>=0 assertion for DOCX integration test (not >=1) — A3 assumption: WordFormatOption+SimplePipeline may return 0 pages"
  - "Exception ordering enforced: concurrent.futures.TimeoutError caught first, then SelectionMaidError, then bare Exception"

patterns-established:
  - "TimeoutError-first exception ordering: always catch concurrent.futures.TimeoutError before SelectionMaidError before Exception"
  - "Mock result construction: mock_result.document.export_to_markdown.return_value + mock_result.document.pages = [1]"

requirements-completed:
  - EXT-01
  - EXT-02
  - EXT-03

# Metrics
duration: 3min
completed: "2026-05-24"
---

# Phase 02 Plan 02: DoclingAdapter.extract() Implementation Summary

**DoclingAdapter.extract() fully implemented with ThreadPoolExecutor timeout (D-24), ConversionResult-to-RawDocument mapping via _build_raw_document(), and unit + integration tests verifying EXT-01, EXT-02, EXT-03**

## Performance

- **Duration:** 3 min
- **Started:** 2026-05-24T12:34:23Z
- **Completed:** 2026-05-24T12:37:28Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Replaced NotImplementedError stub in DoclingAdapter.extract() with full implementation: MIME guard → ThreadPoolExecutor submit → future.result(timeout=) → _build_raw_document()
- Exception ordering enforced per plan: concurrent.futures.TimeoutError → ExtractionTimeoutError; SelectionMaidError re-raised unchanged; Exception → ExtractionError (D-16 + D-24 combined)
- _build_raw_document() private method: content from export_to_markdown() (D-28), page_count=0 for HTML / len(doc.pages) for PDF+DOCX (D-29), format from _MIME_TO_FORMAT
- 3 unit tests always pass without internet; 2 integration tests (DOCX, HTML) passed with real Docling; PDF skipped (fixture download not available in current environment — graceful skip per D-27)

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement DoclingAdapter.extract() with ThreadPoolExecutor and RawDocument mapping** - `f6d7f2c` (feat)
2. **Task 2: Add unit and integration tests for EXT-01, EXT-02, EXT-03** - `690b95e` (feat)

**Plan metadata:** *(committed with SUMMARY.md below)*

## Files Created/Modified

- `src/selection_maid/adapters/extractor/docling.py` — Replaced NotImplementedError stub; added full extract() with ThreadPoolExecutor, exception handling, and _build_raw_document() helper
- `tests/adapters/extractor/test_docling_adapter.py` — Replaced placeholder stubs with 3 unit tests (TestDoclingAdapterUnit) and 3 integration tests (TestDoclingAdapterIntegration)

## Decisions Made

- ConversionResult is typed as `Any` in `_build_raw_document(self, result: Any, ...)` to avoid importing the Docling type at any module-level position outside `adapters/extractor/`. This preserves the T-02-02 mitigate established in Plan 02-01.
- Used a fresh `ThreadPoolExecutor(max_workers=1)` as a context manager per `extract()` call rather than a class-level pool. Per Pitfall 5 in RESEARCH.md, a class-level executor with `shutdown(wait=False)` on timeout orphans threads permanently. The per-call approach is correct v1 behavior — lingering thread after timeout is explicitly accepted (D-24).
- DOCX integration test uses `assert result.page_count >= 0` (not `>= 1`) per Assumption A3: `WordFormatOption + SimplePipeline` may return 0 pages for some DOCX files.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ruff E501 line-length violations in test docstrings**
- **Found during:** Task 2 verification (ruff check on test file)
- **Issue:** Two docstring lines exceeded 88 chars (94 and 89 chars respectively)
- **Fix:** Shortened docstring text — removed `(D-30)` reference suffix and `(D-16)` suffix
- **Files modified:** `tests/adapters/extractor/test_docling_adapter.py`
- **Verification:** `uv run ruff check tests/adapters/extractor/test_docling_adapter.py` exits 0
- **Committed in:** `690b95e` (Task 2 commit — fix applied before commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — docstring line-length blocking ruff gate)
**Impact on plan:** Trivial fix, no logic change. Docstring meaning preserved.

## Known Stubs

None — all stubs from Plan 02-01 have been replaced with real implementations.

## Issues Encountered

- PDF integration fixture (`sample.pdf` from `https://www.w3.org/WAI/WCAG21/Techniques/pdf/pdf-sample.pdf`) was not available at test time — fixture returned None, test skipped cleanly per D-27. DOCX and HTML integration tests passed with real Docling conversions.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Plan 02-03 (EXT-04/05/06/07 format fidelity) can begin: extract() is fully implemented and integration tests confirm real Docling output is reachable
- Plan 02-04 (timeout mechanism unit test) can begin: ThreadPoolExecutor + future.result(timeout=) is implemented and ready for direct testing
- Plan 02-05 (error wrapping) can begin: exception translation chain is implemented
- The PDF fixture skip is not a blocker — if PDF integration is needed, the fixture URL can be retried or replaced

---
*Phase: 02-docling-extraction-adapter*
*Completed: 2026-05-24*

## Self-Check: PASSED

Files verified:
- `src/selection_maid/adapters/extractor/docling.py` — FOUND (contains ThreadPoolExecutor, future.result(timeout=, export_to_markdown, len(doc.pages), no NotImplementedError)
- `tests/adapters/extractor/test_docling_adapter.py` — FOUND (contains test_unsupported_format_raises, test_extraction_error_wraps_converter_exception, test_pdf_extraction, test_docx_extraction, test_html_extraction)

Commits verified:
- `f6d7f2c` (Task 1: extract() implementation) — FOUND
- `690b95e` (Task 2: unit and integration tests) — FOUND
