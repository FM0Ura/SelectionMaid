---
phase: 02-docling-extraction-adapter
plan: "03"
subsystem: testing
tags: [docling, pytest, markdown, gfm-tables, code-blocks, headings, lists, integration-tests]

# Dependency graph
requires:
  - phase: 02-docling-extraction-adapter
    plan: "02"
    provides: DoclingAdapter.extract() fully implemented; EXT-01/02/03 integration tests passing

provides:
  - test_headings_in_pdf: asserts heading marker '# ' in PDF Markdown output (EXT-04)
  - test_tables_in_docx: asserts GFM table markers '|' and '---' in DOCX Markdown output (EXT-05)
  - test_lists_in_html: asserts list marker presence in HTML Markdown output (EXT-06)
  - test_code_blocks: asserts triple-backtick fenced block in HTML with <pre><code> via tmp_path (EXT-07)

affects:
  - 02-05 (error wrapping tests — builds on same integration test infrastructure)
  - 06-http-adapter (relies on EXT-04..EXT-07 behavior being verified)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Inline HTML fixture pattern: write minimal HTML string to tmp_path for unconditional code block assertion"
    - "EXT-07 assertion strategy: HTML <pre><code> fixture via tmp_path guarantees code content; no vacuous pass"
    - "Skip-guard pattern: if real_*_path is None: pytest.skip() in every fixture-dependent integration test"

key-files:
  created: []
  modified:
    - tests/adapters/extractor/test_docling_adapter.py

key-decisions:
  - "EXT-07 validated via inline HTML fixture (tmp_path) not DOCX — DOCX code detection is uncertain (A3); HTML <pre><code> behavior is confirmed per RESEARCH.md Pattern: Verified Pattern"
  - "test_headings_in_pdf asserts '# ' (substring) not '## ' exactly — Docling issue #1023 H2 flattening is documented in comment"
  - "test_code_blocks is unconditional (no pytest.skip guard) — tmp_path fixture is always available, fixture content is deterministic"

patterns-established:
  - "tmp_path fixture for unconditional integration tests: use pytest tmp_path to create local files when behavior must be asserted without network dependency"

requirements-completed:
  - EXT-04
  - EXT-05
  - EXT-06
  - EXT-07

# Metrics
duration: 1min
completed: "2026-05-24"
---

# Phase 02 Plan 03: Markdown Structure Tests for EXT-04, EXT-05, EXT-06, EXT-07 Summary

**Four integration tests verify Docling Markdown output structure: heading presence (EXT-04), GFM table syntax (EXT-05), list markers (EXT-06), and triple-backtick code fences via inline HTML fixture (EXT-07)**

## Performance

- **Duration:** 1 min
- **Started:** 2026-05-24T12:45:27Z
- **Completed:** 2026-05-24T12:46:25Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Added `test_headings_in_pdf` to `TestDoclingAdapterIntegration`: extracts real PDF, asserts `"# "` present in Markdown content; comment documents Docling issue #1023 (H2 flattening — checking presence only, not level)
- Added `test_tables_in_docx`: extracts real DOCX, asserts `"|"` and `"---"` present (GFM table column and separator markers)
- Added `test_lists_in_html`: extracts real HTML, asserts at least one of `"- "`, `"* "`, or `"1. "` present (ordered/unordered list markers)
- Added `test_code_blocks`: writes minimal `<html><body><pre><code>some_code()</code></pre></body></html>` to `tmp_path / "code_sample.html"`, extracts it via DoclingAdapter, asserts `"```"` present — unconditional assertion (EXT-07; no network dependency)
- Full test suite: 37 passed, 2 skipped (PDF and DOCX/HTML path fixtures may vary by environment)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Markdown structure tests for EXT-04, EXT-05, EXT-06, EXT-07** - `c586427` (test)

**Plan metadata:** *(committed with SUMMARY.md below)*

## Files Created/Modified

- `tests/adapters/extractor/test_docling_adapter.py` — Added four methods to `TestDoclingAdapterIntegration`: `test_headings_in_pdf`, `test_tables_in_docx`, `test_lists_in_html`, `test_code_blocks`

## Decisions Made

- EXT-07 uses an inline HTML fixture (`tmp_path`) rather than a DOCX file because DOCX code block detection is uncertain (Assumption A3 from RESEARCH.md: `WordFormatOption + SimplePipeline` may not recognize monospace-formatted DOCX paragraphs as `CodeItem`). HTML `<pre><code>` is confirmed behavior in Docling's MarkdownSerializer. This is documented in the test docstring.
- `test_code_blocks` does not call `pytest.skip()` — `tmp_path` is a built-in pytest fixture always available, so the assertion is unconditional. This ensures EXT-07 always exercises real code path rather than being allowed to silently skip.
- `test_headings_in_pdf` checks for `"# "` (substring present in `##`, `###`, etc.) rather than an exact heading level, explicitly accepting Docling issue #1023 behavior.

## Deviations from Plan

None - plan executed exactly as written. All four test methods match the plan's behavior and action specifications.

## Known Stubs

None — all four test methods are fully implemented with real assertions.

## Threat Flags

None — this plan adds test methods only. No new network endpoints, auth paths, file access patterns, or schema changes introduced.

## Issues Encountered

None — all tests pass or skip cleanly. `uv run pytest tests/ -x -q` exits 0 (37 passed, 2 skipped).

## User Setup Required

None — no external service configuration required. The `test_code_blocks` test uses only `tmp_path` (no network). Other tests skip gracefully if fixtures are unavailable.

## Next Phase Readiness

- EXT-04, EXT-05, EXT-06, EXT-07 now have integration test coverage via `TestDoclingAdapterIntegration`
- Plan 02-05 (error wrapping / exception taxonomy tests) can proceed: extraction infrastructure is fully proven
- Known Docling limitation (issue #1023, H2 flattening) is documented in test comment and accepted per D-28
- DOCX code block detection (Assumption A3) remains uncertain but is not blocking — EXT-07 is covered via HTML

---
*Phase: 02-docling-extraction-adapter*
*Completed: 2026-05-24*

## Self-Check: PASSED

Files verified:
- `tests/adapters/extractor/test_docling_adapter.py` — FOUND (contains test_headings_in_pdf, test_tables_in_docx, test_lists_in_html, test_code_blocks)
- `.planning/phases/02-docling-extraction-adapter/02-03-SUMMARY.md` — FOUND

Commits verified:
- `c586427` (Task 1: Markdown structure tests) — FOUND
