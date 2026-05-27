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

key-decisions:
  - "Download button uses ghost variant (not outline) to visually distinguish it from the Copy button"
  - "aria-label changes on chunkDownloaded state for accessible feedback (Chunk baixado for 1.5s)"
  - "max-height scroll applied only to content body div, not the entire card — header remains always visible"
  - "sectionSlug falls back to section-N when section_title is absent, ensuring always-valid filename"

patterns-established:
  - "Ref-based download feedback: identical 1.5s timeout pattern as useClipboard for visual consistency"
  - "URL stub in spec: vi.stubGlobal('URL', { createObjectURL, revokeObjectURL }) before download tests"
  - "Specific aria-label selectors in tests: never use wrapper.get('button') when multiple buttons present"

requirements-completed: [RES-03]

# Metrics
duration: 8min
completed: 2026-05-27
---

# Phase 14 Plan 05: ChunkCard Glassmorphism, Hover Glow, Download Button, and Scroll Cap Summary

**ChunkCard updated with glassmorphism bg-white/5 + backdrop-blur, purple hover glow, icon-only Download button with 1.5s CheckIcon feedback via Blob API, and max-h-[400px] scroll cap on content body**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-05-27T10:08:39Z
- **Completed:** 2026-05-27T10:16:00Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 2

## Accomplishments

- ChunkCard receives full glassmorphism treatment matching Phase 14 design system (D-03)
- Hover glow box-shadow on ChunkCard activates on mouse-over for premium interactivity (D-07)
- Per-chunk Download icon button triggers Blob download named `chunk-N-section-slug.md` (D-20)
- Download button toggles to CheckIcon for 1.5s then reverts — mirrors copy button pattern (D-21)
- Content area capped at 400px with vertical scroll so long chunks don't dominate the layout (D-14)
- All 4 ChunkCard tests pass; full suite 62/62 green

## Task Commits

TDD cycle for Task 1:

1. **Task 1 RED: Failing tests for download button** - `4d6509a` (test)
   - Added URL.createObjectURL/revokeObjectURL stub
   - Fixed copy test selector from generic `button` to `[aria-label="Copiar texto do chunk"]`
   - Added 2 new failing tests for download presence and CheckIcon feedback

2. **Task 1 GREEN: ChunkCard implementation** - `271f071` (feat)
   - Glassmorphism, hover glow, download button, max-height scroll all implemented
   - All 4 tests pass, no regressions

## Files Created/Modified

- `frontend/src/components/result/ChunkCard.vue` — Glassmorphism Card + hover glow + Download button + max-height scroll wrapper
- `frontend/src/components/result/ChunkCard.spec.ts` — 4 tests (2 updated selectors + 2 new download tests)

## Decisions Made

- Download button uses `variant="ghost"` (not `variant="outline"`) to visually distinguish from Copy button's outline style
- Content scroll cap is on the inner `<div>` only — ChunkCard header with metadata and buttons remains always visible above the fold
- `sectionSlug` fallback to `section-${chunk_index + 1}` ensures the filename is always valid even for untitled chunks
- Used `transition-shadow duration-200` (not `duration-300`) for snappier hover response matching the design spec

## Deviations from Plan

None — plan executed exactly as written. The plan explicitly noted that the copy test selector needed updating when the Download button was added first in DOM order, and that fix was included as part of Task 1 spec update.

## Issues Encountered

None.

## Known Stubs

None — all ChunkCard data flows from real `Chunk` props from the API response.

## Threat Flags

No new threat surface introduced. T-14-07 (filename via slugifyFilename) and T-14-08 (URL.revokeObjectURL memory leak) are both mitigated as specified in the plan's threat model.

## Next Phase Readiness

- ChunkCard design contract fully satisfied (D-03, D-07, D-14, D-20, D-21)
- Plan 06 (DropZone hover state + processing pulse) can proceed independently
- All 62 tests green, no regressions

---
*Phase: 14-redesign-ui-with-purple-black-theme-fix-output-formatting-an*
*Completed: 2026-05-27*
