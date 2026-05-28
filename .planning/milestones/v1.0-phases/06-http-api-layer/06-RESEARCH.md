# Phase 6: HTTP API Layer - Research

**Researched:** 2026-05-24
**Domain:** FastAPI Adapter / HTTP API
**Confidence:** HIGH

## Summary

This research establishes the implementation patterns for the FastAPI adapter of SelectionMaid. The adapter serves as the entry point (`InputPort`) to the system, providing endpoints for document ingestion and health monitoring. 

Key architectural decisions include using a singleton `DocumentConverter` managed via FastAPI's `lifespan` context manager, offloading CPU-bound document processing to a separate thread using `run_in_threadpool`, and implementing a robust 3-layer validation process for file uploads (size, MIME type, and magic bytes).

**Primary recommendation:** Implement the API as a standalone adapter in `src/selection_maid/adapters/http/`, following the factory pattern `build_router(service)` to keep the domain core isolated from framework-specific logic.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| HTTP Routing | API / Backend | — | FastAPI handles request dispatching. |
| File Validation | API / Backend | — | Size, MIME, and magic bytes check happen before processing. |
| Doc Extraction | API / Backend | — | Docling-based extraction (CPU-bound). |
| Domain Orchestration| API / Backend | — | `ExtractionService` coordinates the pipeline. |
| Health Monitoring | API / Backend | — | RSS and uptime metrics via `psutil`. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.136.3 | Web framework | High performance, async support, auto-OpenAPI. [VERIFIED: npm registry fallback to uv dry-run] |
| Pydantic | 2.13.4 | Schema validation | Standard for FastAPI, fast Rust-based core. [VERIFIED: uv pip list] |
| uvicorn | 0.48.0 | ASGI server | Standard production-grade server for FastAPI. [VERIFIED: uv dry-run] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-magic | 0.4.27 | Magic bytes detection | Identifying real file types from content. [VERIFIED: uv dry-run] |
| psutil | 7.2.2 | System metrics | Reading process RSS for /health. [VERIFIED: uv pip list] |
| python-multipart| 0.0.29 | Form data parsing | Required for `UploadFile` support. [VERIFIED: uv dry-run] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `run_in_threadpool` | `ProcessPoolExecutor` | Process pool avoids GIL but adds serialization overhead and complexity. Thread pool is sufficient for current v1 traffic. |
| `python-magic` | `filetype` | `filetype` is pure Python but less comprehensive than `libmagic`. `python-magic` is the industry standard. |

