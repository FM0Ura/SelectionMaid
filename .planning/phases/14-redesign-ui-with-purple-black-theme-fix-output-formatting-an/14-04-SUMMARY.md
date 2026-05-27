---
phase: 14
plan: 04
subsystem: frontend
tags: [download, markdown, result-view, tdd, vue3]
dependency_graph:
  requires: [14-03]
  provides: [ResultView download feature]
  affects: [frontend/src/components/result/ResultView.vue, frontend/src/components/result/ResultView.spec.ts, frontend/src/App.spec.ts]
tech_stack:
  added: []
  patterns: [Blob API download, ref + setTimeout feedback pattern, YAML front-matter generation]
key_files:
  created: []
  modified:
    - frontend/src/components/result/ResultView.vue
    - frontend/src/components/result/ResultView.spec.ts
    - frontend/src/App.spec.ts
decisions:
  - App.spec.ts reset test fixed to use aria-label selector (broken when Download button added before Novo Upload)
metrics:
  duration: 159s
  completed: "2026-05-27"
  tasks_completed: 1
  files_modified: 3
---

# Phase 14 Plan 04: Global Download .MD Button in ResultView Summary

**One-liner:** Global Markdown download button in ResultView header with YAML front-matter + chunk separator format, TDD-verified with 3 passing tests.

## What Was Built

Added the global "Download .MD" feature to ResultView. Users can now download all extracted chunks as a single `.md` file with:
- YAML front-matter containing title, language, doc_type, ingested_at, chunk_count
- Each chunk with a `# Chunk N` header, HTML comment metadata, content, and `---` separator
- Filename slugified from `source_filename`: e.g. `report-chunks.md`
- Check icon / "Baixado!" feedback for 1.5 seconds after click (mirrors copy button pattern)

## Tasks Completed

| Task | Name | Commits | Files |
|------|------|---------|-------|
| 1 | Add global download button and logic to ResultView.vue; fix ResultView.spec.ts | ea8fbff, 4072dce | ResultView.vue, ResultView.spec.ts, App.spec.ts |

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| ea8fbff | test (RED) | Failing tests: download button aria-label, reset selector fix, download feedback |
| 4072dce | feat (GREEN) | buildMarkdownContent + downloadAll + header Download button + App.spec.ts fix |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed App.spec.ts reset test broken by Download button insertion**
- **Found during:** Task 1, GREEN phase (full test suite run)
- **Issue:** `App.spec.ts` line 90 used `wrapper.get('button').trigger('click')` — the first button is now the Download button, not Novo Upload; the `reset` mock was never called
- **Fix:** Changed selector to `wrapper.get('[aria-label="Fazer novo upload"]').trigger('click')` — consistent with the aria-label added to the Novo Upload button in this plan
- **Files modified:** `frontend/src/App.spec.ts`
- **Commit:** 4072dce

## Test Results

- ResultView tests: 3/3 passing (2 updated + 1 new)
- Full suite: 62/62 passing — no regressions

## Known Stubs

None. The download feature is fully wired: buildMarkdownContent generates real YAML front-matter from API data, downloadAll triggers a real Blob download.

## Threat Flags

No new threat surface introduced beyond what was specified in the plan's threat model. URL.revokeObjectURL() is called immediately after anchor.click() to prevent memory leaks (T-14-06 mitigated).

## Self-Check: PASSED

- frontend/src/components/result/ResultView.vue: FOUND
- frontend/src/components/result/ResultView.spec.ts: FOUND
- frontend/src/App.spec.ts: FOUND
- Commit ea8fbff: FOUND
- Commit 4072dce: FOUND
- All 62 tests passing: VERIFIED
