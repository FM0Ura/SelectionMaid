# Phase 10: Upload Interaction - Context

**Gathered:** 2026-05-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Esta fase entrega a interface de interação inicial com o sistema: o componente de DropZone para upload de arquivos. O objetivo é fornecer um feedback visual rico e animado durante o drag-and-drop, permitir a seleção manual de arquivos e gerenciar os estados iniciais de boas-vindas e erro estruturado antes e durante o processamento.

</domain>

<decisions>
## Implementation Decisions

### DropZone Scope & Boundary
- **D-01:** O DropZone será um componente centralizado (estilo Card), focando a atenção do usuário no centro da tela, em vez de um drop zone de página inteira.

### Animation implementation details
- **D-02:** Utilização de **Motion-v** (Framer Motion para Vue) para o feedback visual de 'border pulse' e transições do overlay de drop. O motion-v permite coreografias mais suaves e integradas ao estado reativo do Vue.

### Empty and Error states layout
- **D-03:** Os estados de 'Boas-vindas' (NAV-03) e 'Erro' (NAV-02) serão implementados como estados internos dentro do Card de upload. Isso mantém o layout da aplicação estável, alterando apenas o conteúdo interno do contêiner conforme o estado da máquina de estados (`idle`, `error`, etc.).

### File selection behavior details
- **D-04:** O sistema suporta apenas um arquivo por vez (limitação do backend v1.0). Se o usuário arrastar múltiplos arquivos, o sistema deve bloquear a operação imediatamente e mostrar uma mensagem de erro pedindo o envio de apenas um arquivo.

### Claude's Discretion
- Detalhes específicos de micro-interações (ex: intensidade do pulse, timing do fade-in do overlay) ficam a critério da implementação, seguindo o estilo minimalista dark mode.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 10 goal and success criteria.
- `.planning/REQUIREMENTS.md` — UPL-01 (Drag & Drop), UPL-02 (Button select), NAV-02 (Error UI), NAV-03 (Welcome screen).

### Existing Logic (Source of Truth for State)
- `frontend/src/composables/useUpload.ts` — Máquina de estados (`dragging`, `idle`, `error`, etc.) e funções `setDragging`, `startUpload`.
- `frontend/src/lib/validators.ts` — Lógica de validação de tamanho (50MB) e tipo (PDF/DOCX/HTML).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/composables/useUpload.ts`: Fornece a lógica reativa para gerenciar o estado de upload e dragging.
- `frontend/src/lib/validators.ts`: Funções puras para validar arquivos antes do envio.
- `frontend/src/components/ui/button`: Componente shadcn pronto para uso no botão de seleção manual.

### Established Patterns
- **Motion-v**: Uso confirmado para animações de interação.
- **Dark Mode**: Fixo via classe `dark` no elemento raiz.
- **State-driven UI**: A interface deve reagir estritamente ao estado retornado por `useUpload`.

### Integration Points
- `frontend/src/App.vue` → Será o hospedeiro do novo componente de DropZone que encapsulará as interações desta fase.

</code_context>

<specifics>
## Specific Ideas

- O erro de múltiplos arquivos deve ser tratado localmente antes de invocar `startUpload` ou refletido como um estado de erro específico na UI.
- O botão de retry (NAV-02) deve chamar a função `reset` ou permitir uma nova seleção de arquivo no mesmo Card.

</specifics>

<deferred>
## Deferred Ideas

- Visualização de chunks e metadados (Phases 11-13).
- Skeleton shimmer durante o processamento (Phase 11).

### Reviewed Todos (not folded)
None — discussion stayed within phase scope

</deferred>

---

*Phase: 10-Upload Interaction*
*Context gathered: 2026-05-26*
