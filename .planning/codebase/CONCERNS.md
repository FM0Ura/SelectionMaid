# Codebase Concerns

**Analysis Date:** 2026-05-27

## Tech Debt

**Upload size validation only trusts `Content-Length`:**
- Issue: `POST /ingest` rejects requests when `Content-Length` exceeds `HttpConfig.max_file_bytes`, but it does not enforce an actual byte counter while streaming the uploaded file. If the header is absent or malformed, the route continues and writes the full upload to disk. The implementation also reads the full accepted file into memory before writing it despite the chunking comment.
- Files: `src/selection_maid/adapters/http/router.py:157`, `src/selection_maid/adapters/http/router.py:221`, `src/selection_maid/adapters/http/router.py:223`, `src/selection_maid/config.py:123`
- Impact: Oversized requests can consume memory and disk before rejection, and the code contradicts its own "Read the file in chunks" comment.
- Fix approach: Stream `UploadFile.read(chunk_size)` into the tempfile, accumulate actual bytes, abort with `UPLOAD-001` once the counter exceeds `http_cfg.max_file_bytes`, and delete the partial tempfile in `finally`.

**Frontend and backend size limits are duplicated:**
- Issue: The client hardcodes `MAX_FILE_BYTES = 50 * 1024 * 1024` while the backend hardcodes `HttpConfig.max_file_bytes = 52_428_800`. They currently match numerically, but there is no shared contract. The backend checks multipart `Content-Length`, not raw file size, so a browser file at exactly the frontend limit can exceed the backend limit after multipart overhead.
- Files: `frontend/src/lib/validators.ts:1`, `src/selection_maid/config.py:123`, `src/selection_maid/adapters/http/router.py:157`
- Impact: Users can pass client validation and still receive backend `413` for boundary-size uploads.
- Fix approach: Expose upload constraints from the backend through a small config endpoint or generated shared constants, and make backend enforcement distinguish raw file bytes from multipart envelope bytes.

**Docling adapter serializes all extraction work:**
- Issue: `DoclingAdapter.extract()` holds a single `threading.Lock` around conversion, markdown export, backend unload, and `gc.collect()`.
- Files: `src/selection_maid/adapters/extractor/docling.py:86`, `src/selection_maid/adapters/extractor/docling.py:118`, `src/selection_maid/adapters/extractor/docling.py:155`
- Impact: HTTP requests can enter the FastAPI threadpool concurrently, but real Docling conversion throughput is one document at a time per process.
- Fix approach: Treat one-process throughput as intentionally single-lane unless Docling converter pooling is added. If concurrency is needed, introduce a bounded converter pool, a queue, explicit overload responses, and stress tests that measure wall-clock behavior.

**FastAPI app runtime wiring differs from integration test wiring:**
- Issue: Production startup builds a default `DocumentConverter()` while integration tests configure `DocumentConverter` with explicit allowed formats and PDF pipeline options.
- Files: `src/selection_maid/adapters/http/app.py:59`, `src/selection_maid/adapters/http/app.py:61`, `tests/adapters/http/test_integration.py:91`, `tests/adapters/http/test_integration.py:101`
- Impact: Integration tests may not exercise the same Docling capabilities, OCR/table settings, memory behavior, or failure modes used by the deployed app.
- Fix approach: Move converter construction into a shared factory such as `src/selection_maid/adapters/extractor/factory.py` and use it from both `app.py` and integration fixtures.

**Production settings are still hardcoded for local development:**
- Issue: CORS allows only `http://localhost:5173` and `allow_credentials=True`; no deployment host, origin list, or proxy mode is configurable.
- Files: `src/selection_maid/adapters/http/app.py:112`, `src/selection_maid/adapters/http/app.py:114`, `src/selection_maid/adapters/http/app.py:117`, `docs/CONFIGURATION.md:159`
- Impact: Production deployment requires code edits or reverse-proxy assumptions outside the app contract.
- Fix approach: Add CORS settings to `GlobalConfig`, validate configured origins on startup, and document production same-origin and cross-origin modes.

**Vite starter component remains in source tree:**
- Issue: `HelloWorld.vue` still contains Vite/Vue starter UI, social links, and a counter, and starter assets remain tracked.
- Files: `frontend/src/components/HelloWorld.vue:1`, `frontend/src/components/HelloWorld.vue:18`, `frontend/src/components/HelloWorld.vue:37`, `frontend/src/assets/vite.svg`, `frontend/src/assets/vue.svg`
- Impact: Future frontend work can accidentally import or preserve starter UX artifacts that do not belong to SelectionMaid.
- Fix approach: Delete `frontend/src/components/HelloWorld.vue`, `frontend/src/assets/vite.svg`, and `frontend/src/assets/vue.svg` if no imports remain.

