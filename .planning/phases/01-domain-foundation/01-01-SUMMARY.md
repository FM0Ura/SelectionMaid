---
phase: 01-domain-foundation
plan: "01"
subsystem: domain
tags: [python, dataclasses, hexagonal-architecture, mypy, ruff, pytest, uv]

# Dependency graph
requires: []
provides:
  - "src/selection_maid/ hexagonal package scaffold with all __init__.py markers"
  - "src/selection_maid/domain/models.py — all 5 frozen domain dataclasses"
  - "src/selection_maid/adapters/{extractor,filter,chunker,enricher,http}/ — empty adapter subpackages"
  - "tests/ mirror structure with tests/stubs/ for shared stubs"
  - "pyproject.toml — [build-system], [tool.mypy] strict, [tool.ruff], [tool.pytest.ini_options]"
  - "Dev deps: pytest, mypy, ruff, pytest-asyncio, httpx, anyio via uv"
affects:
  - "01-02-ports"
  - "01-03-service"
  - "01-04-errors"
  - "01-05-tests"
  - "All adapter phases (02–06)"

# Tech tracking
tech-stack:
  added:
    - "hatchling (build backend)"
    - "mypy 2.1.0 (static type checking, strict mode)"
    - "ruff 0.15.14 (linting + formatting)"
    - "pytest 9.0.3 (test runner)"
    - "pytest-asyncio 1.3.0 (async test support)"
    - "httpx 0.28.1 (HTTP client for tests)"
    - "anyio 4.13.0 (async I/O abstraction)"
  patterns:
    - "Frozen dataclasses as immutable domain value objects"
    - "src/ layout with hatchling — packages=[\"src/selection_maid\"]"
    - "TDD cycle: RED (failing tests) → GREEN (minimal impl) → REFACTOR (linting)"
    - "from __future__ import annotations for forward-reference-safe type hints"
    - "tuple[T, ...] for immutable collections in frozen dataclasses"

key-files:
  created:
    - "src/selection_maid/domain/models.py — 5 frozen dataclasses"
    - "src/selection_maid/__init__.py"
    - "src/selection_maid/domain/__init__.py"
    - "src/selection_maid/adapters/__init__.py"
    - "src/selection_maid/adapters/extractor/__init__.py"
    - "src/selection_maid/adapters/filter/__init__.py"
    - "src/selection_maid/adapters/chunker/__init__.py"
    - "src/selection_maid/adapters/enricher/__init__.py"
    - "src/selection_maid/adapters/http/__init__.py"
    - "tests/__init__.py"
    - "tests/domain/__init__.py"
    - "tests/stubs/__init__.py"
    - "tests/adapters/__init__.py"
    - "tests/adapters/extractor/__init__.py"
    - "tests/adapters/filter/__init__.py"
    - "tests/adapters/chunker/__init__.py"
    - "tests/adapters/enricher/__init__.py"
    - "tests/domain/test_models.py — 16 tests for all 5 dataclasses"
    - "uv.lock"
  modified:
    - "pyproject.toml — added [build-system], [tool.hatch], [tool.mypy], [tool.ruff], [tool.pytest.ini_options], [dependency-groups]"

key-decisions:
  - "frozen=True on all domain dataclasses enforces immutability at Python runtime (STRIDE T-01-01)"
  - "tuple[DocumentChunk, ...] for ExtractionResult.chunks — immutable collection matches frozen domain design (D-07, D-08)"
  - "Zero third-party imports in models.py — only stdlib: __future__, dataclasses, datetime, pathlib (T-01-02)"
  - "src/ layout with hatchling as build backend — uv creates .venv automatically"
  - "asyncio_mode=auto in pytest for future async tests in Phase 6"
  - "dataclasses.replace() creates new object (correct), direct mutation raises FrozenInstanceError (correct)"

patterns-established:
  - "Frozen dataclass pattern: @dataclass(frozen=True) with from __future__ import annotations"
  - "No default values on domain value object fields — caller provides all"
  - "No __post_init__ validation in value objects — service layer owns validation"
  - "TDD protocol: commit test(RED) then feat(GREEN) then refactor if needed"

requirements-completed:
  - ARCH-07

# Metrics
duration: 6min
completed: 2026-05-23
---

# Phase 01 Plan 01: Domain Foundation Scaffold Summary

**Hexagonal package scaffold with 5 frozen dataclasses (RawInput, RawDocument, DocumentChunk, DocumentMetadata, ExtractionResult) and full mypy --strict compliance; zero third-party imports in domain layer**

## Performance

- **Duration:** 6 min
- **Started:** 2026-05-23T22:27:00Z
- **Completed:** 2026-05-23T22:33:00Z
- **Tasks:** 2
- **Files modified:** 20

