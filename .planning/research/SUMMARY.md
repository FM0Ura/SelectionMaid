# Project Research Summary

**Project:** SelectionMaid — v2.0 Frontend Milestone
**Domain:** Vue 3 SPA consuming a FastAPI document-processing backend
**Researched:** 2026-05-25
**Confidence:** HIGH

---

## Executive Summary

SelectionMaid v2.0 adds a minimal dark-mode SPA that consumes the already-complete v1.0 FastAPI backend. The frontend is a pure static artifact — no SSR, no Nuxt, no shared codebase with the Python service — serving one user flow: drag a document onto a drop zone, wait for the backend to process it, and inspect the extracted chunks with their Markdown content and metadata. The correct stack is Vue 3 + Vite 6 + Tailwind CSS v4 + shadcn-vue + motion-v. State is managed by a single `useUpload` composable modeled as a discriminated union state machine (idle / dragging / uploading / result / error). No Pinia, no Axios — the scope does not justify them.

The recommended build order is dictated by three dependency chains. First, CORS middleware must land in the backend (`adapters/http/app.py`) before any browser test is possible — this is the only backend change required for the entire milestone. Second, the TypeScript types and fetch wrapper should be established before any Vue component is built, because every component downstream depends on the `ExtractionResponse` schema. Third, animation is purely additive and must be built last, on top of verified working functionality, to prevent animation interactions from masking functional bugs during development.

The primary risk category for this milestone is not technology complexity — it is well-understood tooling. The risk is implementation traps: missing `dragover.preventDefault()` that silently prevents drops, manually setting `Content-Type` on a `FormData` fetch that breaks multipart parsing on the server, setting `allow_origins=["*"]` alongside `allow_credentials=True` causing every preflight to fail, attaching no `AbortSignal` to the fetch so a 90-second OCR job hangs the UI indefinitely, and animating `height`/`top` instead of `transform`/`opacity` causing layout jank that defeats the premium feel this milestone is designed to deliver. All five pitfalls are one-line mistakes with non-obvious symptoms.

---

## Key Findings

### Recommended Stack

The frontend adds exactly seven net-new runtime dependencies to the repository. Vite 6 scaffolds and serves the SPA; Vue Router v5 provides route-level `<Transition>` hooks for view transitions; `@vueuse/core` v14 supplies `useDropZone` (drag-and-drop), `useClipboard` (copy-to-clipboard), and `useColorMode`; motion-v v2.2 handles stagger animations and entrance/exit orchestration (MIT-licensed, no GSAP commercial-license ambiguity); Tailwind CSS v4 styles everything via its Vite plugin (no `tailwind.config.js` required); shadcn-vue provides accessible component primitives via CLI copy-paste (no npm install); and reka-ui is the transitive headless primitive layer under shadcn-vue. Native `fetch` replaces Axios entirely.

**Core technologies:**

- **Vite 6 + @vitejs/plugin-vue**: Build tool and dev server — native ESM, sub-50ms HMR; dev proxy eliminates CORS in development
- **Vue 3.5 + TypeScript 5.5**: UI framework — Composition API, `<script setup>`, full TS integration; required by @vueuse/core v14
- **Vue Router v5**: Client-side routing — `<RouterView>` + `<Transition>` enables animated view transitions
- **Tailwind CSS v4 + @tailwindcss/vite**: Utility-first CSS — Vite plugin delivery, no config file, CSS-variable design tokens, class-based dark mode via `@variant dark`
- **shadcn-vue (CLI)**: UI components — copied into `src/components/ui/`, owned not installed, built on Reka UI + Tailwind, dark mode first-class
- **motion-v v2.2**: Animation — Vue-native Motion library, `stagger()` for chunk reveal cascades, WAAPI-accelerated, MIT license
- **@vueuse/core v14**: Composable utilities — `useDropZone`, `useClipboard`, `useColorMode`

**What not to add:** Pinia (single linear flow; composable is sufficient), Axios (14kB for one endpoint), GSAP (commercial license ambiguity for products), vue-dropzone (Vue 2, unmaintained), any skeleton loader library (10 lines of CSS with Tailwind CSS variables handles it natively).

### Expected Features

**Must have (table stakes):**

- Drag-and-drop file drop zone with visible active state (border + background change)
- Click-to-browse `<input type="file">` fallback — required for keyboard users and touch devices
- Client-side file type and size validation with inline error message before the POST
- Upload state machine: idle → dragging → uploading → result → error → idle
- Shimmer skeleton loading state during backend processing (1-30 second wait)
- Chunk list with Markdown rendering per chunk (`chunk.content` is Markdown; raw strings look broken)
- Chunk index badge (`chunk_index / total_chunks`)
- Document metadata display (`title`, `language`, `doc_type`, `page_count`, `chunk_count`, `ingested_at`)
- Copy-to-clipboard per chunk with "Copied!" confirmation feedback
- Error state with human-readable message and retry affordance
- Empty/idle state with clear call to action
- Reset button to return to upload state

