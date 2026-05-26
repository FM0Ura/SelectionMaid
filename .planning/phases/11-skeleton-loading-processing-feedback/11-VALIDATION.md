# Phase 11 Validation Strategy: Skeleton Loading + Processing Feedback

## Goal
Ensure that the "perceived performance" layer (skeleton screens, timer, and transitions) functions correctly, provides accurate feedback, and maintains visual consistency without introducing layout regressions.

## 1. Unit Testing (Logic & Components)

### `useUpload` Timer Logic
- **Scope:** `frontend/src/composables/useUpload.ts`
- **Scenarios:**
  - Timer starts exactly at 0 when status transitions to `processing`.
  - Timer increments every 1,000ms (+/- tolerance).
  - Timer pauses/stops when status is no longer `processing` (e.g., `result`, `error`, `idle`).
  - Timer resets to 0 upon a new upload sequence.
- **Tool:** Vitest with `vi.useFakeTimers()`.

### Atomic Components
- **SkeletonChunk.vue:**
  - Verify it renders the expected structure (lines/placeholders).
  - Verify it applies the shimmer CSS classes.
- **ProcessingCard.vue:**
  - Verify it formats seconds into `MM:SS` correctly (e.g., 65s -> `01:05`).
  - Verify it displays the provided `elapsedSeconds` prop.
  - Verify it renders the `LoaderCircle` icon with `animate-spin`.
- **Tool:** Vitest + `@vue/test-utils`.

## 2. Integration Testing (Transitions)

### DropZone Minimize Flow
- **Scope:** `frontend/src/components/upload/DropZone.vue`
- **Scenarios:**
  - Verify class changes between `idle` and `processing` states (e.g., `min-h-96` to `min-h-48`).
  - Verify `ProcessingCard` is rendered only during `processing`.
  - Verify interaction elements (input, buttons) are removed/hidden during `processing`.
- **Tool:** Vitest + `@vue/test-utils`.

### App Layout Integration
- **Scope:** `frontend/src/App.vue`
- **Scenarios:**
  - Verify that when `status === 'processing'`, the skeleton list (3-5 chunks) appears below the `DropZone`.
  - Verify that skeletons are removed when status changes to `result` or `error`.
- **Tool:** Vitest + `@vue/test-utils`.

## 3. Visual Verification (Manual)

| Feature | Verification Step | Expected Outcome |
|---------|-------------------|------------------|
| Shimmer Animation | Inspect the skeleton cards in dev tools. | Shimmer gradient moves smoothly across the cards (not static). |
| Layout Transition | Trigger an upload. | The DropZone card shrinks smoothly (no instant "pop"). |
| Dark Mode Contrast | Toggle dark mode (if applicable). | Shimmer is visible but subtle in dark mode. |
| Timer Accuracy | Observe the timer for 10 seconds. | Matches real-world clock time. |

## 4. Performance & Accessibility

- **Animation:** Ensure all animations use `transform` and `opacity` where possible to maintain 60fps.
- **Aria-live:** `ProcessingCard` should use an `aria-live="polite"` region for the timer/status if appropriate for screen readers.
- **Icons:** `LoaderCircle` should have `aria-hidden="true"` as it is a decorative status indicator.
