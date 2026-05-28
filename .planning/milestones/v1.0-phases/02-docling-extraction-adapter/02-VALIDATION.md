---
phase: 02
slug: docling-extraction-adapter
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-23
last_audited: 2026-05-25
---

# Phase 02 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/adapters/extractor/ -x -q --tb=short` |
| **Unit-only command** | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterUnit -q` |
| **Phase type-boundary command** | `uv run mypy src/selection_maid/adapters/extractor src/selection_maid/domain src/selection_maid/errors.py --strict` |
| **Full workspace command** | `uv run pytest tests/ -x -q && uv run mypy src/ --strict` |
| **Estimated runtime** | ~20 seconds for extractor suite with cached fixtures |

---

## Sampling Rate

- **After every extractor change:** Run `uv run pytest tests/adapters/extractor/ -x -q --tb=short`
- **After error or boundary changes:** Run `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterUnit -q`
- **After Docling import or adapter surface changes:** Run the phase type-boundary command above
- **Before cross-phase release:** Run `uv run pytest tests/ -x -q && uv run mypy src/ --strict`
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | EXT-01..EXT-03, D-21..D-30 | T-02-01, T-02-02, T-02-03 | CPU-only torch index, lazy Docling imports, fixture skips on download failure | static/unit | `uv run python -c "from selection_maid.adapters.extractor import DoclingAdapter, build_docling_adapter; print('import ok')"` | yes | green |
| 02-02-01 | 02 | 2 | EXT-01 | T-02-04, T-02-05, T-02-06, T-02-07 | PDF conversion errors are translated to domain errors | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterIntegration::test_pdf_extraction -q` | yes | green |
| 02-02-02 | 02 | 2 | EXT-02 | T-02-04, T-02-05, T-02-06, T-02-07 | DOCX conversion errors are translated to domain errors | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterIntegration::test_docx_extraction -q` | yes | green |
| 02-02-03 | 02 | 2 | EXT-03 | T-02-04, T-02-05, T-02-06, T-02-07 | HTML page_count is normalized to 0 | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterIntegration::test_html_extraction -q` | yes | green |
| 02-03-01 | 03 | 4 | EXT-04 | T-02-08 | Heading presence is checked while documenting Docling issue #1023 | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterIntegration::test_headings_in_pdf -q` | yes | green |
| 02-03-02 | 03 | 4 | EXT-05 | T-02-08 | GFM table markers are verified in DOCX Markdown | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterIntegration::test_tables_in_docx -q` | yes | green |
| 02-03-03 | 03 | 4 | EXT-06 | T-02-08 | Ordered or unordered list markers are verified in HTML Markdown | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterIntegration::test_lists_in_html -q` | yes | green |
| 02-03-04 | 03 | 4 | EXT-07 | T-02-08 | Inline HTML code blocks produce fenced Markdown | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterIntegration::test_code_blocks -q` | yes | green |
| 02-04-01 | 04 | 3 | D-24/D-25 | T-02-10 | Timeout is translated to `ExtractionTimeoutError` | unit | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterUnit::test_timeout_raises_extraction_timeout_error -q` | yes | green |
| 02-04-02 | 04 | 3 | D-30 | T-02-04 | Unsupported MIME types fail before Docling is called | unit | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterUnit::test_unsupported_format_raises -q` | yes | green |
| 02-04-03 | 04 | 3 | ARCH-01 | T-02-09 | Docling types remain inside the extractor adapter boundary | static | `uv run mypy src/selection_maid/adapters/extractor src/selection_maid/domain src/selection_maid/errors.py --strict` | yes | green |
| 02-05-01 | 05 | 5 | EXT-01..EXT-07, D-21, D-26 | T-02-11, T-02-12 | DoclingAdapter plugs into `ExtractionService`; converter fixture is singleton-scoped | integration | `uv run pytest tests/adapters/extractor/ -x -q --tb=short` | yes | green |

*Status: pending | green | red | flaky*

---

## Requirement Coverage

| Requirement | Coverage | Test Evidence |
|-------------|----------|---------------|
| EXT-01 | COVERED | `test_pdf_extraction`, `test_service_with_docling_adapter` |
| EXT-02 | COVERED | `test_docx_extraction` |
| EXT-03 | COVERED | `test_html_extraction` |
| EXT-04 | COVERED | `test_headings_in_pdf` |
| EXT-05 | COVERED | `test_tables_in_docx` |
| EXT-06 | COVERED | `test_lists_in_html` |
| EXT-07 | COVERED | `test_code_blocks` |
| ARCH-01 | COVERED | scoped mypy boundary command; bare extractor import check |
| D-21 | COVERED | `test_service_with_docling_adapter` |
| D-22/D-23 | COVERED | bare extractor import check and public factory export |
| D-24/D-25 | COVERED | `test_timeout_raises_extraction_timeout_error` |
| D-26 | COVERED | `test_converter_singleton_behavior` |
| D-27 | COVERED | fixture `Path | None` skip guards in integration tests |
| D-28/D-29 | COVERED | extraction format tests and `_build_raw_document()` assertions |
| D-30 | COVERED | `test_unsupported_format_raises` |

---

## Wave 0 Requirements

- [x] `tests/adapters/extractor/conftest.py` - session fixtures: `real_pdf_path`, `real_docx_path`, `real_html_path`
- [x] `tests/adapters/extractor/test_docling_adapter.py` - unit tests with mock converter and integration tests with real fixtures
- [x] `tests/fixtures/.gitkeep` - fixtures directory exists and cached fixture files are gitignored
- [x] `pyproject.toml` - `docling>=2.95.0` dependency plus CPU-only PyTorch uv index configuration

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | - | All Phase 02 requirements have automated coverage | - |

---

## Validation Audit 2026-05-25

| Metric | Count |
|--------|-------|
| Requirements audited | 15 |
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
| Automated checks run | 5 |

### Evidence

| Command | Result |
|---------|--------|
| `uv run pytest tests/adapters/extractor/ -x -q --tb=short` | PASS: 14 passed, 1 Docling deprecation warning |
| `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterUnit -q` | PASS: 5 passed |
| `uv run mypy src/selection_maid/adapters/extractor src/selection_maid/domain src/selection_maid/errors.py --strict` | PASS: no issues in 6 source files |
| `uv run python -c "from selection_maid.adapters.extractor import DoclingAdapter, build_docling_adapter; print('import ok')"` | PASS: import ok |
| `uv run pytest tests/ -x -q` | FAIL outside Phase 02: `tests/adapters/http/test_integration.py::TestAdversarialInputs::test_valid_html_returns_200` returned HTTP 422 instead of 200 after 116 passing tests |
| `uv run mypy src/ --strict` | FAIL outside Phase 02: `src/selection_maid/adapters/filter/heuristic.py:229` undefined `FilterConfig`; `src/selection_maid/adapters/http/router.py:30` missing `psutil` stubs |

Current workspace-wide gates are red due to later-phase HTTP/filter issues. Phase 02's extractor adapter requirements remain Nyquist-compliant under the scoped phase validation commands.

---

## Validation Sign-Off

- [x] All tasks have automated verify or resolved Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all previously missing references
- [x] No watch-mode flags
- [x] Feedback latency < 120s for Phase 02 suite
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** automated audit complete
