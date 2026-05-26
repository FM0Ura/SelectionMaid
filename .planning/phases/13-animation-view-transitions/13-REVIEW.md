---
phase: 13-animation-view-transitions
reviewed: 2026-05-26T00:00:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - frontend/src/App.vue
  - frontend/src/components/result/ChunkCard.vue
  - frontend/src/components/result/MetadataCard.vue
  - frontend/src/components/result/ResultView.vue
  - frontend/src/components/upload/DropOverlay.vue
  - frontend/src/components/upload/DropZone.vue
  - frontend/src/components/upload/ProcessingCard.vue
findings:
  critical: 0
  warning: 4
  info: 3
  total: 7
status: issues_found
---

# Phase 13: Code Review Report

**Reviewed:** 2026-05-26T00:00:00Z
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Seven Vue/TypeScript frontend components were reviewed covering the animation and view-transitions phase. The files implement a motion-v-based upload/processing/result flow with layout-id shared-element transitions, stagger animations, and an `AnimatePresence` fade swap.

No critical (security, data loss, crash) issues were found. Four warnings were identified — two are logic bugs that will produce incorrect runtime behavior in edge cases, and two are robustness issues. Three informational items cover code quality concerns.

---

## Warnings

### WR-01: `useDropZone` configured with `multiple: true` — bypasses the single-file guard for drag-and-drop

**File:** `frontend/src/components/upload/DropZone.vue:33-38`

**Issue:** `useDropZone` is called with `multiple: true`, meaning the VueUse hook itself accepts and passes multiple files to `onDrop`. The explicit single-file check (`files.length > 1`) in `handleFiles` catches this _after_ the fact and shows an error, but the call to `upload.setDragging(isOver)` in the `watch` block still fires when a multi-file drag hovers over the zone, setting the state to `dragging` and showing the drop overlay — giving the user a green "drop here" affordance for an operation that will immediately fail. More importantly, the `multiple` flag on the hidden `<input type="file">` (line 94) is _absent_, so the file-picker path is already correctly single-file-only. Setting `multiple: false` on `useDropZone` would align the drag-and-drop path with the picker path and eliminate the confusing success-then-error UX.

**Fix:**
```typescript
const { isOverDropZone } = useDropZone(dropZoneRef, {
  multiple: false,          // reject multi-file drops at the hook level
  onDrop(files) {
    handleFiles(files)
  },
})
```

---

### WR-02: `setDragging` guard only blocks the transition _into_ `dragging`, not out of it — state can get stuck on `dragging`

**File:** `frontend/src/components/upload/DropZone.vue:40-44`

**Issue:** When `isBusy` is `true` (uploading or processing), the `watch` on `isOverDropZone` skips the `setDragging` call entirely for both `isOver === true` _and_ `isOver === false`. If the user drags a file over the drop zone while the composable is not busy, `setDragging(true)` fires and state becomes `dragging`. If the composable then transitions to `uploading`/`processing` (e.g., another tab triggers upload), and the user moves the cursor out of the drop zone, `isOverDropZone` goes `false` — but the `watch` guard prevents `setDragging(false)` from being called. The state is now permanently `dragging` until a `reset()`. The guard should only block the _entry_ into dragging, not the exit.

**Fix:**
```typescript
watch(isOverDropZone, (isOver) => {
  if (isOver && isBusy.value) {
    return  // don't enter dragging while busy
  }
  upload.setDragging(isOver)
})
```

---

### WR-03: `formatDate` passes an invalid ISO string silently — renders "Invalid Date" to the user

**File:** `frontend/src/lib/formatters.ts:29-37`  
**Called from:** `frontend/src/components/result/MetadataCard.vue:57`

**Issue:** `formatDate` constructs `new Date(isoString)` without checking whether the result is a valid date. If the API returns a malformed or empty `ingested_at` value, `new Date(isoString)` produces an `Invalid Date` object, and `Intl.DateTimeFormat.format()` renders the string `"Invalid Date"` in the UI. The `DocumentMetadata` type declares `ingested_at: string` (non-nullable), so TypeScript offers no protection here. A guard is needed.

**Fix:**
```typescript
export function formatDate(isoString: string): string {
  const d = new Date(isoString)
  if (Number.isNaN(d.getTime())) {
    return '—'
  }
  return new Intl.DateTimeFormat('pt-BR', {
    year: '2-digit',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(d)
}
```

---

### WR-04: Shared `layout-id="metadata-card"` on two components that can be simultaneously present in the DOM

**File:** `frontend/src/components/upload/ProcessingCard.vue:20` and `frontend/src/components/result/MetadataCard.vue:20`

