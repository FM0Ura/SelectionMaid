---
phase: 14-redesign-ui-with-purple-black-theme-fix-output-formatting-an
reviewed: 2026-05-27T00:00:00Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - frontend/src/assets/index.css
  - frontend/src/style.css
  - frontend/src/App.vue
  - frontend/src/components/upload/DropZone.vue
  - frontend/src/lib/formatters.ts
  - frontend/src/lib/formatters.spec.ts
  - frontend/src/components/result/ResultView.vue
  - frontend/src/components/result/ResultView.spec.ts
  - frontend/src/App.spec.ts
  - frontend/src/components/result/ChunkCard.vue
  - frontend/src/components/result/ChunkCard.spec.ts
  - frontend/src/components/result/MetadataCard.vue
findings:
  critical: 1
  warning: 4
  info: 3
  total: 8
status: issues_found
---

# Phase 14: Code Review Report

**Reviewed:** 2026-05-27T00:00:00Z
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found

## Summary

Reviewed 12 frontend source files covering the Phase 14 purple-black glassmorphism redesign: the OKLCH CSS theme layers, upload/drop-zone components, result-display components (ResultView, ChunkCard, MetadataCard), formatter utilities, and their test suites.

The overall structure is clean: the upload flow, state machine, type definitions, and download helpers are coherent. One blocker was found: the `formatDate` test hardcodes a UTC-3 time offset and will deterministically fail in any CI environment running in UTC or another timezone. Four warnings cover: premature blob URL revocation that silently breaks downloads in Firefox, an unhandled async rejection path in clipboard copy, a layout centering gap in the ResultView success state, and a YAML/HTML-comment injection risk in the generated download file content. Three info items flag the orphaned scaffold CSS file, the wrong `lang` attribute, and the unlabeled hidden file input.

---

## Critical Issues

### CR-01: `formatDate` test hardcodes UTC-3 time offset — fails in any non-Brazilian CI environment

**File:** `frontend/src/lib/formatters.spec.ts:22`

**Issue:** The test asserts that the UTC timestamp `2026-05-26T15:30:00.000Z` formats to `12:30`:

```ts
expect(formatDate('2026-05-26T15:30:00.000Z')).toMatch(/26\/05\/26,? 12:30/)
```

This assertion is only correct on a machine set to `America/Sao_Paulo` (UTC-3). In a UTC environment the same call returns `26/05/26, 15:30`, which does not match, and the test fails. This was verified by running the formatter under `TZ=UTC`.

`formatDate` uses `Intl.DateTimeFormat` without specifying a `timeZone` option, so it inherits the host machine's locale. CI runners (GitHub Actions, CircleCI, GitLab CI) default to UTC.

**Fix:** Add an explicit `timeZone` option to `formatDate` and update the test to rely on the now-deterministic output:

```ts
// formatters.ts
export function formatDate(isoString: string): string {
  return new Intl.DateTimeFormat('pt-BR', {
    timeZone: 'America/Sao_Paulo',
    year: '2-digit',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(isoString))
}
```

The test regex `/26\/05\/26,? 12:30/` then becomes stable regardless of the runner's system timezone.

---

## Warnings

### WR-01: Premature `URL.revokeObjectURL` can silently break file downloads in Firefox

**File:** `frontend/src/components/result/ResultView.vue:52-57` and `frontend/src/components/result/ChunkCard.vue:38-43`

**Issue:** Both download helpers follow this pattern:

```ts
anchor.click()
URL.revokeObjectURL(url)   // synchronous, immediately after click
```

The browser's download queue is populated asynchronously: `anchor.click()` schedules a navigation to the blob URL, but the actual resource fetch happens on the next microtask or event loop tick. Revoking the URL synchronously before that fetch completes causes a "Failed – Network error" in Firefox (this is a known Firefox behavior difference from Chrome). The anchor element is also never appended to `document.body`; Firefox requires the anchor to be in the live DOM before a programmatic `.click()` triggers a download.

This pattern is duplicated identically in both `ResultView.downloadAll` and `ChunkCard.downloadChunk`.

**Fix:** Append the anchor to the DOM before clicking, remove it after, and defer revocation via `setTimeout`:

```ts
// Apply to both ResultView.vue (downloadAll) and ChunkCard.vue (downloadChunk)
const anchor = document.createElement('a')
anchor.href = url
anchor.download = filename
document.body.appendChild(anchor)
anchor.click()
document.body.removeChild(anchor)
setTimeout(() => URL.revokeObjectURL(url), 0)
```

### WR-02: `copyChunk` async rejection is silently swallowed

**File:** `frontend/src/components/result/ChunkCard.vue:26-28`

**Issue:**

```ts
async function copyChunk() {
  await copy(props.chunk.content)
}
```

`useClipboard`'s `copy()` rejects when the Clipboard API is unavailable (e.g., insecure context, user denies the permission prompt). The `@click="copyChunk"` binding does not attach a rejection handler, so the error becomes an unhandled promise rejection — logged to the console but invisible to the user. The `copied` ref remains `false`, so the button gives no feedback at all, and the user does not know the copy failed.

**Fix:** Wrap in a try/catch and surface a fallback:

```ts
async function copyChunk() {
  try {
    await copy(props.chunk.content)
  } catch {
    // Clipboard API unavailable — optionally show an error toast
    console.warn('Clipboard copy failed')
  }
}
```

### WR-03: `ResultView` section missing `mx-auto` — result content is left-aligned on wide viewports

**File:** `frontend/src/components/result/ResultView.vue:73`

**Issue:** The section is:

```html
<section class="w-full max-w-4xl space-y-5" aria-label="Resultado da extração">
```

In `App.vue` the success-state wrapper is `<motion.div class="w-full">`, a block element that fills the full viewport width. The section inside it is a block element with `max-w-4xl` but no `mx-auto`. Without `mx-auto`, `max-width` clamps the width but does not center the element — it stays pinned to the left edge of its container. On viewports wider than `max-w-4xl` (~896 px), the result panel is visually left-aligned, inconsistent with the upload view which is horizontally centered by the flex `items-center` on `<main>` plus `max-w-2xl` on the content.

**Fix:**

```html
<section class="w-full max-w-4xl mx-auto space-y-5" aria-label="Resultado da extração">
```

### WR-04: YAML frontmatter and HTML comment in `buildMarkdownContent` are vulnerable to injection from API-provided string fields

**File:** `frontend/src/components/result/ResultView.vue:24-43`

**Issue:** `buildMarkdownContent` interpolates API-provided values directly into YAML frontmatter and into an HTML comment without sanitizing newlines or the `-->` sequence:

```ts
`title: ${meta.title || meta.source_filename}`,   // newline in title breaks YAML
...
`<!-- pages: ... | section: ${chunk.section_title} -->`,  // --> in title breaks comment
```

A title containing `\n---\nmalicious: injected` produces a malformed YAML block with injected keys. A `section_title` containing `-->` prematurely closes the HTML comment, emitting literal text into the Markdown body.

These values originate from the backend service (which this codebase controls), so this is not an external-attacker vector, but the downloaded `.md` artifact is the product's primary deliverable and its integrity should be guaranteed.

**Fix:** Strip control characters and escape `-->` sequences before interpolating:

```ts
const safeScalar = (s: string) => s.replace(/[\r\n]/g, ' ')
const safeComment = (s: string) => s.replace(/-->/g, '--\\>')

const frontmatter = [
  '---',
  `title: ${safeScalar(meta.title || meta.source_filename)}`,
  `language: ${safeScalar(meta.language)}`,
  `doc_type: ${safeScalar(meta.doc_type)}`,
  `ingested_at: ${meta.ingested_at}`,
  `chunk_count: ${meta.chunk_count}`,
  '---',
  '',
].join('\n')

// In the chunk loop:
`<!-- pages: ${chunk.page_start}-${chunk.page_end} | words: ${chunk.word_count} | section: ${safeComment(chunk.section_title ?? '')} -->`,
```

---

## Info

### IN-01: `style.css` is an unreferenced Vite scaffold file — dead code

**File:** `frontend/src/style.css`

**Issue:** `style.css` is never imported by `main.ts`, never linked from `index.html`, and not referenced by any component. It is the default Vite Vue template stylesheet containing `.hero`, `.counter`, `.ticks`, `#next-steps`, and `#social` selectors — all of which belong to the unused `HelloWorld.vue` scaffold. Additionally it duplicates both `@keyframes shimmer` and `.shimmer-gradient` with different color values (light-mode grays) compared to the authoritative definitions in `assets/index.css` (dark-mode purple OKLCH). Accidentally importing this file would regress the shimmer animation colors.

The Phase 14 rules added at the bottom of `style.css` (`.hljs` override, scrollbar styling, lines 317-344) are not present in `assets/index.css` and need to be migrated before deleting the file.

**Fix:** Migrate the Phase 14 rules (lines 317-344) from `style.css` into `assets/index.css`, then delete `frontend/src/style.css`.

### IN-02: `<html lang="en">` does not match the Portuguese UI

**File:** `frontend/index.html:2`

**Issue:** The HTML document declares `lang="en"` while all visible UI text is in Brazilian Portuguese. Assistive technologies, browser spell-checkers, and search engine crawlers rely on this attribute for correct language processing (hyphenation, TTS voice selection, translation hints).

**Fix:**

```html
<html lang="pt-BR" class="dark">
```

### IN-03: Hidden file input has no accessible label

**File:** `frontend/src/components/upload/DropZone.vue:94-101`

**Issue:** The `<input type="file" class="sr-only">` element has no `aria-label` and no associated `<label>`. Screen readers that enumerate form controls will announce it as an unlabeled file upload. The visible "Selecionar arquivo" `<Button>` is correctly described by its text content, but it is a `<button>`, not a `<label>`, so the association is not programmatic.

**Fix:** Add `aria-label` directly to the input:

```html
<input
  ref="fileInput"
  class="sr-only"
  type="file"
  :accept="acceptedTypes.join(',')"
  aria-label="Selecionar arquivo para processar"
  data-testid="file-input"
  @change="handleFileChange"
>
```

---

_Reviewed: 2026-05-27T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