## Known Bugs

**Accepted 50 MB frontend upload can be rejected by backend:**
- Symptoms: A browser-selected file with `file.size === 50 * 1024 * 1024` passes `validateFile()` but the multipart request `Content-Length` can exceed `52_428_800` bytes and return `UPLOAD-001`.
- Files: `frontend/src/lib/validators.ts:9`, `src/selection_maid/adapters/http/router.py:158`, `src/selection_maid/adapters/http/router.py:164`
- Trigger: Upload a file exactly at the client-side limit through the SPA.
- Workaround: Keep files below the advertised limit until backend enforcement is changed to count raw file bytes.

**Password-protected PDFs return a generic 500:**
- Symptoms: Integration tests codify password-protected PDFs as HTTP 500 with `EXT-001` rather than a user-actionable unsupported/encrypted-document error.
- Files: `tests/adapters/http/test_integration.py:267`, `tests/adapters/http/test_integration.py:282`, `src/selection_maid/adapters/http/error_map.py`, `src/selection_maid/errors.py`
- Trigger: Upload `tests/fixtures/adversarial/protected.pdf` as `application/pdf`.
- Workaround: None in the API; clients receive a generic extraction failure.

**Unexpected server exceptions are exposed to clients:**
- Symptoms: The catch-all handler includes `str(exc)` in the response body.
- Files: `src/selection_maid/adapters/http/router.py:241`, `src/selection_maid/adapters/http/router.py:243`
- Trigger: Any non-domain exception during tempfile writing, service processing, or response serialization.
- Workaround: Domain adapters should wrap expected failures in `SelectionMaidError`, but unexpected exception text can still leak.

## Security Considerations

**Rendered markdown uses `v-html`:**
- Risk: Extracted document content is converted to HTML and injected with `v-html`. The current path disables raw markdown HTML and sanitizes with DOMPurify, but this remains a high-sensitivity boundary because uploaded documents are untrusted input.
- Files: `frontend/src/components/result/MarkdownRenderer.vue:14`, `frontend/src/components/result/MarkdownRenderer.vue:38`, `frontend/src/components/result/MarkdownRenderer.vue:46`
- Current mitigation: `MarkdownIt({ html: false })`, `DOMPurify.sanitize(...)`, and link `rel="noopener noreferrer"` are present.
- Recommendations: Keep all future markdown extensions behind tests for XSS payloads, avoid enabling raw HTML, and add regression tests for links, images, code blocks, and dangerous URL schemes.

**File validation relies on first 2048 bytes and declared MIME matching:**
- Risk: Magic-byte validation rejects simple spoofing, but complex polyglot or parser exploit files can still pass and be sent to Docling.
- Files: `src/selection_maid/adapters/http/router.py:38`, `src/selection_maid/adapters/http/router.py:181`, `src/selection_maid/adapters/http/router.py:193`
- Current mitigation: Declared MIME allowlist, libmagic detection, and tempfiles with restricted permissions.
- Recommendations: Keep Docling isolated from the request process when threat model increases; add malware scanning or sandboxed worker execution for production untrusted uploads.

**Server-side error details can disclose internals:**
- Risk: Catch-all API errors expose exception messages to the caller.
- Files: `src/selection_maid/adapters/http/router.py:241`, `src/selection_maid/adapters/http/router.py:243`
- Current mitigation: Expected domain errors use structured `SelectionMaidError` codes.
- Recommendations: Return a generic public message for unexpected exceptions, log the full exception server-side, and add tests asserting no raw exception text in 500 responses.

## Performance Bottlenecks

**Large uploads are buffered in memory before tempfile write:**
- Problem: The route reads the full upload into `content_bytes` before `tmp.write(...)`.
- Files: `src/selection_maid/adapters/http/router.py:221`, `src/selection_maid/adapters/http/router.py:223`, `tests/adapters/http/test_integration.py:334`
- Cause: `UploadFile.read()` is called without a size after validation.
- Improvement path: Stream chunks directly from `UploadFile` to the tempfile and enforce raw byte limits during the stream.

**Docling conversion is CPU/memory heavy and intentionally serialized:**
- Problem: A request can take 10-30 seconds for real Docling conversion, and memory warm-up can add about 1 GB RSS before baseline measurements.
- Files: `src/selection_maid/adapters/extractor/docling.py:118`, `tests/test_memory_regression.py:8`, `tests/test_memory_regression.py:11`, `tests/adapters/http/test_integration.py:410`
- Cause: Docling model loading, conversion cost, a single converter lock, per-extraction `ThreadPoolExecutor`, and `gc.collect()` after every extraction.
- Improvement path: Add queue metrics, request concurrency limits, and process-level horizontal scaling before increasing in-process parallelism.

