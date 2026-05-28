---
phase: 01-domain-foundation
plan: "03"
subsystem: domain
tags: [python, hexagonal-architecture, service-layer, exception-wrapping, ports-adapters]

# Dependency graph
requires:
  - phase: 01-domain-foundation
    plan: "01"
    provides: "Domain models: RawInput, RawDocument, DocumentChunk, DocumentMetadata, ExtractionResult"
  - phase: 01-domain-foundation
    plan: "02"
    provides: "Port protocols: ExtractorPort, FilterPort, ChunkerPort, MetadataEnricherPort"
  - phase: 01-domain-foundation
    plan: "04"
    provides: "Error taxonomy: SelectionMaidError, ExtractionError, FilterError, ChunkingError, EnrichmentError"
provides:
  - "ExtractionService class at src/selection_maid/service.py with process(input: RawInput) -> ExtractionResult"
  - "Four-port constructor injection pattern: extractor, filter_, chunker, enricher"
  - "Pipeline: extract -> filter -> chunk -> enrich -> ExtractionResult"
  - "Exception wrapping at each boundary (D-16): domain errors propagate unchanged, non-domain exceptions are wrapped"
affects:
  - "01-05: integration tests will exercise ExtractionService with stub adapters"
  - "phase-06: FastAPI HTTP adapter calls ExtractionService.process()"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Constructor injection: all four ports injected at __init__; service never imports concrete adapters"
    - "Exception boundary wrapping: SelectionMaidError re-raised as-is; all others wrapped in domain subclass with cause= parameter"
    - "Frozen-to-frozen pipeline: each step receives an immutable value object and produces another"
    - "tuple() conversion: ChunkerPort.chunk() returns list[DocumentChunk]; ExtractionResult.chunks is tuple[DocumentChunk, ...]"

key-files:
  created:
    - src/selection_maid/service.py
  modified: []

key-decisions:
  - "D-15: ExtractionService.process(input) runs extract -> filter -> chunk -> enrich and returns ExtractionResult"
  - "D-16: Port exceptions are wrapped — SelectionMaidError propagates unchanged; other exceptions wrapped in domain error subclasses with cause= and from e"
  - "Private attributes _extractor, _filter, _chunker, _enricher — no public accessor needed (hexagonal core)"
  - "filtered.content (not raw.content) passed to chunker — filtering must precede chunking"
  - "enricher receives both raw and chunks_list — allows page_count from raw and total_chunks from chunks"

patterns-established:
  - "Exception wrapping pattern: try: ... except SelectionMaidError: raise / except Exception as e: raise DomainError(..., cause=e) from e"
  - "Zero third-party imports in domain layer — enforces hexagonal boundary at import level"

requirements-completed:
  - ARCH-06

# Metrics
duration: 8min
completed: 2026-05-23
---

# Phase 01 Plan 03: ExtractionService Summary

**ExtractionService with four-port constructor injection implementing the extract → filter → chunk → enrich pipeline with per-boundary exception wrapping (D-15, D-16)**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-05-23T00:00:00Z
- **Completed:** 2026-05-23T00:08:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- ExtractionService at `src/selection_maid/service.py` — application core with no third-party dependencies
- Four-port constructor injection: `extractor`, `filter_`, `chunker`, `enricher` stored as private attributes
- Bounded exception wrapping at every port call boundary: SelectionMaidError propagates unchanged, all other exceptions wrapped with `cause=` and `from e`
- `tuple(chunks_list)` conversion ensures ExtractionResult.chunks immutability invariant is preserved

## Task Commits

1. **Task 1: Implement ExtractionService with pipeline and exception wrapping** - `(pending)` (feat)

**Plan metadata:** `(pending)` (docs: complete plan)

## Files Created/Modified
- `src/selection_maid/service.py` — ExtractionService class; orchestrates the 4-step pipeline; zero third-party imports; mypy strict clean

## Decisions Made
- Used `input` as parameter name for `process()` (matching port convention in plan) — shadowing the built-in is intentional and conventional for domain entry points
- Used explicit type annotations on all intermediate variables (`raw: RawDocument`, `filtered: RawDocument`, `chunks_list: list[DocumentChunk]`, `metadata: DocumentMetadata`) to ensure mypy --strict passes without inference gaps
- Passed `raw` (not `filtered`) to enricher as first argument — enricher needs the original document's page_count and format; filtered content is accessed via `chunks_list`

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness
- ExtractionService is ready for exercise by stub adapters (plan 01-05)
- Phase 6 (FastAPI HTTP adapter) can call `ExtractionService.process()` with a `RawInput` constructed from `UploadFile`
- No blockers

---
*Phase: 01-domain-foundation*
*Completed: 2026-05-23*
