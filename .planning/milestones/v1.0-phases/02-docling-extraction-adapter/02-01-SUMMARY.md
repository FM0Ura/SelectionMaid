---
phase: 02-docling-extraction-adapter
plan: "01"
subsystem: extraction
tags: [docling, pytorch-cpu, uv, mypy, pytest, hexagonal-architecture]

# Dependency graph
requires:
  - phase: 01-domain-foundation
    provides: ExtractorPort protocol, RawInput, RawDocument, SelectionMaidError hierarchy

provides:
  - DoclingAdapter skeleton (importable, mypy-clean) with SUPPORTED_MIME_TYPES and extract() stub
  - build_docling_adapter factory function
  - adapters/extractor/__init__.py with public re-exports
  - tests/adapters/extractor/conftest.py with four session fixtures (real_converter, real_pdf_path, real_docx_path, real_html_path)
  - tests/adapters/extractor/test_docling_adapter.py scaffold (empty test classes)
  - pyproject.toml with docling>=2.95.0 and pytorch-cpu uv index configuration
  - .gitignore with tests/fixtures/ exclusion

affects:
  - 02-02 (extract() full implementation — depends on skeleton + fixtures)
  - 02-03 through 02-05 (all populate test scaffold from this plan)
  - 06-http-adapter (build_docling_adapter factory interface)

# Tech tracking
tech-stack:
  added:
    - docling>=2.95.0 (document conversion engine)
    - torch==2.12.0 CPU-only via pytorch-cpu index
    - torchvision==0.27.0 CPU-only via pytorch-cpu index
  patterns:
    - TYPE_CHECKING guard for Docling imports (prevents torch loading on bare import)
    - pytest session-scoped fixture with download-on-demand and skip-on-failure (D-26/D-27)
    - noqa: F401 for pre-staged imports needed by downstream plans

key-files:
  created:
    - src/selection_maid/adapters/extractor/docling.py
    - tests/adapters/extractor/conftest.py
    - tests/adapters/extractor/test_docling_adapter.py
    - tests/fixtures/.gitkeep
    - .gitignore
  modified:
    - pyproject.toml
    - uv.lock
    - src/selection_maid/adapters/extractor/__init__.py
    - src/selection_maid/domain/ports.py

key-decisions:
  - "D-22 applied: SUPPORTED_MIME_TYPES as module-level frozenset (PDF, DOCX, HTML) — not configurable via constructor"
  - "D-23 applied: build_docling_adapter factory function alongside DoclingAdapter class"
  - "TYPE_CHECKING guard for DocumentConverter prevents torch model loading on bare import (T-02-02)"
  - "pytorch-cpu [[tool.uv.index]] with explicit=true prevents malicious PyPI torch shadowing (T-02-01)"
  - "Pre-staged imports (concurrent.futures, Path, error types) use noqa: F401 — needed by Plan 02-02"
  - "Pre-existing ruff E501 in domain/ports.py fixed as Rule 1 auto-fix (would block ruff gate)"

patterns-established:
  - "TYPE_CHECKING guard pattern: all docling.* imports inside if TYPE_CHECKING: block in adapter modules"
  - "Session fixture pattern: real_converter with scope=session, docling imports inside fixture body only"
  - "Download-on-demand fixture: _ensure_fixture() returns Path|None; tests call pytest.skip() on None"
  - "Factory function pattern: build_docling_adapter(converter, timeout_seconds) consistent with build_router"

requirements-completed:
  - EXT-01
  - EXT-02
  - EXT-03

# Metrics
duration: 7min
completed: "2026-05-24"
---

# Phase 02 Plan 01: DoclingAdapter Skeleton and Test Infrastructure Summary

**DoclingAdapter skeleton with CPU-only Docling install, TYPE_CHECKING import guard, SUPPORTED_MIME_TYPES constant, and download-on-demand session fixtures for integration tests**

## Performance

- **Duration:** 7 min
- **Started:** 2026-05-24T12:24:23Z
- **Completed:** 2026-05-24T12:31:17Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Installed docling>=2.95.0 with CPU-only torch via `[tool.uv.sources]` + `[[tool.uv.index]]` pytorch-cpu (no CUDA download, T-02-01 mitigated)
- Created DoclingAdapter skeleton: TYPE_CHECKING guard keeps Docling out of runtime import graph, SUPPORTED_MIME_TYPES frozenset (D-22), extract() validates MIME before any Docling call (D-30), stub raises NotImplementedError for Plan 02-02
- Created conftest.py with four session fixtures: real_converter (one-time model init per session, D-26), real_pdf_path/real_docx_path/real_html_path (download-on-demand with skip-on-failure, D-27)
- Import of `selection_maid.adapters.extractor` completes in 70ms with no torch loading

## Task Commits

Each task was committed atomically:

