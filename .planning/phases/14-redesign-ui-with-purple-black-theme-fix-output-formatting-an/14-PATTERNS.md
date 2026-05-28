# Phase 14: Redesign UI with purple/black theme, fix output formatting, and add Markdown download - Pattern Map

**Mapped:** 2026-05-26
**Files analyzed:** 8
**Analogs found:** 8 / 8

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `frontend/src/assets/index.css` | config | transform | `frontend/src/assets/index.css` (self — extend `.dark` block) | exact |
| `frontend/src/style.css` | config | transform | `frontend/src/style.css` (self — update `:root` vars, add scrollbar) | exact |
| `frontend/src/App.vue` | component | request-response | `frontend/src/App.vue` (self — add gradient class to existing `h1`) | exact |
| `frontend/src/lib/formatters.ts` | utility | transform | `frontend/src/lib/formatters.ts` (self — add `slugifyFilename` beside existing formatters) | exact |
| `frontend/src/components/result/ChunkCard.vue` | component | request-response | `frontend/src/components/result/ChunkCard.vue` (self — add download button + glassmorphism) | exact |
| `frontend/src/components/result/MetadataCard.vue` | component | request-response | `frontend/src/components/result/MetadataCard.vue` (self — add glassmorphism classes only) | exact |
| `frontend/src/components/result/MarkdownRenderer.vue` | component | transform | `frontend/src/components/result/MarkdownRenderer.vue` (self — add highlightjs plugin + prose overrides) | exact |
| `frontend/src/components/result/ResultView.vue` | component | request-response | `frontend/src/components/result/ResultView.vue` (self — add global download button) | exact |

---

## Pattern Assignments

### `frontend/src/assets/index.css` (config, transform)

**Analog:** Self — update the `.dark` block (lines 109–141). This is the authoritative shadcn token source. All shadcn components inherit their colors from these OKLCH custom properties via `class="bg-background"` etc.

**Existing `.dark` block** (lines 109–141):
```css
.dark {
    --background: oklch(0.145 0 0);
    --foreground: oklch(0.985 0 0);
    --card: oklch(0.205 0 0);
    --card-foreground: oklch(0.985 0 0);
    --primary: oklch(0.922 0 0);
    --primary-foreground: oklch(0.205 0 0);
    --secondary: oklch(0.269 0 0);
    --muted: oklch(0.269 0 0);
    --muted-foreground: oklch(0.708 0 0);
    --accent: oklch(0.269 0 0);
    --destructive: oklch(0.704 0.191 22.216);
    --border: oklch(1 0 0 / 10%);
    --input: oklch(1 0 0 / 15%);
    --ring: oklch(0.556 0 0);
    /* ... */
}
```

**What changes (D-01 through D-09):** Replace the existing `.dark` block with purple OKLCH values:
- `--background` → `oklch(0.13 0.02 293)` (approx. `#111118`)
- `--primary` → `oklch(0.558 0.243 293)` (approx. `#9333ea`, purple-600)
- `--primary-foreground` → `oklch(0.985 0 0)`
- `--card` → `oklch(0.16 0.02 293 / 0.5)` (glassmorphism base — card background)
- `--border` → `oklch(0.34 0.12 293 / 0.4)` (purple-900/40)
- `--destructive` → `oklch(0.628 0.258 29)` (approx. `#ef4444`, red-500) — unchanged severity but confirm value
- `--ring` → `oklch(0.558 0.243 293 / 0.5)`

**`@custom-variant dark` line (line 12) — do not touch:**
```css
@custom-variant dark (&:is(.dark *));
```
The `.dark` class is already applied on `<html>` and active. Only update token values inside the `.dark {}` block.

---

### `frontend/src/style.css` (config, transform)

**Analog:** Self — currently has legacy `--bg`, `--accent` vars under `:root` and `@media (prefers-color-scheme: dark)`.

**Existing `:root` vars to update** (lines 1–31):
```css
:root {
  --bg: #fff;
  --border: #e5e4e7;
  --accent: #aa3bff;
  /* ... */
}
```

