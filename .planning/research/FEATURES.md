# Feature Landscape — SelectionMaid v2.0 Frontend SPA

**Domain:** Internal developer tool SPA — document upload and chunk inspection UI
**Researched:** 2026-05-25
**Scope:** Vue 3 + Vite SPA consuming the existing `/ingest` API (POST multipart/form-data)
**Confidence:** HIGH (patterns verified across Postman, RapidAPI, OpenAI Playground, and multiple UX research sources)

---

## Backend API Contract (Dependency Baseline)

The frontend consumes one existing endpoint. All feature complexity must stay compatible with this contract.

```http
POST /ingest
  Content-Type: multipart/form-data
  Body: file (PDF or DOCX or HTML)

Response 200:
{
  "metadata": {
    "doc_id": str,
    "source_filename": str,
    "title": str | null,
    "language": str | null,       // ISO 639-1, e.g. "pt", "en"
    "doc_type": str | null,
    "page_count": int | null,
    "chunk_count": int,
    "ingested_at": str            // ISO 8601
  },
  "chunks": [
    {
      "chunk_id": str,
      "doc_id": str,
      "text": str,               // Markdown-formatted content
      "word_count": int,
      "chunk_index": int,
      "total_chunks": int,
      "document_type": str | null,
      "language": str | null,
      "title": str | null
    }
  ]
}

Response 4xx/5xx:
  { "detail": str }   // FastAPI error format
```

**Critical frontend implications:**

- `text` is Markdown — must be rendered, not displayed as raw string
- `chunk_count` may be 0 for empty or unparseable documents — frontend must handle
- No streaming — the response arrives in one payload after full server processing (1–30 seconds)
- File types are enforced server-side; frontend validation is advisory only

---

## Table Stakes

Features users expect in any file-upload-and-inspect developer tool. Missing any of these makes the tool feel broken or unfinished.

| Feature | Why Expected | Complexity | Backend Dependency |
| ------- | ------------ | ---------- | ------------------ |
| Drag-and-drop file drop zone | De facto standard since 2018; all modern upload UIs provide it; dashed-border drop zone is a recognized affordance | LOW | None |
| Click-to-browse fallback | Drag-and-drop alone excludes keyboard-only users and unfamiliar users; click-open is always required | LOW | None |
| Drop zone hover state (border + bg color change) | Immediate visual confirmation that the zone is active and the file will be accepted; without it users are unsure if drop worked | LOW | None |
| Client-side file type validation | Must reject non-PDF/DOCX/HTML with a clear message before making the network request; reduces wasted requests and user confusion | LOW | Enforced independently on server; client check is advisory |
| Client-side file size validation | A 50MB limit warning before upload prevents long waits followed by a confusing 413 error | LOW | None |
| Loading / processing state | Server processing takes 1–30 seconds; the UI must clearly signal "working" or users will re-submit or abandon | MEDIUM | None — triggered on POST start |
| Skeleton loader (not spinner) | Skeleton screens reduce perceived wait time by ~40% vs. spinners; they show the shape of the result before it arrives, anchoring expectations | MEDIUM | Schema known in advance — skeleton matches chunk+metadata layout |
| Error state with message | Server errors (4xx/5xx), network failures, and file rejection must show a clear human-readable message and a retry affordance | LOW | `detail` field from FastAPI error response |
| Empty state (before first upload) | The app starts in an empty state; this must feel intentional, not broken; a clear call to action ("Drop a document to begin") is required | LOW | None |
| Chunk list display | The primary result: a scrollable list of extracted chunks with their text content; this is the core deliverable of the tool | MEDIUM | `chunks[]` array |
| Markdown rendering per chunk | `text` is Markdown; rendering it (bold, headings, code, tables) is required for readability; raw Markdown strings look broken | MEDIUM | `chunk.text` is Markdown |
| Chunk index badge | Shows position (e.g. "3 / 47"); essential for orientation in a long document | LOW | `chunk_index`, `total_chunks` |
| Document metadata display | Shows `title`, `language`, `doc_type`, `chunk_count`, `page_count`, `ingested_at`; without this, users cannot verify the document was processed correctly | LOW | `metadata` object |
| Copy-to-clipboard per chunk | The #1 action after reviewing chunks: copy the text to paste into a test query or vector DB insertion script; expected in all AI tool UIs | LOW | `chunk.text` |
| Copy confirmation feedback | "Copied!" toast or icon check that appears for ~1.5s after clicking copy; without it users click repeatedly thinking it didn't work | LOW | None |
| Reset / start over action | After reviewing results, users need a one-click way to return to the upload state to process another document | LOW | Clears local state |
| Accepted formats display | The drop zone must state what file types are accepted (PDF, DOCX, HTML) so users know before attempting an upload | LOW | None |
| Responsive layout (desktop + wide screens) | Internal tools are used on developer workstations; minimum 1280px layout must not break; mobile not required | LOW | None |

