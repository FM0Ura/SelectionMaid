# Technology Stack — v2.0 Frontend (Vue 3 + Vite SPA)

**Project:** SelectionMaid
**Milestone:** v2.0 Frontend — Vue 3 + Vite SPA consuming the FastAPI /ingest endpoint
**Researched:** 2026-05-25
**Confidence:** HIGH (core stack) / MEDIUM (version-specific details from npm/WebSearch)

---

## Context

The backend (Python 3.13+, FastAPI, hexagonal architecture) ships production-ready as v1.0.
This document covers only the **net-new frontend stack** for the v2.0 milestone.
The SPA is a separate static artifact that talks to the backend over HTTP (CORS).

Target feature set:
- Drag-and-drop file upload with animated feedback
- Skeleton/shimmer loading states during backend processing
- Chunk list reveal with stagger animation
- Smooth view transitions between sections
- Metadata visualization
- Dark-mode-first, minimalist aesthetic

---

## Recommended Stack

### Core Build Tools

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Vite | ^6.3 | Build tool and dev server | Native ESM, HMR under 50ms, official Vue plugin; Vite 6 is the current stable release (announced Nov 2024) |
| @vitejs/plugin-vue | ^5.x | Vue 3 SFC support in Vite | Official plugin; required to process `.vue` files |
| TypeScript | ^5.5 | Type safety | Fully supported in Vue 3 + Vite; `lang="ts"` in SFCs; zero config via `vue-ts` template |

**Scaffold command:**
```bash
npm create vite@latest selection-maid-ui -- --template vue-ts
```

---

### Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Vue 3 | ^3.5 | UI framework | Constraint from milestone; Composition API, `<script setup>`, excellent TS integration |
| Vue Router | ^5.0 | Client-side routing | Official Vue router; v5 merges unplugin-vue-router into core, no breaking changes from v4; use `createWebHistory` for clean URLs |

Vue Router is included even for a single-page tool because view transitions between "upload zone" and "results" states benefit from router-level transition hooks (`<RouterView>` + `<Transition>`).

---

### Styling System

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Tailwind CSS | ^4.1 | Utility-first CSS | v4 ships as a Vite plugin (`@tailwindcss/vite`); no `tailwind.config.js` needed; CSS variable-based design tokens; 10x faster build than v3 |
| @tailwindcss/vite | ^4.1 | Tailwind Vite integration | Official plugin for v4; replaces PostCSS config; zero config required |

**Dark mode strategy:** Use the `class` strategy (not `media`), controlled by `@vueuse/core`'s `useColorMode`. This allows a UI toggle that overrides OS preference. In Tailwind v4, set `@variant dark (&:where(.dark, .dark *))` in your CSS entry point to activate class-based dark mode.

**Why not CSS-in-JS or styled-components?** Tailwind + CSS variables is the natural fit for shadcn-vue components. CSS-in-JS adds runtime overhead and complicates the dark mode token strategy.

---

### Component Library

**Recommendation: shadcn-vue**

shadcn-vue is the correct choice for this project. Rationale:

- Components are copied into `src/components/ui/` — you own the code, zero bundle bloat
- Built on Reka UI (headless, accessible primitives) for the complex interaction logic
- Styled with Tailwind CSS + CSS variables for theming
- Dark mode is a first-class citizen: the shadcn-vue dark mode guide targets the exact Vite setup used here
- 50+ components including everything needed: Button, Card, Badge, Separator, Sheet/Dialog
- `useColorMode` from `@vueuse/core` is the recommended toggle mechanism in official shadcn-vue docs
- The copy-paste model means no dependency to update; components live alongside your code

| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| shadcn-vue | CLI (no npm install) | UI components | Components copied into src; uses Reka UI + Tailwind |
| reka-ui | ^2.x (transitive) | Headless primitives | Installed by shadcn-vue; do not import directly |

**Why not PrimeVue?** PrimeVue brings its own theming system that fights Tailwind. Its unstyled mode works but requires stripping all defaults; more config overhead than shadcn-vue for a minimal dark aesthetic.

**Why not Headless UI Vue?** Headless UI is maintained by the Tailwind team but targets React first; Vue support lags and component coverage is narrower than Reka UI.

**Why not Vuetify / Element Plus / Naive UI?** All ship with opinionated theming that conflicts with a from-scratch dark design. Customization overhead exceeds the cost of building components on shadcn-vue primitives.

---

### Animation Library

**Recommendation: motion-v (Motion for Vue)**

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| motion-v | ^2.2 | All animations | Official Motion library for Vue 3; 5kb; GSAP-comparable capability; built by the Motion team |

