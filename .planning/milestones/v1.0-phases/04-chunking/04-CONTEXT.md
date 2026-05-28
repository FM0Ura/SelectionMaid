# Phase 4: Chunking - Context

**Gathered:** 2026-05-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 entrega `MarkdownChunker` — a implementação concreta de `ChunkerPort` que recebe o `RawDocument.content` (string Markdown filtrada) e retorna `list[DocumentChunk]` com todos os campos obrigatórios do CHUNK-03 preenchidos. O chunker implementa duas estratégias: heading-based split (primária, quando o documento tem H1/H2) e fixed-size fallback com tiktoken (quando não há headings).

A fase também estende o módulo `selection_maid.config` com uma seção `[chunker]` no `config.toml` para parâmetros configuráveis.

**Não inclui:** enriquecimento de metadados (Phase 5), interface HTTP (Phase 6). O port `ChunkerPort` já está definido e não muda.

</domain>

<decisions>
## Implementation Decisions

### Heading Split Strategy

- **D-45:** Estratégia primária de chunking: split nos headings H1 (`#`) e H2 (`##`). Headings H3 e abaixo não disparam split — são tratados como conteúdo da seção.
- **D-46:** Conteúdo que aparece antes do primeiro H1/H2 (pré-heading text) é preservado como um chunk separado com `section_title = ""`. Não é descartado.
- **D-47:** Seções grandes (quando o conteúdo entre dois headings excede `max_section_words` configurável) são subdivididas por boundary de parágrafo (linha em branco). Parágrafos são acumulados até atingir o limite; nunca quebra dentro de um parágrafo.
- **D-48:** O limite de subdivisão de seções tem o mesmo default que `max_tokens` do fallback fixed-size (512 tokens equivalente em palavras), mas pode ser configurado separadamente via `config.toml`.

### Fixed-Size Fallback

- **D-49:** Fallback ativado quando o documento não contém nenhum heading H1 ou H2. Aplica chunking por token budget usando tiktoken.
- **D-50:** Tokenizer: `tiktoken` com encoding `cl100k_base` (GPT-4 / text-embedding-ada-002). Encoding não é configurável no v1 — hardcoded como constante de módulo.
- **D-51:** `max_tokens` default: 512. Configurável via `config.toml` na seção `[chunker]` com chave `max_tokens`.
- **D-52:** O fallback também respeita boundary de parágrafo: acumula parágrafos até atingir `max_tokens`. Se adicionar o próximo parágrafo ultrapassar, fecha o chunk atual. Nunca corta dentro de um parágrafo.

### Campos de Metadados por Chunk

- **D-53:** `page_start` e `page_end` são sempre `0` para todos os chunks. O `ChunkerPort` recebe apenas uma string Markdown — sem informação de página disponível. Documentado explicitamente. Phase 7 pode melhorar com marcadores de página no Markdown se necessário.
- **D-54:** `chunk_id` é UUID v4 aleatório gerado via `uuid.uuid4()`. Globalmente único, sem colisões entre chamadas ou documentos diferentes.
- **D-55:** `word_count` é contagem de palavras do `chunk.content` via `len(content.split())`.
- **D-56:** `section_title` recebe o texto do heading que inicia a seção (ex: "Introdução"), sem o(s) `#`. Para o chunk pré-heading e para o fallback fixed-size, `section_title = ""`.

### Configuração

- **D-57:** `MarkdownChunker` recebe seus parâmetros via injeção de construtor: `MarkdownChunker(max_tokens: int = 512)`. A factory `build_markdown_chunker(config: ChunkerConfig) -> MarkdownChunker` segue o padrão D-23.
- **D-58:** O módulo `selection_maid.config` é estendido com `ChunkerConfig` dataclass e a seção `[chunker]` no `GlobalConfig`. Chave: `max_tokens`. O `config.toml` já usado pelo HeuristicFilter ganha uma nova seção.

### Estrutura do Arquivo

- **D-59:** `MarkdownChunker` vive em `src/selection_maid/adapters/chunker/markdown.py` — mesmo padrão de `adapters/filter/heuristic.py` e `adapters/extractor/docling.py`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 4 goal, success criteria (4 itens: CHUNK-01/02/03 + consistência de chunk_index), e planos pré-definidos (04-01, 04-02, 04-03).
- `.planning/REQUIREMENTS.md` — CHUNK-01 (heading boundaries como critério primário), CHUNK-02 (fallback fixed-size sem headings), CHUNK-03 (campos obrigatórios por chunk: chunk_id, page_start, page_end, section_title, chunk_index, total_chunks, word_count).

