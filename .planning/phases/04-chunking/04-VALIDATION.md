---
phase: 04
slug: chunking
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-25
last_audited: 2026-05-25
---

# Phase 04 - Validation Strategy

> Per-phase validation contract reconstructed from completed plans, summaries, and live tests.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/adapters/chunker/test_markdown_chunker.py -q` |
| **Service integration command** | `uv run pytest tests/domain/test_service.py::TestMarkdownChunkerIntegration -q` |
| **Phase type-boundary command** | `uv run mypy src/selection_maid/adapters/chunker src/selection_maid/config.py src/selection_maid/domain src/selection_maid/errors.py --strict` |
| **Full workspace command** | `uv run pytest tests/ -x -q && uv run mypy src/ --strict` |
| **Estimated runtime** | < 1 second for chunker suite; < 2 seconds for scoped Phase 04 gates |

---

## Sampling Rate

- **After every chunker implementation change:** Run `uv run pytest tests/adapters/chunker/test_markdown_chunker.py -q`
- **After factory/config/service wiring changes:** Run `uv run pytest tests/domain/test_service.py::TestMarkdownChunkerIntegration -q`
- **After type annotation or adapter surface changes:** Run the phase type-boundary command above
- **Before cross-phase release:** Run `uv run pytest tests/ -x -q && uv run mypy src/ --strict`
- **Max feedback latency:** 10 seconds for Phase 04 scoped checks

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | CHUNK-02, D-49..D-51, D-57..D-59 | T-04-01, T-04-SC | `tiktoken` dependency and `ChunkerConfig` are resolved through locked project config | static/unit | `uv run python -c "from selection_maid.config import get_config; print(get_config().chunker.max_tokens)"` | yes | green |
| 04-01-02 | 01 | 1 | CHUNK-01..CHUNK-03, D-57 | T-04-01 | Factory creates `MarkdownChunker` from resolved config | static/unit | `uv run python -c "from selection_maid.adapters.chunker.markdown import MarkdownChunker, build_markdown_chunker; from selection_maid.config import ChunkerConfig; print(type(build_markdown_chunker(ChunkerConfig())).__name__)"` | yes | green |
| 04-02-01 | 02 | 2 | CHUNK-01, D-45..D-46, D-56 | T-04-02 | H1/H2 boundaries drive primary split without treating H3+ as boundaries | unit | `uv run pytest tests/adapters/chunker/test_markdown_chunker.py::TestHeadingBasedSplit -q` | yes | green |
| 04-02-02 | 02 | 2 | CHUNK-01, D-47..D-48, D-56 | T-04-02 | Oversized heading sections split only at paragraph boundaries | unit | `uv run pytest tests/adapters/chunker/test_markdown_chunker.py::TestLargeSectionSubdivision -q` | yes | green |
| 04-03-01 | 03 | 3 | CHUNK-02, D-49..D-52, D-56 | T-04-03 | No-heading documents use tiktoken fallback without cutting paragraphs | unit | `uv run pytest tests/adapters/chunker/test_markdown_chunker.py::TestFixedSizeFallback -q` | yes | green |
| 04-03-02 | 03 | 3 | CHUNK-03, D-53..D-55 | T-04-02, T-04-03 | All chunks receive UUID, page placeholders, word counts, and consistent indexes | unit/integration | `uv run pytest tests/adapters/chunker/test_markdown_chunker.py -q` | yes | green |
| 04-03-03 | 03 | 3 | CHUNK-01..CHUNK-03 | T-04-03 | `ExtractionService.process()` invokes the real chunker through `ChunkerPort` | integration | `uv run pytest tests/domain/test_service.py::TestMarkdownChunkerIntegration -q` | yes | green |
| 04-03-04 | 03 | 3 | ARCH-02, CHUNK-03 | T-04-03 | Chunker adapter satisfies domain contracts under strict typing | static | `uv run mypy src/selection_maid/adapters/chunker src/selection_maid/config.py src/selection_maid/domain src/selection_maid/errors.py --strict` | yes | green |

*Status: pending | green | red | flaky*

---

## Requirement Coverage

| Requirement | Coverage | Test Evidence |
|-------------|----------|---------------|
| CHUNK-01 | COVERED | `TestHeadingBasedSplit`, `TestLargeSectionSubdivision`, `test_service_with_headings_document_splits_correctly` |
| CHUNK-02 | COVERED | `TestFixedSizeFallback`, `test_service_with_no_headings_uses_fallback` |
| CHUNK-03 | COVERED | chunk metadata assertions across `TestHeadingBasedSplit`, `TestLargeSectionSubdivision`, `TestFixedSizeFallback`, and `TestMarkdownChunkerIntegration` |
| D-45..D-46 | COVERED | H1/H2 split, H3/H4 non-split, pre-heading preservation tests |
| D-47..D-48 | COVERED | paragraph subdivision tests with parent section-title retention |
| D-49..D-52 | COVERED | fixed-size fallback tests using `tiktoken` and paragraph-boundary assertions |
| D-53..D-56 | COVERED | UUID v4, page `0`, word-count, section-title, index, and total assertions |
| D-57..D-59 | COVERED | config/factory smoke checks and scoped mypy |

---

## Wave 0 Requirements

- [x] `tests/adapters/chunker/test_markdown_chunker.py` - heading split, subdivision, fallback, and metadata tests
- [x] `tests/domain/test_service.py` - `TestMarkdownChunkerIntegration` service wiring tests
- [x] `src/selection_maid/adapters/chunker/markdown.py` - real `MarkdownChunker` and factory
- [x] `src/selection_maid/config.py` and `config.toml` - `ChunkerConfig(max_tokens=512)` and `[chunker]` section

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | - | All Phase 04 requirements have automated coverage | - |

---

## Validation Audit 2026-05-25

| Metric | Count |
|--------|-------|
| Requirements audited | 11 |
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
| Automated checks run | 6 |

### Evidence

| Command | Result |
|---------|--------|
| `uv run pytest tests/adapters/chunker/test_markdown_chunker.py -q` | PASS: 33 passed |
| `uv run pytest tests/domain/test_service.py::TestMarkdownChunkerIntegration -q` | PASS: 8 passed |
| `uv run mypy src/selection_maid/adapters/chunker src/selection_maid/config.py src/selection_maid/domain src/selection_maid/errors.py --strict` | PASS: no issues in 7 source files |
| `uv run python -c "from selection_maid.config import get_config; print(get_config().chunker.max_tokens)"` | PASS: printed `512` |
| `uv run python -c "from selection_maid.adapters.chunker.markdown import MarkdownChunker, build_markdown_chunker; from selection_maid.config import ChunkerConfig; print(type(build_markdown_chunker(ChunkerConfig())).__name__)"` | PASS: printed `MarkdownChunker` |
| `uv run pytest tests/ -x -q` | FAIL outside Phase 04: `tests/adapters/http/test_integration.py::TestAdversarialInputs::test_valid_html_returns_200` returned HTTP 422 instead of 200 after 117 passing tests |
| `uv run mypy src/ --strict` | FAIL outside Phase 04: `src/selection_maid/adapters/http/router.py:30` missing `psutil` stubs |

Current workspace-wide gates are red due to later-phase HTTP issues. Phase 04's chunking requirements are Nyquist-compliant under the scoped phase validation commands.

---

## Validation Sign-Off

- [x] All tasks have automated verify or resolved Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all previously missing references
- [x] No watch-mode flags
- [x] Feedback latency < 10s for Phase 04 scoped checks
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** automated audit complete