motion-v is the Vue-native package for Motion (formerly Motion One, now motion.dev). It provides:
- `<motion.div>` component with declarative `animate`, `initial`, `exit` props
- `stagger()` function for chunk reveal cascades — exactly the use case
- `drag` prop for drag-to-dismiss and interactive drag gestures
- `useAnimate()` composable for imperative control (shimmer sequencing)
- Vue Transitions integration via `<AnimatePresence>` equivalent
- Hardware-accelerated via WAAPI where possible; JS fallback for spring physics
- Current npm version: 2.2.1 (verified April 2026)

**Stagger pattern for chunk reveal:**
```ts
import { stagger, useAnimate } from 'motion-v'
// or use variants with delayChildren + staggerChildren on the list container
```

**Why not GSAP?** GSAP's free tier is sufficient technically, but its license restricts use in SaaS/products without a commercial license. For an internal dev tool this is legally murky. motion-v is MIT-licensed, Vue-native, and covers all required animation primitives.

**Why not @vueuse/motion?** @vueuse/motion (the vueuse ecosystem package) is a separate, older library. It provides physics-based animations via composables but lacks the `<AnimatePresence>`-style exit animation orchestration and the WAAPI acceleration layer that motion-v ships. motion-v is the more capable choice for complex sequences.

**Why not native CSS transitions?** Pure CSS cannot do dynamic stagger on a variable-length list returned from an API, nor can it sequence enter/exit based on route changes. Use CSS transitions only for hover micro-interactions (button states) that don't need JS control.

---

### Drag-and-Drop File Upload

**Recommendation: native HTML5 + @vueuse/core `useDropZone`**

| Utility | Version | Purpose | Notes |
|---------|---------|---------|-------|
| @vueuse/core | ^14.3 | `useDropZone`, `useColorMode`, `useDark`, etc. | Already pulled in by shadcn-vue; use throughout |

Do not install a dedicated drag-and-drop library. `useDropZone` from `@vueuse/core` provides everything needed:
- `isOverDropZone` reactive boolean for visual feedback styling
- `onDrop(files: File[])` callback with file list
- `dataTypes` filter for restricting to `['application/pdf', ...]`

Pair `useDropZone` with motion-v to animate the drop zone border, scale, and overlay entrance on hover.

`@vueuse/core` v14 requires Vue 3.5+. It ships tree-shakeable; only the composables you import are bundled.

---

### State Management

**Recommendation: plain composables for this scope — no Pinia**

The SPA state is:
1. `uploadFile: File | null` — selected file
2. `isProcessing: boolean` — waiting for API
3. `result: IngestResponse | null` — API response
4. `error: string | null` — error message

This is single-page, single-flow, linear state. A single `useIngestion()` composable encapsulates all of it. No cross-component shared state is needed; the results component and the upload component can be siblings under a single parent.

Pinia adds devtools, plugin support, and persistence — valuable when multiple features share state across many components. For a single upload-process-display flow, Pinia is organizational overhead that signals complexity this tool does not have.

**Add Pinia if:** A second major flow (e.g., history of processed documents, session storage of previous results) is added in a future milestone.

---

### HTTP Client

**Recommendation: native `fetch` with a thin composable wrapper**

Do not add axios or ofetch for this project.

Rationale:
- The SPA makes exactly **one API call**: `POST /ingest` with `multipart/form-data`
- `fetch` handles multipart uploads natively via `FormData`
- `fetch` throws on network errors; HTTP error codes require a manual check — but for a single endpoint this is one `if (!response.ok)` guard
- axios weighs ~14kB gzip; ofetch is 2kB but still a dependency for one endpoint

The composable pattern:
```ts
// src/composables/useIngestion.ts
export function useIngestion() {
  const isProcessing = ref(false)
  const result = ref<IngestResponse | null>(null)
  const error = ref<string | null>(null)

  async function ingest(file: File) {
    isProcessing.value = true
    error.value = null
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch('/api/ingest', { method: 'POST', body: form })
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      result.value = await res.json()
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      isProcessing.value = false
    }
  }

  return { isProcessing, result, error, ingest }
}
```

**Upload progress:** `fetch` does not expose upload progress natively. If a progress bar during upload is required, use `XMLHttpRequest` inside the composable (fires `progress` events). This is the only reason to deviate — and it is still not a reason to add axios.

---

### Dev Tooling

| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| ESLint | ^9.x | Linting | Use `@vue/eslint-config-typescript` flat config |
| Prettier | ^3.x | Formatting | `prettier-plugin-tailwindcss` sorts class order automatically |
| Vitest | ^2.x | Unit testing | Vite-native; same config as the build |
| @vue/test-utils | ^2.x | Component testing | Mount components in Vitest |
| vue-devtools (browser ext) | — | Debug | Vue 3 devtools for component inspection |

---

## FastAPI Backend Integration

### CORS Configuration

Add `CORSMiddleware` to the existing FastAPI app. The SPA runs on `http://localhost:5173` in dev (Vite default) and on a separate origin in production.

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # dev; replace with deployed SPA origin in prod
    allow_methods=["POST", "OPTIONS"],          # only /ingest is called
    allow_headers=["Content-Type"],
    max_age=600,                                # cache preflight for 10 minutes
)
```

`CORSMiddleware` must be added before any other middleware. In production, replace the hardcoded origin with an environment variable (`CORS_ALLOWED_ORIGINS`).

### Vite Dev Proxy (eliminates CORS in development)

Configure Vite to proxy `/api` to the FastAPI server. This removes the need for CORS headers entirely during local development and mirrors the production path structure.

```ts
// vite.config.ts
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
```

With this proxy, `fetch('/api/ingest', ...)` routes to `http://localhost:8000/ingest` during dev.
In production, configure the reverse proxy (nginx / Caddy) to do the same rewrite.

### Multipart Upload

The FastAPI endpoint already accepts `UploadFile`. The frontend sends `multipart/form-data` via `FormData`. Do not set a `Content-Type` header manually — `fetch` sets the boundary automatically when the body is `FormData`.

**Never send** `Content-Type: multipart/form-data` manually; omitting the boundary makes the request malformed.

### Expected API Contract

```
POST /ingest
Content-Type: multipart/form-data

file: <binary>

200 OK
{
  "chunks": [
    { "text": "...", "metadata": { "heading": "...", "page": 1 } }
  ],
  "metadata": { "title": "...", "language": "...", "doc_type": "..." }
}
```

Define a matching TypeScript interface in `src/types/api.ts` and use it in the composable.

---

## Skeleton Loading — Implementation Approach

Do not install a skeleton loader library. A pure CSS shimmer component is trivial and integrates naturally with Tailwind dark mode tokens.

```vue
<!-- src/components/SkeletonChunk.vue -->
<template>
  <div class="rounded-lg bg-muted animate-pulse h-24 w-full" />
</template>
```

For a shimmer gradient effect, add a single Tailwind custom animation in `globals.css`:
```css
@keyframes shimmer {
  from { background-position: -200% 0; }
  to   { background-position: 200% 0; }
}
.shimmer {
  background: linear-gradient(90deg, var(--muted) 25%, var(--muted-foreground/20) 50%, var(--muted) 75%);
  background-size: 200%;
  animation: shimmer 1.5s infinite;
}
```

Using shadcn-vue's CSS variable tokens (`--muted`, `--muted-foreground`) makes this automatically dark-mode-aware without any `dark:` prefix.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Animation | motion-v | GSAP | GSAP requires commercial license for SaaS/product use; motion-v is MIT |
| Animation | motion-v | @vueuse/motion | Less capable exit animation orchestration; no WAAPI acceleration |
| Animation | motion-v | CSS-only | Cannot stagger dynamic lists or sequence route transitions with JS state |
| Components | shadcn-vue | PrimeVue (unstyled) | More config overhead; theming system fights Tailwind |
| Components | shadcn-vue | Headless UI | Vue support lags React; narrower component set than Reka UI |
| Components | shadcn-vue | Vuetify / Element Plus | Opinionated theming conflicts with custom dark aesthetic |
| State | composables | Pinia | Overkill for single linear flow; add if multi-flow state emerges |
| HTTP | fetch | axios | 14kB dependency for one endpoint; not justified |
| HTTP | fetch | ofetch | Still a dependency for one endpoint; native fetch is sufficient |
| Drag-drop | @vueuse/core useDropZone | vue-dropzone | vue-dropzone is Vue 2 + unmaintained; native HTML5 is the correct approach |
| Drag-drop | @vueuse/core useDropZone | react-dropzone port | Does not exist for Vue 3 |
| Skeleton | custom CSS | vue-skeletor | Extra dependency for 10 lines of CSS; dark mode integration is trivial without it |
| CSS | Tailwind v4 | Tailwind v3 | v4 is the current stable release; v3 is in maintenance mode |

---

## Installation

