---
phase: 02-docling-extraction-adapter
verified: 2026-05-24T13:05:00Z
status: gaps_found
score: 5/7
overrides_applied: 0
gaps:
  - truth: "Um arquivo PDF com texto digital é aceito e retorna RawDocument com Markdown contendo headings H1/H2/H3 preservados"
    status: partial
    reason: "A fixture de PDF (sample.pdf) não pôde ser baixada: o URL https://www.w3.org/WAI/WCAG21/Techniques/pdf/pdf-sample.pdf retorna HTTP 404. Os testes test_pdf_extraction, test_headings_in_pdf e test_service_with_docling_adapter foram PULADOS (pytest.skip). O mecanismo de extração existe e está correto no código, mas a cobertura de teste para PDF não é exercitada no ambiente atual. A lógica de heading extração está documentada (D-28: export_to_markdown(), limitação H2 via issue #1023 aceita com comentário no teste), mas não foi executada contra um PDF real."
    artifacts:
      - path: "tests/fixtures/"
        issue: "sample.pdf ausente — URL fixture retorna 404; apenas sample.docx e sample.html presentes"
      - path: "tests/adapters/extractor/test_docling_adapter.py"
        issue: "test_pdf_extraction, test_headings_in_pdf e test_service_with_docling_adapter pulados por 'Integration fixtures unavailable'"
    missing:
      - "Substituir URL da fixture PDF por uma URL funcional ou incluir um PDF mínimo no repositório (tests/fixtures/sample.pdf) para garantir cobertura contínua de SC-1"
  - truth: "DocumentConverter é instanciado uma única vez (singleton via lifespan) — chamadas repetidas não criam novas instâncias"
    status: partial
    reason: "O padrão de singleton via injeção de construtor (D-21) está implementado: DoclingAdapter recebe o converter pronto e não o cria internamente. A cobertura de teste via fixture session-scoped (test_converter_singleton_behavior) PASSOU e confirma que o mesmo objeto é compartilhado dentro da sessão pytest. Porém, o 'via lifespan' mencionado no SC-5 refere-se ao lifespan do FastAPI, que é responsabilidade da Phase 6, não ainda implementado. A interpretação do SC-5 sob Phase 2 é atendida pelo padrão de injeção (adapter nunca instancia converter) e pelo teste de singleton — mas a garantia de lifespan em produção (FastAPI) não existe ainda."
    artifacts:
      - path: "src/selection_maid/adapters/http/__init__.py"
        issue: "Arquivo vazio — FastAPI lifespan não implementado (previsto para Phase 6)"
    missing:
      - "Este item é parcialmente deferred para Phase 6 (FastAPI lifespan). A Phase 2 entrega o contrato de injeção; Phase 6 entrega o singleton em produção. O gap no contexto de Phase 2 é aceitável se tratado como deferred."
deferred:
  - truth: "DocumentConverter é instanciado uma única vez (singleton via lifespan) — chamadas repetidas não criam novas instâncias"
    addressed_in: "Phase 6"
    evidence: "Phase 6 goal: 'O serviço é acessível via HTTP'; D-21 documenta explicitamente 'Phase 6 cria o converter no lifespan do FastAPI e injeta'. O padrão de injeção está pronto em Phase 2; o lifespan real é Phase 6."
human_verification:
  - test: "Substituir sample.pdf por fixture funcional e rodar test_pdf_extraction + test_headings_in_pdf"
    expected: "RawDocument com content contendo pelo menos um marcador '# ' (qualquer nível de heading)"
    why_human: "Requer download de PDF funcional ou inclusão de fixture binária no repositório — decisão sobre estratégia de fixture cabe ao desenvolvedor"
  - test: "Verificar que test_service_with_docling_adapter passa com PDF real"
    expected: "ExtractionResult com metadata != None e len(chunks) >= 1"
    why_human: "Depende da disponibilidade do fixture PDF — mesmo bloqueador acima"
---

# Phase 2: Docling Extraction Adapter — Verification Report

