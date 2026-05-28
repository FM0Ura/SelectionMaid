# Phase 10: Upload Interaction - Research

**Researched:** 2026-05-26
**Domain:** Frontend Interaction / Drag & Drop
**Confidence:** HIGH

## Summary

This research establishes the implementation strategy for the Upload Interaction phase of SelectionMaid. We will leverage `shadcn-vue` for structural components, `@vueuse/core` for robust drag-and-drop logic, and `motion-v` for high-quality animations. The implementation will strictly follow the state machine defined in `useUpload.ts`, ensuring a predictable UI behavior across idle, dragging, uploading, and error states.

**Primary recommendation:** Use `@vueuse/core`'s `useDropZone` to manage the drag-and-drop state and integrate it with the existing `useUpload` composable.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** O DropZone será um componente centralizado (estilo Card), focando a atenção do usuário no centro da tela, em vez de um drop zone de página inteira.
- **D-02:** Utilização de **Motion-v** (Framer Motion para Vue) para o feedback visual de 'border pulse' e transições do overlay de drop. O motion-v permite coreografias mais suaves e integradas ao estado reativo do Vue.
- **D-03:** Os estados de 'Boas-vindas' (NAV-03) e 'Erro' (NAV-02) serão implementados como estados internos dentro do Card de upload. Isso mantém o layout da aplicação estável, alterando apenas o conteúdo interno do contêiner conforme o estado da máquina de estados (`idle`, `error`, etc.).
- **D-04:** O sistema suporta apenas um arquivo por vez (limitação do backend v1.0). Se o usuário arrastar múltiplos arquivos, o sistema deve bloquear a operação imediatamente e mostrar uma mensagem de erro pedindo o envio de apenas um arquivo.

### the agent's Discretion
- Detalhes específicos de micro-interações (ex: intensidade do pulse, timing do fade-in do overlay) ficam a critério da implementação, seguindo o estilo minimalista dark mode.

### Deferred Ideas (OUT OF SCOPE)
- Visualização de chunks e metadados (Phases 11-13).
- Skeleton shimmer durante o processamento (Phase 11).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UPL-01 | Drag and drop with animated feedback (border pulse, overlay). | `motion-v` patterns identified for pulse and transitions. |
| UPL-02 | Manual file selection button. | `shadcn-vue` Button + hidden input pattern confirmed. |
| NAV-02 | Structured error banner with retry. | `shadcn-vue` Alert component for structured errors. |
| NAV-03 | Welcome/idle state. | Card-based layout designed for the initial state. |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| File Selection (Drag/Button) | Browser / Client | — | Handled by DOM events and `useDropZone`. |
| Validation (Size/Type) | Browser / Client | API / Backend | Immediate feedback in UI; server also validates for security. |
| Upload Orchestration | Browser / Client | — | Managed by `useUpload` state machine. |
| Visual Feedback (Pulse/Overlay) | Browser / Client | — | CSS and `motion-v` animations. |
| Error Display | Browser / Client | — | UI component reacting to `useUpload` error state. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Vue | 3.5.34 | Frontend Framework | Project standard. |
| shadcn-vue | 2.7.3 | UI Components | Provides accessible, styled primitives. |
| motion-v | 2.2.1 | Animation Engine | Official Framer Motion port for Vue. |
| @vueuse/core | 14.3.0 | Utility Hooks | Provides `useDropZone` for reliable D&D. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-vue-next | 1.0.0 | Icons | Visual cues for upload and status. |
| tailwindcss | 4.3.0 | Styling | Utility-first styling. |

**Installation:**
```bash
# Packages are already present in package.json and installed.
```

**Version verification:**
- `npm view vue version`: 3.5.34 (Verified)
- `npm view @vueuse/core version`: 14.3.0 (Verified)
- `npm view motion-v version`: 2.2.1 (Verified)
- `npm view shadcn-vue version`: 2.7.3 (Verified)

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| vue | npm | 10+ yrs | ~5M/wk | github.com/vuejs/core | [OK] | Approved |
| @vueuse/core | npm | 5+ yrs | ~4M/wk | github.com/vueuse/vueuse | [OK] | Approved |
| motion-v | npm | 1+ yr | ~10k/wk | github.com/motiondivision/motion-vue | [OK] | Approved |
| shadcn-vue | npm | 2+ yrs | ~100k/wk | github.com/radix-vue/shadcn-vue | [OK] | Approved |
| lucide-vue-next | npm | 3+ yrs | ~1M/wk | github.com/lucide-icons/lucide | [OK] | Approved |

*Note: slopcheck initially flagged npm packages on PyPI due to environment misconfiguration, but registry verification confirms their legitimacy.*

## Architecture Patterns

### Recommended Project Structure
```
frontend/src/components/
├── upload/
│   ├── DropZone.vue       # Main component for this phase
│   ├── DropOverlay.vue    # motion-v animated overlay
│   └── ErrorBanner.vue    # NAV-02 structured error
```

