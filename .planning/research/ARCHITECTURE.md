# Architecture Research

**Domain:** Document extraction / RAG ingestion service — hexagonal (ports & adapters)
**Researched:** 2026-05-23
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
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
│  │   extract(file: bytes, mime: str) → ExtractionResult       │   │
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
|-----------|----------------|------------------------|
| FastAPI router | HTTP boundary: accept file upload, return JSON | `APIRouter` with `UploadFile`, calls `ExtractionService` |
| Pydantic schemas | HTTP contract: request/response shapes, validation | `BaseModel` classes in `adapters/http/schemas.py` |
| ExtractionService | Orchestrate the full pipeline: extract → filter → chunk → enrich | Plain Python class, injected with 4 port instances |
| ExtractorPort | Contract: `extract(data, mime) → RawDocument` | `typing.Protocol` with one required method |
| FilterPort | Contract: `filter(raw) → RawDocument` (noise removed) | `typing.Protocol` |
| ChunkerPort | Contract: `chunk(doc) → list[DocumentChunk]` | `typing.Protocol` |
| MetadataEnricherPort | Contract: `enrich(chunk, doc) → DocumentChunk` | `typing.Protocol` |
| DoclingAdapter | Wraps `docling.DocumentConverter`; satisfies ExtractorPort | Concrete class; Docling is a private implementation detail |
| HeuristicFilter | Header/footer/page-number removal heuristics; satisfies FilterPort | Concrete class using regex/positional rules |
| MarkdownChunker | Splits Markdown at heading boundaries + token count; satisfies ChunkerPort | Concrete class; uses `tiktoken` or `len()` |
| MetadataEnricher | Infers language, doc type, date, author; satisfies MetadataEnricherPort | Concrete class using `langdetect` or similar |
| Composition root | Creates concrete adapters; wires them into service; mounts router | `app/main.py` — the only place all layers touch |
| Domain models | Immutable data containers with no framework dependencies | `@dataclass(frozen=True, slots=True)` |

## Recommended Project Structure

```
src/
└── selectionmaid/
    ├── domain/                    # Pure Python, zero external deps
    │   ├── __init__.py
    │   ├── models.py              # RawDocument, DocumentChunk, DocumentMetadata, ExtractionResult
    │   └── ports.py               # ExtractorPort, FilterPort, ChunkerPort, MetadataEnricherPort
    │
    ├── application/               # Orchestration only — depends on domain, not on adapters
    │   ├── __init__.py
    │   └── extraction_service.py  # ExtractionService
    │
    ├── adapters/
    │   ├── __init__.py
    │   ├── extractor/
    │   │   ├── __init__.py
    │   │   └── docling_adapter.py     # DoclingAdapter implements ExtractorPort
    │   ├── filter/
    │   │   ├── __init__.py
    │   │   └── heuristic_filter.py    # HeuristicFilter implements FilterPort
    │   ├── chunker/
    │   │   ├── __init__.py
    │   │   └── markdown_chunker.py    # MarkdownChunker implements ChunkerPort
    │   ├── enricher/
    │   │   ├── __init__.py
    │   │   └── metadata_enricher.py   # MetadataEnricher implements MetadataEnricherPort
    │   └── http/
    │       ├── __init__.py
    │       ├── router.py              # APIRouter — FastAPI input adapter
    │       └── schemas.py             # Pydantic request/response models
    │
    └── main.py                    # Composition root: wires everything, creates FastAPI app
```

### Structure Rationale

- **domain/:** No framework imports allowed. `models.py` + `ports.py` are the only files other layers must import from. This constraint enforces the dependency rule.
- **application/:** Imports only from `domain/`. The service receives port instances at construction time — it never imports a concrete adapter.
- **adapters/:** Each subdirectory is one adapter family. Adding a new extractor backend means adding a file here; zero changes to domain or application layers.
- **adapters/http/:** FastAPI is treated as infrastructure. Schemas here are never imported by the service — they exist only to translate HTTP concepts into domain calls and back.
- **main.py as composition root:** The only file that imports both application and adapter layers simultaneously. This is where you instantiate `DoclingAdapter()`, pass it to `ExtractionService(extractor=...)`, and mount the router. In tests you substitute mock adapters here.

## Architectural Patterns

### Pattern 1: Protocol as Port Definition

**What:** Define each port as a `typing.Protocol`. Adapters satisfy the port structurally — no inheritance required.