**Phase Goal:** PDFs, DOCX e HTML reais são convertidos para Markdown estruturado via DoclingAdapter sem vazar tipos Docling para fora do adaptador
**Verified:** 2026-05-24T13:05:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                          | Status            | Evidence                                                                                                                                                  |
|----|-----------------------------------------------------------------------------------------------|-------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1  | PDF aceito e retorna RawDocument com headings H1/H2/H3 preservados                            | PARTIAL           | Fixture sample.pdf ausente (URL 404); test_pdf_extraction + test_headings_in_pdf PULADOS. Lógica implementada corretamente mas sem execucao real de PDF.  |
| 2  | DOCX com tabelas aceito e retorna Markdown com tabelas GFM                                     | VERIFIED          | test_tables_in_docx PASSOU: asserta `|` e `---` em result.content com sample.docx real (1.3MB fixture baixada com sucesso)                               |
| 3  | HTML aceito e retorna Markdown com listas ordenadas e não-ordenadas preservadas                | VERIFIED          | test_lists_in_html PASSOU: asserta `- `, `* ` ou `1. ` em result.content com www.w3.org/TR/WCAG20/ real                                                  |
| 4  | Blocos de código delimitados com backticks no Markdown retornado                               | VERIFIED          | test_code_blocks PASSOU: fixture inline `<pre><code>` em tmp_path; asserta ` ``` ` no output de Docling sem dependência de rede                           |
| 5  | DocumentConverter instanciado uma única vez (singleton via lifespan)                           | PARTIAL (deferred) | test_converter_singleton_behavior PASSOU (scope=session fixture). FastAPI lifespan não implementado — previsto Phase 6 per D-21.                          |
| 6  | Nenhum tipo docling aparece fora de adapters/extractor/ — mypy confirma boundary               | VERIFIED          | `uv run mypy src/ --strict` exits 0, 13 arquivos, zero erros. `from docling.*` em docling.py está dentro de `if TYPE_CHECKING:`. Nenhum import fora do módulo. |
| 7  | Conversão excede 120 segundos lança ExtractionTimeoutError sem travar o processo              | VERIFIED          | test_timeout_raises_extraction_timeout_error PASSOU: mock com sleep(2) + timeout=1s dispara ExtractionTimeoutError via concurrent.futures.ThreadPoolExecutor |

**Score:** 5/7 truths fully verified (2 parciais; 1 deferred para Phase 6, 1 bloqueado por fixture PDF ausente)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | Singleton via lifespan (FastAPI) | Phase 6 | D-21 no CONTEXT.md: "Phase 6 cria o converter no lifespan do FastAPI e injeta." Phase 2 entrega o contrato de injeção; lifespan em produção é Phase 6. |

### Required Artifacts

| Artifact                                               | Expected                                              | Status     | Details                                                                                                          |
|-------------------------------------------------------|-------------------------------------------------------|------------|------------------------------------------------------------------------------------------------------------------|
| `src/selection_maid/adapters/extractor/docling.py`    | DoclingAdapter + SUPPORTED_MIME_TYPES + factory       | VERIFIED   | 176 linhas; DoclingAdapter completo, build_docling_adapter, SUPPORTED_MIME_TYPES frozenset com 3 MIME types      |
| `src/selection_maid/adapters/extractor/__init__.py`   | Re-exports DoclingAdapter, build_docling_adapter      | VERIFIED   | Exports corretos: `__all__ = ["DoclingAdapter", "build_docling_adapter"]`                                        |
| `tests/adapters/extractor/conftest.py`                | Fixtures session-scoped: real_converter, pdf/docx/html | VERIFIED  | 4 fixtures session-scoped; imports Docling dentro do corpo da fixture (não no módulo top-level — D-27 correto)   |
| `tests/adapters/extractor/test_docling_adapter.py`    | Testes unit + integration                             | VERIFIED   | 14 testes coletados: 5 unitários (sempre passam), 9 de integração (6 passam, 3 pulados por falta de PDF)         |
| `tests/fixtures/sample.docx`                          | Fixture DOCX real para testes                         | VERIFIED   | 1.3MB, presente, baixado com sucesso de calibre-ebook.com                                                        |
| `tests/fixtures/sample.html`                          | Fixture HTML real para testes                         | VERIFIED   | 191KB, presente, baixado com sucesso de www.w3.org/TR/WCAG20/                                                    |
| `tests/fixtures/sample.pdf`                           | Fixture PDF real para testes                          | MISSING    | URL https://www.w3.org/WAI/WCAG21/Techniques/pdf/pdf-sample.pdf retorna HTTP 404; arquivo não foi baixado        |

### Key Link Verification

| From                                                 | To                                   | Via                                             | Status   | Details                                                                          |
|------------------------------------------------------|-------------------------------------|-------------------------------------------------|----------|----------------------------------------------------------------------------------|
| `adapters/extractor/__init__.py`                     | `adapters/extractor/docling.py`      | `from selection_maid.adapters.extractor.docling import` | WIRED | Import direto confirmado; `__all__` exporta corretamente                         |
| `DoclingAdapter.extract()`                           | `RawDocument`                        | `_build_raw_document()` helper                  | WIRED    | `RawDocument(content=..., filename=..., page_count=..., format=...)` confirmado |
| `ThreadPoolExecutor.submit()`                        | `converter.convert()`                | `future.result(timeout=self._timeout_seconds)`  | WIRED    | Padrão D-24 implementado; `ExtractionTimeoutError` lançado conforme spec         |
| `test_tables_in_docx`                               | `RawDocument.content`                | `assert '|' in result.content`                  | WIRED    | Teste passou com fixture DOCX real                                               |
| `test_lists_in_html`                                 | `RawDocument.content`               | `assert any(marker in result.content ...)`      | WIRED    | Teste passou com fixture HTML real                                               |
| `test_code_blocks`                                   | `RawDocument.content`               | `assert '` ``` `' in result.content`             | WIRED    | Teste passou com fixture HTML inline (tmp_path)                                  |
| Docling `TYPE_CHECKING` guard                        | `src/` namespace boundary            | `if TYPE_CHECKING: from docling...`             | WIRED    | `mypy --strict` 0 erros; nenhum `from docling` fora de `adapters/extractor/`    |

### Data-Flow Trace (Level 4)

| Artifact                        | Data Variable  | Source                              | Produces Real Data | Status    |
|---------------------------------|---------------|-------------------------------------|--------------------|-----------|
| `DoclingAdapter.extract()`       | `content`     | `doc.export_to_markdown()`          | Sim (Docling real)  | FLOWING   |
| `DoclingAdapter.extract()`       | `page_count`  | `len(doc.pages)` / `0` para HTML   | Sim (Docling real)  | FLOWING   |
| `_build_raw_document()`          | `RawDocument` | `result.document` (ConversionResult)| Sim                | FLOWING   |
| `test_docx_extraction`           | `result.content` | `DoclingAdapter.extract()` real  | Sim (sample.docx)   | FLOWING   |
| `test_pdf_extraction`            | `result.content` | `DoclingAdapter.extract()` real  | N/A — skipped      | SKIP      |

### Behavioral Spot-Checks

| Behavior                                        | Command                                                                         | Result                                  | Status   |
|-------------------------------------------------|---------------------------------------------------------------------------------|-----------------------------------------|----------|
| Boundary: nenhum import docling fora do adaptador | `grep -rn "from docling\|import docling" src/ --include="*.py" \| grep -v adapters/extractor/` | Nenhuma saída                  | PASS     |
| mypy strict sem erros                           | `uv run mypy src/ --strict`                                                     | `Success: no issues found in 13 source files` | PASS |
| Suite de testes extractor                       | `uv run pytest tests/adapters/extractor/ -q`                                   | `11 passed, 3 skipped in 7.40s`         | PASS     |
| Suite completa sem regressões                   | `uv run pytest tests/ -q`                                                       | `38 passed, 3 skipped in 6.66s`         | PASS     |
| DOCX retorna GFM tables                         | test_tables_in_docx (real fixture)                                             | PASSED — `|` e `---` em result.content  | PASS     |
| HTML retorna listas Markdown                    | test_lists_in_html (real fixture)                                              | PASSED — marcador de lista encontrado   | PASS     |
| HTML com `<pre><code>` retorna backticks        | test_code_blocks (fixture inline)                                              | PASSED — ` ``` ` encontrado             | PASS     |
| Timeout 120s lança ExtractionTimeoutError       | test_timeout_raises_extraction_timeout_error (mock sleep 2s, timeout=1s)       | PASSED                                  | PASS     |
| Formato inválido lança UnsupportedFormatError   | test_unsupported_format_raises                                                 | PASSED                                  | PASS     |
| PDF extraction e headings                       | test_pdf_extraction, test_headings_in_pdf                                      | SKIPPED — sample.pdf URL 404            | SKIP     |

