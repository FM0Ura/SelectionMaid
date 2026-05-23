# Phase 2: Docling Extraction Adapter - Research

**Researched:** 2026-05-23
**Domain:** Docling DocumentConverter API, FastAPI lifespan, threading timeout, mypy boundary enforcement
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-21:** `DoclingAdapter` receives `DocumentConverter` via constructor injection: `__init__(self, converter: DocumentConverter, timeout_seconds: int = 120)`. The adapter does not create the converter — receives one pre-built. Phase 6 creates the converter in FastAPI lifespan and injects it. Tests pass a real instance (integration) or mock as needed.
- **D-22:** Supported formats hardcoded as a module-level constant (not configurable via constructor): `SUPPORTED_MIME_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/html"}`. v2 formats (PPTX, XLSX) will be added to the same set in the future.
- **D-23:** `DoclingAdapter` exposed as direct class plus factory function `build_docling_adapter(converter: DocumentConverter, timeout_seconds: int = 120) -> DoclingAdapter`. Consistent pattern with `build_router(service)` to be defined in Phase 6.
- **D-24:** Timeout of 120s implemented with `concurrent.futures.ThreadPoolExecutor`: the `converter.convert()` call is submitted in a separate thread, and the result obtained via `future.result(timeout=timeout_seconds)`. Python's `TimeoutError` is caught and translated to `ExtractionTimeoutError`. Accepted trade-off for v1: the conversion thread may continue running in background after timeout (low-traffic on-demand behavior does not require abrupt termination).
- **D-25:** `timeout_seconds: int = 120` is a constructor parameter (D-21). Integration tests can use a smaller value (e.g., 5s) to validate the mechanism without waiting 120s.
- **D-26:** Integration fixtures downloaded from public URLs on first test run. Local cache in `tests/fixtures/` (directory in `.gitignore`). Implemented as pytest fixture with `scope="session"`: checks if file exists in cache before downloading.
- **D-27:** If download fails (no internet, URL unavailable), integration tests are skipped with `pytest.skip("Integration fixtures unavailable — skipping")`. No CI failure due to connectivity. Unit tests (with mock converter) always execute regardless of connectivity.
- **D-28:** Markdown content extracted via `result.document.export_to_markdown()` — native `DoclingDocument` method. Known heading-flattening bug (issue #1023) accepted in v1. The `ExtractorPort` boundary allows fixing the output without changing the interface when the bug is fixed upstream.
- **D-29:** `RawDocument.page_count` filled with `len(result.document.pages)` for PDF and DOCX; `page_count=0` for HTML (HTML has no page concept — compatible with D-06 "page_count=0 when unknown").
- **D-30:** `UnsupportedFormatError` raised at the start of `extract()` if `document.mime_type` not in `SUPPORTED_MIME_TYPES`, **before** calling Docling. Internal Docling failures for supported formats are caught and translated to `ExtractionError` (D-16 wrapping pattern already defined in ExtractionService, applied also in the adapter).

### Claude's Discretion

None specified for Phase 2 — all key decisions are locked.

### Deferred Ideas (OUT OF SCOPE)

- **multiprocessing for timeout** — Real isolation with child process termination. Considered and discarded for v1 due to overhead and complexity. Revisit if thread-lingering becomes a production problem.
- **Configurable formats via constructor** — `DoclingAdapter(converter, allowed_formats={"application/pdf"})`. Discarded for v1 (hardcoded is sufficient). Candidate for v2 when PPTX/XLSX are added (EXT-V2-02, EXT-V2-03).
- **Binary fixtures in repo** — Option considered and discarded in favor of on-demand download. Keep the decision: fixtures in `tests/fixtures/` are gitignored.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EXT-01 | System accepts native-text PDF for content extraction | DocumentConverter with InputFormat.PDF + PdfFormatOption confirmed; `convert(Path)` API verified |
| EXT-02 | System accepts DOCX/Word for content extraction | WordFormatOption + SimplePipeline confirmed; InputFormat.DOCX verified in official docs |
| EXT-03 | System accepts HTML for content extraction | InputFormat.HTML confirmed in allowed_formats list; no separate FormatOption needed |
| EXT-04 | Extracted content converted to Markdown with heading hierarchy preserved (H1/H2/H3+) | `export_to_markdown()` confirmed; H2-flattening bug (issue #1023) known and accepted per D-28 |
| EXT-05 | Tables converted to Markdown table syntax with structure preserved | `do_table_structure=True` (default) + TableFormer AI model; GFM table output confirmed |
| EXT-06 | Ordered and unordered lists preserved in Markdown output | Docling preserves list structure in DoclingDocument; export serializes list items correctly |
| EXT-07 | Code blocks delimited with backticks in Markdown output | CodeItem serialized as fenced triple-backtick blocks by default in MarkdownSerializer; `do_code_enrichment=True` adds language detection |
</phase_requirements>

---

## Summary

Phase 2 delivers `DoclingAdapter` — the concrete implementation of `ExtractorPort` that converts PDF, DOCX, and HTML files into `RawDocument` with structured Markdown content. The adapter is the sole boundary where Docling types exist; no Docling type crosses into the domain or service layers.

The Docling library (v2.95.0, released 2026-05-21) has a stable, well-documented API centered on `DocumentConverter`. The key call chain is: `converter.convert(Path)` → `ConversionResult.document` → `DoclingDocument.export_to_markdown()`. Format-specific options (`PdfFormatOption`, `WordFormatOption`) are passed via the `format_options` dict at converter construction time, not at call time. The singleton pattern (D-21) means the converter is constructed once with all format options pre-configured and injected into the adapter.

Timeout is implemented via `concurrent.futures.ThreadPoolExecutor` — submit the blocking `converter.convert()` call, call `future.result(timeout=N)`, catch `concurrent.futures.TimeoutError` and re-raise as `ExtractionTimeoutError`. This is correct Python; `TimeoutError` in Python 3.11+ is an alias for `concurrent.futures.TimeoutError`, but explicitly catching `concurrent.futures.TimeoutError` is more precise. The lingering thread behavior is explicitly accepted per D-24.

The mypy boundary enforcement strategy uses `--no-implicit-reexport` (already implied by `strict = true` in pyproject.toml) plus the fact that `adapters/extractor/` is the only module that imports from `docling.*`. Since `DoclingAdapter.extract()` returns `RawDocument` (a pure domain type), no Docling type propagates outward unless the implementor explicitly passes one — which mypy strict will flag as a type error anywhere in the codebase outside the adapter module.

**Primary recommendation:** Use `DocumentConverter` with explicit `allowed_formats` + `format_options` at construction. Wrap `converter.convert()` in a `ThreadPoolExecutor` future. Return `RawDocument` with `content=result.document.export_to_markdown()`, `page_count=len(result.document.pages)`, `format` derived from mime_type mapping.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| File format detection | Adapter (extractor) | — | MIME type already on RawInput from Phase 6; adapter just validates against SUPPORTED_MIME_TYPES |
| Document conversion | Adapter (extractor) | — | Docling lives entirely within adapters/extractor/; no domain type needed |
| Markdown export | Adapter (extractor) | — | `export_to_markdown()` is a Docling method; called inside adapter, result stored in RawDocument.content |
| Page count calculation | Adapter (extractor) | — | `len(result.document.pages)` is a Docling API call; adapter maps it to RawDocument.page_count |
| Timeout enforcement | Adapter (extractor) | — | Threading concern; fully contained in adapter via ThreadPoolExecutor |
| Error translation | Adapter (extractor) | Domain (errors.py) | Adapter catches Docling exceptions and raises domain errors (EXT-001/002/003) |
| Singleton lifecycle | Phase 6 (lifespan) | — | Converter created in FastAPI lifespan; adapter receives it pre-built via constructor injection |
| Integration test fixtures | Test infrastructure | — | Download-on-demand in conftest.py; pytest session fixture with skip-on-failure |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| docling | 2.95.0 | Document conversion engine | Project constraint; confirmed on PyPI 2026-05-21; 36M all-time downloads; IBM/LF AI provenance |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| concurrent.futures (stdlib) | stdlib | Thread-based timeout for blocking calls | D-24: submit `converter.convert()` to ThreadPoolExecutor; `future.result(timeout=N)` |
| pytest | >=9.0.3 (installed) | Test runner | All tests |
| pytest-asyncio | >=1.3.0 (installed) | Async test support | Not needed in Phase 2 (all adapter methods are sync) |
| httpx or urllib.request (stdlib) | stdlib preferred | Download test fixtures on-demand | conftest.py session fixture; stdlib `urllib.request.urlretrieve` avoids adding a dependency |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ThreadPoolExecutor timeout | multiprocessing.Process | Deferred per D-deferred — harder to set up, kills lingering work; overkill for v1 |
| `urllib.request` for fixture download | `httpx` | httpx already in dev deps; either works; urllib.request has zero extra cost |
| `do_code_enrichment=True` | default (off) | Enrichment loads an extra model; EXT-07 requires code blocks in output — default behavior already wraps CodeItems in fenced backticks; enrichment only adds language detection which EXT-07 does not require |

**Installation (pyproject.toml additions):**

```toml
[project]
dependencies = [
  "docling>=2.95.0",
]

# CPU-only PyTorch to avoid 2GB CUDA download
[tool.uv.sources]
torch = [
    { index = "pytorch-cpu" },
]
torchvision = [
    { index = "pytorch-cpu" },
]

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true
```

```bash
# Add docling (uv resolves torch via pytorch-cpu index above)
uv add "docling>=2.95.0"
```

**Version verification:** Confirmed via PyPI JSON API — `docling 2.95.0` uploaded 2026-05-21, Python `>=3.10,<4.0`. [VERIFIED: PyPI JSON API + slopcheck OK]

---

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| docling | PyPI | ~23 months (first: 2024-07-15) | 7.1M/month, 36M total | github.com/docling-project/docling | OK | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none

**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
RawInput(path, filename, mime_type)
         |
         v
  DoclingAdapter.extract()
         |
         +--> MIME check against SUPPORTED_MIME_TYPES
         |    └─ Not in set → UnsupportedFormatError (EXT-002)
         |
         +--> ThreadPoolExecutor.submit(converter.convert, path)
         |         |
         |    future.result(timeout=120s)
         |         |
         |         +--> TimeoutError → ExtractionTimeoutError (EXT-003)
         |         +--> Any other Exception → ExtractionError (EXT-001)
         |         |
         |    ConversionResult
         |         |
         |    result.status check
         |         +--> FAILURE → ExtractionError (EXT-001)
         |         |
         |    result.document (DoclingDocument) ← stays inside adapters/extractor/
         |         |
         |    export_to_markdown() → content: str
         |    len(pages) → page_count: int  (0 for HTML)
         |    mime_type → format: str
         |
         v
  RawDocument(content, filename, page_count, format)
         |
         v
  ExtractorPort boundary ──────────────────────────────────────────
         |                  No docling.* types cross this line
         v
  ExtractionService.process() (domain)
```

### Recommended Project Structure

```
src/selection_maid/adapters/extractor/
├── __init__.py          # exports: DoclingAdapter, build_docling_adapter
└── docling.py           # DoclingAdapter class + SUPPORTED_MIME_TYPES constant

tests/adapters/extractor/
├── __init__.py          # (exists)
├── conftest.py          # session fixtures: real_pdf_path, real_docx_path, real_html_path (download-on-demand)
└── test_docling_adapter.py  # unit tests (mock converter) + integration tests (real converter)

tests/fixtures/          # .gitignored — populated by conftest.py on first run
├── sample.pdf
├── sample.docx
└── sample.html
```

### Pattern 1: DocumentConverter Construction with Format Options

**What:** Pre-configure `DocumentConverter` at construction time with explicit `allowed_formats` and `format_options`. This is the singleton — constructed once in Phase 6 lifespan, or once per integration test session.

**When to use:** Always — this is the only supported construction pattern.

```python
# Source: https://docling-project.github.io/docling/examples/run_with_formats/
# Source: https://docling-project.github.io/docling/examples/custom_convert/

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption, WordFormatOption
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

pdf_options = PdfPipelineOptions(
    do_ocr=False,           # digital text PDF — no OCR needed
    do_table_structure=True,  # enable GFM table output (default: True)
)

converter = DocumentConverter(
    allowed_formats=[
        InputFormat.PDF,
        InputFormat.DOCX,
        InputFormat.HTML,
    ],
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_cls=StandardPdfPipeline,
            pipeline_options=pdf_options,
        ),
        InputFormat.DOCX: WordFormatOption(
            pipeline_cls=SimplePipeline,
        ),
        # HTML: no FormatOption needed — uses default SimplePipeline
    },
)
```

### Pattern 2: Conversion Call with ThreadPoolExecutor Timeout

**What:** Wrap the blocking synchronous `converter.convert(path)` call in a thread so a timeout can be applied without blocking the calling thread indefinitely.

**When to use:** Every call to `extract()`. The timeout value comes from `self._timeout_seconds`.

```python
# Source: https://docs.python.org/3/library/concurrent.futures.html