---

## Differentiators

Features beyond table stakes that distinguish a "modern, animated, performant" tool from a basic form+table implementation. These are what makes the v2.0 milestone worth building.

| Feature | Value Proposition | Complexity | Notes |
| ------- | ----------------- | ---------- | ----- |
| Stagger reveal animation on chunk list | Chunks appear sequentially with a 30–60ms delay between each rather than all-at-once; makes the result feel alive and gives the eye a reading anchor; GPU-accelerated `transform: translateY` + `opacity` for 60fps | MEDIUM | Use GSAP `stagger` or Vue `<TransitionGroup>` with staggered delay; animate only `transform` and `opacity` to avoid layout reflow |
| Drop zone drag-active visual upgrade | Beyond border color change: scale the zone slightly (`transform: scale(1.02)`), increase border weight, pulse a glow; makes the interaction feel premium | LOW | Pure CSS; no JS required; `dragover` event toggles a class |
| Shimmer skeleton loading | Animate the skeleton placeholder with a sweeping shimmer rather than a static grey box; signals active loading vs. broken | LOW | Pure CSS `@keyframes` with `background-position` sweep; no library required |
| Smooth view transitions between states | Animated transition between "empty → uploading → results" app states using Vue `<Transition>` with `fade` + `slide`; prevents jarring content jumps | LOW | Vue built-in; keep duration at or below 200ms to avoid feeling slow |
| Per-chunk expand/collapse | Long chunks can be truncated to ~4 lines with a "Show more / Show less" toggle; keeps the list scannable without losing detail | LOW | Pure CSS `max-height` transition; no library |
| Word count badge per chunk | Quick visual indicator of chunk size; helps users identify outlier chunks (too long, too short) that signal chunking quality issues | LOW | `chunk.word_count` from API |
| Document summary stats bar | A sticky bar showing `chunk_count`, `language`, `doc_type`, `page_count` and inferred `title`; acts as a persistent context anchor while scrolling chunks | LOW | From `metadata` object; no extra API calls |
| Chunk text search/filter | A text input that filters the displayed chunk list in real-time; essential when processing long documents with 50+ chunks | MEDIUM | Pure client-side `computed` filter on `chunks`; no backend call |
| Dark mode only (no toggle) | The tool targets developers who prefer dark environments; committing fully to dark mode simplifies the CSS and avoids the complexity of a light/dark system while matching the aesthetic stated in PROJECT.md | LOW | Single dark color palette; no `prefers-color-scheme` toggle needed at v2.0 |
| Keyboard shortcut to open file dialog | Power-user affordance; when the drop zone is focused, Enter opens the file browser | LOW | `@keydown.enter` and `@keydown.space` on the drop zone element |
| File name and size display after selection | Show the selected file's name and size before/during upload; confirms the right file was chosen | LOW | From `File` object: `file.name`, `file.size` |
| Chunk count summary after load | Show "47 chunks extracted" prominently before the list; users immediately know if extraction succeeded or produced unexpected results | LOW | `metadata.chunk_count` |
| Animated processing indicator with elapsed time | A progress indicator that shows elapsed seconds ("Processing... 4s") during the API call; reduces anxiety during long OCR jobs | MEDIUM | `setInterval` counter + displayed elapsed time; no backend progress API needed |

---

## Anti-Features

Commonly considered features that would harm the v2.0 milestone by adding complexity, scope creep, or coupling to backend concerns.