**Should have (differentiators):**

- Stagger reveal animation on chunk list (30-60ms delay per card, `transform` + `opacity` only — the signature visual feature)
- Shimmer gradient animation on skeleton (sweeping `background-position` keyframe, not static grey)
- Smooth `<Transition>` between app states (200ms max, prevents jarring jumps)
- Drop zone drag-active visual upgrade: subtle scale, heavier border, glow pulse
- Per-chunk expand/collapse for long chunks (CSS `max-height` transition)
- Client-side chunk text search/filter (Vue `computed` on reactive `chunks` ref)
- Elapsed time counter during processing ("Processing... 4s") via `setInterval`
- Chunk count summary after load using `metadata.chunk_count`

**Defer to v2.1:**

- Per-chunk word count badge
- Keyboard shortcut (Enter/Space on drop zone)
- Dark mode toggle (dark-only for v2.0)
- Upload progress bar (byte-level XHR progress misleads; elapsed counter is more honest)
- Multiple file upload queue (3x complexity for single-file tool)
- History / session persistence (ephemeral by design)
- Authentication UI (infrastructure concern, not SPA concern)

### Architecture Approach

The SPA is a separate static artifact deployed independently from the FastAPI backend. All state lives in a single `useUpload` composable called once in `App.vue` and passed down via props — no global store. The API layer is a thin `src/api/ingest.ts` fetch wrapper that never touches Vue reactivity; the composable owns reactivity. Components are purely presentational. The stagger animation uses Vue's built-in `<TransitionGroup>` with CSS custom property delay (`--delay: index * 60ms`) — no JavaScript animation hook required for the base case. The Vite dev proxy eliminates CORS during development so backend CORS config only ever contains production origins.

**Major components:**

1. **`src/api/ingest.ts`** — framework-agnostic fetch wrapper; `postIngest(file, signal)` returns `ExtractionResponse`; throws typed `IngestApiError`; never sets `Content-Type` manually
2. **`src/composables/useUpload.ts`** — discriminated union state machine (`'idle' | 'dragging' | 'uploading' | 'result' | 'error'`); owns `AbortController` for cancellation; exposes `readonly` refs
3. **`src/types/api.ts`** — TypeScript interfaces mirroring backend `ChunkSchema`, `MetadataSchema`, `ExtractionResponse`, `ApiError`
4. **`DropZone.vue`** — uses `useDropZone` from @vueuse/core; drag depth counter prevents child-element flickering; always includes `<input type="file">` fallback
5. **`SkeletonLoader.vue`** — N shimmer placeholder cards during `uploading` state; pure CSS `@keyframes` shimmer using Tailwind CSS variable tokens
6. **`ResultView.vue` + `ChunkCard.vue`** — `<TransitionGroup>` stagger on chunk list; Markdown rendered via `markdown-it`; `useClipboard` for copy action
7. **`MetadataSidebar.vue`** — sticky document-level metadata panel
8. **`src/selection_maid/adapters/http/app.py` (backend, single change)** — `CORSMiddleware` registered before all other middleware; origins from `CORS_ORIGINS` env var; `allow_credentials=False`

### Critical Pitfalls

1. **CORS misconfiguration** — `allow_origins=["*"]` + `allow_credentials=True` is rejected by all browsers per spec; every preflight fails. Prevention: use `allow_credentials=False`; register `CORSMiddleware` first before all other middleware; drive allowed origins from `CORS_ORIGINS` env var.

2. **`Content-Type` override on FormData fetch** — manually setting `Content-Type: multipart/form-data` removes the browser-generated `boundary` parameter; FastAPI returns 422. Prevention: never set `Content-Type` when posting `FormData`.

3. **Drop zone flickering (child element `dragleave` events)** — `dragleave` fires when the cursor moves from the drop zone to a child element, causing the active state to flash. Prevention: track drag depth with a counter (`dragCount++` on `dragenter`, `dragCount--` on `dragleave`; zone is active when `dragCount > 0`; reset to 0 on `drop`).

4. **No `AbortSignal` timeout on the fetch call** — Docling OCR can take 90-120 seconds; without a timeout the browser waits indefinitely. Prevention: use `AbortSignal.timeout(130_000)`; store `AbortController` ref for manual cancellation; abort on component unmount.

5. **Animating layout-affecting CSS properties** — animating `top`, `left`, `height`, `width` forces Layout + Paint on every frame; 50 chunk cards staggering simultaneously produces visible jank. Prevention: animate only `transform` (translateY, scale) and `opacity`.

---

## Implications for Roadmap

