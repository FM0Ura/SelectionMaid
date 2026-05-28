# Testing Patterns

**Analysis Date:** 2026-05-27

## Test Framework

**Runner:**
- Backend: pytest `>=9.0.3` with pytest-asyncio `>=1.3.0`, configured in `pyproject.toml`.
- Frontend: Vitest `^4.1.7` with jsdom `^29.1.1`, configured in `frontend/vitest.config.ts`.
- Frontend Vue components use `@vue/test-utils` `^2.4.10`, declared in `frontend/package.json`.
- Config: `pyproject.toml` for backend pytest, ruff, and mypy; `frontend/vitest.config.ts` for frontend Vitest.

**Assertion Library:**
- Backend: pytest built-in `assert`, `pytest.raises`, `pytest.skip`, and `pytest.mark.parametrize`, as used in `tests/domain/test_models.py`, `tests/domain/test_service.py`, and `tests/adapters/http/test_error_map.py`.
- Frontend: Vitest `expect`, including `toEqual`, `toBe`, `toContain`, `toMatchObject`, and async `rejects`, as used in `frontend/src/api/ingest.spec.ts` and `frontend/src/composables/useUpload.spec.ts`.

**Run Commands:**
```bash
uv run pytest                         # Run backend tests from pyproject.toml testpaths
uv run pytest -m "not slow"           # Run backend tests excluding slow Docling/model tests
uv run pytest -m slow                 # Run only slow backend integration tests
uv run pytest tests/domain/test_service.py  # Run one backend test file
uv run ruff check src tests           # Backend lint check
uv run mypy src                       # Backend strict type check
cd frontend && npm run test:unit      # Run frontend Vitest in default watch mode
cd frontend && npx vitest run         # Run frontend Vitest once for CI-style verification
cd frontend && npm run build          # Frontend typecheck and production build
```

## Test File Organization

**Location:**
- Backend tests live under `tests/` and mirror backend architecture layers: `tests/domain/`, `tests/adapters/chunker/`, `tests/adapters/extractor/`, `tests/adapters/filter/`, `tests/adapters/enricher/`, and `tests/adapters/http/`.
- Backend shared fixtures live in `tests/conftest.py`; HTTP adapter fixtures live in `tests/adapters/http/conftest.py`; extractor-specific fixtures live in `tests/adapters/extractor/conftest.py`.
- Backend reusable test doubles live in `tests/stubs/adapters.py`.
- Frontend tests live under `frontend/src/` next to the unit under test or in component `__tests__/` directories, for example `frontend/src/api/ingest.spec.ts`, `frontend/src/composables/useUpload.spec.ts`, and `frontend/src/components/upload/__tests__/DropZone.spec.ts`.

**Naming:**
- Backend test files use `test_*.py`, for example `tests/adapters/http/test_router.py`.
- Backend test classes use `Test*`, for example `TestPipeline` and `TestMarkdownChunkerIntegration` in `tests/domain/test_service.py`.
- Backend test functions use `test_*` with behavior-specific names, for example `test_validation_magic_spoofed_pdf_returns_422` in `tests/adapters/http/test_router.py`.
- Frontend test files use `*.spec.ts`, for example `frontend/src/lib/validators.spec.ts` and `frontend/src/components/result/MarkdownRenderer.spec.ts`.
- Frontend suites use `describe('<unit name>')` and `it('<behavior>')`, as in `frontend/src/composables/useUpload.spec.ts`.

**Structure:**
```text
tests/
├── conftest.py
├── stubs/adapters.py
├── domain/test_*.py
├── adapters/<adapter>/test_*.py
└── fixtures/

frontend/src/
├── api/*.spec.ts
├── composables/*.spec.ts
├── lib/*.spec.ts
├── types/*.spec.ts
└── components/**/{*.spec.ts,__tests__/*.spec.ts}
```

## Test Structure

**Suite Organization:**
```python
class TestPipeline:
    def test_process_returns_extraction_result(
        self, stub_service: ExtractionService, raw_input: RawInput
    ) -> None:
        result = stub_service.process(raw_input)
        assert isinstance(result, ExtractionResult)
```

```typescript
describe('useUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('starts in idle state', () => {
    const upload = useUpload()

    expect(upload.state.value).toEqual({ status: 'idle' })
  })
})
```

**Patterns:**
- Group backend tests by behavior-focused classes when a module has many cases, as in `tests/domain/test_service.py` and `tests/adapters/http/test_router.py`.
- Use plain module-level tests for narrow mappings or schema checks, as in `tests/adapters/http/test_error_map.py` and `tests/test_config.py`.
- Use fixture injection for shared services, input values, clients, and expensive external converters, as in `tests/domain/test_service.py`, `tests/conftest.py`, and `tests/adapters/http/conftest.py`.
- Keep frontend setup inside `beforeEach()` and cleanup inside `afterEach()` when mocks, timers, globals, or refs are mutated, as in `frontend/src/composables/useUpload.spec.ts`, `frontend/src/api/ingest.spec.ts`, and `frontend/src/components/upload/__tests__/DropZone.spec.ts`.
- Use `data-testid` selectors for UI states that are structural or interactive, for example `frontend/src/components/upload/__tests__/DropZone.spec.ts`.

## Mocking

**Framework:** Backend uses explicit stubs plus `unittest.mock.MagicMock`; frontend uses Vitest `vi.mock`, `vi.fn`, `vi.mocked`, `vi.stubGlobal`, fake timers, and Vue Test Utils `mount`.