**Existing dark media query** (lines 52–70):
```css
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #16171d;   /* ← D-01: replace with #111118 */
    --accent: #c084fc;
    /* ... */
  }
}
```

**What changes:**
1. Update `--bg: #111118` in the dark media query (D-01).
2. Update `--accent: #9333ea` in the dark media query (D-02).
3. Add `.hljs { background: transparent; }` override to neutralize highlight.js github-dark background (Pitfall 1 from RESEARCH.md).
4. Add custom scrollbar CSS block at end of file (D-08 — new section, no existing analog):

```css
/* Custom scrollbar — purple/transparent */
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

/* Neutralize hljs github-dark background inside prose cards */
.hljs {
  background: transparent !important;
}
```

**The `#app` border-inline rule** (lines 178–189) uses `var(--border)` — this refers to the legacy `--border` in `style.css`, not the shadcn `--border`. It stays as-is unless explicitly in scope.

---

### `frontend/src/App.vue` (component, request-response)

**Analog:** Self — current h1 is at line 25 inside the upload section.

**Current h1** (line 25):
```html
<h1 class="text-3xl font-semibold leading-tight">Transforme documentos em chunks Markdown</h1>
```

**Target change (D-06):** Add gradient text classes:
```html
<h1 class="text-3xl font-semibold leading-tight bg-gradient-to-r from-purple-400 to-white bg-clip-text text-transparent">
  Transforme documentos em chunks Markdown
</h1>
```

**`<main>` element** (line 12) uses `bg-background text-foreground` — these Tailwind utility classes map to the shadcn OKLCH tokens in `index.css`. After updating `--background` in the `.dark` block, this element automatically picks up the new purple-dark background. No class change needed here.

**`motion-v` import pattern** (lines 1–8) — import structure to follow for any new Vue SFC in this phase:
```typescript
import { AnimatePresence, motion } from 'motion-v'
import ComponentName from '@/components/path/ComponentName.vue'
import { useUpload } from '@/composables/useUpload'
```

---

### `frontend/src/lib/formatters.ts` (utility, transform)

**Analog:** Self — existing pure-function module with named exports. Each function follows the same structure: typed parameters, guarded edge cases, return value.

**Existing function pattern** (lines 21–27) — copy this structure for `slugifyFilename`:
```typescript
export function formatDuration(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 1) {
    return '< 1s'
  }

  return `${seconds.toFixed(1)}s`
}
```

**New function to add** (D-18 — after existing exports at line 45):
```typescript
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

**Note:** Use `̀-ͯ` escape form (Unicode combining diacriticals block) instead of literal characters to avoid encoding issues in TypeScript source. This handles Portuguese "Calendário" → "calendario" correctly.

**Existing test pattern** (from `formatters.spec.ts` lines 1–31) — each function gets its own `describe` block with `it` cases:
```typescript
describe('slugifyFilename', () => {
  it('strips extension and slugifies ASCII filenames', () => {
    expect(slugifyFilename('report.pdf')).toBe('report')
  })
  it('strips Portuguese diacritics', () => {
    expect(slugifyFilename('Calendário de Provas 2026.pdf')).toBe('calendario-de-provas-2026')
  })
  it('collapses multiple non-alphanumeric chars into a single hyphen', () => {
    expect(slugifyFilename('my  file--name.docx')).toBe('my-file-name')
  })
  it('trims leading and trailing hyphens', () => {
    expect(slugifyFilename('-bad-name-.pdf')).toBe('bad-name')
  })
})
```

---

### `frontend/src/components/result/ChunkCard.vue` (component, request-response)

**Analog:** Self — add download button alongside existing Copy button, add glassmorphism + glow to Card, add max-height scroll to content area.

**Current imports** (lines 1–10):
```typescript
import { useClipboard } from '@vueuse/core'
import { Check, Copy } from 'lucide-vue-next'
import { motion } from 'motion-v'
import { computed } from 'vue'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { formatPageRange } from '@/lib/formatters'
import type { Chunk } from '@/types/api'
import MarkdownRenderer from './MarkdownRenderer.vue'
```

**Updated imports** — add `Download` from lucide, add `ref` from vue, add `slugifyFilename`:
```typescript
import { useClipboard } from '@vueuse/core'
import { Check, Copy, Download } from 'lucide-vue-next'
import { motion } from 'motion-v'
import { computed, ref } from 'vue'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { formatPageRange, slugifyFilename } from '@/lib/formatters'
import type { Chunk } from '@/types/api'
import MarkdownRenderer from './MarkdownRenderer.vue'
```

**Existing Copy button feedback pattern** (lines 16–28) — the download feedback mirrors this exact pattern with a `ref` instead of `useClipboard`:
```typescript
const { copy, copied } = useClipboard({ copiedDuring: 2000 })

