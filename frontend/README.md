<!-- generated-by: gsd-doc-writer -->
# SelectionMaid Frontend

Vue 3 SPA that provides the drag-and-drop interface for the SelectionMaid document ingestion service — upload a file, watch it process with skeleton feedback, and browse or copy the resulting Markdown chunks.

Part of the [SelectionMaid](../) monorepo.

## Prerequisites

- **Node.js >= 18** (npm is included with Node; no other runtime required)
- **SelectionMaid backend** running at `http://localhost:8000` (see the [backend README](../README.md))

## Installation

```bash
cd frontend
npm install
```

## Development

Start the Vite dev server with hot-module reload and backend proxy:

```bash
npm run dev
```

The dev server starts at `http://localhost:5173`. Requests to `/api/*` are proxied to `http://localhost:8000`, so the backend must be running separately.

## Available Scripts

| Command | Description |
| --- | --- |
| `npm run dev` | Start Vite dev server with HMR |
| `npm run build` | Type-check with `vue-tsc`, then produce a production bundle |
| `npm run preview` | Serve the production bundle locally for smoke-testing |
| `npm run test:unit` | Run the Vitest unit test suite |
| `npm run test:ui` | Run Vitest with the browser-based UI |

## Architecture

### Composable state machine — `src/composables/useUpload.ts`

All upload state is owned by a single `useUpload` composable. State transitions are expressed as a discriminated union (`UploadState`) with the following statuses:

```text
idle → dragging → uploading → processing → success
                                         ↘ error (from any async step)
```

`useUpload` exposes `state` (readonly ref), `elapsedSeconds` (readonly ref), and the actions `startUpload`, `setDragging`, `setError`, and `reset`. No global state store (Pinia) is used; the composable instance is created once in `App.vue` and passed down as a prop.

### API layer — `src/api/`

| File | Purpose |
| --- | --- |
| `ingest.ts` | `postIngest(file)` — `POST /api/ingest` via `fetch`, 130 s timeout, returns `ExtractionResponse` |
| `errors.ts` | `ApiResponseError` class; `mapApiError` normalises any thrown value to a user-facing string |

The Vite dev-server proxy rewrites `/api/*` → `http://localhost:8000/*`, so the frontend never embeds the backend origin directly.

### Component tree

```text
App.vue
├── DropZone.vue          — drag-and-drop target, file-input trigger, delegates to upload.startUpload()
│   ├── DropOverlay.vue   — full-screen drop highlight shown while dragging
│   └── ErrorBanner.vue   — inline error message when state.status === 'error'
├── SkeletonChunk.vue     — animated skeleton card shown for each expected chunk while processing
└── ResultView.vue        — success view; receives ExtractionResponse and elapsedSeconds
    ├── MetadataCard.vue  — document-level metadata (title, author, language, page count, etc.)
    ├── ChunkCard.vue     — individual chunk with section title, word count, and rendered Markdown
    └── MarkdownRenderer.vue — sanitised markdown-it render (DOMPurify + highlight.js)
```

UI primitives live in `src/components/ui/` (alert, button, card, skeleton) sourced from shadcn-vue.

### Type contracts — `src/types/api.ts`

The `ExtractionResponse` type mirrors the backend response schema:

```ts
interface ExtractionResponse {
  metadata: DocumentMetadata   // doc_id, source_filename, title, author, language, doc_type, page_count, chunk_count, ingested_at
  chunks: Chunk[]              // chunk_id, content, page_start, page_end, section_title, chunk_index, total_chunks, word_count
}
```

## Testing

```bash
# Run all unit tests
npm run test:unit

# Run with the Vitest browser UI (coverage, file filter, re-run controls)
npm run test:ui
```

Test files live next to their subjects as `*.spec.ts` files:

- `src/App.spec.ts`
- `src/api/ingest.spec.ts`, `errors.spec.ts`
- `src/lib/api.spec.ts`, `formatters.spec.ts`, `validators.spec.ts`
- `src/components/result/ChunkCard.spec.ts`, `MarkdownRenderer.spec.ts`, `MetadataCard.spec.ts`, `ResultView.spec.ts`

The test environment is `jsdom` (configured in `vitest.config.ts`). Async component tests use `@vue/test-utils`.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Framework | Vue 3.5 + TypeScript 5.5 |
| Build | Vite 6 |
| Styling | Tailwind CSS v4 + shadcn-vue (reka-ui) |
| Animation | motion-v v2.2 |
| Markdown | markdown-it + markdown-it-highlightjs + DOMPurify |
| Testing | Vitest + @vue/test-utils + jsdom |
| State | `useUpload` composable (no Pinia) |