**Health endpoint computes process RSS on every call:**
- Problem: `/health` instantiates `psutil.Process()` and reads memory info per request.
- Files: `src/selection_maid/adapters/http/router.py:101`, `src/selection_maid/adapters/http/router.py:102`
- Cause: Health responses include `rss_mb`.
- Improvement path: Keep as-is for low traffic; if health checks are frequent, split `/health` liveness from `/metrics` diagnostics or cache RSS briefly.

## Fragile Areas

**Docling timeout cannot cancel the underlying conversion cleanly:**
- Files: `src/selection_maid/adapters/extractor/docling.py:124`, `src/selection_maid/adapters/extractor/docling.py:127`, `src/selection_maid/adapters/extractor/docling.py:130`
- Why fragile: `future.result(timeout=...)` raises `ExtractionTimeoutError`, but the converter work already submitted to a thread is not forcibly killed. The code comments acknowledge lingering-thread tradeoffs.
- Safe modification: Prefer worker process isolation for hard cancellation; keep timeout tests around both fast fake converters and real slow fixtures.
- Test coverage: Unit timeout tests exist in `tests/adapters/extractor/test_docling_adapter.py`; production-grade cancellation is not covered.

**HTTP router mixes validation, tempfile I/O, service dispatch, and error mapping:**
- Files: `src/selection_maid/adapters/http/router.py:130`, `src/selection_maid/adapters/http/router.py:157`, `src/selection_maid/adapters/http/router.py:180`, `src/selection_maid/adapters/http/router.py:217`, `src/selection_maid/adapters/http/router.py:238`
- Why fragile: `ingest()` owns several concerns in one function, so upload hardening changes can unintentionally alter API error semantics or cleanup behavior.
- Safe modification: Extract private helpers for content-length parsing, MIME validation, magic validation, bounded tempfile streaming, and error response construction.
- Test coverage: `tests/adapters/http/test_router.py` is broad, but add explicit tests for missing/malformed `Content-Length` and actual byte-limit enforcement.

**Integration fixtures are generated opportunistically:**
- Files: `tests/adapters/http/test_integration.py:52`, `tests/adapters/http/test_integration.py:71`, `tests/adapters/http/test_integration.py:76`, `tests/fixtures/generate_adversarial.py`
- Why fragile: Fixture generation failure is non-fatal, so some reliability checks silently skip when generated files are missing.
- Safe modification: Keep fast unit tests independent, but make CI integration jobs fail clearly when required adversarial fixtures cannot be generated.
- Test coverage: Integration tests use skip behavior rather than mandatory fixture availability.

## Scaling Limits

**Single-process extraction capacity:**
- Current capacity: One real Docling conversion at a time per process because of the adapter lock.
- Limit: Concurrent HTTP requests queue behind `DoclingAdapter._lock`; long documents can push perceived latency above frontend timeout.
- Scaling path: Run multiple worker processes or container replicas, then introduce backpressure and queue depth metrics.

**Frontend timeout is fixed at 130 seconds:**
- Current capacity: The SPA aborts `/api/ingest` after `130000` ms.
- Limit: Backend Docling timeout is 120 seconds, but queueing behind the single converter lock can consume most of the client timeout before conversion starts.
- Scaling path: Return a job ID for long-running processing, or reject when the extraction queue is full instead of letting clients wait.
- Files: `frontend/src/api/ingest.ts:19`, `src/selection_maid/adapters/extractor/docling.py:74`, `src/selection_maid/adapters/extractor/docling.py:127`

**Large document memory budget:**
- Current capacity: Tests exercise a generated `large_sample.pdf` above 40 MB and below 50 MB.
- Limit: The route buffers the upload, Docling loads models, and conversion can add large temporary allocations in one process.
- Scaling path: Stream uploads, isolate conversion in workers, and add memory/timeout limits around workers.
- Files: `tests/adapters/http/test_integration.py:334`, `tests/adapters/http/test_integration.py:348`, `src/selection_maid/adapters/http/router.py:223`

## Dependencies at Risk