### Requirements Coverage

| Requirement | Source Plan | Description                              | Status         | Evidence                                                        |
|-------------|-------------|------------------------------------------|----------------|-----------------------------------------------------------------|
| EXT-01      | 02-01, 02-02 | PDF aceito pelo extrator                | PARTIAL        | Lógica implementada; teste pulado por fixture ausente            |
| EXT-02      | 02-01, 02-02 | DOCX aceito pelo extrator               | VERIFIED       | test_docx_extraction PASSOU com sample.docx real                |
| EXT-03      | 02-01, 02-02 | HTML aceito pelo extrator               | VERIFIED       | test_html_extraction PASSOU com sample.html real                |
| EXT-04      | 02-03        | Headings preservados no Markdown        | PARTIAL        | Lógica: `export_to_markdown()` D-28; test_headings_in_pdf PULADO|
| EXT-05      | 02-03        | Tabelas GFM no DOCX                     | VERIFIED       | test_tables_in_docx PASSOU: `|` e `---` confirmados             |
| EXT-06      | 02-03        | Listas no HTML                          | VERIFIED       | test_lists_in_html PASSOU: marcadores confirmados               |
| EXT-07      | 02-03        | Code blocks com backticks               | VERIFIED       | test_code_blocks PASSOU: ` ``` ` confirmado com fixture inline  |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| Nenhum encontrado | — | — | — | — |

Nenhum marcador TBD/FIXME/XXX/HACK encontrado nos arquivos modificados pela Phase 2. Nenhum `return null` ou implementação vazia encontrada. Todos os handlers de erro estão corretamente implementados.

### Human Verification Required

#### 1. PDF Fixture: Headings e Extração Básica

**Test:** Substituir a URL da fixture PDF por uma funcional (ou adicionar `tests/fixtures/sample.pdf` manualmente com um PDF que contenha headings H1/H2) e executar `uv run pytest tests/adapters/extractor/ -v -k pdf`
**Expected:** `test_pdf_extraction` PASSES com `result.content` não-vazio e `result.format == "pdf"` e `result.page_count >= 1`; `test_headings_in_pdf` PASSES com `"# "` encontrado em `result.content`
**Why human:** O URL `https://www.w3.org/WAI/WCAG21/Techniques/pdf/pdf-sample.pdf` retorna HTTP 404. A escolha do PDF substituto (URL alternativa ou arquivo binário no repo) é decisão do desenvolvedor.

