# SelectionMaid

## What This Is

SelectionMaid é um serviço de curadoria e normalização de documentos — a "empregada" que recebe arquivos brutos (PDF, DOCX, HTML, imagens), extrai o conteúdo via Docling, limpa o ruído, enriquece metadados, segmenta em chunks e devolve Markdown estruturado pronto para ser inserido em um banco de dados vetorial. É a porta de entrada do pipeline RAG, desenhada como arquitetura hexagonal: todos os adaptadores (extrator, filtro, chunker, interface HTTP) são intercambiáveis sem tocar no núcleo de domínio.

## Current State: v1.0 Shipped (2026-05-25)

✓ **Hexagonal Stack**: Core domain, service layer, and all adapters (Docling, HeuristicFilter, MarkdownChunker, MetadataEnricher, FastAPI) are fully implemented and decoupled.
✓ **Multi-Format Extraction**: Production-ready extraction for PDF, DOCX, and HTML.
✓ **Hardened API**: 3-layer file validation, concurrent request handling, and memory-safe implementation.
✓ **Verified**: 100% test coverage (204 tests) and Nyquist compliance.

## Current Milestone: v2.0 Frontend

**Goal:** Criar uma SPA Vue 3 + Vite que expõe todo o pipeline do SelectionMaid com dark mode minimalista e animações de alta qualidade.

**Current state:** Phase 8 complete — backend CORS is enabled for the local Vite SPA, and the Vue/Vite/Tailwind/shadcn frontend scaffold is in place.

**Target features:**

- Upload via drag-and-drop animado com feedback visual rico
- Loading states (skeleton/shimmer) enquanto o backend processa
- Revelação dos chunks com stagger animation após a resposta
- Transições de view suaves entre seções da interface
- Visualização dos metadados retornados pela API
- SPA desacoplada consumindo a FastAPI via HTTP (CORS)

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
- [x] CORS habilitado no backend para consumo pela SPA — Validated in Phase 8
- [x] Frontend Vue 3 + Vite scaffold com Tailwind CSS v4, shadcn-vue e dark mode fixo — Validated in Phase 8

### Active (v2.0)

- [ ] Interface de upload via drag-and-drop com feedback visual animado
- [ ] Loading states (skeleton/shimmer) durante o processamento
- [ ] Visualização dos chunks com stagger animation na revelação
- [ ] Transições de view suaves entre seções
- [ ] Exibição dos metadados retornados pela API

### Out of Scope

- Inserção no banco de dados vetorial — responsabilidade do sistema consumidor
- Autenticação e autorização — infraestrutura do ambiente de deploy
- Processamento assíncrono com fila (Celery/RQ) — volume on-demand não exige
- OCR, PPTX/XLSX, chunking configurável, observabilidade — deferidos para v2.1+

## Context

O SelectionMaid v1.0 estabilizou o pipeline de normalização. O design hexagonal provou seu valor permitindo que a extração via Docling fosse integrada sem poluir o domínio. O sistema é síncrono e eficiente para o volume atual.

O v2.0 adiciona uma camada de apresentação (Vue 3 + Vite SPA) completamente desacoplada do backend. O frontend consome a API existente via HTTP sem modificar o núcleo hexagonal.

O projeto usa Python 3.13+ no backend e Vue 3 + Vite no frontend.

## Constraints

- **Backend Stack**: Python 3.13+, FastAPI, Docling — inalterado
- **Frontend Stack**: Vue 3 + Vite — SPA estática desacoplada
- **Arquitetura**: Hexagonal (Ports & Adapters) no backend — não negociável
- **Deploy**: Frontend como SPA separada; backend expõe CORS para o domínio da SPA
- **Target**: Ferramenta de uso interno (dev) — não requer auth nem acessibilidade WCAG

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Arquitetura hexagonal como constraint de design | Requisito explícito: trocar biblioteca não deve exigir mudança global | ✓ Validated |
| Docling como ExtractorPort inicial | Suporte nativo a PDF, DOCX, HTML + exportação Markdown de qualidade | ✓ Validated |
| FastAPI como InputPort inicial | Simples, escalável o suficiente para volume on-demand | ✓ Validated |
| Saída: chunks + metadados | Separação de responsabilidades | ✓ Validated |
| Markdown como formato de saída normalizado | Preserva hierarquia semântica, legível por LLMs | ✓ Validated |
| Thread-safety via threading.Lock em DoclingAdapter | Docling é CPU-bound e não thread-safe em algumas operações internas | ✓ Shipped |

## Evolution

This document evolves at phase transitions and milestone boundaries.

### After each phase transition (via `/gsd-transition`)

1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

### After each milestone (via `/gsd:complete-milestone`)

1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---

Last updated: 2026-05-26 after Phase 8 completion
