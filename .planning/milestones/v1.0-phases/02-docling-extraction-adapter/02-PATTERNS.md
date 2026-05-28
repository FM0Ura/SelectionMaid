# Phase 2: Docling Extraction Adapter - Pattern Map

**Mapped:** 2026-05-23
**Files analyzed:** 5 new/modified files
**Analogs found:** 5 / 5

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/selection_maid/adapters/extractor/docling.py` | adapter (extractor) | request-response | `src/selection_maid/service.py` + `tests/stubs/adapters.py#StubExtractor` | role-match (same port, real vs. stub) |
| `src/selection_maid/adapters/extractor/__init__.py` | package exports | — | `src/selection_maid/adapters/extractor/__init__.py` (exists, 1 line) | exact (expand in-place) |
| `tests/adapters/extractor/conftest.py` | test fixture / config | file-I/O | `tests/domain/test_service.py` session fixtures | role-match (session scope, fixture pattern) |
| `tests/adapters/extractor/test_docling_adapter.py` | test | request-response | `tests/domain/test_service.py` | exact (same test class structure, exception-wrapping pattern) |
| `pyproject.toml` (modified) | config | — | `pyproject.toml` (exists) | exact (add `[project].dependencies` + `[tool.uv.*]` sections) |

---

## Pattern Assignments

### `src/selection_maid/adapters/extractor/docling.py` (adapter, request-response)

**Primary analog:** `src/selection_maid/service.py`
**Secondary analog:** `tests/stubs/adapters.py` (StubExtractor — minimal protocol implementation to copy structure from)

**Imports pattern** — copy the `from __future__ import annotations` + domain imports convention from `service.py` lines 1-31; add `TYPE_CHECKING` guard for Docling:

```python
# service.py lines 1-11 (import header convention)
from __future__ import annotations

from selection_maid.domain.models import (
    RawDocument,
    RawInput,
)
from selection_maid.errors import (
    ExtractionError,
    ExtractionTimeoutError,
    UnsupportedFormatError,
)
```

Add the `TYPE_CHECKING` guard on top of that (Docling-specific — no analog in Phase 1):

```python
import concurrent.futures
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from docling.document_converter import DocumentConverter
```

**Constructor injection pattern** — copy from `service.py` lines 48-58 (constructor receives ports, stores as `self._attr`):

```python
# service.py lines 48-58
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
```

Phase 2 applies the same pattern with fewer injected dependencies:

```python
def __init__(
    self,
    converter: "DocumentConverter",
    timeout_seconds: int = 120,
) -> None:
    self._converter = converter
    self._timeout_seconds = timeout_seconds
```

**Exception wrapping pattern (D-16)** — copy from `service.py` lines 79-84 (the try/except SelectionMaidError + bare except pattern is the canonical D-16 implementation):

```python
# service.py lines 79-84 — Step 1 extract block
try:
    raw: RawDocument = self._extractor.extract(input)
except SelectionMaidError:
    raise
except Exception as e:
    raise ExtractionError(message=f"Extraction failed: {e}", cause=e) from e
```

Phase 2's adapter applies D-16 internally for Docling calls. The pattern is identical; only error types differ (`ExtractionTimeoutError` for `concurrent.futures.TimeoutError`, `ExtractionError` for all others).

**Port protocol signature** — copy from `tests/stubs/adapters.py` lines 14-21 (StubExtractor shows the minimal structural interface to satisfy `ExtractorPort`):

```python
# tests/stubs/adapters.py lines 14-21
class StubExtractor:
    def extract(self, document: RawInput) -> RawDocument:
        return RawDocument(
            content="# Hello\nContent.",
            filename=document.filename,
            page_count=1,
            format="pdf",
        )
```

Phase 2 replaces the hardcoded return with real Docling output but the method signature is locked: `def extract(self, document: RawInput) -> RawDocument`.