```bash
# Scaffold
npm create vite@latest selection-maid-ui -- --template vue-ts
cd selection-maid-ui

# Core runtime
npm install vue-router@5 @vueuse/core motion-v

# Tailwind v4 (Vite plugin — no tailwind.config.js needed)
npm install -D tailwindcss @tailwindcss/vite

# shadcn-vue CLI (run after Tailwind is configured)
npx shadcn-vue@latest init

# Add individual shadcn-vue components as needed
npx shadcn-vue@latest add button card badge separator

# Dev tooling
npm install -D vitest @vue/test-utils @vitejs/plugin-vue prettier prettier-plugin-tailwindcss
```

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| axios | 14kB for one endpoint; multipart upload works natively with `fetch` + `FormData` | native `fetch` |
| Pinia | Linear single-flow state; composable is sufficient | `useIngestion()` composable |
| LangChain / LlamaIndex on frontend | No text processing on the client; backend handles all of this | N/A |
| vue-dropzone | Vue 2 + unmaintained | `@vueuse/core` `useDropZone` |
| A skeleton loader library | 10 lines of CSS; Tailwind shimmer with CSS variables is dark-mode-aware | Custom `SkeletonChunk.vue` |
| GSAP | License ambiguity for internal tools shipped as products | motion-v (MIT) |
| @vueuse/motion | Less capable than motion-v for this use case | motion-v |
| Vuetify / Quasar / Element Plus | Opinionated theming fights the minimal dark aesthetic | shadcn-vue on Reka UI |
| Nuxt | SSR overhead for a static SPA backed by a separate FastAPI service | Vite + Vue Router |
| react-* anything | Wrong ecosystem | Vue 3 equivalents |

---

## Version Summary

| Package | Verified Version | Source |
|---------|-----------------|--------|
| Vite | ^6.3 | MEDIUM — announced Nov 2024, v6.x current |
| @vitejs/plugin-vue | ^5.x | MEDIUM — matches Vite 6 release |
| Vue 3 | ^3.5 | HIGH — required by @vueuse/core v14 |
| Vue Router | ^5.0 (or 4.6.x) | MEDIUM — v5 published, v4.6.3 stable alt |
| Tailwind CSS | ^4.1 | MEDIUM — v4 is current stable |
| @tailwindcss/vite | ^4.1 | MEDIUM — official Vite plugin for Tailwind v4 |
| motion-v | ^2.2 | MEDIUM — 2.2.1 verified via npm (Apr 2026) |
| @vueuse/core | ^14.3 | HIGH — 14.3.0 verified via npm |
| shadcn-vue | CLI (no version pin) | MEDIUM — components copied, not installed |
| reka-ui | ^2.x (transitive) | MEDIUM — shadcn-vue dependency |

---

## Sources

- [Motion for Vue — motion.dev/docs/vue](https://motion.dev/docs/vue) — motion-v features, stagger, drag
- [motion-v on npm](https://www.npmjs.com/package/motion-v) — version 2.2.1 confirmed
- [Motion for Vue stagger docs](https://motion.dev/docs/stagger)
- [motion-v GitHub — motiondivision/motion-vue](https://github.com/motiondivision/motion-vue)
- [@vueuse/core on npm](https://www.npmjs.com/package/@vueuse/core) — version 14.3.0 confirmed; requires Vue 3.5+
- [useDropZone — VueUse](https://vueuse.org/core/usedropzone/)
- [shadcn-vue GitHub — unovue/shadcn-vue](https://github.com/unovue/shadcn-vue)
- [shadcn-vue Dark Mode — Vite setup](https://www.shadcn-vue.com/docs/dark-mode)
- [Reka UI](https://reka-ui.com/) — headless accessible primitives, Tailwind compatible
- [Tailwind CSS v4 dark mode](https://tailwindcss.com/docs/dark-mode)
- [Vite 6.0 announcement](https://vite.dev/blog/announcing-vite6)
- [Vue Router on npm](https://www.npmjs.com/package/vue-router) — v5.0.7 latest
- [Pinia on npm](https://www.npmjs.com/package/pinia) — v3.0.4; not recommended for this scope
- [Vue 3 state management — Composables vs Pinia](https://vueschool.io/articles/vuejs-tutorials/composables-vs-provide-inject-pinia-when-to-use-what/)
- [FastAPI CORS docs](https://fastapi.tiangolo.com/tutorial/cors/)
- [Best Vue UI Libraries 2025 — Can Akyuz](https://www.canakyuz.dev/blog/the-best-react-and-vue-ui-libraries-of-2025-an-in-depth-review)

---

*Stack research for: Vue 3 + Vite SPA frontend — SelectionMaid v2.0 milestone*
*Researched: 2026-05-25*
