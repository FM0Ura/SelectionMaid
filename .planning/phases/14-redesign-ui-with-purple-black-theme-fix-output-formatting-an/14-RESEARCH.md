# Phase 14: Redesign UI with purple/black theme, fix output formatting, and add Markdown download - Research

**Researched:** 2026-05-26
**Domain:** Vue 3 UI theming, markdown-it plugins, Tailwind v4 prose customization, browser download API
**Confidence:** HIGH

---

## Summary

This phase has three self-contained deliverables: (1) a visual redesign swapping the neutral dark palette for a purple/black OKLCH palette, (2) improvements to the MarkdownRenderer component (syntax highlight, table borders and scroll, link targets), and (3) a Markdown download feature requiring a slugify utility and the browser Blob API.

All work is pure frontend — no backend changes. The locked decisions in 14-CONTEXT.md and the UI contract in 14-UI-SPEC.md collectively cover every visual detail. Research confirms those decisions are sound and adds API-level precision for implementation.

**Critical path insight:** The single new npm dependency is `markdown-it-highlightjs` (which pulls `highlight.js` as a production dependency). Neither package is installed yet. Both are confirmed legitimate on npm with verified GitHub source repos. All other deliverables use libraries already in `package.json` — no other installs are needed.

**Primary recommendation:** Install `markdown-it-highlightjs` and `highlight.js` first (Wave 0), then proceed through theme tokens → component glassmorphism → MarkdownRenderer upgrades → download feature, in that order. The CSS token rebase lands first to avoid fighting against the old neutral palette on every subsequent task.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Palette:**
- D-01: Background `#111118` (replaces `--bg: #16171d`)
- D-02: Accent `#9333ea` (purple-600) for borders, buttons, glows
- D-03: ChunkCards + MetadataCard glassmorphism: `bg-white/5 backdrop-blur-md border border-purple-900/40`
- D-04: Primary button ghost purple: outline idle, fill hover
- D-05: DropZone idle neutral border, hover purple
- D-06: h1 gradient text: `bg-gradient-to-r from-purple-400 to-white bg-clip-text text-transparent`
- D-07: ChunkCard hover glow purple (`shadow-purple-900/30`) — MetadataCard has no glow
- D-08: Custom scrollbar purple/transparent via `scrollbar-color` + WebKit pseudo-elements
- D-09: Error red `#ef4444`, processing purple pulsing

**MarkdownRenderer:**
- D-10: Table borders: `prose-table:border prose-table:border-purple-900/40`, thead `bg-purple-950/60`
- D-11: Tables wrap in `overflow-x-auto` div
- D-12: Syntax highlight via `markdown-it-highlightjs`, dark theme (github-dark or atom-one-dark)
- D-13: Links: `target="_blank"` + `rel="noopener noreferrer"` via markdown-it renderer override
- D-14: Chunk body max height: `max-h-[400px] overflow-y-auto` wrapping `<MarkdownRenderer>`
- D-15: Images: `max-width: 100%` via prose styling

**Download:**
- D-16: Both global (ResultView header) and per-chunk (ChunkCard icon button)
- D-17: Global button position: between heading block and "Novo Upload" button
- D-18: Filename: `{slugified-source_filename}-chunks.md`
- D-19: Format: YAML front-matter + chunks separated by `---` with `# Chunk N` headers
- D-20: Per-chunk: `DownloadIcon` icon-only button beside Copy button
- D-21: Download feedback: `CheckIcon` for 1.5s, then reverts

### Claude's Discretion
- Typography: maintain system-ui or adjust — Inter is already configured in `@theme inline`
- Glassmorphism intensity: backdrop-blur and card background opacity
- Easing and timing of purple processing pulse
- Exact prose padding/spacing in MarkdownRenderer
- Exact highlight.js theme (github-dark or atom-one-dark, both confirmed available)

