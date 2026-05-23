# Feature Research

**Domain:** Document extraction and normalization service for RAG ingestion pipelines
**Researched:** 2026-05-23
**Confidence:** HIGH (stack confirmed via official Docling docs; patterns verified across multiple production sources)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that any document ingestion service must have. Missing these makes the service non-functional for its primary purpose.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| PDF ingestion with text extraction | PDF is the dominant document format in enterprise and research contexts — any ingestion service without it is unusable | MEDIUM | Docling handles native-text PDFs natively; scanned PDFs require OCR pipeline |
| DOCX ingestion | Word documents are the dominant authoring format; required for office-document workflows | LOW | Docling supports .docx natively with full structure preservation |
| HTML ingestion | Web content, documentation sites, and scraped pages arrive as HTML | LOW | Docling supports HTML natively |
| Image ingestion with OCR | Scanned documents and image-only PDFs need OCR to be processable | HIGH | Requires model weight download (EasyOCR or Tesseract); adds latency |
| Markdown output | LLMs consume Markdown natively; it preserves heading hierarchy, tables, and lists that plain text destroys | LOW | Docling's primary export format; no additional implementation needed |
| Heading / section hierarchy preservation | Consumers use heading levels to determine chunk boundaries and context; flat text loses document structure | MEDIUM | Docling's DoclingDocument model tracks heading levels; exporter emits `#`, `##`, etc. |
| Table preservation in output | Tables contain structured facts that are high-value for RAG; dropped tables = information loss | HIGH | Docling uses TableFormer model for structure extraction; complex nested tables can fail |
| Fixed-size chunking with configurable size | The simplest chunking strategy; must be available as a baseline; every production system supports it | LOW | Token-count or character-count boundary with configurable `chunk_size` param |
| Chunk overlap / sliding window | Adjacent chunks sharing a boundary window prevents context loss at split points | LOW | Overlap percentage configurable; ~10–20% is the standard default |
| Page-number metadata per chunk | Consumers use page numbers to cite sources and debug retrieval; missing = unusable for citation | LOW | Docling exposes page provenance; must be threaded through to output schema |
| Source document identifier per chunk | Consumers must join chunk back to source document; a stable `doc_id` is required | LOW | Generate on ingest: hash of file bytes or UUID; store in every chunk |
| Chunk index within document | Position of chunk in document order is required for coherence; consumers use it for re-ranking | LOW | Counter during chunking loop |
| Structured JSON response schema | Consumers need a deterministic schema to parse; ad-hoc text output is unacceptable in API context | LOW | Pydantic model on output; version-stable |
| HTTP POST endpoint for file upload | Primary interaction pattern; multipart/form-data is the standard for binary file transfer | LOW | FastAPI `UploadFile` with `python-multipart`; well-understood pattern |
| Synchronous response for on-demand use | Low-traffic, on-demand pipelines block and wait for result; async with job-polling is over-engineered for this volume | LOW | Direct response on same HTTP connection; no queue or polling required at v1 scale |
| Noise filtering: headers and footers | Repeated headers/footers pollute every chunk they appear in, degrading retrieval precision | MEDIUM | Heuristic: detect lines repeated across pages; Docling's layout model also classifies these as "header"/"footer" element types |
| Noise filtering: page numbers | Standalone page number lines are non-informative content that wastes token budget | LOW | Regex + position heuristic (short line at page top/bottom matching `^\d+$`) |
| Language detection (inferred metadata) | Consumers need language to select the right embedding model and apply correct stopwords | LOW | Use `langdetect` or `lingua` on extracted text; HIGH confidence from full-doc sample |
| Document type classification (inferred metadata) | Report vs. article vs. form vs. legal document drives chunking strategy choices downstream | MEDIUM | Heuristic or LLM-based; classify from title, structure cues, and extension |

### Differentiators (Competitive Advantage)