**Module-level constant pattern** — no direct analog in Phase 1 (first module-level constant in this project). Use `frozenset` for `SUPPORTED_MIME_TYPES` and `dict[str, str]` for `_MIME_TO_FORMAT` per the RESEARCH.md Pattern 4 skeleton.

**Factory function pattern** — no direct analog in Phase 1 (D-23 anticipates `build_router(service)` from Phase 6). Use the pattern from RESEARCH.md Pattern 4 directly:

```python
def build_docling_adapter(
    converter: "DocumentConverter",
    timeout_seconds: int = 120,
) -> DoclingAdapter:
    return DoclingAdapter(converter=converter, timeout_seconds=timeout_seconds)
```

---

### `src/selection_maid/adapters/extractor/__init__.py` (package exports)

**Analog:** `src/selection_maid/adapters/extractor/__init__.py` line 1 (current single-line docstring)

Current content (line 1):
```python
"""Extractor adapter subpackage — ExtractorPort implementations."""
```

Expand to add public exports. Copy the docstring convention and add `__all__`:

```python
"""Extractor adapter subpackage — ExtractorPort implementations."""

from selection_maid.adapters.extractor.docling import DoclingAdapter, build_docling_adapter

__all__ = ["DoclingAdapter", "build_docling_adapter"]
```

Note: `from docling...` is NOT imported here — only the domain-facing classes from `docling.py`. The `TYPE_CHECKING` guard in `docling.py` ensures torch is not loaded when the package is imported.

---

### `tests/adapters/extractor/conftest.py` (test fixture, file-I/O)

**Analog:** `tests/domain/test_service.py` lines 18-25 (session-scoped pytest fixtures)

```python
# tests/domain/test_service.py lines 18-25
@pytest.fixture(scope="session")
def stub_service() -> ExtractionService:
    return ExtractionService(StubExtractor(), StubFilter(), StubChunker(), StubEnricher())


@pytest.fixture(scope="session")
def raw_input() -> RawInput:
    return RawInput(path=Path("/tmp/test.pdf"), filename="test.pdf", mime_type="application/pdf")
```

Phase 2 uses `scope="session"` for the same reason: expensive setup (here, network download) should happen once per test session. The `raw_input` fixture also shows that `RawInput(path=Path(...), filename=..., mime_type=...)` is the standard construction pattern.

**File-I/O fixture additions** (no analog in Phase 1 — use RESEARCH.md Pattern 5):

```python
# RESEARCH.md Pattern 5 (tests/adapters/extractor/conftest.py)
from __future__ import annotations

import urllib.request
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"
FIXTURE_URLS = {
    "sample.pdf": "https://www.w3.org/WAI/WCAG21/Techniques/pdf/pdf-sample.pdf",
    "sample.docx": "https://calibre-ebook.com/downloads/demos/demo.docx",
    "sample.html": "https://www.w3.org/TR/WCAG20/",
}


@pytest.fixture(scope="session")
def real_pdf_path() -> Path | None:
    return _ensure_fixture("sample.pdf")
# ... (same pattern for docx and html)
```

Also add a session-scoped `real_converter` fixture (analogous to `stub_service` in test_service.py — one expensive object per session):

```python
@pytest.fixture(scope="session")
def real_converter() -> "DocumentConverter":
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption, WordFormatOption
    from docling.pipeline.simple_pipeline import SimplePipeline
    from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
    # ... construct per RESEARCH.md Pattern 1
```

The `from docling...` imports live inside the fixture body — same principle as the `TYPE_CHECKING` guard in the adapter: Docling is only imported when the fixture is actually invoked (integration tests), not when conftest.py is collected.

---

### `tests/adapters/extractor/test_docling_adapter.py` (test, request-response)

**Analog:** `tests/domain/test_service.py` (entire file — same structure)

**Test class organization pattern** — copy from `test_service.py` lines 28-79 and 81-148 (group related tests in classes; use method-level test functions, not standalone functions):

