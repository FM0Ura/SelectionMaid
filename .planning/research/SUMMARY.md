# Research Summary: SelectionMaid

**Domain:** Python document extraction and normalization service for RAG ingestion pipelines
**Researched:** 2026-05-23
**Confidence:** HIGH

---

## Executive Summary

SelectionMaid é uma API HTTP headless que aceita uploads de documentos (PDF, DOCX, HTML, imagens) e retorna chunks Markdown normalizados com metadados ricos prontos para o estágio de embedding de um pipeline RAG. O padrão recomendado é arquitetura hexagonal (ports & adapters): o motor de extração (Docling) fica atrás de um protocolo estável, podendo ser trocado sem tocar na lógica de domínio.

Stack: Python 3.13 + Docling 2.95+ + FastAPI + Pydantic v2 + uv. O `HybridChunker` do Docling é a primitiva de chunking correta — ciente de estrutura e tokenização, ao contrário do `RecursiveCharacterTextSplitter` do LangChain que destrói hierarquia.

Os dois riscos mais graves são **memória** (Docling acumula 10–13GB RSS em conversões repetidas sem liberar) e **bloqueio de event loop** (extração é CPU-bound e trava o FastAPI se não for encapsulada em `run_in_threadpool`).

---

## Stack Recomendado

| Tecnologia | Versão | Papel |
|------------|--------|-------|
| Python | 3.13+ | Constraint do projeto |
| Docling | >=2.95 | Extração — melhor preservação estrutural open-source |
| FastAPI | >=0.115 | Adaptador HTTP de entrada |
| Pydantic v2 | latest | Schemas de resposta e validação |
| uv | latest | Gerenciamento de dependências (substitui pip/Poetry) |
| ruff + mypy | latest | Lint, formato, tipagem estrita |
| pytest + pytest-asyncio + httpx | latest | Testes |

**Notas críticas:**
- Instalar torch CPU-only: `--extra-index-url https://download.pytorch.org/whl/cpu` (evita ~2GB do CUDA default)
- Docker: pre-warm do cache de modelos na build time com uma conversão dummy
- `DocumentConverter` deve ser singleton via `lifespan` event — nunca instanciar por request

---

## Features: Table Stakes (v1)

- Ingestão de PDF, DOCX, HTML e imagens (OCR) via `POST /ingest` multipart
- Saída Markdown com hierarquia de headings, tabelas e listas preservadas
- Filtragem de ruído: headers/footers repetidos e linhas de número de página
- Chunking fixo (chunk_size configurável) e baseado em seções (default quando headings existem)
- Schema `DocumentChunk`: `chunk_id`, `doc_id`, `text`, `chunk_index`, `total_chunks`, `page_start`, `page_end`, `section_title`, `source_filename`, `word_count`, `char_count`
- Schema `DocumentMetadata`: `doc_id`, `source_filename`, `title`, `author`, `language` (ISO 639-1), `doc_type`, `page_count`, `chunk_count`, `ingested_at`
- `GET /health` com RSS do processo

**Anti-features confirmados (nunca construir neste serviço):**
geração de embeddings, inserção em vector DB, fila assíncrona (Celery/RQ), autenticação, deduplicação

---

## Arquitetura: Hexagonal / Ports & Adapters

**Regra de dependência:** nada no domínio ou aplicação conhece adaptadores.

**Componentes:**

| Componente | Camada | Responsabilidade |
|------------|--------|------------------|
| `domain/models.py` | Domínio | `RawDocument`, `DocumentChunk`, `DocumentMetadata`, `ExtractionResult` — dataclasses frozen |
| `domain/ports.py` | Domínio | `ExtractorPort`, `FilterPort`, `ChunkerPort`, `MetadataEnricherPort` — `typing.Protocol` |
| `ExtractionService` | Aplicação | Orquestra extract → filter → chunk → enrich via injeção de ports |
| `DoclingAdapter` | Adaptador | Encapsula `DocumentConverter`; nenhum tipo Docling vaza para fora |
| `HeuristicFilter` | Adaptador | Remove headers/footers/número de páginas via regex + frequência |
| `MarkdownChunker` | Adaptador | Split em heading boundaries com fallback fixed-size; token budget via tiktoken |
| `MetadataEnricher` | Adaptador | Detecção de idioma (langdetect), inferência de doc_type, confiança anotada |
| `router.py` | Adaptador HTTP | `build_router(service)` factory; `run_in_threadpool`; Pydantic schemas |
| `main.py` | Raiz de composição | Único ponto que importa todas as camadas e instancia adaptadores |