Features beyond table stakes that make the service meaningfully better for RAG consumers.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Section-based (heading-aware) chunking | Chunks that respect document sections are more semantically coherent than fixed-size splits; retrieval precision improves because a chunk is about one thing | MEDIUM | Walk DoclingDocument heading tree; emit one chunk per section or subsection; fall back to fixed-size when sections are absent |
| Chunk-level section title propagation | Including the containing section title in each chunk metadata improves LLM context and allows metadata filtering by topic | LOW | Extract from DoclingDocument heading hierarchy during chunking |
| PPTX ingestion | Presentations are a major document format in business contexts; slide content + speaker notes | LOW | Docling supports .pptx natively |
| XLSX ingestion | Spreadsheets contain tabular data valuable for RAG; Docling converts sheets to table blocks | MEDIUM | Table-heavy output; chunking strategy for tables needs care |
| Watermark / repeated boilerplate detection | Legal watermarks and recurring corporate disclaimers inflate every chunk; detection and stripping is a quality lever | HIGH | Requires cross-page text frequency analysis; adds significant complexity |
| Confidence score per chunk | When OCR is involved, low-confidence regions should be flagged so consumers can down-weight them | MEDIUM | Docling exposes OCR confidence scores at element level; aggregate per chunk |
| Configurable chunking strategy selection | Expose `strategy` param (fixed, section, sentence) so consumers choose the right strategy per document type | MEDIUM | Requires clean Port/Adapter separation of chunker; SelectionMaid's hexagonal design makes this natural |
| Inferred author / title metadata | Standard bibliographic fields from document metadata layer (PDF XMP/Dublin Core, DOCX core properties) | LOW | Docling extracts title and authors from document intrinsic metadata; expose in output |
| Word count and character count per chunk | Cheap metadata fields that help consumers implement token budget guards and size-based retrieval filters | LOW | Trivial to compute; add to schema at zero extraction cost |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem valuable but introduce disproportionate complexity or scope creep for this service.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Vector embedding generation | "One service that does it all" sounds convenient | Embedding model choice is tightly coupled to the vector database and retrieval query strategy — SelectionMaid must not own this decision; it would bind the service to a specific model | Return clean Markdown chunks; let the consumer embed with their chosen model |
| Vector database insertion | End-to-end pipeline simplicity | Out of scope by design; SelectionMaid's contract is chunks-out, not indexed-into-store; every vector DB has a different API; this would require maintaining adapters for Qdrant, Pinecone, Weaviate, pgvector, etc. | Consumer calls their DB's insertion API with the chunks they receive |
| Asynchronous job queue (Celery/RQ) | Needed for high-throughput batch ingest | Adds infrastructure dependency (Redis/RabbitMQ), worker management, and polling endpoint complexity that is unjustified at on-demand low-traffic volume | Synchronous response; revisit only if p95 latency exceeds acceptable threshold |
| LLM-based semantic chunking | Best retrieval precision in theory | Each chunk requires an LLM API call for boundary detection; 10–100x cost and latency increase; a February 2026 benchmark showed recursive 512-token splitting at 69% accuracy outperforming LLM semantic chunking at 54% | Section-based chunking + configurable overlap achieves >90% of the benefit at 1/100th the cost |
| UI / dashboard | Visibility into what was ingested | Fully out of scope; SelectionMaid is a headless API; a UI belongs in the orchestration layer that consumes it | Expose `GET /health` and structured JSON responses; consumers build their own dashboards |
| Authentication and authorization | Security | Auth is infrastructure-level (API gateway, reverse proxy, service mesh); baking it into the extraction service couples security policy to extraction logic | Deploy behind an API gateway or reverse proxy that handles auth |
| Document deduplication | Avoid re-ingesting the same file | Requires persistent state and a hash store; SelectionMaid is stateless by design; dedup belongs in the orchestration layer | Consumer tracks `doc_id` (content hash) and skips re-submission |
| Real-time streaming of chunks as they are extracted | Low latency first-chunk delivery | Docling processes documents in a blocking batch; true streaming requires re-architecting the extraction model; complexity far exceeds benefit for typical document sizes | Return full chunk list synchronously; typical docs process in 1–20 seconds |
| Named-entity extraction per chunk | Structured entity metadata for advanced filtering | Requires NLP model (spaCy/GLiNER); adds significant inference latency and a new dependency; NER belongs in the enrichment layer downstream | Return raw chunk text; let consumer run their NER pipeline on the extracted Markdown |
| Automatic chunking strategy selection based on content | "Smart" strategy selection | Requires content classification before chunking; adds latency and a new inference step; strategy choice is a consumer decision that depends on their retrieval setup | Expose `strategy` param; consumer selects; default to section-based with fixed-size fallback |

