# Phase 3: Content Filtering - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-24
**Phase:** 03-content-filtering
**Areas discussed:** Detecção de headers/footers, Política de número de página, Configurabilidade do HeuristicFilter, Fixtures e estratégia de testes

---

## Detecção de headers/footers

### Questão 1: Estratégia principal para FILT-01 sem page boundaries

| Option | Description | Selected |
|--------|-------------|----------|
| Frequência pura no blob | Linha que aparece N+ vezes = header/footer. Simples, sem page boundaries. | |
| Frequência + proximidade topológica | Frequência + linha curta + início/fim do documento. Mais preciso. | |
| Confiar no Docling + filtro leve | Docling já detecta headers/footers via layout AI; filtro é safety net. | ✓ |

**User's choice:** Confiar no Docling + filtro leve
**Notes:** Docling já usa modelos de layout para detectar e remover headers/footers de PDFs — o HeuristicFilter atua como complemento para casos perdidos.

### Questão 2: Comportamento do safety net

| Option | Description | Selected |
|--------|-------------|----------|
| Frequência mínima simples | Linhas curtas (< 80 chars) que aparecem 3+ vezes são removidas. | ✓ |
| Só padrões conhecidos | Lista de regexes para padrões típicos (nomes de empresa, "Confidential", etc.). | |
| Sem safety net para FILT-01 | Se Docling resolve, não implementar detecção no filtro. | |

**User's choice:** Frequência mínima simples
**Notes:** Threshold de 3 repetições e 80 chars de comprimento máximo.

### Questão 3: Threshold de tamanho máximo de linha candidata

| Option | Description | Selected |
|--------|-------------|----------|
| 80 caracteres | Padrão — cobre maioria dos headers/footers sem falsos positivos. | ✓ |
| 120 caracteres | Mais permissivo — cobre headers/footers com nomes longos. | |
| Sem limite | Qualquer linha que repete — arriscado. | |

**User's choice:** 80 caracteres

### Questão 4: Exclusões do safety net de frequência

| Option | Description | Selected |
|--------|-------------|----------|
| Excluir headings | Linhas com # não são removidas mesmo que repitam. | |
| Excluir headings e linhas de tabela | Linhas com # e linhas com \| são sempre excluídas. | ✓ |
| Não excluir nenhum padrão | Frequência decide tudo. | |

**User's choice:** Excluir headings e linhas de tabela
**Notes:** Evita remoção de seções com título idêntico (ex: "Referências" em capítulos múltiplos) e separadores de tabela.

---

## Política de número de página

### Questão 1: O que reconhecer como número de página em FILT-02

| Option | Description | Selected |
|--------|-------------|----------|
| Só `^\d+$` | Número puro — conservador, zero falsos positivos com anos. | |
| Número puro + padrões comuns | `^\d+$` + "Página N", "Page N", "N de M", "N of M". | |
| Padrão amplo com números romanos | Inclui romanos (I, II, III...) e variações com hífen (-5-, - 5 -). | ✓ |

**User's choice:** Padrão amplo com números romanos
**Notes:** Cobertura máxima — cobre documentos acadêmicos e relatórios que usam numeração romana em prefácio.

### Questão 2: Inline vs isolado — escopo da remoção

| Option | Description | Selected |
|--------|-------------|----------|
| Só linhas completamente isoladas | Linha inteira (strip) = padrão. Inline não afetado. | ✓ |
| Linhas isoladas + início/fim de parágrafo | Mais agressivo — também remove número colado no bloco de texto. | |

**User's choice:** Só linhas completamente isoladas
**Notes:** "Ver item 42" não é afetado. Garantia de preservação de conteúdo legítimo.

---

## Configurabilidade do HeuristicFilter

### Questão 1: Onde vivem os thresholds

**User's choice (freeform):** "devem estar em um arquivo .toml"
**Clarificação solicitada:** arquivo dentro do pyproject.toml ou separado, e comportamento em runtime.

### Questão 2: Como o TOML de configuração deve funcionar

| Option | Description | Selected |
|--------|-------------|----------|
| Seção no pyproject.toml | `[tool.selection_maid.filter]` — sem arquivo extra. | |
| Arquivo config.toml separado | `config.toml` na raiz — mais flexível para deploy. | |
| TOML como defaults + construtor para override | TOML define defaults, construtor sobrescreve. | |

**User's choice (freeform):** "usaremos um config.toml, mas teremos também valores default"
**Notes:** config.toml na raiz; defaults hardcoded como fallback quando o arquivo não existe.

### Questão 3: Comportamento quando config.toml não é encontrado

| Option | Description | Selected |
|--------|-------------|----------|
| Usar defaults hardcoded | Serviço sobe normalmente. CI roda sem arquivo. | ✓ |
| Falhar ao iniciar | config.toml obrigatório. | |
| Log de aviso + defaults | Usa defaults mas emite WARNING. | |

**User's choice:** Usar defaults hardcoded

### Questão 4: Quem lê o config.toml

| Option | Description | Selected |
|--------|-------------|----------|
| HeuristicFilter diretamente | Filtro lê o TOML no construtor — acoplamento direto. | |
| Camada de config central | `selection_maid.config` resolve; HeuristicFilter recebe via injeção. | ✓ |

**User's choice:** Camada de config central
**Notes:** Novo módulo `src/selection_maid/config.py` usando `tomllib` (stdlib Python 3.11+). Será o ponto central de configuração para fases futuras.

---

## Fixtures e estratégia de testes

### Questão 1: Como criar fixtures de documentos ruidosos

| Option | Description | Selected |
|--------|-------------|----------|
| Strings Markdown inline nos testes | Self-contained, visível no código, sem dependência de arquivo. | ✓ |
| Arquivos .md em tests/fixtures/ | Mais próximos de documentos reais, mas adiciona complexidade. | |

**User's choice:** Strings Markdown inline nos testes

### Questão 2: Estrutura dos testes

| Option | Description | Selected |
|--------|-------------|----------|
| Uma classe de teste por regra | `TestFILT01Headers`, `TestFILT02PageNumbers`, `TestFILT03Whitespace`, `TestContentPreservation`. | ✓ |
| Classe única TestHeuristicFilter | Um grupo com métodos nomeados por requirement. | |

**User's choice:** Uma classe de teste por regra

### Questão 3: O que TestContentPreservation verifica

| Option | Description | Selected |
|--------|-------------|----------|
| Headings, parágrafos, tabelas e listas | Cada elemento legítimo verificado como presente após filtro. | ✓ |
| Round-trip: input = output sem ruído | Documento sem ruído sai idêntico após filtro. | |

**User's choice:** Headings, parágrafos, tabelas e listas

---

## Claude's Discretion

- Ordem de aplicação das regras no `filter()`: frequência → números de página → whitespace. Definida pelo assistente para garantir que compressão de whitespace não interfere na detecção de frequência.
- Limite de comprimento para números romanos: 1-10 caracteres (evita falsos positivos com siglas longas).
- Uso de `tomllib` (stdlib Python 3.11+) para parsing do config.toml, sem dependência externa.

## Deferred Ideas

- **OCR artifact removal** — remoção de artefatos de OCR (caracteres inválidos). Candidato para Phase 7 ou v2.
- **Configuração por tipo de documento** — thresholds diferentes por doc_type. Requer Phase 5 (META-03). Candidato para v2.
