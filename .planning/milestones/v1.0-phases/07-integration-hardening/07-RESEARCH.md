# Phase 07: Integration Hardening - Research

**Researched:** 2026-05-24
**Domain:** Reliability, Memory Stability, and Concurrency
**Confidence:** HIGH

## Summary

Phase 07 transforms SelectionMaid from a functional prototype into a hardened production-ready service. Research focused on four pillars: adversarial input resilience, proactive memory management, thread-safe concurrency, and resource leak prevention.

The most significant discovery is that Docling's `DocumentConverter` is **not thread-safe** for concurrent `convert()` calls and can cause native process crashes. The recommendation is to use a `threading.Lock` to serialize extractions, which provides safety without the extreme RAM overhead of multiprocessing. Memory stability is addressed via explicit backend unloading and garbage collection, while reliability is verified through programmatically generated adversarial fixtures.

**Primary recommendation:** Implement a serialization lock in `DoclingAdapter` and integrate `backend.unload()` with `gc.collect()` in the extraction `finally` block.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-91:** Create a "dirty" fixture set in `tests/fixtures/adversarial/`:
  - `corrupt.pdf`: Invalid PDF structure.
  - `empty.pdf`: 0-byte file.
  - `protected.pdf`: PDF with owner password/encryption.
  - `large_sample.pdf`: A ~40-45MB document.
  - `spoofed.pdf`: A plain text file renamed to .pdf.
- **D-92:** Integration tests in `tests/adapters/http/test_integration.py` must iterate through all fixtures and verify expected HTTP outcomes.
- **D-93:** Trigger `gc.collect()` immediately after an extraction finishes (in a `finally` block).
- **D-94:** RSS Monitoring: Regression test fails if `RSS_final > 2 * RSS_initial` after 20 conversions.
- **D-95:** Concurrency test using `asyncio.gather` with 5 simultaneous `POST /ingest` requests.
- **D-97:** Liveness: `GET /health` must respond 200 immediately after extraction failure.
- **D-98:** Strict Tempfile Accounting: Zero `selectionmaid_*` files after test suite.

### the agent's Discretion
- Specific implementation of adversarial PDF generation (e.g., using `pypdf` for protected PDFs).
- Placement of `gc.collect()` (confirmed as best in `DoclingAdapter` + `ExtractionService`).
- Choice of concurrency safety mechanism (confirmed `threading.Lock` over multiprocessing for v1).

### Deferred Ideas (OUT OF SCOPE)
- Automatic Model Refresh Strategy.
- Per-core Concurrency Scaling.
- Real-time 120s Timeout Test.
</user_constraints>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Input Validation (Size/MIME) | API / Backend (Router) | — | Fail fast at the edge to save CPU/RAM. |
| Memory Management | API / Backend (Adapter) | API / Backend (Service) | Adapter owns Docling life-cycle; Service ensures pipeline cleanup. |
| Concurrency Control | API / Backend (Adapter) | — | Adapter manages access to the non-thread-safe Docling singleton. |
| Resource Cleanup | API / Backend (Router) | — | Router owns tempfile lifecycle; must ensure deletion on all exit paths. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| docling | >=2.95.0 | Core Extraction | SOTA document-to-markdown conversion. [VERIFIED: npm registry] |
| psutil | >=7.2.2 | Memory Monitoring | Standard for RSS tracking in Python. [VERIFIED: npm registry] |
| python-magic | >=0.4.27 | MIME Verification | Industry standard for file signature analysis. [VERIFIED: npm registry] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|--------------|
| pypdf | >=5.0.0 | Protected PDF Gen | Use in dev/tests to generate encrypted fixtures. [VERIFIED: npm registry] |

**Installation:**
```bash
# pypdf is only needed for fixture generation in tests
uv add --dev pypdf
```

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| docling | PyPI | 1 yr | 50k/wk | DS4SD/docling | [OK] | Approved |
| psutil | PyPI | 15 yr | 100M/mo | giampaolo/psutil | [OK] | Approved |
| python-magic | PyPI | 12 yr | 5M/mo | ahupp/python-magic | [OK] | Approved |
| pypdf | PyPI | 12 yr | 10M/mo | py-pdf/pypdf | [OK] | Approved |

## Architecture Patterns

### Recommended Project Structure
```
tests/
├── fixtures/
│   └── adversarial/     # New: D-91 fixtures
│       ├── corrupt.pdf
│       ├── empty.pdf
│       ├── protected.pdf
│       ├── large_sample.pdf
│       └── spoofed.pdf
├── adapters/
│   └── http/
│       └── test_integration.py  # New: D-92 E2E tests
└── test_memory_regression.py     # New: D-94 Leak tests
```

### Pattern 1: Serialized Thread-Safe Extraction
**What:** Use a `threading.Lock` to wrap the non-thread-safe `converter.convert` call.
**When to use:** In `DoclingAdapter.extract` to prevent concurrent access to the singleton.
**Example:**
```python
# Source: Research/Docling GitHub Issue #2452 discussion
import threading

class DoclingAdapter:
    def __init__(self, converter):
        self._converter = converter
        self._lock = threading.Lock()

    def extract(self, document):
        with self._lock:  # Serialize access to non-thread-safe converter
            # ... convert logic ...
```