```python
# test_service.py lines 28-29, 81-82
class TestPipeline:
    def test_process_returns_extraction_result(...): ...

class TestExceptionWrapping:
    def test_non_domain_extractor_exception_becomes_extraction_error(...): ...
```

Phase 2 maps to:
- `class TestDoclingAdapterUnit:` — tests with mock converter (no real Docling; always run)
- `class TestDoclingAdapterIntegration:` — tests with real converter and downloaded fixtures (skip if fixtures unavailable)

**Exception wrapping test pattern** — copy from `test_service.py` lines 83-93 (inline class that raises, inject into service, assert domain error raised):

```python
# test_service.py lines 83-93
def test_non_domain_extractor_exception_becomes_extraction_error(
    self, raw_input: RawInput
) -> None:
    class ExtractorThatRaises:
        def extract(self, document: RawInput) -> RawDocument:
            raise ValueError("raw error")

    service = ExtractionService(
        ExtractorThatRaises(), StubFilter(), StubChunker(), StubEnricher()
    )
    with pytest.raises(ExtractionError):
        service.process(raw_input)
```

Phase 2 equivalent — use a mock converter that raises, inject into DoclingAdapter:

```python
def test_extraction_error_wraps_converter_exception(self) -> None:
    mock_converter = Mock()
    mock_converter.convert.side_effect = RuntimeError("docling internal error")
    adapter = DoclingAdapter(converter=mock_converter, timeout_seconds=5)
    raw_input = RawInput(path=Path("/tmp/test.pdf"), filename="test.pdf", mime_type="application/pdf")
    with pytest.raises(ExtractionError):
        adapter.extract(raw_input)
```

**Imports pattern** — copy from `test_service.py` lines 1-15 (all test imports at top, `from __future__ import annotations` first):

```python
# test_service.py lines 1-15
from __future__ import annotations

from pathlib import Path

import pytest

from selection_maid.domain.models import (...)
from selection_maid.errors import (...)
from selection_maid.service import ExtractionService
from tests.stubs.adapters import (...)
```

Phase 2 adds `from unittest.mock import Mock` and uses `DoclingAdapter` / `build_docling_adapter` instead of `ExtractionService`.

**Integration test skip pattern** (no exact analog in Phase 1 — use D-27 / RESEARCH.md Pattern 5 skip pattern):

```python
def test_pdf_extraction(self, real_converter, real_pdf_path):
    if real_pdf_path is None:
        pytest.skip("Integration fixtures unavailable — skipping")
    adapter = DoclingAdapter(converter=real_converter)
    raw_input = RawInput(path=real_pdf_path, filename="sample.pdf", mime_type="application/pdf")
    result = adapter.extract(raw_input)
    assert isinstance(result, RawDocument)
    assert result.content  # non-empty Markdown
    assert result.format == "pdf"
```

---

### `pyproject.toml` (modified, config)

**Analog:** `pyproject.toml` lines 1-43 (existing file — targeted additions only)

Current `[project].dependencies` (line 7):
```toml
dependencies = []
```

Add Docling dependency and pytorch-cpu index:

```toml
# [project] section — replace dependencies = []
dependencies = [
    "docling>=2.95.0",
]

# New sections to append after [dependency-groups]
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

---

## Shared Patterns

### `from __future__ import annotations` — Universal
**Source:** Every Phase 1 file (`models.py` line 1, `ports.py` line 1, `service.py` line 1, `errors.py` line 1, `stubs/adapters.py` line 1)
**Apply to:** All new `.py` files in Phase 2

This is the established project-wide convention. Every module starts with this annotation.

### Constructor Injection
**Source:** `src/selection_maid/service.py` lines 48-58
**Apply to:** `DoclingAdapter.__init__`

```python
# service.py lines 48-58
def __init__(
    self,
    extractor: ExtractorPort,
    ...
) -> None:
    self._extractor = extractor
    ...