### Decisões herdadas das fases anteriores
- `.planning/phases/01-domain-foundation/01-CONTEXT.md` — D-11 (ChunkerPort.chunk signature), D-16 (exception wrapping pattern), D-18 (ChunkingError code "CHUNK-001").
- `.planning/phases/02-docling-extraction-adapter/02-CONTEXT.md` — D-03/D-04 (directory structure), D-23 (factory function pattern `build_*()`).
- `.planning/phases/03-content-filtering/03-CONTEXT.md` — D-38/D-39/D-40 (config.toml pattern, GlobalConfig, injeção de construtor com defaults). ChunkerConfig segue o mesmo padrão que FilterConfig.

### Domain Contracts (código existente)
- `src/selection_maid/domain/ports.py` — `ChunkerPort.chunk(self, content: str) -> list[DocumentChunk]` — assinatura locked. MarkdownChunker deve satisfazer este Protocol sem herança.
- `src/selection_maid/domain/models.py` — `DocumentChunk` (chunk_id, content, page_start, page_end, section_title, chunk_index, total_chunks, word_count) — campos exatos.
- `src/selection_maid/errors.py` — `ChunkingError` já definida — MarkdownChunker lança em falhas internas.
- `src/selection_maid/config.py` — `GlobalConfig` e padrão `FilterConfig` — `ChunkerConfig` segue o mesmo padrão; estender `GlobalConfig` com `chunker: ChunkerConfig`.

### Tech Stack
- `CLAUDE.md` §Technology Stack e §Constraints — Python 3.13+, uv, mypy strict, ruff. tiktoken deve ser adicionado via `uv add tiktoken`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/selection_maid/errors.py` — `ChunkingError` pronta para uso. MarkdownChunker importa e lança diretamente.
- `src/selection_maid/config.py` — `GlobalConfig`, `FilterConfig` e `get_config()` já existem. Estender com `ChunkerConfig` e campo `chunker: ChunkerConfig` — sem reescrever o módulo.
- `tests/stubs/adapters.py` — `StubChunker` (passthrough) existe para uso em testes de outras fases. MarkdownChunker é a implementação real.

### Established Patterns
- **Injeção de construtor:** `HeuristicFilter.__init__(self, min_repeat, max_line_len)` → `MarkdownChunker.__init__(self, max_tokens)` segue o mesmo padrão.
- **Factory function D-23:** `build_heuristic_filter(config)` → `build_markdown_chunker(config: ChunkerConfig) -> MarkdownChunker`.
- **Exception wrapping D-16:** `try/except` em cada boundary. MarkdownChunker aplica internamente: exceções inesperadas capturadas e relançadas como `ChunkingError`.
- **Config pattern D-38:** `ChunkerConfig(max_tokens: int = 512)` dataclass com defaults hardcoded; `GlobalConfig` ganha `chunker: ChunkerConfig = field(default_factory=ChunkerConfig)`.

### Integration Points
- `src/selection_maid/adapters/chunker/__init__.py` — docstring de subpacote existe. `MarkdownChunker` vai em `adapters/chunker/markdown.py`.
- `tests/adapters/chunker/` — diretório presumivelmente vazio. Testes vão em `tests/adapters/chunker/test_markdown_chunker.py`.
- `src/selection_maid/service.py` — `ExtractionService` já injeta `ChunkerPort` e chama `self._chunker.chunk(filtered.content)` — nenhuma mudança necessária.

</code_context>

<specifics>
## Specific Ideas

- Para heading split, a detecção de H1/H2 deve usar regex `^#{1,2}\s+(.+)` aplicado linha a linha (não `###` ou mais). O texto capturado no grupo 1 é o `section_title`.
- Para o fallback fixed-size com tiktoken, inicializar o encoder uma única vez no `__init__` do MarkdownChunker via `tiktoken.get_encoding("cl100k_base")` — não reconstruir a cada chamada de `chunk()`.
- A ordem correta para montar `total_chunks` e `chunk_index`: primeiro acumular todos os chunks em uma lista local, depois atribuir `total_chunks = len(lista)` e `chunk_index = i` em uma segunda passagem — ou usar enumerate com total calculado antes.
- `section_title` para subdivisões de seção grande: mantém o título do heading pai (ex: se "Introdução" é subdividida em 3 chunks, todos têm `section_title = "Introdução"`).

</specifics>

<deferred>
## Deferred Ideas

- **Encoding configurável** — `cl100k_base` como default, overridable via `config.toml`. Descartado para v1 (um encoding é suficiente). Candidato para v2 se outros modelos forem adicionados ao pipeline RAG.
- **Chunk overlap** — Overlap de N tokens entre chunks consecutivos para melhor retrieval de contexto. Mencionado como padrão comum em RAG, mas não incluído no v1. Candidato para CHUNK-V2-02.
- **Score de confiança por chunk** — Relevante especialmente para OCR. Já em REQUIREMENTS.md como CHUNK-V2-03.

</deferred>

---

*Phase: 4-Chunking*
*Context gathered: 2026-05-24*
