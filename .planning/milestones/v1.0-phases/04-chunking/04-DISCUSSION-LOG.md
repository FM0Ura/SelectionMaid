# Phase 4: Chunking - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-24
**Phase:** 4-Chunking
**Areas discussed:** Heading split strategy, Fixed-size fallback, page_start/page_end, chunk_id format

---

## Heading Split Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Qualquer heading (H1–H6) | Qualquer `#` até `######` cria novo chunk. Mais granular, mas pode criar chunks muito pequenos. | |
| H1 e H2 apenas | Split em `#` e `##`. Natural dado o bug #1023 que achata tudo para H2. | ✓ |
| H2 apenas | Só `##` dispara split. H1 tratado como título do documento. | |

**User's choice:** H1 e H2 apenas

---

| Option | Description | Selected |
|--------|-------------|----------|
| Chunk separado com section_title vazio | Preserva todo o conteúdo pré-heading. section_title="" é válido no schema. | ✓ |
| Descartado silenciosamente | Qualquer texto antes do primeiro H1/H2 é ignorado. | |
| Anexado ao primeiro chunk | Texto pré-heading prefixado ao primeiro chunk com heading. | |

**User's choice:** Chunk separado com section_title vazio

---

| Option | Description | Selected |
|--------|-------------|----------|
| Retorna o chunk completo | Section = 1 chunk, sem limites máximos. | |
| Subdivide se exceder limite configurado | Subdivisão adicional dentro da seção quando ultrapassa max. | ✓ |

**User's choice:** Subdivide se exceder limite configurado

---

| Option | Description | Selected |
|--------|-------------|----------|
| Por parágrafo (¶) | Agrupa parágrafos até atingir o limite. Nunca split intra-parágrafo. | ✓ |
| Por palavra (word count) | Acumula palavras até atingir o limite. Quebra no espaço mais próximo. | |
| Você decide | Claude escolhe a abordagem mais segura para v1. | |

**User's choice:** Por parágrafo (¶)

---

## Fixed-Size Fallback

| Option | Description | Selected |
|--------|-------------|----------|
| Word count como proxy | Zero dependência extra. 1 token ≈ 0.75 palavras. | |
| tiktoken (token budget real) | Conta tokens reais. Mais preciso para embeddings. Adiciona dep C-extension (~3MB). | ✓ |

**User's choice:** tiktoken

---

| Option | Description | Selected |
|--------|-------------|----------|
| cl100k_base | GPT-4 / text-embedding-ada-002. Padrão de fato para sistemas RAG modernos. | ✓ |
| o200k_base | Encoding GPT-4o. Menos documentado nos guias RAG. | |
| Configurável via config.toml | Default cl100k_base, overridable. | |

**User's choice:** cl100k_base

---

| Option | Description | Selected |
|--------|-------------|----------|
| 512 tokens | Padrão comum em RAG. Cabe em qualquer embedding model. | ✓ |
| 256 tokens | Chunks menores = retrieval mais preciso, perde contexto. | |
| 1024 tokens | Chunks maiores = mais contexto, pode ultrapassar alguns context windows. | |

**User's choice:** 512 tokens (default)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Respeitar boundary de parágrafo | Acumula parágrafos até max_tokens. Nunca corta dentro de um parágrafo. | ✓ |
| Cortar em tokens exatos | Corta no token mais próximo do limite. Pode quebrar frases. | |

**User's choice:** Sim, respeitar boundary de parágrafo

---

## page_start / page_end

| Option | Description | Selected |
|--------|-------------|----------|
| Sempre 0 | page_start=0, page_end=0. Sem informação de página disponível no chunker. | ✓ |
| Inferir por proporção do conteúdo | Estimar por chunk_index/total_chunks * page_count. Aproximado. | |
| Mudar a assinatura do ChunkerPort | Passar page_count para o chunker. Breaking change no port já definido. | |

**User's choice:** Sempre 0 — não inferível pelo chunker puro

---

## chunk_id format

| Option | Description | Selected |
|--------|-------------|----------|
| UUID v4 aleatório | Gerado via `uuid.uuid4()`. Globalmente único. | ✓ |
| Índice sequencial como string | chunk_id = str(chunk_index). Simples e determinístico. | |
| Hash SHA-256 do conteúdo (prefixo) | Content-addressable. Útil para dedup. | |

**User's choice:** UUID v4 aleatório

---

## Claude's Discretion

Nenhuma área foi delegada para decisão do Claude nesta sessão.

## Deferred Ideas

- **Encoding configurável** — `cl100k_base` hardcoded no v1. Candidato para v2 se outros modelos forem adicionados.
- **Chunk overlap** — Overlap de N tokens entre chunks consecutivos para melhor retrieval de contexto. Candidato CHUNK-V2-02.
- **Score de confiança por chunk** — Já em REQUIREMENTS.md como CHUNK-V2-03.