**Installation:**
```bash
uv add fastapi pydantic uvicorn python-magic psutil python-multipart
```

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| fastapi | PyPI | 6 yrs | 20M/mo | github.com/fastapi/fastapi | [OK] | Approved |
| pydantic | PyPI | 7 yrs | 100M/mo | github.com/pydantic/pydantic | [OK] | Approved |
| uvicorn | PyPI | 7 yrs | 30M/mo | github.com/encode/uvicorn | [OK] | Approved |
| psutil | PyPI | 15 yrs | 80M/mo | github.com/giampaolo/psutil | [OK] | Approved |
| python-magic | PyPI | 13 yrs | 2M/mo | github.com/ahupp/python-magic | [OK] | Approved |
| python-multipart| PyPI | 10 yrs | 10M/mo | github.com/Kludex/python-multipart| [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### Recommended Project Structure
```
src/selection_maid/adapters/http/
├── __init__.py
├── app.py           # create_app() and lifespan
├── router.py        # build_router(service) and endpoint handlers
├── schemas.py       # Pydantic v2 schemas
└── error_map.py     # Domain code -> HTTP status mapping
```

### Pattern 1: Router Factory (D-85)
**What:** Decoupling the router definition from the service instance using a factory function that captures the service in a closure.
**When to use:** To allow the router to be tested in isolation or with different service implementations without global state.
**Example:**
```python
def build_router(service: ExtractionService) -> APIRouter:
    router = APIRouter()

    @router.post("/ingest", response_model=ExtractionResponse)
    async def ingest(file: UploadFile):
        # ... logic capturing service ...
        result = await run_in_threadpool(service.process, raw_input)
        return ExtractionResponse.model_validate(result)

    return router
```

### Pattern 2: 3-Layer Validation (API-03)
**What:** Sequential validation from fastest/cheapest to slowest/most expensive.
1. **Header check:** `Content-Length` (instant failure for obviously large files).
2. **Type check:** `file.content_type` (reject unsupported MIME types immediately).
3. **Content check:** Read 2048 bytes and use `python-magic` to verify the actual format.

### Anti-Patterns to Avoid
- **Blocking the event loop:** Never call `service.process` directly in an `async` route handler. Always use `run_in_threadpool`.
- **Manual Mapping:** Avoid manual `dict` construction for responses. Use Pydantic's `model_validate(obj, from_attributes=True)`.
- **Globals for dependencies:** Don't use global variables for `ExtractionService` or `DocumentConverter`. Use `lifespan` and factory functions.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File type detection | Custom byte signatures | `python-magic` | `libmagic` handles thousands of edge cases and complex signatures. |
| Thread management | `threading.Thread` | `run_in_threadpool` | Part of Starlette/FastAPI; correctly integrates with the asyncio event loop. |
| Object mapping | Manual field copying | Pydantic `from_attributes`| Reduced boilerplate, type safety, and automatic nested object conversion. |

## Common Pitfalls

### Pitfall 1: `NamedTemporaryFile` deletion on Windows
**What goes wrong:** Standard `NamedTemporaryFile` with `delete=True` cannot be opened by another process (or sometimes the same process if not handled carefully) while the file handle is open.
**How to avoid:** Use `delete=False`, close the handle immediately after writing, and use `os.unlink()` in a `finally` block.

### Pitfall 2: `libmagic` System Dependency
**What goes wrong:** `python-magic` requires the `libmagic` shared library. On Linux, it's often `libmagic1`. On Windows, you need `python-magic-bin`.
**How to avoid:** Explicitly document the requirement and consider `python-magic-bin` for development environments on non-Linux systems.

## Code Examples

### RSS Measurement with psutil (API-02)
```python
import psutil
import os

def get_rss_mb() -> float:
    # Source: [Official psutil docs]
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)
```

### Pydantic v2 from_attributes (D-77)
```python
from pydantic import BaseModel, ConfigDict

class ExtractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # ... fields ...

# Usage
response = ExtractionResponse.model_validate(extraction_result, from_attributes=True)
```

### Error Mapping (D-82)
```python
from selection_maid.errors import SelectionMaidError
from fastapi.responses import JSONResponse

ERROR_CODE_TO_HTTP = {
    "EXT-002": 415,
    "UPLOAD-001": 413,
    "UPLOAD-002": 422,
    # ...
}

def maid_error_handler(request, exc: SelectionMaidError):
    status_code = ERROR_CODE_TO_HTTP.get(exc.code, 500)
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": exc.code, "message": exc.message}}
    )
```

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1| `run_in_threadpool` is sufficient for Docling CPU load | Summary | If Docling is too heavy, GIL may block other requests significantly. |
| A2| `python-magic` is preferred over `filetype` | Tech Stack | `libmagic` system dependency might complicate deployment. |
| A3| `importlib.metadata.version` works in dev | Summary | Might return error if package is not installed via `uv`. |

## Open Questions (RESOLVED)

1. **Exact timeout for Docling:** Should we implement an explicit timeout in the router for v1? 
   - *Recommendation:* Postpone to Phase 7 integration testing; use 504 for domain timeout errors.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | ✓ | 3.14.5 | — |
| uv | Pkg Management | ✓ | 0.11.14 | — |
| libmagic1 | python-magic | ✓ | — | Manual install if missing |

**Missing dependencies with no fallback:**
- None.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | pyproject.toml |
| Quick run command | `pytest tests/adapters/http/ -x` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | `POST /ingest` returns schema | Integration| `pytest tests/adapters/http/test_router.py::test_ingest_success` | ❌ Wave 0 |
| API-02 | `GET /health` returns RSS | Unit | `pytest tests/adapters/http/test_router.py::test_health` | ❌ Wave 0 |
| API-03 | 3-layer validation | Integration| `pytest tests/adapters/http/test_router.py::test_validation` | ❌ Wave 0 |

### Wave 0 Gaps
- [ ] `tests/adapters/http/test_router.py` — endpoint testing.
- [ ] `tests/adapters/http/conftest.py` — FastAPI TestClient fixture.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | Size limit, MIME validation, Magic bytes check. |
| V12 File Upload | yes | Store in temp directory, strict extension/type check. |

### Known Threat Patterns for FastAPI

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Denial of Service (large files) | Availability | Enforce `Content-Length` and max body size. |
| Malicious file upload (spoofing) | Tampering | Magic bytes validation via `python-magic`. |

## Sources

### Primary (HIGH confidence)
- [FastAPI UploadFile docs] - `UploadFile` behavior and `run_in_threadpool`.
- [Pydantic v2 Migration Guide] - `from_attributes` and `model_validate`.
- [psutil docs] - Memory measurement patterns.

### Secondary (MEDIUM confidence)
- [Docling GitHub] - Path requirement for conversion.

### Tertiary (LOW confidence)
- [WebSearch] - `python-magic` implementation examples.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Core libs are de-facto standards.
- Architecture: HIGH - Hexagonal patterns are well-defined in project.
- Pitfalls: MEDIUM - Windows-specific tempfile behavior needs careful handling.

**Research date:** 2026-05-24
**Valid until:** 2026-06-23
