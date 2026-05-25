# Pitfalls Research

**Domain:** Document extraction and RAG ingestion pipeline (Docling + FastAPI + Hexagonal Architecture)
**Researched:** 2026-05-23
**Confidence:** HIGH (multiple independent sources, official GitHub issues, official documentation)

---

## Critical Pitfalls

### Pitfall 1: Docling Memory Leak on Repeated Conversions

**What goes wrong:**
`DoclingParseV2DocumentBackend` (the default PDF backend) accumulates memory on repeated conversions and never releases it. In a long-running service that processes multiple documents, this grows to 10–13GB RAM consumed within minutes, triggering OOM kills. The problem is compounded by three independent leak sources: the parse backend itself, formula enrichment (causes 100% memory usage when enabled), and EasyOCR reader.

**Why it happens:**
Docling loads heavy model weights (ML models for table detection, layout analysis, OCR) into C-extension memory pools that Python's garbage collector cannot observe or reclaim. The `DocumentConverter` instance holds references to these pools for its entire lifetime. Calling `del converter` or `gc.collect()` does not reliably free the underlying memory.

**How to avoid:**
- Instantiate `DocumentConverter` once at startup (not per-request) but monitor RSS memory.
- If the service must process many documents in a single process lifetime, implement a "converter refresh" strategy: periodically recreate the converter instance (e.g., every N conversions) and call `gc.collect()` explicitly.
- For production workloads, isolate Docling extraction inside a subprocess or worker process with a bounded lifetime, so the OS reclaims memory on subprocess exit. The hexagonal `ExtractorPort` boundary makes this swap transparent.
- Disable pipeline features you do not need: `do_table_structure=False`, `do_formula_enrichment=False`, `generate_picture_images=False` — each reduces memory footprint.
- Pin Docling version and re-test memory after upgrades; this bug has had regressions across versions.

**Warning signs:**
- RSS memory of the process growing monotonically across requests while CPU is idle.
- OOM kills in container environments.
- Prometheus/system metrics showing heap never shrinking between requests.

**Phase to address:** Architecture foundation phase (when `ExtractorPort` adapter is first implemented). The adapter boundary must be designed to allow process-isolation as a drop-in change, not retrofitted later.

---

### Pitfall 2: Docling Extreme Slowness on Image-Heavy PDFs

**What goes wrong:**
Docling is 30–80x slower than PyMuPDF when processing PDFs that are primarily scanned images. A 12MB scanned PDF can take 30 minutes. Even modest 50-page image PDFs take 65+ seconds. This is not a bug — it is the expected cost of running neural layout analysis and OCR on every page image.

**Why it happens:**
For digital PDFs (text layer present), Docling reads text coordinates directly. For image-based pages, it runs: (1) page rasterization, (2) layout detection (DLA model), (3) OCR (EasyOCR or Tesseract), (4) table structure recognition, (5) optionally formula/picture enrichment. Each step is sequential and CPU-bound by default. Without GPU, this is the bottleneck.

**How to avoid:**
- Detect whether a PDF has a text layer before sending to the full pipeline. Use a lightweight pre-check (e.g., `pdfminer` or `pypdfium2` zero-cost text extraction) and skip OCR if text is already present.
- Expose pipeline configuration through the `ExtractorPort` interface: callers can specify `ocr=False` for digital documents, dramatically reducing processing time.
- Set a hard timeout on the extractor adapter (e.g., 120 seconds) and return a structured error rather than hanging indefinitely. Docling is documented to hang indefinitely on some PDFs.
- For image-only documents, document the performance expectation explicitly in API responses (e.g., an `estimated_seconds` field based on page count and image ratio).

**Warning signs:**
- P95 latency spiking far above P50 — almost always caused by image-heavy documents hitting the OCR path.
- Request timeouts on documents that look small by file size but contain many pages of scanned images.
- `identify -verbose` or `pdfinfo` showing page images at high resolution without embedded text.

**Phase to address:** PDF extraction phase. Pipeline options must be configurable at the adapter level, not hardcoded. Timeout enforcement is mandatory from day one.

---

### Pitfall 3: Docling Library Types Leaking into the Domain

**What goes wrong:**
`DoclingDocument`, `TableItem`, `TextItem`, `ConversionResult` — Docling's rich internal types — leak out of the `ExtractorAdapter` into the domain service or into `Port` return types. Now the domain depends on `docling` as a transitive import. Swapping Docling for another library (pypdfium2, unstructured, LlamaParse) requires changing the domain service, not just the adapter.

**Why it happens:**
Docling's output types are convenient and feature-rich. Developers take the path of least resistance by returning `ConversionResult` directly from the adapter, then accessing `.document.export_to_markdown()` in the service layer. This is a natural shortcut that violates the port contract.

**How to avoid:**
- Define domain-native types for all port return values: `ExtractedDocument(text: str, markdown: str, pages: list[PageInfo], format: DocumentFormat)`. These are plain dataclasses with no library imports.
- The `ExtractorPort` protocol must use only domain types in its signature. If the type cannot be expressed without importing Docling, the boundary is violated.
- Apply the same discipline to `FilterPort`, `ChunkerPort`: their input/output types live in `domain/models.py`, never in adapter modules.
- Review imports: if `docling` appears anywhere outside `adapters/docling_extractor.py`, it is a boundary violation.

**Warning signs:**
- `from docling.datamodel import ...` appearing in `services/`, `domain/`, or `ports/` modules.
- Port method signatures with `Any` type hints (a sign the developer gave up on clean types).
- Tests of the domain service that require Docling to be installed to run.

**Phase to address:** Architecture foundation phase. The type boundary must be established before any implementation begins; retrofitting it after the fact requires touching every layer.

---

### Pitfall 4: Anemic Ports That Mirror Library APIs

**What goes wrong:**
A port is defined as a one-to-one copy of the library's public API — for example, `ExtractorPort.convert(path: str) -> ConversionResult` where `ConversionResult` is Docling's type. The port is nominally present but provides zero abstraction. Replacing the library still requires changing every caller.

**Why it happens:**
Developers write the adapter first, then extract the interface mechanically from what they built. The result is an interface shaped by the implementation, not by the domain's needs.

**How to avoid:**
- Define ports from the domain's perspective, not the library's: "What does the domain need from extraction?" — not "What does Docling offer?"
- The domain needs: `extract(source: DocumentSource) -> ExtractedDocument`. It does not need table cell coordinates, PDF bounding boxes, or Docling pipeline options.
- Resist adding library-specific configuration to port signatures. Configuration belongs in the adapter constructor or an `AdapterConfig` type, not in the port method.

**Warning signs:**
- Port method has more than 3–4 parameters.
- Port method parameter names match library function parameter names exactly.
- Changing Docling version requires changing the port interface.

**Phase to address:** Architecture foundation phase. Ports are a design artifact before implementation begins.

---

### Pitfall 5: FastAPI UploadFile Blocking the Event Loop

**What goes wrong:**
Docling extraction is CPU-bound and synchronous. If called directly inside an `async def` FastAPI route handler, it blocks the entire event loop for the duration of extraction (potentially 30+ seconds for image-heavy PDFs). All other requests queue behind it, causing cascading timeouts under any concurrent load.

