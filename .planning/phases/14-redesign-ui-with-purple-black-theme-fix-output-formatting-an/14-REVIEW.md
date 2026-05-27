---
phase: 14-redesign-ui-with-purple-black-theme-fix-output-formatting-an
reviewed: 2026-05-27T00:00:00Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - frontend/src/App.spec.ts
  - frontend/src/App.vue
  - frontend/src/assets/index.css
  - frontend/src/components/result/ChunkCard.spec.ts
  - frontend/src/components/result/ChunkCard.vue
  - frontend/src/components/result/MetadataCard.vue
  - frontend/src/components/result/ResultView.spec.ts
  - frontend/src/components/result/ResultView.vue
  - frontend/src/components/upload/DropZone.vue
  - frontend/src/lib/formatters.spec.ts
  - frontend/src/lib/formatters.ts
  - frontend/src/style.css
findings:
  critical: 2
  warning: 5
  info: 3
  total: 10
status: issues_found
---

# Phase 14: Code Review Report

**Reviewed:** 2026-05-27T00:00:00Z
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found

## Summary

Phase 14 adds a purple/black OKLCH color theme, syntax-highlighted MarkdownRenderer, global and per-chunk "Download .MD" buttons, glassmorphism card styling, and the `slugifyFilename` utility. The overall architecture is sound: DOMPurify is present, `html: false` is set on markdown-it, and `rel="noopener noreferrer"` is correctly injected on links.

However, two blockers were found: `slugifyFilename` silently returns an empty string for a class of common inputs (all-special-char filenames, hidden files, extension-only filenames), which produces structurally malformed download filenames. Additionally, both `ChunkCard` and `ResultView` start a `setTimeout` to reset visual feedback state but never call `clearTimeout` on unmount — if the user navigates away within the 1.5 s window the callback fires against the stale ref and, more critically, if the user clicks download rapidly the timers stack and the feedback duration becomes unpredictably long.

Five warnings cover: the vacuous XSS sanitization test that does not actually exercise DOMPurify, over-permissive `ADD_ATTR` configuration, unverified Blob URL revocation in tests, YAML frontmatter corruption from newlines in API-provided fields, and the lack of a disabled guard on the download button during the active feedback window.

---

## Critical Issues

### CR-01: `slugifyFilename` returns empty string for entire input classes, producing malformed filenames

**File:** `frontend/src/lib/formatters.ts:47-55`

**Issue:** `slugifyFilename` returns `""` for any filename whose base (pre-extension) portion contains only non-alphanumeric characters after NFD decomposition: hidden files (`.hidden`), extension-only inputs (`.pdf`), all-punctuation names (`!!!.pdf`), and whitespace-only names (`   .pdf`). The callers do not guard against this:

- `ResultView.vue:50` produces `` `${slugifyFilename(source_filename)}-chunks.md` `` → `"-chunks.md"` (leading hyphen, confusing to users, some shells treat as a flag).
- `ChunkCard.vue:36` produces `` `chunk-1-${sectionSlug}.md` `` → `"chunk-1-.md"` (trailing hyphen) when `section_title` contains only special characters.

The spec at `formatters.spec.ts:42-45` tests `'-bad-name-.pdf'` → `'bad-name'` (covered), but has no case for the zero-output scenario.

**Fix:** Either guard the return value in `slugifyFilename`:
```typescript
export function slugifyFilename(filename: string): string {
  const base = filename.replace(/\.[^.]+$/, '')
  const slug = base
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return slug || 'untitled'
}
```

Or guard at each call site:
```typescript
// ResultView.vue
const slug = slugifyFilename(data.metadata.source_filename) || 'document'
const filename = `${slug}-chunks.md`

// ChunkCard.vue
const sectionSlug = props.chunk.section_title
  ? (slugifyFilename(props.chunk.section_title) || `section-${props.chunk.chunk_index + 1}`)
  : `section-${props.chunk.chunk_index + 1}`
```

