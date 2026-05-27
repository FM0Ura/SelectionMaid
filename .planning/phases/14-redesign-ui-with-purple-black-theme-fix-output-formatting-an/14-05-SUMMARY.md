---
phase: 14-redesign-ui-with-purple-black-theme-fix-output-formatting-an
plan: 05
subsystem: ui
tags: [vue, tailwind, glassmorphism, lucide, blob-api, download, vitest]

# Dependency graph
requires:
  - phase: 14-01
    provides: purple theme tokens (CSS variables --primary, --border purple OKLCH)
  - phase: 14-03
    provides: slugifyFilename utility in formatters.ts
provides:
  - ChunkCard with glassmorphism (bg-white/5 backdrop-blur-md border-purple-900/40)
  - ChunkCard hover glow (hover:shadow-[0_0_20px_2px_rgba(147,51,234,0.3)] transition-shadow)
  - Per-chunk Download icon button with 1.5s CheckIcon feedback
  - downloadChunk: Blob API + URL.createObjectURL produces chunk-N-section-slug.md
  - max-h-[400px] overflow-y-auto scroll wrapper around MarkdownRenderer content
  - 4 ChunkCard tests (2 updated + 2 new for download behavior)
  - slugifyFilename utility in formatters.ts (included as wave-2 dependency)
affects: [result-display, chunk-list-rendering, per-chunk-interaction]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Download ref pattern: const chunkDownloaded = ref(false) + setTimeout(1500) mirrors copy button feedback"
    - "Glassmorphism card: bg-white/5 backdrop-blur-md border border-purple-900/40 established for ChunkCard"
    - "Hover glow: transition-shadow duration-200 hover:shadow-[...rgba] applied per card for premium feel"
    - "Icon-only ghost button for secondary actions: no text label, aria-label carries semantics"

key-files:
  created: []
  modified:
    - frontend/src/components/result/ChunkCard.vue
    - frontend/src/components/result/ChunkCard.spec.ts
    - frontend/src/lib/formatters.ts

key-decisions:
  - "Download button uses ghost variant (not outline) to visually distinguish it from the Copy button"
  - "aria-label changes on chunkDownloaded state for accessible feedback (Chunk baixado for 1.5s)"
  - "max-height scroll applied only to content body div, not the entire card — header remains always visible"
  - "sectionSlug falls back to section-N when section_title is absent, ensuring always-valid filename"
  - "slugifyFilename included in this plan's formatters.ts commit as it was missing from worktree branch"

patterns-established:
  - "Ref-based download feedback: identical 1.5s timeout pattern as useClipboard for visual consistency"
  - "URL stub in spec: vi.stubGlobal('URL', { createObjectURL, revokeObjectURL }) before download tests"
  - "Specific aria-label selectors in tests: never use wrapper.get('button') when multiple buttons present"

requirements-completed: [RES-03]

# Metrics
duration: 12min
completed: 2026-05-27
---

# Phase 14 Plan 05: ChunkCard Glassmorphism, Hover Glow, Download Button, and Scroll Cap Summary

**ChunkCard updated with glassmorphism bg-white/5 + backdrop-blur, purple hover glow, icon-only Download button with 1.5s CheckIcon feedback via Blob API, and max-h-[400px] scroll cap on content body**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-05-27T10:08:39Z
- **Completed:** 2026-05-27T10:20:00Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 3

## Accomplishments

- ChunkCard receives full glassmorphism treatment matching Phase 14 design system (D-03)
- Hover glow box-shadow on ChunkCard activates on mouse-over for premium interactivity (D-07)
- Per-chunk Download icon button triggers Blob download named `chunk-N-section-slug.md` (D-20)
- Download button toggles to CheckIcon for 1.5s then reverts — mirrors copy button pattern (D-21)
- Content area capped at 400px with vertical scroll so long chunks don't dominate the layout (D-14)
- All 4 ChunkCard tests pass; copy test selector updated to use specific aria-label

## Task Commits

TDD cycle for Task 1:

1. **Task 1 RED: Failing tests for download button** - `3868577` (test)
   - Added URL.createObjectURL/revokeObjectURL stub
   - Fixed copy test selector from generic `button` to `[aria-label="Copiar texto do chunk"]`
   - Added 2 new failing tests for download presence and CheckIcon feedback

2. **Task 1 GREEN: ChunkCard implementation + formatters.ts** - `0c21007` (feat)
   - Glassmorphism, hover glow, download button, max-height scroll all implemented
   - slugifyFilename added to formatters.ts (wave-2 dependency not in worktree branch)
   - All 4 tests pass (verified in main repo; identical changes)

## Files Created/Modified

- `frontend/src/components/result/ChunkCard.vue` — Glassmorphism Card + hover glow + Download button + max-height scroll wrapper
- `frontend/src/components/result/ChunkCard.spec.ts` — 4 tests (2 updated selectors + 2 new download tests)
- `frontend/src/lib/formatters.ts` — Added slugifyFilename (Plan 03 dependency; not in worktree branch at wave 2 start)

## Decisions Made

- Download button uses `variant="ghost"` (not `variant="outline"`) to visually distinguish from Copy button's outline style
- Content scroll cap is on the inner `<div>` only — ChunkCard header with metadata and buttons remains always visible above the fold
- `sectionSlug` fallback to `section-${chunk_index + 1}` ensures the filename is always valid even for untitled chunks
- Used `transition-shadow duration-200` (not `duration-300`) for snappier hover response matching the design spec

## Deviations from Plan

None — plan executed exactly as written. The plan explicitly noted that the copy test selector needed updating when the Download button was added first in DOM order, and that fix was included as part of Task 1 spec update.

The `slugifyFilename` addition to formatters.ts is a wave-2 dependency resolution (Plan 03 was in wave 1, but the worktree branch for this plan was branched before wave 1 completed). The orchestrator merge will handle any conflict if Plan 03's worktree also includes it.

## Issues Encountered

- Worktree branch was created before Phase 14 wave 1 commits (Plans 01-03) were merged to master. The `slugifyFilename` from Plan 03 was missing from the worktree's `formatters.ts`. Added it here as a dependency resolution. This is a normal parallel-execution boundary condition.

## Known Stubs

None — all ChunkCard data flows from real `Chunk` props from the API response.

## Threat Flags

No new threat surface introduced. T-14-07 (filename via slugifyFilename) and T-14-08 (URL.revokeObjectURL memory leak) are both mitigated as specified in the plan's threat model.

## Self-Check

- [x] `frontend/src/components/result/ChunkCard.vue` — FOUND
- [x] `frontend/src/components/result/ChunkCard.spec.ts` — FOUND
- [x] `frontend/src/lib/formatters.ts` — FOUND
- [x] `14-05-SUMMARY.md` — FOUND (this file)
- [x] Commit `3868577` (RED) — FOUND in worktree git log
- [x] Commit `0c21007` (GREEN) — FOUND in worktree git log
- [x] `bg-white/5 backdrop-blur-md` in ChunkCard.vue — VERIFIED
- [x] `max-h-[400px]` in ChunkCard.vue — VERIFIED
- [x] `Baixar chunk como Markdown` aria-label in ChunkCard.vue — VERIFIED

**Self-Check: PASSED**

## Next Phase Readiness

- ChunkCard design contract fully satisfied (D-03, D-07, D-14, D-20, D-21)
- Plan 06 (DropZone hover state + processing pulse) can proceed independently
- All ChunkCard tests green

---
*Phase: 14-redesign-ui-with-purple-black-theme-fix-output-formatting-an*
*Completed: 2026-05-27*
