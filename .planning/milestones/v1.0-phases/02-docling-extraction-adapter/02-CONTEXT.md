# Phase 2: Docling Extraction Adapter - Context

**Gathered:** 2026-05-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 entrega `DoclingAdapter` — a implementação concreta de `ExtractorPort` que usa a biblioteca Docling para converter PDF, DOCX e HTML em `RawDocument` com conteúdo Markdown estruturado. O adaptador é a única fronteira onde tipos Docling podem existir: nenhum tipo do namespace `docling` vaza para fora de `src/selection_maid/adapters/extractor/`. A fase também cobre: ciclo de vida do `DocumentConverter` (singleton injetado), timeout de 120s, validação de formato no ponto de entrada, e testes de integração com documentos reais baixados on-demand.

**Não inclui:** filtragem de conteúdo (Phase 3), chunking (Phase 4), enriquecimento de metadados (Phase 5), interface HTTP (Phase 6).

</domain>

<decisions>
## Implementation Decisions

### Singleton Ownership (DoclingAdapter constructor)

- **D-21:** `DoclingAdapter` recebe o `DocumentConverter` via injeção de construtor: `__init__(self, converter: DocumentConverter, timeout_seconds: int = 120)`. O adapter não cria o converter — recebe um pronto. Phase 6 cria o converter no lifespan do FastAPI e injeta. Testes passam uma instância real (integração) ou mocam conforme necessário.
- **D-22:** Formatos suportados são hardcoded como constante de módulo (não configurável via construtor): `SUPPORTED_MIME_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/html"}`. Formatos v2 (PPTX, XLSX) serão adicionados ao mesmo conjunto no futuro.
- **D-23:** `DoclingAdapter` é exposto como classe direta mais uma factory function `build_docling_adapter(converter: DocumentConverter, timeout_seconds: int = 120) -> DoclingAdapter`. Padrão consistente com o `build_router(service)` que será definido na Phase 6.

### Timeout Mechanism

- **D-24:** Timeout de 120s implementado com `concurrent.futures.ThreadPoolExecutor`: a chamada `converter.convert()` é submetida em thread separada, e o resultado obtido com `future.result(timeout=timeout_seconds)`. A `TimeoutError` do Python é capturada e traduzida para `ExtractionTimeoutError`. Trade-off aceito para v1: a thread de conversão pode continuar rodando em background após timeout (comportamento de low-traffic on-demand não exige término abrupto).
- **D-25:** `timeout_seconds: int = 120` é parâmetro do construtor (D-21). Testes de integração podem usar valor menor (ex: 5s) para validar o mecanismo sem esperar 120s.

### Integration Test Fixtures

- **D-26:** Fixtures de integração são baixadas de URLs públicas na primeira execução dos testes. Cache local em `tests/fixtures/` (diretório no `.gitignore`). Implementado como pytest fixture com escopo `session`: verifica se arquivo existe no cache antes de baixar.
- **D-27:** Se o download falhar (sem internet, URL indisponível), testes de integração são pulados com `pytest.skip("Integration fixtures unavailable — skipping")`. Sem falha de CI por conectividade. Testes unitários (com mock do converter) sempre executam independente de conectividade.

### Docling Output Mapping

