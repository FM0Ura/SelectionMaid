<!-- generated-by: gsd-doc-writer -->
# Testing

SelectionMaid uses pytest with pytest-asyncio. Tests are organised by architectural layer and split into unit tests (no Docling model loading) and integration tests (real `DocumentConverter`, slow-marked).

## Test Framework and Setup

| Tool | Version | Role |
|------|---------|------|
| pytest | >=9.0.3 | Test runner |
| pytest-asyncio | >=1.3.0 | Async test support (`asyncio_mode = "auto"`) |
| httpx | >=0.28.1 | `AsyncClient` + `ASGITransport` for HTTP endpoint tests |
| anyio | >=4.13.0 | Async I/O backend pulled in by FastAPI/pytest-asyncio |
| pypdf | >=6.12.1 | PDF utilities in test helpers |

No additional setup is required beyond the standard dev install:

```bash
uv sync
```

`asyncio_mode = "auto"` is set in `pyproject.toml`, so every `async def` test function runs automatically without a `@pytest.mark.asyncio` decorator.

## Running Tests

```bash
# Full test suite
uv run pytest

# Skip slow integration tests (no Docling model loading, fast feedback)
uv run pytest -m "not slow"

# Only slow/integration tests
uv run pytest -m slow

# With coverage report
uv run pytest --cov=src --cov-report=term-missing

# Verbose output with print statements (useful for memory audit)
uv run pytest tests/test_memory_regression.py -s -v
```

The `slow` marker identifies tests that run real Docling inference (model loading, actual document conversion). These tests can take 10–30 seconds per extraction call and are excluded from fast CI runs.

## Test Structure

```
tests/
  conftest.py                     # session-scoped real_converter, real_pdf_path
  test_config.py                  # unit tests for config.py
  test_memory_regression.py       # RSS memory audit (marked slow)
  domain/
    test_models.py                # domain value object tests
    test_service.py               # ExtractionService unit + integration tests
  adapters/
    extractor/
      conftest.py                 # session-scoped converter + fixture paths
      test_docling_adapter.py     # DoclingAdapter unit and integration tests
    filter/
      test_heuristic_filter.py    # HeuristicFilter unit tests
    chunker/
      test_markdown_chunker.py    # MarkdownChunker unit tests
    enricher/
      test_metadata_enricher.py   # MetadataEnricher unit tests
    http/
      conftest.py                 # TestClient fixture with mock ExtractionService
      test_router.py              # HTTP router unit tests (mocked service)
      test_schemas.py             # Pydantic schema validation tests
      test_error_map.py           # Domain error -> HTTP status mapping
      test_integration.py         # End-to-end HTTP tests with real Docling (slow)
  stubs/
    adapters.py                   # Structural stubs: StubExtractor, StubFilter,
                                  # StubChunker, StubEnricher
  fixtures/
    sample.pdf                    # Downloaded on first run (orimi.com)
    sample.docx                   # Downloaded on first run (calibre-ebook.com)
    sample.html                   # Downloaded on first run (w3.org)
    adversarial/
      corrupt.pdf                 # Random bytes (triggers UPLOAD-002)
      empty.pdf                   # 0-byte file (triggers UPLOAD-002)
      spoofed.pdf                 # Plain text with .pdf extension (UPLOAD-002)
      protected.pdf               # AES-256 password-protected (triggers 500)
      large_sample.pdf            # ~40 MB PDF (below 50 MB limit)
    generate_adversarial.py       # Script to regenerate adversarial fixtures
```

## Writing New Tests

### File naming

Test files follow the `test_*.py` convention. Directories mirror the `src/selection_maid/` package layout:

- Domain tests live in `tests/domain/`
- Adapter tests live in `tests/adapters/<adapter_name>/`
- Top-level service and config tests live in `tests/`

### Stubs vs mocks

`tests/stubs/adapters.py` provides lightweight structural stubs — `StubExtractor`, `StubFilter`, `StubChunker`, `StubEnricher` — that satisfy the port protocols via duck typing. Use these in unit tests for `ExtractionService` so no real Docling or langdetect dependency is triggered.