### Deferred Ideas (OUT OF SCOPE)
- Raw/rendered toggle per chunk
- Dynamic themes by file type
- Line numbers in code blocks
- Custom typography (Inter decision already made in index.css)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RES-01 | Markdown chunks rendered as HTML (not raw text) | Already working; extend with highlightjs plugin and prose overrides |
| RES-03 | Copy per-chunk with clipboard button | Already working; extend with Download button at same position |
| RES-04 | Metadata panel with doc type, language, title, processing time | Already working; add glassmorphism to card |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CSS token redesign | Browser/Client | — | Pure CSS variables in `index.css` and `style.css`; no server involvement |
| Glassmorphism/glow on cards | Browser/Client | — | Tailwind utility classes on existing shadcn Card components |
| MarkdownRenderer syntax highlight | Browser/Client | — | markdown-it plugin runs at render time in the browser |
| MarkdownRenderer table scroll | Browser/Client | — | Renderer override wraps `<table>` in `<div class="overflow-x-auto">` |
| Download Blob generation | Browser/Client | — | `URL.createObjectURL(new Blob([...], {type: 'text/markdown'}))` — entirely client-side |
| slugifyFilename utility | Browser/Client | — | Pure string transform in `formatters.ts` |
| DropZone hover/drag states | Browser/Client | — | Tailwind class binding on existing `useDropZone` reactive state |

---

## Standard Stack

### Already Installed (no new installs needed for most of phase)

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| `tailwindcss` | 4.3.0 | Utility classes, arbitrary values, prose variants | `[VERIFIED: npm registry]` — in package.json |
| `@tailwindcss/typography` | 0.5.19 (devDep) | `prose-table:*`, `prose-thead:*`, etc. | `[VERIFIED: npm registry]` — in devDependencies |
| `markdown-it` | 14.2.0 | Markdown render engine | `[VERIFIED: npm registry]` — in package.json |
| `dompurify` | 3.4.6 | Sanitize rendered HTML | `[VERIFIED: npm registry]` — in package.json |
| `lucide-vue-next` | 1.0.0 | `DownloadIcon`, `CheckIcon` | `[VERIFIED: npm registry]` — in package.json |
| `@vueuse/core` | 14.3.0 | `useClipboard` (pattern for download feedback) | `[VERIFIED: npm registry]` — in package.json |

### New Installs Required

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `markdown-it-highlightjs` | 4.3.0 | Registers highlight.js as syntax highlight backend for markdown-it | De facto standard plugin for this combination; official GitHub repo; no postinstall scripts |
| `highlight.js` | 11.11.1 | Syntax highlight engine with `github-dark` theme CSS | Ships as a dependency of `markdown-it-highlightjs`; already pulled transitively but should be explicit for theme CSS import |

**Installation:**
```bash
cd frontend && npm install markdown-it-highlightjs highlight.js
```

Note: `highlight.js` is already a declared dependency of `markdown-it-highlightjs` (`"highlight.js": "^11.9.0"`), so it will install automatically. Listing it explicitly ensures the theme CSS file is importable directly.

---

## Package Legitimacy Audit

> slopcheck is installed but incorrectly targets PyPI for these npm packages. Manual npm verification used instead.

| Package | Registry | Age | Source Repo | Postinstall | Disposition |
|---------|----------|-----|-------------|-------------|-------------|
| `markdown-it-highlightjs` | npm | ~4 yrs (v1.0 2018, v4.3.0 Feb 2026) | github.com/valeriangalliat/markdown-it-highlightjs | None | Approved — `[ASSUMED]` (slopcheck ecosystem mismatch) |
| `highlight.js` | npm | ~13 yrs (active, v11.11.1 Dec 2024) | github.com/highlightjs/highlight.js | None | Approved — `[ASSUMED]` (slopcheck ecosystem mismatch) |

**Packages removed due to slopcheck [SLOP] verdict:** none

**Packages flagged as suspicious [SUS]:** none

**Note on slopcheck:** `slopcheck install markdown-it-highlightjs highlight.js` returned `[SLOP]` because slopcheck checked PyPI (wrong ecosystem). Both packages are confirmed legitimate on npm via `npm view` (canonical source) AND verified against official GitHub repos (authoritative source). The `[ASSUMED]` tag reflects the slopcheck tooling limitation, not any legitimacy concern.

---

## Architecture Patterns

### System Architecture Diagram

