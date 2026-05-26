# Phase 12: Result Display - Research

**Researched:** 2026-05-26
**Domain:** Frontend (Vue 3, Markdown, Clipboard API)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from 12-CONTEXT.md)

### Locked Decisions
- **D-01:** Utilização da biblioteca **markdown-it** para renderizar o conteúdo dos chunks. Esta escolha garante flexibilidade e suporte a extensões caso necessário no futuro.
- **D-02:** Os metadados do documento serão exibidos em um **Top Card** posicionado no início da lista de resultados. Este card rolará junto com os chunks, apresentando o contexto do arquivo processado.
- **D-03:** Cada card de chunk será **Detalhado**, incluindo:
    - Conteúdo Markdown renderizado.
    - Título da Seção (se disponível).
    - Intervalo de páginas (`page_start` a `page_end`).
    - Contagem de palavras.
    - Botão de "Copiar para área de transferência" com feedback visual.

### the agent's Discretion
- Estilo visual específico dos cards de chunk (bordas, sombras, espaçamento) seguindo o dark mode minimalista.
- Implementação exata do feedback visual do botão de cópia (ex: mudança temporária de ícone).
- Ordenação e rotulagem exata dos campos de metadados no card de topo.

### Deferred Ideas (OUT OF SCOPE)
- Animação "staggered" na revelação dos chunks (Phase 13).
- Transições de view animadas entre telas (Phase 13).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RES-01 | Usuário vê os chunks do documento renderizados como Markdown | `markdown-it` + `dompurify` + `@tailwindcss/typography` |
| RES-03 | Usuário pode copiar o texto de cada chunk individualmente com um botão | `@vueuse/core` `useClipboard` with icon swap feedback |
| RES-04 | Usuário vê painel de metadados com tipo, idioma, título e tempo | Metadata fields mapped from `ExtractionResponse` and frontend timer |
</phase_requirements>

## Summary

This phase delivers the final step of the document extraction pipeline: displaying the results to the user. We will implement a structured view featuring a metadata card and a list of detailed chunk cards. Markdown content within chunks will be rendered with full formatting support while ensuring security through sanitization. Users will be able to copy individual chunks and return to the upload state via a reset action.

**Primary recommendation:** Use `markdown-it` for parsing and `dompurify` for sanitization, coupled with the `@tailwindcss/typography` plugin for effortless styling. Leverage `@vueuse/core`'s `useClipboard` to handle the copy-to-clipboard functionality with built-in state management for user feedback.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Markdown Parsing | Browser / Client | — | `markdown-it` transforms raw text to HTML strings in the frontend. |
| Sanitization | Browser / Client | — | `dompurify` strips potentially malicious HTML before rendering. |
| Clipboard Access | Browser / Client | — | Native Clipboard API (via VueUse) handles copying to system buffer. |
| Formatting | Browser / Client | — | Formatting utilities for dates, file sizes, and durations. |
| State Reset | Browser / Client | — | `useUpload` composable clears the success state and returns to idle. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| markdown-it | 14.2.0 | Markdown parser | High performance, extensible, industry standard. |
| dompurify | 3.4.6 | HTML sanitizer | Essential for safe `v-html` rendering. |
| @tailwindcss/typography | 0.5.19 | Markdown styling | Official Tailwind plugin for "prose" styling. |
| @vueuse/core | 14.3.0 | Utilities | Provides `useClipboard` for reliable copy feedback. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|--------------|
| lucide-vue-next | 1.0.0 | Icons | Copy, Check, Reset, and Metadata icons. |
| motion-v | 2.2.1 | Animations | Subtle transitions for the "Copied!" feedback state. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| @tailwindcss/typography | Custom CSS | Custom CSS gives more control but requires significantly more effort to maintain (especially for dark mode / OKLCH). |
| Toast Notification | Local UI State | Roadmap RES-03 specifies a "brief confirmation" on the button; local state is less intrusive than a global toast for repeated actions like copying multiple chunks. |

**Installation:**
```bash
npm install markdown-it dompurify
npm install -D @tailwindcss/typography @types/markdown-it @types/dompurify
```

**Version verification:**
```bash
npm view markdown-it version          # 14.2.0 (Verified 2026-05-26)
npm view dompurify version            # 3.4.6 (Verified 2026-05-26)
npm view @tailwindcss/typography version # 0.5.19 (Verified 2026-05-26)
```

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| markdown-it | npm | 14 yrs | 5M/wk | github.com/markdown-it/markdown-it | [OK] | Approved |
| dompurify | npm | 11 yrs | 12M/wk | github.com/cure53/dompurify | [OK] | Approved |
| @tailwindcss/typography | npm | 4 yrs | 5M/wk | github.com/tailwindlabs/tailwindcss-typography | [OK] | Approved |

*Note: slopcheck was verified manually via NPM registry as the tool has a PyPI bias.*

## Architecture Patterns

