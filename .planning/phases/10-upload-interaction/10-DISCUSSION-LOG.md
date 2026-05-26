# Phase 10: Upload Interaction - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-26
**Phase:** 10-Upload Interaction
**Areas discussed:** DropZone Scope & Boundary, Animation implementation details, Empty and Error states layout, File selection behavior details

---

## DropZone Scope & Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Componente centralizado (Card) | Uma área retangular clara (Card) no centro, focando a atenção. | ✓ |
| Full-page DropZone | Qualquer lugar da tela aceita o arquivo, com um overlay visual global. | |

**User's choice:** Componente centralizado (Card)
**Notes:** O usuário prefere manter a interação focada em um contêiner central.

---

## Animation implementation details

| Option | Description | Selected |
|--------|-------------|----------|
| CSS Keyframes puro | Simples, leve e performático para o efeito de pulse. | |
| Motion-v (Framer Motion para Vue) | Mais controle para coreografias complexas e transições suaves de entrada/saída. | ✓ |

**User's choice:** Motion-v (Framer Motion para Vue)
**Notes:** Decidido pelo uso da biblioteca motion-v para maior controle e suavidade.

---

## Empty and Error states layout

| Option | Description | Selected |
|--------|-------------|----------|
| Estados internos no Card | O conteúdo do Card muda dependendo do estado (vazio, erro, pronto). Mantém o layout estável. | ✓ |
| Substituição total do componente | Componentes distintos que substituem a zona de upload quando necessário. | |

**User's choice:** Estados internos no Card
**Notes:** Preferência por estabilidade visual mantendo o Card fixo.

---

## File selection behavior details

| Option | Description | Selected |
|--------|-------------|----------|
| Pegar apenas o primeiro | Ignora os outros e processa apenas o primeiro arquivo válido encontrado. | |
| Bloquear e mostrar erro | Bloqueia o upload e pede que envie apenas um arquivo por vez. | ✓ |

**User's choice:** Bloquear e mostrar erro
**Notes:** Explicitamente solicitado para evitar confusão no suporte a múltiplos arquivos.

---

## Claude's Discretion

- Micro-interações de feedback (timing, eases de animação).
- Estilização detalhada das mensagens de erro e estados vazios seguindo o tema dark.

## Deferred Ideas

- Visualização de metadados e chunks (escopo de fases futuras).
