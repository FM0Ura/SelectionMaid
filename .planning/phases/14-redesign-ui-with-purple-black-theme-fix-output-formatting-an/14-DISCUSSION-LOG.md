# Phase 14: Redesign UI with purple/black theme, fix output formatting, and add Markdown download - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-26
**Phase:** 14-redesign-ui-with-purple-black-theme-fix-output-formatting-an
**Areas discussed:** Paleta roxa/preta, Formatação do output, Download do .MD

---

## Paleta roxa/preta

| Option | Description | Selected |
|--------|-------------|----------|
| Preto puro (#0a0a0a) | Fundo quase preto, muito contraste com o roxo. Visual mais agressivo e premium. | |
| Preto-grafite (#111118) | Fundo escuro com tom leve de azúl-roxo. Mais suave e sofisticado. | ✓ |
| Mantém o atual (#16171d) | Já é escuro, só mudar o roxo e os outros elementos. | |

**User's choice:** Preto-grafite (#111118)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Roxo vibrante (#7c3aed / violet-700) | Roxo saturado clássico, bastante visível sobre o fundo preto. | |
| Roxo néon (#9333ea / purple-600) | Um pouco mais brilhante, efeito de glow mais pronunciado. | ✓ |
| Roxo suave (#a78bfa / violet-400) | Mais claro e pastel, menos agressivo sobre fundo escuro. | |

**User's choice:** Roxo néon (#9333ea / purple-600) como `--accent` principal.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Fundo semi-transparente com borda roxa sutil | Glassmorphism leve: bg rgba + border roxo tênue. | ✓ |
| Fundo sólido escuro + borda neutra | Mais limpo, sem efeitos de transparência. | |
| Você decide | Deixa o pesquisador/planner escolher o estilo dos cards. | |

**User's choice:** Glassmorphism roxo nos ChunkCards e MetadataCard.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Fundo roxo sólido + texto branco | Clássico e direto. Botão chamativo. | |
| Borda roxa + texto roxo + hover com fill roxo | Estilo ghost/outline, mais sutil. Efeito premium de hover. | ✓ |
| Gradiente roxo-para-violeta | Gradiente no background do botão. | |

**User's choice:** Ghost/outline roxo com fill no hover para botões primários.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Borda tracejada roxa + fundo transparente | Borda dashed com a cor roxa definida. Chamativo em idle. | |
| Borda sólida neutra com hover roxo | Borda cinza, só fica roxa quando o usuário passa o mouse. | ✓ |
| Você decide | Deixa o planner escolher o estado idle da DropZone. | |

**User's choice:** DropZone com borda neutra em idle, roxa no hover.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Título com gradiente roxo-branco | O h1 principal fica com gradient text (roxo para branco). | ✓ |
| Branco normal com 'Selection' em roxo | Apenas a palavra 'Selection' fica colorida de roxo no título. | |
| Texto branco simples | Sem destaque especial. | |

**User's choice:** Gradient text roxo-branco no h1 principal.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Sim, scrollbar personalizada roxo/transparente | CSS scrollbar-color com roxo. Detalhe de acabamento premium. | ✓ |
| Não, mantém o padrão do sistema | Menos CSS pra manter, foco nas mudanças principais. | |
| Você decide | Planner decide sobre esses microdetalhes. | |

**User's choice:** Scrollbar customizada roxo/transparente em toda a aplicação.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Só nos ChunkCards ao hover | Apenas os cards de chunk ficam com glow roxo ao passar o mouse. | ✓ |
| ChunkCards + MetadataCard | Todos os cards principais ficam com glow ao hover. | |
| Você decide | Planner decide onde aplicar o glow. | |

**User's choice:** Glow roxo somente nos ChunkCards ao hover.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Erro: vermelho (#ef4444) / Processando: roxo pulsante | Cores clássicas. Erro em vermelho, processamento em roxo com pulso. | ✓ |
| Erro: coral/laranja (#f97316) / Processando: roxo neutro | Laranja para erro, roxo neutro para processamento. | |
| Você decide | Planner escolhe as cores de status. | |

**User's choice:** Erro vermelho (#ef4444), processando roxo pulsante.

---

## Formatação do output

**Problemas identificados:** Tabelas sem estilo, código sem syntax highlight, espaçamento/padding ruim, headers sem hierarquia visual.

| Option | Description | Selected |
|--------|-------------|----------|
| highlight.js integrado ao markdown-it | Plugin markdown-it-highlightjs. Simples, suporta muitas linguagens. | ✓ |
| Shiki (servidor-side highlighting) | Qualidade premium, mas mais pesado. | |
| CSS simples sem highlight | Só estilizar o fundo do bloco de código sem colorir sintaxe. | |

**User's choice:** highlight.js via markdown-it-highlightjs.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Bordas roxas sutis + header roxo escuro | Tabelas com bordas na paleta roxa, header roxo escuro. | ✓ |
| Bordas neutras + zebra striping escuro | Bordas cinza, linhas alternadas. | |
| Sem borda, só separadores horizontais | Estilo minimalista. | |

**User's choice:** Tabelas com bordas roxas e header roxo escuro.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Scroll horizontal dentro do card | A tabela fica scrollável horizontalmente dentro do ChunkCard. | ✓ |
| Reduzir fonte da tabela automaticamente | Tabela encolhe o texto para caber no container. | |
| Você decide | Planner decide sobre overflow de tabelas. | |

**User's choice:** Scroll horizontal para tabelas largas.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Nova aba (_blank) com rel=noopener | Padrão seguro. Link abre em nova aba. | ✓ |
| Mesma aba | Link abre na mesma aba. | |

**User's choice:** Links abrem em nova aba com rel=noopener.

---

| Option | Description | Selected |
|--------|-------------|----------|
| 600px com scroll interno | max-h-[600px] e overflow-y-auto. | |
| 400px com scroll interno | Mais compacto, mais densidade de chunks na tela. | ✓ |
| Sem limite (scroll da página) | Card cresce livremente. | |

**User's choice:** max-h-[400px] com scroll interno na área de conteúdo do ChunkCard.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Renderizadas normalmente (img tag) com max-width: 100% | Imagens aparecem no card. | ✓ |
| Não renderizar imagens — mostrar o texto alt | Substituídas pelo texto alternativo. | |
| Você decide | Planner decide sobre imagens nos chunks. | |

**User's choice:** Imagens renderizadas normalmente com max-width: 100%.

---

## Download do .MD

| Option | Description | Selected |
|--------|-------------|----------|
| Download de todos os chunks em um único .md | Botão global que gera um único arquivo com todos os chunks. | |
| Download por chunk individual | Cada ChunkCard tem seu próprio botão de download. | |
| Ambos: download global + download por chunk | Botão global na tela de resultado + botão por chunk em cada card. | ✓ |

**User's choice:** Ambos — download global + por chunk.

---

| Option | Description | Selected |
|--------|-------------|----------|
| No header da ResultView, ao lado de 'Novo Upload' | Botão 'Download .MD' no topo da página de resultados. | ✓ |
| Flutuante fixo no canto inferior direito | Botão flutuante (FAB). | |
| No MetadataCard | Botão de download junto com as informações de metadados. | |

**User's choice:** Botão global no header da ResultView ao lado de "Novo Upload".

---

| Option | Description | Selected |
|--------|-------------|----------|
| {filename}-chunks.md (baseado no nome do arquivo original) | Ex: 'calendario-provas-2026-chunks.md'. | ✓ |
| selection-maid-{timestamp}.md | Ex: 'selection-maid-20260526-2110.md'. | |
| Você decide | Planner escolhe a convenção de nome. | |

**User's choice:** `{filename-slug}-chunks.md`.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Chunks separados por --- com header de metadados | Front-matter YAML + separadores por chunk. | ✓ |
| Chunks concatenados sem separação | Só o conteúdo em sequência. | |
| Você decide | Planner decide o formato do arquivo gerado. | |

**User's choice:** Front-matter YAML + chunks separados por `---` com header `# Chunk N`.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Icônico (DownloadIcon) ao lado do botão 'Copiar' existente | Icon-only no header de cada ChunkCard. | ✓ |
| Botão com texto 'Download' ao lado de 'Copiar' | Botão com label explícito. | |
| Você decide | Planner decide o estilo do botão por chunk. | |

**User's choice:** DownloadIcon icon-only ao lado do CopyIcon.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Check icon por 1.5s, igual ao botão 'Copiar' atual | Consistência com o padrão já estabelecido. | ✓ |
| Texto 'Baixado!' por 2s | Apenas muda o label. | |
| Você decide | Planner decide o feedback. | |

**User's choice:** Check icon por 1.5s, igual ao botão Copiar.

---

| Option | Description | Selected |
|--------|-------------|----------|
| title, language, doc_type, ingested_at, chunk_count | Os campos retornados pela API. | ✓ |
| Só title e chunk_count | Front-matter mínimo. | |
| Você decide | Planner decide os campos. | |

**User's choice:** Front-matter YAML com todos os 5 campos de metadados.

---

## Claude's Discretion

- Tipografia: manter fontes do sistema ou ajustar — planner decide.
- Intensidade exata do glassmorphism (backdrop-blur e opacidade dos cards).
- Curvas de easing e timing do pulso roxo no processamento.
- Espaçamento e padding exatos do prose no MarkdownRenderer.
- Tema exato do highlight.js (preferência por dark, paleta roxa).

## Deferred Ideas

- Alternância raw/renderizado por chunk (toggle Markdown bruto vs renderizado em cada ChunkCard).
- Temas dinâmicos por tipo de arquivo (azul para PDF, verde para DOCX etc.) — deferred para v3.0.
- Números de linha no código no syntax highlighter.
- Tipografia customizada (Inter, Geist ou similar) — planner pode incluir se simples.
