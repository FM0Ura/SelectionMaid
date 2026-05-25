---
phase: 03
slug: content-filtering
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-24
last_audited: 2026-05-25
---

# Phase 03 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/adapters/filter/test_heuristic_filter.py -q` |
| **Service integration command** | `uv run pytest tests/domain/test_service.py -q` |
| **Phase type-boundary command** | `uv run mypy src/selection_maid/adapters/filter src/selection_maid/config.py src/selection_maid/domain src/selection_maid/errors.py --strict` |
| **Full workspace command** | `uv run pytest tests/ -x -q && uv run mypy src/ --strict` |
| **Estimated runtime** | < 1 second for filter suite; < 2 seconds for scoped Phase 03 gates |

---

## Sampling Rate

- **After every filter implementation change:** Run `uv run pytest tests/adapters/filter/test_heuristic_filter.py -q`
- **After factory/config/service wiring changes:** Run `uv run pytest tests/domain/test_service.py -q`
- **After type annotation or public adapter surface changes:** Run the phase type-boundary command above
- **Before cross-phase release:** Run `uv run pytest tests/ -x -q && uv run mypy src/ --strict`
- **Max feedback latency:** 10 seconds for Phase 03 scoped checks

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | ARCH-02, FILT-01..FILT-03, D-38..D-40 | T-03-01 | Missing or partial config falls back to defaults | static/unit | `uv run python -c "from selection_maid.config import get_config; print(get_config().filter.min_repeat)"` | yes | green |
| 03-02-01 | 02 | 1 | FILT-01, D-31..D-34 | T-03-02 | Repeated header/footer filtering avoids headings and tables | unit | `uv run pytest tests/adapters/filter/test_heuristic_filter.py::TestFILT01Headers -q` | yes | green |
| 03-02-02 | 02 | 1 | FILT-02, D-35..D-36 | T-03-02 | Non-backtracking regex removes only isolated page numbers | unit | `uv run pytest tests/adapters/filter/test_heuristic_filter.py::TestFILT02PageNumbers -q` | yes | green |
| 03-02-03 | 02 | 1 | FILT-03, D-37 | T-03-02 | Whitespace compression is bounded and applied last | unit | `uv run pytest tests/adapters/filter/test_heuristic_filter.py::TestFILT03Whitespace -q` | yes | green |
| 03-02-04 | 02 | 1 | FILT-01..FILT-03, D-44 | T-03-02 | Legitimate headings, tables, paragraphs, and lists survive filtering | unit | `uv run pytest tests/adapters/filter/test_heuristic_filter.py::TestContentPreservation -q` | yes | green |
| 03-02-05 | 02 | 1 | ARCH-02, D-16 | T-03-02 | Unexpected filter exceptions become `FilterError`; domain errors pass through | unit | `uv run pytest tests/adapters/filter/test_heuristic_filter.py::TestErrorHandling -q` | yes | green |
| 03-03-01 | 03 | 2 | ARCH-02, D-39, D-41 | T-03-03 | Factory uses centralized config values without leaking runtime cycles | unit/static | `uv run pytest tests/adapters/filter/test_heuristic_filter.py::TestFactory -q && uv run mypy src/selection_maid/adapters/filter src/selection_maid/config.py src/selection_maid/domain src/selection_maid/errors.py --strict` | yes | green |
| 03-03-02 | 03 | 2 | ARCH-02, FILT-01..FILT-03 | T-03-03 | `ExtractionService.process()` invokes the real filter and preserves useful content | integration | `uv run pytest tests/domain/test_service.py::TestHeuristicFilterIntegration -q` | yes | green |

*Status: pending | green | red | flaky*

---

## Requirement Coverage

| Requirement | Coverage | Test Evidence |
|-------------|----------|---------------|
| FILT-01 | COVERED | `TestFILT01Headers`, `TestContentPreservation` |
| FILT-02 | COVERED | `TestFILT02PageNumbers`, `TestContentPreservation` |
| FILT-03 | COVERED | `TestFILT03Whitespace`, `TestContentPreservation` |
| ARCH-02 | COVERED | `TestErrorHandling`, `TestFactory`, `TestHeuristicFilterIntegration`, scoped mypy |
| D-16 | COVERED | `TestErrorHandling` |
| D-31..D-34 | COVERED | `TestFILT01Headers` |
| D-35..D-36 | COVERED | `TestFILT02PageNumbers` |
| D-37 | COVERED | `TestFILT03Whitespace` |
| D-38..D-40 | COVERED | config smoke check and `TestFactory` |
| D-41 | COVERED | filter package export and factory smoke check |
| D-44 | COVERED | `TestContentPreservation` |

---

## Wave 0 Requirements

- [x] `tests/adapters/filter/test_heuristic_filter.py` - FILT-01, FILT-02, FILT-03, content-preservation, error-handling, and factory tests
- [x] `tests/domain/test_service.py` - service integration test using real `HeuristicFilter`
- [x] `src/selection_maid/config.py` - `FilterConfig` and `get_config()` defaults
- [x] `config.toml` - default `[filter]` section

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | - | All Phase 03 requirements have automated coverage | - |

---

## Validation Audit 2026-05-25

| Metric | Count |
|--------|-------|
| Requirements audited | 11 |
| Gaps found | 1 |
| Resolved | 1 |
| Escalated | 0 |
| Automated checks run | 7 |

### Gaps Filled

| Gap | Resolution | Evidence |
|-----|------------|----------|
| `build_heuristic_filter(config: "FilterConfig | None")` referenced `FilterConfig` only as a forward string without a type-checking import, causing scoped strict mypy failure. Factory behavior also lacked direct unit coverage. | Added `TYPE_CHECKING` import guard for `FilterConfig` in `heuristic.py` and added `TestFactory::test_build_heuristic_filter_uses_explicit_config`. | scoped mypy passes; filter suite increased from 33 to 34 tests |

### Evidence

| Command | Result |
|---------|--------|
| `uv run pytest tests/adapters/filter/test_heuristic_filter.py -q` | PASS: 34 passed |
| `uv run pytest tests/domain/test_service.py -q` | PASS: 20 passed |
| `uv run mypy src/selection_maid/adapters/filter src/selection_maid/config.py src/selection_maid/domain src/selection_maid/errors.py --strict` | PASS: no issues in 7 source files |
| `uv run python -c "from selection_maid.config import get_config; print(get_config().filter.min_repeat)"` | PASS: printed `3` |
| `uv run python -c "from selection_maid.adapters.filter import build_heuristic_filter; print(type(build_heuristic_filter()).__name__)"` | PASS: printed `HeuristicFilter` |
| `uv run pytest tests/ -x -q` | FAIL outside Phase 03: `tests/adapters/http/test_integration.py::TestAdversarialInputs::test_valid_html_returns_200` returned HTTP 422 instead of 200 after 117 passing tests |
| `uv run mypy src/ --strict` | FAIL outside Phase 03: `src/selection_maid/adapters/http/router.py:30` missing `psutil` stubs |

Current workspace-wide gates are red due to later-phase HTTP issues. Phase 03's content-filtering requirements are Nyquist-compliant under the scoped phase validation commands.

---

## Validation Sign-Off

- [x] All tasks have automated verify or resolved Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all previously missing references
- [x] No watch-mode flags
- [x] Feedback latency < 10s for Phase 03 scoped checks
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** automated audit complete
