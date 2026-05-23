# Requirements: SelectionMaid

**Defined:** 2026-05-23
**Core Value:** Documentos entram em qualquer formato suportado, chunks Markdown normalizados saem via interface estável — independente da biblioteca de extração ou protocolo de entrada usados.

## v1 Requirements

### Extraction

- [ ] **EXT-01**: Sistema aceita arquivo PDF com texto nativo (digital) para extração de conteúdo
- [ ] **EXT-02**: Sistema aceita arquivo DOCX/Word para extração de conteúdo
- [ ] **EXT-03**: Sistema aceita arquivo HTML para extração de conteúdo
- [ ] **EXT-04**: Conteúdo extraído é convertido para Markdown com hierarquia de headings preservada (H1/H2/H3+)
- [ ] **EXT-05**: Tabelas do documento são convertidas para Markdown table syntax com estrutura preservada
- [ ] **EXT-06**: Listas ordenadas e não-ordenadas são preservadas na saída Markdown
- [ ] **EXT-07**: Blocos de código identificados no documento são delimitados com backticks no Markdown

### Filtering

- [ ] **FILT-01**: Headers e footers que se repetem em múltiplas páginas são detectados e removidos do conteúdo
- [ ] **FILT-02**: Linhas isoladas que contêm apenas número de página são removidas do conteúdo
- [ ] **FILT-03**: Sequências excessivas de linhas em branco são comprimidas para no máximo uma linha em branco

### Chunking

- [ ] **CHUNK-01**: Conteúdo Markdown é segmentado em chunks usando boundaries de heading como critério primário de split
- [ ] **CHUNK-02**: Quando não há headings no documento, chunking aplica estratégia de tamanho fixo como fallback
- [ ] **CHUNK-03**: Cada chunk retornado contém: `chunk_id`, `page_start`, `page_end`, `section_title`, `chunk_index`, `total_chunks`, `word_count`

### Metadata

- [ ] **META-01**: API retorna metadados do documento: título, autor, idioma detectado, tipo de documento, número de páginas, contagem de chunks, data de ingestão
- [ ] **META-02**: Idioma do documento é detectado automaticamente e retornado em formato ISO 639-1 (ex: "pt", "en", "es")
- [ ] **META-03**: Tipo de documento é inferido e categorizado em vocabulário fechado (article, report, presentation, form, legal, other)

### API

- [ ] **API-01**: Endpoint `POST /ingest` aceita upload de arquivo via multipart/form-data e retorna `ExtractionResponse` com metadados e lista de chunks normalizados
- [ ] **API-02**: Endpoint `GET /health` retorna status de saúde do serviço incluindo RSS do processo em memória
- [ ] **API-03**: Arquivos enviados passam por validação de tamanho máximo, MIME type e magic bytes antes de qualquer processamento

### Architecture

- [ ] **ARCH-01**: Extração é encapsulada atrás de `ExtractorPort` (`typing.Protocol`) — nenhum tipo Docling vaza para domínio ou serviço
- [ ] **ARCH-02**: Filtragem é encapsulada atrás de `FilterPort` (`typing.Protocol`) com adaptador substituível
- [ ] **ARCH-03**: Chunking é encapsulado atrás de `ChunkerPort` (`typing.Protocol`) com adaptador substituível
- [ ] **ARCH-04**: Enriquecimento de metadados é encapsulado atrás de `MetadataEnricherPort` (`typing.Protocol`) com adaptador substituível
- [ ] **ARCH-05**: FastAPI é adaptador de entrada isolado da lógica de domínio — router é instanciado via factory function, nunca contém lógica de negócio
- [ ] **ARCH-06**: `ExtractionService` recebe todos os ports via injeção de construtor e não importa nenhuma biblioteca externa
- [ ] **ARCH-07**: Modelos de domínio (`RawDocument`, `DocumentChunk`, `DocumentMetadata`, `ExtractionResult`) são dataclasses frozen sem imports de framework

## v2 Requirements

### Extended Formats

- **EXT-V2-01**: Suporte a imagens e PDFs escaneados via OCR (lento; requer configuração de timeout e aviso ao consumidor)
- **EXT-V2-02**: Suporte a PPTX (apresentações PowerPoint)
- **EXT-V2-03**: Suporte a XLSX (planilhas Excel)

### Chunking Avançado

- **CHUNK-V2-01**: Chunk size configurável por request via parâmetro `max_tokens`
- **CHUNK-V2-02**: Seleção de estratégia de chunking via parâmetro no request (section-based, fixed-size, sentence-based)
- **CHUNK-V2-03**: Score de confiança por chunk (relevante para OCR)

### Metadata Avançado

- **META-V2-01**: Campos inferidos (idioma, tipo de documento, autor, título) anotados com score de confiança e fonte da inferência
- **META-V2-02**: Extração de metadados XMP/EXIF do PDF (quando disponíveis)

### Observabilidade

- **OBS-V2-01**: Métricas de processamento: tempo de extração, número de chunks, tamanho do documento
- **OBS-V2-02**: Logging estruturado com request_id rastreável

## Out of Scope

| Feature | Motivo |
|---------|--------|
| Inserção em vector DB | Responsabilidade do sistema consumidor; SelectionMaid entrega dados, não armazena |
| Geração de embeddings | Fora do escopo de normalização; pertence ao pipeline do consumidor |
| Autenticação e autorização | Responsabilidade da infra de deploy |
| UI / dashboard | API headless; sem interface visual planejada |
| Fila assíncrona (Celery/RQ/SQS) | Volume on-demand não exige; scope creep para v1 |
| Deduplicação de documentos | Alta complexidade, baixo valor imediato |
| LLM-based chunking | Benchmark 2026 mostra underperformance vs section-based; over-engineering para v1 |
| Autenticação por documento | Detectar e rejeitar PDFs com senha — v2 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ARCH-01 | Phase 1 | Pending |
| ARCH-02 | Phase 1 | Pending |
| ARCH-03 | Phase 1 | Pending |
| ARCH-04 | Phase 1 | Pending |
| ARCH-06 | Phase 1 | Pending |
| ARCH-07 | Phase 1 | Pending |
| EXT-01 | Phase 2 | Pending |
| EXT-02 | Phase 2 | Pending |
| EXT-03 | Phase 2 | Pending |
| EXT-04 | Phase 2 | Pending |
| EXT-05 | Phase 2 | Pending |
| EXT-06 | Phase 2 | Pending |
| EXT-07 | Phase 2 | Pending |
| FILT-01 | Phase 3 | Pending |
| FILT-02 | Phase 3 | Pending |
| FILT-03 | Phase 3 | Pending |
| CHUNK-01 | Phase 4 | Pending |
| CHUNK-02 | Phase 4 | Pending |
| CHUNK-03 | Phase 4 | Pending |
| META-01 | Phase 5 | Pending |
| META-02 | Phase 5 | Pending |
| META-03 | Phase 5 | Pending |
| API-01 | Phase 6 | Pending |
| API-02 | Phase 6 | Pending |
| API-03 | Phase 6 | Pending |
| ARCH-05 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 26 total
- Mapped to phases: 26
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-23*
*Last updated: 2026-05-23 after roadmap creation*
