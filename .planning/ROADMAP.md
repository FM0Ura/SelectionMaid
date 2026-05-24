# Roadmap: SelectionMaid

## Overview

SelectionMaid é construído de dentro para fora, seguindo a regra de dependência da arquitetura hexagonal. O núcleo de domínio (modelos e ports) vem primeiro porque todos os adaptadores dependem dele. Em seguida, o adaptador de maior risco (Docling) é integrado e validado com documentos reais. Cada adaptador subsequente (filtro, chunker, enricher) é plugado no serviço sem tocar no domínio. A camada HTTP chega por último, quando o serviço já é funcional. A fase final endurece o sistema com fixtures reais, testes de regressão de memória e concorrência.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Domain Foundation** - Modelos de domínio, ports (Protocols) e ExtractionService com stubs (completed 2026-05-23)
- [x] **Phase 2: Docling Extraction Adapter** - DoclingAdapter com singleton lifespan, timeout, CPU-only, testes com docs reais (completed 2026-05-24)
- [x] **Phase 3: Content Filtering** - HeuristicFilter para headers/footers, números de página e whitespace excessivo (completed 2026-05-24)
- [x] **Phase 4: Chunking** - MarkdownChunker com split por heading e fallback fixed-size com token budget (completed 2026-05-24)
- [x] **Phase 5: Metadata Enrichment** - MetadataEnricher com detecção de idioma, inferência de doc_type e campos completos (completed 2026-05-24)
- [ ] **Phase 6: HTTP API Layer** - Router FastAPI como adaptador de entrada, validação de arquivo, run_in_threadpool
- [ ] **Phase 7: Integration Hardening** - Fixtures reais multi-formato, regressão de memória, teste de concorrência

## Phase Details

### Phase 1: Domain Foundation

**Goal**: O núcleo de domínio existe e pode ser testado sem nenhuma biblioteca externa
**Depends on**: Nothing (first phase)
**Requirements**: ARCH-01, ARCH-02, ARCH-03, ARCH-04, ARCH-06, ARCH-07
**Success Criteria** (what must be TRUE):

  1. `RawDocument`, `DocumentChunk`, `DocumentMetadata` e `ExtractionResult` são dataclasses frozen sem imports de framework ou biblioteca de terceiros
  2. `ExtractorPort`, `FilterPort`, `ChunkerPort` e `MetadataEnricherPort` são `typing.Protocol` — qualquer classe que satisfaça a assinatura implementa o port sem herança explícita
  3. `ExtractionService` recebe todos os quatro ports via injeção de construtor e executa o pipeline extract → filter → chunk → enrich com stubs in-memory sem erros
  4. `ExtractionService` não contém nenhum import de biblioteca externa (sem `docling`, `fastapi`, `pydantic`) — mypy strict passa
  5. Suite de testes unitários exercita o pipeline completo com adaptadores stub e confirma que a saída de `ExtractionResult` tem o shape correto

**Plans**: 5 plans

Plans:
**Wave 1**

- [x] 01-01: Criar estrutura de pacotes hexagonal e dataclasses de domínio frozen
- [x] 01-02: Definir os quatro Ports como typing.Protocol com assinaturas de domínio

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-03: Implementar ExtractionService com injeção de construtor e pipeline orquestrado
- [x] 01-04: Taxonomia de erros de domínio (ExtractionError, FilterError, ChunkingError, UnsupportedFormatError)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-05: Testes unitários do pipeline completo com stubs e validação de boundary

### Phase 2: Docling Extraction Adapter

**Goal**: PDFs, DOCX e HTML reais são convertidos para Markdown estruturado via DoclingAdapter sem vazar tipos Docling para fora do adaptador
**Depends on**: Phase 1
**Requirements**: EXT-01, EXT-02, EXT-03, EXT-04, EXT-05, EXT-06, EXT-07
**Success Criteria** (what must be TRUE):

  1. Um arquivo PDF com texto digital é aceito e retorna `RawDocument` com Markdown contendo headings H1/H2/H3 preservados
  2. Um arquivo DOCX com tabelas é aceito e retorna Markdown com tabelas em syntax GFM
  3. Um arquivo HTML é aceito e retorna Markdown com listas ordenadas e não-ordenadas preservadas
  4. Blocos de código identificados no documento são delimitados com backticks no Markdown retornado
  5. `DocumentConverter` é instanciado uma única vez (singleton via lifespan) — chamadas repetidas não criam novas instâncias
  6. Nenhum tipo do namespace `docling` aparece fora do módulo `adapters/extractor/` — mypy confirma boundary
  7. Conversão excede 120 segundos lança `ExtractionTimeoutError` sem travar o processo