**Ordem de construção obrigatória:**
`models.py` → `ports.py` → `extraction_service.py` → adaptadores (qualquer ordem) → `schemas.py` → `router.py` → `main.py`

---

## Armadilhas Críticas

| # | Armadilha | Prevenção |
|---|-----------|-----------|
| 1 | **Memory leak Docling** — acúmulo de 10–13GB RSS em conversões repetidas | Refresh do converter a cada N conversões; desabilitar pipeline features não usados; design do ExtractorPort permite isolamento em subprocess sem alterar service |
| 2 | **OCR lento** — 30–80x mais devagar em PDFs image-heavy; pode travar worker indefinidamente | Timeout hard de 120s no adaptador desde o início |
| 3 | **Tipos Docling vazando no domínio** — `DoclingDocument`, `ConversionResult` no service | Se `from docling` aparece fora de `adapters/extractor/`, é violação de boundary |
| 4 | **Ports anêmicos** moldados pela API do Docling | Assinaturas de ports usam apenas tipos de domínio; config da lib fica no construtor do adaptador |
| 5 | **Bloqueio do event loop** — Docling é CPU-bound, trava async FastAPI | `run_in_threadpool()` no adaptador HTTP; verificar com teste de carga concorrente |
| 6 | **Chunks sem metadados do documento** | `Chunk` com campos obrigatórios (não-Optional): `source_id`, `page_range`, `section_heading`, `chunk_index` |
| 7 | **Sem timeout de extração** | Timeout de 120s hard no adaptador desde a primeira implementação |
| 8 | **Apenas fixtures sintéticas** | Fixtures reais: PDF digital, PDF scanenado, DOCX com tabelas, HTML, PDF protegido por senha, PDF vazio, PDF corrompido, script não-Latino |

---

## Roadmap Sugerido (7 fases)

| # | Fase | Entregável Chave | Research? |
|---|------|-------------------|-----------|
| 1 | Arquitetura Foundation | `models.py`, `ports.py`, `ExtractionService` com stubs, taxonomia de erros | Não |
| 2 | DoclingAdapter (Extração) | `DoclingAdapter`, singleton lifespan, timeout, CPU-only, testes com docs reais | **Sim** |
| 3 | Content Filtering | `HeuristicFilter`, regex + frequência, fixtures com documentos ruidosos | Não |
| 4 | Chunking | `MarkdownChunker`, section-based default, token budget, configurável | **Sim** |
| 5 | Metadata Enrichment | `MetadataEnricher`, langdetect, doc_type com confiança | Não |
| 6 | HTTP API Layer | Router factory, `run_in_threadpool`, validação de arquivo, segurança | Não |
| 7 | Integration Hardening | Real-document fixtures, memory regression test, concurrency test | Não |

**Research flags:** Fase 2 (padrões de memória + pipeline options do Docling), Fase 4 (HybridChunker token budget behavior)

---

## Lacunas e Questões em Aberto

- **Bug heading H2 (issue #1023):** `export_to_markdown()` achata todos os headings para H2. Aceitar output flat no v1; `ExporterPort` boundary permite fix drop-in quando upstream corrigir.
- **Intervalo de refresh do converter:** Determinar empiricamente durante Phase 2 profiling RSS com docs reais.
- **langdetect vs lingua-py:** Começar com langdetect; reavaliar na Fase 5 se precisão for problema.
- **Chunk size default:** 512 tokens é calibrado para `text-embedding-3-small`. Expor `chunk_size` como parâmetro de request desde o v1 para evitar defaults hardcoded por modelo.

---

*Síntese concluída: 2026-05-23*
*Pronto para roadmap: sim*