import concurrent.futures
from pathlib import Path

from docling.datamodel.base_models import ConversionStatus

from selection_maid.errors import ExtractionError, ExtractionTimeoutError

def _convert_with_timeout(
    converter: DocumentConverter,
    path: Path,
    timeout_seconds: int,
) -> "ConversionResult":  # quoted to keep Docling type from propagating
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(converter.convert, path)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError as exc:
            raise ExtractionTimeoutError(
                f"Conversion exceeded {timeout_seconds}s timeout",
                cause=exc,
            ) from exc
        except Exception as exc:
            raise ExtractionError(
                f"Docling conversion failed: {exc}",
                cause=exc,
            ) from exc
```

### Pattern 3: RawDocument Assembly from ConversionResult

**What:** Map Docling's internal types to the domain's `RawDocument`. This is the boundary crossing — Docling types stop here.

```python
# Source: documented API from https://docling-project.github.io/docling/reference/document_converter/
# and https://docling-project.github.io/docling/reference/docling_document/

from selection_maid.domain.models import RawDocument

_MIME_TO_FORMAT: dict[str, str] = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/html": "html",
}

def _build_raw_document(
    result: "ConversionResult",
    input_doc: "RawInput",
) -> RawDocument:
    doc = result.document
    content = doc.export_to_markdown()
    # page_count: 0 for HTML (no page concept), len(pages) for others
    page_count = 0 if input_doc.mime_type == "text/html" else len(doc.pages)
    fmt = _MIME_TO_FORMAT[input_doc.mime_type]
    return RawDocument(
        content=content,
        filename=input_doc.filename,
        page_count=page_count,
        format=fmt,
    )
