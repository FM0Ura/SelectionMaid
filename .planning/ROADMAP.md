# Roadmap: SelectionMaid

## Milestones

- ✅ **v1.0 Multi-Format Extraction** — Phases 1-7 (shipped 2026-05-25)
- 🚧 **v2.0 Frontend** — Phases 8-13 (in progress)

## Phases

v1.0 archive: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)

### v2.0 Frontend (In Progress)

**Milestone Goal:** SPA Vue 3 + Vite que expõe todo o pipeline do SelectionMaid com dark mode minimalista, drag-and-drop animado, skeleton loading, stagger animation na revelação dos chunks, e transições de view suaves — consumindo a FastAPI existente via HTTP.

- [x] **Phase 8: Backend CORS + Project Scaffold** — Enable browser access and establish the frontend development environment (completed 2026-05-26)
- [x] **Phase 9: TypeScript Types + API Layer + State Machine** — Typed contract and tested state machine before any component is built (completed 2026-05-26)
- [x] **Phase 10: Upload Interaction** — Complete drop zone with drag, click fallback, validation, and error handling (completed 2026-05-26)
- [x] **Phase 11: Skeleton Loading + Processing Feedback** — Perceived-performance layer for the 1-30 second backend wait (completed 2026-05-26)
- [ ] **Phase 12: Result Display** — Chunk list with Markdown rendering, copy-to-clipboard, and metadata panel
- [ ] **Phase 13: Animation + View Transitions** — Stagger reveal, smooth state transitions, and drag-active visual upgrade

## Phase Details

### Phase 8: Backend CORS + Project Scaffold

**Goal**: Browser requests from the SPA reach the FastAPI backend and the frontend development environment is running

**Depends on**: Nothing (first phase of v2.0)

**Requirements**: INT-01

**Success Criteria** (what must be TRUE):

1. A preflight `OPTIONS` request from `http://localhost:5173` to the FastAPI server returns `Access-Control-Allow-Origin` without error
2. Running `npm run dev` starts a Vite dev server and the browser shows a Vue 3 app at `localhost:5173`
3. The Vite dev proxy routes `/ingest` to `localhost:8000` so no CORS error appears in the browser console during local development
4. Tailwind CSS v4 and shadcn-vue are initialized and a sample dark-mode component renders correctly

**Plans**: 2 plans
- [x] [08-01-PLAN.md](phases/08-backend-cors-project-scaffold/08-01-PLAN.md) — Backend CORS configuration and integration tests
- [x] [08-02-PLAN.md](phases/08-backend-cors-project-scaffold/08-02-PLAN.md) — Frontend project scaffold (Vue 3, Vite, Tailwind v4, shadcn-vue)

**UI hint**: yes

### Phase 9: TypeScript Types + API Layer + State Machine

**Goal**: Every component downstream has a typed contract and a tested state machine before any UI is built

**Depends on**: Phase 8

**Requirements**: UPL-03, PROC-01, PROC-03

**Success Criteria** (what must be TRUE):

1. TypeScript interfaces in `src/types/api.ts` match the backend `ChunkSchema`, `MetadataSchema`, and `ExtractionResponse` exactly — verified by compiling against a real API response
2. `postIngest(file, signal)` in `src/api/ingest.ts` sends a `FormData` POST without manually setting `Content-Type` and returns a typed `ExtractionResponse`
3. The `useUpload` composable enforces the state machine: only valid transitions (idle → dragging → uploading → result/error) are reachable
4. A file with wrong type or size exceeding 50MB triggers an error state with a human-readable message before any network request is made
5. A fetch that exceeds 130 seconds triggers a timeout error state with a clear message

**Plans**: 3 plans
Plans:
- [x] 12-01-PLAN.md — Foundation and Markdown Rendering
- [ ] 12-02-PLAN.md — Result Display Components
- [ ] 12-03-PLAN.md — Result View Integration
- [x] [09-01-PLAN.md](phases/09-typescript-types-api-layer-state-machine/09-01-PLAN.md) — Frontend testing infrastructure and type definitions
- [x] [09-02-PLAN.md](phases/09-typescript-types-api-layer-state-machine/09-02-PLAN.md) — API layer, error mapping, and validation
- [x] [09-03-PLAN.md](phases/09-typescript-types-api-layer-state-machine/09-03-PLAN.md) — useUpload state machine composable

