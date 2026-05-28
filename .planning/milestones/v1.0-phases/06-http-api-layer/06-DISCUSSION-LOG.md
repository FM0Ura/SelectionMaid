# Phase 6: HTTP API Layer - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-24
**Phase:** 06-http-api-layer
**Areas discussed:** Schemas de resposta, Validação de arquivo, Lifespan e wiring, run_in_threadpool e config HTTP

---

## Schemas de Resposta

### Campos de DocumentChunk no JSON

| Option | Description | Selected |
|--------|-------------|----------|
| Todos os 8 campos | chunk_id, content, page_start, page_end, section_title, chunk_index, total_chunks, word_count — espelha o domínio | ✓ |
| Subconjunto sem page_start/page_end | Omitir campos que são sempre 0 no v1 | |
| Subconjunto mínimo | chunk_id, content, section_title, chunk_index, word_count apenas | |

**User's choice:** Todos os 8 campos de DocumentChunk
**Notes:** Expor o contrato completo; o consumidor decide o que usa.

---

### Serialização de ingested_at

| Option | Description | Selected |
|--------|-------------|----------|
| ISO 8601 string | Ex: "2026-05-24T20:15:00Z". Padrão Pydantic v2 para datetime | ✓ |
| Unix timestamp (float) | Ex: 1748124900.0. Sem ambiguidade de timezone, mas menos legível | |

**User's choice:** ISO 8601 string
**Notes:** Default do Pydantic v2; sem configuração adicional necessária.

---

### Construção de ExtractionResponse a partir de ExtractionResult

| Option | Description | Selected |
|--------|-------------|----------|
| model_config from_attributes=True | Pydantic v2 lê dataclasses via model_validate(obj, from_attributes=True). Sem mapeamento manual | ✓ |
| Método from_result() classmethod | Conversão explícita, mas boilerplate desnecessário | |
| Construção manual no router | Mistura serialização com lógica de routing, conflita com ARCH-05 | |

**User's choice:** model_config from_attributes=True
**Notes:** Abordagem mais idiomática e alinhada com CLAUDE.md §FastAPI Patterns.

---

### Localização dos schemas Pydantic

| Option | Description | Selected |
|--------|-------------|----------|
| src/selection_maid/adapters/http/schemas.py | Schemas pertencem ao adaptador HTTP, não ao domínio | ✓ |
| src/selection_maid/schemas.py | Nível de pacote, mais visível; mas no v1 apenas o HTTP usa | |

**User's choice:** adapters/http/schemas.py
**Notes:** Consistente com arquitetura hexagonal — domínio não importa Pydantic.

---

## Validação de Arquivo

### Limite máximo de tamanho (HTTP 413)

| Option | Description | Selected |
|--------|-------------|----------|
| 50MB | Mencionado no CLAUDE.md para volume on-demand v1 | ✓ |
| 10MB | Mais conservador, pode rejeitar relatórios longos | |
| 100MB | Mais generoso, mas arriscado para threadpool | |

**User's choice:** 50MB
**Notes:** Configurável via HttpConfig.max_file_bytes.

---

### Formatos permitidos no v1

| Option | Description | Selected |
|--------|-------------|----------|
| PDF, DOCX, HTML apenas | Cobre EXT-01/02/03; imagens são v2 per EXT-V2-01 | ✓ |
| PDF, DOCX, HTML + imagens | OCR desde v1; mais completo mas mais lento | |

**User's choice:** PDF, DOCX, HTML apenas
**Notes:** Imagens e PPTX/XLSX ficam nos v2 requirements.

---

### Verificação de magic bytes

| Option | Description | Selected |
|--------|-------------|----------|
| python-magic | Detecta MIME type real via libmagic. Cobre formatos compostos como DOCX (ZIP) | ✓ |
| Verificação manual dos primeiros bytes | Sem dependência extra, mas mais frágil para DOCX | |

**User's choice:** python-magic
**Notes:** DOCX é um ZIP — verificação manual de %PK seria frágil. python-magic é o caminho correto.

---

### Formato de resposta de erro

| Option | Description | Selected |
|--------|-------------|----------|
| JSON estruturado: {"error": {"code": "...", "message": "..."}} | Usa error codes do domínio, parseável por clientes | ✓ |
| FastAPI default: {"detail": "..."} | Mais simples, menos descritivo | |

**User's choice:** JSON estruturado com error code
**Notes:** Consistente com a taxonomia de erros já em errors.py.

---

## Lifespan e Wiring

### Montagem do ExtractionService e wiring do router

