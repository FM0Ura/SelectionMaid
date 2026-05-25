# Phase 7: Integration Hardening - Context

**Gathered:** 2026-05-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 focuses on the end-to-end reliability and stability of SelectionMaid. It transforms the functional service into a hardened system capable of handling "dirty" inputs, high concurrency, and long-running sessions without degradation.

Key deliverables:
- **Edge-case Fixtures:** Implementation of "adversarial" documents (corrupt, empty, password-protected, large 40MB+, spoofed extensions).
- **Proactive Memory Management:** Integration of explicit garbage collection (`gc.collect()`) in the processing pipeline to mitigate Docling's memory footprint.
- **Concurrency Verification:** Stress tests with 5 simultaneous requests to ensure thread safety and monitor RAM behavior.
- **Liveness & Recovery:** Verification that the server recovers gracefully from any processing failure and strictly cleans up all temporary resources.

**Out of Scope:** Automatic model refresh strategy (deferred to v2), real-time 120s timeout waiting tests (focused on liveness instead).

</domain>

<decisions>
## Implementation Decisions

### Adversarial Fixtures (REQUIREMENTS: ALL)

- **D-91:** Create a "dirty" fixture set in `tests/fixtures/adversarial/`:
  - `corrupt.pdf`: Invalid PDF structure (e.g., random bytes with .pdf extension).
  - `empty.pdf`: 0-byte file.
  - `protected.pdf`: PDF with owner password/encryption.
  - `large_sample.pdf`: A ~40-45MB document to test disk I/O and near-limit memory.
  - `spoofed.pdf`: A plain text file renamed to .pdf (validates Magic Bytes check).
- **D-92:** Integration tests in `tests/adapters/http/test_integration.py` must iterate through all fixtures (normal and adversarial) and verify expected HTTP outcomes (200 for normal, 4xx/5xx for adversarial).

### Proactive Memory Management (D-26 update)

- **D-93:** The `ExtractionService` or `DoclingAdapter` will trigger `gc.collect()` immediately after an extraction finishes (in a `finally` block). This ensures that heavy Docling objects are marked for collection before the next request starts.
- **D-94:** RSS Monitoring: Integration tests will capture RSS before and after a batch of 20 conversions. The test fails if `RSS_final > 2 * RSS_initial`.

### Concurrency Stress (ARCH-05, API-01)

- **D-95:** The concurrency test will use `asyncio.gather` with 5 simultaneous `POST /ingest` requests using different file types.
- **D-96:** Success criteria for concurrency: 0 failures, all tempfiles deleted, and peak RSS does not trigger system OOM (monitored via `psutil`).

### Liveness and Cleanup (API-03, D-87)

- **D-97:** "Liveness" is defined as the server's ability to respond to `GET /health` with HTTP 200 immediately after a catastrophic extraction failure (e.g., a process-crashing corrupt file).
- **D-98:** Strict Tempfile Accounting: Tests must verify that `/tmp` (or the configured temp dir) contains zero `selectionmaid_*` files after the test suite completes.

</decisions>

<canonical_refs>
## Canonical References

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 7 goals and success criteria.
- `.planning/REQUIREMENTS.md` — All v1 requirements (final verification phase).

### Existing Integration Tests
- `tests/adapters/extractor/test_docling_adapter.py` — Existing integration tests with real Docling. Re-use the `real_converter` fixture.
- `tests/adapters/http/test_router.py` — Existing unit tests with mocked service. Use as blueprint for `test_integration.py`.

### Domain & Service
- `src/selection_maid/service.py` — Pipeline entry point.
- `src/selection_maid/adapters/extractor/docling.py` — Main memory consumer; target for `gc.collect()`.
- `src/selection_maid/adapters/http/router.py` — Target for concurrency and RSS monitoring.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/adapters/extractor/conftest.py` — `real_converter` session-scoped fixture.
- `tests/fixtures/` — `sample.pdf`, `sample.docx`, `sample.html`.
- `psutil` — Used in `router.py` for health checks; reuse for memory regression tests.

### Established Patterns
- **run_in_threadpool (D-88):** Already used in `router.py`. Phase 7 verifies its effectiveness under load.
- **Tempfile Cleanup (D-87):** `finally` block in `router.py` handles deletion. Phase 7 audits this.

### Integration Points
- `tests/adapters/http/test_integration.py` — New file for end-to-end API tests with real adapters.
- `tests/test_memory_regression.py` — New file for the 20-conversion leak test.

</code_context>

<deferred>
## Deferred Ideas

- **Automatic Model Refresh Strategy:** Re-instantiating `DocumentConverter` when memory hits a threshold. Postponed to v2 as `gc.collect()` is the primary hardening tool for v1.
- **Per-core Concurrency Scaling:** Dynamically scaling the number of test workers based on CPU. Fixed at 5 for stability across different environments.
- **Real-time 120s Timeout Test:** Actually waiting 120s for a slow doc. Too slow for standard CI; focused on liveness and error recovery instead.

</deferred>