### Phase 10: Upload Interaction

**Goal**: Users can submit a document to the pipeline via drag-and-drop or file picker, with full visual feedback and error handling

**Depends on**: Phase 9

**Requirements**: UPL-01, UPL-02, NAV-02, NAV-03

**Success Criteria** (what must be TRUE):

1. Dragging a file over the drop zone shows an animated active state (border pulse, overlay with icon) and dropping it starts the upload
2. Clicking a button on the drop zone opens the system file picker and selecting a file starts the upload
3. A user who has never uploaded sees a welcoming idle/empty state with a clear call-to-action before the first upload
4. If the API returns an error or the request fails, a structured error banner appears with a retry button that returns the user to the upload state

**Plans**: 2 plans
- [x] [10-01-PLAN.md](phases/10-upload-interaction/10-01-PLAN.md) — Foundation and Error UI
- [x] [10-02-PLAN.md](phases/10-upload-interaction/10-02-PLAN.md) — Interaction Logic and Animations

**UI hint**: yes

### Phase 11: Skeleton Loading + Processing Feedback

**Goal**: Users see continuous visual feedback during the entire backend processing window, eliminating perceived dead time

**Depends on**: Phase 10

**Requirements**: PROC-02

**Success Criteria** (what must be TRUE):

1. While the API call is in-flight, the UI shows animated shimmer skeleton placeholder cards in place of the chunk list — no blank area
2. The shimmer animation uses a sweeping gradient keyframe (not a static color), communicating active processing
3. An elapsed time counter increments during processing so the user knows time is passing

**Plans**: 2 plans
- [x] [11-01-PLAN.md](phases/11-skeleton-loading-processing-feedback/11-01-PLAN.md) — Timer Logic & Atomic Components
- [x] [11-02-PLAN.md](phases/11-skeleton-loading-processing-feedback/11-02-PLAN.md) — Layout Transition & Flow Integration

**UI hint**: yes

### Phase 12: Result Display

**Goal**: Users can read, inspect, and copy the extracted chunks and document metadata returned by the API

**Depends on**: Phase 11

**Requirements**: RES-01, RES-03, RES-04

**Success Criteria** (what must be TRUE):

1. Each chunk is rendered as formatted Markdown (headings, code blocks, bold text) — not raw Markdown strings
2. Every chunk card has a copy-to-clipboard button; clicking it copies the raw chunk text and briefly shows a "Copied!" confirmation
3. A metadata panel displays the document's inferred type, detected language, inferred title, and processing time
4. A reset button on the result view returns the user to the idle upload state

**Plans**: 3 plans
Plans:
- [ ] 12-01-PLAN.md — Foundation and Markdown Rendering
- [ ] 12-02-PLAN.md — Result Display Components
- [ ] 12-03-PLAN.md — Result View Integration

**UI hint**: yes

### Phase 13: Animation + View Transitions

**Goal**: Users experience a polished interface where all state changes and content reveals are smooth and intentional

**Depends on**: Phase 12

**Requirements**: RES-02, NAV-01

**Success Criteria** (what must be TRUE):

1. After the API response arrives, chunks appear one-by-one in sequence with a visible stagger delay between cards — not all at once
2. Navigating from the upload view to the result view (and back) is animated with a smooth transition rather than an instant swap
3. All animations use only `transform` and `opacity` CSS properties — no layout-thrashing properties (`height`, `top`, `width`)

**Plans**: TBD

**UI hint**: yes

## Progress

**Execution Order:** 8 → 9 → 10 → 11 → 12 → 13

| Phase | Milestone | Plans Complete | Status | Completed |
| --- | --- | --- | --- | --- |
| 8. Backend CORS + Project Scaffold | v2.0 | 2/2 | Complete   | 2026-05-26 |
| 9. TypeScript Types + API Layer + State Machine | v2.0 | 3/3 | Complete   | 2026-05-26 |
| 10. Upload Interaction | v2.0 | 2/2 | Complete | 2026-05-26 |
| 11. Skeleton Loading + Processing Feedback | v2.0 | 2/2 | Complete | 2026-05-26 |
| 12. Result Display | v2.0 | 1/3 | In Progress|  |
| 13. Animation + View Transitions | v2.0 | 0/? | Not started | - |
