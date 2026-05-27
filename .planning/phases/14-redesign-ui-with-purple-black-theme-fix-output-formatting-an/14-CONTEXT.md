# Phase 14: Redesign UI with purple/black theme, fix output formatting, and add Markdown download - Context

**Gathered:** 2026-05-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Esta fase entrega três melhorias relacionadas à interface visual do SelectionMaid:
1. **Redesign visual completo** — nova paleta roxa/preta como produto final, substituindo o dark mode minimalista atual por um visual mais premium.
2. **Correção da formatação do output** — fix do Markdown renderer para tabelas, código com syntax highlight, headers com hierarquia, scroll horizontal, e altura máxima nos chunks.
3. **Download do resultado em .md** — botão global para baixar todos os chunks + botão por chunk individual.

</domain>

<decisions>
## Implementation Decisions

### Paleta de Cores

- **D-01: Fundo principal #111118** — Preto-grafite com leve tom roxo-azulado. Substituir o `--bg: #16171d` atual por `#111118`.
- **D-02: Roxo néon como cor de destaque** — `#9333ea` (purple-600) como `--accent`. Usado em bordas, botões, glows e destaques.
- **D-03: Cards com glassmorphism roxo** — ChunkCards e MetadataCard com fundo semi-transparente (`bg-white/5` ou equivalente OKLCH) e borda roxa sutil (`border-purple-900/40`).
- **D-04: Botão primário ghost roxo** — Estilo outline: borda roxa + texto roxo em idle, fill roxo completo no hover. Substituir o estilo `variant="outline"` atual para refletir a nova paleta.
- **D-05: DropZone idle com borda neutra + hover roxo** — Estado idle fica neutro (borda cinza), borda muda para roxa quando o mouse está sobre a zona ou durante drag.
- **D-06: Gradiente roxo-branco no título principal** — O `h1` "Transforme documentos em chunks Markdown" recebe gradient text (roxo para branco) via `bg-gradient-to-r from-purple-400 to-white bg-clip-text text-transparent`.
- **D-07: Glow roxo nos ChunkCards ao hover** — `box-shadow` roxo sutil (`shadow-purple-900/30`) ativado no `:hover` dos ChunkCards. MetadataCard sem glow.
- **D-08: Scrollbar customizada roxo/transparente** — CSS `scrollbar-color` e `scrollbar-width` com tom roxo em toda a aplicação.
- **D-09: Erro vermelho (#ef4444) | Processando roxo pulsante** — Estado de erro usa vermelho (#ef4444). Estado de processamento usa roxo (`#9333ea`) com animação de pulso CSS.

### Formatação do Output (MarkdownRenderer)

- **D-10: Tabelas sem estilo → bordas roxas sutis + header roxo escuro** — Adicionar classes Tailwind prose para tabelas: `prose-table:border prose-table:border-purple-900/40`, header da tabela com `bg-purple-950/60` e texto claro.
- **D-11: Tabelas largas → scroll horizontal dentro do card** — Wrapper com `overflow-x-auto` ao redor das tabelas no MarkdownRenderer.
- **D-12: Syntax highlight com highlight.js via markdown-it** — Integrar `markdown-it-highlightjs` para blocos de código. Tema escuro compatível com a paleta (ex: `github-dark` ou `atom-one-dark`).
- **D-13: Links abrem em nova aba** — Configurar `markdown-it` com `target="_blank"` e `rel="noopener noreferrer"` em todos os links renderizados.
- **D-14: Altura máxima dos ChunkCards com scroll interno** — `max-h-[400px] overflow-y-auto` na área de conteúdo do ChunkCard (não no card inteiro — só no corpo do Markdown).
- **D-15: Imagens Markdown renderizadas normalmente** — `<img>` tags com `max-width: 100%` e `height: auto` via prose styling.

### Download do .MD

- **D-16: Ambos: download global + por chunk** — Botão global no header da ResultView + ícone de download por ChunkCard.
- **D-17: Download global no header da ResultView** — Botão "Download .MD" posicionado no header da ResultView, ao lado do botão "Novo Upload" existente.
- **D-18: Nome do arquivo: `{filename-slug}-chunks.md`** — O nome do arquivo baixado é gerado a partir do `source_filename` da API (slugificado), ex: `calendario-provas-2026-chunks.md`.
- **D-19: Formato do .md gerado** — Front-matter YAML no topo com campos `title`, `language`, `doc_type`, `ingested_at`, `chunk_count`. Seguido pelos chunks separados por `---` com header `# Chunk N` e metadata de página antes de cada conteúdo.
- **D-20: Botão por chunk** — Ícone `DownloadIcon` (da Lucide) ao lado do botão "Copiar" existente em cada ChunkCard. Icon-only, sem label.
- **D-21: Feedback visual do botão de download** — Ao clicar, muda para `CheckIcon` por 1.5s, igual ao comportamento do botão "Copiar" atual (via `useClipboard` pattern, mas para download).

### Claude's Discretion

- Tipografia: manter fontes do sistema (`system-ui`) ou ajustar — planner decide.
- Intensidade exata do glassmorphism (backdrop-blur e opacidade do fundo dos cards).
- Curvas de easing e timing do pulso roxo no processamento.
- Espaçamento e padding exatos do prose no MarkdownRenderer.
- Tema exato do highlight.js (preferência por dark, paleta roxa).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Componentes Existentes
- `frontend/src/components/result/ChunkCard.vue` — Card de chunk atual; glassmorphism e glow devem ser adicionados aqui.
- `frontend/src/components/result/MetadataCard.vue` — Card de metadados; glassmorphism sem glow.
- `frontend/src/components/result/MarkdownRenderer.vue` — Renderer atual com markdown-it; syntax highlight e table styling aqui.
- `frontend/src/components/result/ResultView.vue` — Layout da tela de resultado; botão global de download vai aqui.
- `frontend/src/components/upload/DropZone.vue` — DropZone; ajuste do hover state roxo.

### Estilos e Tema
- `frontend/src/style.css` — CSS variables `--bg`, `--accent`, `--border`, `--text`; scrollbar custom aqui.
- `frontend/src/App.vue` — Layout raiz; gradiente do h1 e bg principal.

### Composables e Utilitários
- `frontend/src/composables/useUpload.ts` — Estado da máquina; `source_filename` disponível no `success.data.metadata`.
- `frontend/src/types/api.ts` — `ExtractionResponse`, `DocumentMetadata`, `Chunk`; campos disponíveis para front-matter YAML.
- `frontend/src/lib/formatters.ts` — Utilitários de formatação existentes; função de slugify provavelmente precisa ser adicionada.

### Roadmap e Requisitos
- `.planning/ROADMAP.md` — Phase 14 goals.
- `.planning/REQUIREMENTS.md` — RES-01 (Markdown rendering), RES-03 (Copy button), RES-04 (Metadata panel).

### Contexto de Fases Anteriores
- `.planning/phases/12-result-display/12-CONTEXT.md` — Decisões de ChunkCard e MetadataCard (markdown-it, estrutura dos cards).
- `.planning/phases/13-animation-view-transitions/13-CONTEXT.md` — Padrões de animação estabelecidos (motion-v, glassmorphism, OKLCH).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `useClipboard` (@vueuse/core): Padrão de feedback visual já implementado no ChunkCard (Check icon por 2s). O botão de download deve seguir o mesmo padrão com `useState` booleano em vez de useClipboard.
- `Card` (shadcn-vue): Base dos cards. Glassmorphism via classes adicionais, sem modificar o componente shadcn.
- `Button` (shadcn-vue): Botão de ação existente. Ajustar via CSS variables globais para refletir a nova paleta.
- `lucide-vue-next`: `DownloadIcon`, `CheckIcon`, `CopyIcon` já instalados.
- `motion-v`: Estabelecido para animações. Manter padrão existente.

### Established Patterns
- **CSS Variables em style.css**: Tema inteiro controlado por `--bg`, `--accent`, `--border` etc. Redesign deve atualizar essas variáveis para dark mode (`:root` sem media query — dark mode é fixo).
- **prose prose-invert**: Tailwind Typography já em uso no MarkdownRenderer. Extensão via classes `prose-table:*`, `prose-code:*`, `prose-a:*`.
- **Glassmorphism OKLCH**: Pattern já estabelecido na Phase 13 (D-04 do 13-CONTEXT). Cards usam `backdrop-blur` + borda OKLCH. Aplicar aqui nos ChunkCards.

### Integration Points
- `frontend/src/components/result/ResultView.vue` → Adicionar botão Download .MD no header (linha da div com "Novo Upload").
- `frontend/src/components/result/ChunkCard.vue` → Adicionar DownloadIcon ao lado do CopyIcon; glassmorphism; glow hover.
- `frontend/src/components/result/MarkdownRenderer.vue` → Adicionar markdown-it-highlightjs e ajustar classes prose.
- `frontend/src/style.css` → Atualizar CSS variables `--bg`, `--accent`, `--border`, adicionar scrollbar custom.
- `frontend/src/App.vue` → Gradient no h1 e ajuste do fundo principal.

</code_context>

<specifics>
## Specific Ideas

- "O efeito de glow nos ChunkCards ao hover reforça que cada card é uma unidade clicável/interativa."
- Gradient text no h1: `bg-gradient-to-r from-purple-400 to-white bg-clip-text text-transparent`.
- O front-matter YAML do .md baixado segue o padrão RAG-ready: metadados no topo + chunks separados por `---` com headers informativos.
- O botão de download por chunk é icon-only (DownloadIcon) — sem label — para não poluir o header de cada card que já tem o botão "Copiar".

</specifics>

<deferred>
## Deferred Ideas

- **Alternância raw/renderizado por chunk** — Botão para ver o Markdown bruto vs renderizado em cada ChunkCard. Seria um toggle interessante mas adiciona complexidade fora do escopo desta fase.
- **Temas dinâmicos por tipo de arquivo** — Azul para PDF, verde para DOCX etc. Deferred para v3.0.
- **Números de linha no código** — highlight.js suporta, mas adiciona complexidade de estilo sem valor proporcional agora.
- **Tipografia customizada** — Inter, Geist ou similar. Planner pode incluir se considerar simples; caso contrário, deferred.

</deferred>

---

*Phase: 14-redesign-ui-with-purple-black-theme-fix-output-formatting-an*
*Context gathered: 2026-05-26*