**Docling / PyTorch runtime footprint:**
- Risk: `docling>=2.95.0` brings heavy model loading and PyTorch CPU wheels.
- Impact: Startup latency, memory footprint, and package resolution are materially affected by Docling and torch.
- Migration plan: Keep Docling isolated behind `ExtractorPort`; evaluate process isolation before replacing the extractor implementation.
- Files: `pyproject.toml:8`, `pyproject.toml:63`, `src/selection_maid/domain/ports.py`, `src/selection_maid/adapters/extractor/docling.py`

**Unbounded dependency ranges for backend runtime packages:**
- Risk: Runtime dependencies use lower bounds only.
- Impact: Future incompatible releases can enter installs without code changes.
- Migration plan: Keep `uv.lock` committed and used for deployment; consider upper bounds for high-risk runtime packages such as `docling`, `fastapi`, and `tiktoken`.
- Files: `pyproject.toml:7`, `pyproject.toml:16`, `uv.lock`

**Frontend dependency and TypeScript version skew:**
- Risk: Vite/Vitest/Vue tooling is versioned with broad caret ranges while TypeScript is pinned to `~5.5.0`.
- Impact: Tooling upgrades can change build/test behavior independently of TypeScript.
- Migration plan: Use `frontend/package-lock.json` for reproducible installs and update build tooling in grouped upgrade phases.
- Files: `frontend/package.json:11`, `frontend/package.json:32`, `frontend/package.json:33`, `frontend/package-lock.json`

## Missing Critical Features

**No asynchronous job API for long-running extraction:**
- Problem: The API is synchronous: one multipart request waits for all extraction, filtering, chunking, and enrichment.
- Blocks: Large-document UX, reliable progress reporting, retry/resume behavior, and clean queue backpressure.
- Files: `src/selection_maid/adapters/http/router.py:130`, `frontend/src/composables/useUpload.ts:50`, `frontend/src/api/ingest.ts:11`

**No production observability beyond logs and `/health`:**
- Problem: There are no request metrics, queue metrics, extraction duration histograms, or structured tracing.
- Blocks: Capacity planning and diagnosis for slow Docling conversions or memory growth.
- Files: `src/selection_maid/adapters/http/router.py:99`, `src/selection_maid/adapters/http/app.py:54`, `src/selection_maid/adapters/http/app.py:84`

**No frontend E2E/browser workflow tests:**
- Problem: Unit tests cover components and composables, but no Playwright/Cypress-style browser tests exercise drag-and-drop upload through result rendering.
- Blocks: Confidence in integrated SPA behavior, visual regressions, and browser-only file handling.
- Files: `frontend/package.json:6`, `frontend/package.json:10`, `frontend/src/App.spec.ts`, `frontend/src/components/upload/__tests__/DropZone.spec.ts`

## Test Coverage Gaps

**Actual upload byte limit enforcement:**
- What's not tested: Missing or malformed `Content-Length` with an actual body over `max_file_bytes`; exact frontend limit plus multipart overhead.
- Files: `tests/adapters/http/test_router.py:120`, `src/selection_maid/adapters/http/router.py:157`, `frontend/src/lib/validators.spec.ts`
- Risk: Oversized uploads can bypass intended validation or valid user files can be rejected.
- Priority: High

**Unexpected 500 response redaction:**
- What's not tested: Public 500 bodies do not leak raw exception text.
- Files: `tests/adapters/http/test_router.py:385`, `src/selection_maid/adapters/http/router.py:241`
- Risk: Internal exception details can be exposed to clients.
- Priority: High

**Markdown rendering XSS regression matrix:**
- What's not tested: Dangerous URL schemes, image/link payloads, nested HTML-like markdown, syntax-highlighted code, and sanitizer behavior together.
- Files: `frontend/src/components/result/MarkdownRenderer.spec.ts`, `frontend/src/components/result/MarkdownRenderer.vue:38`, `frontend/src/components/result/MarkdownRenderer.vue:46`
- Risk: Future markdown plugin or sanitizer changes can introduce XSS.
- Priority: High

**Production app converter parity:**
- What's not tested: `create_app()` with production converter construction and the same options used by integration tests.
- Files: `src/selection_maid/adapters/http/app.py:61`, `tests/adapters/http/test_integration.py:91`
- Risk: Tests pass against a converter configuration that differs from deployed behavior.
- Priority: Medium

**Slow and integration tests can skip critical paths:**
- What's not tested: CI-enforced memory and adversarial-document behavior when fixtures or network-dependent resources are unavailable.
- Files: `tests/test_memory_regression.py:83`, `tests/adapters/http/test_integration.py:76`, `tests/adapters/http/test_integration.py:343`
- Risk: Memory regressions and adversarial-input failures can be missed in routine verification.
- Priority: Medium

---

*Concerns audit: 2026-05-27*