```

Pattern: receive dependencies as typed constructor arguments, store as `self._name` (underscore prefix for private attributes). No `Optional` params with post-init resolution — all required at construction time.

### D-16 Exception Wrapping (try / except SelectionMaidError / except Exception)
**Source:** `src/selection_maid/service.py` lines 79-84, 87-92, 95-100, 103-108
**Apply to:** `DoclingAdapter.extract()` for the `converter.convert()` call

The canonical pattern has three parts:
1. `try:` — call the external dependency
2. `except SelectionMaidError: raise` — let domain errors through unchanged
3. `except Exception as e: raise SpecificError(..., cause=e) from e` — wrap non-domain exceptions

```python
# service.py lines 79-84
try:
    raw: RawDocument = self._extractor.extract(input)
except SelectionMaidError:
    raise
except Exception as e:
    raise ExtractionError(message=f"Extraction failed: {e}", cause=e) from e
```

Note: For `DoclingAdapter`, `concurrent.futures.TimeoutError` must be caught *before* the bare `except Exception` to translate it to `ExtractionTimeoutError` specifically. The `SelectionMaidError` re-raise branch still comes first.

### Error Construction (`message=`, `cause=`)
**Source:** `src/selection_maid/errors.py` lines 20-23 (`SelectionMaidError.__init__`); `service.py` lines 84, 92, 100, 108
**Apply to:** All `raise` statements in `DoclingAdapter`

```python
# errors.py lines 20-23
def __init__(self, message: str, cause: Exception | None = None) -> None:
    self.message = message
    self.cause = cause
    super().__init__(message)
```

```python
# service.py line 84 — usage pattern
raise ExtractionError(message=f"Extraction failed: {e}", cause=e) from e
```

`UnsupportedFormatError` has an extra `format:` kwarg (errors.py lines 44-47):

```python
# errors.py lines 44-47
def __init__(
    self, message: str, format: str, cause: Exception | None = None
) -> None:
```

### Session-Scoped Pytest Fixtures
**Source:** `tests/domain/test_service.py` lines 18-25
**Apply to:** `tests/adapters/extractor/conftest.py`

```python
# test_service.py lines 18-25
@pytest.fixture(scope="session")
def stub_service() -> ExtractionService:
    return ExtractionService(StubExtractor(), StubFilter(), StubChunker(), StubEnricher())

@pytest.fixture(scope="session")
def raw_input() -> RawInput:
    return RawInput(path=Path("/tmp/test.pdf"), filename="test.pdf", mime_type="application/pdf")
```

Use `scope="session"` for any fixture that is expensive to create (converter, downloaded files). The `real_converter` fixture in Phase 2 follows the same convention.

### Test Class Grouping
**Source:** `tests/domain/test_service.py` lines 28 and 81 (two class blocks: `TestPipeline` and `TestExceptionWrapping`)
**Apply to:** `tests/adapters/extractor/test_docling_adapter.py`

Group by concern: one class per scenario category (unit vs. integration, happy-path vs. error cases).

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `tests/fixtures/.gitkeep` | test infrastructure | — | Trivial file (empty); no pattern needed |

No significant new patterns are without analog. The `TYPE_CHECKING` guard for Docling and the `ThreadPoolExecutor` timeout are new infrastructure patterns documented in RESEARCH.md Patterns 2-4 which serve as the reference.

---

## Metadata

**Analog search scope:** `src/selection_maid/` (all subdirectories), `tests/` (all subdirectories)
**Files scanned:** 12 source files, 4 test files
**Key insight:** Phase 1 established every structural pattern Phase 2 needs. `DoclingAdapter` is to `StubExtractor` what `ExtractionService` is to its stubs: same protocol signature, same injection style, same D-16 wrapping — but with real I/O and a third-party library behind the boundary.
**Pattern extraction date:** 2026-05-23
