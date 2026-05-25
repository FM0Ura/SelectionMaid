# Architecture Research

**Domain:** Document extraction / RAG ingestion service — hexagonal backend + Vue 3 SPA frontend
**Researched:** 2026-05-25 (v2.0 frontend milestone added)
**Confidence:** HIGH (backend, unchanged from v1.0) / HIGH (frontend patterns, verified via official Vue docs + VueUse docs + FastAPI CORS docs)

---

## Part 1 — Backend Architecture (v1.0, unchanged)

### System Overview

```text
┌──────────────────────────────────────────────────────────────────┐
│                     INPUT ADAPTERS (Driving Side)                │
│  ┌──────────────────────┐   ┌──────────────────────────────┐     │
│  │  FastAPI Router       │   │  CLI / test harness          │     │
│  │  (HTTP input adapter) │   │  (alternate driving adapter) │     │
│  └──────────┬───────────┘   └──────────────┬───────────────┘     │
└─────────────┼────────────────────────────────┼────────────────────┘
              │ calls                          │ calls
              ▼                                ▼
┌──────────────────────────────────────────────────────────────────┐
│               APPLICATION LAYER (Use-Case Orchestration)         │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  ExtractionService                                         │   │
│  │   process(raw_input: RawInput) → ExtractionResult          │   │
│  └───┬─────────────┬──────────────┬────────────────┬─────────┘   │
│      │ via port    │ via port     │ via port       │ via port     │
└──────┼─────────────┼──────────────┼────────────────┼─────────────┘
       ▼             ▼              ▼                ▼
┌──────────────────────────────────────────────────────────────────┐
│                     PORTS (Protocol contracts)                   │
│  ExtractorPort   FilterPort   ChunkerPort   MetadataEnricherPort  │
└──────┬─────────────┬──────────────┬────────────────┬─────────────┘
       │             │              │                │
       ▼             ▼              ▼                ▼
┌──────────────────────────────────────────────────────────────────┐
│                  OUTPUT ADAPTERS (Driven Side)                   │
│  ┌───────────┐  ┌──────────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Docling   │  │ Heuristic    │  │ Markdown │  │ LangDetect │  │
│  │ Adapter   │  │ Filter       │  │ Chunker  │  │ Enricher   │  │
│  └───────────┘  └──────────────┘  └──────────┘  └────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

**Dependency direction:** Everything depends inward — adapters depend on ports, ports depend on domain models, nothing in the domain or ports knows about adapters.

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
| --- | --- | --- |
| FastAPI router | HTTP boundary: accept file upload, return JSON | `APIRouter` with `UploadFile`, calls `ExtractionService` |
| Pydantic schemas | HTTP contract: request/response shapes, validation | `BaseModel` classes in `adapters/http/schemas.py` |
| ExtractionService | Orchestrate the full pipeline: extract → filter → chunk → enrich | Plain Python class, injected with 4 port instances |
| ExtractorPort | Contract: `extract(raw_input) → RawDocument` | `typing.Protocol` with one required method |
| FilterPort | Contract: `filter(raw) → RawDocument` (noise removed) | `typing.Protocol` |
| ChunkerPort | Contract: `chunk(doc) → list[DocumentChunk]` | `typing.Protocol` |
| MetadataEnricherPort | Contract: `enrich(doc) → DocumentMetadata` | `typing.Protocol` |
| DoclingAdapter | Wraps `docling.DocumentConverter`; satisfies ExtractorPort | Concrete class; Docling is a private implementation detail |
| HeuristicFilter | Header/footer/page-number removal heuristics; satisfies FilterPort | Concrete class using regex/positional rules |
| MarkdownChunker | Splits Markdown at heading boundaries + token count; satisfies ChunkerPort | Concrete class; uses `tiktoken` |
| MetadataEnricher | Infers language, doc type, author; satisfies MetadataEnricherPort | Concrete class using `langdetect` |
| Composition root | Creates concrete adapters; wires them into service; mounts router | `app.py` + `_lifespan()` — the only place all layers touch |
| Domain models | Immutable data containers with no framework dependencies | `@dataclass(frozen=True)` |

### Existing Backend File Structure

```text
src/selection_maid/
├── domain/
│   ├── models.py       # RawInput, RawDocument, DocumentChunk, DocumentMetadata, ExtractionResult
│   └── ports.py        # ExtractorPort, FilterPort, ChunkerPort, MetadataEnricherPort (Protocol)
├── service.py          # ExtractionService (application layer)
├── config.py           # GlobalConfig (GlobalConfig, HttpConfig, etc.)
├── errors.py           # SelectionMaidError taxonomy
└── adapters/
    ├── extractor/docling.py      # DoclingAdapter
    ├── filter/heuristic.py       # HeuristicFilter
    ├── chunker/markdown.py       # MarkdownChunker
    ├── enricher/default.py       # MetadataEnricher
    └── http/
        ├── app.py       # create_app() + _lifespan(); entry point for uvicorn
        ├── router.py    # build_router(service, config); GET /health + POST /ingest
        ├── schemas.py   # ChunkSchema, MetadataSchema, ExtractionResponse, HealthResponse
        └── error_map.py # ERROR_CODE_TO_HTTP mapping