**When to use:** Always, for ports that external libraries implement or that you want third-party code to satisfy without subclassing.

**Trade-offs:** Static type checkers (mypy, pyright) enforce correctness at check time; runtime `isinstance` checks require `@runtime_checkable` (checks only method presence, not signatures). ABCs give runtime enforcement of abstract methods — use ABC when you want a `TypeError` at instantiation time if someone forgets to implement a method.

**Recommendation:** Use `Protocol` for all four ports (ExtractorPort, FilterPort, ChunkerPort, MetadataEnricherPort). The `DoclingAdapter` never needs to inherit from `ExtractorPort` — it just needs to have the right method signatures. This is especially important for wrapping third-party libraries you cannot modify.

**Example:**
```python
# src/selectionmaid/domain/ports.py
from typing import Protocol
from .models import RawDocument, DocumentChunk, ExtractionResult

class ExtractorPort(Protocol):
    def extract(self, data: bytes, mime_type: str) -> RawDocument: ...

class FilterPort(Protocol):
    def filter(self, document: RawDocument) -> RawDocument: ...

class ChunkerPort(Protocol):
    def chunk(self, document: RawDocument) -> list[DocumentChunk]: ...

class MetadataEnricherPort(Protocol):
    def enrich(self, chunk: DocumentChunk) -> DocumentChunk: ...
```

### Pattern 2: Frozen Dataclass Domain Models

**What:** All domain objects are `@dataclass(frozen=True, slots=True)`. No Pydantic, no ORM, no framework dependency in the domain layer.

**When to use:** Always for objects that cross layer boundaries (from adapter → service, from service → adapter).

**Trade-offs:** `frozen=True` makes objects hashable and prevents accidental mutation, catching a whole class of bugs. `slots=True` (Python 3.10+, available in 3.13) reduces memory overhead. Pydantic is *not* used in domain models to avoid coupling the domain to a validation framework — Pydantic is confined to `adapters/http/schemas.py`.

**Example:**
```python
# src/selectionmaid/domain/models.py
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True, slots=True)
class DocumentMetadata:
    source_filename: str
    mime_type: str
    language: str | None = None
    title: str | None = None
    author: str | None = None
    detected_at: str | None = None        # ISO-8601 string; no datetime to avoid TZ complexity
    extra: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True, slots=True)
class RawDocument:
    """Intermediate: extracted text before chunking."""
    content_markdown: str                  # Docling exports to Markdown
    metadata: DocumentMetadata
    page_count: int | None = None

@dataclass(frozen=True, slots=True)
class DocumentChunk:
    chunk_id: str                          # deterministic: f"{source_filename}-{index}"
    text: str
    index: int                             # position within source document
    token_count: int
    heading_path: list[str]               # ["Section 1", "Subsection 1.2"] — breadcrumb
    metadata: DocumentMetadata

@dataclass(frozen=True, slots=True)
class ExtractionResult:
    chunks: list[DocumentChunk]
    source_metadata: DocumentMetadata
    total_chunks: int
    filtered_page_count: int | None = None
```

### Pattern 3: Composition Root / Manual DI via Constructor Injection

**What:** The application service receives concrete adapter instances through its constructor. The composition root (`main.py`) is the only place that instantiates adapters and wires them together.

**When to use:** Always. No DI framework (dependency-injector, lagom, inject) is needed for a service with four well-known ports. The overhead of a DI container exceeds its value here.

**Trade-offs:** Explicit, traceable, zero magic. Adapters are swapped by changing one line in `main.py`. In tests, you replace one argument with a mock.

**Example:**
```python
# src/selectionmaid/application/extraction_service.py
from ..domain.ports import ExtractorPort, FilterPort, ChunkerPort, MetadataEnricherPort
from ..domain.models import ExtractionResult

class ExtractionService:
    def __init__(
        self,
        extractor: ExtractorPort,
        filter_: FilterPort,
        chunker: ChunkerPort,
        enricher: MetadataEnricherPort,
    ) -> None:
        self._extractor = extractor
        self._filter = filter_
        self._chunker = chunker
        self._enricher = enricher

    def extract(self, data: bytes, mime_type: str, source_filename: str) -> ExtractionResult:
        raw = self._extractor.extract(data, mime_type)
        filtered = self._filter.filter(raw)
        chunks = self._chunker.chunk(filtered)
        enriched = [self._enricher.enrich(c) for c in chunks]
        return ExtractionResult(
            chunks=enriched,
            source_metadata=raw.metadata,
            total_chunks=len(enriched),
        )
```

