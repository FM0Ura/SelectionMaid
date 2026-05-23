# SelectionMaid

## What This Is

SelectionMaid é um serviço de curadoria e normalização de documentos — a "empregada" que recebe arquivos brutos (PDF, DOCX, HTML, imagens), extrai o conteúdo via Docling, limpa o ruído, enriquece metadados, segmenta em chunks e devolve Markdown estruturado pronto para ser inserido em um banco de dados vetorial. É a porta de entrada do pipeline RAG, desenhada como arquitetura hexagonal: todos os adaptadores (extrator, filtro, chunker, interface HTTP) são intercambiáveis sem tocar no núcleo de domínio.

## Core Value

Documentos entram em qualquer formato, chunks Markdown normalizados saem via uma interface estável — independente da biblioteca de extração ou do protocolo de entrada usado.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Aceitar documentos PDF, DOCX, HTML e imagens (OCR) via API HTTP
- [ ] Extrair texto via Docling encapsulado em adaptador intercambiável
- [ ] Filtrar ruído (cabeçalhos, rodapés, números de página, artefatos de OCR)
- [ ] Converter conteúdo para Markdown preservando hierarquia de seções
- [ ] Enriquecer metadados (tipo de documento, idioma, data, autor inferidos)
- [ ] Segmentar o conteúdo em chunks de tamanho controlado
- [ ] Retornar lista de chunks com metadados em schema consistente
- [ ] Interface HTTP (FastAPI) isolada como adaptador de entrada plugável
- [ ] Arquitetura hexagonal: todo componente de processamento é um Port com Adapter substituível

### Out of Scope

- Inserção no banco de dados vetorial — responsabilidade do sistema consumidor
- Autenticação e autorização — infraestrutura do ambiente de deploy
- UI / dashboard — API headless
- Processamento assíncrono com fila (Celery/RQ) — volume on-demand não exige

## Context

O SelectionMaid é o módulo de ingestão de um pipeline RAG maior. A identidade do vector DB ainda não foi definida — deliberadamente, pois o módulo não se responsabiliza pela inserção. O consumidor chama a API, recebe os chunks normalizados e os insere onde quiser.

O projeto usa Python 3.13+ e começa com Docling como biblioteca de extração, mas o design hexagonal garante que qualquer troca futura (pypdfium2, pdfplumber, unstructured) afete apenas o adaptador, não o serviço nem a API.

O histórico do projeto já tem experimentação com pypdfium2 e filtros heurísticos (Fases 1–3 anteriores). Esse reinício unifica a visão com Docling como backend principal desde a fundação.

## Constraints

- **Tech Stack**: Python 3.13+ (já fixado no pyproject.toml)
- **Biblioteca de extração**: Docling como implementação inicial do ExtractorPort
- **Interface primária**: FastAPI como implementação inicial do InputPort
- **Arquitetura**: Hexagonal (Ports & Adapters) — não negociável; é o requisito central de desacoplamento
- **Volume**: Low-traffic, on-demand — sem necessidade de fila ou workers horizontais no v1

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Arquitetura hexagonal como constraint de design | Requisito explícito do usuário: trocar biblioteca não deve exigir mudança global | — Pending |
| Docling como ExtractorPort inicial | Suporte nativo a PDF, DOCX, HTML, imagens + exportação Markdown de qualidade | — Pending |
| FastAPI como InputPort inicial | Simples, escalável o suficiente para volume on-demand, amplamente adotado | — Pending |
| Saída: chunks + metadados (não insere no vector DB) | Separação de responsabilidades; consumidor decide onde armazenar | — Pending |
| Markdown como formato de saída normalizado | Preserva hierarquia semântica do documento, legível por humanos e LLMs | — Pending |

## Evolution

Este documento evolui a cada transição de fase e marcos do projeto.

**Após cada transição de fase** (via `/gsd-transition`):
1. Requirements invalidados? → Mover para Out of Scope com motivo
2. Requirements validados? → Mover para Validated com referência de fase
3. Novos requirements emergiram? → Adicionar em Active
4. Decisões a registrar? → Adicionar em Key Decisions
5. "What This Is" ainda preciso? → Atualizar se derivou

**Após cada milestone** (via `/gsd:complete-milestone`):
1. Revisão completa de todas as seções
2. Core Value check — ainda é a prioridade certa?
3. Auditoria de Out of Scope — motivos ainda válidos?
4. Atualizar Context com estado atual

---
*Last updated: 2026-05-23 after initialization*