- **D-28:** Conteúdo Markdown extraído via `result.document.export_to_markdown()` — método nativo do `DoclingDocument`. O bug conhecido de achatamento de headings para H2 (issue #1023) é aceito no v1. O boundary `ExtractorPort` permite corrigir o output sem mudar a interface quando o bug for corrigido no Docling.
- **D-29:** `RawDocument.page_count` preenchido com `len(result.document.pages)` para PDF e DOCX; `page_count=0` para HTML (HTML não tem conceito de páginas — compatível com D-06 "page_count=0 when unknown").
- **D-30:** `UnsupportedFormatError` lançada no início de `extract()` se `document.mime_type` não estiver em `SUPPORTED_MIME_TYPES`, **antes** de chamar Docling. Falhas internas do Docling para formatos suportados são capturadas e traduzidas para `ExtractionError` (padrão D-16 de wrapping já definido no ExtractionService, aplicado também no adapter).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 2 goal, success criteria (7 itens: EXT-01..EXT-07 + singleton + timeout + boundary check), e planos pré-definidos (02-01 a 02-05).
- `.planning/REQUIREMENTS.md` — EXT-01 a EXT-07 (formatos aceitos, preservação de Markdown), ARCH-01 (ExtractorPort boundary).

### Phase 1 Context (decisões herdadas)
- `.planning/phases/01-domain-foundation/01-CONTEXT.md` — Decisões D-05 a D-20 que Phase 2 herda: assinatura do port (D-09), tipos de entrada/saída (D-05, D-06), métodos síncronos (D-13), taxonomia de erros (D-17 a D-20), localização dos arquivos (D-03, D-04).

### Domain Contracts (código existente)
- `src/selection_maid/domain/ports.py` — `ExtractorPort.extract(document: RawInput) -> RawDocument` — assinatura locked.
- `src/selection_maid/domain/models.py` — `RawInput`, `RawDocument` — campos exatos que DoclingAdapter recebe e retorna.
- `src/selection_maid/errors.py` — `ExtractionError`, `UnsupportedFormatError`, `ExtractionTimeoutError` já definidas — DoclingAdapter usa estas classes.

### Tech Stack
- `CLAUDE.md` §Technology Stack — Docling `>=2.95`, `DocumentConverter`, `PipelineOptions`, `DoclingDocument.export_to_markdown()`, CPU-only torch install pattern. Seção "Docling Markdown Export — Known Limitation" documenta bug #1023 (headings achatados para H2).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/selection_maid/errors.py` — `ExtractionError`, `UnsupportedFormatError`, `ExtractionTimeoutError` prontas para uso. DoclingAdapter importa e lança estas classes diretamente.
- `tests/stubs/adapters.py` — Stubs das fases anteriores. DoclingAdapter NÃO usa stubs — é a implementação real. Mas os testes de integração de Phase 2 podem chamar ExtractionService com DoclingAdapter real + stubs dos outros ports (filter, chunker, enricher).

### Established Patterns
- Injeção de construtor: `ExtractionService.__init__(self, extractor, filter, chunker, enricher)` — Phase 2 segue o mesmo padrão para `DoclingAdapter.__init__(self, converter, timeout_seconds)`.
- Exception wrapping D-16: `try/except` em cada chamada de port. DoclingAdapter aplica o mesmo padrão internamente ao chamar `converter.convert()`.

### Integration Points
- `src/selection_maid/adapters/extractor/__init__.py` — vazio. `DoclingAdapter` vai aqui (em `docling.py` dentro do subpacote ou direto no `__init__`).
- `tests/adapters/extractor/` — vazio. Testes de integração do DoclingAdapter vão aqui.
- Phase 6 vai criar `DocumentConverter` no lifespan do FastAPI e injetá-lo em `DoclingAdapter` — a interface `build_docling_adapter(converter)` é o ponto de integração.

</code_context>

<specifics>
## Specific Ideas

- A thread que "lingers" após timeout é aceita explicitamente para v1 (low-traffic, on-demand). Se em produção o memory leak de threads se tornar um problema, a estratégia pode evoluir para `multiprocessing` sem mudar a interface.
- `tests/fixtures/` deve ter um `README.md` ou comentário no conftest documentando de onde as fixtures são baixadas — facilita reprodução manual e auditoria.
- O bug de headings H2 (Docling issue #1023) está documentado no STATE.md como concern conhecido. Não precisa de workaround em Phase 2 — aceitar o output flat do `export_to_markdown()`.

</specifics>

<deferred>
## Deferred Ideas

- **multiprocessing para timeout** — Isolamento real com término de processo filho. Considerado e descartado para v1 por overhead e complexidade. Revisitar se thread-lingering se tornar problema em produção.
- **Configuração de formatos via construtor** — `DoclingAdapter(converter, allowed_formats={"application/pdf"})`. Descartado para v1 (hardcoded é suficiente). Candidato para v2 quando PPTX/XLSX forem adicionados (EXT-V2-02, EXT-V2-03).
- **Fixtures binárias no repo** — Opção considerada e descartada em favor de download on-demand. Manter a decisão: fixtures em `tests/fixtures/` são gitignored.

</deferred>

---

*Phase: 2-Docling Extraction Adapter*
*Context gathered: 2026-05-23*
