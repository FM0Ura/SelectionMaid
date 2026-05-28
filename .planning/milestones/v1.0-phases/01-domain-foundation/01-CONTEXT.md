# Phase 1: Domain Foundation - Context

**Gathered:** 2026-05-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 delivers the pure domain core: frozen dataclasses (models), `typing.Protocol` port contracts, `ExtractionService` with constructor injection, and the domain error taxonomy. **Zero external library dependencies.** No Docling, no FastAPI, no Pydantic. Every subsequent adapter (Phases 2–6) implements against the contracts defined here.

</domain>

<decisions>
## Implementation Decisions

### Package Structure

- **D-01:** Domain models and port contracts live in `src/selection_maid/domain/` — `models.py` for dataclasses, `ports.py` for Protocols. All domain types are importable from this subpackage.
- **D-02:** `ExtractionService` lives at `src/selection_maid/service.py` (not inside `domain/`). Error taxonomy at `src/selection_maid/errors.py`. Both are at the package root, not inside `domain/`.
- **D-03:** Adapter subpackages at `src/selection_maid/adapters/{extractor,filter,chunker,enricher,http}/` — one subpackage per adapter. Phase 1 creates the directory structure empty; adapters are implemented in Phases 2–6.
- **D-04:** `tests/` mirrors `src/` structure: `tests/domain/`, `tests/adapters/extractor/`, `tests/adapters/filter/`, etc. Shared stub adapters live in `tests/stubs/` (reusable across all phases — do NOT inline stubs in individual test files).

### Domain Model Contracts

- **D-05:** `RawInput(path: Path, filename: str, mime_type: str)` — frozen dataclass. This is the entry object passed to `ExtractorPort.extract()`. `mime_type` is detected and validated by the HTTP adapter (Phase 6) from the uploaded file's magic bytes; the domain never detects it.
- **D-06:** `RawDocument(content: str, filename: str, page_count: int, format: str)` — frozen dataclass. `content` is a single Markdown string blob (no per-page structure). `page_count` is 0 when unknown. `format` is a lowercase string ("pdf", "docx", "html").
- **D-07:** `ExtractionResult(metadata: DocumentMetadata, chunks: tuple[DocumentChunk, ...])` — frozen dataclass. No `warnings` field in v1 (deferred to v2).
- **D-08:** All collections in frozen dataclasses use `tuple[..., ...]` (not `list`) for immutability. `DocumentChunk` fields defined by REQUIREMENTS.md CHUNK-03.

### Port Signatures (typing.Protocol)

- **D-09:** `ExtractorPort.extract(self, document: RawInput) -> RawDocument`
- **D-10:** `FilterPort.filter(self, document: RawDocument) -> RawDocument` — same type in and out; filter returns a cleaned copy.
- **D-11:** `ChunkerPort.chunk(self, content: str) -> list[DocumentChunk]` — receives the Markdown string from the filtered `RawDocument.content`.
- **D-12:** `MetadataEnricherPort.enrich(self, raw: RawDocument, chunks: list[DocumentChunk]) -> DocumentMetadata` — receives both the original raw document and the final chunks list.
- **D-13:** All port methods are **sync** (`def`, not `async def`). The async boundary is managed by the HTTP adapter in Phase 6 via `run_in_threadpool`. Domain stays pure Python with no asyncio.
- **D-14:** Protocols do NOT use `@runtime_checkable`. Type checking is mypy-only; `isinstance(adapter, ExtractorPort)` is not used in tests or runtime code.

### ExtractionService Pipeline

- **D-15:** `ExtractionService.process(self, input: RawInput) -> ExtractionResult` — single sync entry point. Pipeline: `extract → filter → chunk → enrich → return ExtractionResult`.
- **D-16:** `ExtractionService` wraps port exceptions at each port boundary. Pattern:
  ```python
  try:
      raw = self._extractor.extract(input)
  except SelectionMaidError:
      raise  # already domain error, propagate unchanged
  except Exception as e:
      raise ExtractionError(f"Extraction failed: {e}", cause=e) from e
  ```
  Same pattern applies at every port call. The HTTP adapter only ever sees `SelectionMaidError` subclasses.

### Error Taxonomy

- **D-17:** `SelectionMaidError(Exception)` is the base. Fields: `code: str` (class attribute — fixed per subclass), `message: str`, `cause: Exception | None = None`. Structured to support machine-readable error codes.
- **D-18:** Error hierarchy with fixed codes per class:
  - `ExtractionError` — code `"EXT-001"`
  - `UnsupportedFormatError` — code `"EXT-002"` (carries `format: str` field)
  - `FilterError` — code `"FILT-001"`
  - `ChunkingError` — code `"CHUNK-001"`
  - `EnrichmentError` — code `"ENRICH-001"`
- **D-19:** HTTP status mapping lives in the HTTP adapter (Phase 6) as a `ERROR_CODE_TO_HTTP` dict. Domain errors carry no HTTP status — no coupling between domain and HTTP.
- **D-20:** `ExtractionTimeoutError` (code `"EXT-003"`) is also part of this taxonomy — ROADMAP.md Phase 2 Success Criteria #7 mentions it. Define the class now; DoclingAdapter raises it in Phase 2.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 1 goal, success criteria (5 items), and pre-defined plans (01-01 through 01-05). Plans are already defined — planner follows them.
- `.planning/REQUIREMENTS.md` — ARCH-01 through ARCH-07 (all assigned to Phase 1). CHUNK-03 defines `DocumentChunk` required fields. META-01 defines `DocumentMetadata` required fields.

### Tech Stack Constraints
- `CLAUDE.md` — `## Technology Stack` and `## Constraints` sections. Python 3.13+, no Poetry/Rye, uv for dependency management, ruff + mypy strict.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project. Only `pyproject.toml`, `CLAUDE.md`, and `README.md` exist. No `src/` directory yet.

### Established Patterns
- `pyproject.toml` already has Python 3.13+ pinned via uv. The planner should check existing `[tool.mypy]`, `[tool.ruff]`, and `[tool.pytest.ini_options]` sections before adding new config — may already be partially set up.

### Integration Points
- Phase 1 creates the directory scaffold that Phases 2–6 will populate. The `adapters/` subpackage structure defined here (D-03) is the integration point for all future adapters.

</code_context>

<specifics>
## Specific Ideas

- `RawInput` was explicitly chosen over simpler `(path: Path, filename: str)` positional params to allow the value object to evolve (e.g., adding `size_bytes` in v2) without changing port signatures.
- `ExtractionResult.chunks` uses `tuple` specifically to match the frozen-domain design — the caller cannot accidentally mutate the returned chunks.
- `ExtractionTimeoutError` (D-20) should be defined in Phase 1 even though it's only raised in Phase 2 — it's a domain error that belongs in `errors.py`, not in the Docling adapter.

</specifics>

<deferred>
## Deferred Ideas

- **`warnings: tuple[str, ...]` in ExtractionResult** — mentioned during discussion, deferred to v2 requirements. Relevant when OCR quality reporting becomes needed.
- **`@runtime_checkable` on Protocols** — not used in v1. If runtime `isinstance` checks become necessary in future tooling, revisit.
- **Async ports** — sync-only in v1. If a future adapter is natively async (e.g., a remote extraction API), the port signatures would need rethinking. Deferred — out of v1 scope.

</deferred>

---

*Phase: 1-Domain Foundation*
*Context gathered: 2026-05-23*
