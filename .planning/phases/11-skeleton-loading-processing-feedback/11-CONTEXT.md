# Phase 11: Skeleton Loading + Processing Feedback - Context

**Gathered:** 2026-05-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Esta fase entrega o feedback visual contínuo durante o processamento do documento pelo backend. O objetivo é eliminar o "tempo morto" percebido pelo usuário, substituindo o spinner estático por skeletons animados que representam os chunks sendo gerados, além de exibir um cronômetro de tempo decorrido para indicar atividade.

</domain>

<decisions>
## Implementation Decisions

### Transição de Layout (Processamento)
- **D-01: Minimização do Card.** Ao iniciar o processamento, o Card de upload deve "subir" ou diminuir de tamanho para abrir espaço para a lista de skeletons abaixo. Isso prepara visualmente a interface para o resultado final em lista (Phase 12).

### Granularidade dos Skeletons
- **D-02: Cards Atômicos.** Em vez de um bloco único, o placeholder deve consistir em 3-5 skeletons em formato de "card", simulando a estrutura de múltiplos chunks que o SelectionMaid devolve.
- **D-03: Animação Shimmer.** Uso de um gradiente linear animado (sweeping gradient) via Motion-v ou CSS keyframes para comunicar processamento ativo.

### Exibição do Cronômetro (Timer)
- **D-04: Contador Proeminente.** O tempo decorrido deve ser exibido de forma central e clara (ex: "Processando... 00:12") para que o usuário tenha certeza de que o sistema não travou.
- **D-05: Precisão.** O contador deve atualizar a cada segundo enquanto o status for `processing`.

### Claude's Discretion
- Estilo exato do shimmer (velocidade, ângulo do gradiente).
- Número exato de skeletons mostrados (3 a 5 conforme melhor se ajuste ao layout).
- Micro-interação de "minimizar" o card de upload.

</decisions>

<specifics>
## Specific Ideas

- O cronômetro deve começar do zero assim que o status mudar de `uploading` para `processing`.
- "Quero que pareça que o sistema já está montando a lista, só esperando o texto chegar."

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 11 goals, success criteria, and dependencies.
- `.planning/REQUIREMENTS.md` — PROC-02 (Skeleton shimmer placeholders).

### Existing Logic
- `frontend/src/composables/useUpload.ts` — State machine defining `uploading` and `processing` states.
- `frontend/src/components/upload/DropZone.vue` — Current host of the processing UI (to be refactored/extended).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/components/ui/card`: Base para os skeletons de chunks.
- `motion-v`: Biblioteca já estabelecida para animações no projeto.
- `useUpload`: Composable que fornece o estado necessário para disparar o timer.

### Established Patterns
- **State-driven UI**: A exibição dos skeletons deve ser condicionada estritamente ao estado `processing`.
- **Dark Mode**: Manter o estilo minimalista dark.

### Integration Points
- `frontend/src/App.vue` ou `DropZone.vue` → O layout precisará ser ajustado para permitir a expansão da lista de skeletons abaixo do ponto de upload.

</code_context>

<deferred>
## Deferred Ideas

- Renderização real do Markdown (Phase 12).
- Animação de revelação "staggered" após o sucesso (Phase 13).

</deferred>

---

*Phase: 11-skeleton-loading-processing-feedback*
*Context gathered: 2026-05-26*