async function copyChunk() {
  await copy(props.chunk.content)
}
```

**New download feedback pattern** — follow the same `ref` + `setTimeout` idiom (D-21):
```typescript
const chunkDownloaded = ref(false)

function downloadChunk(): void {
  const sectionSlug = props.chunk.section_title
    ? slugifyFilename(props.chunk.section_title)
    : `section-${props.chunk.chunk_index + 1}`
  const filename = `chunk-${props.chunk.chunk_index + 1}-${sectionSlug}.md`
  const blob = new Blob([props.chunk.content], { type: 'text/markdown; charset=utf-8' })
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

**Current Card + header template** (lines 33–65):
```html
<Card class="w-full overflow-hidden">
  <div class="flex flex-col gap-4 border-b border-border p-4 sm:flex-row sm:items-center sm:justify-between">
    <!-- ... metadata ... -->
    <Button type="button" variant="outline" size="sm" class="self-start"
      :aria-label="copied ? 'Texto copiado' : 'Copiar texto do chunk'"
      @click="copyChunk"
    >
      <Check v-if="copied" class="text-primary" aria-hidden="true" />
      <Copy v-else aria-hidden="true" />
      <span>{{ copied ? 'Copied!' : 'Copiar' }}</span>
    </Button>
  </div>
  <div class="p-4">
    <MarkdownRenderer :content="chunk.content" />
  </div>
</Card>
```

**Updated Card with glassmorphism + glow + download + max-height scroll** (D-03, D-07, D-14, D-20):
```html
<Card class="w-full overflow-hidden bg-white/5 backdrop-blur-md border border-purple-900/40 transition-shadow hover:shadow-[0_0_20px_4px_oklch(0.34_0.12_293_/_0.3)]">
  <div class="flex flex-col gap-4 border-b border-purple-900/40 p-4 sm:flex-row sm:items-center sm:justify-between">
    <!-- ... metadata (unchanged) ... -->
    <div class="flex items-center gap-2 self-start">
      <!-- Download icon-only button (D-20) -->
      <Button
        type="button"
        variant="outline"
        size="sm"
        :aria-label="chunkDownloaded ? 'Chunk baixado' : 'Baixar chunk como Markdown'"
        @click="downloadChunk"
      >
        <Check v-if="chunkDownloaded" class="text-primary" aria-hidden="true" />
        <Download v-else aria-hidden="true" />
      </Button>
      <!-- Copy button (existing) -->
      <Button
        type="button"
        variant="outline"
        size="sm"
        :aria-label="copied ? 'Texto copiado' : 'Copiar texto do chunk'"
        @click="copyChunk"
      >
        <Check v-if="copied" class="text-primary" aria-hidden="true" />
        <Copy v-else aria-hidden="true" />
        <span>{{ copied ? 'Copied!' : 'Copiar' }}</span>
      </Button>
    </div>
  </div>
  <div class="p-4">
    <!-- max-h-[400px] scroll on content body only, not the whole card (D-14) -->
    <div class="max-h-[400px] overflow-y-auto">
      <MarkdownRenderer :content="chunk.content" />
    </div>
  </div>
</Card>
```

**Existing `chunkVariants` motion pattern** (lines 21–24) — keep as-is, it drives the stagger animation from ResultView:
```typescript
const chunkVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' } },
}
```

**Test pattern for new download button** — mirrors existing copy test in `ChunkCard.spec.ts` (lines 55–64). Must mock `URL.createObjectURL` and `URL.revokeObjectURL`:
```typescript
// Add to ChunkCard.spec.ts
vi.stubGlobal('URL', {
  createObjectURL: vi.fn(() => 'blob:mock'),
  revokeObjectURL: vi.fn(),
})

it('shows CheckIcon feedback on chunk download click', async () => {
  const wrapper = mount(ChunkCard, { props: { chunk } })
  const buttons = wrapper.findAll('button')
  // First button is Download (icon-only), second is Copy
  await buttons[0].trigger('click')
  expect(wrapper.find('[aria-label="Chunk baixado"]').exists()).toBe(true)
})
```

---

### `frontend/src/components/result/MetadataCard.vue` (component, request-response)

**Analog:** Self — same glassmorphism without hover glow (D-03, no D-07).

**Current Card** (line 23):
```html
<Card class="w-full p-5">
```

**Updated Card — glassmorphism only, no glow** (D-03):
```html
<Card class="w-full p-5 bg-white/5 backdrop-blur-md border border-purple-900/40">
```

**Existing stat grid items** (lines 35–59) use `rounded-md border border-border bg-muted/30`. These will automatically inherit the new `--border` and `--muted` OKLCH values from the updated `index.css` `.dark` block — no class changes needed on the `<div>` stat items.

---

### `frontend/src/components/result/MarkdownRenderer.vue` (component, transform)

**Analog:** Self — the `markdown` instance is already at module scope (line 10), which is the correct place to add `.use()` calls and `renderer.rules` overrides (Pitfall 3 from RESEARCH.md).

**Current full file** (lines 1–24):
```typescript
import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'
import { computed } from 'vue'

const props = defineProps<{
  content: string
}>()

const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
})

const sanitizedHtml = computed(() => DOMPurify.sanitize(markdown.render(props.content)))
```

**Updated `<script setup>` — add after existing `MarkdownIt` import** (D-12, D-13, D-11):
```typescript
import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'
import type { Token, Options, Renderer } from 'markdown-it'
import highlightjs from 'markdown-it-highlightjs'
import 'highlight.js/styles/github-dark.css'
import { computed } from 'vue'

const props = defineProps<{
  content: string
}>()

// Module-scope instance — must stay outside setup() to avoid recreation on each render
const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
}).use(highlightjs, { auto: true, code: true, inline: false })

// D-13: target="_blank" on all links
const defaultLinkOpen = markdown.renderer.rules.link_open
  || function (tokens: Token[], idx: number, options: Options, _env: unknown, self: Renderer) {
      return self.renderToken(tokens, idx, options)
    }

markdown.renderer.rules.link_open = function (tokens, idx, options, env, self) {
  tokens[idx].attrSet('target', '_blank')
  tokens[idx].attrSet('rel', 'noopener noreferrer')
  return defaultLinkOpen(tokens, idx, options, env, self)
}

// D-11: wrap tables in overflow-x-auto div
markdown.renderer.rules.table_open = () => '<div class="overflow-x-auto"><table>'
markdown.renderer.rules.table_close = () => '</table></div>'

const sanitizedHtml = computed(() => DOMPurify.sanitize(markdown.render(props.content)))
```

**Updated `<template>` — replace existing prose div** (D-10, D-12, D-13, D-15):
```html
<template>
  <div
    class="prose prose-invert prose-sm max-w-none text-foreground
           prose-headings:text-foreground
           prose-a:text-purple-400 prose-a:no-underline prose-a:hover:underline
           prose-strong:text-foreground
           prose-code:bg-purple-950/40 prose-code:text-purple-200 prose-code:rounded prose-code:px-1
           prose-code:before:content-none prose-code:after:content-none
           prose-pre:bg-purple-950/60 prose-pre:border prose-pre:border-purple-900/40
           prose-table:border prose-table:border-purple-900/40
           prose-thead:bg-purple-950/60
           prose-img:max-w-full prose-img:h-auto"
    v-html="sanitizedHtml"
  />
</template>
```

**Note on `prose-code:before:content-none`:** If Tailwind v4 chained pseudo-element modifiers on prose don't work, fall back to this in `style.css`:
```css
.prose code::before,
.prose code::after {
  content: none;
}
```

**Existing test pattern** (from `MarkdownRenderer.spec.ts` lines 28–36) — verify classes on the container div:
```typescript
it('applies typography classes to the rendered container', () => {
  const wrapper = mount(MarkdownRenderer, { props: { content: 'Plain text' } })
  expect(wrapper.classes()).toEqual(expect.arrayContaining(['prose', 'prose-invert', 'max-w-none']))
})
```

**New test cases to add to `MarkdownRenderer.spec.ts`:**
```typescript
it('wraps tables in overflow-x-auto div', () => {
  const wrapper = mount(MarkdownRenderer, {
    props: { content: '| A | B |\n|---|---|\n| 1 | 2 |' },
  })
  expect(wrapper.find('.overflow-x-auto').exists()).toBe(true)
  expect(wrapper.find('.overflow-x-auto table').exists()).toBe(true)
})

it('adds target=_blank and rel=noopener on links', () => {
  const wrapper = mount(MarkdownRenderer, {
    props: { content: '[Link](https://example.com)' },
  })
  const anchor = wrapper.find('a')
  expect(anchor.attributes('target')).toBe('_blank')
  expect(anchor.attributes('rel')).toBe('noopener noreferrer')
})

it('applies syntax highlight class to fenced code blocks', () => {
  const wrapper = mount(MarkdownRenderer, {
    props: { content: '```python\nprint("hello")\n```' },
  })
  expect(wrapper.find('code.hljs').exists()).toBe(true)
})
```

---

### `frontend/src/components/result/ResultView.vue` (component, request-response)

**Analog:** Self — add global download button between the heading block and the existing "Novo Upload" button (D-16, D-17).

**Current imports** (lines 1–7):
```typescript
import { ArrowLeft } from 'lucide-vue-next'
import { motion } from 'motion-v'
import { Button } from '@/components/ui/button'
import type { ExtractionResponse } from '@/types/api'
import ChunkCard from './ChunkCard.vue'
import MetadataCard from './MetadataCard.vue'
```

**Updated imports** — add Download/Check icons, ref, slugifyFilename:
```typescript
import { ArrowLeft, Check, Download } from 'lucide-vue-next'
import { motion } from 'motion-v'
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import type { ExtractionResponse } from '@/types/api'
import { slugifyFilename } from '@/lib/formatters'
import ChunkCard from './ChunkCard.vue'
import MetadataCard from './MetadataCard.vue'
```

**Current `defineProps` / `defineEmits`** (lines 9–16) — keep unchanged:
```typescript
defineProps<{
  data: ExtractionResponse
  elapsedSeconds: number
}>()

defineEmits<{
  reset: []
}>()
```

**New download logic** — add after `defineEmits` (D-16 to D-19):
```typescript
const downloaded = ref(false)

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

**Current header template** (lines 30–39):
```html
<div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
  <div class="space-y-1">
    <p class="text-sm font-medium text-muted-foreground">SelectionMaid</p>
    <h1 class="text-2xl font-semibold leading-tight">Chunks extraídos</h1>
  </div>
  <Button type="button" variant="outline" @click="$emit('reset')">
    <ArrowLeft aria-hidden="true" />
    Novo Upload
  </Button>
</div>
```

**Updated header** — Download .MD button inserted between heading block and Novo Upload (D-17). CRITICAL: "Novo Upload" must remain LAST in DOM order so the existing test `wrapper.get('button')` still targets the Download button (update the test to use `[aria-label]` selector per Pitfall 4 in RESEARCH.md):
```html
<div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
  <div class="space-y-1">
    <p class="text-sm font-medium text-muted-foreground">SelectionMaid</p>
    <h1 class="text-2xl font-semibold leading-tight">Chunks extraídos</h1>
  </div>
  <div class="flex items-center gap-2">
    <Button
      type="button"
      variant="outline"
      :aria-label="downloaded ? 'Download concluído' : 'Baixar todos os chunks como arquivo Markdown'"
      @click="downloadAll(data)"
    >
      <Check v-if="downloaded" class="text-primary" aria-hidden="true" />
      <Download v-else aria-hidden="true" />
      {{ downloaded ? 'Baixado!' : 'Download .MD' }}
    </Button>
    <Button type="button" variant="outline" aria-label="Fazer novo upload" @click="$emit('reset')">
      <ArrowLeft aria-hidden="true" />
      Novo Upload
    </Button>
  </div>
</div>
```

**Test fix required in `ResultView.spec.ts`** (line 65) — the existing test:
```typescript
// BEFORE (breaks when Download button is added before Novo Upload)
await wrapper.get('button').trigger('click')

// AFTER — target by aria-label
await wrapper.get('[aria-label="Fazer novo upload"]').trigger('click')
```

---

## Shared Patterns

### CSS Token Architecture
**Source:** `frontend/src/assets/index.css` (lines 109–141)
**Apply to:** All theme changes
The shadcn token system uses OKLCH color space. The `.dark` block overrides tokens for the dark theme. Utility classes like `bg-background`, `text-foreground`, `border-border`, `bg-muted`, `text-primary` all resolve through this. Changing values here propagates automatically to all shadcn components without touching their class attributes.

### Glassmorphism Pattern
**Source:** `frontend/src/components/upload/DropZone.vue` (line 79) — established in Phase 13
**Apply to:** `ChunkCard.vue`, `MetadataCard.vue`
The existing DropZone uses `backdrop-blur-md` for glassmorphism during drag state. Cards adopt the same blur level:
```html
class="bg-white/5 backdrop-blur-md border border-purple-900/40"
```
ChunkCard additionally adds hover glow via `transition-shadow hover:shadow-[0_0_20px_4px_oklch(0.34_0.12_293_/_0.3)]`.
MetadataCard uses glassmorphism only (no hover glow per D-07).

### Feedback Ref Pattern (Copy → Download mirror)
**Source:** `frontend/src/components/result/ChunkCard.vue` (lines 16–28)
**Apply to:** Download button in ChunkCard + ResultView
The Copy button uses `useClipboard({ copiedDuring: 2000 })` which manages the `copied` boolean automatically. Since `useClipboard` is not applicable for downloads, mirror with a manual `ref<boolean>` + `setTimeout`:
```typescript
const downloaded = ref(false)
// After triggering download:
downloaded.value = true
setTimeout(() => { downloaded.value = false }, 1500)
```
Template mirrors the existing `<Check v-if="copied">` / `<Copy v-else>` toggle exactly.

### motion-v Animation (stagger)
**Source:** `frontend/src/components/result/ResultView.vue` (lines 18–25) + `frontend/src/components/result/ChunkCard.vue` (lines 21–24)
**Apply to:** No new animation files — existing `chunkVariants` / `chunkListVariants` are preserved unchanged.
```typescript
const chunkListVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07 } },
}
const chunkVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' } },
}
```

### Test Structure (Vitest + Vue Test Utils)
**Source:** `frontend/src/components/result/ChunkCard.spec.ts` (all) + `frontend/src/lib/formatters.spec.ts` (all)
**Apply to:** New test cases in `ChunkCard.spec.ts`, `ResultView.spec.ts`, `MarkdownRenderer.spec.ts`, `formatters.spec.ts`
- `describe` block per component/function, `it` per behavior
- `mount(Component, { props: { ... } })` for component tests
- `vi.mock('@vueuse/core')` for composable stubs
- `vi.stubGlobal('URL', { createObjectURL: vi.fn(), revokeObjectURL: vi.fn() })` for download tests
- No `beforeAll`/`afterAll` — use `beforeEach` for state reset
- Assert via `wrapper.text()`, `wrapper.find()`, `wrapper.classes()`, `wrapper.emitted()`

---

## No Analog Found

All files in this phase have direct self-analogs in the codebase. No new files are created — every change is an in-place edit.

---

## Metadata

**Analog search scope:** `frontend/src/` — all Vue SFCs, CSS files, TypeScript utility modules, spec files
**Files scanned:** 12
**Pattern extraction date:** 2026-05-26