| Option | Description | Selected |
|--------|-------------|----------|
| App state via lifespan + build_router() recebe o service | Padrão do CLAUDE.md. DocumentConverter singleton no lifespan | ✓ |
| FastAPI Depends | Mais idiomático para FastAPI, mas DocumentConverter seria recriado sem lru_cache | |
| Variável global de módulo | Mais simples, mas viola hexagonal e dificulta testes | |

**User's choice:** App state via lifespan + build_router(service)
**Notes:** CLAUDE.md documenta esse padrão explicitamente como a abordagem correta.

---

### Localização do app FastAPI

| Option | Description | Selected |
|--------|-------------|----------|
| src/selection_maid/adapters/http/app.py | create_app() + app = create_app(). Uvicorn aponta para .app:app | ✓ |
| src/selection_maid/main.py | Mais visível no nível do pacote, mas mistura ponto de entrada com adaptador | |

**User's choice:** adapters/http/app.py
**Notes:** Separar app.py de router.py facilita testes que importam apenas o router.

---

### Como build_router recebe o service

| Option | Description | Selected |
|--------|-------------|----------|
| Closure: build_router(service) captura service nos handlers | Sem globals, sem Depends, mypy happy | ✓ |
| Classe Router com __init__(self, service) | OOP approach, mas FastAPI prefere funções como handlers | |

**User's choice:** Closure
**Notes:** Padrão mais simples e consistente com build_heuristic_filter, build_markdown_chunker, etc.

---

### Conteúdo de GET /health

| Option | Description | Selected |
|--------|-------------|----------|
| status + rss_mb | Minimalista, cobre API-02 exatamente | |
| status + rss_mb + uptime + version | Mais informativo para monitoring | ✓ |

**User's choice:** status + rss_mb + uptime_seconds + version
**Notes:** uptime via app.state.start_time no lifespan; version via importlib.metadata.

---

## run_in_threadpool e Config HTTP

### Descarregar Docling do event loop

| Option | Description | Selected |
|--------|-------------|----------|
| fastapi.concurrency.run_in_threadpool | API oficial do FastAPI. await run_in_threadpool(service.process, input) | ✓ |
| asyncio.get_event_loop().run_in_executor | Equivalente de nível mais baixo | |

**User's choice:** run_in_threadpool
**Notes:** Resolve o blocker explicitamente listado no STATE.md.

---

### GlobalConfig vs constantes de módulo para parâmetros HTTP

| Option | Description | Selected |
|--------|-------------|----------|
| HttpConfig dataclass no GlobalConfig | Seguindo padrão de FilterConfig/ChunkerConfig/EnricherConfig | ✓ |
| Constantes de módulo em adapters/http/ | Mais simples, mas fora do padrão estabelecido | |

**User's choice:** HttpConfig no GlobalConfig
**Notes:** Seção [http] no config.toml com max_file_bytes e allowed_mime_types.

---

### Gerenciamento do arquivo temporário

| Option | Description | Selected |
|--------|-------------|----------|
| tempfile.NamedTemporaryFile(delete=False) + cleanup manual em finally | Padrão do CLAUDE.md para UploadFile + Docling | ✓ |
| SpooledTemporaryFile direto | Docling precisa de path real no disco, não funciona com file handles | |

**User's choice:** NamedTemporaryFile com delete=False
**Notes:** CLAUDE.md documenta explicitamente que Docling requer path no filesystem.

---

## Claude's Discretion

- **Mapeamento de erros de domínio para HTTP status:** Claude decide o dict `ERROR_CODE_TO_HTTP` completo (sugestão: `ExtractionTimeoutError` → 504, `UnsupportedFormatError` → 415, demais erros de domínio → 500).
- **Ordem de validação no endpoint:** Claude decide a ordem exata das 3 camadas de validação (Content-Length header primeiro ou após ler o arquivo).
- **Parsing de `allowed_mime_types` como list[str] do TOML:** Claude decide a implementação type-safe para mypy strict.

## Deferred Ideas

- **Timeout por request para Docling** — `asyncio.wait_for` com executor wrapper. Complexidade para v1; Phase 7 medirá comportamento real.
- **CORS middleware** — necessário se o consumidor for uma SPA. Sem requisito para v1.
- **Rate limiting** — não necessário para volume on-demand v1.
- **Suporte a imagens OCR** — EXT-V2-01 em REQUIREMENTS.md; postergado para v2.
- **Autenticação/autorização** — Out of Scope explícito em PROJECT.md.
