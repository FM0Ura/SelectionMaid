---
phase: 13-animation-view-transitions
plan: 02
subsystem: ui
tags: [motion-v, layoutId, stagger, spring, vue3, animation]

# Dependency graph
requires:
  - phase: 13-01
    provides: AnimatePresence global view transitions that contain the layoutId morph
  - phase: 12-result-display
    provides: MetadataCard and ChunkCard components targeted by these animations
  - phase: 11-skeleton-loading-processing-feedback
    provides: ProcessingCard that is the morph source

provides:
  - layoutId="metadata-card" morph between ProcessingCard and MetadataCard via motion-v spring
  - Staggered slide-up/fade cascade for chunk list on result reveal
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "layoutId morph pattern: motion.div with layout-id prop and spring transition on both source/target components"
    - "Parent-child variant stagger: parent motion.div sets staggerChildren, child motion.div defines hidden/show opacity+y states"

key-files:
  created: []
  modified:
    - frontend/src/components/upload/ProcessingCard.vue
    - frontend/src/components/result/MetadataCard.vue
    - frontend/src/components/result/ResultView.vue
    - frontend/src/components/result/ChunkCard.vue

key-decisions:
  - "Spring stiffness 260, damping 30 chosen for the layout morph — provides snappy but not jarring physical feel"
  - "staggerChildren set to 0.07s (within the 0.05–0.1s range) — creates visible cascade without making the list feel slow"
  - "ChunkCard wrapped in motion.div rather than converting Card itself — avoids touching the shared UI primitive"
  - "easeOut 0.3s per chunk — consistent with Plan 01 global fade duration, reinforces a unified motion language"

requirements-completed: [RES-02]

# Metrics
duration: 10min
completed: 2026-05-26
---

# Phase 13 Plan 02: Layout Morphing and Staggered Result Reveal Summary

**Processing card morphs into the metadata card via motion-v layoutId spring, and result chunks cascade in with staggered slide-up/fade animation**

## Performance

- **Duration:** ~10 min
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- ProcessingCard now wraps its content in a `motion.div` with `layout-id="metadata-card"` and spring transition settings (stiffness: 260, damping: 30), making it the morph source
- MetadataCard wraps its Card in the same `motion.div` with `layout-id="metadata-card"`, making it the morph target — motion-v interpolates size, position, and content between the two on state change
- ResultView chunks container converted to `motion.div` with parent variants that set `staggerChildren: 0.07` on the show transition
- ChunkCard wrapped in `motion.div` with child variants: `hidden = { opacity: 0, y: 20 }` → `show = { opacity: 1, y: 0 }` with easeOut 0.3s — all chunks enter in a cascade sequence

## Task Commits

1. **Task 1: Implement Layout Morphing for the Metadata Card** - `aa67e71` (feat)
2. **Task 2: Implement Staggered Result Reveal** - `8946bb1` (feat)

## Files Created/Modified

- `frontend/src/components/upload/ProcessingCard.vue` — Replaced root div with motion.div, added layout-id and spring transition
- `frontend/src/components/result/MetadataCard.vue` — Wrapped Card in motion.div, added layout-id and spring transition
- `frontend/src/components/result/ResultView.vue` — Converted chunks div to motion.div with parent stagger variants
- `frontend/src/components/result/ChunkCard.vue` — Wrapped Card in motion.div with child hidden/show variants

## Decisions Made

- Spring transition (stiffness 260, damping 30) is the recommended motion-v setting for smooth layout morphs — avoids the overshoot of higher stiffness values while still feeling physical
- staggerChildren: 0.07s sits in the middle of the 0.05–0.1s range from the context decisions — fast enough to feel snappy, slow enough to perceive the cascade
- ChunkCard retains the existing Card component unchanged; only a wrapping motion.div is added to avoid coupling the shared UI primitive to animation concerns

## Deviations from Plan

None — plan executed exactly as written. Used `layout-id` kebab-case attribute (Vue SFC prop convention) which is equivalent to the `layoutId` camelCase used in JSX contexts.

## Threat Model Review

No new trust boundaries introduced. Changes are purely visual/animation — no network requests, no data handling, no new external inputs.

## Known Stubs

None.

## Self-Check: PASSED

- `aa67e71` — feat(13-02): implement layout morphing for metadata card — confirmed in git log
- `8946bb1` — feat(13-02): implement staggered result reveal for chunk list — confirmed in git log
- Both modified files confirmed present on disk
- TypeScript check passed with no errors after all changes