```
User action (drag/upload/view)
    │
    ▼
useUpload (composable) ─── success state ───► ExtractionResponse
    │                                               │
    ▼                                               ▼
App.vue (AnimatePresence)              ResultView.vue
    │                                   ├── MetadataCard.vue  ← glassmorphism (D-03)
    ├── DropZone.vue                    ├── [Download .MD btn]  ← new (D-17)
    │   └── hover/drag → purple         └── ChunkCard.vue ×N   ← glassmorphism + glow (D-03, D-07)
    │       border (D-05)                   ├── [Copy btn] + [Download icon btn] ← new (D-20)
    │                                       └── MarkdownRenderer.vue
    │                                           ├── markdown-it + highlightjs plugin (D-12)
    │                                           ├── renderer.rules.link_open override (D-13)
    │                                           ├── renderer.rules.table override (D-11)
    │                                           └── DOMPurify.sanitize() — class attr allowed
    │
    ▼
style.css + index.css (.dark block)
    └── OKLCH purple tokens → all shadcn components inherit via CSS custom properties
```

### Recommended Project Structure

No new directories needed. All changes are in-place edits:

```
frontend/src/
├── assets/index.css            ← UPDATE: .dark OKLCH tokens (D-01 through D-09)
├── style.css                   ← UPDATE: --bg, --accent, scrollbar (D-01, D-08)
├── App.vue                     ← UPDATE: h1 gradient (D-06)
├── lib/formatters.ts           ← UPDATE: add slugifyFilename()
├── components/
│   ├── upload/DropZone.vue     ← UPDATE: hover purple border (D-05)
│   └── result/
│       ├── ChunkCard.vue       ← UPDATE: glassmorphism, glow, download button (D-03, D-07, D-20, D-21)
│       ├── MetadataCard.vue    ← UPDATE: glassmorphism only (D-03)
│       ├── MarkdownRenderer.vue ← UPDATE: highlightjs, table wrapper, link target (D-10–D-15)
│       └── ResultView.vue      ← UPDATE: global download button (D-16, D-17)
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Syntax highlighting in fenced code blocks | Custom regex colorizer | `markdown-it-highlightjs` plugin + `highlight.js` | 192 languages, tested tokenizer, CSS-based theming |
| Prose element targeting in Tailwind | Custom CSS selectors fighting prose specificity | Element modifier variants (`prose-table:`, `prose-thead:`, etc.) | Built into `@tailwindcss/typography` 0.5.19 — verified in source |
| Download trigger | Hidden `<a>` element with server endpoint | `URL.createObjectURL(new Blob(...))` + `<a>.click()` | Standard browser API, no server, works everywhere |
| HTML sanitization | Trust hljs output directly | Keep existing `DOMPurify.sanitize()` — `class` attr is allowed by default | DOMPurify allows `class` in `DEFAULT_ALLOWED_ATTR`; hljs spans preserve their classes |

---

## Critical Technical Findings

### 1. markdown-it-highlightjs API (ESM in Vite)

The package ships CJS (`dist/index.js`). Vite handles CJS→ESM interop automatically. The correct import pattern in a Vite/Vue 3 project is:

```typescript
// Source: [CITED: github.com/valeriangalliat/markdown-it-highlightjs/blob/main/src/index.ts]
import MarkdownIt from 'markdown-it'
import highlightjs from 'markdown-it-highlightjs'

const markdown = new MarkdownIt({ html: false, linkify: true, typographer: true })
  .use(highlightjs, { auto: true, code: true, inline: false })