**Plans**: 5 plans

Plans:
**Wave 1**

- [x] 02-01-PLAN.md — Install docling CPU-only, DoclingAdapter skeleton, TYPE_CHECKING guard, test infrastructure

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-02-PLAN.md — Implement extract() with ThreadPoolExecutor, RawDocument mapping; EXT-01/02/03 tests

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 02-04-PLAN.md — Timeout and domain-error-propagation unit tests; mypy boundary verification (ARCH-01)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 02-03-PLAN.md — Markdown structure tests: headings, GFM tables, lists, code blocks (EXT-04..EXT-07)

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 02-05-PLAN.md — End-to-end ExtractionService integration test; phase gate (full suite + mypy)

### Phase 3: Content Filtering

**Goal**: Ruído estrutural (headers/footers repetidos, linhas de página, whitespace excessivo) é removido do Markdown extraído antes do chunking
**Depends on**: Phase 2
**Requirements**: FILT-01, FILT-02, FILT-03
**Success Criteria** (what must be TRUE):

  1. Headers e footers que aparecem em 3 ou mais páginas consecutivas são detectados e removidos do conteúdo final
  2. Linhas isoladas que contêm apenas um número (número de página) são removidas sem afetar números inline em parágrafos
  3. Sequências de duas ou mais linhas em branco são comprimidas para exatamente uma linha em branco
  4. Conteúdo legítimo (parágrafos, headings, tabelas) não é removido pelo filtro em nenhum dos casos de teste

**Plans**: 3 plans

Plans:

**Wave 1**

- [x] 03-01-PLAN.md — Centralized configuration management via selection_maid.config and config.toml
- [x] 03-02-PLAN.md — Implement HeuristicFilter logic and rule-based unit tests (FILT-01/02/03)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-03-PLAN.md — Factory function and ExtractionService integration verification

### Phase 4: Chunking

**Goal**: Conteúdo Markdown filtrado é segmentado em chunks com metadados completos por chunk usando heading boundaries como critério primário
**Depends on**: Phase 3
**Requirements**: CHUNK-01, CHUNK-02, CHUNK-03
**Success Criteria** (what must be TRUE):

  1. Documento com headings H2 é segmentado em chunks onde cada chunk começa em um boundary de heading e contém o conteúdo da seção correspondente
  2. Documento sem headings é segmentado por tamanho fixo (token budget) sem quebrar palavras
  3. Cada chunk retornado contém todos os campos obrigatórios: `chunk_id`, `page_start`, `page_end`, `section_title`, `chunk_index`, `total_chunks`, `word_count`
  4. `chunk_index` e `total_chunks` são consistentes — `chunk_index` vai de 0 a `total_chunks - 1` e cobre todos os chunks

**Plans**: 3 plans

Plans:

**Wave 1**

- [x] 04-01-PLAN.md — Configuração centralizada (tiktoken) e esqueleto do MarkdownChunker

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 04-02-PLAN.md — Implementação do split por heading boundary e subdivisão de seções grandes

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 04-03-PLAN.md — Estratégia fallback fixed-size com tiktoken e integração com ExtractionService

### Phase 5: Metadata Enrichment

**Goal**: Cada documento processado retorna metadados ricos inferidos automaticamente: idioma ISO 639-1, tipo de documento categorizado, título, autor e campos de auditoria
**Depends on**: Phase 4
**Requirements**: META-01, META-02, META-03
**Success Criteria** (what must be TRUE):

  1. Resposta final contém todos os campos de `DocumentMetadata`: `doc_id`, `source_filename`, `title`, `author`, `language`, `doc_type`, `page_count`, `chunk_count`, `ingested_at`
  2. `language` retorna código ISO 639-1 correto (ex: "pt" para documento em português, "en" para inglês) — validado com três documentos em idiomas diferentes
  3. `doc_type` é um dos valores do vocabulário fechado: `article`, `report`, `presentation`, `form`, `legal`, `other` — nunca retorna valor fora do enum
  4. `ingested_at` contém timestamp ISO 8601 da ingestão (não da criação do arquivo)

