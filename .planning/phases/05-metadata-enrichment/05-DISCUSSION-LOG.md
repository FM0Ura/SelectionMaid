# Phase 5: Metadata Enrichment - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-24
**Phase:** 5-metadata-enrichment
**Areas discussed:** Detecção de idioma, Inferência de doc_type, Campos title e author, Discrepância doc_id / source_filename

---

## Detecção de idioma

### Q1: Fallback quando langdetect falha

| Option | Description | Selected |
|--------|-------------|----------|
| "und" (undetermined) | Código ISO 639-3 padrão para indeterminado. Deixa claro sem silenciar o problema. | ✓ |
| String vazia "" | Campo presente mas vazio. Menos descritivo que 'und'. | |
| Enriquecimento parcial com warning | Preenche outros campos e marca language como erro. Requer warnings no ExtractionResult — adiado para v2. | |

**User's choice:** "und"

---

### Q2: API do langdetect a usar

| Option | Description | Selected |
|--------|-------------|----------|
| detect() simples | Retorna idioma com maior probabilidade. Não-determinista entre chamadas. | |
| detect_langs() com threshold >= 0.8 | Aceita só se confiança alta; retorna 'und' caso contrário. Evita falsos positivos. | ✓ |
| detect() com seed (DETECTOR_FACTORY.setSeed(0)) | Determinista. Efeito colateral em contexto multithreaded. | |

**User's choice:** `detect_langs()` com threshold de confiança

---

### Q3: Texto passado ao langdetect

| Option | Description | Selected |
|--------|-------------|----------|
| RawDocument.content completo | Mais texto disponível — maior precisão. Já filtrado (sem headers/footers). | ✓ |
| Primeiros N chars do content (ex: 1000) | Langdetect funciona bem com amostras. Melhor performance. | |
| Concat dos primeiros K chunks | Usa versão segmentada. Chunks podem ter contexto menos coeso. | |

**User's choice:** `RawDocument.content` completo

---

## Inferência de doc_type

### Q1: Abordagem de inferência

| Option | Description | Selected |
|--------|-------------|----------|
| Heurísticas estruturais no Markdown | Regras baseadas em padrões: tabelas → report, campos → form, etc. Zero deps extras. | |
| Keywords em headings + estrutura combinados | Detecta palavras como "Cláusula", "Slide" nos headings combinado com contagem de elementos. Mais expressivo, requer keywords multilingual. | ✓ |

**User's choice:** Keywords em headings + estrutura combinados

---

### Q2: Multilingual?

| Option | Description | Selected |
|--------|-------------|----------|
| Sim — keywords em PT, EN e ES | Ex: legal → ['cláusula', 'clause', 'contrato', 'contract', ...]. Mais abrangente. | ✓ |
| Apenas EN como baseline | Mais simples para v1. Perde eficácia em documentos PT/ES. | |

**User's choice:** Keywords multilinguais em PT, EN e ES

---

### Q3: Default quando nenhuma heurística bate

| Option | Description | Selected |
|--------|-------------|----------|
| "other" | Já no vocab fechado. Semântica clara: não reconhecido. | ✓ |
| "article" | Maioria de docs RAG é texto corrido. Pragmático mas potencialmente enganoso. | |

**User's choice:** `"other"`

---

## Campos title e author

### Q1: Origem do campo title

| Option | Description | Selected |
|--------|-------------|----------|
| Primeiro H1 do Markdown filtrado | Extrai `# Heading` do content. Simples, funciona bem para artigos/relatórios. Se não houver H1, retorna "". | ✓ |
| source_filename sem extensão | Sempre disponível. Ruim semanticamente — filenames não são títulos. | |
| String vazia quando não detectado | Honesto, mas perde a inferência via H1 que é confiável. | |

**User's choice:** Primeiro H1 do Markdown filtrado

---

### Q2: Origem do campo author

| Option | Description | Selected |
|--------|-------------|----------|
| String vazia sempre | Honesto — sem acesso a metadados XMP/PDF por trás do ExtractorPort. | ✓ |
| Heurística no Markdown (Author:, Por:, By:) | Baixa precisão, muitos falsos positivos. Complexidade desproporcional para v1. | |

**User's choice:** `author = ""`  sempre

---

## Discrepância doc_id / source_filename

### Q1: O que fazer com doc_id e source_filename ausentes em models.py

| Option | Description | Selected |
|--------|-------------|----------|
| Adicionar ao model nesta fase | Estender DocumentMetadata com doc_id (UUID v4) e source_filename (str). Alinha ROADMAP com código. | ✓ |
| Manter modelo atual, ignorar ROADMAP | doc_id/source_filename adicionados na Phase 6. Cria inconsistência temporária. | |
| Erro de documentação — corrigir só o ROADMAP | O model está correto; o ROADMAP foi escrito com nomes que mudaram. | |

**User's choice:** Adicionar ao model nesta fase

---

### Q2: Como gerar doc_id

| Option | Description | Selected |
|--------|-------------|----------|
| UUID v4 aleatório (mesmo padrão que chunk_id) | uuid.uuid4(). Consistente com D-54. Simples e idiomático. | ✓ |
| Hash determinístico do filename + conteúdo | Mesmo documento → mesmo doc_id. Útil para deduplication — Out of Scope no v1. | |

**User's choice:** UUID v4 aleatório

---

### Q3: Renomear ingestion_date → ingested_at e document_type → doc_type

| Option | Description | Selected |
|--------|-------------|----------|
| Renomear agora (ingested_at, doc_type) | Mais concisos, convencionais em APIs REST. Melhor fazer antes Phase 6 expor via Pydantic. | ✓ |
| Manter nomes atuais | Pode quebrar testes existentes. Pode ser feito na Phase 6 via alias Pydantic. | |

**User's choice:** Renomear agora

---

## Claude's Discretion

- Ordem de prioridade das heurísticas de doc_type: Claude decide a lógica de scoring/prioridade (keywords first vs. estrutural first).
- Desempate para documentos com conteúdo misto (ex: legal + tabelas): Claude decide se usa a primeira regra que bate ou a mais frequente.

## Deferred Ideas

- Threshold de confiança do langdetect configurável — v2 candidate (META-V2-01)
- Extração de metadados XMP/EXIF do PDF — requer mudança no ExtractorPort (META-V2-02)
- Score de confiança em campos inferidos — META-V2-01
- Autor inferido via heurística — baixa precisão, descartado para v1
