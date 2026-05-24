---
phase: 03-content-filtering
plan: "01"
subsystem: config
tags: [tomllib, toml, configuration, dataclass, python313]

# Dependency graph
requires:
  - phase: 01-domain-foundation
    provides: established hexagonal architecture pattern (adapters receive config via constructor injection)
  - phase: 02-docling-extraction-adapter
    provides: directory structure convention (adapters/extractor/docling.py pattern for constructor injection)
provides:
  - selection_maid.config module with get_config() reading config.toml via tomllib (stdlib)
  - FilterConfig dataclass: min_repeat (int, default 3) and max_line_len (int, default 80)
  - GlobalConfig dataclass: container for all adapter config sections
  - config.toml at project root with [filter] section
  - Graceful fallback to hardcoded defaults when config.toml is missing or partial (D-38)
affects:
  - 03-02 (HeuristicFilter receives FilterConfig via constructor injection)
  - 03-03 (integration tests import get_config to verify wiring)
  - all future phases adding configurable adapters (chunker, enricher)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "tomllib (stdlib, Python 3.11+) for TOML parsing — no external dependency"
    - "Dataclass defaults + field(default_factory=...) for nested config without mutable default"
    - "get_config(config_path: Path | None = None) signature allows test injection without monkey-patching"

key-files:
  created:
    - src/selection_maid/config.py
    - config.toml
  modified: []

key-decisions:
  - "D-38: get_config() falls back silently to defaults if config.toml is missing or unreadable — no startup failure"
  - "D-39: HeuristicFilter receives thresholds via constructor injection; config resolves and injects them"
  - "D-40: [filter] TOML section with min_repeat=3 and max_line_len=80 keys"

patterns-established:
  - "Config injection pattern: get_config(path) accepts optional Path for testability without file system coupling"
  - "Nested dataclass defaults: FilterConfig standalone + GlobalConfig.filter = field(default_factory=FilterConfig)"

requirements-completed: [FILT-01, FILT-02, FILT-03]

# Metrics
duration: 2min
completed: 2026-05-24
---

# Phase 03 Plan 01: Configuration Module Summary

**tomllib-based GlobalConfig with FilterConfig defaults (min_repeat=3, max_line_len=80) and graceful fallback when config.toml is absent**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-24T18:02:34Z
- **Completed:** 2026-05-24T18:04:28Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Created `selection_maid.config` with `FilterConfig` and `GlobalConfig` dataclasses using only stdlib (tomllib)
- Implemented `get_config()` that silently falls back to hardcoded defaults when `config.toml` is missing or lacks expected keys
- Created `config.toml` at project root with `[filter]` section documenting all configurable thresholds
- Verified override behavior: changing `min_repeat` in `config.toml` to 5 returns 5; reverting to 3 returns 3

## Task Commits

Each task was committed atomically:

1. **Task 1: Create configuration module** - `07797da` (feat)
2. **Task 2: Create default config.toml** - `6845c3a` (feat)

## Files Created/Modified
- `src/selection_maid/config.py` - Central config module: FilterConfig, GlobalConfig dataclasses and get_config()
- `config.toml` - Project-root TOML file with [filter] section (min_repeat=3, max_line_len=80)

## Decisions Made
- Used `get_config(config_path: Path | None = None)` signature instead of always reading `Path("config.toml")` — this allows tests to pass a temp-file path directly without monkey-patching or environment variables
- Used `field(default_factory=FilterConfig)` to avoid mutable default in `GlobalConfig` dataclass — correct Python pattern
- Type-ignored `filter_raw.get(...)` calls because mypy strict cannot narrow `dict[str, object]` values to `int` without explicit cast; `int(...)` wrapping handles type safety at runtime

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. `config.toml` is already created at project root with default values.

## Next Phase Readiness
- `get_config()` is ready for 03-02 to import and pass `FilterConfig` to `HeuristicFilter.__init__()`
- `config.toml` can be extended with new sections (e.g., `[chunker]`) in future phases without breaking existing code
- Tests in 03-03 can call `get_config(Path("config.toml"))` directly or pass `FilterConfig(...)` values directly per D-39

## Self-Check: PASSED

| Artifact | Status |
|----------|--------|
| src/selection_maid/config.py | FOUND |
| config.toml | FOUND |
| .planning/phases/03-content-filtering/03-01-SUMMARY.md | FOUND |
| Commit 07797da (Task 1) | FOUND |
| Commit 6845c3a (Task 2) | FOUND |

---
*Phase: 03-content-filtering*
*Completed: 2026-05-24*