```

### Pattern 4: DoclingAdapter Class Skeleton

```python
# src/selection_maid/adapters/extractor/docling.py

from __future__ import annotations

import concurrent.futures
from pathlib import Path
from typing import TYPE_CHECKING

from selection_maid.domain.models import RawDocument, RawInput
from selection_maid.errors import (
    ExtractionError,
    ExtractionTimeoutError,
    SelectionMaidError,
    UnsupportedFormatError,
)

if TYPE_CHECKING:
    # Keep Docling types out of the runtime import graph for non-extractor modules
    from docling.document_converter import DocumentConverter

SUPPORTED_MIME_TYPES: frozenset[str] = frozenset({
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/html",
})

_MIME_TO_FORMAT: dict[str, str] = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/html": "html",
}


class DoclingAdapter:
    def __init__(
        self,
        converter: "DocumentConverter",
        timeout_seconds: int = 120,
    ) -> None:
        self._converter = converter
        self._timeout_seconds = timeout_seconds

    def extract(self, document: RawInput) -> RawDocument:
        if document.mime_type not in SUPPORTED_MIME_TYPES:
            raise UnsupportedFormatError(
                f"Unsupported format: {document.mime_type}",
                format=document.mime_type,
            )
        # ... threading + conversion + mapping
        ...