Add test cases to `formatters.spec.ts`:
```typescript
it('returns "untitled" for all-special-char input', () => {
  expect(slugifyFilename('!!!')).toBe('untitled')
  expect(slugifyFilename('.pdf')).toBe('untitled')
  expect(slugifyFilename('')).toBe('untitled')
})
```

---

### CR-02: `setTimeout` timers not cancelled on component unmount — stacking timers on rapid clicks

**File:** `frontend/src/components/result/ChunkCard.vue:45-47` and `frontend/src/components/result/ResultView.vue:59`

**Issue:** Both `downloadChunk()` (ChunkCard) and `downloadAll()` (ResultView) start a 1500 ms `setTimeout` to reset feedback state (`chunkDownloaded`, `downloaded`) but never store the handle or cancel it. Two distinct problems follow:

1. **Timer stacking on rapid clicks:** Each click fires a new download and schedules a new `setTimeout`. If the user clicks five times in 1.5 s, five timers are queued. The first fires at 1.5 s and resets the ref to `false`; the subsequent four re-flip it at 3 s, 4.5 s, 6 s, and 7.5 s. The button flickers between `Chunk baixado` and `Baixar chunk como Markdown` four extra times after the user has stopped clicking. Each click also creates and immediately revokes a new Blob URL, which is correct, but the visual state machine is broken.

2. **Post-unmount state write (minor):** If the component unmounts (user clicks "Novo Upload") within 1.5 s of a download, the `setTimeout` callback sets the ref on the now-orphaned reactive object. Vue 3 does not error on this, but the callback runs unnecessarily and would suppress any pending reactivity flush.

**Fix:**
```typescript
// ChunkCard.vue (same pattern for ResultView.vue)
import { ref, onBeforeUnmount } from 'vue'

const chunkDownloaded = ref(false)
let feedbackTimer: ReturnType<typeof setTimeout> | null = null

function downloadChunk(): void {
  if (chunkDownloaded.value) return  // guard against rapid re-click
  // ... blob creation and anchor.click() ...
  chunkDownloaded.value = true
  feedbackTimer = setTimeout(() => {
    chunkDownloaded.value = false
    feedbackTimer = null
  }, 1500)
}

onBeforeUnmount(() => {
  if (feedbackTimer !== null) clearTimeout(feedbackTimer)
})
```

The `if (chunkDownloaded.value) return` guard is the minimal fix to prevent stacking; `clearTimeout` on unmount eliminates the orphaned callback.

---

## Warnings

### WR-01: XSS sanitization test exercises `html: false` (markdown-it), not DOMPurify — test is vacuous

**File:** `frontend/src/components/result/MarkdownRenderer.spec.ts:17-26`

**Issue:** The test inputs `'<script>alert(1)</script>\n\n# Safe'` and asserts `wrapper.html()` does not contain `'<script>'`. Because `MarkdownIt` is instantiated with `html: false`, it escapes raw HTML to `&lt;script&gt;` before DOMPurify is ever invoked. The test passes even if `DOMPurify.sanitize` is removed entirely — it proves nothing about the sanitizer. A real DOMPurify bypass would come from markdown-it generating unsafe HTML output (e.g., via `linkify: true` producing a `javascript:` href), not from raw HTML pass-through.

**Fix:** Add a test that creates a vector markdown-it might produce and that DOMPurify must strip, or mock DOMPurify to verify it is called with the markdown output:
```typescript
it('DOMPurify strips event-handler attributes injected via markdown', () => {
  // markdown-it linkify generates <a href="..."> for URLs; DOMPurify must not pass
  // through onerror/onload if they somehow appear in rendered output
  const wrapper = mount(MarkdownRenderer, {
    props: { content: '[xss](javascript:alert(1))' },
  })
  const anchor = wrapper.find('a')
  // DOMPurify removes javascript: hrefs
  expect(anchor.exists()).toBe(false)
})
```

