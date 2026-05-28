---
phase: 01-domain-foundation
plan: "04"
subsystem: domain
tags: [errors, exceptions, domain-taxonomy]

requires:
  - phase: 01-01
    provides: src/selection_maid/ package structure (errors.py lives at root of package)

provides:
  - Domain error taxonomy: SelectionMaidError base + 6 subclasses with fixed code class attributes
  - ExtractionError (EXT-001), UnsupportedFormatError (EXT-002, +format field), ExtractionTimeoutError (EXT-003)
  - FilterError (FILT-001), ChunkingError (CHUNK-001), EnrichmentError (ENRICH-001)

affects: [service.py (01-03), Phase 6 HTTP adapter, Phase 2 DoclingAdapter]

tech-stack:
  added: []
  patterns: [exception-wrapping, fixed-code-class-attributes, no-http-coupling-in-domain]

key-files:
  created: [src/selection_maid/errors.py]
  modified: []

key-decisions:
  - "D-19: No HTTP status codes in domain errors — HTTP mapping lives in Phase 6 adapter"
  - "D-20: ExtractionTimeoutError defined now for Phase 2 use (DoclingAdapter raises it)"
  - "UnsupportedFormatError is sibling of ExtractionError (not child) — flat hierarchy"
  - "code is a class attribute, not instance attribute — enables ERROR_CODE_TO_HTTP mapping in Phase 6"

patterns-established:
  - "Exception wrapping pattern: catch Exception, wrap in domain error with cause=e"
  - "class code: str = 'EXT-001' pattern for machine-readable error classification"

requirements-completed: [ARCH-06]

duration: 5min
completed: 2026-05-23
---

# Plan 01-04: Domain Error Taxonomy Summary

**Domain error contract complete: SelectionMaidError base + 6 typed subclasses with machine-readable codes, no HTTP coupling.**

## Performance

- **Duration:** ~5 min
- **Completed:** 2026-05-23
- **Tasks:** 1/1
- **Files modified:** 1

## Accomplishments

- `src/selection_maid/errors.py` created with `SelectionMaidError(Exception)` base class
- Six subclasses all inheriting `SelectionMaidError` directly (flat hierarchy):
  - `ExtractionError` (EXT-001)
  - `UnsupportedFormatError` (EXT-002) — carries `format: str` extra field
  - `ExtractionTimeoutError` (EXT-003) — defined now, raised by DoclingAdapter in Phase 2
  - `FilterError` (FILT-001)
  - `ChunkingError` (CHUNK-001)
  - `EnrichmentError` (ENRICH-001)
- All codes verified via assertions; mypy --strict clean
- Zero third-party imports; no HTTP status codes

## Verification Results

- All 6 subclass codes verified: `assert ExtractionError.code == 'EXT-001'` etc. → OK
- `UnsupportedFormatError(message='bad', format='xyz').format == 'xyz'` → OK
- `isinstance(ExtractionError('x'), SelectionMaidError)` → True
- `uv run mypy src/selection_maid/errors.py --strict` → Success: no issues found