### Recommended Project Structure
```
frontend/src/
├── components/
│   └── result/
│       ├── ResultView.vue       # Main container for success state
│       ├── MetadataCard.vue     # Top Card with document info
│       ├── ChunkCard.vue        # Individual chunk card with copy button
│       └── MarkdownRenderer.vue # Reusable sanitized markdown component
└── lib/
    └── formatters.ts           # Utilities for dates, sizes, and duration
```

### Pattern 1: Secure Markdown Component
**What:** A dedicated component that wraps `markdown-it` and `dompurify` to prevent XSS.
**Example:**
```vue
<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

const props = defineProps<{ content: string }>()
const md = new MarkdownIt({ html: false, linkify: true, typographer: true })

const sanitizedHtml = computed(() => {
  const rawHtml = md.render(props.content)
  return DOMPurify.sanitize(rawHtml)
})
</script>

<template>
  <div v-html="sanitizedHtml" class="prose prose-invert max-w-none" />
</template>
```

### Pattern 2: Contextual Copy Button
**What:** Use `useClipboard` to toggle a state-driven feedback loop on the button itself.
**Example:**
```vue
<script setup lang="ts">
import { useClipboard } from '@vueuse/core'
import { Copy, Check } from 'lucide-vue-next'

const props = defineProps<{ text: string }>()
const { copy, copied } = useClipboard({ source: props.text, copiedDuring: 2000 })
</script>

<template>
  <Button variant="ghost" size="sm" @click="copy()">
    <Check v-if="copied" class="h-4 w-4 text-green-500" />
    <Copy v-else class="h-4 w-4" />
    <span v-if="copied" class="ml-2">Copied!</span>
  </Button>
</template>
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Markdown Rendering | Custom regex/replace | `markdown-it` | Markdown is complex (nested blocks, lists, escaping). Hand-rolling is insecure and brittle. |
| XSS Prevention | Simple string stripping | `dompurify` | Comprehensive security against edge cases like `javascript:` links and nested malicious tags. |
| Clipboard Sync | Manual `execCommand` | `useClipboard` | Handles modern Async Clipboard API with fallbacks and reactive state. |

## Common Pitfalls

### Pitfall 1: `v-html` Vulnerabilities
**What goes wrong:** Rendering markdown with `v-html` without sanitization allows malicious input to execute scripts.
**How to avoid:** Always use `dompurify` on the output of the markdown parser.

### Pitfall 2: Prose Width Issues
**What goes wrong:** The `prose` class by default limits width for readability (e.g., `65ch`), which might look odd in a wide dashboard card.
**How to avoid:** Use `max-w-none` on the prose container to allow it to fill the card's width.

## Code Examples

### Formatting Utilities (`lib/formatters.ts`)
```typescript
/**
 * Formats a file size in bytes to a human-readable string.
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

/**
 * Formats seconds into a short duration string.
 */
export function formatDuration(seconds: number): string {
  if (seconds < 1) return '< 1s'
  return `${seconds.toFixed(1)}s`
}

/**
 * Formats an ISO date string to a readable format.
 */
export function formatDate(isoString: string): string {
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short'
  }).format(new Date(isoString))
}
```

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `elapsedSeconds` from Phase 11 is sufficient for "processing time". | Specific Ideas | User might expect actual server-side timing if network lag is high. |
| A2 | `@tailwindcss/typography` is compatible with Tailwind v4's CSS-first approach. | Standard Stack | May require manual plugin registration in CSS via `@plugin`. |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | All | ✓ | 26.1.0 | — |
| npm | All | ✓ | 11.14.1 | — |
| Tailwind v4 | Styles | ✓ | 4.3.0 | — |

## Validation Architecture

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RES-01 | Markdown renders correctly | Unit | `npm run test:unit MarkdownRenderer` | ❌ Wave 0 |
| RES-03 | Copy button updates state | Unit | `npm run test:unit ChunkCard` | ❌ Wave 0 |
| RES-04 | Metadata card shows correct fields | Unit | `npm run test:unit MetadataCard` | ❌ Wave 0 |
| NAV-RESET | Reset button clears success state | Unit | `npm run test:unit ResultView` | ❌ Wave 0 |

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | `dompurify` for all dynamic HTML rendering. |

### Known Threat Patterns for Markdown

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| XSS via Malicious Markdown | Tampering | `markdown-it` options (`html: false`) + `dompurify`. |
| Malicious Links | Spoofing | `dompurify` strips `javascript:` and `data:` URIs from `href`. |

## Sources

### Primary (HIGH confidence)
- [markdown-it Documentation](https://github.com/markdown-it/markdown-it) - Parsing and security options.
- [DOMPurify Documentation](https://github.com/cure53/dompurify) - Vue integration and sanitization rules.
- [Tailwind CSS v4 Docs](https://tailwindcss.com/docs/v4-beta) - Typography plugin usage.
- [VueUse useClipboard Docs](https://vueuse.org/core/useClipboard/) - API and feedback options.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Industry standard libraries.
- Architecture: HIGH - Follows established Vue 3 composition patterns.
- Pitfalls: HIGH - Security risks are well-documented.

**Research date:** 2026-05-26
**Valid until:** 2026-06-25
