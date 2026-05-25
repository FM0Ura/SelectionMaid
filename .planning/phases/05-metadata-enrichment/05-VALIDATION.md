---
phase: 05
slug: metadata-enrichment
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-25
last_audited: 2026-05-25
---

# Phase 05 - Validation Strategy

> Per-phase validation contract reconstructed from completed plans, summaries, and live tests.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/adapters/enricher/test_metadata_enricher.py -q` |
| **Domain/service command** | `uv run pytest tests/domain/test_models.py tests/domain/test_service.py -q` |
| **Phase type-boundary command** | `uv run mypy src/selection_maid/adapters/enricher src/selection_maid/config.py src/selection_maid/domain src/selection_maid/errors.py --strict` |
| **Full workspace command** | `uv run pytest tests/ -x -q && uv run mypy src/ --strict` |
| **Estimated runtime** | < 1 second for enricher suite; < 2 seconds for scoped Phase 05 gates |

---

## Sampling Rate

- **After every metadata-enricher change:** Run `uv run pytest tests/adapters/enricher/test_metadata_enricher.py -q`
- **After domain metadata schema changes:** Run `uv run pytest tests/domain/test_models.py tests/domain/test_service.py -q`
- **After type annotation or adapter surface changes:** Run the phase type-boundary command above
- **Before cross-phase release:** Run `uv run pytest tests/ -x -q && uv run mypy src/ --strict`
- **Max feedback latency:** 10 seconds for Phase 05 scoped checks

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | META-01, ARCH-01, D-68..D-70 | T-05-01-SC | `DocumentMetadata` has all 9 required immutable fields and stubs use the new schema | unit/static | `uv run python -c "from selection_maid.domain.models import DocumentMetadata; import dataclasses; print(len(dataclasses.fields(DocumentMetadata)))"` | yes | green |
| 05-01-02 | 01 | 1 | META-01, D-68 | T-05-01-SC | Domain/service tests enforce schema compatibility across the pipeline | unit/integration | `uv run pytest tests/domain/test_models.py tests/domain/test_service.py -q` | yes | green |
| 05-01-03 | 01 | 1 | D-72..D-73 | T-05-01-SC | `langdetect` and empty `EnricherConfig` are wired through project config | static | `uv run python -c "from selection_maid.config import get_config; assert hasattr(get_config(), 'enricher')"` | yes | green |
| 05-02-01 | 02 | 2 | META-02, D-60..D-62 | T-05-02-02 | Language detection uses confidence threshold and returns `und` on uncertainty or exceptions | unit | `uv run pytest tests/adapters/enricher/test_metadata_enricher.py::TestDetectLanguage -q` | yes | green |
| 05-02-02 | 02 | 2 | META-03, D-63..D-65 | T-05-02-01 | `doc_type` inference stays inside closed vocabulary with deterministic fallback | unit | `uv run pytest tests/adapters/enricher/test_metadata_enricher.py::TestInferDocType -q` | yes | green |
| 05-02-03 | 02 | 2 | META-01, D-66..D-70 | T-05-02-01 | `enrich()` maps title, author, doc_id, filename, counts, and timestamp | unit | `uv run pytest tests/adapters/enricher/test_metadata_enricher.py::TestEnrich -q` | yes | green |
| 05-02-04 | 02 | 2 | D-71..D-73 | T-05-02-01 | Factory creates a real `MetadataEnricher` from `EnricherConfig` | static/unit | `uv run python -c "from selection_maid.adapters.enricher.default import MetadataEnricher, build_metadata_enricher; from selection_maid.config import get_config; print(type(build_metadata_enricher(get_config().enricher)).__name__)"` | yes | green |
| 05-03-01 | 03 | 3 | META-01..META-03 | T-05-03-01 | Edge cases cover empty content, duplicate H1, UUID uniqueness, and timezone-aware timestamps | unit | `uv run pytest tests/adapters/enricher/test_metadata_enricher.py::TestEdgeCases -q` | yes | green |
| 05-03-02 | 03 | 3 | ARCH-01, META-01..META-03 | T-05-03-01 | Enricher adapter satisfies domain contracts under strict typing | static | `uv run mypy src/selection_maid/adapters/enricher src/selection_maid/config.py src/selection_maid/domain src/selection_maid/errors.py --strict` | yes | green |

*Status: pending | green | red | flaky*

---

## Requirement Coverage

| Requirement | Coverage | Test Evidence |
|-------------|----------|---------------|
| META-01 | COVERED | `TestDocumentMetadata`, `TestEnrich`, `TestEdgeCases`, `tests/domain/test_service.py` metadata assertions |
| META-02 | COVERED | `TestDetectLanguage` for English, Portuguese, Spanish, low confidence, and exceptions |
| META-03 | COVERED | `TestInferDocType` for legal, presentation, form, report, and fallback `other` |
| D-60..D-62 | COVERED | `TestDetectLanguage` threshold and exception tests |
| D-63..D-65 | COVERED | `TestInferDocType` closed-vocabulary heuristics |
| D-66..D-67 | COVERED | `TestExtractTitle`, `TestEnrich::test_author_is_empty_string` |
| D-68..D-70 | COVERED | schema smoke check, `TestEnrich`, `TestEdgeCases` |
| D-71..D-73 | COVERED | factory smoke check and scoped mypy |

---

## Wave 0 Requirements

- [x] `tests/adapters/enricher/test_metadata_enricher.py` - language detection, doc type, title, field mapping, and edge-case tests
- [x] `tests/domain/test_models.py` - `DocumentMetadata` 9-field schema tests
- [x] `tests/domain/test_service.py` - pipeline metadata field assertions
- [x] `src/selection_maid/adapters/enricher/default.py` - real `MetadataEnricher` and factory
- [x] `src/selection_maid/config.py` - `EnricherConfig` and `GlobalConfig.enricher`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | - | All Phase 05 requirements have automated coverage | - |

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
| `uv run pytest tests/adapters/enricher/test_metadata_enricher.py -q` | PASS: 30 passed |
| `uv run pytest tests/domain/test_models.py tests/domain/test_service.py -q` | PASS: 36 passed |
| `uv run mypy src/selection_maid/adapters/enricher src/selection_maid/config.py src/selection_maid/domain src/selection_maid/errors.py --strict` | PASS: no issues in 7 source files |
| `uv run python -c "from selection_maid.domain.models import DocumentMetadata; import dataclasses; print(len(dataclasses.fields(DocumentMetadata)))"` | PASS: printed `9` |
| `uv run python -c "from selection_maid.adapters.enricher.default import MetadataEnricher, build_metadata_enricher; from selection_maid.config import get_config; print(type(build_metadata_enricher(get_config().enricher)).__name__)"` | PASS: printed `MetadataEnricher` |
| `uv run pytest tests/ -x -q` | FAIL outside Phase 05: `tests/adapters/http/test_integration.py::TestAdversarialInputs::test_valid_html_returns_200` returned HTTP 422 instead of 200 after 117 passing tests |
| `uv run mypy src/ --strict` | FAIL outside Phase 05: `src/selection_maid/adapters/http/router.py:30` missing `psutil` stubs |

Current workspace-wide gates are red due to later-phase HTTP issues. Phase 05's metadata-enrichment requirements are Nyquist-compliant under the scoped phase validation commands.

---

## Validation Sign-Off

- [x] All tasks have automated verify or resolved Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all previously missing references
- [x] No watch-mode flags
- [x] Feedback latency < 10s for Phase 05 scoped checks
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** automated audit complete