```

### Existing API Contract (v1.0)

**POST /ingest** — multipart/form-data, field name: `file`

Success response (HTTP 200):

```json
{
  "metadata": {
    "doc_id": "string",
    "source_filename": "string",
    "title": "string",
    "author": "string",
    "language": "string (ISO 639-1)",
    "doc_type": "string",
    "page_count": 0,
    "chunk_count": 0,
    "ingested_at": "2026-05-25T00:00:00Z"
  },
  "chunks": [
    {
      "chunk_id": "string",
      "content": "string (Markdown)",
      "page_start": 0,
      "page_end": 0,
      "section_title": "string",
      "chunk_index": 0,
      "total_chunks": 0,
      "word_count": 0
    }
  ]
}
```

Error response (HTTP 4xx/5xx):

```json
{
  "error": {
    "code": "UPLOAD-001",
    "message": "human-readable description"
  }
}
```

Error codes: `UPLOAD-001` (413 too large), `UPLOAD-002` (422 magic bytes mismatch), `EXT-001` (500 extraction failure), `EXT-002` (415 unsupported MIME).

**GET /health** — no parameters

```json
{
  "status": "ok",
  "rss_mb": 0.0,
  "uptime_seconds": 0.0,
  "version": "string"
}
```

---

## Part 2 — Frontend Architecture (v2.0, new)

### System Context

```text
┌──────────────────────────────────────────────────────────┐
│  Browser                                                 │
│  ┌───────────────────────────────────────────────────┐   │
│  │  Vue 3 SPA (localhost:5173 dev / static prod)     │   │
│  │                                                   │   │
│  │  DropZone → useUpload composable → ChunksView     │   │
│  └───────────────────────┬───────────────────────────┘   │
│                          │ HTTP (CORS)                   │
└──────────────────────────┼───────────────────────────────┘
                           │
                           ▼
           ┌───────────────────────────────┐
           │  FastAPI backend              │
           │  (localhost:8000 dev / prod)  │
           │                               │
           │  POST /ingest                 │
           │  GET  /health                 │
           └───────────────────────────────┘
```

The SPA and backend are deployed as separate artifacts. The SPA is a static bundle served by any CDN or simple file server. There is no shared codebase between the two — they communicate exclusively over HTTP.

### Frontend Project Layout

Use **feature-based layout** (not type-based). For an app this size (one feature: document ingestion), a single feature directory is overkill — use a flat composables + components pattern. The layout below is correctly sized for the v2.0 scope.

```text
frontend/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tsconfig.app.json
├── package.json
├── .env                    # VITE_API_BASE_URL=http://localhost:8000
├── .env.production         # VITE_API_BASE_URL=https://api.your-domain.com
│
└── src/
    ├── main.ts             # App entry: createApp(App).mount('#app')
    ├── App.vue             # Root component: dark-mode wrapper, layout shell
    │
    ├── api/
    │   └── ingest.ts       # fetch wrapper — buildFormData, postIngest, ApiError
    │
    ├── composables/
    │   ├── useUpload.ts    # Upload state machine (idle/dragging/uploading/result/error)
    │   └── useDarkMode.ts  # Dark mode toggle with localStorage persistence
    │
    ├── types/
    │   └── api.ts          # TypeScript types mirroring backend schemas
    │
    └── components/
        ├── DropZone.vue        # Drag-and-drop target + click-to-browse
        ├── UploadProgress.vue  # Progress/spinner shown during uploading state
        ├── ResultView.vue      # Chunks list + metadata sidebar container
        ├── ChunkCard.vue       # Single chunk with Markdown rendering
        ├── MetadataSidebar.vue # Document-level metadata panel
        ├── SkeletonLoader.vue  # Shimmer placeholder during processing
        └── ErrorBanner.vue     # Structured error display