For the HTTP layer, use `unittest.mock.MagicMock(spec=ExtractionService)` (already set up in `tests/adapters/http/conftest.py`) so router tests never load Docling models.

### Docling import discipline

All `from docling.*` imports must be placed **inside fixture bodies or test functions**, never at module top level. Conftest collection must not trigger torch model loading.

```python
# Correct — deferred import
@pytest.fixture(scope="session")
def real_converter() -> Any:
    from docling.document_converter import DocumentConverter
    ...

# Incorrect — triggers torch loading during collection
from docling.document_converter import DocumentConverter
```

### Async tests

With `asyncio_mode = "auto"`, declare any async test with `async def` and it runs automatically:

```python
async def test_ingest_returns_200(client: httpx.AsyncClient) -> None:
    response = await client.post("/ingest", files={"file": ...})
    assert response.status_code == 200
```

### HTTP endpoint tests

Use `httpx.AsyncClient` with `httpx.ASGITransport` for async endpoint tests. The `tests/adapters/http/conftest.py` `client` fixture provides a synchronous `TestClient` backed by a minimal FastAPI app with a mock service — suitable for unit-level router tests that do not require real Docling.

For end-to-end tests against the real service (no mocks), use `httpx.ASGITransport` directly, as shown in `tests/adapters/http/test_integration.py`:

```python
async def test_valid_pdf_returns_200(self, real_app: FastAPI) -> None:
    transport = httpx.ASGITransport(app=real_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/ingest",
            files={"file": ("sample.pdf", pdf_bytes, "application/pdf")},
        )
    assert response.status_code == 200
```

### Slow tests

Mark tests that run real Docling inference with `@pytest.mark.slow`:

```python
@pytest.mark.slow
def test_memory_leak_audit(real_converter: Any, real_pdf_path: Path | None) -> None:
    ...
```

## Fixtures

### Session-scoped fixtures (`tests/conftest.py`)

| Fixture | Scope | Description |
|---------|-------|-------------|
| `real_converter` | session | Single `DocumentConverter` shared for the entire session. Configured with `do_ocr=False` and `do_table_structure=True` for PDF; `SimplePipeline` for DOCX. Expensive AI model loading occurs once. |
| `real_pdf_path` | session | Path to `tests/fixtures/sample.pdf`, downloaded from orimi.com on first run. Returns `None` if download fails — tests must call `pytest.skip()`. |

The extractor conftest at `tests/adapters/extractor/conftest.py` also provides `real_docx_path` and `real_html_path` fixtures with the same lazy-download pattern.

### HTTP layer fixtures (`tests/adapters/http/conftest.py`)

| Fixture | Scope | Description |
|---------|-------|-------------|
| `mock_service` | function | `MagicMock(spec=ExtractionService)` for use in router unit tests. |
| `client` | function | Synchronous `TestClient` backed by a minimal FastAPI app. Skips full Docling lifespan — no model loading. |

### Test fixture files

Fixture files in `tests/fixtures/` are downloaded lazily on the first integration test run and cached locally. If a download fails (no internet access), the dependent test calls `pytest.skip()` rather than failing with an error.

Adversarial fixtures in `tests/fixtures/adversarial/` are generated by `tests/fixtures/generate_adversarial.py`. The `ensure_adversarial_fixtures` session-scoped fixture in `test_integration.py` runs this generator automatically if any adversarial file is missing.

## Coverage

No minimum coverage threshold is configured in `pyproject.toml`. Run with coverage manually:

```bash
uv run pytest --cov=src --cov-report=term-missing
```

`tests/` is excluded from strict mypy type checking (`exclude = ["tests/"]` in `pyproject.toml`).

## CI Integration

No CI workflow is currently configured in this repository. To run the test suite locally in a manner consistent with a future CI setup:

```bash
# Fast pass — unit tests only (no model loading)
uv run pytest -m "not slow"

# Full pass — all tests including integration
uv run pytest
```
