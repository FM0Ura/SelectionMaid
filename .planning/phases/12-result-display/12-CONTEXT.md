# Phase 12: Result Display - Context

**Gathered:** 2026-05-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Esta fase entrega a visualização dos resultados do processamento do documento. O objetivo é renderizar os chunks extraídos em formato Markdown, permitir a cópia individual de cada chunk e exibir os metadados do documento (título, idioma, tipo, etc.) de forma estruturada.

</domain>

<decisions>
## Implementation Decisions

### Renderização de Markdown
- **D-01:** Utilização da biblioteca **markdown-it** para renderizar o conteúdo dos chunks. Esta escolha garante flexibilidade e suporte a extensões caso necessário no futuro.

### Painel de Metadados
- **D-02:** Os metadados do documento serão exibidos em um **Top Card** posicionado no início da lista de resultados. Este card rolará junto com os chunks, apresentando o contexto do arquivo processado.

### Detalhamento dos Chunks
- **D-03:** Cada card de chunk será **Detalhado**, incluindo:
    - Conteúdo Markdown renderizado.
    - Título da Seção (se disponível).
    - Intervalo de páginas (`page_start` a `page_end`).
    - Contagem de palavras.
    - Botão de "Copiar para área de transferência" com feedback visual.

### Claude's Discretion
- Estilo visual específico dos cards de chunk (bordas, sombras, espaçamento) seguindo o dark mode minimalista.
- Implementação exata do feedback visual do botão de cópia (ex: mudança temporária de ícone).
- Ordenação e rotulagem exata dos campos de metadados no card de topo.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 12 goals and success criteria.
- `.planning/REQUIREMENTS.md` — RES-01 (Markdown rendering), RES-03 (Copy button), RES-04 (Metadata panel).

### Data Schemas
- `frontend/src/types/api.ts` — Definition of `ExtractionResponse`, `DocumentMetadata`, and `Chunk`.

### Existing Logic
- `frontend/src/composables/useUpload.ts` — State machine containing the `success` state and extraction data.
- `frontend/src/App.vue` — Main layout where the result list will be integrated.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/components/ui/card`: Base para os cards de metadados e chunks.
- `frontend/src/components/ui/button`: Utilizado para o botão de cópia.
- `motion-v`: Biblioteca para transições suaves na entrada dos resultados.

### Established Patterns
- **State-driven UI**: A lista de resultados deve ser exibida apenas quando `upload.state.value.status === 'success'`.
- **Dark Mode**: Manter o estilo visual minimalista e escuro já estabelecido.

### Integration Points
- `frontend/src/App.vue` → Substituir ou expandir a seção de processamento para exibir a lista de resultados após o sucesso.
- `frontend/src/composables/useUpload.ts` → Consumir o objeto `data` dentro do estado `success`.

</code_context>

<specifics>
## Specific Ideas

- "Quero que as informações de página e título de seção ajudem a dar contexto de onde aquele texto veio no documento original."
- O card de metadados deve incluir o tempo de processamento (`elapsedSeconds` capturado na Phase 11).

</specifics>

<deferred>
## Deferred Ideas

- Animação "staggered" na revelação dos chunks (Phase 13).
- Transições de view animadas entre telas (Phase 13).

</deferred>

---

*Phase: 12-Result Display*
*Context gathered: 2026-05-26*
