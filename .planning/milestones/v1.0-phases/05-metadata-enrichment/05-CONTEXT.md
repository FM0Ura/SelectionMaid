# Phase 5: Metadata Enrichment - Context

**Gathered:** 2026-05-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 5 entrega `MetadataEnricher` — a implementação concreta de `MetadataEnricherPort` que recebe `RawDocument` + `list[DocumentChunk]` e retorna `DocumentMetadata` com todos os campos META-01/02/03 preenchidos: `doc_id`, `source_filename`, `title`, `author`, `language`, `doc_type`, `page_count`, `chunk_count`, `ingested_at`.

A fase também inclui a atualização de `DocumentMetadata` em `models.py` para adicionar `doc_id` (UUID v4) e `source_filename` (str), e renomear `ingestion_date` → `ingested_at` e `document_type` → `doc_type` para alinhar com o ROADMAP.

**Não inclui:** interface HTTP (Phase 6), testes de integração multi-formato end-to-end (Phase 7). O port `MetadataEnricherPort` já está definido e não muda.

</domain>

<decisions>
## Implementation Decisions

### Detecção de Idioma (META-02)

- **D-60:** Biblioteca: `langdetect`. Detecta o idioma do `RawDocument.content` completo (Markdown filtrado) — não amostra, não chunks.
- **D-61:** API: `detect_langs()` com threshold de confiança. Só aceita o resultado se o score do idioma mais provável for >= 0.8; caso contrário retorna `"und"` (ISO 639-3 para undetermined).
- **D-62:** Fallback: qualquer exceção interna do langdetect (texto muito curto, encoding inválido, erro interno) → retorna `"und"`. Nunca propaga exceção do langdetect para fora do enricher.

### Inferência de doc_type (META-03)

- **D-63:** Abordagem: palavras-chave em headings + análise estrutural combinados. Vocabulário fechado: `article`, `report`, `presentation`, `form`, `legal`, `other`.
- **D-64:** Keywords multilinguais (PT, EN, ES) hardcoded como dict no adaptador:
  - `legal`: ["cláusula", "contrato", "artigo", "parágrafo", "clause", "contract", "article", "whereas", "cláusula", "contrato"]
  - `presentation`: ["slide", "apresentação", "presentation", "agenda", "outline", "presentación"]
  - `form`: campos de preenchimento (`_____`, `[ ]`, `Name:`, `Nome:`, `Nombre:`)
  - `report`: título + múltiplas tabelas + seções numeradas
- **D-65:** Default quando nenhuma heurística bate: `"other"`. Nunca retorna valor fora do enum.

### Campos title e author

- **D-66:** `title`: extraído do primeiro H1 do `RawDocument.content` via regex `^# (.+)` na primeira linha que case. Se não houver H1, `title = ""`.
- **D-67:** `author`: sempre `""` (string vazia). Extração de autor não é possível sem acesso a metadados XMP/PDF (que ficam atrás do ExtractorPort). Honesto sobre limitação — sem inferência heurística.

### Campos doc_id e source_filename (adição ao model)

- **D-68:** `DocumentMetadata` é atualizado em `models.py` para adicionar dois campos novos e renomear dois existentes:
  - Adicionados: `doc_id: str`, `source_filename: str`
  - Renomeados: `ingestion_date` → `ingested_at`, `document_type` → `doc_type`
- **D-69:** `doc_id` gerado com `uuid.uuid4()` no `enrich()` — mesmo padrão que `chunk_id` (D-54). UUID v4 aleatório, globalmente único.
- **D-70:** `source_filename` vem diretamente de `RawDocument.filename` — o enricher já recebe `RawDocument`, portanto tem acesso sem mudança de assinatura.

### Estrutura do Adaptador

- **D-71:** `MetadataEnricher` vive em `src/selection_maid/adapters/enricher/default.py` — mesmo padrão de `adapters/chunker/markdown.py`, `adapters/filter/heuristic.py`.
- **D-72:** Factory: `build_metadata_enricher(config: EnricherConfig) -> MetadataEnricher` — segue padrão D-23. `EnricherConfig` é dataclass com defaults hardcoded; `GlobalConfig` ganha `enricher: EnricherConfig`.
- **D-73:** Não há parâmetros configuráveis relevantes para o v1 (threshold de langdetect e keywords de doc_type são constantes de módulo). `EnricherConfig` pode ser uma dataclass vazia por ora — estrutura está lá para futuras extensões (ex: threshold configurável em v2).

### Claude's Discretion

- Ordem de prioridade das heurísticas de doc_type: verificar keywords primeiro (mais específico), depois elementos estruturais (tabelas, formulários), depois fallback para "other". Claude decide a implementação concreta da lógica de scoring/prioridade.
- Tratamento de documentos com conteúdo misto (ex: legal + tabelas): Claude decide como desempatar — pode usar a primeira regra que bate ou a mais frequente.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 5 goal, success criteria (4 itens: campos completos de DocumentMetadata, language ISO 639-1, doc_type vocabulário fechado, ingested_at timestamp). Também contém planos pré-definidos (05-01, 05-02, 05-03).
- `.planning/REQUIREMENTS.md` — META-01 (campos completos), META-02 (language ISO 639-1), META-03 (doc_type vocabulário fechado: article/report/presentation/form/legal/other).

