# Phase 13: Animation + View Transitions - Context

**Gathered:** 2026-05-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Esta fase é focada no polimento visual e na orquestração de movimentos da interface. O objetivo é garantir que a transição entre os estados (idle -> processing -> success) seja fluida e profissional, utilizando técnicas de animação baseadas em `motion-v` e transições de layout inteligentes.

</domain>

<decisions>
## Implementation Decisions

### Dinâmica de Revelação (Stagger)
- **D-01: Slide Up + Fade.** Após o sucesso da extração, os chunks de Markdown entrarão na lista um a um com um efeito de deslizamento para cima (20px) e aumento gradual de opacidade. 
- **D-02: Delay Escalonado.** O atraso (stagger) entre a entrada de cada chunk deve ser de aproximadamente 0.05s a 0.1s para criar um efeito de "cascata" sem atrasar excessivamente a visualização total.

### Transição de View (Sucesso)
- **D-03: Layout Morph (Morphing).** O card de processamento (compacto, da Phase 11) deve se transformar visualmente no card de metadados do topo (Phase 12). Utilizaremos a prop `layout` do `motion-v` para interpolar a mudança de tamanho e posição, evitando cortes bruscos na interface.

### Upgrade Visual (Drag Active)
- **D-04: Efeito Glass + Glow.** Quando um arquivo estiver sendo arrastado sobre a DropZone, a interface deve ganhar um efeito de glassmorphism (`backdrop-blur`) e uma borda com gradiente sutil de brilho (glow), reforçando a área de interação.

### Transição de Reset (Retorno)
- **D-05: Global Fade Out/In.** Ao clicar no botão de "Reset" ou "Novo Upload", a visualização de resultados deve desaparecer globalmente com um fade-out rápido, seguido pelo ressurgimento suave do card de upload original no centro da tela.

### Claude's Discretion
- Curvas de easing exatas para os efeitos de "Slide Up" e "Scale".
- Intensidade exata do efeito de blur e brilho no estado de drag.
- Duração precisa das transições globais para garantir que a interface pareça ágil e não "lenta" devido às animações.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 13 goals and dependencies.
- `.planning/REQUIREMENTS.md` — RES-02 (Stagger animation), NAV-01 (View transitions).

### Prior Context
- `.planning/phases/11-skeleton-loading-processing-feedback/11-CONTEXT.md` — Define o estado "Minimize Card" que serve de base para o morphing.
- `.planning/phases/12-result-display/12-CONTEXT.md` — Define a estrutura dos cards de chunks e metadados que serão animados.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `motion-v`: Biblioteca mandatória para todas as animações complexas e transições de layout.
- `Tailwind v4`: Utilizado para os efeitos de glassmorphism (`backdrop-blur`) e gradientes de borda.
- `useUpload`: Estado reativo que dispara as mudanças de fase da animação.

### Established Patterns
- **Layout Animations**: Uso da prop `layout` do Motion-v para transições entre diferentes estados de componentes.
- **Dark Mode**: As animações de glow e glassmorphism devem ser calibradas para o tema escuro (cores OKLCH).

### Integration Points
- `frontend/src/App.vue`: Ponto central onde as transições de view principais são orquestradas.
- `frontend/src/components/upload/DropZone.vue`: Receberá o upgrade visual do estado de drag.
- Componentes de Resultado (Phase 12): Devem suportar as props de animação do `motion-v` para o efeito de stagger.

</code_context>

<specifics>
## Specific Ideas

- "O movimento de morphing entre o card de processamento e o de metadados é a chave para a interface parecer uma aplicação 'premium'."
- O efeito de stagger deve ser aplicado à lista de chunks, mas o card de metadados (topo) deve entrar primeiro ou junto com o início da sequência.

</specifics>

<deferred>
## Deferred Ideas

- Animações micro-interativas em botões individuais (além do copy feedback).
- Temas visuais dinâmicos baseados no tipo de arquivo (ex: azul para PDF, verde para DOCX).

</deferred>

---

*Phase: 13-Animation + View Transitions*
*Context gathered: 2026-05-26*