```

**Rationale for flat component layout:** There is one user flow (drag → upload → inspect). Feature-based sub-directories add path depth without clarity at this scale. If a second feature (e.g., history, settings) is added in v2.1+, promote to `features/ingest/` at that point.

### TypeScript Types (api.ts)

Mirror the backend schemas exactly. Do not add optional fields that the backend guarantees.

```typescript
// src/types/api.ts

export interface ChunkSchema {
  chunk_id: string
  content: string          // Markdown text
  page_start: number
  page_end: number
  section_title: string
  chunk_index: number
  total_chunks: number
  word_count: number
}

export interface MetadataSchema {
  doc_id: string
  source_filename: string
  title: string
  author: string
  language: string         // ISO 639-1
  doc_type: string
  page_count: number
  chunk_count: number
  ingested_at: string      // ISO 8601, serialized by Pydantic
}

export interface ExtractionResponse {
  metadata: MetadataSchema
  chunks: ChunkSchema[]
}

export interface ApiError {
  error: {
    code: string
    message: string
  }
}
```

### API Layer (ingest.ts)

A thin, framework-agnostic fetch wrapper. No Axios — native `fetch` is sufficient and avoids a dependency for a single endpoint.

```typescript
// src/api/ingest.ts

const BASE_URL = import.meta.env.VITE_API_BASE_URL as string

export class IngestApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly httpStatus: number
  ) {
    super(message)
    this.name = 'IngestApiError'
  }
}

export async function postIngest(
  file: File,
  signal?: AbortSignal
): Promise<ExtractionResponse> {
  const form = new FormData()
  form.append('file', file)          // field name must match FastAPI param name: "file"

  const response = await fetch(`${BASE_URL}/ingest`, {
    method: 'POST',
    body: form,
    signal,
    // DO NOT set Content-Type manually — browser sets multipart boundary automatically
  })

  if (!response.ok) {
    const body = await response.json() as ApiError
    throw new IngestApiError(
      body.error.code,
      body.error.message,
      response.status
    )
  }

  return response.json() as Promise<ExtractionResponse>
}
```

**Critical:** Never manually set `Content-Type: multipart/form-data` when using `FormData`. The browser must set this header itself to include the correct boundary parameter. Setting it manually breaks the multipart parse on the server.

### Upload State Machine (useUpload.ts)

The upload flow has exactly five states. Model this as a discriminated union, not a bag of booleans.

```text
idle ──drag-enter──► dragging ──drag-leave──► idle
  │                     │
  └──file-selected───► uploading ──success──► result
  │                     │
  │                     └──error──► error
  │
  └──reset──► idle  (from result or error)
```

States:

- `idle` — nothing happening; DropZone shows default prompt
- `dragging` — file is hovering over drop zone; DropZone highlights
- `uploading` — `fetch` in flight; SkeletonLoader visible
- `result` — response received; ChunksView visible with stagger animation
- `error` — fetch failed or API error; ErrorBanner visible

```typescript
// src/composables/useUpload.ts

import { ref, readonly } from 'vue'
import { postIngest, IngestApiError } from '@/api/ingest'
import type { ExtractionResponse } from '@/types/api'

type UploadState = 'idle' | 'dragging' | 'uploading' | 'result' | 'error'