```python
# src/selectionmaid/main.py  — Composition Root
from fastapi import FastAPI
from .adapters.extractor.docling_adapter import DoclingAdapter
from .adapters.filter.heuristic_filter import HeuristicFilter
from .adapters.chunker.markdown_chunker import MarkdownChunker
from .adapters.enricher.metadata_enricher import MetadataEnricher
from .application.extraction_service import ExtractionService
from .adapters.http.router import build_router

def create_app() -> FastAPI:
    service = ExtractionService(
        extractor=DoclingAdapter(),
        filter_=HeuristicFilter(),
        chunker=MarkdownChunker(max_tokens=512, overlap_tokens=64),
        enricher=MetadataEnricher(),
    )
    app = FastAPI(title="SelectionMaid")
    app.include_router(build_router(service))
    return app

app = create_app()
```

### Pattern 4: FastAPI as Input Adapter — Router Factory

**What:** The HTTP router does not instantiate the service itself. It receives a pre-built service instance and closes over it. This keeps the router ignorant of which concrete adapters are wired in.

**When to use:** Always with hexagonal FastAPI. Avoids the trap of using `Depends(get_service)` factory functions that re-instantiate adapters per request.

**Trade-offs:** Simple and predictable. The router is a thin translation layer: HTTP request → domain call → HTTP response. No business logic leaks into route handlers. In tests, `app.dependency_overrides` is unused because there are no Depends-based factories to override — you simply call `create_app()` with mock service.

**Example:**
```python
# src/selectionmaid/adapters/http/router.py
from fastapi import APIRouter, UploadFile, HTTPException
from ...application.extraction_service import ExtractionService
from .schemas import ExtractionResponse

def build_router(service: ExtractionService) -> APIRouter:
    router = APIRouter(prefix="/v1")

    @router.post("/extract", response_model=ExtractionResponse)
    async def extract(file: UploadFile) -> ExtractionResponse:
        data = await file.read()
        mime = file.content_type or "application/octet-stream"
        try:
            result = service.extract(data, mime, file.filename or "unknown")
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        return ExtractionResponse.from_domain(result)

    return router
```

### Pattern 5: DoclingAdapter — Wrapping a Third-Party Library

**What:** The adapter hides all Docling-specific concepts behind the `ExtractorPort` interface. `DoclingDocument`, pipeline options, format-specific config — all private to the adapter file.

**When to use:** For any third-party library that should be swappable (Docling, pdfplumber, unstructured, etc.).

**Trade-offs:** The domain never sees Docling imports. Swapping to a different library requires only rewriting this one adapter. The adapter is the *only* file that changes when Docling's API changes.

**Example:**
```python
# src/selectionmaid/adapters/extractor/docling_adapter.py
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from ...domain.models import RawDocument, DocumentMetadata
import io

class DoclingAdapter:
    def __init__(self) -> None:
        options = PdfPipelineOptions(do_ocr=True, do_table_structure=True)
        self._converter = DocumentConverter(
            format_options={"pdf": PdfFormatOption(pipeline_options=options)}
        )

    def extract(self, data: bytes, mime_type: str) -> RawDocument:
        # Docling accepts file paths or streams — wrap bytes in BytesIO
        result = self._converter.convert(io.BytesIO(data))
        markdown = result.document.export_to_markdown()
        page_count = getattr(result.document, "num_pages", None)
        metadata = DocumentMetadata(
            source_filename="unknown",   # caller patches this upstream
            mime_type=mime_type,
            page_count=page_count,
        )
        return RawDocument(content_markdown=markdown, metadata=metadata, page_count=page_count)
```

## Data Flow

### Request Flow

```
HTTP POST /v1/extract (multipart/form-data)
    │
    ▼
FastAPI router (adapters/http/router.py)
    │  reads UploadFile → bytes + mime_type
    │
    ▼
ExtractionService.extract(data, mime_type, filename)
    │
    ├─→ ExtractorPort.extract(data, mime_type)
    │       └─→ DoclingAdapter → Docling DocumentConverter
    │               └─→ RawDocument(content_markdown, metadata)
    │
    ├─→ FilterPort.filter(raw_document)
    │       └─→ HeuristicFilter → strips headers/footers/page numbers
    │               └─→ RawDocument (cleaned)
    │
    ├─→ ChunkerPort.chunk(filtered_document)
    │       └─→ MarkdownChunker → splits at headings + token budget
    │               └─→ list[DocumentChunk]
    │
    └─→ MetadataEnricherPort.enrich(chunk) × N
            └─→ MetadataEnricher → adds language, inferred fields
                    └─→ list[DocumentChunk] (enriched)
                            └─→ ExtractionResult
    │
    ▼
ExtractionResponse.from_domain(result)   ← Pydantic schema
    │
    ▼
HTTP 200 JSON response
```

