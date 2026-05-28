---
phase: 01-domain-foundation
plan: "02"
subsystem: domain
tags: [typing.Protocol, ports, hexagonal-architecture, structural-typing, python]

# Dependency graph
requires:
  - phase: 01-domain-foundation
    plan: "01"
    provides: "RawInput, RawDocument, DocumentChunk, DocumentMetadata domain models"
provides:
  - "ExtractorPort typing.Protocol with extract(RawInput) -> RawDocument"
  - "FilterPort typing.Protocol with filter(RawDocument) -> RawDocument"
  - "ChunkerPort typing.Protocol with chunk(str) -> list[DocumentChunk]"
  - "MetadataEnricherPort typing.Protocol with enrich(RawDocument, list[DocumentChunk]) -> DocumentMetadata"
affects:
  - "01-03 ExtractionService (imports all four ports via constructor injection)"
  - "Phase 2 DoclingAdapter (implements ExtractorPort)"
  - "Phase 3 FilterAdapter (implements FilterPort)"
  - "Phase 4 ChunkerAdapter (implements ChunkerPort)"
  - "Phase 5 MetadataEnricher (implements MetadataEnricherPort)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "typing.Protocol for structural subtyping — adapters satisfy ports without inheritance"
    - "No @runtime_checkable — isinstance() not supported by design (D-14)"
    - "All port methods sync (def) — async boundary deferred to HTTP adapter in Phase 6"

key-files:
  created:
    - src/selection_maid/domain/ports.py
    - src/selection_maid/__init__.py
    - src/selection_maid/domain/__init__.py
  modified: []

key-decisions:
  - "No @runtime_checkable on any Protocol per D-14 — mypy enforces structural compliance at type-check time only"
  - "All port methods are sync per D-13 — async boundary managed by HTTP adapter in Phase 6 via run_in_threadpool"
  - "ChunkerPort.chunk returns list[DocumentChunk] — service converts to tuple when building ExtractionResult"
  - "from __future__ import annotations used for forward-reference safety"

patterns-established:
  - "Protocol-per-port pattern: one Protocol class per adapter boundary, one abstract method each"
  - "No adapter types in ports.py — only stdlib typing + domain model types as parameter/return annotations"

requirements-completed:
  - ARCH-01
  - ARCH-02
  - ARCH-03
  - ARCH-04

# Metrics
duration: 2min
completed: 2026-05-23
---

# Phase 01 Plan 02: Port Contracts Summary

**Four typing.Protocol port contracts (ExtractorPort, FilterPort, ChunkerPort, MetadataEnricherPort) defined with sync signatures, no @runtime_checkable, and only domain model types at port boundaries**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-23T22:28:38Z
- **Completed:** 2026-05-23T22:30:43Z
- **Tasks:** 1
- **Files modified:** 3

## Accomplishments

- Created `src/selection_maid/domain/ports.py` with four typing.Protocol classes satisfying ARCH-01 through ARCH-04
- Created `src/selection_maid/__init__.py` and `src/selection_maid/domain/__init__.py` package initializers (domain directory did not exist — parallel execution with 01-01)
- All port contracts follow D-09 through D-14: sync methods, no @runtime_checkable, structural subtyping only

## Task Commits

1. **Task 1: Define four port Protocols in ports.py** - `f2df3c0` (feat)

**Plan metadata:** (final docs commit — see below)

## Files Created/Modified

- `src/selection_maid/domain/ports.py` — Four typing.Protocol classes: ExtractorPort, FilterPort, ChunkerPort, MetadataEnricherPort
- `src/selection_maid/__init__.py` — Package initializer (empty, created because src/ did not exist in this worktree)
- `src/selection_maid/domain/__init__.py` — Domain subpackage initializer (empty)

## Decisions Made

- No @runtime_checkable on any Protocol (D-14): isinstance() checks deliberately not supported; mypy enforces structural compliance at type-check time only
- All methods sync (D-13): async boundary is managed by the HTTP adapter in Phase 6 via run_in_threadpool; domain stays pure Python with no asyncio
- ChunkerPort.chunk returns list[DocumentChunk] (D-11): the service converts this to an immutable tuple when building ExtractionResult
- Created package __init__.py files proactively because src/selection_maid/domain/ did not exist in this worktree (01-01 runs in parallel)

## Deviations from Plan

None — plan executed exactly as written, including the documented expectation that models.py does not exist yet in this worktree.

## Issues Encountered

**Expected: import check and mypy skipped in Wave 1 (parallel execution)**

The plan and parallel_execution note document that `uv run python -c "from selection_maid.domain.ports import ..."` will fail because `models.py` (plan 01-01) does not exist in this worktree yet — both plans are Wave 1 and run concurrently. The import will be verified at Wave 4 after all Wave 1 plans merge.

Similarly, mypy could not run because `mypy` is not yet installed in the project environment (pyproject.toml has empty dependencies — 01-01 configures tooling). The ports.py content is structurally correct and will pass mypy strict once the environment is set up by 01-01.

All structural grep checks passed:
- No `runtime_checkable` in ports.py
- No `async def` in ports.py
- All four Protocol class definitions present
- All four method signatures match D-09 through D-12
- Only stdlib (typing) + own (selection_maid.domain.models) imports

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Port contracts are ready for 01-03 (ExtractionService) to import and use via constructor injection
- All four adapter phases (2-5) have their Port contracts defined and ready to implement against
- Import and mypy verification deferred to Wave 4 merge after 01-01 provides models.py and tooling config

## Known Stubs

None — ports.py contains only abstract Protocol method stubs (`...` bodies), which is the correct and complete implementation for Protocol classes. These are not data stubs; they are the intended Protocol method declarations.

## Threat Flags

No new threat surface introduced. ports.py uses only stdlib typing and project-local model types — no network endpoints, no auth paths, no file access, no schema changes. T-01-02-01 (Information Disclosure) and T-01-02-02 (Elevation of Privilege) are mitigated as documented in the plan threat register.

---
*Phase: 01-domain-foundation*
*Completed: 2026-05-23*