export function useUpload() {
  const state = ref<UploadState>('idle')
  const result = ref<ExtractionResponse | null>(null)
  const error = ref<{ code: string; message: string } | null>(null)
  let abortController: AbortController | null = null

  function onDragEnter() {
    if (state.value === 'idle') state.value = 'dragging'
  }

  function onDragLeave() {
    if (state.value === 'dragging') state.value = 'idle'
  }

  async function upload(file: File) {
    state.value = 'uploading'
    result.value = null
    error.value = null
    abortController = new AbortController()

    try {
      result.value = await postIngest(file, abortController.signal)
      state.value = 'result'
    } catch (err) {
      if (err instanceof IngestApiError) {
        error.value = { code: err.code, message: err.message }
      } else {
        error.value = { code: 'NETWORK', message: 'Network error. Is the backend running?' }
      }
      state.value = 'error'
    } finally {
      abortController = null
    }
  }

  function cancel() {
    abortController?.abort()
    state.value = 'idle'
  }

  function reset() {
    state.value = 'idle'
    result.value = null
    error.value = null
  }

  return {
    state: readonly(state),
    result: readonly(result),
    error: readonly(error),
    onDragEnter,
    onDragLeave,
    upload,
    cancel,
    reset,
  }
}
```

**Why `readonly()`:** Expose refs as readonly to prevent external mutation of state — state transitions must go through the composable's actions, not direct assignment from components.

### Frontend Component Responsibilities

| Component | Input | Output | Role |
| --- | --- | --- | --- |
| `App.vue` | — | Layout shell | Provides dark mode class on `<html>`, places components |
| `DropZone.vue` | `@dragenter`, `@dragleave`, `@drop`, `@change` | `emit('file', File)` | Captures file via drag-and-drop or click; delegates state to parent |
| `UploadProgress.vue` | `state: UploadState` | — | Shows spinner/progress indicator during `uploading` state |
| `SkeletonLoader.vue` | `count: number` | — | Renders N shimmer placeholder cards during `uploading` |
| `ResultView.vue` | `result: ExtractionResponse` | — | Container for chunks list + metadata sidebar |
| `ChunkCard.vue` | `chunk: ChunkSchema`, `index: number` | — | Renders single chunk: Markdown content + metadata badges |
| `MetadataSidebar.vue` | `metadata: MetadataSchema` | — | Document-level metadata panel (language, type, page count, etc.) |
| `ErrorBanner.vue` | `error: { code, message }` | `emit('retry')`, `emit('dismiss')` | Shows structured error with retry action |

### Data Flow: Drag-to-Chunks

```text
User drags file onto DropZone.vue
  │
  ▼
DropZone emits 'file' event with File object
  │
  ▼
App.vue calls useUpload().upload(file)
  │
  ├── state transitions to 'uploading'
  ├── SkeletonLoader renders (v-if state === 'uploading')
  │
  ▼
fetch POST /ingest with FormData
  │
  ├── success:
  │     state → 'result'
  │     result.value = ExtractionResponse
  │     ResultView renders (v-if state === 'result')
  │     TransitionGroup staggers ChunkCard animations (CSS delay via index)
  │
  └── error:
        state → 'error'
        error.value = { code, message }
        ErrorBanner renders (v-if state === 'error')
        User can retry → reset() → state → 'idle'
```

### Stagger Animation Pattern

Vue's built-in `<TransitionGroup>` handles stagger without GSAP dependency. CSS custom properties on each element carry the delay.

```vue
<!-- ResultView.vue -->
<TransitionGroup name="chunk" tag="div">
  <ChunkCard
    v-for="(chunk, index) in result.chunks"
    :key="chunk.chunk_id"
    :chunk="chunk"
    :style="{ '--delay': `${index * 60}ms` }"
  />
</TransitionGroup>
```

```css
/* ChunkCard.vue <style scoped> */
.chunk-enter-active {
  transition: opacity 0.35s ease var(--delay), transform 0.35s ease var(--delay);
}
.chunk-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
```

This pattern is pure CSS — no GSAP, no JavaScript animation hook. If more complex orchestration is needed (e.g., sequential reveal with scroll tracking), GSAP's stagger can be added via the TransitionGroup JavaScript hooks (`@enter`, `@leave`).

### Shimmer Skeleton Pattern

```vue
<!-- SkeletonLoader.vue -->
<template>
  <div v-for="n in count" :key="n" class="skeleton-card" />
