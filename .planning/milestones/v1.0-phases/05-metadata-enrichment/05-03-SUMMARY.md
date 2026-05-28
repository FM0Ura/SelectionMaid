---
phase: "05"
plan: "03"
subsystem: metadata-enrichment
tags: [testing, unit-tests, metadata, langdetect, doc-type, language-detection]
dependency_graph:
  requires:
    - "05-01"  # DocumentMetadata model updates
    - "05-02"  # MetadataEnricher implementation
  provides:
    - unit test coverage for MetadataEnricher (_detect_language, _infer_doc_type, _extract_title, enrich)
  affects:
    - tests/adapters/enricher/test_metadata_enricher.py
tech_stack:
  added: []
  patterns:
    - unittest.mock.patch for langdetect.detect_langs isolation
    - MagicMock for confidence-threshold boundary tests
key_files:
  created:
    - tests/adapters/enricher/test_metadata_enricher.py
  modified: []
decisions:
  - "test_returns_und_for_very_short_text uses mock instead of real 'hi' input — langdetect returns 'sw' (Swahili) with 0.5+ confidence for 'hi', so the test was refactored to mock detect_langs and explicitly test the threshold rejection logic at 0.5 prob"
metrics:
  duration_seconds: 151
  completed_date: "2026-05-24"
  tasks_completed: 3
  files_created: 1
  files_modified: 0
---

# Phase 5 Plan 03: MetadataEnricher Unit Tests — Summary

**One-liner:** 30 unit tests covering language detection (EN/PT/ES + mock threshold), doc_type keyword heuristics, H1 title extraction, all 9 enrich() fields, and edge cases — 146 total tests passing, mypy strict clean.

## What Was Built

Created `tests/adapters/enricher/test_metadata_enricher.py` with 5 test classes and 30 test methods covering the full `MetadataEnricher` surface:

- **TestDetectLanguage (5 tests):** English/Portuguese/Spanish detection via real langdetect, low-confidence threshold rejection via mock, exception→"und" via `LangDetectException` mock.
- **TestInferDocType (7 tests):** legal via "contrato" heading keyword, legal via "cláusula" heading keyword, presentation via "slide" heading keyword, presentation via "agenda" heading keyword, form via `_____`/`[ ]` indicators, report via table+numbered-section structural heuristic, fallback to "other".
- **TestExtractTitle (4 tests):** First H1 extraction, no H1 returns `""`, accented characters in title, empty content.
- **TestEnrich (8 tests):** Returns `DocumentMetadata`, all 9 fields non-None, `doc_id` is UUID v4, `source_filename` matches `raw.filename`, `ingested_at` within 5 seconds of now, `author == ""`, `chunk_count == len(chunks)`, `page_count == raw.page_count`.
- **TestEdgeCases (6 tests):** Empty content → language="und"/title=""/doc_type="other", two H1s → first is used, `doc_id` unique per call, `ingested_at.tzinfo` is not None.

## Phase Gate Verification

Phase 5 success criteria verified:

1. **All 9 DocumentMetadata fields populated** — confirmed via `test_enrich_all_nine_fields_present` and `test_enrich_returns_document_metadata`.
2. **language returns ISO 639-1 code or "und"** — confirmed via multilingual detection tests and threshold/exception tests.
3. **doc_type from closed vocabulary {article, report, presentation, form, legal, other}** — confirmed via `TestInferDocType` covering all produced values; "other" is the fallback.
4. **ingested_at is UTC-aware datetime** — confirmed via `test_ingested_at_is_timezone_aware`.

Full suite: **146 tests passed**, 1 deprecation warning (unrelated Docling `generate_table_images` field). mypy strict: **no issues found** in 17 source files.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test Fix] test_returns_und_for_very_short_text used "hi" which gets detected as Swahili**

- **Found during:** Task 1 initial run
- **Issue:** langdetect assigns "sw" (Swahili) with confidence >= 0.8 to the string "hi", so the raw input test did not exercise the threshold-rejection path as intended.
- **Fix:** Replaced real input with a `unittest.mock.patch` that makes `detect_langs` return a mock language object with `prob=0.5` (below the 0.8 threshold). This directly tests the threshold check logic in `_detect_language`.
- **Files modified:** `tests/adapters/enricher/test_metadata_enricher.py`
- **Commit:** c827b4d

**2. [Rule 2 - Unused Import] Removed unused `pytest` import**

- **Found during:** IDE diagnostic after initial write
- **Fix:** Removed `import pytest` — none of the test methods use pytest-specific decorators or fixtures.
- **Files modified:** `tests/adapters/enricher/test_metadata_enricher.py`
- **Commit:** c827b4d (same commit, fixed before staging)

## Known Stubs

None — all test assertions target real implementation behavior. No placeholder or hardcoded stub values.

## Threat Flags

None — test-only files; no new network endpoints, auth paths, or schema changes.

## Self-Check: PASSED

- `tests/adapters/enricher/test_metadata_enricher.py` — FOUND
- Commit c827b4d — FOUND (`git log --oneline | grep c827b4d`)
- 146 tests passed, 0 failed
- mypy strict: no issues in 17 source files