**Why it happens:**
FastAPI's async machinery gives a false sense of concurrency. Developers assume `async def` endpoints handle blocking operations correctly — they do not. Asyncio is single-threaded; one blocking call pauses all coroutines.

**How to avoid:**
- Run Docling extraction inside `asyncio.get_event_loop().run_in_executor(None, extractor.extract, source)` or use `starlette.concurrency.run_in_threadpool(extractor.extract, source)`.
- Define the `InputAdapter` (FastAPI) as responsible for executor dispatch — the domain service should not know it is running async.
- For large file reads, do not use `await file.read()` to load the entire file into memory. Use `UploadFile.read(chunk_size)` in a loop or write to a `NamedTemporaryFile` first.
- Set an explicit `uvicorn` `--timeout-keep-alive` and configure a request timeout middleware to prevent indefinitely hung connections from exhausting workers.

**Warning signs:**
- All API requests slow down when one large PDF is being processed.
- `uvicorn` worker shows 100% CPU on a single core during extraction.
- `asyncio` debug mode reporting coroutines blocked for >100ms.

**Phase to address:** FastAPI adapter phase. The executor pattern must be built into the adapter from the start, not added when performance issues are observed in production.

---

### Pitfall 6: Chunks Losing Document Metadata

**What goes wrong:**
The chunker produces `Chunk(text=..., index=N)` but does not propagate document-level metadata: source file name, document format, inferred author, language, page range, section heading, extraction timestamp. The consumer receives chunks with no provenance. Retrieval returns results the consumer cannot attribute to a source document, cannot filter by date, and cannot surface to end users.

**Why it happens:**
Chunking is often implemented as a text-splitting problem ("split on N tokens"), with metadata treated as an afterthought. The chunk data model is defined before the metadata schema is finalized, and propagation is never added.

**How to avoid:**
- Define `Chunk` with mandatory metadata fields from day one: `source_id`, `source_filename`, `document_format`, `page_start`, `page_end`, `section_heading`, `chunk_index`, `total_chunks`, `language`, `extracted_at`.
- `ChunkerPort.chunk(document: ExtractedDocument) -> list[Chunk]` receives the full `ExtractedDocument` (which carries all metadata), so the chunker has everything needed to populate each chunk.
- Make `source_id` and `source_filename` non-optional fields in the `Chunk` dataclass — a missing value must be a type error, not a runtime `None`.
- Test: serialize a `Chunk` to JSON and verify every metadata field is present and correctly typed before shipping.

**Warning signs:**
- `Chunk.metadata` is a `dict[str, Any]` instead of a typed dataclass — a sign it was added informally.
- Chunk unit tests only assert on `text` content, not metadata fields.
- The consumer (vector DB integration) has to re-read the original file to get the source name.

**Phase to address:** Chunking phase, but the `Chunk` domain model must be designed in the architecture foundation phase so all upstream components know what to populate.

---

### Pitfall 7: Wrong Chunk Size for the Target Embedding Model

**What goes wrong:**
Chunks are sized arbitrarily (e.g., 1000 characters) without considering the token limit and optimal input length of the embedding model the consumer will use. Chunks larger than the model's context window are silently truncated by most embedding APIs, losing the end of the chunk. Chunks smaller than ~150 tokens produce embeddings with too little semantic content to retrieve reliably.

**Why it happens:**
Chunk size is treated as a tuning knob to add later, but it is baked into the output schema. The consuming system that owns the vector DB integration often has different assumptions about what "a good chunk" looks like.

**How to avoid:**
- Document the chunking strategy explicitly: default chunk size target (tokens, not characters), overlap size, minimum chunk floor, and maximum chunk ceiling.
- Expose chunk size as a configurable parameter in the API request, not hardcoded in the chunker. Different document types (legal contracts, technical specs, news articles) have different optimal sizes.
- Enforce a hard maximum (e.g., 512 tokens for `text-embedding-3-small`, 8192 for `text-embedding-3-large`) and a hard minimum (e.g., 100 tokens) at the `ChunkerPort` level.
- Include `token_count` in the `Chunk` output so the consumer can verify without re-tokenizing.

**Warning signs:**
- Chunk size defined in characters, not tokens.
- No overlap between adjacent chunks (context at boundaries is lost).
- No minimum chunk size check (produces single-sentence stub chunks at document end).

**Phase to address:** Chunking phase. Chunk size defaults and limits must be established as policy, not left as implementation details.

---

### Pitfall 8: Not Testing with Real Documents

**What goes wrong:**
The test suite runs entirely against synthetic or minimal fixture PDFs ("hello world" one-pagers). Real production documents — multi-column academic papers, government forms, scanned contracts, tables spanning multiple pages, Arabic/Chinese/mixed-language content — expose failures that synthetic tests never see. The service passes CI and fails immediately in production.

**Why it happens:**
Real documents require effort to collect and store in version control. Developers default to generating minimal fixtures programmatically. Over-mocking the `ExtractorPort` in service tests means Docling itself is never exercised.

**How to avoid:**
- Maintain a `tests/fixtures/` directory with a diverse set of real-world documents: digital PDF, scanned PDF, DOCX with tables, HTML page, password-protected PDF, empty PDF, zero-byte file, corrupted PDF, non-Latin script document (Arabic or Chinese).
- Write at least one integration test per document type that runs the full `ExtractorAdapter` (not a mock) against the real fixture.
- Include explicit test cases for failure modes: password-protected → `ExtractionError.PASSWORD_PROTECTED`; corrupted → `ExtractionError.CORRUPTED`; empty → `ExtractionError.EMPTY_DOCUMENT`; zero-byte → `ExtractionError.INVALID_FORMAT`.
- Mark integration tests with a pytest marker (`@pytest.mark.integration`) so they can run in CI without blocking fast unit test feedback.

**Warning signs:**
- All PDF fixtures are generated by `fpdf` or similar in `conftest.py`.
- `ExtractorPort` is always mocked in service tests — the real adapter has no tests.
- Test suite has no fixtures for edge cases (password, corrupted, empty).

**Phase to address:** Architecture foundation phase (define the error taxonomy and fixture strategy). Each subsequent phase adds fixture coverage for the features it introduces.

---

### Pitfall 9: Scope Creep via "Small" Infrastructure Additions

**What goes wrong:**
Features that appear adjacent to the core mission expand into large independent systems: adding a vector DB client ("it's just an insert"), adding Celery workers ("just for async"), adding auth middleware ("just JWT validation"), adding a document storage layer ("just S3"), adding a job status polling endpoint ("just one more route"). Each individually seems small; together they triple the codebase and the operational surface area.

**Why it happens:**
The service solves a clear problem (extract + chunk) but sits at the boundary between raw files and a vector pipeline, making it a natural aggregation point. Consumers ask for conveniences that are "almost" in scope. The hexagonal structure makes adding adapters feel cheap — until there are ten adapters.

**How to avoid:**
- The explicit out-of-scope list in `PROJECT.md` is a commitment, not a suggestion: no vector DB insertion, no auth, no async queues, no storage. Enforce this at PR review.
- When a consumer requests an in-scope-looking feature, validate against the core value statement: "Documents enter, normalized chunks exit via a stable interface." If the feature is not on that critical path, it belongs in the consumer's system.
- Use `# SCOPE: explicitly out of scope — see PROJECT.md` comments in code near natural extension points (e.g., near where chunks are returned) to surface the decision.