</template>

<style scoped>
.skeleton-card {
  height: 120px;
  border-radius: 8px;
  background: linear-gradient(
    90deg,
    var(--skeleton-base) 25%,
    var(--skeleton-shimmer) 50%,
    var(--skeleton-base) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite linear;
}

@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
```

CSS custom properties (`--skeleton-base`, `--skeleton-shimmer`) are set on `:root[data-theme="dark"]` and `:root` for light/dark switching without JavaScript.

### Dark Mode Implementation

Tailwind CSS v4 uses class-based dark mode when `darkMode: 'class'` (or in v4 syntax, `@variant dark (.dark &)`). Toggle by adding/removing the `dark` class on `<html>`.

```typescript
// src/composables/useDarkMode.ts
import { ref, watch } from 'vue'

export function useDarkMode() {
  const isDark = ref(localStorage.getItem('theme') === 'dark')

  function apply(dark: boolean) {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }

  // Apply on mount
  apply(isDark.value)

  watch(isDark, apply)

  function toggle() {
    isDark.value = !isDark.value
  }

  return { isDark, toggle }
}
```

This composable is called once in `App.vue`. The `dark` class on `<html>` drives all Tailwind dark variant styles.

### DropZone Implementation

Use **VueUse `useDropZone`** rather than manual drag event handling. VueUse is the standard utility library for Vue 3 composables (200+ functions, actively maintained).

```vue
<!-- DropZone.vue -->
<script setup lang="ts">
import { ref } from 'vue'
import { useDropZone } from '@vueuse/core'

const emit = defineEmits<{ file: [file: File] }>()

const dropZoneRef = ref<HTMLDivElement>()

const { isOverDropZone } = useDropZone(dropZoneRef, {
  onDrop(files) {
    if (files && files[0]) emit('file', files[0])
  },
  dataTypes: ['application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/html'],
})

function onClickBrowse() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.pdf,.docx,.html'
  input.onchange = () => {
    if (input.files?.[0]) emit('file', input.files[0])
  }
  input.click()
}
</script>
```

**Note on `dataTypes` filtering in VueUse:** MIME type filtering during dragover only works reliably in Chrome/Firefox. Safari reports an empty type list during drag. Accept any drop and let the backend's Layer 2 MIME check reject unsupported types with a clear error message.

### Vite Configuration

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      // Dev-only proxy: avoids CORS entirely during development
      '/ingest': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    }
  }
})
```

**The dev proxy is an alternative to CORS during development**, not a replacement. The backend must still have CORS configured for production. Choose one of these strategies:

- **Strategy A (recommended):** Use Vite dev proxy (`/ingest` → backend). No CORS needed in dev. Configure CORS on backend for production origin only.
- **Strategy B:** Configure CORS on backend for both `localhost:5173` (dev) and production origin. No proxy needed.

Strategy A is cleaner — CORS config only ever contains production origins, no localhost exceptions to remember.

---

## Part 3 — Backend Changes Required for v2.0

### File: `src/selection_maid/adapters/http/app.py` (MODIFY)

Add `CORSMiddleware` to the FastAPI app. This is the only backend change required for the frontend milestone.

```python
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI(
        title="SelectionMaid",
        # ... existing args
        lifespan=_lifespan,
    )

    # CORS: allow the SPA origin to call /ingest and /health
    # Use explicit origins — never "*" in production
    allowed_origins = [
        "http://localhost:5173",           # Vite dev server
        "http://localhost:4173",           # vite preview
        # Add production SPA URL here: "https://selection-maid.your-domain.com"
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,           # No cookies or Auth headers needed
        allow_methods=["GET", "POST"],     # Only the methods the SPA uses
        allow_headers=["*"],               # Content-Type set by browser for multipart
    )

    return app
```

