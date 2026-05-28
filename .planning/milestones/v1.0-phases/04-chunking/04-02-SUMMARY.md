---
phase: 04-chunking
plan: "02"
subsystem: chunker
tags: [tdd, chunking, heading-split, paragraph-subdivision, uuid, metadata]
dependency_graph:
  requires:
    - "04-01"  # ChunkerConfig, build_markdown_chunker factory, MarkdownChunker skeleton
    - "01-domain-foundation"  # DocumentChunk, ChunkerPort, ChunkingError
  provides:
    - "heading_split_strategy"  # MarkdownChunker._heading_split()
    - "paragraph_subdivision"   # _subdivide_by_paragraph()
  affects:
    - "04-03"  # fixed-size fallback; _fixed_size_split() is already present
tech_stack:
  added:
    - re (stdlib, regex for H1/H2 detection)
    - uuid (stdlib, UUID v4 generation)
  patterns:
    - TDD RED/GREEN two-task sequence covering all 22 behaviours before implementation
    - Line-iteration accumulation pattern for heading-boundary detection
    - Paragraph-accumulation pattern for word-budget subdivision
    - Second-pass index assignment after all chunks are collected
key_files:
  created:
    - tests/adapters/chunker/test_markdown_chunker.py
  modified:
    - src/selection_maid/adapters/chunker/markdown.py
decisions:
  - "D-45: regex ^#{1,2}\s+(.+) applied line-by-line; H3+ treated as content"
  - "D-46: pre-heading text captured as chunk with section_title=''"
  - "D-47: _subdivide_by_paragraph() accumulates whole paragraphs; flushes on word-budget exceeded"
  - "D-48: word count (len(split())) used as the budget measure for paragraph subdivision"
  - "D-53: page_start=page_end=0 for all chunks"
  - "D-54: chunk_id=str(uuid.uuid4()) — unique per chunk per call"
  - "D-55: word_count=len(content.split())"
  - "D-56: section_title stripped of leading '#'; all sub-chunks inherit parent title"
metrics:
  duration_minutes: ~30
  completed: "2026-05-24"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 1
---

# Phase 04 Plan 02: Heading-Based Split Implementation Summary

**One-liner:** Line-iteration heading-split and paragraph-boundary subdivision with UUID v4 metadata, tested TDD-first across 22 behaviours.

## What Was Built

`MarkdownChunker.chunk()` is now fully implemented with the primary heading-based strategy and the paragraph-subdivision pass. The fixed-size fallback (`_fixed_size_split()`) was also delivered as a complete stub — it is exercised by Plan 04-03's tests but its logic was straightforward to include here.

Key additions to `src/selection_maid/adapters/chunker/markdown.py`:

- `_H1_H2_PATTERN`: module-level compiled regex `^#{1,2}\s+(.+)` (D-45)
- `_make_chunk()`: helper that assembles a `DocumentChunk` with all CHUNK-03 fields
- `_subdivide_by_paragraph()`: module-level function that splits a section's text by `\n\n` boundaries without cutting inside a paragraph (D-47)
- `MarkdownChunker._heading_split()`: primary strategy — line-iteration accumulator, heading detection, per-section subdivision
- `MarkdownChunker._fixed_size_split()`: fallback strategy — tiktoken-measured paragraph accumulation
- `MarkdownChunker.chunk()`: dispatcher — empty-string guard, strategy selection, second-pass index assignment

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED (test) | 9a33847 | PASSED — 22 tests failed as expected |
| GREEN (feat) | 434b745 | PASSED — 22 tests pass |
| REFACTOR | N/A | No refactor needed — code was clean on first pass |

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| RED | Failing tests for heading split + large section | 9a33847 | tests/adapters/chunker/test_markdown_chunker.py |
| GREEN | Implement heading split + subdivision | 434b745 | src/selection_maid/adapters/chunker/markdown.py |

## Decisions Made

- **D-45 confirmed:** Regex `^#{1,2}\s+(.+)` applied line-by-line. Heading line is included in the chunk content (the heading text itself), while `section_title` holds just the text without `#`.
- **D-46 confirmed:** Pre-heading text is only emitted if non-empty after stripping; truly empty pre-heading sections are silently discarded.
- **D-47/D-48:** Word count (`len(section_text.split())`) used as the budget measure during paragraph subdivision — consistent with D-55's definition of word_count. This avoids a tiktoken call per section in the heading path.
- **D-53/D-54/D-55:** Applied identically in `_make_chunk()`.
- **Second pass confirmed:** `chunk_index` and `total_chunks` are assigned after all `(content, title)` pairs are collected, preventing the need to know total count during accumulation.

## Verification

```
$ uv run pytest tests/adapters/chunker/test_markdown_chunker.py -v
22 passed in 0.12s

$ uv run pytest tests/ -v --tb=short
97 passed, 1 warning in 19.21s  (no regressions)

$ uv run mypy src/selection_maid/adapters/chunker/markdown.py --strict
Success: no issues found in 1 source file
```

## Deviations from Plan

None — plan executed exactly as written.

Both tasks in the plan were combined into a single TDD RED/GREEN cycle covering all 22 behaviours (16 for Task 1, 6 for Task 2) before any implementation was written. This is consistent with the plan's `tdd="true"` annotation.

The `_fixed_size_split()` method was also implemented in this plan even though Plan 04-03 owns its tests, because the method is trivially derived from the same paragraph-accumulation pattern used for subdivision. It does not conflict with 04-03 and reduces the implementation surface of the next plan.

## Known Stubs

None — all fields are fully populated; no placeholder values or hardcoded empties that flow to consumers.

## Self-Check

**Files created/modified:**
- `tests/adapters/chunker/test_markdown_chunker.py`: FOUND
- `src/selection_maid/adapters/chunker/markdown.py`: FOUND

**Commits:**
- 9a33847: FOUND
- 434b745: FOUND

## Self-Check: PASSED
