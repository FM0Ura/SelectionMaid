# Stack Research

**Domain:** Python document extraction + normalization service for RAG ingestion pipelines
**Researched:** 2026-05-23
**Confidence:** HIGH (core stack) / MEDIUM (version-specific details cross-verified via PyPI + official docs)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.13+ | Runtime | Constraint set by project; supported by Docling since v2.18.0; full support confirmed current |
| Docling | >=2.95 (latest) | Primary document extraction engine | Best-in-class structural preservation (DocLayNet + TableFormer AI models); native multi-format support; first-class Markdown + JSON export; MIT licensed; now LF AI & Data Foundation incubating project |
| FastAPI | >=0.115 | HTTP input adapter (Port) | Native async; UploadFile/SpooledTemporaryFile for streaming file upload; lifespan events for DocumentConverter singleton; OpenAPI auto-docs; de facto standard for Python ML/data APIs |
| Pydantic | v2 (bundled with FastAPI >=0.100) | Response schema, input validation | Rust-backed core; 5-50x faster than v1; `response_model` enforces chunk+metadata output schema; `model_config` with `from_attributes=True` for domain object mapping |
| uvicorn | >=0.30 | ASGI server | Standard ASGI runner for FastAPI; supports `--reload` in development |
| python-multipart | >=0.0.9 | Multipart form data parsing | Required by FastAPI for `UploadFile`; installed as a transitive dependency but must be explicit |

### Extraction Engine Details

**Docling 2.x architecture:**

- `DocumentConverter` — main entry point; accepts `allowed_formats` and `format_options` dict
- `PipelineOptions` — per-format pipeline configuration (OCR, image scale, table mode)
- `FormatOption` — bundles pipeline class + options + backend per format
- `DoclingDocument` — unified internal representation; exposes `export_to_markdown()`, `export_to_json()`, `export_to_html()`
- `HybridChunker` — Docling's own tokenization-aware chunker; the correct choice for this project (see Chunking section)

**Supported input formats (HIGH confidence — official docs):**

| Format | Notes |
|--------|-------|
| PDF | Native text extraction via docling-parse; OCR for scanned |
| DOCX | Full support; preserves heading structure |
| PPTX | Supported |
| XLSX | Supported |
| HTML | Supported |
| Images (PNG, TIFF, JPEG, BMP, WebP) | OCR pipeline |
| LaTeX | Supported |
| Plain text | Supported |
| AsciiDoc | Supported |
| Audio (WAV, MP3) / WebVTT | Via optional extras (out of scope for SelectionMaid v1) |

**OCR engines available via `PipelineOptions`:**

| Engine | Class | Notes |
|--------|-------|-------|
| EasyOCR | `EasyOcrOptions` | Default if GPU available; multilingual |
| Tesseract | `TesseractOcrOptions` | Best for CPU-only; auto language detection supported |
| Tesseract CLI | `TesseractCliOcrOptions` | When Tesseract binary is in PATH |
| RapidOCR | `RapidOcrOptions` | CPU (onnxruntime) or GPU (torch); fastest on CPU |
| macOS OCR | `OcrMacOptions` | macOS only |

**Recommendation:** Use `TesseractOcrOptions` for CPU-only server deployments (matches the low-traffic on-demand constraint). RapidOCR if throughput matters later.

### Docling Markdown Export — Known Limitation

MEDIUM confidence — confirmed via GitHub issues:

