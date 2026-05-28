---
phase: 14
slug: 14-redesign-ui-with-purple-black-theme-fix-output-formatting-an
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-26
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.1.7 |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npm run test:unit` |
| **Full suite command** | `cd frontend && npm run test:unit` |
| **Estimated runtime** | ~10 seconds |

Baseline: 15 test files, 52 tests, all passing.

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run test:unit`
- **After every plan wave:** Run `cd frontend && npm run test:unit`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 1 | D-01,D-02,D-04,D-08,D-09 | source + lint | `cd frontend && npm run lint && npm run type-check` | ✅ | ⬜ pending |
| 14-01-02 | 01 | 1 | D-05,D-06 | source | `grep -r "from-purple-400 to-white bg-clip-text" frontend/src/App.vue` | ✅ | ⬜ pending |
| 14-02-01 | 02 | 1 | D-12 | unit | `cd frontend && npm run test:unit -- MarkdownRenderer` | ✅ (extend) | ⬜ pending |
| 14-02-02 | 02 | 1 | D-10,D-11,D-13,D-14,D-15 | unit | `cd frontend && npm run test:unit -- MarkdownRenderer` | ✅ (extend) | ⬜ pending |
| 14-03-01 | 03 | 1 | D-18 | unit | `cd frontend && npm run test:unit -- formatters` | ✅ (extend) | ⬜ pending |
| 14-04-01 | 04 | 2 | D-16,D-17,D-18,D-19,D-21 | unit | `cd frontend && npm run test:unit -- ResultView` | ✅ (extend) | ⬜ pending |
| 14-05-01 | 05 | 2 | D-03,D-07,D-14,D-16,D-20,D-21 | unit | `cd frontend && npm run test:unit -- ChunkCard` | ✅ (extend) | ⬜ pending |
| 14-06-01 | 06 | 2 | D-03,D-07 | source | `grep -c "hover:shadow\|hover:glow" frontend/src/components/result/MetadataCard.vue` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/src/components/result/MarkdownRenderer.spec.ts` — extend with test cases for syntax highlight output, table scroll wrapper (`overflow-x-auto`), and link `target="_blank"` attribute
- [ ] `frontend/src/components/result/ChunkCard.spec.ts` — extend with test for download button presence and 1.5s CheckIcon feedback
- [ ] `frontend/src/components/result/ResultView.spec.ts` — update "emits reset" selector from `wrapper.get('button')` to `wrapper.get('[aria-label="Fazer novo upload"]')`; add test for "Download .MD" button presence
- [ ] `frontend/src/lib/formatters.spec.ts` — add `slugifyFilename` test cases including Portuguese diacritics (`ç`, `ã`, `é`, etc.)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| h1 gradient text (purple → white) visible in browser | D-06 | CSS gradient rendering not testable in jsdom | Open localhost:5173 and confirm the h1 shows gradient text |
| ChunkCard hover glow appears on mouse over | D-07 | CSS :hover state not testable in jsdom | Hover over a ChunkCard in the browser — purple box-shadow should appear |
| Scrollbar shows purple tint in Chrome/Firefox | D-08 | scrollbar-color CSS not rendered in jsdom | Open app in browser, scroll a long chunk list — scrollbar thumb should be purple-tinted |
| Syntax highlighting renders in chunk markdown | D-12 | highlight.js DOM output varies by jsdom version | Upload a file with code blocks — check that code blocks have colored spans |
| Download .MD button triggers file download | D-16,D-19 | File download (blob URL) not triggered in jsdom | Click "Download .MD" in ResultView — browser saves a .md file with YAML front-matter |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
