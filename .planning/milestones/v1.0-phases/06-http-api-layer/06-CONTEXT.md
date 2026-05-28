# Phase 6: HTTP API Layer - Context

**Gathered:** 2026-05-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 6 entrega o adaptador HTTP FastAPI — a implementação concreta do `InputPort` da arquitetura hexagonal. O adaptador inclui:

- Schemas Pydantic de request/response (`ExtractionResponse`, `HealthResponse`) em `adapters/http/schemas.py`
- Factory `build_router(service: ExtractionService) -> APIRouter` com endpoints `POST /ingest` e `GET /health`
- Validação de arquivo em 3 camadas: tamanho máximo (413), MIME type declarado (415), magic bytes (422)
- Criação do app FastAPI via `create_app()` em `adapters/http/app.py` com lifespan para singleton do `DocumentConverter`
- Integração com `run_in_threadpool` para descarregar o processamento CPU-bound do event loop
- Extensão de `GlobalConfig` com `HttpConfig` para parâmetros configuráveis

**Não inclui:** testes de integração multi-formato com arquivos reais (Phase 7), regressão de memória, teste de concorrência formal. O port `InputPort` não existe como Protocol explícito — o router é o próprio adaptador de entrada.

</domain>

<decisions>
## Implementation Decisions

### Schemas de Resposta (API-01)

- **D-74:** `ExtractionResponse` e `HealthResponse` vivem em `src/selection_maid/adapters/http/schemas.py` — schemas pertencem ao adaptador HTTP, não ao domínio. Domínio não importa Pydantic.
- **D-75:** `ExtractionResponse` espelha `ExtractionResult` com todos os 8 campos de `DocumentChunk` (chunk_id, content, page_start, page_end, section_title, chunk_index, total_chunks, word_count) e todos os 9 campos de `DocumentMetadata` (doc_id, source_filename, title, author, language, doc_type, page_count, chunk_count, ingested_at). Sem omissão de campos.
- **D-76:** `DocumentMetadata.ingested_at` (datetime) é serializado como ISO 8601 string no JSON — padrão Pydantic v2 para datetime. Ex: `"2026-05-24T20:15:00Z"`.
- **D-77:** `ExtractionResponse` usa `model_config = ConfigDict(from_attributes=True)`. O router chama `ExtractionResponse.model_validate(result, from_attributes=True)` para converter o `ExtractionResult` (dataclass frozen) sem código de mapeamento manual. `ExtractionResult.chunks` é `tuple[DocumentChunk, ...]` — Pydantic v2 serializa tuple como JSON array automaticamente.
- **D-78:** `HealthResponse` contém: `status: str` ("ok"), `rss_mb: float` (RSS via `psutil.Process().memory_info().rss / 1024**2`), `uptime_seconds: float` (calculado de `start_time` salvo no lifespan), `version: str` (via `importlib.metadata.version("selection-maid")`).

### Validação de Arquivo (API-03)

- **D-79:** Limite máximo de tamanho: **50 MB** (`50 * 1024 * 1024` bytes). Retorna HTTP 413 se `Content-Length` ou tamanho real do arquivo exceder esse limite. Configurável via `HttpConfig.max_file_bytes`.
- **D-80:** Formatos permitidos no v1: **PDF, DOCX, HTML** apenas. MIME types permitidos: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `text/html`. Imagens e PPTX/XLSX ficam no v2. Retorna HTTP 415 se MIME type declarado não estiver na lista. Lista configurável via `HttpConfig.allowed_mime_types`.
- **D-81:** Magic bytes verificados com **`python-magic`** (ou `python-magic-bin` no Windows/macOS). Lê os primeiros bytes do arquivo e detecta o MIME type real via libmagic. Se o MIME type detectado divergir do MIME type declarado pelo cliente, retorna HTTP 422. Validação ocorre ANTES de chamar `ExtractionService.process()` — fail fast.
- **D-82:** Corpo de erro estruturado para 413/415/422: `{"error": {"code": "...", "message": "..."}}`. Usa os error codes da taxonomia de domínio onde aplicável (ex: `UnsupportedFormatError` → `"EXT-002"`, erros de validação de tamanho → `"UPLOAD-001"`, magic bytes mismatch → `"UPLOAD-002"`).

### Lifespan e Wiring (ARCH-05)

- **D-83:** O app FastAPI vive em `src/selection_maid/adapters/http/app.py` como `create_app() -> FastAPI`. Uvicorn aponta para `selection_maid.adapters.http.app:app` (instância criada no nível de módulo via `app = create_app()`). Separado do router para facilitar testes que importam apenas o router.
- **D-84:** `DocumentConverter` é criado no lifespan como singleton. O lifespan monta todos os adaptadores e `ExtractionService`, depois chama `build_router(service)` e inclui o router no app. Padrão `@asynccontextmanager` lifespan do FastAPI (não `on_event` — deprecated).
- **D-85:** `build_router(service: ExtractionService) -> APIRouter` usa **closure**: os handlers dos endpoints capturam `service` diretamente via closure. Sem globals, sem FastAPI `Depends`, sem estado mutável. Assinatura: `def build_router(service: ExtractionService) -> APIRouter`.
- **D-86:** O `start_time` para cálculo de uptime é salvo como variável local no lifespan via `app.state.start_time = datetime.now(UTC)`. O handler de `GET /health` lê `request.app.state.start_time` para calcular `uptime_seconds`. Não requer estado global.