def build_docling_adapter(
    converter: "DocumentConverter",
    timeout_seconds: int = 120,
) -> DoclingAdapter:
    return DoclingAdapter(converter=converter, timeout_seconds=timeout_seconds)
```

**Note on `TYPE_CHECKING`:** Using `if TYPE_CHECKING:` for the `DocumentConverter` import means Docling is imported at runtime only inside `adapters/extractor/docling.py` (where the real instantiation happens in Phase 6), not merely from the type annotation. This is the correct pattern for keeping Docling out of the domain's import graph. The actual runtime annotation `"DocumentConverter"` (string) is used in the method signatures to defer resolution.

### Pattern 5: Integration Test Fixture with On-Demand Download

```python
# tests/adapters/extractor/conftest.py

from __future__ import annotations

import urllib.request
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"
FIXTURE_URLS = {
    "sample.pdf": "https://www.w3.org/WAI/WCAG21/Techniques/pdf/pdf-sample.pdf",
    "sample.docx": "https://calibre-ebook.com/downloads/demos/demo.docx",
    "sample.html": "https://www.w3.org/TR/WCAG20/",  # or a simpler static URL
}


@pytest.fixture(scope="session")
def real_pdf_path() -> Path | None:
    return _ensure_fixture("sample.pdf")


@pytest.fixture(scope="session")
def real_docx_path() -> Path | None:
    return _ensure_fixture("sample.docx")


@pytest.fixture(scope="session")
def real_html_path() -> Path | None:
    return _ensure_fixture("sample.html")


def _ensure_fixture(filename: str) -> Path | None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    target = FIXTURES_DIR / filename
    if target.exists():
        return target
    url = FIXTURE_URLS[filename]
    try:
        urllib.request.urlretrieve(url, target)
        return target
    except Exception:
        return None