**Why `allow_credentials=False`:** The SPA sends no cookies or `Authorization` headers. Keeping credentials disabled allows `allow_origins=["*"]` as a fallback if needed. With `allow_credentials=True`, wildcards are forbidden by the CORS spec and the browser will reject the preflight.

**Why explicit methods:** `allow_methods=["GET", "POST"]` rather than `["*"]`. The SPA only uses these two methods. Restrict the surface.

**Where in the file:** `add_middleware` must be called before any route is registered. Call it inside `create_app()` before `return app`, after the FastAPI instance is created but before `_lifespan` wires the router. The lifespan wires routes on startup — that timing is correct because `add_middleware` applies at the ASGI layer regardless.

**Configuring origins from environment:** For a real deployment, read origins from an environment variable rather than hardcoding:

```python
import os

cors_origins_raw = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
allowed_origins = [o.strip() for o in cors_origins_raw.split(",")]
```

### File: `src/selection_maid/config.py` (OPTIONALLY MODIFY)

Add a `cors_allowed_origins: list[str]` field to `HttpConfig` if origins should be part of the config system rather than a raw env var.

---

## Part 4 — Full System Data Flow (v2.0)

```text
User drops PDF on DropZone.vue
         │
         ▼
DropZone emits 'file' (File object)
         │
         ▼
App.vue calls useUpload().upload(file)
         │
         ├─ state → 'uploading'
         ├─ SkeletonLoader renders N cards (guess: chunk_count unknown until response)
         │
         ▼
fetch('POST /ingest', { body: FormData { file: File } })
         │         [CORS preflight OPTIONS /ingest if cross-origin]
         │         [FastAPI CORSMiddleware responds to OPTIONS]
         │
         ▼
FastAPI /ingest handler
  │ Layer 1: Content-Length check
  │ Layer 2: MIME type check (content_type)
  │ Layer 3: Magic bytes check
  │ ExtractionService.process(RawInput)
  │   → DoclingAdapter → HeuristicFilter → MarkdownChunker → MetadataEnricher
  └─ ExtractionResponse JSON
         │
         ▼
fetch response → result.value = ExtractionResponse
         │
         ├─ state → 'result'
         │
         ▼
ResultView.vue renders:
  ├─ MetadataSidebar (doc_id, title, language, doc_type, page_count, chunk_count)
  └─ TransitionGroup of ChunkCard components
       └─ CSS stagger: --delay = index * 60ms
            └─ each card: opacity 0→1 + translateY 12px→0
```

---

## Part 5 — Build Order for Frontend Phases

The frontend should be built in this order to minimize integration surprises:

| Step | Phase Focus | Why This Order |
| --- | --- | --- |
| 1 | Backend CORS middleware | Unblocks all browser testing immediately; small change, zero risk |
| 2 | Project scaffold + types + API layer | `types/api.ts` and `api/ingest.ts` have no UI dependencies; can be verified against a running backend before any Vue component exists |
| 3 | `useUpload` composable | Pure logic; testable with Vitest without any DOM rendering |
| 4 | `DropZone` + `UploadProgress` + `ErrorBanner` | Core upload interaction; get the upload working before building result display |
| 5 | `SkeletonLoader` + loading state | Polish the waiting state before building result — avoids jarring flash to data |
| 6 | `ChunkCard` + `MetadataSidebar` + `ResultView` | Result display depends on knowing the exact shape of ExtractionResponse, which is validated after steps 2-4 |
| 7 | `TransitionGroup` stagger animation + dark mode | Animation is purely additive on top of working functionality; add last to avoid animation interfering with debugging |

**Critical dependency:** Steps 4-7 all require a running backend with CORS configured (Step 1). Do not build UI components against a mocked response if the real backend is available — mock the `useUpload` state instead, not the API layer.

---

## Part 6 — Architecture Anti-Patterns for the Frontend

### Anti-Pattern 1: Using Pinia for Upload State

**What goes wrong:** Defining a Pinia store for upload state when a composable suffices.

**Why bad:** Pinia adds a global singleton. Upload state is scoped to the session and does not need to survive navigation or be shared across multiple components simultaneously. A composable called in `App.vue` provides the same singleton behavior without the global store.