`export_to_markdown()` currently exports all headings as H2 (`##`) regardless of their original nesting depth. The Docling team plans to fix this using TOC information from docling-parse, but as of current versions it is an **open bug** (#1023). The `DoclingDocument` internal tree does preserve hierarchy; the serialization loses it.

**Workaround:** Walk the document tree programmatically via `DoclingDocument.body.children` to emit H1/H2/H3 correctly in a custom serializer, or accept H2-flat output as sufficient for embedding quality (retrieval is not sensitive to heading depth; LLMs parse flat Markdown well).

**Decision for SelectionMaid:** Accept H2-flat output initially. The hexagonal `ExporterPort` design means a custom serializer can be dropped in without touching the service core when upstream fixes this.

### Chunking

**Use Docling's own `HybridChunker`. Do not use LangChain text splitters for this service.**

Rationale:

- `HybridChunker` is structure-aware: it starts from Docling's hierarchical chunker and applies tokenizer-aware split/merge passes
- It preserves heading context in chunk metadata via `contextualize()` — essential for RAG retrieval quality
- It avoids mid-sentence splits and mid-table splits by design
- `merge_peers=True` (default) merges undersized consecutive chunks that share the same heading scope
- `repeat_table_header=True` (default) repeats table headers when a table spans multiple chunks
- LangChain's `RecursiveCharacterTextSplitter` is character-aware, not structure-aware — it would destroy the document hierarchy that Docling worked to extract

**HybridChunker instantiation:**

```python
from docling.chunking import HybridChunker

# Default: uses internal tokenizer, sensible defaults
chunker = HybridChunker()
chunks = list(chunker.chunk(dl_doc=result.document))

# With explicit HuggingFace tokenizer (optional, for token-budget control)
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer

chunker = HybridChunker(
    tokenizer=HuggingFaceTokenizer(
        tokenizer=AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2"),
        max_tokens=256,
    )
)
```

For SelectionMaid v1, the default instantiation is sufficient since chunk size configuration is a caller concern, not a service concern.

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-multipart | >=0.0.9 | Multipart form parsing (UploadFile) | Always — required by FastAPI for file uploads |
| uvicorn | >=0.30 | ASGI server | Run in production and dev |
| pytest | >=8.0 | Test runner | All tests |
| pytest-asyncio | >=0.23 | Async test support | Needed for `async def` endpoint tests |
| httpx | >=0.27 | HTTP client for FastAPI TestClient | `AsyncClient` for async endpoint tests; `TestClient` for sync |
| anyio | >=4.0 | Async I/O abstraction | Pulled in by FastAPI; needed for `pytest-asyncio` compatibility |
| langdetect | >=1.0.9 | Language detection for metadata enrichment | Metadata enrichment phase; optional dependency |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Dependency management, venv, lockfile, Python version pinning | Replace pip entirely; `uv add`, `uv sync`, `uv run`; 10-100x faster than pip; handles torch CPU/GPU variants via `--extra-index-url` in `tool.uv` config |
| ruff | Linting + formatting | Replaces black + isort + flake8; zero-config with pyproject.toml `[tool.ruff]` |
| mypy | Static type checking | Use `strict = true` in `[tool.mypy]`; Docling and FastAPI are fully typed |
| pytest-cov | Coverage reporting | `--cov=src --cov-report=term-missing` |

---

## Installation

```toml
# pyproject.toml (uv-managed)
[project]
name = "selection-maid"
requires-python = ">=3.13"
dependencies = [
    "docling>=2.95",
    "fastapi>=0.115",
    "uvicorn>=0.30",
    "python-multipart>=0.0.9",
    "pydantic>=2.7",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "httpx>=0.27",
    "pytest-cov>=5.0",
    "ruff>=0.4",
    "mypy>=1.10",
]

[tool.uv]
# For CPU-only servers, override torch to CPU wheel:
# uv add --extra-index-url https://download.pytorch.org/whl/cpu torch
```

```bash
# Install core + dev deps
uv sync --extra dev

# CPU-only torch (avoids 2GB CUDA download on servers)
uv add --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision

# Run tests
uv run pytest

# Run dev server
uv run uvicorn selection_maid.api.app:app --reload
```

**Warning:** Docling's default install pulls the full CUDA-enabled PyTorch (~2GB). For CI and CPU-only deployments, always add `--extra-index-url https://download.pytorch.org/whl/cpu`. Docling also downloads AI models (DocLayNet layout model, TableFormer) on first run — pre-warm the cache in Docker builds with `python -c "from docling.document_converter import DocumentConverter; DocumentConverter()"`.

**Modular install note:** From Docling v2.92.0, a `docling-slim` meta-package exists with minimal dependencies (~50MB). For SelectionMaid, use full `docling` (standard extras) since PDF + table recognition is core functionality.

---

## FastAPI Patterns for This Service

### DocumentConverter Singleton via Lifespan

`DocumentConverter` initialization is expensive (model loading). Use the `lifespan` event to initialize once and store in `app.state`:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from docling.document_converter import DocumentConverter

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.converter = DocumentConverter()
    yield
    # no cleanup needed for DocumentConverter

app = FastAPI(lifespan=lifespan)
```

Access in endpoints via `Request.app.state.converter` or FastAPI `Depends`.

### File Upload Pattern

```python
from fastapi import FastAPI, File, UploadFile, Request, HTTPException
import tempfile, pathlib

ALLOWED_MIME = {
    "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/html", "image/png", "image/jpeg", "image/tiff",
}

@app.post("/extract")
async def extract(request: Request, file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=415, detail=f"Unsupported media type: {file.content_type}")

    # Write to named temp file — Docling needs a real path, not a file handle
    suffix = pathlib.Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = pathlib.Path(tmp.name)

    try:
        result = request.app.state.converter.convert(tmp_path)
        # ... chunking, metadata, response
    finally:
        tmp_path.unlink(missing_ok=True)
```

**Note:** Docling's `DocumentConverter.convert()` accepts a `Path` or URL string, not a file-like object. Writing to a named temp file is the correct pattern.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Docling | unstructured-io | When strong OCR on complex layouts is the primary concern; unstructured has better OCR breadth but worse table accuracy and slower development velocity in 2024-2025 |
| Docling | pypdfium2 / pdfplumber | When speed is critical and document structure is not needed (plain text extraction only); 10x faster but no layout understanding |
| Docling | pymupdf4llm | When you need lightweight PDF-to-Markdown without AI model downloads; hits the sweet spot of speed + quality for simple/well-structured PDFs |
| Docling | LlamaParse | When accuracy on highly complex PDFs outweighs cost concerns; LlamaParse is a cloud API (paid), not embeddable |
| Docling HybridChunker | LangChain RecursiveCharacterTextSplitter | Never for this project; structure-blind splitter loses all hierarchy Docling extracted |
| Docling HybridChunker | llama-index DoclingNodeParser | Viable alternative if llama-index is already in the dependency tree; functionally similar; adds ~100MB of llama-index deps for no gain in a standalone service |
| uv | pip + pip-tools | If the environment enforces pip only; uv is the clear modern choice |
| uv | Poetry | Poetry has slower resolver and larger install overhead; uv has subsumed most of Rye's functionality and is faster; Rye's author recommends migrating to uv |
| FastAPI lifespan | @app.on_event("startup") | The `on_event` decorator is deprecated since FastAPI 0.95.0; use `lifespan` |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `@app.on_event("startup")` / `@app.on_event("shutdown")` | Deprecated since FastAPI 0.95.0; will be removed | `@asynccontextmanager` lifespan passed to `FastAPI(lifespan=...)` |
| LangChain as a chunking dependency | Pulls 200+ transitive dependencies for a text splitter; RecursiveCharacterTextSplitter is structure-blind | Docling's own `HybridChunker` |
| `pip install docling` on a CPU-only server without `--extra-index-url` | Downloads 2GB+ of CUDA-enabled PyTorch unnecessarily | `uv add --extra-index-url https://download.pytorch.org/whl/cpu torch` |
| Reading `UploadFile` directly and passing to Docling | Docling's `convert()` requires a filesystem path, not a file handle | Write to `tempfile.NamedTemporaryFile`, pass the path, delete after |
| Celery / RQ for job queues | Out of scope for v1; low-traffic on-demand model doesn't require it | Synchronous FastAPI handler is sufficient |
| `file.read()` for large files without size validation | Can exhaust server memory | Enforce `Content-Length` limit at the ASGI level or with a middleware check; for v1 and on-demand traffic, a per-request 50MB cap is sufficient |
| Poetry | Slower resolver, heavier toolchain; being displaced by uv in the Python ecosystem | uv |
| Rye | Rye's author is converging Rye into uv; new projects should start with uv directly | uv |

---

## Testing Patterns for Document Processing

```python
# conftest.py
import pytest
from fastapi.testclient import TestClient
from selection_maid.api.app import app

@pytest.fixture(scope="session")
def client():
    # session-scoped to avoid re-initializing DocumentConverter per test
    with TestClient(app) as c:
        yield c

@pytest.fixture
def sample_pdf(tmp_path) -> Path:
    """Minimal valid PDF for unit tests — avoids network or model calls in fast tests."""
    # Use a real small fixture PDF committed to tests/fixtures/
    return Path("tests/fixtures/minimal.pdf")

# For async endpoint tests
import httpx, pytest_asyncio
from asgi_lifespan import LifespanManager

@pytest_asyncio.fixture
async def async_client():
    async with LifespanManager(app):
        async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
```

**Pattern for pipeline tests:**
- Use `scope="session"` fixtures for `DocumentConverter` — model loading is expensive
- Use `tmp_path` for output files; `tmp_path_factory` for session-scoped temp dirs
- Mock the `ExtractionPort` adapter in unit tests; only hit real Docling in integration tests
- Keep a `tests/fixtures/` directory with minimal real files (minimal PDF ~10KB, simple DOCX) to avoid generating test documents programmatically

---

## Version Compatibility Matrix

| Package | Version | Python | Notes |
|---------|---------|--------|-------|
| docling | >=2.95 | >=3.10 (3.13 supported since 2.18.0) | Python 3.14 supported from 2.59.0 |
| fastapi | >=0.115 | >=3.8 | Pydantic v2 is default since 0.100 |
| pydantic | v2.x | >=3.8 | v1 compatibility shim available but avoid it |
| uvicorn | >=0.30 | >=3.8 | |
| pytest-asyncio | >=0.23 | >=3.8 | `asyncio_mode = "auto"` in pyproject.toml recommended |
| torch | >=2.2.2 | >=3.8 | Docling requires torch >=2.2.2,<3.0.0 |

---

## Sources

- [Docling GitHub — docling-project/docling](https://github.com/docling-project/docling) — main repo, confirmed version and Python requirements
- [Docling PyPI page](https://pypi.org/project/docling/) — confirmed latest version 2.95.0, Python 3.13 support
- [Docling Supported Formats](https://docling-project.github.io/docling/usage/supported_formats/) — format list HIGH confidence
- [Docling HybridChunker docs](https://docling-project.github.io/docling/examples/hybrid_chunking/) — chunking API, `merge_peers`, `repeat_table_header`
- [Docling Pipeline Options](https://docling-project.github.io/docling/reference/pipeline_options/) — OCR engine options confirmed
- [Docling GitHub Issue #1023 — H2-only headings](https://github.com/docling-project/docling/issues/1023) — MEDIUM confidence, open bug
- [FastAPI Lifespan docs](https://fastapi.tiangolo.com/advanced/testing-events/) — lifespan pattern confirmed
- [FastAPI UploadFile reference](https://fastapi.tiangolo.com/reference/uploadfile/) — SpooledTemporaryFile behavior confirmed
- [uv documentation](https://docs.astral.sh/uv/concepts/projects/dependencies/) — dependency management patterns
- [PDF extraction benchmark — Procycons](https://procycons.com/en/blogs/pdf-data-extraction-benchmark/) — Docling vs alternatives accuracy
- [Docling RAG + LangChain example](https://docling-project.github.io/docling/examples/rag_langchain/) — DoclingLoader modes, HybridChunker integration
- [Reducing Docling Docker image size — Shekhar Gulati](https://shekhargulati.com/2025/02/05/reducing-size-of-docling-pytorch-docker-image/) — CPU-only torch install pattern

---

*Stack research for: Python document extraction service (SelectionMaid) — RAG ingestion layer*
*Researched: 2026-05-23*