# In test functions, skip if fixture is None:
# def test_pdf(real_pdf_path):
#     if real_pdf_path is None:
#         pytest.skip("Integration fixtures unavailable — skipping")
```

### Anti-Patterns to Avoid

- **Importing `DocumentConverter` at module level in `DoclingAdapter`:** This causes the entire Docling runtime (including torch model loading) to trigger on any `import selection_maid`. Use `if TYPE_CHECKING:` guard + string annotations. The real import lives in the function/module that constructs the converter (Phase 6 lifespan).
- **Passing `DocumentConverter` type annotation without string quoting outside `adapters/extractor/`:** Breaks the mypy boundary — mypy will trace the type through the `ExtractorPort` Protocol and find no leak, but any `from docling...` at module top level in `service.py` or domain modules would be a violation.
- **Checking `result.status != ConversionStatus.SUCCESS` with `raises_on_error=True` (default):** When `raises_on_error=True` (the default), Docling raises `RuntimeError` on failure — the status check is redundant. Use `raises_on_error=True` and let the `except Exception` handler in the adapter translate it to `ExtractionError`.
- **Reading `UploadFile` directly and passing the handle to Docling:** Docling's `convert()` requires a filesystem `Path`, not a file handle. Phase 6 responsibility — write to `tempfile.NamedTemporaryFile`, pass path. Phase 2 only deals with `RawInput.path` which is already a `Path`.
- **Using `executor.map()` for timeout instead of `future.result(timeout=N)`:** `map()` with a timeout raises on the iterator, not on a specific future — use `submit()` + `future.result(timeout=N)` for single-call timeout.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF text extraction + layout understanding | Custom PDF parser | Docling `DocumentConverter` | DocLayNet + TableFormer AI models; handles mixed text/image PDFs; GFM table output |
| DOCX heading/table parsing | python-docx custom traversal | Docling `WordFormatOption` | Docling preserves DOCX heading styles and converts tables to GFM |
| HTML-to-Markdown conversion | html2text or custom regex | Docling `InputFormat.HTML` | Docling preserves ordered/unordered list structure; html2text loses semantic structure |
| Code block detection in PDFs | Regex on exported text | Docling `CodeItem` + `export_to_markdown()` | MarkdownSerializer wraps CodeItem in triple-backtick blocks automatically |
| Thread timeout | signal.alarm / custom event | `concurrent.futures.ThreadPoolExecutor` + `future.result(timeout=N)` | signal.alarm is Unix-only and not safe in threaded environments |

**Key insight:** Docling's `export_to_markdown()` is a faithful serialization of the `DoclingDocument` internal structure — it handles headings, tables (GFM), lists, and code blocks (fenced backticks) without any post-processing. The heading H2 flattening is a known upstream limitation, accepted per D-28.

---

## Common Pitfalls

### Pitfall 1: Docling Memory Accumulation on Repeated Conversions

**What goes wrong:** `DoclingParseV2DocumentBackend` accumulates memory on repeated conversions and never releases it (GitHub issue #2209). A 0.41 MB PDF can cause memory to jump from 500 MB to 13+ GB after just one conversion when reusing a `DocumentConverter` instance in a tight loop.

**Why it happens:** The backend retains references to converted document internals, processed pages, and ML model intermediate data — no cleanup mechanism exists as of v2.95.

**How to avoid:** Phase 2's on-demand, low-traffic model is not affected by this — the issue manifests in batch/repeated conversion loops, not single-document requests. Phase 7 (Integration Hardening) will measure RSS regression over 20 conversions. If needed, the mitigation is to recreate the converter periodically (`gc.collect()` after deletion) — but this is Phase 7 scope, not Phase 2.

**Warning signs:** RSS growing monotonically across requests; `htop` showing Python process consuming >2GB after a few dozen conversions.

### Pitfall 2: H2 Heading Flattening in export_to_markdown()

**What goes wrong:** `export_to_markdown()` exports all headings as `##` (H2) regardless of the original document's heading hierarchy (GitHub issue #1023). A document with H1/H2/H3 structure comes out as all `##`.

**Why it happens:** Docling classifies headers by visual prominence but collapses the hierarchy in the Markdown serializer. Issue filed 2025-02-19, assigned but not resolved as of 2026-05.

**How to avoid:** Accepted per D-28 — the `ExtractorPort` boundary means a fix can be applied (post-processing or upstream fix) without changing the interface. EXT-04 success criterion says "H1/H2/H3 preserved" — the integration test for this requirement should document the known limitation and adjust the assertion to check that headings exist (are formatted as `#`) rather than checking exact levels, OR the test can accept H2-flat output with a comment.

**Warning signs:** Integration test for EXT-04 failing because all headings are `##` even when the source PDF had clear H1/H2/H3 distinctions.

### Pitfall 3: Docling Import at Module Level Leaks Torch Load Time

**What goes wrong:** If `from docling.document_converter import DocumentConverter` appears at the module top level in any file outside `adapters/extractor/`, importing the `selection_maid` package triggers torch model loading (several seconds, multiple GB RAM) even for modules that never call extraction.

**Why it happens:** Python's import system executes module top-level code on first import. Docling's module-level code loads torch and initializes model registries.

**How to avoid:** In `DoclingAdapter`, use `if TYPE_CHECKING:` guard for the type annotation and string-quoted forward references in signatures. The real `from docling...` import should only appear in the module(s) that physically construct `DocumentConverter` (Phase 6 lifespan handler, integration test conftest).

**Warning signs:** `import selection_maid` taking >5 seconds; any test that imports domain modules triggering torch loads.

### Pitfall 4: ConversionStatus.FAILURE Not Raised When raises_on_error=True