---

## Feature Dependencies

```
[PDF ingestion]
    └──requires──> [Text extraction (Docling adapter)]
                       └──requires──> [Markdown output]
                                          └──enables──> [Section-based chunking]
                                                            └──requires──> [Heading hierarchy preservation]

[Image ingestion]
    └──requires──> [OCR pipeline (Docling + EasyOCR/Tesseract)]
                       └──enables──> [Confidence score per chunk]

[Fixed-size chunking]
    └──enables──> [Chunk overlap / sliding window]

[Section-based chunking]
    └──requires──> [Heading hierarchy preservation]
    └──enables──> [Chunk-level section title propagation]

[Any chunking strategy]
    └──requires──> [Source document identifier (doc_id)]
    └──requires──> [Chunk index within document]
    └──produces──> [Page-number metadata per chunk]

[Language detection]
    └──requires──> [Text extraction] (needs extracted text corpus)

[Document type classification]
    └──requires──> [Text extraction] (needs title, structure signals)

[Confidence score per chunk]
    └──requires──> [OCR pipeline]
    └──requires──> [Image ingestion]
```

### Dependency Notes

- **Section-based chunking requires Heading hierarchy preservation:** Docling's DoclingDocument model exposes heading levels natively; the chunker must consume that tree, not flat text.
- **Chunk overlap enhances fixed-size chunking:** Overlap is a modifier applied on top of a base chunking strategy; it does not work independently.
- **Language detection requires extracted text:** Language detection runs on the extracted corpus, not raw bytes; must follow extraction.
- **Confidence scores require OCR path:** Confidence is only meaningful when OCR was involved; native-text PDFs do not have character-level confidence scores.
- **Image ingestion and OCR conflict with synchronous latency expectations:** OCR on complex multi-page documents can exceed 30 seconds; consumers must be warned in API documentation and given the option to disable OCR via a request param.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed for the service to be usable by a RAG pipeline consumer.

- [ ] PDF ingestion via HTTP POST (multipart/form-data) — core use case; everything else is secondary
- [ ] DOCX ingestion — second most common enterprise format; Docling supports it at zero marginal cost
- [ ] HTML ingestion — third most common; also zero marginal cost given Docling support
- [ ] Image ingestion with OCR — required for scanned-document workflows; accept latency tradeoff
- [ ] Markdown output with heading hierarchy, tables, and lists preserved — the entire value of the service
- [ ] Noise filtering: headers, footers, and page numbers — without this, every chunk is polluted
- [ ] Fixed-size chunking with configurable `chunk_size` and `overlap` — baseline strategy; must work reliably
- [ ] Section-based chunking as default when headings are present — the differentiating default; better than fixed-size for most documents
- [ ] `DocumentChunk` schema: `chunk_id`, `doc_id`, `text`, `chunk_index`, `total_chunks`, `page_start`, `page_end`, `section_title`, `source_filename`, `word_count`, `char_count` — stable consumer contract
- [ ] Document-level metadata: `doc_id`, `source_filename`, `language`, `doc_type`, `title`, `author`, `page_count`, `chunk_count` — bibliographic context for downstream use
- [ ] `GET /health` — liveness check for deployment orchestration

### Add After Validation (v1.x)

Features to add once the core extraction pipeline is proven stable.

