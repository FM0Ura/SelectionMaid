---
phase: 14-redesign-ui-with-purple-black-theme-fix-output-formatting-an
fixed_at: 2026-05-27T00:00:00Z
review_path: .planning/phases/14-redesign-ui-with-purple-black-theme-fix-output-formatting-an/14-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 14: Code Review Fix Report

**Fixed at:** 2026-05-27
**Source review:** .planning/phases/14-redesign-ui-with-purple-black-theme-fix-output-formatting-an/14-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5 (1 Critical, 4 Warning)
- Fixed: 5
- Skipped: 0

## Fixed Issues

### CR-01: `formatDate` test hardcodes UTC-3 time offset — fails in any non-Brazilian CI environment

**Files modified:** `frontend/src/lib/formatters.ts`
**Commit:** 12db82b
**Applied fix:** Added `timeZone: 'America/Sao_Paulo'` to the `Intl.DateTimeFormat` options in `formatDate`. The existing test regex `/26\/05\/26,? 12:30/` was already correct for the UTC-3 rendering of `2026-05-26T15:30:00.000Z` and required no change — the fix makes the formatter deterministic so the test passes on any host timezone including UTC CI environments.

### WR-01: Premature `URL.revokeObjectURL` can silently break file downloads in Firefox

**Files modified:** `frontend/src/components/result/ResultView.vue`, `frontend/src/components/result/ChunkCard.vue`
**Commit:** 18e1e27
**Applied fix:** In both `downloadAll` (ResultView) and `downloadChunk` (ChunkCard): appended anchor to `document.body` before `click()`, removed it with `removeChild` after, and deferred `URL.revokeObjectURL` via `setTimeout(..., 0)`. This ensures the browser can queue the blob fetch before the URL is revoked and satisfies Firefox's requirement for the anchor to be in the live DOM.

### WR-02: `copyChunk` async rejection is silently swallowed

**Files modified:** `frontend/src/components/result/ChunkCard.vue`
**Commit:** 32889af
**Applied fix:** Wrapped `await copy(props.chunk.content)` in a `try/catch` block. The catch branch emits `console.warn('Clipboard copy failed')` as a minimal fallback, preventing the unhandled promise rejection from being invisible to the user and laying the groundwork for a future error toast.

### WR-03: `ResultView` section missing `mx-auto` — result content is left-aligned on wide viewports

**Files modified:** `frontend/src/components/result/ResultView.vue`
**Commit:** 174c18c
**Applied fix:** Added `mx-auto` to the section's class list: `class="w-full max-w-4xl mx-auto space-y-5"`. This centers the result panel on viewports wider than `max-w-4xl` (~896px), consistent with the upload view layout.

### WR-04: YAML frontmatter and HTML comment in `buildMarkdownContent` vulnerable to injection

**Files modified:** `frontend/src/components/result/ResultView.vue`
**Commit:** 8ebf93f
**Applied fix:** Added two sanitizer helpers inside `buildMarkdownContent`: `safeScalar` strips CR/LF characters from string fields before YAML frontmatter interpolation (prevents newline-based key injection), and `safeComment` escapes `-->` sequences in `section_title` before HTML comment interpolation (prevents premature comment close). Applied `safeScalar` to `title`, `language`, and `doc_type`; applied `safeComment` to `section_title`. Numeric/typed fields `ingested_at` and `chunk_count` remain unmodified as they are safe by type.

---

_Fixed: 2026-05-27_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