### Key Data Flows

1. **Bytes in, Markdown out (extractor):** Raw file bytes enter DoclingAdapter; Markdown text exits as `RawDocument`. Docling's internal `DoclingDocument` is never exposed outside the adapter.
2. **Markdown filtered (filter):** `RawDocument.content_markdown` is cleaned; the result is still a `RawDocument` with the same shape — the filter is a pure transformation.
3. **Chunks created (chunker):** Markdown is split at heading boundaries. Each `DocumentChunk` carries its heading breadcrumb, token count, and index for stable deterministic IDs.
4. **Metadata enriched (enricher):** Each chunk's `DocumentMetadata` is supplemented with inferred fields (language via langdetect, etc.). The enricher returns a new frozen chunk — no mutation.
5. **HTTP response (serialization):** `ExtractionResult` is translated to `ExtractionResponse` (a Pydantic model) at the HTTP boundary. Domain models are never directly serialized to JSON.

## Build Order

Build in this dependency order — each layer depends only on what is built before it:

| Step | Build | Depends On | Why First |
|------|-------|------------|-----------|
| 1 | `domain/models.py` | Nothing | All other layers import from here |
| 2 | `domain/ports.py` | `domain/models.py` | Ports reference model types; service and adapters depend on ports |
| 3 | `application/extraction_service.py` | `domain/` | Can be written and tested with mock adapters before any real adapter exists |
| 4 | Adapters (any order) | `domain/` | Each adapter satisfies a port independently; no cross-adapter deps |
| 5 | `adapters/http/schemas.py` | `domain/models.py` | HTTP schemas translate domain models; router depends on schemas |
| 6 | `adapters/http/router.py` | `application/`, `adapters/http/schemas.py` | Router needs service type annotation and response schema |
| 7 | `main.py` | Everything | Composition root wires it all; only file that imports all layers |

**Critical path:** `models.py` → `ports.py` → `extraction_service.py` → any adapter → `router.py` → `main.py`

If you need to validate the service logic early, build step 3 with a `StubExtractor` that returns a hardcoded `RawDocument`, and test the full pipeline end-to-end before touching Docling.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-100 req/day (current) | Single-process uvicorn; synchronous Docling calls are fine; no queue needed |
| 100-10k req/day | Add `asyncio.to_thread()` wrapper around Docling (it is CPU-bound, not async-native); `max_workers` uvicorn setting |
| 10k+ req/day | Introduce a task queue (Celery + Redis or ARQ); extraction becomes async; HTTP adapter returns a job ID; polling/webhook endpoint added — this only changes `adapters/http/` and adds `adapters/queue/`, not the domain |

### Scaling Priorities

1. **First bottleneck:** Docling's OCR and layout model inference is CPU-heavy and synchronous. Running it in the main async loop will block the event loop. Wrap in `asyncio.to_thread()` before traffic matters.
2. **Second bottleneck:** Memory per request scales with document size (Docling loads ML models once at startup, but intermediate representations can be large for dense PDFs). Profile before optimizing.

## Anti-Patterns

### Anti-Pattern 1: Domain Models Importing Framework Types

**What people do:** Use Pydantic `BaseModel` as domain objects directly, or use SQLAlchemy models as the entity passed between layers.

**Why it's wrong:** Couples the domain to a framework. If you swap Pydantic v1 → v2 or add an ORM, domain logic breaks. Domain objects cannot be tested without installing the framework.

**Do this instead:** Domain objects are plain `@dataclass(frozen=True)`. Pydantic schemas live only in `adapters/http/schemas.py` and have a `from_domain()` classmethod.

### Anti-Pattern 2: Service Instantiating Its Own Adapters

**What people do:** `DoclingAdapter()` called inside `ExtractionService.__init__` or as a default argument.

**Why it's wrong:** Couples the service to a concrete adapter. Tests must use real Docling; you cannot inject a mock without patching at import level.