**What goes wrong:** Developer checks `result.status == ConversionStatus.FAILURE` after calling `converter.convert()` with default settings, but the convert() call itself already raised a `RuntimeError` — the status check branch is dead code.

**Why it happens:** `raises_on_error=True` is the default. With this setting, Docling raises on failure instead of returning a FAILURE status result. The status field is only useful when `raises_on_error=False`.

**How to avoid:** Use `raises_on_error=True` (default) and wrap `converter.convert()` in a `try/except Exception` block. The `except` branch translates to `ExtractionError`. No status check needed.

**Warning signs:** Silent failures on corrupt files; the adapter returning empty Markdown without raising an error.

### Pitfall 5: ThreadPoolExecutor Reuse vs. Per-Call Creation

**What goes wrong:** Creating a `ThreadPoolExecutor` inside `extract()` on every call creates and tears down a thread pool per request, which is inefficient but correct. Using a module-level or class-level executor with `shutdown(wait=False)` on timeout can leave threads orphaned permanently.

**Why it happens:** ThreadPoolExecutor does not support cancelling running futures — only pending ones (`cancel_futures=True` in shutdown only affects not-yet-started futures).

**How to avoid:** Per D-24 the lingering thread is accepted. Use a fresh `ThreadPoolExecutor(max_workers=1)` as a context manager inside `extract()`. The context manager calls `shutdown(wait=False)` on exit, which doesn't block the caller but also doesn't kill the lingering thread. This is the correct v1 pattern.

---

## Code Examples

### Verified Pattern: Minimal DocumentConverter Construction

```python
# Source: https://docling-project.github.io/docling/examples/run_with_formats/
# Source: https://docling-project.github.io/docling/examples/custom_convert/

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption, WordFormatOption
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

converter = DocumentConverter(
    allowed_formats=[InputFormat.PDF, InputFormat.DOCX, InputFormat.HTML],
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_cls=StandardPdfPipeline,
            pipeline_options=PdfPipelineOptions(do_ocr=False, do_table_structure=True),
        ),
        InputFormat.DOCX: WordFormatOption(pipeline_cls=SimplePipeline),
        # HTML uses default pipeline — no entry needed
    },
)
```

### Verified Pattern: Conversion and Export

```python
# Source: https://docling-project.github.io/docling/getting_started/quickstart/

result = converter.convert(Path("document.pdf"))
markdown_content: str = result.document.export_to_markdown()
page_count: int = len(result.document.pages)
```

### Verified Pattern: CodeItem Serialization (from docling-core source)

```python
# Source: https://github.com/docling-project/docling-core/blob/main/docling_core/transforms/serializer/markdown.py

# Default behavior (format_code_blocks=True by default):
# CodeItem → ```\n{text}\n```
# Inline code (inside table cell or with hyperlink) → `{text}`

# export_to_markdown() uses format_code_blocks=True by default
# No special options needed for EXT-07 compliance
```

### Verified Pattern: ConversionResult Status and Error Fields

```python
# Source: https://www.mintlify.com/docling-project/docling/api/conversion-result

# With raises_on_error=True (default):
result = converter.convert(path)  # raises RuntimeError on failure

# With raises_on_error=False (for explicit status inspection):
result = converter.convert(path, raises_on_error=False)
if result.status not in (ConversionStatus.SUCCESS, ConversionStatus.PARTIAL_SUCCESS):
    for err in result.errors:
        print(err.error_message)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@app.on_event("startup")` | `@asynccontextmanager` lifespan | FastAPI 0.95.0 | `on_event` is deprecated — Phase 6 must use lifespan |
| LangChain RecursiveCharacterTextSplitter | Docling HybridChunker | Docling >=2.9.0 | HybridChunker is structure-aware; LangChain splitter is character-blind (Phase 4 concern) |
| `pip install docling` on CPU server | `uv add docling` with `[tool.uv.sources]` torch CPU index | uv >=0.4 | Avoids 2GB CUDA PyTorch download |
| PyPdfium2 backend | StandardPdfPipeline + DoclingParse | Docling v2 | DoclingParse v2/v4 provides AI-based layout understanding; pypdfium2 backend still available as fallback |

**Deprecated/outdated:**

