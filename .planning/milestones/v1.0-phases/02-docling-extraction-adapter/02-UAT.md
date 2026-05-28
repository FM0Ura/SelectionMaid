---
status: testing
phase: 02-docling-extraction-adapter
source: [02-01-SUMMARY.md, 02-02-SUMMARY.md, 02-03-SUMMARY.md, 02-04-SUMMARY.md, 02-05-SUMMARY.md]
started: 2026-05-25T01:00:00Z
updated: 2026-05-25T01:00:00Z
---

## Current Test

number: 4
name: Domain Error Pass-Through (No Double-Wrapping)
expected: |
  Running `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterUnit::test_domain_error_propagates_unchanged -v` passes. A `SelectionMaidError` raised inside the converter is re-raised unchanged — not wrapped in another domain error.
awaiting: user response

## Tests

### 1. DoclingAdapter Fast Import (No Torch Loading)
expected: Running `time python -c "from selection_maid.adapters.extractor import DoclingAdapter"` completes in under 2 seconds. The TYPE_CHECKING guard prevents torch/docling from loading on bare import — if it takes 30+ seconds, the guard is broken.
result: pass

### 2. MIME Type Guard — Unsupported Format Raises
expected: Running `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterUnit::test_unsupported_format_raises -v` passes. An unsupported MIME type (e.g. `text/csv`) raises `UnsupportedFormatError` before any Docling conversion happens.
result: pass

### 3. Timeout Raises ExtractionTimeoutError
expected: Running `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterUnit::test_timeout_raises_extraction_timeout_error -v` passes. A converter that sleeps longer than `timeout_seconds` causes `ExtractionTimeoutError` (not the raw `concurrent.futures.TimeoutError`).
result: pass

### 4. Domain Error Pass-Through (No Double-Wrapping)
expected: Running `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterUnit::test_domain_error_propagates_unchanged -v` passes. A `SelectionMaidError` raised inside the converter is re-raised unchanged — not wrapped in another domain error.
result: [pending]

### 5. DOCX Extraction — RawDocument with Content
expected: Running `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterIntegration::test_docx_extraction -v` passes. A real DOCX file is converted to a `RawDocument` with non-empty `content` (Markdown string) and `page_count >= 0`.
result: [pending]

### 6. HTML Extraction — RawDocument with page_count 0
expected: Running `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterIntegration::test_html_extraction -v` passes. A real HTML file converts to a `RawDocument` with non-empty `content` and `page_count == 0` (HTML has no concept of pages, D-29).
result: [pending]

### 7. Markdown Structure — GFM Tables in DOCX (EXT-05)
expected: Running `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterIntegration::test_tables_in_docx -v` passes. The Markdown output from a DOCX with a table contains `|` and `---` (GFM table syntax).
result: [pending]

### 8. Markdown Structure — List Markers in HTML (EXT-06)
expected: Running `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterIntegration::test_lists_in_html -v` passes. The Markdown output from an HTML file with a list contains at least one of `- `, `* `, or `1. `.
result: [pending]

### 9. Markdown Structure — Code Fences via HTML (EXT-07)
expected: Running `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterIntegration::test_code_blocks -v` passes (never skips — uses tmp_path). A minimal HTML file with `<pre><code>` produces Markdown with triple-backtick fences.
result: [pending]

### 10. DocumentConverter Singleton Contract
expected: Running `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterIntegration::test_converter_singleton_behavior -v` passes (never skips — unconditional). Two DoclingAdapter instances built from the same session fixture share the same `_converter` object identity.
result: [pending]

### 11. Full Test Suite Green
expected: Running `uv run pytest tests/ -q` exits 0. At least 38 tests pass; skips are allowed only for PDF-dependent tests (fixture not available). Zero failures, zero errors.
result: [pending]

### 12. Mypy Strict — ARCH-01 Boundary Intact
expected: Running `uv run mypy src/ --strict` exits with "Success: no issues found". No Docling types (DocumentConverter, ConversionResult, etc.) appear outside `src/selection_maid/adapters/extractor/`.
result: [pending]

## Summary

total: 12
passed: 0
issues: 0
pending: 12
skipped: 0
blocked: 0

## Gaps

[none yet]