---

### WR-02: `ADD_ATTR: ['target']` in DOMPurify config allows `target` on all HTML elements

**File:** `frontend/src/components/result/MarkdownRenderer.vue:39`

**Issue:** `DOMPurify.sanitize(html, { ADD_ATTR: ['target'] })` adds `target` to DOMPurify's global `ALLOWED_ATTR` list, meaning `target="..."` is allowed on every permitted HTML element, not just `<a>`. While `target` only has semantic meaning on `<a>`, `<form>`, `<area>`, and `<base>`, this is marginally over-permissive. The intended narrower config is:

```typescript
DOMPurify.sanitize(html, {
  ADD_ATTR: ['target'],
  // target is safe on <a>; no new executable surface is created
})
```

This is not exploitable today but is worth tightening. A safer approach uses a `BEFORE_SANITIZE_ATTRIBUTES` hook or restricts via `ALLOWED_ATTR` if you control the full allowed set. Given the current scope (read-only Markdown display), the risk is negligible, but the comment (`// ADD_ATTR allows 'target' which is not in DOMPurify's DEFAULT_ALLOWED_ATTR`) is slightly misleading: `target` IS in `DEFAULT_ALLOWED_ATTR` for `<a>` in many DOMPurify versions. Verify against the bundled version and remove `ADD_ATTR` if it is already permitted by default, to avoid widening the surface unnecessarily.

**Fix:** Check the actual DOMPurify version behavior and, if `target` is already default-allowed on `<a>`, remove the `ADD_ATTR` option entirely.

---

### WR-03: Neither `ResultView.spec.ts` nor `ChunkCard.spec.ts` asserts `revokeObjectURL` was called

**File:** `frontend/src/components/result/ResultView.spec.ts:75-89` and `frontend/src/components/result/ChunkCard.spec.ts:81-89`

**Issue:** Both specs stub `URL.createObjectURL` and `URL.revokeObjectURL`, but only the download-feedback state is asserted. If the `URL.revokeObjectURL(url)` call were removed from the implementation, both test suites would still pass. This means a Blob URL leak introduced by a future refactor would go undetected.

**Fix:** Add an assertion to each download test:
```typescript
// In ResultView.spec.ts — "shows download feedback" test
await downloadBtn.trigger('click')
expect(vi.mocked(URL.createObjectURL)).toHaveBeenCalledOnce()
expect(vi.mocked(URL.revokeObjectURL)).toHaveBeenCalledWith('blob:mock')

// In ChunkCard.spec.ts — "shows CheckIcon feedback" test
await wrapper.get('[aria-label="Baixar chunk como Markdown"]').trigger('click')
expect(vi.mocked(URL.revokeObjectURL)).toHaveBeenCalledWith('blob:mock')
```

---

### WR-04: YAML frontmatter in `buildMarkdownContent` is vulnerable to newline injection from API-provided fields

**File:** `frontend/src/components/result/ResultView.vue:22-46`

**Issue:** `buildMarkdownContent` constructs a YAML frontmatter block by string-interpolating API-provided fields directly:

```typescript
`title: ${meta.title || meta.source_filename}`,
`language: ${meta.language}`,
```

If any field (title, language, doc_type, ingested_at) contains a newline character, the YAML block is structurally broken. For example, a `title` of `"evil\n---\nmalicious: injected\n---"` produces:

```
---
title: evil
---
malicious: injected
---
language: en
...
```

This corrupts the downloaded Markdown file. This is not an XSS vector (the file is only downloaded, not rendered by the SPA), but it corrupts the output artifact that is the product's primary deliverable.

**Fix:** Escape newlines in frontmatter values before interpolation:
```typescript
function escapeFrontmatterValue(value: string): string {
  // Replace bare newlines so YAML remains single-line scalar
  return value.replace(/\r?\n/g, ' ').replace(/:/g, '\\:')
}

const frontmatter = [
  '---',
  `title: ${escapeFrontmatterValue(meta.title || meta.source_filename)}`,
  `language: ${escapeFrontmatterValue(meta.language)}`,
  // ...
].join('\n')
```