**Patterns:**
```python
@pytest.fixture
def mock_service() -> MagicMock:
    """Return a MagicMock that satisfies the ExtractionService interface."""
    return MagicMock(spec=ExtractionService)
```

```typescript
vi.mock('@/api/ingest', () => ({
  postIngest: vi.fn(),
}))

const postIngestMock = vi.mocked(postIngest)
```

**What to Mock:**
- Mock the HTTP router's `ExtractionService` with `MagicMock(spec=ExtractionService)` in `tests/adapters/http/conftest.py` so router unit tests avoid Docling model loading.
- Use explicit backend stub adapters from `tests/stubs/adapters.py` for service tests that exercise orchestration without infrastructure.
- Mock browser/network APIs in frontend tests. Use `vi.stubGlobal('fetch', fetchMock)` in `frontend/src/api/ingest.spec.ts`, `vi.stubGlobal('URL', ...)` in `frontend/src/components/result/ChunkCard.spec.ts`, and `vi.mock('@vueuse/core', ...)` in `frontend/src/components/upload/__tests__/DropZone.spec.ts`.
- Mock frontend composables when component tests should focus on rendering and event wiring, as in `frontend/src/components/upload/__tests__/DropZone.spec.ts`.

**What NOT to Mock:**
- Do not mock pure value objects or dataclasses in `src/selection_maid/domain/models.py`; instantiate real `RawInput`, `RawDocument`, `DocumentChunk`, `DocumentMetadata`, and `ExtractionResult` in tests.
- Do not load real Docling in unit tests. Tests that invoke real document conversion belong in slow integration files such as `tests/adapters/extractor/test_docling_adapter.py` or `tests/adapters/http/test_integration.py`.
- Do not mock simple frontend validators/formatters when testing their own behavior; use direct input/output tests in `frontend/src/lib/validators.spec.ts` and `frontend/src/lib/formatters.spec.ts`.

## Fixtures and Factories

**Test Data:**
```python
@pytest.fixture(scope="session")
def raw_input() -> RawInput:
    return RawInput(
        path=Path("/tmp/test.pdf"),
        filename="test.pdf",
        mime_type="application/pdf",
    )
```

```typescript
function pdfFile() {
  return new File(['content'], 'paper.pdf', { type: 'application/pdf' })
}
```

**Location:**
- Backend shared fixtures: `tests/conftest.py`.
- Backend HTTP adapter fixtures: `tests/adapters/http/conftest.py`.
- Backend extractor fixtures: `tests/adapters/extractor/conftest.py`.
- Backend stub adapters: `tests/stubs/adapters.py`.
- Backend downloaded or generated document fixtures: `tests/fixtures/`.
- Frontend factories are local to each spec file, for example `pdfFile()` and `extractionResponse` in `frontend/src/composables/useUpload.spec.ts` and `frontend/src/api/ingest.spec.ts`.
- Integration fixture downloads should return `None` on failure and tests should call `pytest.skip()`, matching `tests/conftest.py` and `tests/adapters/extractor/conftest.py`.

## Coverage

**Requirements:** No enforced minimum coverage threshold is configured in `pyproject.toml`, `frontend/vitest.config.ts`, or `frontend/package.json`.

**View Coverage:**
```bash
uv run pytest --cov=src --cov-report=term-missing   # Backend, requires pytest-cov
cd frontend && npx vitest run --coverage            # Frontend, requires Vitest coverage provider setup
```

## Test Types

**Unit Tests:**
- Backend unit tests cover domain immutability, service orchestration, adapters with stubs/mocks, schemas, and error mapping. Examples: `tests/domain/test_models.py`, `tests/domain/test_service.py`, `tests/adapters/filter/test_heuristic_filter.py`, and `tests/adapters/http/test_router.py`.
- Frontend unit tests cover API clients, error mapping, validators, formatters, types, composables, and Vue components. Examples: `frontend/src/api/ingest.spec.ts`, `frontend/src/composables/useUpload.spec.ts`, `frontend/src/lib/validators.spec.ts`, and `frontend/src/components/result/ResultView.spec.ts`.

**Integration Tests:**
- Backend integration tests cover real adapter wiring and real document conversion where needed. Examples include `TestMarkdownChunkerIntegration` in `tests/domain/test_service.py`, `tests/adapters/extractor/test_docling_adapter.py`, `tests/adapters/http/test_integration.py`, and `tests/test_memory_regression.py`.
- Slow or resource-heavy integration tests use `@pytest.mark.slow`, as in `tests/test_memory_regression.py`.
- HTTP integration tests use `httpx.AsyncClient`/ASGI transport patterns and async pytest tests in `tests/adapters/http/test_integration.py`.

**E2E Tests:**
- Browser E2E testing is not used. No Playwright, Cypress, or similar E2E configuration was detected.
- Current frontend tests are component/unit tests running in jsdom through Vitest and Vue Test Utils.

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_ingest_pdf_success(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/ingest",
        files={"file": ("sample.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
```

```typescript
it('transitions failed uploads to error with the mapped message', async () => {
  postIngestMock.mockRejectedValue(new DOMException('Timed out', 'AbortError'))

  await upload.startUpload(pdfFile())

  expect(upload.state.value.status).toBe('error')
})
```

**Error Testing:**
```python
with pytest.raises(ExtractionError) as exc_info:
    service.process(raw_input)

assert exc_info.value.cause is not None
```

```typescript
await expect(
  postIngest(new File(['content'], 'paper.pdf', { type: 'application/pdf' })),
).rejects.toMatchObject({
  status: 413,
  code: 'UPLOAD-001',
  message: 'File too large',
})
```

---

*Testing analysis: 2026-05-27*
