---
phase: 07-integration-hardening
slug: integration-hardening
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-25
updated: 2026-05-25
---

# Phase 7: Integration Hardening - Validation Strategy

Phase 7 validates production hardening around dirty inputs, Docling
thread-safety, memory behavior, liveness after failures, and tempfile cleanup.
Unlike earlier unit-heavy phases, most checks intentionally exercise the real
Docling pipeline and therefore load real models.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | pytest 9.x with pytest-asyncio |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run pytest tests/adapters/http/test_integration.py -q` |
| Full phase command | `uv run pytest tests/adapters/extractor/test_docling_adapter.py tests/adapters/http/test_integration.py tests/test_memory_regression.py` |
| Fixture generation | `uv run python tests/fixtures/generate_adversarial.py` |
| Estimated runtime | ~40 seconds after model cache is warm |

## Sampling Rate

- After Docling adapter changes: run `uv run pytest tests/adapters/extractor/test_docling_adapter.py -q`.
- After HTTP ingress changes: run `uv run pytest tests/adapters/http/test_integration.py -q`.
- After memory-management changes: run `uv run pytest tests/test_memory_regression.py -q`.
- Before `$gsd-verify-work`: run the full phase command.
- Max feedback latency: < 2 minutes for the full phase slice on a CPU-only machine.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | HARD-01, HARD-03 | T-07-03 | Adversarial fixtures are reproducibly generated, including a >40MB sample | Fixture/integration | `uv run python tests/fixtures/generate_adversarial.py` and `uv run pytest tests/adapters/http/test_integration.py -q` | yes | green |
| 07-01-02 | 01 | 1 | HARD-01 | T-07-01 | Docling access is serialized through an adapter lock; concurrent HTTP requests do not corrupt shared converter state | Integration/static | `uv run pytest tests/adapters/http/test_integration.py -k concurrency -q`; `rg 'threading.Lock' src/selection_maid/adapters/extractor/docling.py` | yes | green |
| 07-01-03 | 01 | 1 | HARD-02 | T-07-02 | Docling conversion unloads backend resources and triggers GC after extraction | Integration/static | `uv run pytest tests/test_memory_regression.py -q`; `rg 'gc.collect|_backend.unload' src/selection_maid/adapters/extractor/docling.py` | yes | green |
| 07-01-04 | 01 | 1 | HARD-03 | T-07-03 | Router tempfiles use the `selectionmaid_` prefix so leaks are auditable | Integration/static | `uv run pytest tests/adapters/http/test_integration.py -k cleanup -q`; `rg 'prefix="selectionmaid_"' src/selection_maid/adapters/http/router.py` | yes | green |
| 07-02-01 | 02 | 2 | HARD-01, API-01, API-03 | T-07-04 | Valid PDF/DOCX/HTML and adversarial PDFs produce expected HTTP outcomes without crashing | Integration | `uv run pytest tests/adapters/http/test_integration.py -k adversarial -q` | yes | green |
| 07-02-02 | 02 | 2 | HARD-04, API-02 | T-07-04 | `/health` remains responsive after a failing ingest request | Integration | `uv run pytest tests/adapters/http/test_integration.py -k liveness -q` | yes | green |
| 07-02-03 | 02 | 2 | HARD-01, HARD-04, API-01 | T-07-04 | Five simultaneous ingest requests complete successfully through the real ASGI stack | Integration | `uv run pytest tests/adapters/http/test_integration.py -k concurrency -q` | yes | green |
| 07-02-04 | 02 | 2 | HARD-03, API-03 | T-07-05 | `/tmp/selectionmaid_*` count returns to baseline after success and error paths | Integration | `uv run pytest tests/adapters/http/test_integration.py -k cleanup -q` | yes | green |
| 07-03-01 | 03 | 2 | HARD-02, API-02 | T-07-06 | RSS after repeated post-warmup conversions stays below 2x baseline | Slow integration | `uv run pytest tests/test_memory_regression.py -q` | yes | green |

## Gap Audit

| Gap | Resolution | Test/Command | Status |
|-----|------------|--------------|--------|
| No `07-VALIDATION.md` existed even though Phase 7 summaries and tests existed | Reconstructed this validation strategy from the plans, summaries, implementation, and test suite | This file | resolved |
| Valid XHTML-family HTML fixture was rejected as 422 because libmagic reported `application/xhtml+xml` while the upload declared `text/html` | Normalized the explicit `application/xhtml+xml` magic alias to `text/html` in the router before exact comparison | `uv run pytest tests/adapters/http/test_integration.py::TestAdversarialInputs::test_valid_html_returns_200 -q` | resolved |

## Automated Verification

### Suite 1: Adapter Hardening

- Location: `src/selection_maid/adapters/extractor/docling.py`, `tests/adapters/extractor/test_docling_adapter.py`
- Command: `uv run pytest tests/adapters/extractor/test_docling_adapter.py -q`
- Success: 14 tests pass; existing extraction behavior remains compatible after lock and GC hardening.

### Suite 2: E2E Adversarial and Reliability Tests

- Location: `tests/adapters/http/test_integration.py`
- Command: `uv run pytest tests/adapters/http/test_integration.py -q`
- Success: 11 tests pass; valid PDF/DOCX/HTML, corrupt/empty/spoofed/protected/large PDFs, liveness, concurrency, and tempfile cleanup are covered.

### Suite 3: Memory Regression

- Location: `tests/test_memory_regression.py`
- Command: `uv run pytest tests/test_memory_regression.py -q`
- Success: 1 slow test passes; post-warmup RSS growth remains under the 2x threshold.

### Suite 4: Static Hardening Checks

- Location: `src/selection_maid/adapters/extractor/docling.py`, `src/selection_maid/adapters/http/router.py`
- Command: `rg 'threading.Lock|gc.collect|_backend.unload|prefix="selectionmaid_"' src/selection_maid/adapters/extractor/docling.py src/selection_maid/adapters/http/router.py`
- Success: lock, backend unload, explicit GC, and tempfile prefix hooks are present.

## Latest Validation Run

Commands:

```bash
uv run pytest tests/adapters/http/test_integration.py -q
uv run pytest tests/adapters/extractor/test_docling_adapter.py -q
uv run pytest tests/test_memory_regression.py -q
```

Results:

| Command | Result |
|---------|--------|
| `uv run pytest tests/adapters/http/test_integration.py -q` | 11 passed, 1 warning in 13.57s |
| `uv run pytest tests/adapters/extractor/test_docling_adapter.py -q` | 14 passed, 1 warning in 12.44s |
| `uv run pytest tests/test_memory_regression.py -q` | 1 passed, 1 warning in 11.27s |

Warnings are Docling deprecation warnings from `standard_pdf_pipeline.py` and do
not affect Phase 7 behavior.

## Manual-Only Verifications

All Phase 7 hardening behaviors have automated verification.

## Validation Audit 2026-05-25

| Metric | Count |
|--------|-------|
| Gaps found | 2 |
| Resolved | 2 |
| Escalated | 0 |

## Validation Sign-Off

- [x] All tasks have automated verification or an explicit manual-only rationale.
- [x] Sampling continuity has no 3 consecutive tasks without automated verification.
- [x] Wave 0/test infrastructure covers all missing references.
- [x] No watch-mode flags.
- [x] Feedback latency < 2 minutes for the phase validation slice.
- [x] `nyquist_compliant: true` set in frontmatter.

Approval: approved 2026-05-25
