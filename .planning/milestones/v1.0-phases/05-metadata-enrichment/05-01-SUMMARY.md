---
phase: 05-metadata-enrichment
plan: "01"
subsystem: domain
tags: [domain-model, schema, config, langdetect]
dependency_graph:
  requires: []
  provides: [DocumentMetadata-9-fields, EnricherConfig, langdetect]
  affects: [tests/domain/, tests/stubs/adapters.py, src/selection_maid/config.py]
tech_stack:
  added: [langdetect==1.0.9]
  patterns: [frozen-dataclass, config-dataclass, factory-config-pattern]
key_files:
  created: []
  modified:
    - src/selection_maid/domain/models.py
    - tests/stubs/adapters.py
    - tests/domain/test_models.py
    - tests/domain/test_service.py
    - src/selection_maid/config.py
    - pyproject.toml
    - uv.lock
decisions:
  - "D-68: DocumentMetadata updated to 9 fields — doc_id, source_filename added; ingestion_date -> ingested_at, document_type -> doc_type"
  - "D-72/D-73: EnricherConfig added as empty dataclass placeholder following GlobalConfig pattern"
metrics:
  duration: "~5 minutes"
  completed: "2026-05-24"
  tasks_completed: 3
  tasks_total: 3
---

# Phase 05 Plan 01: Schema Update and Infrastructure Setup Summary

**One-liner:** Added doc_id/source_filename to DocumentMetadata, renamed ingestion_date/document_type, and wired EnricherConfig into GlobalConfig with langdetect installed.

## What Was Built

### Task 1 — Domain Model and Stubs

`DocumentMetadata` in `src/selection_maid/domain/models.py` was updated per decision D-68:
- Added `doc_id: str` and `source_filename: str` as new fields (positions 1 and 2)
- Renamed `ingestion_date` to `ingested_at`
- Renamed `document_type` to `doc_type`
- Field count is now exactly 9

`StubEnricher` in `tests/stubs/adapters.py` updated to pass `doc_id="stub-id"`, `source_filename="test.pdf"`, and use the new field names.

### Task 2 — Test Fixes

`tests/domain/test_models.py`:
- Renamed `test_document_metadata_has_all_seven_fields` to `test_document_metadata_has_all_nine_fields`
- Renamed `test_document_metadata_field_count_is_exactly_seven` to `test_document_metadata_field_count_is_exactly_nine`
- Updated all `DocumentMetadata` instantiations to use new fields
- Updated `_make_metadata()` in `TestExtractionResult` to use new schema

`tests/domain/test_service.py`:
- Updated `test_metadata_has_all_required_fields` to assert `meta.doc_id`, `meta.source_filename`, `meta.doc_type`, `meta.ingested_at`

All 36 domain tests pass.

### Task 3 — Infrastructure and Config

`src/selection_maid/config.py`:
- Added `EnricherConfig` dataclass (empty v1 placeholder per D-73)
- Added `enricher: EnricherConfig = field(default_factory=EnricherConfig)` to `GlobalConfig`
- Updated `get_config()` to construct and return `EnricherConfig()` for the `[enricher]` TOML section

`pyproject.toml` / `uv.lock`: `langdetect>=1.0.9` installed via `uv add langdetect`.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | 2430ac3 | feat(05-01): update DocumentMetadata schema with doc_id, source_filename, ingested_at, doc_type |
| 2 | 8d264d7 | test(05-01): fix domain tests for updated DocumentMetadata schema |
| 3 | c349100 | feat(05-01): add EnricherConfig to GlobalConfig and install langdetect |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — no placeholder data flows to UI rendering or output schemas in this plan.

## Threat Flags

No new network endpoints, auth paths, or trust-boundary surface introduced.

## Self-Check: PASSED

- [x] `src/selection_maid/domain/models.py` modified — `DocumentMetadata` has 9 fields
- [x] `tests/stubs/adapters.py` modified — `StubEnricher` uses new field names
- [x] `tests/domain/test_models.py` modified — tests updated for 9 fields
- [x] `tests/domain/test_service.py` modified — new field assertions
- [x] `src/selection_maid/config.py` modified — `EnricherConfig` added
- [x] `pyproject.toml` has `langdetect>=1.0.9`
- [x] All 36 domain tests pass
- [x] `get_config().enricher` returns `EnricherConfig()` instance
- [x] All 3 task commits verified: 2430ac3, 8d264d7, c349100
