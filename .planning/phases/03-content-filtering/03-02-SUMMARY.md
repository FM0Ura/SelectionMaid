# Plan 03-02 Summary — HeuristicFilter Implementation

**Status:** Complete
**Commits:** e9d94d7
**Duration:** ~5 min

## What Was Built

### `src/selection_maid/adapters/filter/heuristic.py`
Concrete `FilterPort` implementation using three heuristic rules applied in order:

1. **Frequency-based header/footer removal (D-31–D-34):** Lines ≤ 80 chars appearing ≥ 3 times are removed as header/footer candidates. Exclusions: lines starting with `#` (headings) or containing `|` (GFM table lines) are never removed.
2. **Isolated page number removal (D-35, D-36):** Lines matching `^\d+$`, `^[ivxlcdm]{1,10}$` (case-insensitive), or `^-\s*(\d+|...)\s*-$` are removed. Only completely isolated lines match — numbers inline in text are unaffected.
3. **Whitespace compression (D-37):** Sequences of 3+ newlines compressed to exactly 2 (`\n\n`). Applied last to avoid interfering with frequency detection.

Also includes `build_heuristic_filter()` factory function (D-23) for consistent construction.

### `tests/adapters/filter/test_heuristic_filter.py`
33 unit tests across 5 test classes (D-43):
- `TestFILT01Headers` — 7 tests for frequency-based detection
- `TestFILT02PageNumbers` — 9 tests for page number patterns
- `TestFILT03Whitespace` — 5 tests for whitespace compression
- `TestContentPreservation` — 8 tests ensuring legitimate content survives
- `TestErrorHandling` — 4 tests for exception wrapping (D-16)

All fixtures are inline Markdown strings (D-42) — no external files.

### `src/selection_maid/adapters/filter/__init__.py`
Updated to export `HeuristicFilter` and `build_heuristic_filter` (D-41).

## Verification

```
uv run pytest tests/adapters/filter/test_heuristic_filter.py -v
# 33 passed in 0.04s
```

## Notes

- `HeuristicFilter` is intentionally independent of `selection_maid.config` — thresholds are injected via constructor (D-39). The factory integration with config comes in plan 03-03.
- Module-level compiled regex constants (`_ARABIC_RE`, `_ROMAN_RE`, `_HYPHEN_RE`) avoid per-call recompilation.
- `dataclasses.replace()` used to return new `RawDocument` instance without mutating input (frozen dataclass, D-06).