**Warning signs:**
- A PR adds a new dependency not in the original stack (boto3, celery, redis, sqlalchemy, authlib).
- A route is added that does not directly serve the `extract → filter → chunk → return` flow.
- The service starts maintaining state between requests (job IDs, upload history).

**Phase to address:** Every phase. Scope discipline is a recurring review, not a one-time decision.

---

### Pitfall 10: Metadata Inference Treated as Reliable

**What goes wrong:**
Author, date, title, and language inferred from PDF metadata fields are presented to consumers as ground truth. In practice: PDF metadata is frequently absent, incorrect, auto-populated by the PDF generator with placeholder values ("Author: Microsoft Word"), or encoded in non-UTF-8 encoding that causes garbled output. Language detection on short documents or mixed-language documents is unreliable.

**Why it happens:**
Docling and similar libraries surface metadata fields from the PDF spec. Developers expose them without accounting for their unreliability, and consumers build filtering logic on fields that are often wrong.

**How to avoid:**
- Return metadata with a `confidence` or `source` field: `{"author": "John Smith", "author_source": "pdf_metadata"}` vs. `{"author": "John Smith", "author_source": "inferred_from_content"}` vs. `{"author": null, "author_source": "unavailable"}`.
- Never return encoding-failed strings: validate all string metadata fields as valid UTF-8 before including them in the response. Replace invalid sequences with `None` and log the encoding error.
- Language detection: use `langdetect` or `langid` as a secondary check on the extracted text, not only on the PDF metadata field `lang`. Treat language as `Optional[str]` and document its unreliability.
- Date inference from filenames or content is LOW confidence and should be flagged as such in the output schema.

**Warning signs:**
- `author` field returns `"Administrator"` or `"Unknown User"` for many documents (PDF generator default).
- Non-Latin documents returning garbled author names (encoding issue).
- Language field returning `"en"` for clearly non-English documents.

**Phase to address:** Metadata enrichment phase. The output schema must include confidence signals from day one.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Return `DoclingDocument` directly from adapter | No translation layer to write | Domain is coupled to Docling; library swap requires touching every layer | Never |
| Hardcode chunk size in chunker | One less config parameter | Consumers with different embedding models get wrong chunk sizes | Never |
| `await file.read()` in async route | Simpler code | OOM on large files; blocks event loop | Never |
| Mock `ExtractorPort` in all service tests | Fast tests, no Docling install required | Docling adapter bugs are never caught before production | Only for pure unit tests of service logic; must have separate integration tests |
| Single `DocumentConverter` instance with no memory management | Simple initialization | Memory leak kills process after N documents | Acceptable as v1 if max document volume is < 20 docs/day; must be fixed before any sustained load |
| Skip timeout on extraction calls | Simpler async code | Single slow document hangs worker indefinitely | Never |
| Store all metadata in `dict[str, Any]` | Fast to add new fields | No type safety; missing fields are runtime errors | Never for the core `Chunk` model; acceptable for optional extension fields |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Docling `DocumentConverter` | Instantiate per request | Instantiate once at startup; add memory monitoring |
| Docling pipeline options | Leave all enrichments enabled (default) | Disable table structure, formula enrichment, picture classification unless explicitly needed |
| FastAPI `UploadFile` | Call `await file.read()` for the full file | Write to `NamedTemporaryFile` in chunks; pass the file path to the extractor |
| FastAPI async route + Docling | Call extractor directly in `async def` | Wrap extractor call in `run_in_threadpool()` or `run_in_executor()` |
| Chunk output schema | Define `metadata` as `dict` | Define as typed `ChunkMetadata` dataclass with all fields required |
| PDF metadata fields | Use raw values from Docling output | Validate encoding, check for placeholder values, attach confidence annotation |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Synchronous Docling call in async route | All requests queue behind one extraction; P99 latency = P99 extraction time | `run_in_threadpool()` wrapping | At first concurrent request |
| Memory accumulation across requests | Container OOM killed after N requests; RSS grows without bound | Converter refresh strategy or subprocess isolation | After ~50–200 documents depending on document size |
| Image-heavy PDF without timeout | Worker hangs for 30+ minutes; upstream times out, retry storms | Hard extraction timeout (120s); return structured timeout error | First time a scanned PDF is uploaded |
| Chunk size mismatch with embedding model | Embedding API silently truncates chunks; retrieval quality degrades | Validate chunk token count against model limit before returning | First time a long-text chunk is embedded |
| Loading entire file into memory | OOM on files > available RAM; slow reads blocking event loop | Chunked reads; temp file on disk | Files > 50MB or concurrent uploads |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Accepting all MIME types without validation | Arbitrary file execution risk; zip bombs; non-document files consuming resources | Validate `Content-Type` and magic bytes (not just file extension) before passing to Docling |
| No file size limit on upload | DoS via memory exhaustion | Enforce maximum file size at the HTTP layer (e.g., 50MB) before reading the body |
| Passing uploaded filename directly to filesystem | Path traversal if filename is used in temp file creation | Use `tempfile.NamedTemporaryFile()` with a generated name; never use `UploadFile.filename` as a filesystem path |
| Returning full extraction error details to API caller | Internal paths, library versions, system info leakage in stack traces | Wrap extraction exceptions in domain error types; log full trace internally; return only `error_code` + `message` to client |

---

## "Looks Done But Isn't" Checklist

- [ ] **Extraction adapter:** Often missing error taxonomy — verify that `PASSWORD_PROTECTED`, `CORRUPTED`, `EMPTY_DOCUMENT`, `TIMEOUT`, `UNSUPPORTED_FORMAT` all return distinct typed errors, not a bare `Exception`
- [ ] **Chunk schema:** Often missing `total_chunks` and `chunk_index` — verify chunks can be re-ordered and deduplicated by a consumer without re-processing the document
- [ ] **Metadata confidence:** Often missing — verify every inferred metadata field has an accompanying source/confidence indicator in the response
- [ ] **Memory monitoring:** Often missing — verify the service exposes a `/health` or `/metrics` endpoint that includes process RSS so memory leaks are observable
- [ ] **Timeout enforcement:** Often missing — verify a request processing a slow document does not block indefinitely; test by uploading a large scanned PDF and killing it after 30 seconds
- [ ] **Event loop safety:** Often missing — verify Docling extraction is not called directly inside `async def` routes; check with `asyncio` debug mode
- [ ] **Real document integration tests:** Often missing — verify the test suite includes at least one test that passes a real PDF through the real `ExtractorAdapter`, not a mock

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Docling types leaked into domain | HIGH | Define domain types, rewrite adapter translation layer, update all service code and tests; requires full regression |
| Memory leak in production | MEDIUM | Add process restart policy (e.g., uvicorn `--workers` with external supervisor restart on OOM); add converter refresh as hotfix; fix properly in next sprint |
| Blocking event loop discovered in production | MEDIUM | Add `run_in_threadpool()` wrapper to extractor call; deploy; no architectural change required |
| Chunks missing metadata in production data | HIGH | Re-process all documents through updated pipeline; no in-place patch possible if consumer already stored chunks without metadata |
| Scope creep feature merged | MEDIUM | Revert PR; document the decision boundary; add pre-merge checklist item |
| Wrong chunk size causing retrieval failures | MEDIUM | Add chunk size config to API; re-process documents with correct size; update consumer embedding pipeline |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Docling types leaking into domain | Architecture foundation | Domain models have zero `docling` imports; `from docling` appears only in adapter file |
| Anemic ports mirroring library API | Architecture foundation | Port signatures use only domain types; reviewed before any adapter is written |
| Chunk metadata missing | Architecture foundation (schema design) + Chunking phase | `Chunk` dataclass has all fields required (non-Optional); serialization test passes |
| Memory leak | PDF extraction phase | Service processes 100 documents sequentially; RSS does not grow monotonically |
| Image PDF slowness + no timeout | PDF extraction phase | Integration test with scanned PDF completes or times out within configured limit |
| Event loop blocking | FastAPI adapter phase | Concurrent request test: two simultaneous uploads do not serialize behind each other |
| File upload memory / safety | FastAPI adapter phase | Upload 100MB file; verify RSS stays bounded; verify path traversal blocked |
| Not testing with real documents | Every phase | CI passes with integration test suite including real PDF fixtures |
| Chunk size policy | Chunking phase | API returns `token_count` per chunk; chunks outside [100, 8192] tokens are rejected |
| Metadata inference reliability | Metadata enrichment phase | API response includes `confidence` annotation on all inferred fields |
| Scope creep | Every phase | PR review checklist item: "does this feature appear in PROJECT.md Active requirements?" |

