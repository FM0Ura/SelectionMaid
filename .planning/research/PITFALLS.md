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