### Tempfile e Integração com ExtractionService

- **D-87:** O endpoint `POST /ingest` escreve o `UploadFile` em `tempfile.NamedTemporaryFile(delete=False, suffix=ext)` onde `ext` é derivado do MIME type. Passa o `Path` do tempfile para `RawInput`. Deleta o tempfile em bloco `finally` após `run_in_threadpool` completar — garantido mesmo em caso de erro.
- **D-88:** `await run_in_threadpool(service.process, raw_input)` descarrega `ExtractionService.process()` para o executor de threads do asyncio. Resolve o blocker de STATE.md: Docling é CPU-bound e não pode bloquear o event loop.

### run_in_threadpool e Configuração HTTP

- **D-89:** `GlobalConfig` é estendido com `HttpConfig` dataclass e campo `http: HttpConfig = field(default_factory=HttpConfig)` — mesmo padrão de `FilterConfig`, `ChunkerConfig`, `EnricherConfig`. Seção `[http]` no `config.toml` com chaves `max_file_bytes` e `allowed_mime_types`.
- **D-90:** `HttpConfig` default: `max_file_bytes: int = 52_428_800` (50MB), `allowed_mime_types: list[str] = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/html"]`.

### Claude's Discretion

- Mapping de erros de domínio (`SelectionMaidError` subclasses) para HTTP status codes: Claude decide o mapeamento completo (ex: `ExtractionTimeoutError` → 504, `UnsupportedFormatError` → 415, demais erros → 500). Um dict `ERROR_CODE_TO_HTTP` no router ou em `errors.py` é o padrão sugerido pelo comentário existente em `errors.py`.
- Ordem exata de validação no endpoint: Claude decide se tamanho é verificado pelo `Content-Length` header antes de ler o arquivo, ou só após ler. Uma abordagem razoável: verificar `Content-Length` first (fail fast sem ler bytes), depois ler e verificar magic bytes.
- Extensão de `config.py` para `allowed_mime_types` como `list[str]`: Claude decide como fazer o parsing do TOML (array de strings) via `tomllib` com type safety para mypy strict.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 6 goal, success criteria (5 itens: API-01/02/03 + ARCH-05 + run_in_threadpool). Contém os planos pré-definidos (06-01, 06-02, 06-03, 06-04).
- `.planning/REQUIREMENTS.md` — API-01 (POST /ingest, ExtractionResponse), API-02 (GET /health com RSS), API-03 (validação 3 camadas: tamanho/MIME/magic bytes), ARCH-05 (router isolado via factory, sem lógica de negócio).

### Domain Contracts (código existente — DEVE ser lido antes de implementar)
- `src/selection_maid/domain/models.py` — `ExtractionResult`, `DocumentMetadata`, `DocumentChunk`, `RawInput` — shapes exatos usados pelos schemas Pydantic e pelo router.
- `src/selection_maid/domain/ports.py` — ports existentes para referência; o router não implementa um Protocol novo, mas deve satisfazer a separação de responsabilidades de ARCH-05.
- `src/selection_maid/service.py` — `ExtractionService.process(input: RawInput) -> ExtractionResult` — assinatura locked. Router constrói `RawInput` e passa para `process()` via `run_in_threadpool`.
- `src/selection_maid/errors.py` — `SelectionMaidError` e subclasses (`ExtractionError`, `UnsupportedFormatError`, `ExtractionTimeoutError`, `FilterError`, `ChunkingError`, `EnrichmentError`) com error codes — router mapeia para HTTP status. Comentário existente em `errors.py` menciona `ERROR_CODE_TO_HTTP` no HTTP adapter.
- `src/selection_maid/config.py` — `GlobalConfig`, `FilterConfig`, `ChunkerConfig`, `EnricherConfig`, `get_config()` — estender com `HttpConfig` seguindo o mesmo padrão.

### Tech Stack
- `CLAUDE.md` §FastAPI Patterns — `DocumentConverter` singleton via lifespan, `UploadFile`/`SpooledTemporaryFile`, padrão `@asynccontextmanager` lifespan. **LEITURA OBRIGATÓRIA** para o padrão de wiring.
- `CLAUDE.md` §What NOT to Use — `@app.on_event("startup")` deprecated, usar lifespan. `file.read()` direto sem escrever em tempfile não funciona com Docling.
- `CLAUDE.md` §Constraints — Python 3.13+, uv, mypy strict, ruff.

