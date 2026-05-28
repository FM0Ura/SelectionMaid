---
phase: 06-http-api-layer
plan: "01"
subsystem: http-adapter
tags: [pydantic, schemas, serialization, http-adapter]
dependency_graph:
  requires:
    - src/selection_maid/domain/models.py
  provides:
    - src/selection_maid/adapters/http/schemas.py
  affects:
    - src/selection_maid/adapters/http/router.py (06-02)
    - src/selection_maid/adapters/http/app.py (06-03)
tech_stack:
  added:
    - pydantic v2 (BaseModel, ConfigDict) — already installed as transitive dep
  patterns:
    - Pydantic v2 from_attributes=True for frozen dataclass conversion
    - ConfigDict for model-level Pydantic config (replaces class Config in v1)
    - ISO 8601 datetime serialization via native Pydantic v2 behavior
key_files:
  created:
    - src/selection_maid/adapters/http/schemas.py
    - tests/adapters/http/__init__.py
    - tests/adapters/http/test_schemas.py
  modified: []
decisions:
  - "D-74: schemas.py lives in adapters/http, not in domain — domain must not import Pydantic"
  - "D-75: ExtractionResponse mirrors ExtractionResult with all 8 chunk fields and all 9 metadata fields"
  - "D-76: ingested_at serialized as ISO 8601 string (Pydantic v2 default behavior for datetime)"
  - "D-77: ConfigDict(from_attributes=True) enables model_validate on frozen dataclasses"
  - "D-78: HealthResponse has status/rss_mb/uptime_seconds/version with status='ok' default"
metrics:
  duration: "~5 minutes"
  completed_date: "2026-05-24"
  tasks_completed: 2
  files_created: 3
  files_modified: 0
  tests_added: 13
  tests_passing: 13
---

# Phase 6 Plan 01: HTTP Pydantic Schemas Summary

Pydantic v2 schemas for the FastAPI HTTP adapter: ChunkSchema (8 fields), MetadataSchema (9 fields with ISO 8601 datetime), ExtractionResponse (from_attributes mapping from frozen dataclasses), and HealthResponse (status/rss_mb/uptime_seconds/version).

## What Was Built

Created `src/selection_maid/adapters/http/schemas.py` with four Pydantic v2 BaseModel classes:

1. **ChunkSchema** — mirrors `DocumentChunk` with all 8 fields: `chunk_id`, `content`, `page_start`, `page_end`, `section_title`, `chunk_index`, `total_chunks`, `word_count`. `ConfigDict(from_attributes=True)` enables `model_validate()` on frozen dataclasses.

2. **MetadataSchema** — mirrors `DocumentMetadata` with all 9 fields: `doc_id`, `source_filename`, `title`, `author`, `language`, `doc_type`, `page_count`, `chunk_count`, `ingested_at`. The `ingested_at: datetime` field serializes to ISO 8601 string automatically via Pydantic v2.

3. **ExtractionResponse** — top-level response schema with `metadata: MetadataSchema` and `chunks: list[ChunkSchema]`. Handles `ExtractionResult.chunks` as `tuple[DocumentChunk, ...]` automatically — Pydantic v2 converts tuple to list during `model_validate`.

4. **HealthResponse** — health endpoint response with `status: str = "ok"`, `rss_mb: float`, `uptime_seconds: float`, `version: str`.

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED (test) | b7a9340 | 13 failing tests committed before implementation |
| GREEN (feat) | 791d4ac | All 13 tests pass after implementation |
| REFACTOR | — | Not needed; implementation is clean |

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Define ChunkSchema and MetadataSchema (TDD) | b7a9340 (test), 791d4ac (feat) | schemas.py, test_schemas.py |
| 2 | Define ExtractionResponse and HealthResponse | 791d4ac (included in same feat commit) | schemas.py |

## Verification Results

All success criteria met:

- `schemas.py` exists with all four models
- No Pydantic imports in `domain/` or `service.py`
- `from_attributes=True` set on `ChunkSchema`, `MetadataSchema`, `ExtractionResponse`
- `ExtractionResponse.model_validate(result, from_attributes=True)` works on frozen `ExtractionResult`
- `ingested_at` serializes as ISO 8601 string in `model_dump(mode="json")`

## Deviations from Plan

None — plan executed exactly as written. Both tasks were bundled into a single `schemas.py` file as intended. The TDD cycle (RED/GREEN) was followed correctly.

## Known Stubs

None — schemas are complete with all required fields. No placeholder values.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| Schema field coverage | schemas.py | Strictly defined fields prevent accidental internal state leakage (T-06-01 mitigated — D-75 enforced, no extra fields beyond domain contract) |

No new threat surface introduced. The schemas expose exactly the fields defined in the domain contract.

## Self-Check: PASSED

Files verified:
- `src/selection_maid/adapters/http/schemas.py` — FOUND
- `tests/adapters/http/__init__.py` — FOUND
- `tests/adapters/http/test_schemas.py` — FOUND

Commits verified:
- `b7a9340` (test) — FOUND
- `791d4ac` (feat) — FOUND
