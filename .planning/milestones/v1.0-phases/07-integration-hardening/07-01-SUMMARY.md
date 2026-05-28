---
phase: "07-integration-hardening"
plan: "01"
subsystem: "adapters/extractor + adapters/http + tests/fixtures"
tags: ["hardening", "thread-safety", "memory-management", "adversarial-fixtures", "tempfile"]
dependency_graph:
  requires: ["06-04"]
  provides: ["07-02"]
  affects: ["DoclingAdapter", "Router.ingest", "tests/fixtures/adversarial/"]
tech_stack:
  added: ["pypdf>=6.12.1"]
  patterns: ["threading.Lock for non-thread-safe adapter serialization", "try/finally GC pattern", "backend.unload() resource release"]
key_files:
  created:
    - "tests/fixtures/generate_adversarial.py"
  modified:
    - "src/selection_maid/adapters/extractor/docling.py"
    - "src/selection_maid/adapters/http/router.py"
    - "pyproject.toml"
    - "uv.lock"
    - ".gitignore"
decisions:
  - "D-31: threading.Lock serializes concurrent access to non-thread-safe DocumentConverter"
  - "D-32: gc.collect() + backend.unload() called in finally block after each extraction"
  - "Adversarial fixtures are generated (not committed) — generator script is versioned instead"
  - "large_sample.pdf generated via binary concatenation (not pypdf page-level) for speed and determinism"
metrics:
  duration: "~15 minutes (execution)"
  completed: "2026-05-25T00:20:27Z"
  tasks_completed: 3
  files_modified: 5
---

# Phase 07 Plan 01: Adversarial Fixtures and Adapter Hardening Summary

**One-liner:** threading.Lock + gc.collect() + backend.unload() added to DoclingAdapter; 5 adversarial fixtures generated via versioned script; tempfile prefix added for leak auditing.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Install pypdf and generate adversarial fixtures | fc5e1de | pyproject.toml, uv.lock, .gitignore, tests/fixtures/generate_adversarial.py |
| 2 | Harden DoclingAdapter (Locking & GC) | 27c7501 | src/selection_maid/adapters/extractor/docling.py |
| 3 | Harden Router tempfile prefix | 5833342 | src/selection_maid/adapters/http/router.py |

## What Was Built

### Task 1: Adversarial Fixtures

Added `pypdf>=6.12.1` to dev dependencies. Created `tests/fixtures/generate_adversarial.py` — a versioned, reproducible script that generates 5 adversarial fixtures on demand:

| Fixture | Description | Size |
|---------|-------------|------|
| `corrupt.pdf` | 1KB of seeded random bytes | 1KB |
| `empty.pdf` | Zero-byte file | 0B |
| `spoofed.pdf` | Plain text content with `.pdf` extension | 16B |
| `protected.pdf` | AES-encrypted PDF via pypdf (password: "test") | ~14KB |
| `large_sample.pdf` | Binary concatenation of sample.pdf until >40MB | ~40MB |

The adversarial fixtures themselves are NOT committed (too large; in `.gitignore`). The generator script is committed and can be re-run with `uv run python tests/fixtures/generate_adversarial.py`.

The `.gitignore` was updated to: track `generate_adversarial.py`, ignore `tests/fixtures/adversarial/` (generated files), and preserve the existing pattern for downloaded integration fixtures.

### Task 2: DoclingAdapter Thread Safety and Memory Hardening

Added two hardening mechanisms to `DoclingAdapter`:

**Thread safety (D-31):** `self._lock = threading.Lock()` initialized in `__init__`. The `with self._lock:` block wraps the entire `ThreadPoolExecutor` + `future.result()` sequence, ensuring only one Docling conversion runs at a time. This prevents model state corruption when the FastAPI thread pool dispatches concurrent requests to the same adapter instance.

**Memory management (D-32):** A `try/finally` block wraps the extraction logic:
- `_build_raw_document()` is called inside `try` (before `finally`), so the domain object is constructed while the Docling result is still valid.
- In `finally`: if `result` was assigned, attempts `result.input._backend.unload()` (best-effort, never crashes caller), then `del result`, then `gc.collect()`.

### Task 3: Router Tempfile Prefix

Added `prefix="selectionmaid_"` to the `NamedTemporaryFile` call in the `ingest` handler. This makes tempfiles uniquely identifiable in `/tmp`, enabling the test suite (Phase 07-02 and beyond) to precisely audit for leaked files without false-positive matches on other processes' temp files.

## Verification

```
tests/adapters/extractor/test_docling_adapter.py  14 passed in 25.84s
```

All 14 tests pass (5 unit + 9 integration). The GC and locking changes are transparent to callers — no test modifications required.

Fixture size check passed:
```
ls -lh tests/fixtures/adversarial/large_sample.pdf  →  41M
stat -c %s ...large_sample.pdf                      →  41956089 > 40000000
```

Router prefix check:
```
grep 'prefix="selectionmaid_"' src/selection_maid/adapters/http/router.py  →  found
```

## Deviations from Plan

### Auto-added: Adversarial fixture generator script (Rule 2 — Missing critical functionality)

**Found during:** Task 1
**Issue:** `tests/fixtures/` directory is in `.gitignore` (by design — integration fixtures are downloaded on-demand). The plan listed the adversarial directory as a task output, but the generated files cannot be committed (large binaries, gitignored).
**Fix:** Created `tests/fixtures/generate_adversarial.py` — a versioned, documented script that reproducibly generates all 5 fixtures. Updated `.gitignore` to track the script while ignoring the generated binary files. This is more maintainable than committing large binary fixtures.
**Files modified:** `tests/fixtures/generate_adversarial.py`, `.gitignore`
**Commit:** fc5e1de

### Implementation detail: large_sample.pdf via binary concatenation (not pypdf page-merge)

**Found during:** Task 1
**Issue:** Initial attempt used pypdf to merge pages repeatedly, but pypdf's incremental write pattern was extremely slow (>1000 iterations for a 20KB source). The file was also being overwritten on each iteration.
**Fix:** Used Python's direct binary concatenation (`f.write(sample_data)`) in a while loop — deterministic, fast, and produces a file that exceeds 40MB. The resulting file is technically a concatenated PDF (not a valid merged document), which is appropriate for adversarial testing purposes.
**Commit:** fc5e1de (same)

## Known Stubs

None — all implementations are complete and wired.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes introduced. The `threading.Lock` reduces attack surface by preventing concurrent-write race conditions in the adapter.

## Self-Check: PASSED

| Check | Result |
|-------|--------|
| src/selection_maid/adapters/extractor/docling.py exists | FOUND |
| src/selection_maid/adapters/http/router.py exists | FOUND |
| tests/fixtures/generate_adversarial.py exists | FOUND |
| 07-01-SUMMARY.md exists | FOUND |
| Commit fc5e1de (Task 1) | FOUND |
| Commit 27c7501 (Task 2) | FOUND |
| Commit 5833342 (Task 3) | FOUND |
| threading.Lock in docling.py | FOUND (2 occurrences) |
| gc.collect in docling.py | FOUND (2 occurrences) |
| prefix="selectionmaid_" in router.py | FOUND |
| All 5 adversarial fixtures on disk | FOUND |
| large_sample.pdf > 40MB | 41,956,089 bytes — PASS |