- `@app.on_event`: Deprecated since FastAPI 0.95.0; Phase 6 will use `@asynccontextmanager` lifespan.
- `PipelineOptions` as top-level DocumentConverter kwarg: The `pipeline_options` parameter in the web search example `DocumentConverter(pipeline_options=...)` is NOT correct — pipeline options go into `PdfFormatOption(pipeline_options=...)`, not directly into `DocumentConverter`. [ASSUMED — verify against source code before using]

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `len(result.document.pages)` is the correct way to get page count (not `result.document.num_pages`) | Architecture Patterns, Pattern 3 | `page_count` field in `RawDocument` could be set to wrong value; verify in integration test |
| A2 | HTML documents return `len(result.document.pages) == 0` (no pages), making `page_count=0` consistent without special-casing | Architecture Patterns, Pattern 3 | If Docling assigns synthetic pages to HTML, the code should still use `0` per D-29 |
| A3 | `WordFormatOption` + `SimplePipeline` is sufficient for DOCX table extraction (GFM output) | Standard Stack, Pattern 1 | DOCX tables might need additional options; verify with a DOCX fixture that has tables |
| A4 | `export_to_markdown()` default call (no parameters) is sufficient for all three formats (PDF/DOCX/HTML) | Architecture Patterns, Pattern 3 | Edge case: certain format-specific options might affect output; integration tests will reveal this |
| A5 | `PipelineOptions` at the `DocumentConverter` constructor level (not per-format) does not override format-specific `PdfFormatOption` settings | Standard Stack, Code Example notes | Wrong construction pattern could cause PdfPipelineOptions to be ignored |

---

## Open Questions

1. **`len(result.document.pages)` vs `result.document.num_pages` for page count**
   - What we know: Web search results show `len(doc.pages)` as the community pattern; `num_pages` was mentioned in one search result as a property
   - What's unclear: Whether `num_pages` is a real property on `DoclingDocument` or just `len(pages)` convenience
   - Recommendation: Use `len(result.document.pages)` in implementation; write an assertion in the integration test: `assert adapter_result.page_count == len(converter_result.document.pages)`; adjust if the field name is different