**Issue:** Both `ProcessingCard` and `MetadataCard` declare `layout-id="metadata-card"`. A motion-v/Framer-Motion `layoutId` must be unique across the entire mounted component tree at any given moment to produce a valid shared-element transition. In `App.vue`, the transition is guarded by `AnimatePresence mode="wait"`, which unmounts the upload view before mounting the result view — so both components are never _rendered_ simultaneously. However, the `DropZone` renders `ProcessingCard` when `isProcessing` is true (line 108), and this entire `DropZone` component lives inside the upload-view branch (`v-if="upload.state.value.status !== 'success'"`). There is therefore no overlap under the current render logic.

The risk is latent: if `AnimatePresence` fails to unmount in time (e.g., an exit animation is still running when the success state arrives), or if either component is ever reused elsewhere, two live nodes will claim the same `layoutId` and motion-v will pick one arbitrarily, breaking the animation. The id should be made more specific or scoped.

**Fix:** Use a unique, intent-expressing id on each component, or — if the shared transition is intentional — add a comment explaining the lifecycle dependency so future developers don't accidentally break it.

```html
<!-- ProcessingCard.vue -->
<motion.div layout-id="upload-processing-card" ...>

<!-- MetadataCard.vue -->
<motion.div layout-id="result-metadata-card" ...>
```

If the shared-element morph from `ProcessingCard` → `MetadataCard` is the explicit design intent, document it with a comment and add an integration test or visual test to protect the lifetime invariant.

---

## Info

### IN-01: Duplicate `<h1>` elements rendered on the same page simultaneously

**File:** `frontend/src/App.vue:25` and `frontend/src/components/upload/DropZone.vue:120`

**Issue:** When `upload.state.value.status` is `idle` (the default state), both `App.vue`'s `<h1>Transforme documentos em chunks Markdown</h1>` (line 25) and `DropZone.vue`'s `<h1>Envie um documento</h1>` (line 120) are rendered on the same page at the same time. A page should have exactly one `<h1>` for correct document outline and screen-reader navigation. The inner heading in `DropZone` should be an `<h2>` since it is visually subordinate to the page title.

**Fix:** Change `DropZone.vue` line 120:
```html
<h2 class="text-2xl font-semibold">Envie um documento</h2>
```

---

### IN-02: `section_title` typed as `string` (non-optional) but guarded with falsy check in `ChunkCard`

**File:** `frontend/src/types/api.ts:6` and `frontend/src/components/result/ChunkCard.vue:18`

**Issue:** The `Chunk` interface declares `section_title: string` (non-optional, non-nullable). The component nevertheless guards against a falsy value with `props.chunk.section_title || \`Chunk ${...}\``. If the API can return an empty string or a missing field, the type should be `section_title: string | null` or `section_title?: string`. If the API always returns a non-empty string, the fallback is dead code. The type and the runtime guard are contradicting each other; one of them is wrong.

**Fix:** Align the type with the actual API contract:
- If `section_title` can be absent or empty: `section_title: string | null` in `api.ts`
- If `section_title` is always a non-empty string: remove the `|| fallback` in `ChunkCard.vue` line 18

---

### IN-03: `elapsedSeconds` frozen at `0` for the `uploading` state — shown as a live timer to the user

**File:** `frontend/src/components/upload/DropZone.vue:112`

**Issue:** When `upload.state.value.status === 'uploading'`, `DropZone` renders `<ProcessingCard :elapsed-seconds="0" />` with a hardcoded `0`. `ProcessingCard` shows a live-looking `MM:SS` counter (line 14 of `ProcessingCard.vue`) that will read `00:00` for the full duration of the HTTP upload phase. This is slightly misleading because the spinner implies time is passing, but the counter never moves. The `uploading` status is currently very brief (the composable immediately transitions to `processing` after starting the fetch), so the practical impact is low — but `postIngest` could be slow on large files, making the frozen timer visible.

The `useUpload` composable only starts `elapsedSeconds` counting during the `processing` phase (watcher at line 19-29 of `useUpload.ts`). If the upload phase is expected to remain instantaneous by design, a code comment explaining this would prevent future confusion. If it may be slow, pass `upload.elapsedSeconds.value` instead of `0`.

**Fix (if uploading should show elapsed time):**
```html
<ProcessingCard :elapsed-seconds="upload.elapsedSeconds.value" />
```
Or, if the instantaneous upload assumption is intentional, add a comment:
```html
<!-- upload phase is always < 1s (fire-and-forget); timer starts at processing -->
<ProcessingCard :elapsed-seconds="0" />
```

---

_Reviewed: 2026-05-26T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