| Anti-Feature | Why Avoid | What to Do Instead |
| ------------ | --------- | ------------------ |
| Upload progress bar (bytes) | The `/ingest` endpoint does not stream progress; an XHR `onprogress` event reflects upload transfer speed, not server processing progress — misleading for large files where processing dominates time | Show elapsed time counter instead; it is honest about what is actually happening |
| Multiple file upload queue | The API accepts one file per POST; supporting a queue would require sequential or parallel requests, result merging UI, and per-file status tracking — 3x the complexity for a tool that processes one document at a time | Single-file upload; users repeat for multiple files |
| Drag-and-drop reordering of chunks | Chunks are ordered by document position; reordering them is meaningless for a RAG inspection tool and implies write-back to the API which does not exist | Display chunks in index order; make order clear via index badges |
| Pagination of chunk list | The chunk list for a typical document is 5–200 items; pagination adds navigation overhead for a list that fits in memory and is filterable client-side | Client-side search/filter is sufficient; render all chunks into the DOM |
| History / session persistence | Storing past ingestion results in localStorage or IndexedDB adds state management complexity and privacy considerations; the tool is ephemeral by design | Each session is stateless; users re-upload if they need to revisit |
| Authentication UI | Out of scope per PROJECT.md; auth is an infrastructure concern (API gateway, reverse proxy) | Backend handles CORS; no auth UI in the SPA |
| Settings/configuration panel | No user-configurable options exist in the v1 API; adding a settings panel without backend support creates orphaned UI | If chunking params are exposed in a future milestone, add settings then |
| Syntax highlighting for Markdown code blocks | Documents processed by SelectionMaid are prose documents (PDFs, DOCX); code blocks in chunks are rare and not a primary use case; adding a syntax highlighter (Shiki, Prism) adds significant bundle weight | Render Markdown with a lightweight renderer (marked.js); add syntax highlighting only if a clear need emerges |
| Custom theming or light mode | Doubles CSS complexity; the tool's identity is dark mode minimalist as stated in PROJECT.md | Dark mode only; use CSS custom properties for the color palette so theming is easy to add later |
| Export results as CSV/JSON | Out of scope for v2.0; consumers who need structured output use the API directly | The raw API response is already JSON; document the endpoint for power users |
| WebSocket / SSE for live updates | The backend is synchronous; there is no streaming API to connect to | One-shot fetch with elapsed time counter |

---

## Feature Dependencies

```text
[Drop zone component]
    └── provides ──> [Drag-and-drop interaction]
    └── provides ──> [Click-to-browse fallback]
    └── requires ──> [Client-side validation] (before POST)
    └── triggers ──> [Upload state machine]

[Upload state machine]
    ├── idle ──────> empty state (call-to-action)
    ├── selected ──> file name + size display
    ├── uploading ──> shimmer skeleton + elapsed time counter
    ├── success ──> [Results view]
    └── error ─────> error state with retry

[Results view]
    ├── requires ──> [Document metadata display] (metadata object)
    ├── requires ──> [Chunk list] (chunks[] array)
    └── requires ──> [Reset action] (returns to idle)

[Chunk list]
    ├── requires ──> [Markdown renderer] (chunk.text is Markdown)
    ├── requires ──> [Chunk index badge] (chunk_index, total_chunks)
    ├── requires ──> [Copy-to-clipboard] (chunk.text)
    ├── provides ──> [Stagger reveal animation] (differentiator)
    ├── provides ──> [Expand/collapse per chunk] (differentiator)
    └── enhanced by ──> [Client-side text search] (differentiator)

[Document metadata display]
    ├── depends on ──> metadata.title (nullable)
    ├── depends on ──> metadata.language (nullable)
    ├── depends on ──> metadata.doc_type (nullable)
    ├── depends on ──> metadata.page_count (nullable)
    ├── depends on ──> metadata.chunk_count
    └── depends on ──> metadata.ingested_at

[Copy-to-clipboard]
    └── requires ──> [Copy confirmation feedback] (toast or icon)
```

---

## MVP Recommendation

**Build this for v2.0 launch (table stakes + highest-impact differentiators):**

1. Drop zone with drag-active state, hover glow, click-to-browse fallback, accepted formats label
2. Client-side file type and size validation with inline error message in the drop zone
3. Upload state machine: idle → uploading → success → error → idle
4. Shimmer skeleton loading state with elapsed time counter
5. Results view: document metadata summary bar + chunk list
6. Chunk list with Markdown rendering, index badge, copy-to-clipboard with confirmation
7. Stagger reveal animation on chunk list (the signature visual feature of v2.0)
8. Smooth `<Transition>` between app states (idle / loading / results / error)
9. Client-side chunk text search/filter
10. Per-chunk expand/collapse for long chunks
11. Reset button to return to upload state

**Defer to v2.1:**

- Animated processing indicator with elapsed time (replace with simpler pulse on skeleton for v2.0)
- Per-chunk word count badge (add once base UI is validated)
- Keyboard shortcut (Enter/Space on drop zone)
- Chunk count summary ("47 chunks extracted" hero stat)