### Decisões herdadas das fases anteriores
- `.planning/phases/01-domain-foundation/01-CONTEXT.md` — D-16 (exception wrapping pattern), D-05 (`RawInput` shape: path, filename, mime_type).
- `.planning/phases/02-docling-extraction-adapter/02-CONTEXT.md` — D-23 (factory function pattern `build_*()`), D-03/D-04 (directory structure).
- `.planning/phases/03-content-filtering/03-CONTEXT.md` — D-38/D-39/D-40 (config.toml pattern, GlobalConfig, injeção de construtor com defaults). `HttpConfig` segue o mesmo padrão.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/selection_maid/errors.py` — taxonomia completa de erros de domínio com `code` attributes. O router cria um mapping `code → HTTP status` usando esses codes.
- `src/selection_maid/config.py` — `GlobalConfig`, `_as_int()` helper, padrão de parsing TOML — estender com `HttpConfig` e `_as_list_str()` ou similar para `allowed_mime_types`.
- `src/selection_maid/adapters/http/__init__.py` — subpacote já existe (docstring de placeholder). Pronto para receber `app.py`, `router.py`, `schemas.py`.

### Established Patterns
- **Factory function D-23:** `build_heuristic_filter(config)` / `build_markdown_chunker(config)` / `build_metadata_enricher(config)` → `build_router(service: ExtractionService) -> APIRouter`.
- **Exception wrapping D-16:** Router captura `SelectionMaidError` subclasses e retorna `JSONResponse` estruturado. Outras exceções → 500 genérico.
- **Config pattern D-38/D-89:** `HttpConfig()` dataclass com defaults; `GlobalConfig` ganha `http: HttpConfig = field(default_factory=HttpConfig)`.
- **Frozen dataclasses + Pydantic v2:** `model_validate(obj, from_attributes=True)` é a abordagem correta para converter dataclasses frozen para schemas Pydantic sem código manual.

### Integration Points
- `src/selection_maid/adapters/http/app.py` — novo arquivo; contém `create_app() -> FastAPI` e `app = create_app()` para uvicorn.
- `src/selection_maid/adapters/http/router.py` — novo arquivo; contém `build_router(service) -> APIRouter`.
- `src/selection_maid/adapters/http/schemas.py` — novo arquivo; contém `ExtractionResponse`, `ChunkSchema`, `MetadataSchema`, `HealthResponse`.
- `src/selection_maid/config.py` — estender com `HttpConfig` e campo `http` em `GlobalConfig`.
- `tests/adapters/http/` — diretório de testes HTTP (criar `__init__.py` + `test_router.py`).
- **Atenção:** `ExtractionResult.chunks` é `tuple[DocumentChunk, ...]` (não `list`) — o schema Pydantic deve declarar `chunks: list[ChunkSchema]` (Pydantic v2 converte tuple para list no JSON automaticamente, mas o type annotation do schema deve ser `list`).

</code_context>

<specifics>
## Specific Ideas

- O comentário em `errors.py` já menciona `ERROR_CODE_TO_HTTP` no HTTP adapter — implementar como dict no `router.py` ou em arquivo separado `adapters/http/error_map.py`.
- A validação de magic bytes ocorre ANTES de chamar `ExtractionService.process()` — fail fast. A ordem completa sugerida no endpoint: (1) verificar Content-Length header, (2) ler arquivo em memória/tempfile, (3) verificar tamanho real, (4) verificar MIME type declarado, (5) verificar magic bytes, (6) run_in_threadpool.
- `psutil` precisa ser adicionado como dependência via `uv add psutil` para a leitura de RSS no `GET /health`.
- `python-magic` precisa ser adicionado via `uv add python-magic`. No Linux/macOS requer `libmagic` instalada no sistema; no Windows usar `python-magic-bin`.
- `start_time` no lifespan deve usar `datetime.now(timezone.utc)` (timezone-aware) — não `datetime.now()` (naive). Consistente com `ingested_at` em `DocumentMetadata`.

</specifics>

<deferred>
## Deferred Ideas

- **Timeout por request para Docling** — `ExtractionTimeoutError` já existe no domínio, mas configurar um timeout real no `run_in_threadpool` requer `asyncio.wait_for` com um executor wrapper. Complexidade extra para v1; os testes de integração da Phase 7 medirão o comportamento real.
- **Autenticação/autorização** — explicitamente Out of Scope em PROJECT.md. Responsabilidade da infra de deploy.
- **Rate limiting** — não necessário para volume on-demand v1.
- **CORS** — se o consumidor for uma SPA web, vai precisar de `CORSMiddleware`. Não há requisito para v1 (API headless sem UI).
- **Suporte a imagens via OCR no v1** — EXT-V2-01 em REQUIREMENTS.md. Docling suporta, mas OCR é lento e requer timeouts maiores. Postergado para v2.

</deferred>

---

*Phase: 6-HTTP API Layer*
*Context gathered: 2026-05-24*