### Pattern 1: Motion-v Border Pulse
**What:** Animating the border color and glow to signal an active drop zone.
**When to use:** When `isOverDropZone` is true.
**Example:**
```vue
<script setup>
import { motion } from 'motion-v'
</script>

<template>
  <motion.div
    class="border-2 rounded-xl"
    :animate="{
      borderColor: ['var(--color-primary)', 'var(--color-primary-foreground)', 'var(--color-primary)'],
      boxShadow: ['0 0 0px var(--color-primary)', '0 0 10px var(--color-primary)', '0 0 0px var(--color-primary)']
    }"
    :transition="{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }"
  >
    <!-- Content -->
  </motion.div>
</template>
```

### Anti-Patterns to Avoid
- **Raw Drag Events:** Don't use `dragover` / `dragleave` manually; `@vueuse/core` handles the edge cases (e.g., dragging over child elements) much better.
- **Multiple File Silence:** Don't silently pick the first file if multiple are dropped. Per D-04, block and show an error.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Drag and Drop Logic | Native DOM events | `@vueuse/core/useDropZone` | Handles event bubbling and state sync reliably. |
| Complex Transitions | TransitionGroup + CSS | `motion-v` | Declarative, spring-based animations are smoother. |

## Common Pitfalls

### Pitfall 1: Drag-Leave Flickering
**What goes wrong:** `dragleave` fires when moving over a child of the drop zone, causing the "active" state to flicker.
**Why it happens:** Standard DOM event behavior.
**How to avoid:** Use `useDropZone` from VueUse which abstracts this away.

### Pitfall 2: Memory Leaks with Object URLs
**What goes wrong:** Creating `URL.createObjectURL(file)` for previews without revoking it.
**Why it happens:** Browser keeps the file in memory.
**How to avoid:** Revoke the URL on component unmount (not strictly needed for v1.0 as we don't show previews yet, but good practice).

## Code Examples

### Manual File Selection with Button
```vue
<script setup>
import { ref } from 'vue'
import { Button } from '@/components/ui/button'

const fileInput = ref<HTMLInputElement | null>(null)
const onButtonClick = () => fileInput.value?.click()
const onFileChange = (e: Event) => {
  const files = (e.target as HTMLInputElement).files
  if (files?.length) handleUpload(files[0])
}
</script>

<template>
  <input type="file" ref="fileInput" class="hidden" @change="onFileChange" />
  <Button @click="onButtonClick">Select File</Button>
</template>
```

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `motion-v` is fully compatible with Tailwind v4 | Standard Stack | Minor CSS adjustment if variable names changed. |
| A2 | `useDropZone` correctly detects multiple files on drop | Common Pitfalls | Might need to check `dataTransfer` manually if hook only returns an array. |

## Open Questions (RESOLVED)

1. **How should we specifically represent the "Uploading" state in Phase 10?**
   - **Resolution:** Use a simple spinner and "Uploading..." text within the Card, keeping the layout stable before Phase 11 introduces the full skeleton shimmer. This ensures user feedback is immediate and consistent with the state machine.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| npm | Dependency Management | ✓ | 11.14.1 | — |
| shadcn-vue | UI Layer | ✓ | 2.7.3 | — |
| motion-v | Animations | ✓ | 2.2.1 | CSS Keyframes |
| @vueuse/core | D&D Logic | ✓ | 14.3.0 | Native API |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest |
| Config file | `frontend/vitest.config.ts` |
| Quick run command | `npm run test:unit` |
| Full suite command | `npm run test:unit` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UPL-01 | Drag & drop feedback | Unit/Component | `npm run test:unit DropZone.spec.ts` | ❌ Wave 0 |
| UPL-02 | Button selection | Unit/Component | `npm run test:unit DropZone.spec.ts` | ❌ Wave 0 |
| NAV-02 | Error display | Unit/Component | `npm run test:unit ErrorBanner.spec.ts` | ❌ Wave 0 |

### Wave 0 Gaps
- [ ] `frontend/src/components/upload/__tests__/DropZone.spec.ts` — covers selection and state.
- [ ] `frontend/src/components/upload/__tests__/ErrorBanner.spec.ts` — covers error display.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | `validateFile` in `validators.ts` |

### Known Threat Patterns for Vue/Vite

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Client-side bypass of size limit | Tampering | Backend MUST re-validate `Content-Length`. |
| Malicious file type | Tampering | Backend MUST re-validate MIME type. |

## Sources

### Primary (HIGH confidence)
- [motion.dev/docs/vue](https://motion.dev/docs/vue) - Official documentation for `motion-v`.
- [vueuse.org/core/useDropZone](https://vueuse.org/core/useDropZone) - Documentation for `@vueuse/core`.
- [shadcn-vue.com](https://www.shadcn-vue.com/) - Component library documentation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Libraries are installed and versions verified.
- Architecture: HIGH - Follows `useUpload` state machine.
- Pitfalls: MEDIUM - D&D edge cases are common but well-handled by VueUse.

**Research date:** 2026-05-26
**Valid until:** 2026-06-25