**Instead:** Use `useUpload()` called once in `App.vue` and pass `state`, `result`, `error` as props or provide/inject. Add Pinia only if a second feature (e.g., upload history) needs cross-route state.

### Anti-Pattern 2: Setting Content-Type for FormData Manually

**What goes wrong:** `headers: { 'Content-Type': 'multipart/form-data' }` in the fetch call.

**Why bad:** FormData requires a `boundary` parameter in the Content-Type header. Only the browser knows the boundary string it generated. Setting Content-Type manually overwrites the browser's auto-generated header and removes the boundary. FastAPI cannot parse the body.

**Instead:** Never set `Content-Type` when posting `FormData`. Let the browser handle it.

### Anti-Pattern 3: Using Boolean Flags for State

**What goes wrong:** `isLoading`, `isError`, `isDragging`, `hasResult` as separate booleans.

**Why bad:** Illegal state combinations become possible (e.g., `isLoading: true, hasResult: true`). Template conditionals become complex chains of `v-if` with multiple flags. Adding a new state (e.g., `queued`) requires touching every conditional.

**Instead:** Use the discriminated union state machine: one `state` ref with string literal type. Each UI section is `v-if="state === 'uploading'"`. Legal states are enforced by the type.

### Anti-Pattern 4: Rendering Markdown as Plain Text

**What goes wrong:** Displaying `chunk.content` directly in a `<p>` or `<pre>` without Markdown parsing.

**Why bad:** The backend returns `content` as Markdown. Headings, bold text, tables, and code blocks render as raw syntax characters, making the result view unusable for inspection.

**Instead:** Use `markdown-it` (via `vue3-markdown-it` or direct usage) to render `content` as HTML inside `ChunkCard`. Sanitize the output with DOMPurify if content comes from untrusted sources (for an internal dev tool, this is lower priority but good practice).

### Anti-Pattern 5: Hardcoding the Backend URL

**What goes wrong:** `fetch('http://localhost:8000/ingest', ...)` in the component or composable.

**Why bad:** Does not work in production without a code change and rebuild.

**Instead:** Always use `import.meta.env.VITE_API_BASE_URL`. In development with the Vite proxy, set `VITE_API_BASE_URL=` (empty string) so fetch calls go to the same origin and the proxy handles routing. In production, set it to the real backend URL.

---

## Sources

**Backend (v1.0, unchanged):**

- FastAPI docs: [Testing Dependencies with Overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/) — HIGH confidence
- Python typing spec: [PEP 544 — Protocols: Structural subtyping](https://peps.python.org/pep-0544/) — HIGH confidence

**Frontend (v2.0):**

- FastAPI docs: [CORS (Cross-Origin Resource Sharing)](https://fastapi.tiangolo.com/tutorial/cors/) — HIGH confidence, fetched directly
- Vue.js docs: [Composables](https://vuejs.org/guide/reusability/composables) — HIGH confidence, fetched directly
- Vue.js docs: [TransitionGroup](https://vuejs.org/guide/built-ins/transition-group) — HIGH confidence
- VueUse docs: [useDropZone](https://vueuse.org/core/usedropzone/) — HIGH confidence
- Vite docs: [Env Variables and Modes](https://vite.dev/guide/env-and-mode) — HIGH confidence
- Vite docs: [Server Options (proxy)](https://vite.dev/config/server-options) — HIGH confidence
- Vue Router docs: [Different History modes](https://router.vuejs.org/guide/essentials/history-mode.html) — HIGH confidence
- create-vue: [GitHub — vuejs/create-vue](https://github.com/vuejs/create-vue) — HIGH confidence
- VueUse issue [#4085](https://github.com/vueuse/vueuse/issues/4085): useDropZone/useFileDialog API consistency note — MEDIUM confidence
- Smashing Magazine: [Drag-and-Drop File Uploader with Vue.js 3](https://www.smashingmagazine.com/2022/03/drag-drop-file-uploader-vuejs-3/) — MEDIUM confidence

---

*Architecture research updated: 2026-05-25 for v2.0 frontend milestone*
*Backend architecture unchanged from v1.0 (2026-05-23)*