#### 2. Service End-to-End com PDF

**Test:** Com sample.pdf disponível, executar `uv run pytest tests/adapters/extractor/test_docling_adapter.py::TestDoclingAdapterIntegration::test_service_with_docling_adapter -v`
**Expected:** `ExtractionResult` com `result.metadata is not None` e `len(result.chunks) >= 1`
**Why human:** Depende da mesma fixture PDF — mesmo bloqueador acima.

### Gaps Summary

**Raiz do problema:** O URL da fixture PDF (`https://www.w3.org/WAI/WCAG21/Techniques/pdf/pdf-sample.pdf`) retorna HTTP 404. Como resultado, `tests/fixtures/sample.pdf` nunca foi baixado, e os 3 testes dependentes de PDF são pulados em toda execução.

**Impacto:**
- **SC-1 (PDF + headings):** O código que converte PDF e preserva headings existe e está correto (D-28 implementado, limitação H2 documentada), mas nenhuma execução de teste valida isso.
- **SC-5 (singleton via lifespan):** A metade de Phase 2 (injeção de construtor D-21, teste de identidade `adapter1._converter is adapter2._converter`) está verificada. A outra metade (FastAPI lifespan) está deferred para Phase 6 por design explícito (D-21 no CONTEXT.md).

**O que funciona (verificado com dados reais):**
- Conversão DOCX real com tabelas GFM
- Conversão HTML real com listas Markdown
- Code blocks via `<pre><code>` HTML
- Boundary architectural (nenhum tipo docling fora do adaptador)
- Timeout (ExtractionTimeoutError via ThreadPoolExecutor)
- mypy strict 0 erros

**Ação recomendada:**
1. Substituir URL da fixture PDF por uma funcional (ex: `https://www.africau.edu/images/general/sample.pdf`) ou adicionar um PDF mínimo ao repositório.
2. Confirmar que test_pdf_extraction, test_headings_in_pdf e test_service_with_docling_adapter passam após a correção.
3. Re-executar verificação para fechar SC-1.

---

_Verified: 2026-05-24T13:05:00Z_
_Verifier: Claude (gsd-verifier)_
