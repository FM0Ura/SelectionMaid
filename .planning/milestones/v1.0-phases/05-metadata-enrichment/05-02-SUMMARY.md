---
phase: "05"
plan: "02"
subsystem: "adapters/enricher"
tags: [metadata, enrichment, langdetect, doc-type-inference, language-detection, hexagonal-architecture]

dependency_graph:
  requires:
    - "05-01"  # DocumentMetadata schema update, EnricherConfig, langdetect install
  provides:
    - "MetadataEnricher concrete adapter"
    - "build_metadata_enricher factory function"
  affects:
    - "service.py injection point (MetadataEnricherPort)"
    - "tests/adapters/enricher/"

tech_stack:
  added:
    - "langdetect.detect_langs() API for ISO 639-1 language detection"
  patterns:
    - "Factory function pattern (D-23): build_metadata_enricher(config: EnricherConfig) -> MetadataEnricher"
    - "Structural typing (D-14): MetadataEnricherPort satisfied without inheritance"
    - "Exception wrapping (D-16): langdetect exceptions never propagate outside _detect_language"
    - "Module-level constants: LANGUAGE_CONFIDENCE_THRESHOLD, DOC_TYPE_KEYWORDS, _FORM_INDICATORS"

key_files:
  created:
    - "src/selection_maid/adapters/enricher/default.py"
  modified:
    - "pyproject.toml"  # added [[tool.mypy.overrides]] for langdetect (no py.typed marker)

decisions:
  - "D-60/61/62: langdetect.detect_langs() on full content, score >= 0.8 threshold, exceptions → 'und'"
  - "D-63/64/65: Keyword heuristics priority: legal > presentation > form > report > other"
  - "D-66: title = first H1 via ^# (.+) regex; empty string if absent"
  - "D-67: author = '' always (no XMP/EXIF access at this layer)"
  - "D-69/70: doc_id = uuid.uuid4(), source_filename = raw.filename"
  - "D-72/73: build_metadata_enricher(config: EnricherConfig) factory; EnricherConfig empty in v1"

metrics:
  duration: "~15 minutes"
  completed: "2026-05-24"
  tasks_completed: 3
  files_created: 1
  files_modified: 1
---

# Phase 5 Plan 02: MetadataEnricher Adapter Summary

MetadataEnricher concrete adapter with langdetect language detection and multilingual keyword-based doc_type inference, satisfying MetadataEnricherPort via structural typing.

## What Was Built

The `MetadataEnricher` class at `src/selection_maid/adapters/enricher/default.py` provides a complete implementation of `MetadataEnricherPort`. It receives a `RawDocument` and `list[DocumentChunk]` and returns a `DocumentMetadata` with all 9 META-01 fields populated.

### Key Components

**Language Detection (_detect_language):**
- Uses `langdetect.detect_langs()` on the full Markdown content (D-60)
- Only accepts top candidate if score >= `LANGUAGE_CONFIDENCE_THRESHOLD` (0.8) (D-61)
- All exceptions silently caught → returns "und" (D-62)
- Returns ISO 639-1 code ("en", "pt", "es") or "und" for undetermined

**Doc Type Inference (_infer_doc_type):**
- Extracts heading lines (lines starting with `#`) and checks lowercased text against DOC_TYPE_KEYWORDS
- Priority: legal → presentation → form → report → other (D-63, D-64, D-65)
- `legal` / `presentation`: matched against headings only (reduces false positives)
- `form`: scanned against full content (`_____`, `[ ]`, `Name:`, `Nome:`, `Nombre:`)
- `report`: structural heuristic — ≥2 table rows AND ≥2 numbered sections
- "article" is in the closed vocabulary but no heuristic produces it; default is "other"

**Title Extraction (_extract_title):**
- `re.search(r'^# (.+)', content, re.MULTILINE)` finds first H1 (D-66)
- Returns stripped matched group or "" if no H1 present

**Field Mapping (enrich):**
- `doc_id = str(uuid.uuid4())` — UUID v4 per call (D-69)
- `source_filename = raw.filename` (D-70)
- `author = ""` always (D-67)
- `ingested_at = datetime.now(timezone.utc)`

**Factory:**
- `build_metadata_enricher(config: EnricherConfig) -> MetadataEnricher` (D-72)
- Config parameter reserved for v2 extensibility; no configurable params in v1 (D-73)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] Added mypy overrides for langdetect**
- **Found during:** Task 1 (mypy strict verification)
- **Issue:** `langdetect` library lacks a `py.typed` marker, causing `import-untyped` error under `mypy --strict`
- **Fix:** Added `[[tool.mypy.overrides]]` section to `pyproject.toml` with `ignore_missing_imports = true` for `langdetect` and `langdetect.*` modules. This is the standard approach for third-party libraries without type stubs.
- **Files modified:** `pyproject.toml`
- **Commit:** 73c11e9

**2. [Implementation Note] All three plan tasks implemented in a single file creation**
- The plan described three tasks building up the same file incrementally. Since the complete design was clear from the context, the file was written in full and committed as Task 1 (skeleton + language detection), with Task 2 (doc_type + title) and Task 3 (enrich + factory) already present. The pyproject.toml fix was committed as the Task 2 commit. Task 3 required no additional file changes after Task 1's commit already contained the factory and enrich() body.

## Commits

| Task | Commit  | Message |
|------|---------|---------|
| 1    | 3a162d1 | feat(05-02): add MetadataEnricher skeleton and language detection |
| 2    | 73c11e9 | feat(05-02): add doc_type inference and title extraction to MetadataEnricher |

## Verification Results

- `python -c "from selection_maid.adapters.enricher.default import MetadataEnricher"` — PASS
- `_detect_language("...English text...")` → `"en"` — PASS
- `_detect_language("")` → `"und"` — PASS  
- `_extract_title("# My Title\n...")` → `"My Title"` — PASS
- `_extract_title("no heading")` → `""` — PASS
- `_infer_doc_type("# Contrato...\nCláusula...")` → `"legal"` — PASS
- `_infer_doc_type("Name: _____")` → `"form"` — PASS
- `_infer_doc_type("# Normal Doc\n...")` → `"other"` — PASS
- `enrich(raw, chunks)` with report structure → `doc_type="report"` — PASS
- `mypy src/selection_maid/ --strict` — 17 files, 0 errors — PASS
- `pytest tests/ -x -q` — 116 passed — PASS

## Known Stubs

None. All fields produce real values on every `enrich()` call.

## Self-Check: PASSED