---

## Sources

- [Docling issue #2829 — Memory not released after each file (DoclingLoader)](https://github.com/docling-project/docling/issues/2829)
- [Docling issue #2209 — DoclingParseV2DocumentBackend 13GB accumulation](https://github.com/docling-project/docling/issues/2209)
- [Docling issue #1886 — Memory leak with formula enrichment enabled](https://github.com/docling-project/docling/issues/1886)
- [Docling issue #2779 — Consumes all available memory and gets killed](https://github.com/docling-project/docling/issues/2779)
- [Docling issue #2954 — GPU memory leak on DocumentConverter delete](https://github.com/docling-project/docling/issues/2954)
- [Docling discussion #1651 — Why Docling is SO slow when converting PDF with images](https://github.com/docling-project/docling/discussions/1651)
- [Docling discussion #245 — Speed for low resource machines](https://github.com/docling-project/docling/discussions/245)
- [Hexagonal Architecture pitfalls — Java Code Geeks (2025)](https://www.javacodegeeks.com/2025/12/hexagonal-architecture-ports-and-adapters-achieving-true-domain-independence.html)
- [Hexagonal Architecture — two sides to every story (SSENSE Tech)](https://medium.com/ssense-tech/hexagonal-architecture-there-are-always-two-sides-to-every-story-bc0780ed7d9c)
- [FastAPI async file uploads — streaming vs buffering](https://medium.com/@connect.hashblock/async-file-uploads-in-fastapi-handling-gigabyte-scale-data-smoothly-aec421335680)
- [FastAPI SpooledTemporaryFile and event loop blocking](https://sqlpey.com/python/optimizing-fastapi-file-uploads/)
- [RAG chunking — chunk boundary and metadata alignment instability](https://dev.to/dowhatmatters/chunk-boundary-and-metadata-alignment-the-hidden-source-of-rag-instability-78b)
- [RAG production failures — ingestion as hidden bottleneck](https://medium.com/@anindyasinghobi/rag-ingestion-the-hidden-bottleneck-behind-retrieval-failures-52c2eb4c7924)
- [Your Chunks Failed Your RAG in Production — Towards Data Science](https://towardsdatascience.com/your-chunks-failed-your-rag-in-production/)
- [Chunking strategies for RAG — Redis Engineering Blog](https://redis.io/blog/chunking-strategy-rag-pipelines/)
- [Why chunking is harder than you think (April 2026)](https://medium.com/@nikolaskallweit_83151/why-chunking-in-rag-pipelines-is-harder-than-you-think-60e5be56b370)
- [Pitfalls of mocking in tests — Xebia](https://xebia.com/blog/pitfalls-mocking-tests-how-to-avoid/)
- [Document extraction evaluation — why accuracy alone misleads](https://www.runpulse.com/blog/evaluating-document-extraction)

---
*Pitfalls research for: document extraction and RAG ingestion pipeline (SelectionMaid)*
*Researched: 2026-05-23*

---
---

# Vue 3 Frontend Pitfalls — v2.0 Milestone

**Domain:** Animated Vue 3 SPA consuming a document-processing FastAPI backend
**Researched:** 2026-05-25
**Confidence:** HIGH (official FastAPI docs, MDN, GSAP docs, Vue 3 official docs, community post-mortems)

---

## Domain 1: Animation Performance (GSAP / Motion One / CSS)

### Pitfall F-1: Layout-Thrashing Animation Properties

**What goes wrong:**
Animating `top`, `left`, `width`, `height`, `margin`, or `padding` forces the browser through the full Layout → Paint → Composite pipeline on every frame. At 60fps, this runs 60 expensive layout recalculations per second. On a stagger animation revealing 50 chunks simultaneously, this produces a paint storm: the browser serializes all 50 layout passes, dropping frames and producing visible jank.

**Why it happens:**
Developers animate what visually makes sense ("move it down from off-screen"), reach for `top`/`left` without knowing they trigger layout, or copy examples that predate GPU-composited animation patterns.

**Prevention:**
Animate only `transform` (translate, scale, rotate) and `opacity`. These properties skip the Layout and Paint stages entirely and execute on the GPU compositor thread, never blocking the main thread. Use `gsap.to(el, { y: 20, opacity: 1 })` not `gsap.to(el, { top: '20px', opacity: 1 })`. GSAP maps `x`/`y`/`xPercent`/`yPercent` to `transform: translateX/Y` automatically — always prefer these aliases.

**Detection:**
Open Chrome DevTools Performance tab, record during animation, look for "Layout" and "Paint" events in the flame chart. Any purple (Layout) or green (Paint) bars during the animation indicate layout-thrashing properties are being animated.

**Phase to address:** Frontend animation phase. Must be a code review criterion from the first animated component.

---

### Pitfall F-2: Premature Animation Before DOM Mount (Vue + GSAP Race)

**What goes wrong:**
GSAP targets are defined at the `<script setup>` top level or in `created()`, before the component's DOM exists. `gsap.to(el, ...)` silently targets `null` and does nothing. The animation never runs. No error is thrown — the failure is invisible.

**Why it happens:**
The `ref()` variable exists immediately, but its `.value` is `null` until after the template renders. Developers unfamiliar with Vue's render cycle call `gsap.to(el.value, ...)` at the wrong lifecycle moment.

**Prevention:**
All GSAP calls that target DOM elements must live inside `onMounted()`. For child components or `v-if`-toggled elements, use `nextTick()` inside `onMounted()` if the element is conditionally rendered. Never reference a template ref's `.value` synchronously at module scope.

```js
// Wrong — el.value is null here
const el = ref(null)
gsap.to(el.value, { opacity: 1 }) // targets null, silent fail

// Correct
onMounted(() => {
  gsap.to(el.value, { opacity: 1 })
})
```

**Detection:** Add a guard: `if (!el.value) { console.warn('GSAP target not mounted') }` during development. Remove in production builds.

**Phase to address:** Frontend animation phase, first animated component.

---

### Pitfall F-3: GSAP Context Not Cleaned Up on Component Unmount (Memory Leak)

**What goes wrong:**
Tweens, timelines, and ScrollTrigger instances created in `onMounted()` are never killed when the component unmounts. In a SPA where the user navigates between views, these orphaned animations continue running against detached DOM nodes. Memory accumulates: empirical studies show retained memory from leaked Vue component animation state reaching 819 KB per navigation cycle vs. 2.6 KB with proper cleanup — a 315x difference.

**Why it happens:**
GSAP animations run outside Vue's reactivity system. Vue's component teardown does not know about GSAP. The animation object holds a reference to the DOM node, preventing garbage collection.

**Prevention:**
Use `gsap.context()` to register all animations, then call `ctx.revert()` in `onBeforeUnmount()`. This is the canonical GSAP cleanup pattern.

```js
let ctx
onMounted(() => {
  ctx = gsap.context(() => {
    gsap.to(el.value, { opacity: 1, duration: 0.6 })
    // All gsap calls inside here are tracked
  })
})
onBeforeUnmount(() => {
  ctx?.revert() // kills tweens, removes event listeners, restores original state
})
```

For ScrollTrigger specifically: call `ScrollTrigger.refresh()` after route changes and `ScrollTrigger.getAll().forEach(t => t.kill())` in the global router `afterEach` hook if triggers are not scoped to a context.

**Detection:** Navigate away from an animated view and back several times; use Chrome Memory tab to verify heap is not growing.

**Phase to address:** Frontend animation phase. Establish the `gsap.context` + `onBeforeUnmount` pattern as the mandatory template for every animated component.

---

### Pitfall F-4: Stagger Animation on Too Many Elements Simultaneously

**What goes wrong:**
A response returns 100 chunks. The UI renders all 100 at once and staggers a `gsap.from()` animation across all of them. GSAP creates 100 simultaneous tweens. Even with GPU-composited properties, promoting 100 elements to their own GPU layers (each requiring `will-change: transform` or equivalent) creates memory pressure and can cause the browser's compositor to stall on low-end hardware.

**Why it happens:**
Stagger feels like it handles the timing problem (items animate one after another), but it does not reduce the number of active tweens or GPU layers at any given moment.

**Prevention:**
- Cap the stagger to the first N visible items (typically 10–15). Items below the fold do not need to animate in — they can appear static.
- Use `will-change: transform` only during the animation, not permanently. Add it via JS before the tween and remove it in the `onComplete` callback.
- For very large lists, use `vue-virtual-scroller` or VueUse's `useVirtualList` and animate only the items in the current render window.
- As a maximum: do not stagger more than 20 elements with GSAP simultaneously. Beyond that, use CSS `animation-delay` with `nth-child` selectors, which is handled by the browser's own animation engine without JS overhead.

**Phase to address:** Frontend chunks display phase. Establish the visible-items-only stagger rule before building the chunk list component.

---

### Pitfall F-5: Overuse of `will-change` Causing GPU Memory Pressure

**What goes wrong:**
`will-change: transform` is added permanently in CSS to "make animations faster." When applied to many elements (e.g., every chunk card), the browser promotes all of them to GPU layers upfront and keeps them promoted permanently — even when idle. On mobile, this exhausts GPU memory and causes the browser to demote layers mid-animation, causing worse stuttering than not using `will-change` at all.

**Why it happens:**
Documentation correctly states that `will-change` helps animation performance, but omits the memory cost of permanent promotion.

**Prevention:**
Apply `will-change: transform` dynamically just before an animation starts and remove it immediately after `onComplete`. GSAP handles this automatically when using the `force3D: true` option during the tween and `force3D: false` or `clearProps: "will-change"` on complete. Alternatively, let GSAP manage layer promotion entirely — it already uses `transform: translateZ(0)` internally.

**Phase to address:** Frontend animation phase. Establish a code review rule: no static `will-change` in CSS files.

---

## Domain 2: CORS Configuration on FastAPI

### Pitfall F-6: `allow_origins=["*"]` with `allow_credentials=True`

**What goes wrong:**
The FastAPI backend is configured with both `allow_origins=["*"]` and `allow_credentials=True`. This is rejected by browsers as an invalid CORS response. The browser refuses to expose the response to JavaScript, regardless of what the server sends. The error message is: `"The value of the 'Access-Control-Allow-Origin' header in the response must not be the wildcard '*' when the request's credentials mode is 'include'."` Every request from the SPA fails.

**Why it happens:**
The CORS spec explicitly forbids this combination. Developers add `allow_credentials=True` by habit ("credentials are usually needed"), not realizing credentials here means cookies and `Authorization` headers — which SelectionMaid v2.0 does not use.

**Prevention:**
For SelectionMaid (no auth, no cookies), use `allow_credentials=False` (the default) with `allow_origins=["*"]`. This is correct for a public tool with no authentication. If credentials are ever added later, switch to explicit origins.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_credentials=False,          # No cookies, no auth headers
    allow_methods=["POST", "GET"],    # Only what the SPA actually uses
    allow_headers=["Content-Type"],
)
```

**Detection:** Browser console will show a CORS error on every request. Network tab shows the preflight OPTIONS response lacks `Access-Control-Allow-Origin`.

**Phase to address:** CORS configuration phase (first frontend-to-backend connection). One-time setup; verify with a browser request before building any feature.

---

### Pitfall F-7: Middleware Registration Order Causing CORS to Miss Error Responses

**What goes wrong:**
`CORSMiddleware` is added after other middleware (e.g., a request logging middleware that raises an exception on invalid requests). When the other middleware raises before the CORS middleware runs, the error response has no CORS headers. The browser sees a CORS error instead of the actual HTTP error (400, 413, etc.), making debugging extremely difficult. The developer investigates CORS when the real problem is an upstream middleware raising on file size limits.

**Why it happens:**
FastAPI middleware is applied in reverse registration order. The last-added middleware runs outermost (first to see requests, last to see responses). Developers add CORS last as an afterthought.

**Prevention:**
Register `CORSMiddleware` as the very first middleware call in the app setup, before any other `add_middleware()` calls. This ensures it wraps all responses, including error responses from inner middleware.

```python
# Correct: CORS is registered first, runs outermost
app.add_middleware(CORSMiddleware, ...)
app.add_middleware(RequestSizeLimitMiddleware, ...)
app.add_middleware(LoggingMiddleware, ...)
```

**Detection:** CORS error on a request that the server legitimately rejects (e.g., file too large). Check if the server is returning 400/413 without CORS headers.

**Phase to address:** CORS configuration phase.

---

### Pitfall F-8: Development vs. Production Origin Mismatch

**What goes wrong:**
During development, the SPA runs at `http://localhost:5173` (Vite default). In production, it runs at `https://selectionmaid.internal` or similar. The backend `allow_origins` list only contains the development origin. Production CORS fails silently in staging when tested from a different machine, then fails loudly in production.

**Prevention:**
Read allowed origins from an environment variable, not hardcoded in source.

```python
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:4173"
).split(",")

app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, ...)
```

Set `CORS_ORIGINS=https://selectionmaid.internal` in the production environment. Never commit production origins to source.

**Phase to address:** CORS configuration phase. Establish the env-var pattern before any environment-specific deployment.

---

## Domain 3: Drag-and-Drop File Upload

### Pitfall F-9: Missing `preventDefault()` on `dragover` Prevents Drop

**What goes wrong:**
The `drop` event never fires. Files cannot be dropped anywhere on the zone. The browser's default behavior is to navigate to the dropped file URL, which overrides the custom drop handler entirely.

**Why it happens:**
Developers handle `drop` but forget `dragover`. The `dragover` event must call `event.preventDefault()` to signal to the browser that the element accepts drops — only then will `drop` fire.

**Prevention:**
Three events require `preventDefault()`: `dragenter`, `dragover`, and `drop`. Vue's `.prevent` modifier handles this declaratively.

```html
<div
  @dragenter.prevent
  @dragover.prevent
  @drop.prevent="onDrop"
>
```

Also prevent `dragleave.prevent` if you want to block browser navigation on drag-out. Without `.prevent` on `dragover`, the drop cursor shows a "forbidden" icon in most browsers.

**Detection:** Drop a file on the zone and observe whether the browser navigates away. If it does, `dragover.preventDefault()` is missing.

**Phase to address:** Frontend upload phase, first implementation of the drop zone component.

---

### Pitfall F-10: Drop Zone Flickering When Dragging Over Child Elements

**What goes wrong:**
The drop zone highlights when a file enters it. As the user drags over an icon, text label, or border element inside the drop zone, the zone briefly flashes between "active" and "inactive" states. This is caused by `dragleave` firing when the cursor transitions from the drop zone to a child element, even though the cursor is still within the logical drop area.

**Why it happens:**
`dragleave` fires for every element boundary crossed, including boundaries between a parent and its children. There is no way to suppress this with `stopPropagation`. It is a browser specification behavior.

**Prevention:**
Track entry depth with a counter. The zone is only considered "left" when the counter reaches zero.

```js
const dragCount = ref(0)
const isDragOver = computed(() => dragCount.value > 0)

function onDragEnter() { dragCount.value++ }
function onDragLeave() { dragCount.value-- }
function onDrop(e) {
  dragCount.value = 0
  handleFiles(e.dataTransfer.files)
}
```

Reset the counter to 0 on `drop` to handle edge cases where events are missed.

**Detection:** Drag a file over the drop zone and move slowly over any child element (icon, text, border). Visual flickering indicates the counter approach is needed.

**Phase to address:** Frontend upload phase.

---

### Pitfall F-11: Drag-and-Drop Does Not Work on Mobile (Touch Devices)

**What goes wrong:**
The HTML5 Drag and Drop API is not triggered by touch events. On iOS Safari, Android Chrome, and all mobile browsers, dragging with a finger does not fire `dragenter`, `dragover`, or `drop` events. The drop zone is completely non-functional on touch devices.

**Why it happens:**
The HTML5 DnD spec and the Touch Events spec are separate and were never reconciled. No browser vendor has implemented DnD via touch input.

**Prevention:**
Always include a visible `<input type="file">` element as a fallback. Style it visually as a "tap to select" affordance on touch devices, or wire the drop zone's `click` event to trigger the hidden input.

```html
<div class="drop-zone" @click="fileInput.click()">
  Drop files here or tap to browse
  <input ref="fileInput" type="file" accept=".pdf,.docx,.html" hidden @change="onFileSelected" />
</div>
```

For SelectionMaid (internal dev tool), mobile support is out of scope, but the `<input>` fallback is still required for keyboard users and for cases where users prefer the file browser dialog.

**Detection:** Open the SPA on a mobile device or simulate touch in DevTools; attempt to drag a file. If nothing happens, the fallback is required.

**Phase to address:** Frontend upload phase. Include `<input type="file">` from the first implementation; do not add it as an afterthought.

---

### Pitfall F-12: Accessing `dataTransfer.files` Outside the `drop` Handler

**What goes wrong:**
The `FileList` from `event.dataTransfer.files` is accessed asynchronously — stored in a ref, then accessed later inside an `await` or `setTimeout`. By then, the `DataTransfer` object may have been cleared by the browser. The `FileList` is empty or the files are null.

**Why it happens:**
`DataTransfer` is a live object tied to the drag event's lifetime. Once the event handler returns, the browser can garbage-collect the data.

**Prevention:**
Extract the files synchronously inside the `drop` handler before any `await`:

```js
function onDrop(event) {
  const files = Array.from(event.dataTransfer.files) // extract immediately
  dragCount.value = 0
  // Now 'files' is a plain array, safe to use asynchronously
  uploadFiles(files)
}
```

**Phase to address:** Frontend upload phase.

---

## Domain 4: Displaying Large Lists of Text Chunks

### Pitfall F-13: Rendering All Chunks Without Virtualization

**What goes wrong:**
The API returns 200 chunks. The template renders all 200 `<ChunkCard>` components into the DOM simultaneously. Each card contains Markdown-rendered text, code highlighting, and metadata badges. The initial render stalls the main thread for 2–5 seconds on mid-range devices. Scrolling is janky because the browser must manage 200 fully-rendered DOM subtrees. Memory usage spikes from the simultaneous creation of thousands of DOM nodes.

**Why it happens:**
Small documents produce 10–30 chunks, which render fine. Developers test with small documents and never discover the performance cliff at 100+ chunks. The cliff appears only with real-world documents in production.

**Prevention:**
Use `@vueuse/core`'s `useVirtualList` or `vue-virtual-scroller` to render only the visible chunk cards plus a small buffer (~5 above and below viewport). The rest of the list is represented by spacer elements that maintain scroll height without DOM nodes.

For SelectionMaid v2.0 (internal tool, typically 20–80 chunks from typical documents), virtualization is not strictly required but should be the default to prevent the cliff. Establish a performance budget: if chunk count exceeds 50, switch to virtual rendering.

If full virtualization is too complex for the initial phase, implement lazy rendering via `IntersectionObserver`: render chunk cards only when they enter the viewport, starting from the top.

**Detection:** Upload a 60-page PDF. Check the chunk count in the response. Open Chrome DevTools → Performance → record while scrolling the chunk list. Any "Long Task" marker over 50ms indicates a rendering bottleneck.

**Phase to address:** Frontend chunks display phase. Establish the chunk count threshold policy before building the list component.

---

### Pitfall F-14: Applying Stagger Animation to All Chunks Including Off-Screen Ones

**What goes wrong:**
On reveal, `gsap.from('.chunk-card', { stagger: 0.05 })` targets all 150 chunk cards. At 0.05s stagger, the last card begins animating 7.5 seconds after the first. The user sees items still animating minutes after the page loaded. GSAP creates 150 simultaneous tweens at their stagger offsets, holding references to all 150 elements for the duration.

**Prevention:**
Limit the stagger animation to the first 10–15 visible items only. Items below the fold appear statically or fade in individually via `IntersectionObserver` when they scroll into view.

```js
onMounted(() => {
  const visibleCards = Array.from(document.querySelectorAll('.chunk-card')).slice(0, 12)
  gsap.from(visibleCards, {
    opacity: 0,
    y: 16,
    stagger: 0.04,
    duration: 0.4,
    ease: 'power2.out'
  })
})
```

**Phase to address:** Frontend chunks display phase.

---

### Pitfall F-15: Markdown Rendering Blocking the Main Thread

**What goes wrong:**
Each chunk contains Markdown text. Rendering 100 chunks with a Markdown parser (e.g., `marked`, `markdown-it`) synchronously in a `v-for` loop blocks the main thread during the initial render. On documents with code blocks requiring syntax highlighting, the blocking time can exceed 500ms.

**Prevention:**
- Parse Markdown lazily: only parse chunks that are visible or about to become visible.
- For syntax highlighting, use a web worker or async highlighting (Shiki's async API, highlight.js with `highlightElement` deferred via `requestIdleCallback`).
- Cache parsed Markdown output in a `computed` or `Map` keyed by chunk index — never re-parse the same chunk.

**Phase to address:** Frontend chunks display phase, when Markdown rendering is first introduced.

---

## Domain 5: Handling Slow API Responses

### Pitfall F-16: No Timeout on the `fetch()` Call

**What goes wrong:**
Docling processing a scanned PDF can take 60–120 seconds. The `fetch()` call has no timeout. The user's browser waits indefinitely with a spinner. The user closes the tab. The connection hangs on the server side too, holding the worker thread. If the user clicks "Upload" again, a second request starts, potentially queuing behind the first. Under concurrent usage, this exhausts server workers.

**Prevention:**
Always attach `AbortSignal.timeout()` to `fetch()` for document processing requests. Choose a timeout slightly above the backend's own extraction timeout (e.g., if the backend kills after 120 seconds, use 130 seconds client-side).

```js
const controller = new AbortController()
const timeoutSignal = AbortSignal.timeout(130_000) // 130 seconds
const combinedSignal = AbortSignal.any([controller.signal, timeoutSignal])

try {
  const response = await fetch('/api/process', {
    method: 'POST',
    body: formData,
    signal: combinedSignal
  })
} catch (err) {
  if (err.name === 'TimeoutError') {
    // Show "Processing is taking too long — try a smaller file"
  } else if (err.name === 'AbortError') {
    // User cancelled
  }
}
```

Store `controller` in a `ref` so the user can cancel manually via a "Cancel" button. Call `controller.abort()` on component unmount to prevent state updates on an unmounted component.

**Detection:** Upload a large scanned PDF. Observe whether the UI provides feedback and eventually times out or hangs indefinitely.

**Phase to address:** Frontend API integration phase. The timeout pattern must be in the first API call implementation.

---

### Pitfall F-17: No Progressive Feedback During Processing (Perceived Performance)

**What goes wrong:**
The backend takes 30–60 seconds. The frontend shows a spinner for the entire duration. The user cannot tell if the system is working, frozen, or failed. Perceived wait time is far worse than actual wait time when no progress is communicated. Users abandon the tool after 15–20 seconds of static feedback.

**Prevention:**
Use skeleton/shimmer loading states that communicate the structure of what is coming. For SelectionMaid specifically: show shimmer placeholder cards for the expected chunk list while processing. Animate the shimmer continuously to confirm the system is alive. Add time-based messaging: after 10 seconds show "Processing large document...", after 30 seconds show "This document is complex — still working...".

For a more sophisticated approach, use FastAPI's `StreamingResponse` with newline-delimited JSON (NDJSON) to emit processing events as they occur: `{"stage": "extracting"}`, `{"stage": "filtering"}`, `{"stage": "chunking"}`, `{"stage": "complete", "chunks": [...]}`. The frontend reads the stream with `response.body.getReader()` and updates the UI progressively.

The NDJSON streaming approach requires changes on both sides but delivers immediate visual feedback and eliminates the perception of a frozen UI.

**Phase to address:** Frontend API integration phase (skeleton states are phase 1; streaming is optional phase 2 if v2.0 scope expands).

---

### Pitfall F-18: Rendering the Entire Response JSON at Once After Long Wait

**What goes wrong:**
After 60 seconds, the server returns a 200-chunk JSON response (potentially 500KB–2MB of text). The frontend parses the entire JSON blob, then triggers a full component render for all 200 chunks in a single synchronous pass. The main thread is blocked for 1–3 seconds immediately after the long wait, producing a "double wait" user experience.

**Prevention:**
- Parse and render chunks incrementally. After parsing the JSON, use `requestIdleCallback` or a chunked rendering approach to add chunks to the reactive list in batches of 10–20 per idle frame.
- Use `v-memo` on chunk cards to prevent unnecessary re-renders when the list grows.
- If NDJSON streaming is implemented, this problem is solved naturally — chunks arrive and render incrementally as the server produces them.

**Phase to address:** Frontend chunks display phase.

---

## Domain 6: Vue 3 Composition API Anti-Patterns (Animation Context)

### Pitfall F-19: Destructuring `reactive()` Objects Breaks Reactivity

**What goes wrong:**
```js
const state = reactive({ isDragOver: false, isUploading: false })
const { isDragOver, isUploading } = state  // Breaks reactivity
```
`isDragOver` and `isUploading` are now plain booleans. Changing `state.isDragOver` does not update the template. The drag-over highlight never appears.

**Prevention:**
Use `ref()` for individual values, or use `toRefs()` when destructuring from `reactive()`.

```js
const isDragOver = ref(false)  // Correct
// Or, if grouping is needed:
const state = reactive({ isDragOver: false })
const { isDragOver } = toRefs(state)  // Correct destructuring
```

**Phase to address:** Frontend setup phase. Establish the `ref()` preference in coding conventions before building components.

---

### Pitfall F-20: `watchEffect` Firing Immediately with Unintended Side Effects

**What goes wrong:**
```js
watchEffect(() => {
  if (chunks.value.length > 0) {
    gsap.from('.chunk-card', { stagger: 0.05 })
  }
})
```
`watchEffect` runs immediately on setup. If `chunks.value` is empty, the condition is false — but GSAP still creates a watcher on the DOM query every time reactivity triggers. More critically, if the `chunks.value` check passes on a re-render, the stagger animation fires again on top of a previously running animation, creating overlapping tweens.

**Prevention:**
Use `watch()` with `immediate: false` (the default) to react only to changes, not the initial state. Kill the previous tween before creating a new one.

```js
let staggerTween = null
watch(chunks, (newChunks) => {
  if (newChunks.length === 0) return
  staggerTween?.kill()
  nextTick(() => {
    const cards = document.querySelectorAll('.chunk-card')
    staggerTween = gsap.from(cards, { opacity: 0, y: 16, stagger: 0.04 })
  })
})
```

**Phase to address:** Frontend animation phase.

---

### Pitfall F-21: Passing Reactive Props to Composables Without Getter Wrapping

**What goes wrong:**
```js
// In parent
const chunkCount = ref(0)

// In composable call
useChunkAnimation(chunkCount.value)  // Passes the current number, not the ref
```
The composable receives `0` (the current value), not the reactive reference. It never reacts to changes in `chunkCount`.

**Prevention:**
Pass refs directly, or wrap in a getter:

```js
useChunkAnimation(chunkCount)           // Pass the ref itself
useChunkAnimation(() => chunkCount.value) // Or a getter function
```

VueUse composables consistently use this pattern — reading their source is the best reference.

**Phase to address:** Frontend composable extraction phase, when animation logic is moved from components into reusable composables.

---

## Frontend Pitfall-to-Phase Mapping

| Pitfall | Severity | Prevention Phase | Key Verification |
|---------|----------|------------------|------------------|
| F-1: Layout-thrashing animation properties | HIGH | Animation phase | DevTools Performance: no Layout/Paint events during animation |
| F-2: GSAP targets before DOM mount | HIGH | Animation phase, first component | Animated element actually animates |
| F-3: Missing GSAP context cleanup | HIGH | Animation phase | Navigate away/back 10 times; heap stable |
| F-4: Stagger on >20 elements | MEDIUM | Chunks display phase | Cap stagger to visible items only |
| F-5: Permanent `will-change` in CSS | MEDIUM | Animation phase | Code review: no static `will-change` in CSS files |
| F-6: `allow_origins="*"` + `allow_credentials=True` | CRITICAL | CORS setup phase | Browser Network tab: OPTIONS preflight returns correct headers |
| F-7: CORS middleware registration order | HIGH | CORS setup phase | Error responses include CORS headers |
| F-8: Hardcoded CORS origins | MEDIUM | CORS setup phase | `CORS_ORIGINS` env var controls allowed origins |
| F-9: Missing `dragover.preventDefault()` | CRITICAL | Upload phase, day 1 | Drop actually works |
| F-10: Drop zone flickering | HIGH | Upload phase | Counter approach tested by dragging over child elements |
| F-11: No mobile/touch fallback | MEDIUM | Upload phase | `<input type="file">` always present |
| F-12: Async `dataTransfer.files` access | HIGH | Upload phase | Files extracted synchronously before any await |
| F-13: Rendering all chunks without virtualization | HIGH | Chunks display phase | Performance test with 100+ chunks |
| F-14: Stagger on off-screen chunks | MEDIUM | Chunks display phase | Only first 10–15 cards are stagger-animated |
| F-15: Synchronous Markdown rendering | MEDIUM | Chunks display phase | Deferred/cached Markdown parsing |
| F-16: No fetch timeout | CRITICAL | API integration phase | 130-second AbortSignal on all processing requests |
| F-17: No progressive feedback | HIGH | API integration phase | Shimmer skeleton visible during processing |
| F-18: All-at-once response rendering | MEDIUM | Chunks display phase | Incremental render in idle frames |
| F-19: Destructuring reactive objects | HIGH | Frontend setup, conventions | ESLint rule or code review; use `ref()` / `toRefs()` |
| F-20: watchEffect immediate side effects | MEDIUM | Animation phase | Use `watch()` with explicit trigger conditions |
| F-21: Non-reactive composable props | HIGH | Composable extraction phase | Composables receive refs, not values |

---

## Frontend "Looks Done But Isn't" Checklist

- [ ] **CORS:** Browser Network tab confirms OPTIONS preflight returns `Access-Control-Allow-Origin` for both `http://localhost:5173` and production origin
- [ ] **Drop zone:** Drag a file and move slowly over all child elements (icon, label, border) — no flickering
- [ ] **Drop zone:** Attempt drag-and-drop on a mobile device or touch simulator — `<input type="file">` is the fallback
- [ ] **Animation:** Open DevTools Performance during chunk reveal stagger — no purple (Layout) or green (Paint) bars
- [ ] **Animation:** Navigate away from an animated view and back 10 times — Chrome Memory heap is stable
- [ ] **Timeout:** Upload a large PDF and wait 130 seconds — UI shows timeout message, not indefinite spinner
- [ ] **Chunk list:** Upload a document that produces 80+ chunks — scrolling is smooth (no long tasks in DevTools)
- [ ] **Reactivity:** All animation trigger conditions use `watch()` not `watchEffect()` where side effects must not run on initial setup

---

## Frontend Sources

- [GSAP In Practice: Avoid The Pitfalls — Marmelab (2024)](https://marmelab.com/blog/2024/05/30/gsap-in-practice-avoid-the-pitfalls.html)
- [High-Performance Web Animation: GSAP, WebGL, and the Secret to 60fps — DEV Community](https://dev.to/kolonatalie/high-performance-web-animation-gsap-webgl-and-the-secret-to-60fps-2l1g)
- [GSAP Stagger Docs — gsap.com](https://gsap.com/resources/getting-started/Staggers/)
- [Optimizing Animation Performance in GSAP — RUSTCODE (2024)](https://www.rustcodeweb.com/2024/04/optimizing-animation-performance-in-gsap.html)
- [GSAP + Vue 3 Composable with context — github.com/c5vargas/gsap-vue](https://github.com/c5vargas/gsap-vue)
- [How to Clean Up Third-party Libraries in Vue Components — Markus Oberlehner](https://markus.oberlehner.net/blog/how-to-clean-up-global-event-listeners-intervals-and-third-party-libraries-in-vue-components)
- [Frontend Memory Leaks Empirical Study — StackInsight](https://stackinsight.dev/blog/memory-leak-empirical-study/)
- [CORS (Cross-Origin Resource Sharing) — FastAPI Official Docs](https://fastapi.tiangolo.com/tutorial/cors/)
- [Blocked by CORS in FastAPI? Here's How to Fix It — David Muraya](https://davidmuraya.com/blog/fastapi-cors-configuration/)
- [CORSMiddleware not work — FastAPI Discussion #7319](https://github.com/fastapi/fastapi/discussions/7319)
- [open-webui: allow_origins wildcard + credentials conflict — Issue #14181](https://github.com/open-webui/open-webui/issues/14181)
- [Drag-and-Drop File Uploader with Vue.js 3 — Smashing Magazine (2022)](https://www.smashingmagazine.com/2022/03/drag-drop-file-uploader-vuejs-3/)
- [Flickering when dragging over child elements — Dropzone Issue #438](https://github.com/dropzone/dropzone/issues/438)
- [HTMLElement: dragleave event — MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/dragleave_event)
- [Drag-and-drop does not work with touch events — Syncfusion Forums](https://www.syncfusion.com/forums/166752/drag-and-drop-does-not-work-with-touch-event-touch-screen-devices)
- [Handling Large Lists Efficiently in Vue 3 — DEV Community](https://dev.to/jacobandrewsky/handling-large-lists-efficiently-in-vue-3-4im1)
- [Create a Performant Virtual Scrolling List in Vue.js — LogRocket](https://blog.logrocket.com/create-performant-virtual-scrolling-list-vuejs/)
- [useVirtualList — VueUse](https://vueuse.org/core/usevirtuallist/)
- [AbortSignal: timeout() static method — MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal/timeout_static)
- [FastAPI Streaming Responses: Real-Time Without WebSockets — Medium](https://medium.com/@bhagyarana80/fastapi-streaming-responses-real-time-without-websockets-bc6b071f5d9e)
- [Getting timeout when response takes >1 minute — FastAPI Discussion #9376](https://github.com/fastapi/fastapi/discussions/9376)
- [Top 3 Composition API Pitfalls — Escuela Vue](https://escuelavue.es/en/devtips/top-3-composition-api-pitfalls)
- [Reactivity Best Practices in Vue — Certificates.dev](https://certificates.dev/blog/reactivity-best-practices-in-vue)
- [Motion vs GSAP — motion.dev](https://motion.dev/docs/gsap-vs-motion)

---
*Frontend pitfalls appended: 2026-05-25 — Vue 3 SPA v2.0 milestone*