**Do this instead:** Always inject adapters via the constructor. The service only holds protocol-typed references.

### Anti-Pattern 3: Business Logic in Route Handlers

**What people do:** Route handlers contain chunking logic, filtering conditions, or metadata inference directly.

**Why it's wrong:** The pipeline logic becomes HTTP-specific and cannot be tested without launching a FastAPI app. Re-use from a CLI adapter becomes impossible.

**Do this instead:** Route handlers are 5-10 lines: read HTTP input → call service → serialize result → return response.

### Anti-Pattern 4: Leaking Docling Types Across the Adapter Boundary

**What people do:** Return `DoclingDocument` from the adapter, pass it to the service, import `docling` in `extraction_service.py`.

**Why it's wrong:** The domain now depends on Docling. Swapping extractor requires changes in the service.

**Do this instead:** The adapter converts `DoclingDocument` → `RawDocument` internally before returning. Only `RawDocument` exits the adapter.

### Anti-Pattern 5: One Giant Adapter Doing Extraction + Filtering + Chunking

**What people do:** Build a `DoclingPipelineAdapter` that does all four steps internally because "Docling already does some chunking."

**Why it's wrong:** You lose independent replaceability. You cannot swap the chunking strategy without touching the extractor. Docling's internal chunking is not tuned for RAG token budgets.

**Do this instead:** Keep the four ports separate even if the initial implementations are simple. The boundary pays off when you need to tune chunking independently of the extraction backend.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Docling | Wrapped by `DoclingAdapter`; Docling's `DocumentConverter` initialized once in `__init__` | Docling loads ML models at startup; keep adapter as a singleton for performance |
| langdetect / lingua | Wrapped by `MetadataEnricher`; no port-level dependency on specific library | lingua-py is faster and more accurate than langdetect for short text; either satisfies the port |
| tiktoken / tokenizers | Used by `MarkdownChunker` for accurate token counting | Use `tiktoken` for OpenAI-compatible token counts; use simple `len(text.split())` × 1.3 as a fast approximation |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| HTTP adapter ↔ ExtractionService | Direct method call; `ExtractionService` is passed into router factory | Not async internally — wrap in `asyncio.to_thread()` if needed |
| ExtractionService ↔ Ports | Protocol method calls; adapters injected at construction | Service holds protocol-typed references, not concrete types |
| Domain models ↔ HTTP schemas | `ExtractionResponse.from_domain(result)` class method | One-way translation at the adapter boundary; domain models never serialized directly |
| Adapters ↔ Domain | Adapters import from `domain/models.py` and `domain/ports.py` only | `domain/` is the only shared vocabulary; adapters never import each other |

## Sources

- AWS Prescriptive Guidance: [Structure a Python project in hexagonal architecture using AWS Lambda](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/structure-a-python-project-in-hexagonal-architecture-using-aws-lambda.html) — HIGH confidence
- Python typing docs: [Protocols and structural subtyping](https://typing.python.org/en/latest/reference/protocols.html) — HIGH confidence
- Python typing spec: [PEP 544 — Protocols: Structural subtyping](https://peps.python.org/pep-0544/) — HIGH confidence
- Docling reference: [DocumentConverter API](https://docling-project.github.io/docling/reference/document_converter/) — HIGH confidence
- FastAPI docs: [Testing Dependencies with Overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/) — HIGH confidence
- Szymon Miks: [Hexagonal architecture in Python](https://blog.szymonmiks.pl/p/hexagonal-architecture-in-python/) — MEDIUM confidence
- Zaur Nasibov: [Hexagonal architecture and Python - Part III: Composition root](https://www.zaurnasibov.com/posts/2022/12/31/hexarch_di_python_part_3.html) — MEDIUM confidence
- DEV Community: [Hexagonal Architecture in Python — wiring, DI, application layer](https://dev.to/elpic/hexagonal-architecture-in-python-wiring-adapters-dependency-injection-and-the-application-layer-61l) — MEDIUM confidence
- Stanza: [Protocols vs Abstract Base Classes](https://www.stanza.dev/courses/python-architecture/protocols/python-architecture-protocols-vs-abc) — MEDIUM confidence
- GitHub: [marcosvs98/hexagonal-architecture-with-python (FastAPI example)](https://github.com/marcosvs98/hexagonal-architecture-with-python) — MEDIUM confidence

---
*Architecture research for: SelectionMaid — document extraction / RAG ingestion service*
*Researched: 2026-05-23*
