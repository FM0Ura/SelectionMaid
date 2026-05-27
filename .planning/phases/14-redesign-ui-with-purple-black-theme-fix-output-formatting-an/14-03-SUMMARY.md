---
phase: 14
plan: 03
subsystem: frontend/lib
tags: [utility, tdd, formatters, slugify, download]
requires: []
provides: [slugifyFilename]
affects: [frontend/src/components/result/ResultView.vue, frontend/src/components/result/ChunkCard.vue]
tech_stack:
  added: []
  patterns: [TDD red-green, NFD Unicode normalization, pure TypeScript utility]
key_files:
  created: []
  modified:
    - frontend/src/lib/formatters.ts
    - frontend/src/lib/formatters.spec.ts
decisions:
  - Use Unicode combining diacriticals range escape form in regex (U+0300-U+036F via NFD decomposition) to handle Portuguese accents without encoding fragility
metrics:
  duration: "1m 7s"
  completed: "2026-05-27"
  tasks: 1
  files: 2
---

# Phase 14 Plan 03: slugifyFilename Utility — Summary

**One-liner:** TDD implementation of `slugifyFilename` in `formatters.ts` using NFD normalization for Portuguese diacritic stripping, exported as a shared dependency for Wave 2 download features.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Add failing slugifyFilename tests | ddc5782 | frontend/src/lib/formatters.spec.ts |
| 1 (GREEN) | Implement slugifyFilename | cb6fa7d | frontend/src/lib/formatters.ts |

## What Was Built

Added `slugifyFilename(filename: string): string` to `frontend/src/lib/formatters.ts` as a pure function that:

1. Strips the file extension via `/\.[^.]+$/`
2. Lowercases the result
3. Applies Unicode NFD normalization to decompose diacritics into base + combining character pairs
4. Removes combining diacriticals (U+0300–U+036F range) — covers all Portuguese accents
5. Replaces sequences of non-alphanumeric characters with a single hyphen
6. Trims leading and trailing hyphens

Extended `frontend/src/lib/formatters.spec.ts` with a `describe('slugifyFilename')` block containing 4 `it()` cases:
- ASCII slug: `report.pdf` → `report`
- Portuguese diacritics: `Calendário de Provas 2026.pdf` → `calendario-de-provas-2026`
- Multi-hyphen collapse: `my  file--name.docx` → `my-file-name`
- Leading/trailing trim: `-bad-name-.pdf` → `bad-name`

Total test count for `formatters.spec.ts`: 8 (4 existing + 4 new) — all passing.

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED — failing tests committed before implementation | ddc5782 | PASS |
| GREEN — implementation makes all tests pass | cb6fa7d | PASS |
| REFACTOR — no refactor needed (clean implementation) | N/A | N/A |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. The utility is fully implemented and tested.

## Threat Flags

The threat model (T-14-04) required that `slugifyFilename` output be safe for use as the `anchor.download` attribute value, preventing path traversal attacks. Verified: the function restricts output to `[a-z0-9-]` only; sequences like `../` decompose to `---` then collapse to `-`, neutralizing traversal attempts.

## Self-Check

### Files exist:
- `frontend/src/lib/formatters.ts` — contains `export function slugifyFilename`
- `frontend/src/lib/formatters.spec.ts` — contains `describe('slugifyFilename'` with 4 cases

### Commits exist:
- `ddc5782` — test(14-03): add failing tests for slugifyFilename
- `cb6fa7d` — feat(14-03): implement slugifyFilename in formatters.ts

## Self-Check: PASSED
