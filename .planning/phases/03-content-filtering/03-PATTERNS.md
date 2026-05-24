# Phase 03: Content Filtering - Pattern Map

**Mapped:** 2026-05-24
**Files analyzed:** 4
**Analogs found:** 3 / 4

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/selection_maid/adapters/filter/heuristic.py` | adapter | transform | `src/selection_maid/adapters/extractor/docling.py` | exact (role-match) |
| `src/selection_maid/adapters/filter/__init__.py` | adapter | config | `src/selection_maid/adapters/extractor/__init__.py` | exact (role-match) |
| `src/selection_maid/config.py` | config | batch | — | no direct analog |
| `tests/adapters/filter/test_heuristic_filter.py` | test | request-response | `tests/adapters/extractor/test_docling_adapter.py` | exact (role-match) |

## Pattern Assignments

### `src/selection_maid/adapters/filter/heuristic.py` (adapter, transform)

**Analog:** `src/selection_maid/adapters/extractor/docling.py`

**Imports pattern** (lines 20-30):
```python
from __future__ import annotations

import re
from collections import Counter
from typing import Any

from selection_maid.domain.models import RawDocument
from selection_maid.errors import FilterError, SelectionMaidError
```

**Class structure implementing Protocol** (lines 53-65):
```python
class HeuristicFilter:
    """Concrete FilterPort implementation using heuristic rules.

    Addresses repetitive headers/footers, isolated page numbers, and
    excessive whitespace in Markdown content.
    """

    def __init__(
        self,
        min_repeat: int = 3,
        max_line_len: int = 80,
    ) -> None:
        self._min_repeat = min_repeat
        self._max_line_len = max_line_len
```

**Exception wrapping pattern** (lines 88-105):
```python
    def filter(self, document: RawDocument) -> RawDocument:
        try:
            # Transformation logic here
            cleaned_content = self._apply_rules(document.content)
            # D-06: return new instance using dataclasses.replace or constructor
            from dataclasses import replace
            return replace(document, content=cleaned_content)
        except SelectionMaidError:
            raise
        except Exception as exc:
            raise FilterError(
                f"Filtering failed: {exc}",
                cause=exc,
            ) from exc
```

**Factory function pattern** (lines 165-176):
```python
def build_heuristic_filter(
    min_repeat: int = 3,
    max_line_len: int = 80,
) -> HeuristicFilter:
    """Factory function for HeuristicFilter (D-23/D-39)."""
    return HeuristicFilter(min_repeat=min_repeat, max_line_len=max_line_len)
```

---

### `src/selection_maid/adapters/filter/__init__.py` (adapter, config)

**Analog:** `src/selection_maid/adapters/extractor/__init__.py`

**Export pattern** (lines 1-7):
```python
"""Filter adapter subpackage — FilterPort implementations."""

from selection_maid.adapters.filter.heuristic import (
    HeuristicFilter,
    build_heuristic_filter,
)

__all__ = ["HeuristicFilter", "build_heuristic_filter"]
```

---

### `tests/adapters/filter/test_heuristic_filter.py` (test, request-response)

**Analog:** `tests/adapters/extractor/test_docling_adapter.py`

**Rule-based test classes** (D-43):
```python
class TestFILT01Headers:
    """Tests for frequency-based header/footer detection (D-31 to D-34)."""
    def test_removes_repeated_lines(self) -> None: ...

class TestFILT02PageNumbers:
    """Tests for isolated page number removal (D-35, D-36)."""
    def test_removes_arabic_numerals(self) -> None: ...

class TestContentPreservation:
    """Ensures legitimate content is NOT removed (D-44)."""
    def test_preserves_headings(self) -> None: ...
```

**Inline string fixtures** (D-42):
```python
    def test_removes_repeated_lines(self) -> None:
        content = "Line 1\nHeader\nLine 2\nHeader\nLine 3\nHeader"
        doc = RawDocument(content=content, filename="test.md", page_count=3, format="pdf")
        # ...
```

## Shared Patterns

### Constructor Injection (D-21/D-39)
**Source:** `src/selection_maid/adapters/extractor/docling.py`
**Apply to:** All adapters (`HeuristicFilter`)
Adapters receive their configuration values (thresholds, timeouts, converters) via `__init__` arguments, allowing for easy testing with different values.

### Exception Wrapping (D-16)
**Source:** `src/selection_maid/service.py` and `src/selection_maid/adapters/extractor/docling.py`
**Apply to:** All adapters and service methods
```python
try:
    # operation
except SelectionMaidError:
    raise
except Exception as e:
    raise DomainSpecificError(message=f"...", cause=e) from e
```

### Factory Function Pattern (D-23)
**Source:** `src/selection_maid/adapters/extractor/docling.py`
**Apply to:** All adapters
Provide a `build_<name>_adapter` or `build_<name>_filter` function to simplify construction and ensure consistent initialization across the project.

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns instead):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `src/selection_maid/config.py` | config | batch | First implementation of centralized configuration. |

## Metadata

**Analog search scope:** `src/selection_maid`, `tests`
**Files scanned:** 12
**Pattern extraction date:** 2026-05-24