### Domain Contracts (código existente — DEVE ser lido antes de modificar)
- `src/selection_maid/domain/models.py` — `DocumentMetadata` precisa ser atualizado nesta fase (D-68): adicionar doc_id + source_filename, renomear ingestion_date → ingested_at e document_type → doc_type. Todos os outros campos (title, author, language, doc_type, page_count, chunk_count, ingested_at) ficam.
- `src/selection_maid/domain/ports.py` — `MetadataEnricherPort.enrich(self, raw: RawDocument, chunks: list[DocumentChunk]) -> DocumentMetadata` — assinatura locked. MetadataEnricher deve satisfazer este Protocol sem herança.
- `src/selection_maid/errors.py` — verificar se `EnrichmentError` já existe; se não, criar seguindo o padrão de `ChunkingError`.
- `src/selection_maid/config.py` — `GlobalConfig` e padrão `FilterConfig`/`ChunkerConfig` — `EnricherConfig` segue o mesmo padrão; estender GlobalConfig com `enricher: EnricherConfig`.

### Decisões herdadas das fases anteriores
- `.planning/phases/01-domain-foundation/01-CONTEXT.md` — D-16 (exception wrapping pattern), D-12 (MetadataEnricherPort signature).
- `.planning/phases/02-docling-extraction-adapter/02-CONTEXT.md` — D-03/D-04 (directory structure), D-23 (factory function pattern `build_*()`).
- `.planning/phases/03-content-filtering/03-CONTEXT.md` — D-38/D-39/D-40 (config.toml pattern, GlobalConfig, injeção de construtor com defaults).
- `.planning/phases/04-chunking/04-CONTEXT.md` — D-54 (chunk_id via uuid.uuid4() — doc_id segue mesmo padrão), D-57/D-58 (padrão de factory e config).

### Tech Stack
- `CLAUDE.md` §Technology Stack — `langdetect >= 1.0.9` listado como dependência opcional para metadata enrichment. Deve ser adicionada via `uv add langdetect`.
- `CLAUDE.md` §Constraints — Python 3.13+, uv, mypy strict, ruff.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/selection_maid/errors.py` — padrão de `ChunkingError` para criar `EnrichmentError` (se não existir).
- `src/selection_maid/config.py` — `GlobalConfig`, `FilterConfig`, `ChunkerConfig` e `get_config()` — estender com `EnricherConfig` seguindo exatamente o mesmo padrão.
- `src/selection_maid/adapters/enricher/__init__.py` — subpacote já existe (docstring de placeholder).
- `tests/stubs/adapters.py` — verificar se `StubEnricher` já existe para uso em testes de outras fases.

### Established Patterns
- **Factory function D-23:** `build_heuristic_filter(config)` / `build_markdown_chunker(config)` → `build_metadata_enricher(config: EnricherConfig) -> MetadataEnricher`.
- **Exception wrapping D-16:** `try/except` em cada boundary. MetadataEnricher aplica internamente; exceções de langdetect nunca propagam para fora.
- **Config pattern D-38:** `EnricherConfig()` dataclass com defaults (pode ser vazia no v1); `GlobalConfig` ganha `enricher: EnricherConfig = field(default_factory=EnricherConfig)`.
- **Injeção de construtor:** `MetadataEnricher.__init__(self)` sem parâmetros obrigatórios no v1 (configuração pode ser adicionada depois).

### Integration Points
- `src/selection_maid/adapters/enricher/` — `MetadataEnricher` vai em `adapters/enricher/default.py`.
- `src/selection_maid/service.py` — `ExtractionService` já injeta `MetadataEnricherPort` e chama `self._enricher.enrich(raw, chunks)` — nenhuma mudança necessária no service.
- `tests/adapters/enricher/` — testes vão em `tests/adapters/enricher/test_metadata_enricher.py`.
- **Atenção:** renomear campos em `DocumentMetadata` pode exigir atualização de testes existentes que referenciam `ingestion_date` ou `document_type` por nome.

</code_context>

<specifics>
## Specific Ideas

- Para `detect_langs()`, o threshold de 0.8 é o valor de partida sugerido na discussão. O planner pode ajustar se os testes com PT/EN/ES mostrarem falsos "und".
- As keywords de `doc_type` devem ser verificadas nos headings (linhas que começam com `#`) do Markdown, não no corpo completo, para reduzir falsos positivos.
- `langdetect` deve ser inicializado uma única vez no módulo — não há estado mutável relevante, mas o carregamento do modelo é feito na primeira chamada. Documentar no adaptador.
- Ao renomear campos de `DocumentMetadata`, verificar todas as referências em `tests/` (pytest vai apontar as quebras em compile time via mypy strict).

</specifics>

<deferred>
## Deferred Ideas

- **Threshold de confiança do langdetect configurável** — `language_confidence_threshold` em `EnricherConfig`. Descartado para v1 (0.8 hardcoded é suficiente). Candidato para v2 se precisar de ajuste por domínio.
- **Extração de metadados XMP/EXIF do PDF** — Requer acesso ao `DoclingDocument` antes de ser convertido para Markdown. Exige mudança no `ExtractorPort` para expor metadados brutos — escopo grande para uma fase de enrichment. Em REQUIREMENTS.md como META-V2-02.
- **Score de confiança em campos inferidos** — language, doc_type e title anotados com score. Em REQUIREMENTS.md como META-V2-01.
- **Autor inferido via heurística** — Tentar detectar "Author:", "Por:", "By:" no início do documento. Baixa precisão, descartado para v1.

</deferred>

---

*Phase: 5-Metadata Enrichment*
*Context gathered: 2026-05-24*
