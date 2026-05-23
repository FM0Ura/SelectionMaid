---
phase: 02
slug: docling-extraction-adapter
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-23
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/adapters/extractor/ -x -q --tb=short` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
| **Estimated runtime** | ~60–120 seconds (integration tests hit real Docling conversion) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/adapters/extractor/ -x -q --tb=short`
- **After every plan wave:** Run `uv run pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** `uv run pytest tests/ -q && uv run mypy src/ --strict` both green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | EXT-01..EXT-07 | — | N/A | unit | `uv run mypy src/ --strict` | ✅ | ⬜ pending |
| 02-02-01 | 02 | 2 | EXT-01 | — | N/A | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_pdf_extraction -x` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 2 | EXT-02 | — | N/A | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_docx_extraction -x` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 2 | EXT-03 | — | N/A | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_html_extraction -x` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 2 | EXT-04 | — | N/A | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_headings_in_pdf -x` | ❌ W0 | ⬜ pending |
| 02-03-02 | 03 | 2 | EXT-05 | — | N/A | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_tables_in_docx -x` | ❌ W0 | ⬜ pending |
| 02-03-03 | 03 | 2 | EXT-06 | — | N/A | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_lists_in_html -x` | ❌ W0 | ⬜ pending |
| 02-03-04 | 03 | 2 | EXT-07 | — | N/A | integration | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_code_blocks -x` | ❌ W0 | ⬜ pending |
| 02-04-01 | 04 | 3 | D-24/D-25 | — | Timeout isolates caller | unit | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_timeout -x` | ❌ W0 | ⬜ pending |
| 02-04-02 | 04 | 3 | D-22 | — | N/A | unit | `uv run pytest tests/adapters/extractor/test_docling_adapter.py::test_unsupported_format -x` | ❌ W0 | ⬜ pending |
| 02-04-03 | 04 | 3 | ARCH-01 | — | No type leakage | static | `uv run mypy src/ --strict` | ✅ | ⬜ pending |
| 02-05-01 | 05 | 3 | EXT-01..EXT-07 | — | N/A | integration | `uv run pytest tests/adapters/extractor/ -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/adapters/extractor/conftest.py` — session fixtures: `real_pdf_path`, `real_docx_path`, `real_html_path` (download-on-demand pattern)
- [ ] `tests/adapters/extractor/test_docling_adapter.py` — unit tests (mock converter) + integration tests (real fixtures)
- [ ] `tests/fixtures/.gitkeep` — ensure fixtures directory exists and is gitignored
- [ ] `pyproject.toml` — add `docling>=2.95.0` dependency + `[tool.uv.sources]` + `[[tool.uv.index]]` for pytorch-cpu index

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| DocumentConverter instanciado apenas uma vez | EXT-05 singleton | Verificado via log + test fixture com contador de instâncias | Injetar spy no `__init__` e chamar extração 3x; confirmar contador = 1 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