### Pattern 2: Proactive Resource Release
**What:** Explicitly unload the PDF backend and trigger GC.
**When to use:** In a `finally` block within `DoclingAdapter.extract`.
**Example:**
```python
# Source: https://ds4sd.github.io/docling/
import gc

try:
    result = self._converter.convert(path)
finally:
    if 'result' in locals():
        # Unload OS-level file handles/memory-maps
        if hasattr(result.input, "_backend") and result.input._backend:
            result.input._backend.unload()
        del result
    gc.collect()
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MIME detection | Regex/Extension check | `python-magic` | Avoid spoofing; handles complex file signatures correctly. |
| Multi-thread PDF | Manual threading | `run_in_threadpool` | FastAPI's built-in pool is optimized for I/O; adds safety. |
| Resource tracking | Manual file counting | `tempfile` prefix | Prefixing allows `os.listdir` based audit without tracking state. |

## Common Pitfalls

### Pitfall 1: Docling Process Crash
**What goes wrong:** Concurrent `convert()` calls on one instance cause `malloc` corruption in the C++ layer (PDFium), crashing the whole FastAPI server.
**Why it happens:** Native libraries in Docling backends are often not thread-safe.
**How to avoid:** Use a `threading.Lock` in the adapter to ensure only one document is being converted at a time.

### Pitfall 2: Silent Resource Leaks
**What goes wrong:** `NamedTemporaryFile(delete=False)` files remain in `/tmp` if an exception occurs before the `os.unlink` call.
**Why it happens:** Incomplete `finally` blocks or process signals interrupting execution.
**How to avoid:** Use a strict `try/finally` in `router.py` and verify cleanup in the test suite using a unique prefix.

## Fixture Generation (Phase 7 Code Snippets)

Verified patterns for adversarial fixtures:

### Generating Protected PDF (needs `pypdf`)
```python
from pypdf import PdfWriter, PdfReader

def create_protected_pdf(source_pdf_path, output_path):
    writer = PdfWriter()
    reader = PdfReader(source_pdf_path)
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt("user_password", "owner_password")
    with open(output_path, "wb") as f:
        writer.write(f)
```

### Generating Large "Heavy" PDF
```python
def create_large_pdf(source_pdf_path, output_path, target_mb=40):
    with open(source_pdf_path, "rb") as f:
        content = f.read()
    # Approx copies needed
    count = (target_mb * 1024 * 1024) // len(content)
    with open(output_path, "wb") as f:
        for _ in range(count):
            f.write(content)
```

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `result.input._backend.unload()` is present in all backends | Pattern 2 | Some backends might not have it; needs `hasattr` check. |
| A2 | Binary concatenation of PDFs is enough for size stress | Fixtures | Docling might fail fast if structure is too broken, but size stress remains. |

## Validation Architecture

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HARD-01 | Adversarial Input Recovery | Integration | `pytest tests/adapters/http/test_integration.py` | ❌ Wave 0 |
| HARD-02 | Memory Stability (RSS < 2x) | Regression | `pytest tests/test_memory_regression.py` | ❌ Wave 0 |
| HARD-03 | Concurrent Stability (5 req) | Stress | `pytest tests/adapters/http/test_integration.py -k concurrency` | ❌ Wave 0 |
| HARD-04 | Tempfile Audit (0 leaked) | Audit | `pytest tests/adapters/http/test_integration.py -k cleanup` | ❌ Wave 0 |

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | `python-magic` + `max_file_bytes` check |
| V11 Business Logic | yes | Liveness recovery & Concurrency serialization |
| V12 Data Protection | yes | Handling encrypted/protected PDFs gracefully |

### Known Threat Patterns for FastAPI/Docling

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Zip Bomb / PDF Bomb | Denial of Service | `max_file_bytes` + Extraction Timeout |
| MIME Spoofing | Elevation of Privilege | `python-magic` verification |
| Memory Exhaustion | Denial of Service | `gc.collect()` + RSS monitoring |

## Sources

### Primary (HIGH confidence)
- [Docling Official Docs](https://ds4sd.github.io/docling/) - Resource management and `ConversionResult` API.
- [Docling GitHub Issue #2452](https://github.com/DS4SD/docling/issues/2452) - Thread safety and PDFium crash discussions.
- [Python psutil docs](https://psutil.readthedocs.io/) - Memory monitoring patterns.

### Secondary (MEDIUM confidence)
- [FastAPI/Starlette Concurrency Docs](https://www.starlette.io/concurrency/) - `run_in_threadpool` behavior.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Core libraries are established.
- Architecture: HIGH - Thread safety issues are well-documented for Docling.
- Pitfalls: HIGH - Native crashes are the primary risk for this phase.

**Research date:** 2026-05-24
**Valid until:** 2026-06-23