---

## Complexity Summary

| Area | Estimated Complexity | Key Risk |
| ---- | -------------------- | -------- |
| Drop zone + drag-and-drop | LOW | None; `useDropZone` (VueUse) handles browser API surface |
| State machine (idle/uploading/success/error) | LOW | State explosion if done without explicit state enum |
| Skeleton shimmer (CSS) | LOW | None; pure CSS `@keyframes` |
| Markdown rendering | LOW–MEDIUM | Bundle size: `marked` is 40KB; `markdown-it` is 60KB; avoid full MDX parsers |
| Stagger animation | MEDIUM | Must animate `transform` and `opacity` only; avoid animating `height` or `width` on list items |
| `<Transition>` between app states | LOW | Keep duration at or below 200ms; avoid conflicting transitions |
| Copy-to-clipboard | LOW | `navigator.clipboard.writeText` async API; VueUse `useClipboard` handles fallbacks |
| Client-side search/filter | LOW | `computed` on reactive `chunks` ref; no debounce needed at fewer than 500 chunks |
| Elapsed time counter | LOW | `setInterval` in `onMounted`; clear in `onUnmounted` |

---

## Sources

- [Building a Modern Drag-and-Drop Upload UI in 2025 — Filestack Blog](https://blog.filestack.com/building-modern-drag-and-drop-upload-ui/)
- [UX Best Practices for File Uploader — Uploadcare](https://uploadcare.com/blog/file-uploader-ux-best-practices/)
- [Drag-and-Drop UX Guidelines — Smart Interface Design Patterns](https://smart-interface-design-patterns.com/articles/drag-and-drop-ux/)
- [Designing Drag-and-Drop UIs: Best Practices — LogRocket](https://blog.logrocket.com/ux-design/drag-and-drop-ui-examples/)
- [File Upload UI Tips — Eleken](https://www.eleken.co/blog-posts/file-upload-ui)
- [Empty States Loading States Error States — Vibe Coder Blog](https://blog.vibecoder.me/empty-states-loading-states-error-states)
- [UI Best Practices: Loading, Error, Empty States — LogRocket](https://blog.logrocket.com/ui-design-best-practices-loading-error-empty-state-react/)
- [Empty States Pattern — NN/G Nielsen Norman Group](https://www.nngroup.com/articles/empty-state-interface-design/)
- [12 UI/UX Design Trends for AI Apps in 2026 — Groovy Web](https://www.groovyweb.co/blog/ui-ux-design-trends-ai-apps-2026)
- [AI UX Playground: Real-World AI Interface Design Patterns — Fountn](https://fountn.design/resource/ai-ux-playground-real-world-ai-interface-design-patterns/)
- [Postman Response Data Docs](https://learning.postman.com/docs/sending-requests/response-data/responses)
- [RapidAPI Response Docs](https://docs.rapidapi.com/docs/response)
- [How To Make A Drag-and-Drop File Uploader With Vue.js 3 — Smashing Magazine](https://www.smashingmagazine.com/2022/03/drag-drop-file-uploader-vuejs-3/)
- [Customized Drag-and-Drop File Uploading with Vue — LogRocket](https://blog.logrocket.com/customizing-drag-drop-file-uploading-vue/)
- [useDropZone — VueUse Official Docs](https://vueuse.org/core/usedropzone/)
- [Modern Web Animations with GSAP and Vue 3 — OpenReplay](https://blog.openreplay.com/modern-web-animations-with-gsap-and-vue-3/)
- [GSAP vs CSS Animations — GSAP Vault](https://gsapvault.com/blog/gsap-vs-css-animations)
- [Optimizing Animation Performance in GSAP — Rustcode](https://www.rustcodeweb.com/2024/04/optimizing-animation-performance-in-gsap.html)
- [Shadcn Vue Dark Mode — shadcn-vue.com](https://www.shadcn-vue.com/docs/dark-mode)
- [Why Use Shadcn Vue — Vue School](https://vueschool.io/articles/vuejs-tutorials/why-use-shadcn-vue-key-advantages-for-your-next-project/)
- [Enhance Markdown Code Blocks With Copy To Clipboard — SplitReq](https://splitreq.com/blog/enhance-markdown-code-blocks-with)

---

*Feature research for: SelectionMaid v2.0 — Vue 3 SPA frontend*
*Researched: 2026-05-25*
