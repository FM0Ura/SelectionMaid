# Phase 12: Result Display - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-26
**Phase:** 12-Result Display
**Areas discussed:** Markdown Rendering Library, Metadata Panel Placement, Chunk Card Detail Level

---

## Markdown Rendering Library

| Option | Description | Selected |
|--------|-------------|----------|
| marked (Recomendado) | Rápida, leve e atende a maioria dos casos de uso de Markdown. | |
| markdown-it | Altamente extensível com plugins, ideal se precisarmos de suporte a extensões complexas futuramente. | ✓ |
| Custom Minimalist | Se o Markdown retornado for muito simples e padronizado. | |

**User's choice:** markdown-it
**Notes:** Nenhuma observação adicional.

---

## Metadata Panel Placement

| Option | Description | Selected |
|--------|-------------|----------|
| Sticky Header (Topo Fixo) | As informações do arquivo ficam sempre visíveis no topo da lista durante a rolagem. | |
| Top Card (Início da Lista) | Um card inicial que rola junto com a lista de chunks. | ✓ |
| Collapsible Sidebar (Lateral) | Painel lateral que pode ser escondido para focar no conteúdo. | |

**User's choice:** Top Card (Início da Lista)
**Notes:** Preferência por um layout linear que rola naturalmente.

---

## Chunk Card Detail Level

| Option | Description | Selected |
|--------|-------------|----------|
| Equilibrado (Recomendado) | Conteúdo + Título da Seção (se houver) + Botão de Copiar. Limpo e focado. | |
| Detalhado (Completo) | Inclui páginas de início/fim, contagem de palavras e índice do chunk. Útil para auditoria. | ✓ |
| Minimalista (Conteúdo) | Apenas o conteúdo Markdown e o botão de copiar. Máximo minimalismo. | |

**User's choice:** Detalhado (Completo)
**Notes:** Desejo de ter o máximo de contexto possível sobre a origem do chunk no documento original.

---

## Claude's Discretion

- Estilo visual dos cards de chunk seguindo o dark mode.
- Feedback visual do botão de cópia.
- Ordenação dos campos de metadados.

## Deferred Ideas

- Animação staggered de revelação (Phase 13).
- Transições suaves de view (Phase 13).