- [ ] PPTX and XLSX ingestion — Docling supports both; add when consumers request them
- [ ] Chunk-level confidence scores — add when OCR workflows are the primary use case
- [ ] Configurable chunking strategy selection via request param — add when consumers need to tune strategy per document type
- [ ] Inferred author and title from document intrinsic metadata — Docling exposes these; wire through to schema

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Watermark and repeated boilerplate detection — high complexity, niche benefit; add when consumers report specific quality problems
- [ ] Sentence-level chunking — useful for short-answer retrieval; add only if section-based + fixed-size proves insufficient
- [ ] Batch document upload (multiple files per request) — add when a consumer needs bulk ingest; not needed for on-demand use

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| PDF ingestion | HIGH | MEDIUM | P1 |
| DOCX ingestion | HIGH | LOW | P1 |
| HTML ingestion | MEDIUM | LOW | P1 |
| Image + OCR | HIGH | HIGH | P1 |
| Markdown output with structure | HIGH | LOW | P1 |
| Noise filtering (headers/footers/page numbers) | HIGH | MEDIUM | P1 |
| Fixed-size chunking + overlap | HIGH | LOW | P1 |
| Section-based chunking | HIGH | MEDIUM | P1 |
| `DocumentChunk` schema with page/section metadata | HIGH | LOW | P1 |
| Document-level metadata (language, type, title, author) | MEDIUM | LOW | P1 |
| `GET /health` | LOW | LOW | P1 |
| PPTX ingestion | MEDIUM | LOW | P2 |
| XLSX ingestion | MEDIUM | MEDIUM | P2 |
| Chunk confidence scores | MEDIUM | MEDIUM | P2 |
| Configurable chunking strategy param | HIGH | MEDIUM | P2 |
| Watermark detection | LOW | HIGH | P3 |
| Sentence-level chunking | MEDIUM | MEDIUM | P3 |
| Batch file upload | MEDIUM | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | Unstructured.io | LlamaParse | Docling (OSS) | SelectionMaid approach |
|---------|-----------------|------------|---------------|------------------------|
| PDF ingestion | Yes | Yes | Yes | Yes — primary use case |
| DOCX/PPTX/XLSX | Yes (SaaS tier) | Yes (90+ formats) | Yes | Yes (DOCX v1; PPTX/XLSX v1.x) |
| HTML ingestion | Yes | Yes | Yes | Yes |
| Image + OCR | Yes (strong) | Yes | Yes (EasyOCR/Tesseract) | Yes |
| Table extraction | 75% on complex tables | Handles multi-page tables | 97.9% on complex tables | Yes — Docling's TableFormer is best-in-class |
| Markdown output | Yes | Yes | Yes (primary export) | Yes — primary output format |
| Section-based chunking | Partial (element types) | No (fixed-size by default) | Via chunker extension | Yes — default when headings detected |
| Metadata extraction | Yes | Yes | Yes (title, author, language) | Yes |
| Chunk confidence scores | No | No | Yes (OCR path) | v1.x |
| Hexagonal / swappable extractors | No | No | N/A (it is the extractor) | Yes — core architectural constraint |
| SOC 2 / HIPAA compliance | Yes (enterprise tier) | Yes (enterprise) | N/A (OSS) | Out of scope (auth is infra) |
| Self-hosted / air-gapped | Partial | No | Yes | Yes — no cloud dependency |
| Pricing | Usage-based SaaS | Usage-based SaaS | Free (OSS) | Free (OSS self-hosted) |

**Key competitive insight:** Unstructured and LlamaParse are SaaS products with vendor lock-in. Docling is the best open-source extractor but provides no API layer — SelectionMaid's value is wrapping Docling in a stable, tested, hexagonally-structured HTTP service with opinionated chunking defaults.

---

## DocumentChunk Schema (Production Reference)

This is the target schema for SelectionMaid's primary output object, synthesized from production RAG system patterns:

