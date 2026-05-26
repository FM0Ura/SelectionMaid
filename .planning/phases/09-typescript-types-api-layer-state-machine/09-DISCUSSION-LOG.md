# Phase 9: TypeScript Types + API Layer + State Machine - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-25
**Phase:** 9-TypeScript Types + API Layer + State Machine
**Areas discussed:** API Organization, Error Mapping, State Machine States, Validation Strategy

---

## API Organization

| Option | Description | Selected |
|--------|-------------|----------|
| Separar src/api/ e src/composables/ | Separa a lógica de rede (fetch) e os tipos da lógica de reatividade do Vue. Melhora a testabilidade. | ✓ |
| Tudo no useUpload.ts | Tudo em um único arquivo. Mais simples para este tamanho de projeto, mas acopla rede e reatividade. | |

**User's choice:** Separar src/api/ e src/composables/

---

## TypeScript Types Location

| Option | Description | Selected |
|--------|-------------|----------|
| src/types/api.ts | Centraliza os tipos da API para facilitar o reuso em múltiplos componentes/composables. | ✓ |
| Junto com o cliente API (src/api/index.ts) | Mantém os tipos junto com a lógica que os consome. | |

**User's choice:** src/types/api.ts

---

## Error Mapping

| Option | Description | Selected |
|--------|-------------|----------|
| Utilitário Central (src/api/errors.ts) | Cria uma utilidade que mapeia códigos de erro do backend (e timeouts) para mensagens amigáveis em português. | ✓ |
| Tratamento Local no useUpload | Trata cada erro individualmente dentro do try/catch do composable. | |

**User's choice:** Utilitário Central (src/api/errors.ts)

---

## Timeout UX

| Option | Description | Selected |
|--------|-------------|----------|
| Mensagem Genérica | Um erro genérico de timeout ("Servidor demorou demais"). | |
| Mensagem Detalhada (PROC-03) | Informa que o processamento é pesado e sugere tentar novamente ("O documento é complexo e o tempo limite de 120s foi atingido"). | ✓ |

**User's choice:** Mensagem Detalhada (PROC-03)

---

## State Machine Differentiation

| Option | Description | Selected |
|--------|-------------|----------|
| 4 Estados (Simplificado) | Idle, Loading, Success, Error. Simples e direto. | |
| 5 Estados (Diferenciado) | Idle, Uploading, Processing, Success, Error. Permite feedbacks diferentes. | ✓ |

**User's choice:** 5 Estados (Diferenciado)

---

## State Machine Implementation

| Option | Description | Selected |
|--------|-------------|----------|
| Discriminated Union (Recomendado) | { status: 'success', data: ExtractionResponse } | ✓ |
| Boolean Flags (Flat) | isLoading, isError, data. | |

**User's choice:** Discriminated Union (Recomendado)

---

## Validation Location

| Option | Description | Selected |
|--------|-------------|----------|
| Dentro do useUpload.ts | No composable, antes de chamar a API. | |
| Utilitário de Validação Separado | Uma função pura em src/lib/validators.ts. | ✓ |

**User's choice:** Utilitário de Validação Separado

---

## Validation Error Feedback

| Option | Description | Selected |
|--------|-------------|----------|
| Estado de Erro Global | Altera o estado para 'error' imediatamente. | |
| Erro de Validação Local | Retorna um erro específico sem alterar o estado global. | ✓ |

**User's choice:** Erro de Validação Local

---

## Claude's Discretion

None requested.

## Deferred Ideas

None mentioned.
