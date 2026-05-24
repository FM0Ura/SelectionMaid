---
phase: 04-chunking
plan: 01
subsystem: chunking
tags: [config, skeleton, tiktoken, architecture]
dependency_graph:
  requires: []
  provides: [ChunkerConfig, MarkdownChunker, build_markdown_chunker]
  affects: [src/selection_maid/config.py, src/selection_maid/adapters/chunker/markdown.py, config.toml, pyproject.toml]
tech_stack:
  added: [tiktoken>=0.13.0]
  patterns: [factory-function-D-23, constructor-injection-D-57, config-dataclass-D-58]
key_files:
  created: [src/selection_maid/adapters/chunker/markdown.py]
  modified: [src/selection_maid/config.py, config.toml, pyproject.toml, uv.lock]
decisions:
  - "D-57: MarkdownChunker(max_tokens=512) constructor injection; tiktoken encoder initialised once in __init__"
  - "D-58: ChunkerConfig follows FilterConfig pattern exactly; GlobalConfig extended with chunker field"
  - "D-59: File at adapters/chunker/markdown.py following adapter subdirectory pattern"
  - "Rule 1 auto-fix: replaced incorrect type:ignore[arg-type] comments in config.py with _as_int() helper for mypy strict compliance"
metrics:
  duration: "~8 minutes"
  completed: "2026-05-24"
  tasks_completed: 3
  tasks_total: 3
  files_changed: 5
---

# Phase 4 Plan 01: Environment Setup and Architecture Skeleton Summary

**One-liner:** Tiktoken dependency added, ChunkerConfig integrated into GlobalConfig, and MarkdownChunker skeleton with build_markdown_chunker factory created following established hexagonal adapter patterns.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Add tiktoken dependency | f9508a2 | pyproject.toml, uv.lock |
| 2 | Update config.toml and GlobalConfig | 2cbe40f | config.toml, src/selection_maid/config.py |
| 3 | Create MarkdownChunker skeleton and factory | f75cbc1 | src/selection_maid/adapters/chunker/markdown.py |

## What Was Built

### Task 1: tiktoken dependency
- `tiktoken>=0.13.0` added to `pyproject.toml` via `uv add tiktoken`
- tiktoken 0.13.0 installed and locked in `uv.lock`
- Required for fixed-size chunking fallback using `cl100k_base` encoding (D-49, D-50)

### Task 2: Configuration extension
- `ChunkerConfig` dataclass added to `src/selection_maid/config.py` with `max_tokens: int = 512` (D-51, D-58)
- `GlobalConfig` extended with `chunker: ChunkerConfig = field(default_factory=ChunkerConfig)` (D-57)
- `[chunker]` section added to `config.toml` with `max_tokens = 512`
- `get_config()` updated to parse the `[chunker]` TOML section using the same pattern as `[filter]`

### Task 3: MarkdownChunker skeleton
- `MarkdownChunker` class created in `src/selection_maid/adapters/chunker/markdown.py` (D-59)
- Constructor accepts `max_tokens: int = 512` and initialises tiktoken encoder once (D-50, D-57)
- `chunk()` method is a skeleton that raises `NotImplementedError` (implementation in Plan 04-02)
- Exception wrapping applied: unexpected errors raised as `ChunkingError` (D-16)
- `build_markdown_chunker(config: ChunkerConfig) -> MarkdownChunker` factory follows D-23 pattern
- Satisfies `ChunkerPort` Protocol via structural typing (no inheritance, D-14)

## Verifications Passed

- `grep "tiktoken" pyproject.toml` → `"tiktoken>=0.13.0"`
- `get_config().chunker.max_tokens` → `512`
- `isinstance(build_markdown_chunker(ChunkerConfig()), MarkdownChunker)` → `True`
- `mypy src/selection_maid/config.py src/selection_maid/adapters/chunker/markdown.py` → `Success: no issues found`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed mypy strict call-overload errors in config.py**
- **Found during:** Task 3 (mypy run after creating markdown.py)
- **Issue:** Pre-existing `type: ignore[arg-type]` comments in `get_config()` were incorrect — mypy strict emitted `call-overload` errors because `dict[str, object].get()` returns `object`, which `int()` cannot accept. The wrong ignore tag masked the real error.
- **Fix:** Introduced `_as_int(value: object, default: int) -> int` helper function that uses `isinstance(value, int)` for type-safe extraction. Removed all `type: ignore` comments from the int-casting lines (both existing `filter_raw` and new `chunker_raw`).
- **Files modified:** `src/selection_maid/config.py`
- **Commit:** f75cbc1 (included in Task 3 commit)

## Known Stubs

- `MarkdownChunker.chunk()` always raises `NotImplementedError` — this is the intentional skeleton stub. The full implementation is scheduled for Plan 04-02 (heading-based split) and Plan 04-03 (integration). No data flows to UI from this stub.

## Self-Check

### Files exist:
- `src/selection_maid/adapters/chunker/markdown.py` — FOUND
- `src/selection_maid/config.py` (modified) — FOUND
- `config.toml` (modified) — FOUND
- `pyproject.toml` (modified) — FOUND

### Commits exist:
- f9508a2 — FOUND
- 2cbe40f — FOUND
- f75cbc1 — FOUND

## Self-Check: PASSED
