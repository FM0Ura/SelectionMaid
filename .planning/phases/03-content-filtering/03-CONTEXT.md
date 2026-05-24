# Phase 3: Content Filtering - Context

**Gathered:** 2026-05-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 entrega `HeuristicFilter` — a implementação concreta de `FilterPort` que recebe o `RawDocument` produzido pelo `DoclingAdapter` e devolve uma cópia limpa: sem headers/footers repetidos detectados por frequência, sem linhas isoladas de número de página, e sem sequências excessivas de linhas em branco. O filtro opera sobre o `RawDocument.content` (blob Markdown único) e retorna um novo `RawDocument` com o mesmo schema.

Esta fase também entrega o módulo de configuração `selection_maid.config`, que lê `config.toml` na raiz do projeto e provê valores resolvidos (com defaults hardcoded como fallback) para todos os adaptadores configuráveis.

**Não inclui:** chunking (Phase 4), enriquecimento de metadados (Phase 5), interface HTTP (Phase 6). Não muda o domínio — nenhum tipo novo, nenhum port novo.

</domain>

<decisions>
## Implementation Decisions

### FILT-01: Detecção de Headers/Footers

- **D-31:** Estratégia principal: confiar no Docling (que já detecta e remove headers/footers de PDFs via modelos de layout AI). O `HeuristicFilter` implementa apenas um _safety net_ para casos que o Docling não cobriu.
- **D-32:** O safety net de frequência funciona sobre o blob Markdown inteiro (sem page boundaries, pois `RawDocument.content` é uma única string). Candidatos a header/footer: linhas com ≤ 80 caracteres que aparecem 3 ou mais vezes no documento.
- **D-33:** Exclusões do safety net: linhas que começam com `#` (headings Markdown) e linhas que contêm `|` (linhas de tabela GFM) nunca são removidas, mesmo que se repitam 3+ vezes. Isso evita falsos positivos em seções de título repetido e tabelas com linha separadora.
- **D-34:** O threshold 3 (mínimo de repetições) mapeia para a heurística "3+ páginas consecutivas" do FILT-01: em documentos PDF digitais típicos, headers/footers repetem pelo menos 3 vezes se o documento tem 3+ páginas. Para documentos muito curtos (< 3 páginas), o safety net pode não disparar — aceito para v1.

### FILT-02: Remoção de Linhas de Número de Página

- **D-35:** Padrão amplo de número de página, cobrindo: números puros (`^\d+$`), números romanos (`^[IVXLCDMivxlcdm]+$` com limite de comprimento razoável para evitar falsos positivos), e variações com hífen (`^-\s*\d+\s*-$`, `^- [IVXLCDM]+ -$`). Regex compilado como constante de módulo.
- **D-36:** Escopo: apenas linhas **completamente isoladas** — a linha inteira (strip) corresponde ao padrão. Números que aparecem inline em parágrafos (ex: "Ver item 42") não são afetados. Strip de whitespace antes da comparação.

### FILT-03: Compressão de Whitespace

- **D-37:** Sequências de 2 ou mais linhas em branco consecutivas são comprimidas para exatamente 1 linha em branco. Aplicado via regex `\n{3,}` → `\n\n` no conteúdo final (após as outras regras). Linha em branco = linha que contém só whitespace (ou vazia).

### Configurabilidade

- **D-38:** Um módulo `selection_maid.config` (em `src/selection_maid/config.py`) lê `config.toml` na raiz do projeto e provê valores resolvidos para todos os adaptadores. Se `config.toml` não existe ou não contém a chave, usa defaults hardcoded definidos no módulo — sem falha de startup.
- **D-39:** `HeuristicFilter` recebe seus thresholds via injeção de construtor: `HeuristicFilter(min_repeat: int = 3, max_line_len: int = 80)`. A camada `selection_maid.config` resolve os valores do TOML e os injeta; testes passam valores diretamente sem depender do arquivo TOML.
- **D-40:** Seção no `config.toml` para o filtro: `[filter]` com chaves `min_repeat` e `max_line_len`. O módulo de config também será o ponto central para configuração de fases futuras (chunker, enricher).

### Estrutura do Arquivo do Adaptador

- **D-41:** `HeuristicFilter` vive em `src/selection_maid/adapters/filter/heuristic.py` — mesmo padrão do `DoclingAdapter` em `adapters/extractor/docling.py`. O `__init__.py` do subpacote importa a classe para expô-la (se necessário).

### Estrutura e Estratégia de Testes

