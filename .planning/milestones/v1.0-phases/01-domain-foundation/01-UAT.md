---
status: complete
phase: 01-domain-foundation
source: [01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md, 01-04-SUMMARY.md, 01-05-SUMMARY.md]
started: 2026-05-25T00:00:00Z
updated: 2026-05-25T01:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Domain Models Import and Immutability
expected: Running `uv run python -c "from selection_maid.domain.models import RawInput, RawDocument, DocumentChunk, DocumentMetadata, ExtractionResult; print('ok')"` prints `ok` without errors. Attempting to mutate a frozen dataclass (e.g. `chunk = DocumentChunk(...); chunk.content = 'x'`) raises `FrozenInstanceError`. Using `dataclasses.replace()` returns a new instance without error.
result: pass

### 2. Port Contracts Import
expected: Running `uv run python -c "from selection_maid.domain.ports import ExtractorPort, FilterPort, ChunkerPort, MetadataEnricherPort; print('ok')"` prints `ok`. The four Protocol classes are present and importable from `selection_maid.domain.ports`.
result: pass

### 3. ExtractionService Pipeline
expected: Running `uv run python -c "from selection_maid.service import ExtractionService; print(ExtractionService.__module__)"` prints `selection_maid.service`. The service accepts four adapter instances via constructor (extractor, filter_, chunker, enricher) and calls `.process(raw_input)` to run the extract → filter → chunk → enrich pipeline, returning an `ExtractionResult`.
result: pass

### 4. Domain Error Taxonomy
expected: Running `uv run python -c "from selection_maid.errors import SelectionMaidError, ExtractionError, UnsupportedFormatError, ExtractionTimeoutError, FilterError, ChunkingError, EnrichmentError; print(ExtractionError.code)"` prints `EXT-001`. All six subclasses inherit from `SelectionMaidError`. `UnsupportedFormatError` carries a `format` field. No HTTP status codes appear in `errors.py`.
result: pass

### 5. Test Suite Green
expected: Running `uv run pytest tests/domain/ -v` completes with 27 tests passing and 0 failures. No test is marked as skipped or errored.
result: pass

### 6. Mypy Strict Clean
expected: Running `uv run mypy src/selection_maid/ --strict` exits with "Success: no issues found" and a non-zero file count. No type errors, no missing annotations.
result: issue
reported: "src/selection_maid/adapters/http/router.py:30: error: Library stubs not installed for 'psutil' [import-untyped]. Found 1 error in 1 file (checked 21 source files)"
severity: major

### 7. Zero Third-Party Imports in Domain Layer
expected: Running `grep -r "import docling\|import fastapi\|import pydantic" src/selection_maid/domain/ src/selection_maid/service.py src/selection_maid/errors.py` returns no output — the entire domain core has no third-party dependencies.
result: pass

## Summary

total: 7
passed: 6
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "uv run mypy src/selection_maid/ --strict exits with Success: no issues found"
  status: failed
  reason: "User reported: src/selection_maid/adapters/http/router.py:30: error: Library stubs not installed for 'psutil' [import-untyped]. Found 1 error in 1 file (checked 21 source files)"
  severity: major
  test: 6
  root_cause: "psutil is a runtime dependency in pyproject.toml but types-psutil (its mypy stub package) was never added to the dev dependency group. mypy --strict requires stubs or inline types for all third-party imports."
  artifacts:
    - path: "pyproject.toml"
      issue: "types-psutil missing from [dependency-groups.dev]"
    - path: "src/selection_maid/adapters/http/router.py"
      issue: "imports psutil at line 30; used at line 110 via psutil.Process()"
  missing:
    - "Run: uv add --dev types-psutil"
  debug_session: ""