```

The plugin automatically uses the full `highlight.js` bundle (all languages). No `hljs` instance needs to be passed — the plugin's default imports it.

### 2. highlight.js Theme Import (github-dark confirmed)

`github-dark.css` is confirmed in the npm tarball at `styles/github-dark.css`. The package's `exports` field exposes `./styles/*`, so Vite resolves the import correctly:

```typescript
// In MarkdownRenderer.vue <script setup> or in index.css
import 'highlight.js/styles/github-dark.css'
```

This is the correct Vite ESM import path. The CSS is plain static CSS with no JS — it styles `.hljs` and `.hljs-*` class names that highlight.js adds to the output spans.

The github-dark background is `#0d1117`. This will conflict with the purple card background unless the `pre` element is styled to override it. The UI-SPEC resolves this via: `prose-pre:bg-purple-950/60 prose-pre:border prose-pre:border-purple-900/40`. This overrides the hljs theme's `pre` background, but the `code` block inside retains the syntax colors. The prose override must come after the hljs CSS import to take precedence.

### 3. DOMPurify and highlight.js class attributes

`class` is in DOMPurify's `DEFAULT_ALLOWED_ATTR` list (verified in source). The `DOMPurify.sanitize(markdown.render(content))` call in MarkdownRenderer will NOT strip `class="hljs language-xxx"` attributes from highlight.js output. No DOMPurify configuration changes needed.

### 4. markdown-it renderer.rules.link_open — target="_blank"

```typescript
// Source: [CITED: markdown-it.github.io/#Renderer]
const defaultLinkOpen = markdown.renderer.rules.link_open
  || function (tokens: Token[], idx: number, options: Options, _env: unknown, self: Renderer) {
      return self.renderToken(tokens, idx, options)
    }

markdown.renderer.rules.link_open = function (tokens, idx, options, env, self) {
  tokens[idx].attrSet('target', '_blank')
  tokens[idx].attrSet('rel', 'noopener noreferrer')
  return defaultLinkOpen(tokens, idx, options, env, self)
}
```

This must be set up once at module level (or in `setup()`), after `.use(highlightjs)`.

### 5. markdown-it table renderer override (overflow-x-auto wrapper)

markdown-it renders tables as `<table>...</table>`. To wrap them in a scrollable div:

```typescript
// Source: [ASSUMED] — standard markdown-it renderer override pattern
markdown.renderer.rules.table_open = function () {
  return '<div class="overflow-x-auto"><table>'
}
markdown.renderer.rules.table_close = function () {
  return '</table></div>'
}
```

### 6. Tailwind v4 prose element modifier variants

Verified in `@tailwindcss/typography` 0.5.19 source (`src/index.js` lines 96–116): `prose-table`, `prose-thead`, `prose-tr`, `prose-th`, `prose-td`, `prose-code`, `prose-pre`, `prose-a` are all registered as Tailwind variants via `addVariant()`. These work as class modifiers on the `.prose` container in Tailwind v4 exactly as in the UI-SPEC.

The plugin is loaded in `index.css` via `@plugin "@tailwindcss/typography"` — already configured.

**Tailwind v4 note:** In v4, modifier stacking order for hover is `prose-a:hover:text-*` (hover comes last), which is the opposite of v3. The UI-SPEC doesn't use hover on prose element modifiers, so this is a non-issue here.

### 7. Download Blob pattern (browser API)

```typescript
// Source: [ASSUMED] — standard browser API
function downloadMarkdown(content: string, filename: string): void {
  const blob = new Blob([content], { type: 'text/markdown; charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)  // release memory
}
```

`URL.createObjectURL` and `URL.revokeObjectURL` are available in all modern browsers. No polyfill needed. The `download` attribute on `<a>` triggers a file save dialog.

### 8. shadcn CSS token architecture — authoritative token source

The `.dark` block in `frontend/src/assets/index.css` is the authoritative shadcn token source. The `frontend/src/style.css` file contains legacy non-shadcn variables (`--bg`, `--accent`, `--border` in `:root` and the `@media (prefers-color-scheme: dark)` block) that are NOT used by shadcn components.

**Critical implication:** The app uses `class="bg-background text-foreground"` (shadcn tokens from `.dark` in `index.css`), not `var(--bg)` from `style.css`. The redesign must update BOTH files:
- `index.css` `.dark` block: update `--background`, `--card`, `--primary`, `--border`, etc. to purple OKLCH
- `style.css`: update `--bg` (used in `#app border-inline`), add scrollbar CSS

The `App.vue` main element uses `bg-background` (shadcn token) — correct.

### 9. `.dark` class is already applied

The app uses `@custom-variant dark (&:is(.dark *))` in `index.css`. The `.dark` class must be present on `<html>`. The existing components already work with dark mode, confirming `.dark` is applied. No `<html class="dark">` change needed.

### 10. ProcessingCard uses `animate-spin text-primary`

ProcessingCard.vue currently uses `text-primary` for the `LoaderCircle`. Once `--primary` changes to purple OKLCH, the spinner automatically becomes purple. No ProcessingCard changes needed for D-09.

### 11. slugifyFilename — Unicode normalization for Portuguese diacritics

The UI-SPEC provides the full implementation including `normalize('NFD').replace(/[̀-ͯ]/g, '')` for diacritic stripping. This handles "Calendário" → "calendario" correctly. The regex `̀-ͯ` (combining diacritical marks block) covers all Portuguese accents.

**Important:** The regex range in the UI-SPEC uses Unicode code points U+0300 through U+036F. In the actual TypeScript source this must be written as `̀-ͯ` or the escaped form shown in the spec. Verify the spec's literal character range compiles correctly — use the explicit `̀-ͯ` form to be safe.

```typescript
// [CITED: 14-UI-SPEC.md]
export function slugifyFilename(filename: string): string {
  const base = filename.replace(/\.[^.]+$/, '')
  return base
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}
```

---

## Common Pitfalls

### Pitfall 1: highlight.js theme background overrides prose-pre styling

**What goes wrong:** highlight.js `github-dark.css` sets `background: #0d1117` on `.hljs` (the `<code>` inside `<pre>`). This conflicts with the desired `prose-pre:bg-purple-950/60` style.

**Why it happens:** `.hljs` background has higher specificity than the `.prose pre code` selector.

**How to avoid:** Style the `<pre>` wrapper with `prose-pre:bg-purple-950/60` AND also override `.hljs { background: transparent; }` in `style.css` or a `@layer components` block. The `<pre>` provides the visual card background; the inner `.hljs` background becomes transparent.

**Warning signs:** Code blocks appear with a mismatched dark blue/gray background inside purple cards.

### Pitfall 2: DOMPurify stripping table overflow wrapper

**What goes wrong:** The `table_open` renderer override injects `<div class="overflow-x-auto">`. DOMPurify allows `div` elements and `class` attributes by default, so this is safe. However if `DOMPurify.sanitize` is called with `ALLOWED_TAGS` it may strip the wrapper div.

**Why it happens:** Only if someone restricts `ALLOWED_TAGS` in the future.

**How to avoid:** Current `DOMPurify.sanitize(html)` call has no config options — uses safe defaults. Do not add `ALLOWED_TAGS` restriction.

**Warning signs:** Tables appear without scroll capability on wide content.

### Pitfall 3: markdown-it module created inside `computed()` (re-created on every render)

**What goes wrong:** If `new MarkdownIt()` and `.use()` calls are placed inside `computed()`, a new instance is created for every render cycle, resetting the plugin configuration.

**Why it happens:** The current MarkdownRenderer.vue creates `markdown` at module scope (outside `setup()`), which is correct. The change adds `.use(highlightjs)` to the same module-scope instance. As long as this remains at module scope, it's correct.

**How to avoid:** Keep the `markdown` instance and all `.use()` + `renderer.rules` assignments at module scope (top of `<script setup>`, before `const props = defineProps()`).

**Warning signs:** Syntax highlighting works on first render but disappears on re-renders.

### Pitfall 4: ResultView "Novo Upload" button emit conflicts with Download button

**What goes wrong:** The `ResultView` header has one button ("Novo Upload") that emits `reset`. The test `wrapper.get('button').trigger('click')` selects the FIRST button. Adding a "Download .MD" button before "Novo Upload" changes which button `.get('button')` targets.

**Why it happens:** `wrapper.get('button')` returns the first matching button in DOM order.

**How to avoid:** Place the "Download .MD" button between the heading block and "Novo Upload". Since the test clicks the first button and expects `reset` to be emitted, the Download button must be positioned AFTER "Novo Upload" in DOM order, OR update the test to use a more specific selector (`wrapper.get('[aria-label="Baixar todos..."]')`).

**Per UI-SPEC:** The layout order in the flex row is `[heading block] [Download .MD button] [Novo Upload button]`. This means "Novo Upload" is the LAST button in DOM order. The test `wrapper.get('button')` will now target the Download button. **The ResultView.spec.ts test must be updated** to select the "Novo Upload" button by a more specific selector.

**Warning signs:** `ResultView.spec.ts` test "emits reset when the new upload button is clicked" fails.

### Pitfall 5: Blob download triggers navigate-away warning in some environments

**What goes wrong:** In some test environments (jsdom), `URL.createObjectURL` and programmatic `.click()` on an `<a>` element may not work.

**Why it happens:** jsdom does not implement the full navigation/download stack.

**How to avoid:** Mock `URL.createObjectURL` and `URL.revokeObjectURL` in download-related tests. Test the download function output (the blob content string) separately from the DOM interaction.

### Pitfall 6: Inter font already in index.css — no separate install needed

**What goes wrong:** Planning an npm font install when Inter is already loaded via Google Fonts in `index.css` line 1: `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap')`.

**How to avoid:** The `--font-sans: 'Inter', sans-serif` in `@theme inline` is already set. No font changes needed.

---

## Code Examples

### markdown-it-highlightjs setup in MarkdownRenderer.vue

```typescript
// Source: [CITED: github.com/valeriangalliat/markdown-it-highlightjs (src/index.ts + README)]
// Source: [CITED: markdown-it.github.io/#Renderer]
import MarkdownIt from 'markdown-it'
import type { Token, Options, Renderer } from 'markdown-it'
import highlightjs from 'markdown-it-highlightjs'
import 'highlight.js/styles/github-dark.css'

const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
})
  .use(highlightjs, { auto: true, code: true, inline: false })

// Override link_open to add target=_blank
const defaultLinkOpen = markdown.renderer.rules.link_open
  || function (tokens: Token[], idx: number, options: Options, _env: unknown, self: Renderer) {
      return self.renderToken(tokens, idx, options)
    }

markdown.renderer.rules.link_open = function (tokens, idx, options, env, self) {
  tokens[idx].attrSet('target', '_blank')
  tokens[idx].attrSet('rel', 'noopener noreferrer')
  return defaultLinkOpen(tokens, idx, options, env, self)
}

// Override table_open/close to wrap with overflow-x-auto
markdown.renderer.rules.table_open = () => '<div class="overflow-x-auto"><table>'
markdown.renderer.rules.table_close = () => '</table></div>'
```

### MarkdownRenderer.vue template (updated prose classes)

```html
<!-- Source: [CITED: @tailwindcss/typography README — element modifiers] -->
<!-- Source: [CITED: 14-UI-SPEC.md — MarkdownRenderer Formatting Additions] -->
<div
  class="prose prose-invert prose-sm max-w-none text-foreground
         prose-headings:text-foreground
         prose-a:text-purple-400 prose-a:no-underline prose-a:hover:underline
         prose-strong:text-foreground
         prose-code:bg-purple-950/40 prose-code:text-purple-200 prose-code:rounded prose-code:px-1 prose-code:before:content-none prose-code:after:content-none
         prose-pre:bg-purple-950/60 prose-pre:border prose-pre:border-purple-900/40
         prose-table:border prose-table:border-purple-900/40
         prose-thead:bg-purple-950/60"
  v-html="sanitizedHtml"
/>
```

**Note on inline code backtick artifacts:** By default, Tailwind Typography adds `::before` and `::after` pseudo-elements with backtick content to `code` elements. Adding `prose-code:before:content-none prose-code:after:content-none` removes them — this is standard practice when using syntax highlighting.

### Download blob pattern (ResultView.vue)

```typescript
// Source: [ASSUMED] — standard browser API
import { ref } from 'vue'
import { Download, Check } from 'lucide-vue-next'
import type { ExtractionResponse } from '@/types/api'
import { slugifyFilename } from '@/lib/formatters'

function buildMarkdownContent(data: ExtractionResponse): string {
  const meta = data.metadata
  const frontmatter = [
    '---',
    `title: ${meta.title || meta.source_filename}`,
    `language: ${meta.language}`,
    `doc_type: ${meta.doc_type}`,
    `ingested_at: ${meta.ingested_at}`,
    `chunk_count: ${meta.chunk_count}`,
    '---',
    '',
  ].join('\n')

  const chunks = data.chunks.map((chunk, i) => [
    `# Chunk ${i + 1}`,
    `<!-- pages: ${chunk.page_start}-${chunk.page_end} | words: ${chunk.word_count} | section: ${chunk.section_title} -->`,
    '',
    chunk.content,
    '',
    '---',
    '',
  ].join('\n')).join('\n')

  return frontmatter + chunks
}

const downloaded = ref(false)

function downloadAll(data: ExtractionResponse): void {
  const content = buildMarkdownContent(data)
  const filename = `${slugifyFilename(data.metadata.source_filename)}-chunks.md`
  const blob = new Blob([content], { type: 'text/markdown; charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
  downloaded.value = true
  setTimeout(() => { downloaded.value = false }, 1500)
}
```

### Per-chunk download (ChunkCard.vue)

```typescript
// Source: [ASSUMED] — same browser API
const chunkDownloaded = ref(false)

function downloadChunk(chunk: Chunk): void {
  const sectionSlug = chunk.section_title
    ? slugifyFilename(chunk.section_title)
    : `section-${chunk.chunk_index + 1}`
  const filename = `chunk-${chunk.chunk_index + 1}-${sectionSlug}.md`
  const blob = new Blob([chunk.content], { type: 'text/markdown; charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
  chunkDownloaded.value = true
  setTimeout(() => { chunkDownloaded.value = false }, 1500)
}
```

### Custom scrollbar CSS (style.css addition)

```css
/* Source: [CITED: 14-UI-SPEC.md — Custom Scrollbar] */
/* CSS Scrolling Level 2 — supported in Firefox 64+, Chrome 121+, Edge 121+ */
html, body {
  scrollbar-width: thin;
  scrollbar-color: oklch(0.558 0.243 293 / 0.5) transparent;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: oklch(0.558 0.243 293 / 0.5);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: oklch(0.558 0.243 293 / 0.8);
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@app.on_event("startup")` for FastAPI | `lifespan` context manager | FastAPI 0.95.0 | Backend only; not relevant here |
| Tailwind v3 `tailwind.config.js` prose customization | Tailwind v4 `@plugin` directive + element modifier variants | Tailwind v4 | `@tailwindcss/typography` loaded via `@plugin` in CSS, same modifier API |
| Tailwind v3 hover modifier order: `hover:prose-a:*` | Tailwind v4 hover modifier order: `prose-a:hover:*` | Tailwind v4 | Phase uses no hover on prose modifiers — non-issue |
| `@media (prefers-color-scheme: dark)` in style.css | Fixed `.dark` class on `<html>` via shadcn | Phase 14 redesign | `style.css` dark media query becomes dead code; shadcn `.dark` block is the only source of truth |

**Deprecated/outdated:**
- `--bg: #16171d` in `style.css` `:root`: replaced by `--background` OKLCH in `index.css` `.dark` block
- `@media (prefers-color-scheme: dark) :root` block in `style.css`: will become dead code after redesign (shadcn `.dark` class is always active)

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `markdown-it-highlightjs` 4.3.0 Vite ESM import works via CJS interop | Standard Stack / Code Examples | Low — Vite's CJS interop is robust; identical pattern used by other markdown-it plugins |
| A2 | `URL.createObjectURL` is available in the jsdom test environment | Common Pitfalls #5 | Low — jsdom supports it but may not trigger downloads; download logic should be tested by inspecting blob content, not DOM behavior |
| A3 | `renderer.rules.table_open` override wrapping `<div>` passes DOMPurify | Critical Technical Finding #2 | Low — DOMPurify allows `div` and `class` by default (confirmed in source) |
| A4 | `slopcheck` flagged packages as [SLOP] due to PyPI ecosystem mismatch | Package Legitimacy Audit | Low — npm view confirms both packages exist with correct GitHub repos; no postinstall scripts |
| A5 | `prose-code:before:content-none prose-code:after:content-none` removes backtick artifacts in Tailwind v4 | Code Examples | Medium — standard pattern for v3; verify v4 prose doesn't rename these; if it fails, use `@layer components { .prose code::before, .prose code::after { content: none; } }` as fallback |

---

## Open Questions

1. **ResultView.spec.ts test for "emits reset" will break**
   - What we know: The test uses `wrapper.get('button')` (first button). Adding Download .MD button before Novo Upload changes button order per UI-SPEC.
   - What's unclear: Whether the planner wants to fix the test as part of the Download task or as a separate task.
   - Recommendation: Update `ResultView.spec.ts` in the same task that adds the Download button — use `wrapper.get('[aria-label="Baixar todos os chunks como arquivo Markdown"]')` for Download and keep the reset test unchanged (it will now correctly target the first button IF Download button is the first in DOM order, or use `wrapper.findAll('button').at(-1)` for Novo Upload).

2. **`prose-code:before:content-none` in Tailwind v4**
   - What we know: In Tailwind v3, `prose-code:before:content-none` was the standard fix for backtick artifacts.
   - What's unclear: Whether Tailwind v4 uses the same modifier chaining syntax for `::before` pseudo-elements on prose element modifiers.
   - Recommendation: Planner should note this as a potential quick CSS override in `style.css` if the Tailwind v4 class syntax doesn't work.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js / npm | Package install | ✓ | (project uses npm) | — |
| `markdown-it-highlightjs` | D-12 syntax highlight | ✗ (not installed) | 4.3.0 on npm | — (must install) |
| `highlight.js` | D-12 syntax highlight, github-dark theme | ✗ (not installed) | 11.11.1 on npm | — (must install) |
| Vitest baseline | All tests | ✓ | 4.1.7 | — |

**Missing dependencies with no fallback:**
- `markdown-it-highlightjs` and `highlight.js` — must be installed before MarkdownRenderer changes

**Missing dependencies with fallback:** none

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.7 |
| Config file | `frontend/vitest.config.ts` |
| Quick run command | `cd frontend && npm run test:unit` |
| Full suite command | `cd frontend && npm run test:unit` |

Baseline: 15 test files, 52 tests, all passing.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RES-01 | Markdown renders with syntax highlighting | unit | `vitest run src/components/result/MarkdownRenderer.spec.ts` | ✅ |
| RES-01 | Table wrapped in overflow-x-auto | unit | `vitest run src/components/result/MarkdownRenderer.spec.ts` | ✅ (extend) |
| RES-01 | Links get target=_blank rel=noopener | unit | `vitest run src/components/result/MarkdownRenderer.spec.ts` | ✅ (extend) |
| RES-03 | ChunkCard download button shows CheckIcon feedback | unit | `vitest run src/components/result/ChunkCard.spec.ts` | ✅ (extend) |
| D-18 | slugifyFilename handles Portuguese diacritics | unit | `vitest run src/lib/formatters.spec.ts` | ✅ (extend) |
| D-16 | ResultView shows global Download .MD button | unit | `vitest run src/components/result/ResultView.spec.ts` | ✅ (extend) |

### Wave 0 Gaps

- [ ] `frontend/src/components/result/MarkdownRenderer.spec.ts` — needs new test cases for syntax highlight output, table scroll wrapper, and link target attributes
- [ ] `frontend/src/components/result/ChunkCard.spec.ts` — needs test for download button presence and 1.5s CheckIcon feedback
- [ ] `frontend/src/components/result/ResultView.spec.ts` — needs selector update for "emits reset" test (button order changes); add test for Download .MD button
- [ ] `frontend/src/lib/formatters.spec.ts` — add `slugifyFilename` test cases including Portuguese diacritics

---

## Security Domain

The phase adds no authentication, no server endpoints, and no new data ingestion. The threat surface is limited.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | — |
| V3 Session Management | No | — |
| V4 Access Control | No | — |
| V5 Input Validation | Partial | `DOMPurify.sanitize()` continues to sanitize markdown-it output; hljs spans are allowed via default `class` attribute allowlist |
| V6 Cryptography | No | — |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| XSS via highlight.js class injection | Tampering | DOMPurify sanitizes all output; `class` is in DEFAULT_ALLOWED_ATTR but script injection via class is not possible |
| Malicious filenames in download `download` attribute | Tampering | `slugifyFilename()` strips all non-alphanumeric characters; output is safe for `download` attribute |

---

## Sources

### Primary (HIGH confidence)
- `frontend/node_modules/@tailwindcss/typography/src/index.js` lines 80–116 — element modifier variants confirmed in source
- `frontend/node_modules/dompurify/dist/purify.cjs.js` line 315 — `class` in `DEFAULT_ALLOWED_ATTR` confirmed
- `frontend/node_modules/markdown-it/README.md` — `renderer.rules.link_open` pattern, highlight option
- `npm view markdown-it-highlightjs` + `npm view highlight.js` — versions and registry data
- `npm pack highlight.js --dry-run` — `styles/github-dark.css` confirmed in tarball
- `highlight.js` exports field — `./styles/*` confirmed

### Secondary (MEDIUM confidence)
- `gh api repos/valeriangalliat/markdown-it-highlightjs/contents/src/index.ts` — ESM default export confirmed
- `gh api repos/valeriangalliat/markdown-it-highlightjs/readme` — API options confirmed
- `markdown-it.github.io/#Renderer` — `attrSet` + `renderToken` pattern confirmed

### Tertiary (LOW confidence — marked [ASSUMED])
- `URL.createObjectURL` download pattern — standard browser API, confirmed by MDN; jsdom behavior in tests is assumed
- `prose-code:before:content-none` Tailwind v4 behavior — confirmed in v3 docs; v4 behavior assumed compatible

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified on npm registry, source repos confirmed
- Architecture: HIGH — all changes are in-place edits to existing files, dependencies confirmed
- Pitfalls: HIGH — confirmed via DOMPurify source and markdown-it internals; download button ordering is a concrete issue derived from reading test source

**Research date:** 2026-05-26
**Valid until:** 2026-06-25 (30 days — stable libraries)
