---
phase: 03
slug: content-filtering
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-24
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest tests/adapters/filter/test_heuristic_filter.py` |
| **Full suite command** | `pytest tests/` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run task-specific verify or `pytest tests/adapters/filter/test_heuristic_filter.py`
- **After every plan wave:** Run `pytest tests/`
- **Before /gsd:verify-work:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | ARCH-02 | T-03-01 | Graceful fallback | unit | `python3 -c "from selection_maid.config import get_config; print(get_config().filter.min_repeat)"` | ✅ | ⬜ pending |
| 03-02-01 | 02 | 1 | FILT-01 | T-03-02 | ReDoS mitigation | unit | `uv run pytest tests/adapters/filter/test_heuristic_filter.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/adapters/filter/test_heuristic_filter.py` — stubs for FILT-01, FILT-02, FILT-03

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| N/A | | | |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