**Plans**: 3 plans

Plans:

**Wave 1**

- [x] 05-01-PLAN.md — Domain model refinement (renaming/adding fields) and infrastructure setup (langdetect)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 05-02-PLAN.md — Implement MetadataEnricher with language detection and doc_type inference logic

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 05-03-PLAN.md — Verification with multilingual documents and edge case handling

### Phase 6: HTTP API Layer

**Goal**: O serviço é acessível via HTTP com endpoint de ingestão que valida uploads e retorna ExtractionResponse, e endpoint de health com RSS do processo
**Depends on**: Phase 5
**Requirements**: API-01, API-02, API-03, ARCH-05
**Success Criteria** (what must be TRUE):

  1. `POST /ingest` com um PDF válido via multipart/form-data retorna HTTP 200 com `ExtractionResponse` contendo `metadata` e lista `chunks` não-vazia
  2. `GET /health` retorna HTTP 200 com status e RSS atual do processo em MB
  3. Upload de arquivo acima do tamanho máximo retorna HTTP 413; arquivo com MIME type inválido retorna HTTP 415; magic bytes inconsistentes retornam HTTP 422
  4. O router não contém lógica de negócio — é instanciado via `build_router(service)` factory e delega toda extração ao `ExtractionService`
  5. Chamada a `POST /ingest` com documento pesado não bloqueia o event loop — confirmado via teste de concorrência com dois requests simultâneos

**Plans**: 4 plans

Plans:

- [ ] 06-01-PLAN.md — Pydantic schemas for Request/Response (API-01, API-02)
- [ ] 06-02-PLAN.md — Router factory and basic endpoints with app lifespan (API-01, API-02, ARCH-05)
- [ ] 06-03-PLAN.md — 3-layer file validation and configuration (API-03)
- [ ] 06-04-PLAN.md — run_in_threadpool integration and full API integration tests (API-01, API-02, API-03)

**UI hint**: yes

### Phase 7: Integration Hardening

**Goal**: O sistema processa documentos reais de múltiplos formatos sem regressão de memória, sem falhas silenciosas e com comportamento previsível sob concorrência
**Depends on**: Phase 6
**Requirements**: (all requirements verified end-to-end)
**Success Criteria** (what must be TRUE):

  1. Pipeline completo processa um PDF digital, um DOCX com tabelas e um HTML em sequência e retorna `ExtractionResponse` válido para cada um
  2. RSS do processo após 20 conversões consecutivas não excede 2× o RSS após a primeira conversão (sem memory leak)
  3. Dois requests simultâneos a `POST /ingest` completam sem erro e sem deadlock em tempo aceitável
  4. Envio de PDF corrompido, PDF vazio e arquivo com extensão falsificada retornam erros HTTP com mensagem estruturada — o servidor não crasha

**Plans**: TBD

Plans:

- [ ] 07-01: Fixtures reais: PDF digital, DOCX com tabelas, HTML, PDF corrompido, PDF vazio
- [ ] 07-02: Teste de regressão de memória (20 conversões, verificar RSS)
- [ ] 07-03: Teste de concorrência (2 requests simultâneos, sem deadlock)
- [ ] 07-04: Teste de resiliência com arquivos inválidos e edge cases

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Domain Foundation | 5/5 | Complete | 2026-05-23 |
| 2. Docling Extraction Adapter | 5/5 | Complete   | 2026-05-24 |
| 3. Content Filtering | 3/3 | Complete | 2026-05-24 |
| 4. Chunking | 3/3 | Complete | 2026-05-24 |
| 5. Metadata Enrichment | 3/3 | Complete   | 2026-05-24 |
| 6. HTTP API Layer | 0/4 | Not started | - |
| 7. Integration Hardening | 0/4 | Not started | - |
