---
phase: 01
slug: domain-foundation
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-24
audited: 2026-05-24T21:51:55-03:00
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/domain/ -q` |
| **Full suite command** | `uv run pytest tests/domain/ -q && uv run mypy src/selection_maid/domain src/selection_maid/service.py src/selection_maid/errors.py tests/domain/test_models.py tests/domain/test_service.py tests/stubs/adapters.py --strict` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-specific automated command in the map below
- **After every plan wave:** Run `uv run pytest tests/domain/ -q`
- **Before `$gsd-verify-work`:** Domain pytest and mypy commands must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | ARCH-07 | T-01-01, T-01-02 | Frozen dataclasses and zero third-party domain imports | unit/static | `uv run pytest tests/domain/test_models.py -q && uv run mypy src/selection_maid/domain/models.py --strict` | ✅ | ✅ green |
| 01-01-02 | 01 | 1 | ARCH-07 | T-01-01 | Package scaffold and immutable result collection present | smoke/static | `uv run python -c "from selection_maid.domain.models import RawInput, RawDocument, DocumentChunk, DocumentMetadata, ExtractionResult; print('OK')"` | ✅ | ✅ green |
| 01-02-01 | 02 | 1 | ARCH-01 | T-01-02-01 | Extractor boundary references only domain model types | static | `uv run mypy src/selection_maid/domain/ports.py --strict` | ✅ | ✅ green |
| 01-02-02 | 02 | 1 | ARCH-02 | T-01-02-01 | Filter boundary references only domain model types | static | `uv run mypy src/selection_maid/domain/ports.py --strict` | ✅ | ✅ green |
| 01-02-03 | 02 | 1 | ARCH-03 | T-01-02-01 | Chunker boundary returns `list[DocumentChunk]` for service conversion | static | `uv run mypy src/selection_maid/domain/ports.py --strict` | ✅ | ✅ green |
| 01-02-04 | 02 | 1 | ARCH-04 | T-01-02-01 | Metadata enricher boundary references only domain model types | static | `uv run mypy src/selection_maid/domain/ports.py --strict` | ✅ | ✅ green |
| 01-03-01 | 03 | 2 | ARCH-06 | T-01-03-01, T-01-03-02 | Service injects all ports and wraps adapter exceptions | unit/static | `uv run pytest tests/domain/test_service.py -q && uv run mypy src/selection_maid/service.py --strict` | ✅ | ✅ green |
| 01-04-01 | 04 | 2 | ARCH-06 | T-01-04-01, T-01-04-02 | Domain errors carry fixed codes with no HTTP coupling | unit/static | `uv run mypy src/selection_maid/errors.py --strict` | ✅ | ✅ green |
| 01-05-01 | 05 | 3 | ARCH-01, ARCH-02, ARCH-03, ARCH-04 | T-01-02-01 | Reusable stubs satisfy port protocols structurally | unit/static | `uv run mypy tests/stubs/adapters.py --strict` | ✅ | ✅ green |
| 01-05-02 | 05 | 3 | ARCH-06, ARCH-07 | T-01-01, T-01-03-02 | Full stubbed pipeline returns immutable `ExtractionResult` and wraps failures | unit | `uv run pytest tests/domain/ -q` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Requirement Coverage

| Requirement | Coverage | Evidence |
|-------------|----------|----------|
| ARCH-01 | COVERED | `ExtractorPort` in `ports.py`; `tests/stubs/adapters.py`; domain mypy clean |
| ARCH-02 | COVERED | `FilterPort` in `ports.py`; `StubFilter`; `TestHeuristicFilterIntegration`; domain tests green |
| ARCH-03 | COVERED | `ChunkerPort` in `ports.py`; `StubChunker`; `TestMarkdownChunkerIntegration`; domain tests green |
| ARCH-04 | COVERED | `MetadataEnricherPort` in `ports.py`; `StubEnricher`; domain tests green |
| ARCH-06 | COVERED | `ExtractionService` constructor injection, zero third-party imports, exception wrapping tests, mypy clean |
| ARCH-07 | COVERED | Frozen domain dataclass tests and import/static checks in `tests/domain/test_models.py` |

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | — | All Phase 1 behaviors have automated verification | — |

---

## Validation Audit 2026-05-24

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
| Automated requirements covered | 6 |
| Manual-only requirements | 0 |

Fresh commands:

| Command | Result |
|---------|--------|
| `uv run pytest tests/domain/ -q` | 36 passed in 0.14s |
| `uv run mypy src/selection_maid/domain src/selection_maid/service.py src/selection_maid/errors.py tests/domain/test_models.py tests/domain/test_service.py tests/stubs/adapters.py --strict` | Success: no issues found in 8 source files |
| `uv run python -c "from selection_maid.domain.models import RawInput, RawDocument, DocumentChunk, DocumentMetadata, ExtractionResult; from selection_maid.domain.ports import ExtractorPort, FilterPort, ChunkerPort, MetadataEnricherPort; from selection_maid.service import ExtractionService; from selection_maid.errors import SelectionMaidError, ExtractionError; print('phase1 imports OK')"` | `phase1 imports OK` |

Additional static checks:

- `grep -c 'frozen=True' src/selection_maid/domain/models.py` → 5
- `grep -c 'except SelectionMaidError' src/selection_maid/service.py` → 4
- `rg -n "docling|fastapi|pydantic" src/selection_maid/domain src/selection_maid/service.py src/selection_maid/errors.py` → no matches

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-05-24