```python
class DocumentChunk(BaseModel):
    # Identity
    chunk_id: str          # Stable hash: sha256(doc_id + str(chunk_index))[:16]
    doc_id: str            # Stable hash: sha256(file_bytes)[:16] or UUID on upload

    # Content
    text: str              # Markdown-formatted chunk content
    word_count: int        # len(text.split())
    char_count: int        # len(text)

    # Position
    chunk_index: int       # 0-based position of this chunk within the document
    total_chunks: int      # Total number of chunks in this document

    # Source location (for citation)
    page_start: int | None # First page this chunk's content originates from (1-based)
    page_end: int | None   # Last page this chunk's content originates from (1-based)
    section_title: str | None  # Title of the containing section (from heading hierarchy)

    # Source document
    source_filename: str   # Original filename as uploaded

    # Quality signal (OCR path only)
    ocr_confidence: float | None  # Mean character-level confidence [0.0, 1.0]; null for native-text
```

```python
class DocumentMetadata(BaseModel):
    doc_id: str
    source_filename: str
    title: str | None       # From PDF XMP / DOCX core properties / inferred from first heading
    author: str | None      # From document intrinsic metadata
    language: str | None    # ISO 639-1 code, e.g. "en", "pt", "de"
    doc_type: str | None    # Inferred: "article", "report", "presentation", "form", "legal", "other"
    page_count: int | None  # Total pages (null for HTML/Markdown which have no pages)
    chunk_count: int        # Total number of chunks produced
    ingested_at: str        # ISO 8601 UTC timestamp
```

```python
class IngestionResponse(BaseModel):
    metadata: DocumentMetadata
    chunks: list[DocumentChunk]
```

---

## Sources

- [IBM Data Ingestion for RAG Cookbook](https://www.ibm.com/think/architectures/rag-cookbook/data-ingestion) — metadata field standards
- [Docling supported formats (official docs)](https://docling-project.github.io/docling/usage/supported_formats/) — HIGH confidence, official source
- [Docling GitHub](https://github.com/docling-project/docling) — HIGH confidence, official source
- [Unstructured.io chunking documentation](https://docs.unstructured.io/open-source/core-functionality/chunking) — element-type chunk patterns
- [Associating Metadata with Document Chunks (apxml.com)](https://apxml.com/courses/getting-started-rag/chapter-3-data-preparation-for-rag/chunk-metadata) — MEDIUM confidence, tutorial
- [LangChain: A Chunk by Any Other Name](https://blog.langchain.com/a-chunk-by-any-other-name/) — MEDIUM confidence, authoritative blog
- [Qdrant chunking strategies course](https://qdrant.tech/course/essentials/day-1/chunking-strategies/) — MEDIUM confidence
- [Firecrawl: Best Chunking Strategies for RAG 2026](https://www.firecrawl.dev/blog/best-chunking-strategies-rag) — MEDIUM confidence
- [Langcopilot: 9 Chunking Strategies Tested 2025](https://langcopilot.com/posts/2025-10-11-document-chunking-for-rag-practical-guide) — MEDIUM confidence
- [Milvus: Max-Min Semantic Chunking](https://milvus.io/blog/embedding-first-chunking-second-smarter-rag-retrieval-with-max-min-semantic-chunking.md) — MEDIUM confidence
- [Reducto: Document Parser Comparison (Docling vs LlamaParse vs Unstructured)](https://llms.reducto.ai/document-parser-comparison) — MEDIUM confidence
- [Procycons: PDF Extraction Benchmark 2025](https://procycons.com/en/blogs/pdf-data-extraction-benchmark/) — MEDIUM confidence
- [Elastic: Advanced RAG Techniques Part 1](https://www.elastic.co/search-labs/blog/advanced-rag-techniques-part-1) — MEDIUM confidence
- [Stack Overflow: Breaking up is hard to do (chunking in RAG)](https://stackoverflow.blog/2024/12/27/breaking-up-is-hard-to-do-chunking-in-rag-applications/) — MEDIUM confidence
- [Azure RAG enrichment phase guide](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-enrichment-phase) — MEDIUM confidence, official Microsoft docs
- [Unstructured: Common Challenges in RAG](https://unstructured.io/insights/rag-pipeline-challenges-from-data-ingestion-to-retrieval) — MEDIUM confidence

---

*Feature research for: Document extraction and normalization service (RAG ingestion pipeline)*
*Researched: 2026-05-23*