## Accomplishments

- Created complete hexagonal package scaffold: `src/selection_maid/` with `domain/` and `adapters/{extractor,filter,chunker,enricher,http}/` subpackages
- Created `tests/` mirror structure with `tests/stubs/` for shared stub adapters
- Configured pyproject.toml with `[build-system]` (hatchling), `[tool.mypy]` (strict), `[tool.ruff]` (E/F/I/UP/B/SIM), `[tool.pytest.ini_options]` (asyncio_mode=auto)
- Installed dev deps via uv: pytest, mypy, ruff, pytest-asyncio, httpx, anyio
- Implemented 5 frozen domain dataclasses with exactly CHUNK-03 (8 fields) and META-01 (7 fields) compliance
- All 16 domain tests pass; mypy --strict exits 0; ruff clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Create hexagonal package scaffold** - `143aa2f` (feat)
2. **Task 2 RED: Add failing domain tests** - `bd09707` (test)
3. **Task 2 GREEN: Implement frozen domain dataclasses** - `51029a4` (feat)
4. **Task 2 REFACTOR: Fix ruff linting in test_models.py** - `199f4eb` (refactor)

**Plan metadata:** (docs commit — see final commit)

## Files Created/Modified

- `src/selection_maid/domain/models.py` — 5 frozen dataclasses; stdlib imports only; mypy strict
- `src/selection_maid/__init__.py` — package root marker
- `src/selection_maid/domain/__init__.py` — domain subpackage marker
- `src/selection_maid/adapters/__init__.py` — adapters subpackage marker
- `src/selection_maid/adapters/{extractor,filter,chunker,enricher,http}/__init__.py` — empty adapter placeholders (D-03)
- `tests/__init__.py` — test suite root
- `tests/domain/__init__.py` — domain test subpackage
- `tests/stubs/__init__.py` — shared stubs subpackage (D-04)
- `tests/adapters/{extractor,filter,chunker,enricher}/__init__.py` — adapter test markers
- `tests/domain/test_models.py` — 16 tests covering all 5 dataclasses
- `pyproject.toml` — [build-system], [tool.hatch], [tool.mypy], [tool.ruff], [tool.pytest.ini_options], [dependency-groups]
- `uv.lock` — locked dependency tree

## Decisions Made

- `frozen=True` on all dataclasses per D-08 and STRIDE T-01-01 (mutation after construction is a tampering threat)
- `tuple[DocumentChunk, ...]` for `ExtractionResult.chunks` per D-07 (consistent with frozen-domain design; list would allow mutation)
- No `__post_init__` validation in value objects — service layer owns validation, domain stays pure
- `dataclasses.replace()` is the correct way to "modify" frozen objects (returns new instance); direct attribute assignment raises `FrozenInstanceError`
- `from __future__ import annotations` used to enable forward-reference-safe type hints without runtime overhead

## Deviations from Plan

None - plan executed exactly as written.

TDD cycle followed as specified: RED (failing tests committed at `bd09707`) → GREEN (implementation committed at `51029a4`) → REFACTOR (linting fixes committed at `199f4eb`).

## Known Stubs

None — all five dataclasses have complete field definitions per CHUNK-03 and META-01 requirements. No placeholder or hardcoded empty values.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries introduced. This plan is pure Python source code with no runtime I/O.

## Issues Encountered

- **ruff E501/SIM102 in test file:** test_models.py had 3 linting violations (line too long in docstring, nested `if` statements). Fixed in REFACTOR commit `199f4eb`. No impact on test behavior.

## User Setup Required

None — no external service configuration required. All dev tools installed locally via `uv add --dev`.

## Next Phase Readiness

- Package importable: `import selection_maid` works
- Domain models importable: `from selection_maid.domain.models import ...` works
- mypy --strict passes on models.py
- Adapter subpackage skeleton ready for Phases 2–6 to populate
- Test infrastructure (pytest, asyncio_mode=auto) ready for Phase 1 remaining plans
- **Next:** Plan 01-02 — port contracts (`typing.Protocol`) in `src/selection_maid/domain/ports.py`

## Self-Check: PASSED

- `src/selection_maid/domain/models.py` — FOUND
- `tests/domain/test_models.py` — FOUND
- `pyproject.toml` with `[tool.mypy]` — FOUND
- Commit `143aa2f` (Task 1) — FOUND
- Commit `bd09707` (Task 2 RED) — FOUND
- Commit `51029a4` (Task 2 GREEN) — FOUND
- Commit `199f4eb` (Task 2 REFACTOR) — FOUND

---
*Phase: 01-domain-foundation*
*Completed: 2026-05-23*
