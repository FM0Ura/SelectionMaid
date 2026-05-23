# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-23)

**Core value:** Documentos entram em qualquer formato suportado, chunks Markdown normalizados saem via interface estável — independente da biblioteca de extração ou protocolo de entrada usados.
**Current focus:** Phase 1 — Domain Foundation

## Current Position

Phase: 1 of 7 (Domain Foundation)
Plan: 0 of 5 in current phase
Status: Ready to plan
Last activity: 2026-05-23 — Roadmap created, all 26 v1 requirements mapped across 7 phases

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: -
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Arquitetura hexagonal como constraint de design — troca de biblioteca não exige mudança global
- Docling como ExtractorPort inicial — suporte nativo multi-formato + exportação Markdown de qualidade
- FastAPI como InputPort inicial — adequado para volume on-demand
- Ordem de build: domínio → DoclingAdapter → filtro → chunker → enricher → HTTP → hardening

### Pending Todos

None yet.

### Blockers/Concerns

- [Research] Memory leak Docling: acúmulo 10–13GB RSS em conversões repetidas — Phase 2 deve implementar refresh strategy e medir empiricamente
- [Research] Event loop blocking: Docling é CPU-bound — Phase 6 deve usar run_in_threadpool e verificar com concurrency test
- [Research] Bug heading H2 (issue #1023): export_to_markdown() achata headings para H2 — aceitar output flat no v1; ExporterPort boundary permite fix drop-in

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-05-23
Stopped at: Roadmap and STATE.md criados; nenhum plano iniciado ainda
Resume file: None
