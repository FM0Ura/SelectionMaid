# Plan 03-03 Summary — Factory + Service Integration

**Status:** Complete
**Commits:** fc5f810, 612a09b
**Duration:** ~5 min

## What Was Built

### Task 1: `build_heuristic_filter` factory with config integration

Updated `build_heuristic_filter` in [src/selection_maid/adapters/filter/heuristic.py](src/selection_maid/adapters/filter/heuristic.py) to accept `None` parameters and resolve them from `get_config()` (D-39):

```python
def build_heuristic_filter(
    min_repeat: int | None = None,
    max_line_len: int | None = None,
) -> HeuristicFilter:
    from selection_maid.config import get_config  # deferred to avoid circular import
    cfg = get_config()
    resolved_min_repeat = min_repeat if min_repeat is not None else cfg.filter.min_repeat
    resolved_max_line_len = max_line_len if max_line_len is not None else cfg.filter.max_line_len
    return HeuristicFilter(min_repeat=resolved_min_repeat, max_line_len=resolved_max_line_len)
```

The deferred import avoids a circular import at module load time. Callers that pass explicit values bypass the config lookup entirely.

### Task 2: Service integration test

Added `TestHeuristicFilterIntegration` class to [tests/domain/test_service.py](tests/domain/test_service.py). The test wires a real `HeuristicFilter(min_repeat=3)` into `ExtractionService` alongside a `NoisyExtractor` (returns content with a repeated header 3×). Verifies the pipeline output has the noise removed and useful content preserved.

## Verification

```
uv run pytest tests/domain/test_service.py -v
# 12 passed in 0.04s
```

## Notes

- `__init__.py` already exported `HeuristicFilter` and `build_heuristic_filter` from plan 03-02 — no changes needed in this plan.
- The deferred `from selection_maid.config import get_config` pattern is intentional and consistent with how Python avoids circular imports in packages where domain ↔ adapter cross-references would otherwise form a cycle.
