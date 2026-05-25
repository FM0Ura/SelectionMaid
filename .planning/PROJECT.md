# SelectionMaid

## What This Is

SelectionMaid é um serviço de curadoria e normalização de documentos — a "empregada" que recebe arquivos brutos (PDF, DOCX, HTML, imagens), extrai o conteúdo via Docling, limpa o ruído, enriquece metadados, segmenta em chunks e devolve Markdown estruturado pronto para ser inserido em um banco de dados vetorial. É a porta de entrada do pipeline RAG, desenhada como arquitetura hexagonal: todos os adaptadores (extrator, filtro, chunker, interface HTTP) são intercambiáveis sem tocar no núcleo de domínio.

## Current State: v1.0 Shipped (2026-05-25)

✓ **Hexagonal Stack**: Core domain, service layer, and all adapters (Docling, HeuristicFilter, MarkdownChunker, MetadataEnricher, FastAPI) are fully implemented and decoupled.
✓ **Multi-Format Extraction**: Production-ready extraction for PDF, DOCX, and HTML.
✓ **Hardened API**: 3-layer file validation, concurrent request handling, and memory-safe implementation.
✓ **Verified**: 100% test coverage (204 tests) and Nyquist compliance.

## Next Milestone: v2.0 Goals

- **Extended Formats**: OCR support for scanned PDFs and images, PPTX/XLSX support.
- **Advanced Chunking**: Configurable chunk size per request, selection of chunking strategy (section vs. fixed).
- **Observability**: Structured logging with request tracking, processing metrics (time, tokens).
- **Advanced Metadata**: Confidence scores for inferred fields, XMP/EXIF extraction.

## Core Value

Documentos entram em qualquer formato, chunks Markdown normalizados saem via uma interface estável — independente da biblioteca de extração ou do protocolo de entrada usado.

## Requirements

### Validated (v1.0)

- [x] Aceitar documentos PDF, DOCX, HTML via API HTTP
- [x] Extrair texto via Docling encapsulado em adaptador intercambiável
- [x] Filtrar ruído (cabeçalhos, rodapés, números de página)
- [x] Converter conteúdo para Markdown preservando hierarquia de seções
- [x] Enriquecer metadados (tipo de documento, idioma, título inferidos)
- [x] Segmentar o conteúdo em chunks de tamanho controlado (heading boundaries + fixed fallback)
- [x] Retornar lista de chunks com metadados em schema consistente
- [x] Interface HTTP (FastAPI) isolada como adaptador de entrada plugável
- [x] Arquitetura hexagonal: todo componente de processamento é um Port com Adapter substituível

### Active (v2.0)

- [ ] Suporte a OCR (Docling OCR) para imagens e PDFs escaneados
- [ ] Suporte a PPTX e XLSX
- [ ] Parâmetros de chunking configuráveis por request
- [ ] Observabilidade e métricas de processamento
- [ ] Metadata com scores de confiança

### Out of Scope

- Inserção no banco de dados vetorial — responsabilidade do sistema consumidor
- Autenticação e autorização — infraestrutura do ambiente de deploy
- UI / dashboard — API headless
- Processamento assíncrono com fila (Celery/RQ) — volume on-demand não exige

## Context

O SelectionMaid v1.0 estabilizou o pipeline de normalização. O design hexagonal provou seu valor permitindo que a extração via Docling fosse integrada sem poluir o domínio. O sistema é síncrono e eficiente para o volume atual.

O projeto usa Python 3.13+ e Docling como biblioteca de extração primária.

## Constraints

- **Tech Stack**: Python 3.13+
- **Biblioteca de extração**: Docling (implementação principal do ExtractorPort)
- **Interface primária**: FastAPI (implementação principal do InputPort)
- **Arquitetura**: Hexagonal (Ports & Adapters) — não negociável

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Arquitetura hexagonal como constraint de design | Requisito explícito: trocar biblioteca não deve exigir mudança global | ✓ Validated |
| Docling como ExtractorPort inicial | Suporte nativo a PDF, DOCX, HTML + exportação Markdown de qualidade | ✓ Validated |
| FastAPI como InputPort inicial | Simples, escalável o suficiente para volume on-demand | ✓ Validated |
| Saída: chunks + metadados | Separação de responsabilidades | ✓ Validated |
| Markdown como formato de saída normalizado | Preserva hierarquia semântica, legível por LLMs | ✓ Validated |
| Thread-safety via threading.Lock em DoclingAdapter | Docling é CPU-bound e não thread-safe em algumas operações internas | ✓ Shipped |

---
*Last updated: 2026-05-25 after v1.0 completion*