The build order is forced by hard dependencies. CORS must precede any browser test. Types and API layer must precede any component that calls the backend. Upload interaction must be verified before result display is built. Animation is last — purely additive.

### Phase 1: Backend CORS + Project Scaffold

**Rationale:** CORS is the gating dependency for everything else. No browser request can succeed without it, and it is a one-file backend change with zero architectural risk. Scaffolding the frontend in the same phase establishes the development environment for all subsequent phases.

**Delivers:** Running Vite dev server; Vite proxy configured (`/ingest` → `localhost:8000`); CORSMiddleware added to `app.py` with env-var origins; Tailwind v4 + shadcn-vue initialized; ESLint + Prettier configured.

**Avoids:** F-6 (wildcard + credentials CORS), F-7 (middleware registration order), F-8 (hardcoded origins).

### Phase 2: TypeScript Types + API Layer + State Machine

**Rationale:** `src/types/api.ts` has no UI dependencies and can be verified against a running backend before any Vue component exists. The `useUpload` composable is fully unit-testable with Vitest without DOM rendering. Establishing these two layers first means every downstream component has a correctly typed contract and a tested state machine.

**Delivers:** `src/types/api.ts` (all backend schema interfaces); `src/api/ingest.ts` (postIngest with AbortSignal, 130s timeout); `src/composables/useUpload.ts` (5-state machine, readonly refs, AbortController); Vitest unit tests for state transitions.

**Avoids:** Anti-pattern 3 (boolean flag state), F-16 (no fetch timeout), Anti-pattern 2 (Content-Type override), Anti-pattern 5 (hardcoded backend URL).

### Phase 3: Upload Interaction (DropZone + Validation + Error)

**Rationale:** The drop zone is the entry point of the entire user flow. It must work completely — drag, click fallback, type validation, size validation, error display — before building result display. This phase is verifiable end-to-end without building the result view.

**Delivers:** `DropZone.vue` (useDropZone, drag depth counter, click-to-browse fallback, accepted formats display); client-side type + size validation; `ErrorBanner.vue` with retry; `UploadProgress.vue`; integration test against real backend.

**Avoids:** F-9 (missing dragover.preventDefault), F-10 (child element flickering), F-11 (no touch/keyboard fallback), F-12 (async dataTransfer access).

### Phase 4: Skeleton Loading + Processing Feedback

**Rationale:** Building the loading state before the result display prevents jarring visual transitions during development and sets the perceived-performance standard. The shimmer skeleton anchors user expectations during the 1-30 second wait.

**Delivers:** `SkeletonLoader.vue` (shimmer CSS keyframe via Tailwind CSS variable tokens); elapsed time counter; state-conditional rendering in `App.vue`.

**Avoids:** F-17 (no progressive feedback during processing).

### Phase 5: Result Display (Chunks + Metadata)

**Rationale:** Results can only be built after the API contract is validated (Phase 2) and the upload flow is verified end-to-end (Phase 3). Chunk rendering has its own complexity: Markdown parsing, expand/collapse, copy-to-clipboard, metadata sidebar.

**Delivers:** `ResultView.vue` with reset; `ChunkCard.vue` (markdown-it rendering, index badge, useClipboard, expand/collapse); `MetadataSidebar.vue` (sticky, null-safe); chunk text search/filter via computed; virtualization guard for 80+ chunks.

**Avoids:** Anti-pattern 4 (rendering Markdown as plain text), F-13 (all chunks without virtualization guard), F-15 (synchronous Markdown rendering blocking main thread).

### Phase 6: Animation + View Transitions

**Rationale:** Animation is purely additive on top of verified working functionality. Adding it last means animation interactions cannot mask functional bugs. This phase also carries the highest risk of subtle regressions (layout jank, context leaks) and benefits from a stable tested base.

**Delivers:** `<TransitionGroup>` stagger on chunk list (CSS `--delay: index * 60ms`; transform + opacity only); `<Transition>` between app states (fade/slide, 200ms max); drop zone drag-active visual upgrade; shimmer entrance animation.

**Avoids:** F-1 (layout-thrashing properties), F-3 (animation context leak on unmount), F-4 (stagger on all elements — cap to first 15 visible), F-5 (permanent will-change in CSS).

### Phase Ordering Rationale

- CORS first because no browser test is possible without it; lowest risk, highest unlock value
- Types + API + composable second because every component is downstream; a typed, tested contract eliminates a whole class of bugs
- Upload before results because the result display requires a verified real API response shape
- Animation last to prevent animated transitions from hiding whether components render correctly with real data

### Research Flags

Phases with standard patterns (research-phase can be skipped during planning):
- **Phase 1 (CORS + Scaffold):** Well-documented FastAPI CORS docs + Vite scaffold template; implementation is mechanical
- **Phase 2 (Types + State Machine):** TypeScript interfaces from known API schema; composable pattern fully specified in research
- **Phase 3 (Drop Zone):** `useDropZone` documented; all pitfalls enumerated with solutions in PITFALLS.md
- **Phase 4 (Skeleton):** Pure CSS pattern fully specified in STACK.md; no unknowns