1. **Task 1: Add docling dependency and pytorch-cpu index** - `b3931b9` (chore)
2. **Task 2: Create DoclingAdapter skeleton and test infrastructure** - `657f809` (feat)

**Plan metadata:** *(committed with SUMMARY.md below)*

## Files Created/Modified

- `pyproject.toml` - Added docling>=2.95.0 dependency, [tool.uv.sources] torch/torchvision, [[tool.uv.index]] pytorch-cpu with explicit=true
- `uv.lock` - Lockfile updated with full dependency closure including CPU torch
- `src/selection_maid/adapters/extractor/docling.py` - DoclingAdapter class, SUPPORTED_MIME_TYPES, _MIME_TO_FORMAT, build_docling_adapter factory
- `src/selection_maid/adapters/extractor/__init__.py` - Public re-exports: DoclingAdapter, build_docling_adapter, __all__
- `src/selection_maid/domain/ports.py` - Fixed pre-existing ruff E501 in MetadataEnricherPort.enrich() signature
- `tests/adapters/extractor/conftest.py` - real_converter, real_pdf_path, real_docx_path, real_html_path session fixtures
- `tests/adapters/extractor/test_docling_adapter.py` - TestDoclingAdapterUnit and TestDoclingAdapterIntegration scaffolds
- `tests/fixtures/.gitkeep` - Persists fixtures directory in repo (contents gitignored)
- `.gitignore` - Created with tests/fixtures/ exclusion and standard Python patterns

## Decisions Made

- Pre-staged imports (`concurrent.futures`, `Path`, `ExtractionError`, `ExtractionTimeoutError`, `SelectionMaidError`) kept in docling.py with `# noqa: F401` — these are required by Plan 02-02's extract() implementation and would need to be re-added immediately; staging them now keeps diffs minimal.
- `real_converter` fixture typed as `Any` in conftest.py — DocumentConverter is a Docling type that must not appear in module-level annotations outside adapters/extractor/ (T-02-02 mitigate).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pre-existing ruff E501 in domain/ports.py**
- **Found during:** Task 2 (ruff verification on src/)
- **Issue:** `src/selection_maid/domain/ports.py` line 54 had a line-length violation (92 > 88 chars) that caused `uv run ruff check src/` to exit non-zero, blocking the Task 2 acceptance criteria check
- **Fix:** Reformatted `MetadataEnricherPort.enrich()` signature across two lines
- **Files modified:** `src/selection_maid/domain/ports.py`
- **Verification:** `uv run ruff check src/` exits 0
- **Committed in:** `657f809` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — pre-existing lint error blocking verification gate)
**Impact on plan:** Necessary fix to pass acceptance criteria gate. No scope creep — single line reformatted in a pre-existing file.

## Known Stubs

| Stub | File | Line | Reason |
|------|------|------|--------|
| `extract()` raises NotImplementedError | `src/selection_maid/adapters/extractor/docling.py` | 106 | Intentional per plan objective — Plan 02-02 implements full extract() with ThreadPoolExecutor timeout, ConversionResult mapping, and RawDocument assembly |
| `TestDoclingAdapterUnit.test_placeholder` | `tests/adapters/extractor/test_docling_adapter.py` | 21 | Scaffold placeholder — Plans 02-02 and 02-04 populate this class |
| `TestDoclingAdapterIntegration.test_placeholder` | `tests/adapters/extractor/test_docling_adapter.py` | 32 | Scaffold placeholder — Plans 02-02, 02-03, 02-05 populate this class |

These stubs are explicitly required by the plan: "Output: ... empty test class scaffold." Plan 02-01's goal is the skeleton; Plan 02-02 delivers the full extract() implementation.

## Issues Encountered

None — plan executed as specified aside from the pre-existing ruff violation.

## User Setup Required

None — no external service configuration required. Docling and CPU torch wheels are installed automatically via `uv sync`.

## Next Phase Readiness

- Plan 02-02 (extract() implementation) can begin immediately: skeleton is importable, mypy-clean, fixtures infrastructure exists
- The `real_converter` fixture construction is validated (tested import path); integration tests can invoke real Docling as soon as extract() is implemented
- Known concern from STATE.md: memory accumulation (issue #2209) — monitored in Phase 7, not Phase 2

---
*Phase: 02-docling-extraction-adapter*
*Completed: 2026-05-24*

## Self-Check: PASSED

Files verified:
- `src/selection_maid/adapters/extractor/docling.py` — FOUND
- `src/selection_maid/adapters/extractor/__init__.py` — FOUND
- `tests/adapters/extractor/conftest.py` — FOUND
- `tests/adapters/extractor/test_docling_adapter.py` — FOUND
- `tests/fixtures/.gitkeep` — FOUND
- `.gitignore` — FOUND

Commits verified:
- `b3931b9` (Task 1: pyproject.toml + uv.lock) — FOUND
- `657f809` (Task 2: adapter skeleton + test infrastructure) — FOUND