2. **`TYPE_CHECKING` guard for `DocumentConverter` — mypy strict mode behavior**
   - What we know: `if TYPE_CHECKING:` prevents the import at runtime; string annotations defer type resolution
   - What's unclear: Whether mypy strict mode with `--no-implicit-reexport` will catch a violation where a non-adapter module accidentally imports `DocumentConverter` outside the guard
   - Recommendation: After implementing, run `mypy src/selection_maid/` and verify that removing the `TYPE_CHECKING` guard in a test file produces a type error that can be detected via policy (code review), OR document that mypy does not enforce this boundary automatically (it's a structural boundary, not a type error)

3. **Code blocks in DOCX — does `WordFormatOption` detect them?**
   - What we know: Docling's `CodeItem` serializes to fenced backticks; EXT-07 requires code blocks
   - What's unclear: Whether DOCX "code-formatted" paragraphs (monospace font) are recognized as `CodeItem` by Docling's DOCX pipeline, or only by the PDF pipeline
   - Recommendation: Include a DOCX fixture with a code-formatted section in the integration test; if Docling doesn't detect it, note it in EXT-07 test results as a known limitation

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | Dependency management | ✓ | 0.11.14 | — |
| Python | Runtime | ✓ | 3.14.5 | — |
| docling | Extraction engine | ✗ (not yet installed) | — | Install via `uv add docling>=2.95.0` |
| torch (CPU) | Docling ML models | ✗ (not yet installed) | — | Install via uv + pytorch-cpu index |

**Missing dependencies with no fallback:**
- `docling>=2.95.0`: Must be installed before Plan 02-01 can execute

**Missing dependencies with fallback:**
- None

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (exists) |
| Quick run command | `uv run pytest tests/adapters/extractor/ -x -q` |
| Full suite command | `uv run pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXT-01 | PDF with digital text → RawDocument with Markdown headings | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_pdf_extraction -x` | ❌ Wave 0 |
| EXT-02 | DOCX with tables → RawDocument with GFM tables | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_docx_extraction -x` | ❌ Wave 0 |
| EXT-03 | HTML → RawDocument with lists preserved | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_html_extraction -x` | ❌ Wave 0 |
| EXT-04 | Headings H1/H2/H3 preserved in output | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_headings_in_pdf -x` | ❌ Wave 0 |
| EXT-05 | Tables → GFM table syntax | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_tables_in_docx -x` | ❌ Wave 0 |
| EXT-06 | Lists preserved in Markdown | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_lists_in_html -x` | ❌ Wave 0 |
| EXT-07 | Code blocks in backticks | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_code_blocks -x` | ❌ Wave 0 |
| D-22 | UnsupportedFormatError on unknown MIME | unit | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_unsupported_format -x` | ❌ Wave 0 |
| D-24/D-25 | TimeoutError → ExtractionTimeoutError | unit | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_timeout -x` | ❌ Wave 0 |
| ARCH-01 | No docling type outside adapters/extractor/ | static | `uv run mypy src/ --strict` | ✅ (mypy config exists) |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/adapters/extractor/ -x -q --tb=short`
- **Per wave merge:** `uv run pytest tests/ -x -q`
- **Phase gate:** `uv run pytest tests/ -q && uv run mypy src/ --strict` both green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/adapters/extractor/conftest.py` — session fixtures for real_pdf_path, real_docx_path, real_html_path (download-on-demand pattern)
- [ ] `tests/adapters/extractor/test_docling_adapter.py` — unit tests (mock converter) + integration tests (real fixtures)
- [ ] `tests/fixtures/.gitkeep` — ensure directory exists and is gitignored
- [ ] `pyproject.toml` dependency additions: `docling>=2.95.0` + `[tool.uv.sources]` + `[[tool.uv.index]]` for pytorch-cpu

---

## Security Domain

> `security_enforcement` not explicitly set to false in config — including this section.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (no auth in adapter layer) |
| V3 Session Management | no | — (stateless adapter) |
| V4 Access Control | no | — |
| V5 Input Validation | yes | MIME type check against `SUPPORTED_MIME_TYPES` before any Docling call; path validation (Path object, not arbitrary string) |
| V6 Cryptography | no | — |

### Known Threat Patterns for Docling Adapter

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious PDF with zip bomb or deeply nested structures | DoS | `max_num_pages` and `max_file_size` params on `converter.convert()`; file size cap enforced at HTTP layer (Phase 6) |
| Password-protected PDF passed to Docling | Tampering/DoS | Docling will raise an exception — captured by `except Exception` → `ExtractionError`; no crash |
| Path traversal via `RawInput.path` | Tampering | Path object prevents null bytes; sanitization is Phase 6 responsibility (temp file); adapter trusts the path it receives |
| Lingering thread reading file after response | Information Disclosure | Tempfile deletion is Phase 6 responsibility; Phase 2 adapter only holds the path, not a file handle |

---

## Sources

### Primary (HIGH confidence)

- [VERIFIED: PyPI JSON API] — `docling 2.95.0`, Python `>=3.10,<4.0`, uploaded 2026-05-21
- [VERIFIED: slopcheck] — `docling` rated `[OK]`
- [CITED: https://docling-project.github.io/docling/reference/document_converter/] — `DocumentConverter.__init__`, `convert()` signature, `ConversionResult` structure
- [CITED: https://docling-project.github.io/docling/examples/custom_convert/] — `PdfFormatOption`, `PdfPipelineOptions`, import paths
- [CITED: https://docling-project.github.io/docling/examples/run_with_formats/] — `WordFormatOption`, `SimplePipeline`, `allowed_formats`, multi-format constructor pattern
- [CITED: https://docling-project.github.io/docling/usage/enrichments/] — `do_code_enrichment` feature description
- [CITED: https://github.com/docling-project/docling-core/blob/main/docling_core/transforms/serializer/markdown.py] — `CodeItem` triple-backtick serialization behavior
- [CITED: https://docs.astral.sh/uv/guides/integration/pytorch/] — `[tool.uv.sources]` + `[[tool.uv.index]]` CPU-only PyTorch pattern
- [CITED: https://docs.python.org/3/library/concurrent.futures.html] — `ThreadPoolExecutor`, `future.result(timeout=N)`, `TimeoutError` behavior

### Secondary (MEDIUM confidence)

- [CITED: https://github.com/docling-project/docling/issues/1023] — H2 heading flattening bug; open as of 2026-05
- [CITED: https://github.com/docling-project/docling/issues/2209] — DoclingParseV2 memory accumulation; open, no fix as of search date
- [CITED: https://pepy.tech/projects/docling] — 7.1M/month downloads, 36M total
- [CITED: https://docling-project.github.io/docling/getting_started/installation/] — CPU-only install via `--extra-index-url`

### Tertiary (LOW confidence, flagged)

- [ASSUMED] — `len(result.document.pages)` is the correct page count accessor (community example pattern; not from official API reference)
- [ASSUMED] — HTML documents return 0 pages from `len(result.document.pages)` (logical inference from "HTML has no page concept"; not verified in docs)
- [ASSUMED] — `WordFormatOption + SimplePipeline` produces GFM tables for DOCX documents (inferred from Docling's stated DOCX support; not explicitly tested)

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — docling 2.95.0 verified on PyPI, slopcheck OK, import paths confirmed via official docs and source code
- Architecture: HIGH — DocumentConverter API confirmed via official reference; ThreadPoolExecutor pattern from Python stdlib docs
- Pitfalls: MEDIUM — memory leak and H2 bug from GitHub issues (confirmed open); import-at-module-level from community knowledge
- Page count accessor: LOW — `len(result.document.pages)` from community examples, not official API reference

**Research date:** 2026-05-23
**Valid until:** 2026-06-23 (stable library; H2 bug and memory leak status may change with new Docling releases)