Phases that may benefit from deeper research during planning:
- **Phase 5 (Result Display):** `markdown-it` integration in Vue 3 SFCs and DOMPurify sanitization pairing — worth a quick spike before full build
- **Phase 6 (Animation):** motion-v v2.2 integration with Vue's `<TransitionGroup>` JavaScript hooks (`@enter`, `@leave`) — the hybrid JS-controlled stagger may need a spike if CSS-only approach proves insufficient

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Core libraries verified on npm: motion-v 2.2.1, @vueuse/core 14.3.0, Vue Router 5.0.7; Vite 6 and Tailwind v4 from official release announcements |
| Features | HIGH | Patterns cross-referenced against NN/G, Uploadcare UX research, Smashing Magazine, LogRocket; API contract verified against actual backend `schemas.py` |
| Architecture | HIGH | State machine and component layout from Vue 3 official docs; CORS config from FastAPI official docs; all code snippets are from official sources |
| Pitfalls | HIGH | CORS pitfalls from FastAPI discussions and open-webui issues; drag event pitfalls from MDN and Dropzone.js issue tracker; animation pitfalls from GSAP official docs and empirical memory study |

**Overall confidence:** HIGH

### Gaps to Address

- **`markdown-it` vs `vue3-markdown-it` integration:** Research identifies `markdown-it` as the correct renderer (40KB, lightweight) but does not specify the exact Vue 3 SFC integration pattern. Validate with a spike in Phase 5.
- **motion-v + TransitionGroup JavaScript hooks:** CSS-only stagger is fully documented; the hybrid approach (motion-v `useAnimate` inside `@enter`/`@leave` hooks) is not verified with a working example. If CSS approach proves insufficient, spike before Phase 6.
- **Vue Router v5 production readiness:** Research notes v5 is published but v4.6.3 is the stable alternative. Confirm v5 readiness at scaffold time (Phase 1).
- **`useDropZone` `dataTypes` filtering on Safari:** Safari reports empty MIME type list during drag; accept any drop and let backend reject with clear error message. Verify error surfacing in Phase 3.

---

## Sources

### Primary (HIGH confidence)

- [FastAPI CORS docs](https://fastapi.tiangolo.com/tutorial/cors/) — CORSMiddleware configuration, credentials/wildcard behavior
- [Vue.js Composables docs](https://vuejs.org/guide/reusability/composables) — useUpload pattern, readonly refs
- [Vue.js TransitionGroup docs](https://vuejs.org/guide/built-ins/transition-group) — stagger with CSS custom properties
- [VueUse useDropZone docs](https://vueuse.org/core/usedropzone/) — drag event API, dataTypes filtering
- [Vite docs — Server proxy](https://vite.dev/config/server-options) — dev proxy configuration
- [motion-v on npm](https://www.npmjs.com/package/motion-v) — version 2.2.1 confirmed
- [@vueuse/core on npm](https://www.npmjs.com/package/@vueuse/core) — version 14.3.0 confirmed
- [MDN — dragleave event](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/dragleave_event) — child element flickering behavior
- [MDN — AbortSignal.timeout()](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal/timeout_static) — fetch timeout pattern

### Secondary (MEDIUM confidence)

- [motion.dev/docs/vue](https://motion.dev/docs/vue) — motion-v features, stagger, drag
- [shadcn-vue GitHub](https://github.com/unovue/shadcn-vue) — component availability, dark mode
- [Tailwind CSS v4 announcement](https://tailwindcss.com/blog/tailwindcss-v4) — Vite plugin, CSS variables
- [Vite 6.0 announcement](https://vite.dev/blog/announcing-vite6) — v6 stable status
- [Frontend Memory Leaks Empirical Study — StackInsight](https://stackinsight.dev/blog/memory-leak-empirical-study/) — 819KB leak vs 2.6KB with cleanup
- [NN/G Empty States](https://www.nngroup.com/articles/empty-state-interface-design/) — idle state UX requirements
- [Smashing Magazine — Vue 3 Drag-and-Drop](https://www.smashingmagazine.com/2022/03/drag-drop-file-uploader-vuejs-3/) — drop zone implementation patterns

### Tertiary (LOW confidence)

- [Vue Router npm](https://www.npmjs.com/package/vue-router) — v5.0.7 latest; production readiness needs validation at scaffold time
- [VueUse useDropZone issue #4085](https://github.com/vueuse/vueuse/issues/4085) — API consistency note; may not reflect current v14 behavior

---

*Research completed: 2026-05-25*
*Ready for roadmap: yes*
