# Phase 1: Domain Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-23
**Phase:** 1-Domain Foundation
**Areas discussed:** Package structure, ExtractorPort input contract, Error taxonomy shape, ExtractionResult shape, Sync vs async no service

---

## Package structure

| Option | Description | Selected |
|--------|-------------|----------|
| `domain/` agrupa tudo | `src/selection_maid/domain/models.py` + `domain/ports.py` + `service.py` na raiz. Padrão DDD. | ✓ |
| `core/` para domain + ports | `src/selection_maid/core/` exporta modelos e ports numa camada única. | |
| Flat (tudo na raiz) | `models.py`, `ports.py`, `service.py` diretamente na raiz do pacote. | |

**User's choice:** `domain/` agrupa tudo
**Notes:** Standard DDD layout — separates domain from service layer clearly.

---

| Option | Description | Selected |
|--------|-------------|----------|
| `adapters/` com subpacote por adapter | Cada adaptador tem seu próprio subpacote: `adapters/extractor/`, `adapters/filter/`, etc. | ✓ |
| `adapters/` flat (sem subpacotes) | Todos os adapters num único nível: `adapters/docling_adapter.py`, etc. | |

**User's choice:** `adapters/` com subpacote por adapter
**Notes:** Isolates dependencies per adapter; Docling stays contained in `adapters/extractor/`.

---

| Option | Description | Selected |
|--------|-------------|----------|
| `tests/` espelhando `src/` | `tests/domain/`, `tests/adapters/extractor/`, `tests/adapters/filter/` etc. | ✓ |
| `tests/` flat por fase | `tests/test_phase1_domain.py`, `tests/test_phase2_extraction.py`, etc. | |

**User's choice:** `tests/` espelhando `src/`
**Notes:** Standard pytest layout; each module has its own test file at the corresponding path.

---

| Option | Description | Selected |
|--------|-------------|----------|
| `tests/stubs/` compartilhado | Stubs reutilizáveis entre todas as fases. | ✓ |
| Inline em cada arquivo de teste | Stubs definidos dentro de cada arquivo de teste. | |
| conftest.py fixtures | Stubs como fixtures pytest no conftest.py da raiz. | |

**User's choice:** `tests/stubs/` compartilhado
**Notes:** Prevents duplication across phases 2–7 when stubs are reused.

---

## ExtractorPort input contract

| Option | Description | Selected |
|--------|-------------|----------|
| `extract(path: Path) -> RawDocument` | Recebe um pathlib.Path para o arquivo temporário. | |
| `extract(content: bytes, filename: str) -> RawDocument` | Recebe os bytes brutos e o nome original. | |
| `extract(document: RawInput) -> RawDocument` | Value object de domínio com path, filename, mime_type. | ✓ |

**User's choice:** `extract(document: RawInput) -> RawDocument`
**Notes:** `RawInput` allows the value object to evolve without changing port signatures.

---

| Option | Description | Selected |
|--------|-------------|----------|
| O HTTP adapter detecta e passa | FastAPI valida via magic bytes e passa para RawInput. | ✓ |
| O DoclingAdapter detecta internamente | RawInput carrega apenas path e filename; adapter infere formato. | |

**User's choice:** O HTTP adapter detecta e passa
**Notes:** Domain never detects mime_type — HTTP adapter validates at the boundary.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Cada port opera no tipo mais adequado ao seu estágio | FilterPort(RawDocument)→RawDocument; ChunkerPort(str)→list[DocumentChunk]; MetadataEnricherPort(RawDocument, list)→DocumentMetadata | ✓ |
| Todos operam sobre ProcessingContext acumulador | Um objeto mutável passado pela pipeline. | |

**User's choice:** Cada port opera no tipo mais adequado ao seu estágio
**Notes:** Clean per-port interface; no shared mutable state in the domain.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Apenas conteúdo Markdown + metainformações básicas | `content: str, filename: str, page_count: int, format: str` | ✓ |
| Lista de páginas (`pages: list[str]`) | Markdown por página para suporte nativo no HeuristicFilter. | |

