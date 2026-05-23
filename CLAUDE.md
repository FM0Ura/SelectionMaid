<!-- GSD:project-start source:PROJECT.md -->
## Project

**SelectionMaid**

SelectionMaid é um serviço de curadoria e normalização de documentos — a "empregada" que recebe arquivos brutos (PDF, DOCX, HTML, imagens), extrai o conteúdo via Docling, limpa o ruído, enriquece metadados, segmenta em chunks e devolve Markdown estruturado pronto para ser inserido em um banco de dados vetorial. É a porta de entrada do pipeline RAG, desenhada como arquitetura hexagonal: todos os adaptadores (extrator, filtro, chunker, interface HTTP) são intercambiáveis sem tocar no núcleo de domínio.

**Core Value:** Documentos entram em qualquer formato, chunks Markdown normalizados saem via uma interface estável — independente da biblioteca de extração ou do protocolo de entrada usado.

### Constraints

- **Tech Stack**: Python 3.13+ (já fixado no pyproject.toml)
- **Biblioteca de extração**: Docling como implementação inicial do ExtractorPort
- **Interface primária**: FastAPI como implementação inicial do InputPort
- **Arquitetura**: Hexagonal (Ports & Adapters) — não negociável; é o requisito central de desacoplamento
- **Volume**: Low-traffic, on-demand — sem necessidade de fila ou workers horizontais no v1
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

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
- `DocumentConverter` — main entry point; accepts `allowed_formats` and `format_options` dict
- `PipelineOptions` — per-format pipeline configuration (OCR, image scale, table mode)
- `FormatOption` — bundles pipeline class + options + backend per format
- `DoclingDocument` — unified internal representation; exposes `export_to_markdown()`, `export_to_json()`, `export_to_html()`
- `HybridChunker` — Docling's own tokenization-aware chunker; the correct choice for this project (see Chunking section)
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
| Engine | Class | Notes |
|--------|-------|-------|
| EasyOCR | `EasyOcrOptions` | Default if GPU available; multilingual |
| Tesseract | `TesseractOcrOptions` | Best for CPU-only; auto language detection supported |
| Tesseract CLI | `TesseractCliOcrOptions` | When Tesseract binary is in PATH |
| RapidOCR | `RapidOcrOptions` | CPU (onnxruntime) or GPU (torch); fastest on CPU |
| macOS OCR | `OcrMacOptions` | macOS only |
### Docling Markdown Export — Known Limitation
### Chunking
- `HybridChunker` is structure-aware: it starts from Docling's hierarchical chunker and applies tokenizer-aware split/merge passes
- It preserves heading context in chunk metadata via `contextualize()` — essential for RAG retrieval quality
- It avoids mid-sentence splits and mid-table splits by design
- `merge_peers=True` (default) merges undersized consecutive chunks that share the same heading scope
- `repeat_table_header=True` (default) repeats table headers when a table spans multiple chunks
- LangChain's `RecursiveCharacterTextSplitter` is character-aware, not structure-aware — it would destroy the document hierarchy that Docling worked to extract
# Default: uses internal tokenizer, sensible defaults
# With explicit HuggingFace tokenizer (optional, for token-budget control)
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
## Installation
# pyproject.toml (uv-managed)
# For CPU-only servers, override torch to CPU wheel:
# uv add --extra-index-url https://download.pytorch.org/whl/cpu torch
# Install core + dev deps
# CPU-only torch (avoids 2GB CUDA download on servers)
# Run tests
# Run dev server
## FastAPI Patterns for This Service
### DocumentConverter Singleton via Lifespan
### File Upload Pattern
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
## Testing Patterns for Document Processing
# conftest.py
# For async endpoint tests
- Use `scope="session"` fixtures for `DocumentConverter` — model loading is expensive
- Use `tmp_path` for output files; `tmp_path_factory` for session-scoped temp dirs
- Mock the `ExtractionPort` adapter in unit tests; only hit real Docling in integration tests
- Keep a `tests/fixtures/` directory with minimal real files (minimal PDF ~10KB, simple DOCX) to avoid generating test documents programmatically
## Version Compatibility Matrix
| Package | Version | Python | Notes |
|---------|---------|--------|-------|
| docling | >=2.95 | >=3.10 (3.13 supported since 2.18.0) | Python 3.14 supported from 2.59.0 |
| fastapi | >=0.115 | >=3.8 | Pydantic v2 is default since 0.100 |
| pydantic | v2.x | >=3.8 | v1 compatibility shim available but avoid it |
| uvicorn | >=0.30 | >=3.8 | |
| pytest-asyncio | >=0.23 | >=3.8 | `asyncio_mode = "auto"` in pyproject.toml recommended |
| torch | >=2.2.2 | >=3.8 | Docling requires torch >=2.2.2,<3.0.0 |
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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