Alternatively, wrap values in YAML block scalars (`|`) or use a YAML serialization library.

---

### WR-05: HTML comment in `buildMarkdownContent` breaks if `section_title` contains `-->`

**File:** `frontend/src/components/result/ResultView.vue:37`

**Issue:** The per-chunk comment line is:
```typescript
`<!-- pages: ${chunk.page_start}-${chunk.page_end} | words: ${chunk.word_count} | section: ${chunk.section_title} -->`,
```

If `chunk.section_title` contains `-->` (e.g., `"Overview --> Details"`), the HTML comment closes prematurely:
```
<!-- pages: 1-2 | words: 5 | section: Overview --> Details -->
```

The text `" Details -->"` appears as raw content in the downloaded Markdown file, corrupting its structure. API-provided values must not be interpolated verbatim into HTML comment syntax.

**Fix:** Strip or escape `-->` sequences from the section_title before interpolation:
```typescript
const safeSection = (chunk.section_title ?? '').replace(/-->/g, '--\\>')
`<!-- pages: ${chunk.page_start}-${chunk.page_end} | words: ${chunk.word_count} | section: ${safeSection} -->`,
```

---

## Info

### IN-01: `style.css` is an orphaned Vite scaffold file — dead code

**File:** `frontend/src/style.css`

**Issue:** `style.css` (317 lines, default Vite scaffold content with hero component styles, social link styles, and unrelated custom properties) is not imported by `main.ts`, not linked from `index.html`, and not referenced anywhere in the source tree. Its variables (`--text`, `--bg`, `--border`, `--accent`) conflict with the OKLCH design token system in `assets/index.css` (which uses the Tailwind CSS variable bridge). The `@keyframes shimmer` and `.shimmer-gradient` defined in `style.css` duplicate definitions that also exist in `assets/index.css`.

**Fix:** Delete `frontend/src/style.css`. Retain the Phase 14-added rules (`.hljs` override, `::-webkit-scrollbar`, `scrollbar-width`) which are already correctly placed in `style.css:317-344` — migrate those to `assets/index.css` if they are not already there (they are: `assets/index.css` does not contain those scrollbar rules, so migration is needed before deletion).

---

### IN-02: `formatDate` throws on invalid ISO strings — no guard

**File:** `frontend/src/lib/formatters.ts:29-37`

**Issue:** `new Date('invalid-string')` produces an Invalid Date object. Calling `Intl.DateTimeFormat.format()` on an Invalid Date throws a `RangeError: Invalid time value`. `MetadataCard.vue` calls `formatDate(metadata.ingested_at)` where `ingested_at` is a raw API string. If the API returns a malformed or missing timestamp, the MetadataCard component throws during render, crashing the entire ResultView.

**Fix:**
```typescript
export function formatDate(isoString: string): string {
  const d = new Date(isoString)
  if (!Number.isFinite(d.getTime())) return '—'
  return new Intl.DateTimeFormat('pt-BR', {
    year: '2-digit',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(d)
}
```

Add a test case:
```typescript
it('returns em-dash for invalid date strings', () => {
  expect(formatDate('not-a-date')).toBe('—')
  expect(formatDate('')).toBe('—')
})
```

---

### IN-03: Hidden file input in `DropZone` has no accessible label

**File:** `frontend/src/components/upload/DropZone.vue:94-101`

**Issue:** The `<input type="file" class="sr-only">` has no `aria-label` or associated `<label>` element. Screen readers announce it as an unlabeled file upload control. The visually adjacent button ("Selecionar arquivo") has text content and is correctly described, but the underlying file input — which a screen reader can discover when navigating by form elements — is anonymous.

**Fix:**
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