**User's choice:** Apenas conteúdo Markdown + metainformações básicas
**Notes:** No Docling-internal structure leaked; single Markdown blob is sufficient for the filter.

---

## Error taxonomy shape

| Option | Description | Selected |
|--------|-------------|----------|
| Hierarquia de exceptions puras com base comum | `SelectionMaidError(Exception)` com subclasses plain. | |
| Erros estruturados com código de máquina | Cada erro tem `code: str` além do `message`. | ✓ |

**User's choice:** Erros estruturados com código de máquina
**Notes:** Enables structured logging and HTTP status mapping via code lookup table.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Um código fixo por subclasse | `ExtractionError` sempre code `EXT-001`, class attribute. | ✓ |
| Códigos por instância (campo de dados) | `code` passado no construtor de cada instância. | |

**User's choice:** Um código fixo por subclasse
**Notes:** Simple to map; codes documented implicitly by the class hierarchy.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Tabela de mapeamento no HTTP adapter | `ERROR_CODE_TO_HTTP` dict in the router. Domain has no HTTP knowledge. | ✓ |
| O erro de domínio já carrega o HTTP status sugerido | `http_status: int` class attribute. Couples domain to HTTP. | |

**User's choice:** Tabela de mapeamento no HTTP adapter
**Notes:** Preserves hexagonal rule — domain has no dependency on HTTP.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Envolve em erros de domínio na fronteira do port | `try/except` in ExtractionService wraps all port exceptions. | ✓ |
| Deixa propagar sem wrapping | Ports responsible for raising domain errors directly. | |

**User's choice:** Envolve em erros de domínio na fronteira do port
**Notes:** HTTP adapter only ever sees `SelectionMaidError` subclasses — implementation details never leak.

---

## ExtractionResult shape

| Option | Description | Selected |
|--------|-------------|----------|
| Apenas `metadata` e `chunks` | `ExtractionResult(metadata: DocumentMetadata, chunks: tuple[DocumentChunk, ...])` | ✓ |
| Com `warnings: tuple[str, ...]` | Optional warnings field for OCR quality etc. | |

**User's choice:** Apenas `metadata` e `chunks`
**Notes:** Warnings deferred to v2 requirements.

---

| Option | Description | Selected |
|--------|-------------|----------|
| `tuple[DocumentChunk, ...]` | Immutable — consistent with frozen-domain design. | ✓ |
| `list[DocumentChunk]` | Mutable but more pythonic for collections. | |

**User's choice:** `tuple[DocumentChunk, ...]`
**Notes:** Prevents accidental mutation of returned chunks by the caller.

---

## Sync vs async no service

| Option | Description | Selected |
|--------|-------------|----------|
| Sync `process(input: RawInput) -> ExtractionResult` | HTTP adapter uses `run_in_threadpool`. Domain stays pure. | ✓ |
| Async `async def process(...)` | Ports become async Protocols; Docling needs `asyncio.to_thread`. | |

**User's choice:** Sync `process(input: RawInput) -> ExtractionResult`
**Notes:** Docling is CPU-bound sync; async handled at the HTTP boundary in Phase 6.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Sim, todos sync | All port methods are `def`, not `async def`. | ✓ |
| Ports async, adapters convertem internamente | Protocols declare `async def`; adapters use `asyncio.to_thread`. | |

**User's choice:** Sim, todos sync
**Notes:** Consistent with sync service; async is a Phase 6 HTTP-layer concern only.

---

## Claude's Discretion

- None — all areas had explicit user selections.

## Deferred Ideas

- `warnings: tuple[str, ...]` in ExtractionResult — deferred to v2
- `@runtime_checkable` on Protocols — not used in v1; revisit if runtime isinstance checks become needed
- Async ports — deferred; relevant only if a future adapter is natively async (e.g., remote extraction API)
