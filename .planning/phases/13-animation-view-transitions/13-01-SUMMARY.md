---
phase: 13-animation-view-transitions
plan: 01
subsystem: ui
tags: [motion-v, AnimatePresence, glassmorphism, tailwind-v4, oklch, vue3, animation]

# Dependency graph
requires:
  - phase: 12-result-display
    provides: ResultView component and success state that transitions need to wrap
  - phase: 11-skeleton-loading-processing-feedback
    provides: upload state machine with dragging status driving glass/glow effects
provides:
  - AnimatePresence-based global fade transition between upload and result views
  - OKLCH dual-layer glow pulse + backdrop-blur glassmorphism on DropZone drag-active state
  - Enhanced DropOverlay glass depth with stronger border and lower background opacity
affects: [13-02-layout-morph-stagger]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "AnimatePresence mode=wait wraps v-if branches with unique keys for exit/enter fade"
    - "OKLCH boxShadow animation for dual-layer glow (diffuse outer + crisp inner border)"
    - "backdrop-blur-md via Tailwind class toggled by state condition"

key-files:
  created: []
  modified:
    - frontend/src/App.vue
    - frontend/src/components/upload/DropZone.vue
    - frontend/src/components/upload/DropOverlay.vue

key-decisions:
  - "AnimatePresence mode=wait chosen so exit animation completes before enter begins — prevents both views overlapping during transition"
  - "Dual-layer OKLCH boxShadow: outer diffuse (24px) for ambience + inner crisp (2px) for border glow — provides depth beyond a single-value pulse"
  - "DropOverlay bg opacity reduced from 90% to 70% so backdrop-blur-md shows through the card's frosted glass effect"
  - "Pulse duration set to 1.4s easeInOut for a natural breathing cadence on drag-hold"

patterns-established:
  - "AnimatePresence wrap pattern: motion.div with key prop on each v-if branch, initial/animate/exit all specify opacity, transition.duration 0.3s"
  - "OKLCH glow pattern: oklch(L C H / alpha) in boxShadow array — three keyframes (0 -> peak -> 0) with Infinity repeat while state active"

requirements-completed: [NAV-01]

# Metrics
duration: 15min
completed: 2026-05-26
---

# Phase 13 Plan 01: Animation + View Transitions — Global Transitions Summary

**AnimatePresence global fade (0.3s, mode=wait) between upload/result views and OKLCH dual-layer glow + backdrop-blur-md on DropZone drag-active state**

## Performance

- **Duration:** 15 min
- **Started:** 2026-05-26T23:38:18Z
- **Completed:** 2026-05-26T23:53:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- App.vue now orchestrates smooth global fade transitions using AnimatePresence mode="wait" — clicking Reset or Novo Upload fades out results before the upload view fades in
- DropZone drag-active state now triggers a pulsing dual-layer OKLCH glow (primary-colored, 1.4s easeInOut) plus backdrop-blur-md glassmorphism
- DropOverlay enhanced to complement the glass effect with reduced background opacity (70%) and stronger border (60%), creating consistent frosted-glass depth

## Task Commits

1. **Task 1: Orchestrate Global View Transitions in App.vue** - `572256f` (feat)
2. **Task 2: Upgrade DropZone with Glassmorphism and Glow** - `bdbd19c` (feat)

## Files Created/Modified

- `frontend/src/App.vue` - Added AnimatePresence import, wrapped upload/result branches with mode="wait", added unique keys and opacity transitions
- `frontend/src/components/upload/DropZone.vue` - Added backdrop-blur-md class toggle, replaced generic glow with dual-layer OKLCH boxShadow animation
- `frontend/src/components/upload/DropOverlay.vue` - Updated from backdrop-blur-sm to backdrop-blur-md, bg/90 to bg/70, border/50 to border/60

## Decisions Made

- Used `AnimatePresence mode="wait"` so the exiting view finishes its fade-out before the entering view begins — prevents both views from being visible simultaneously which would create visual clutter in a full-screen transition
- Chose dual-layer boxShadow (outer diffuse glow + inner border glow) over a single-value shadow to give the drag zone a premium depth that reads on dark backgrounds
- Kept 0.3s duration for view transitions (snappy per plan spec); 1.4s easeInOut for drag glow (breathing cadence, not distracting)

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None. TypeScript type check passed with no errors after changes.

## Threat Model Review

No new trust boundaries introduced. Changes are purely visual/CSS/animation — no network requests, no data handling, no new external inputs.

## Known Stubs

None.

## Next Phase Readiness

- Global view transitions and DropZone visual upgrade complete
- Plan 13-02 (Layout Morph + Stagger) can proceed: it targets ResultView chunk animations and the processing card morph which are independent of changes here
- The AnimatePresence pattern established here (key-based, mode=wait, opacity-only transitions) serves as the reference for Plan 13-02's stagger patterns

---
*Phase: 13-animation-view-transitions*
*Completed: 2026-05-26*