- **D-42:** Fixtures de teste são strings Markdown inline no código de teste — sem arquivos `.md` externos. O `filter()` recebe `RawDocument(content=..., ...)` com Markdown embutido, o que é self-contained e independente de arquivo.
- **D-43:** Uma classe de teste por regra: `TestFILT01Headers`, `TestFILT02PageNumbers`, `TestFILT03Whitespace`, e `TestContentPreservation`. Cada classe testa sua regra em isolamento.
- **D-44:** `TestContentPreservation` verifica que os seguintes elementos sobrevivem ao filtro sem alteração: headings (H1, H2, H3), parágrafos com texto, tabelas GFM, e listas ordenadas/não-ordenadas. Cada elemento é verificado como presente no conteúdo filtrado.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 3 goal, success criteria (4 itens: FILT-01/02/03 + preservação de conteúdo), e planos pré-definidos (03-01, 03-02, 03-03).
- `.planning/REQUIREMENTS.md` — FILT-01 ("headers e footers que se repetem em múltiplas páginas"), FILT-02 ("linhas isoladas com apenas número de página"), FILT-03 ("sequências excessivas de linhas em branco comprimidas para no máximo uma").

### Decisões herdadas das fases anteriores
- `.planning/phases/01-domain-foundation/01-CONTEXT.md` — D-10 (FilterPort.filter signature), D-16 (exception wrapping pattern), D-18 (FilterError code "FILT-001").
- `.planning/phases/02-docling-extraction-adapter/02-CONTEXT.md` — D-03/D-04 (directory structure), D-23 (factory function pattern), padrão de injeção de construtor.

### Domain Contracts (código existente)
- `src/selection_maid/domain/ports.py` — `FilterPort.filter(self, document: RawDocument) -> RawDocument` — assinatura locked. HeuristicFilter deve satisfazer este Protocol sem herança.
- `src/selection_maid/domain/models.py` — `RawDocument` (content: str, filename: str, page_count: int, format: str) — campos exatos que HeuristicFilter recebe e retorna.
- `src/selection_maid/errors.py` — `FilterError` com code `"FILT-001"` já definida — HeuristicFilter lança esta classe em falhas internas.

### Tech Stack
- `CLAUDE.md` §Technology Stack e §Constraints — Python 3.13+, uv, mypy strict, ruff.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/selection_maid/errors.py` — `FilterError` pronta para uso. HeuristicFilter importa e lança diretamente.
- `tests/stubs/adapters.py` — `StubFilter` (passthrough) existe. HeuristicFilter é a implementação real; `StubFilter` continua sendo usado nos testes de outras fases para substituir o filtro.

### Established Patterns
- **Injeção de construtor:** `DoclingAdapter.__init__(self, converter, timeout_seconds)` — `HeuristicFilter.__init__(self, min_repeat, max_line_len)` segue o mesmo padrão.
- **Exception wrapping D-16:** `try/except` em cada chamada de port. HeuristicFilter aplica o padrão internamente: exceções inesperadas são capturadas e relançadas como `FilterError`.
- **Factory function D-23:** Considerar `build_heuristic_filter(config: FilterConfig) -> HeuristicFilter` para consistência com `build_docling_adapter()` e futuro `build_router()`.

### Integration Points
- `src/selection_maid/adapters/filter/__init__.py` — vazio. `HeuristicFilter` vai em `adapters/filter/heuristic.py`.
- `tests/adapters/filter/__init__.py` — vazio. Testes vão em `tests/adapters/filter/test_heuristic_filter.py`.
- **Novo:** `src/selection_maid/config.py` — novo módulo de configuração central. Não existia antes desta fase.
- O `ExtractionService` em `src/selection_maid/service.py` recebe `FilterPort` via injeção — nenhuma mudança necessária lá.

</code_context>

<specifics>
## Specific Ideas

- O safety net de frequência (D-32) deve processar as linhas com strip de whitespace antes de comparar — headers/footers com espaços variáveis são normalizados.
- Para números romanos (D-35): limitar o padrão a strings de 1-10 caracteres para evitar falsos positivos em siglas longas (ex: "MCMLXXXIX" é um ano, não número de página).
- O módulo `selection_maid.config` (D-38/D-40) deve usar `tomllib` (stdlib Python 3.11+, disponível no Python 3.13) — sem dependência externa para parsing TOML.
- A ordem de aplicação das regras no `filter()`: (1) safety net de frequência para headers/footers, (2) remoção de números de página, (3) compressão de whitespace. Esta ordem evita que a compressão de whitespace interfira na detecção de frequência.

</specifics>

<deferred>
## Deferred Ideas

- **OCR artifact removal** — remoção de artefatos de OCR (caracteres inválidos, sequências de símbolos sem sentido). Mencionado como potencial extensão do filtro; requer fixtures de OCR real. Candidato para Phase 7 (Integration Hardening) ou v2.
- **Configuração de filtros por tipo de documento** — diferentes thresholds para PDFs de relatório vs artigos vs formulários. Requer META-03 (doc_type) que só existe após Phase 5. Candidato para v2.

</deferred>

---

*Phase: 3-Content Filtering*
*Context gathered: 2026-05-24*
