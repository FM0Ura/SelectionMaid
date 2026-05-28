# Phase 9: TypeScript Types + API Layer + State Machine - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Esta fase entrega a infraestrutura de comunicação e gerenciamento de estado do frontend. O objetivo é garantir que o app possa enviar arquivos para o backend, tratar a resposta (chunks + metadados) de forma tipada e gerenciar o ciclo de vida do upload com uma máquina de estados robusta.

</domain>

<decisions>
## Implementation Decisions

### Organização da API e Tipagem
- **D-01:** Separação clara entre `src/api/` (lógica de rede pura) e `src/composables/` (lógica reativa do Vue). Isso facilita testes isolados da camada de rede.
- **D-02:** Tipos TypeScript gerados a partir dos schemas Pydantic do backend serão centralizados em `src/types/api.ts`.

### Mapeamento de Erros e Timeout
- **D-03:** Utilitário central de erros em `src/api/errors.ts` para mapear status codes e exceções para mensagens amigáveis.
- **D-04:** Mensagens de timeout detalhadas (PROC-03) informando o limite de 130s e sugerindo re-tentativa para documentos complexos.

### Máquina de Estados (State Machine)
- **D-05:** Implementação via **Discriminated Union** para evitar estados impossíveis.
- **D-06:** 5 estados distintos: `idle`, `uploading`, `processing`, `success`, `error`. A distinção entre 'uploading' e 'processing' é semântica para melhorar o feedback visual (PROC-01).

### Validação de Arquivos
- **D-07:** Lógica de validação (tamanho < 50MB, tipos PDF/DOCX/HTML) isolada em `src/lib/validators.ts` como funções puras.
- **D-08:** Erros de validação retornados localmente para o componente chamador, sem forçar o estado global de erro imediatamente, permitindo UI específica de "pré-vôo".

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 9 goal and success criteria.
- `.planning/REQUIREMENTS.md` — UPL-03 (validation), PROC-01 (processing feedback), PROC-03 (timeout).

### Backend Schema (Source of Truth for Types)
- `src/selection_maid/adapters/http/schemas.py` — `ExtractionResponse`, `MetadataSchema`, `ChunkSchema`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/lib/utils.ts`: Utilitários padrão do shadcn/Tailwind.
- `frontend/src/components/ui/button`: Componente já disponível para ações de upload/retry.

### Established Patterns
- **Fetch API**: Uso nativo de `fetch` com `AbortSignal.timeout(130_000)` como definido no STATE.md.
- **Hexagonal Alignment**: A separação entre `src/api` e `src/composables` espelha a separação de adaptadores e serviços no backend.

### Integration Points
- `frontend/src/api/index.ts` → Novo cliente fetch apontando para `/api/ingest`.
- `frontend/src/composables/useUpload.ts` → Ponto central de reatividade consumido por `App.vue`.

</code_context>

<specifics>
## Specific Ideas

- O estado `processing` deve ser ativado após o envio bem-sucedido do payload, cobrindo o tempo de extração do Docling no backend.
- O mapeador de erros deve tratar especificamente o `AbortError` do timeout como um caso especial de PROC-03.

</specifics>

<deferred>
## Deferred Ideas

### Reviewed Todos (not folded)
None — discussion stayed within phase scope

</deferred>

---

*Phase: 9-TypeScript Types + API Layer + State Machine*
*Context gathered: 2026-05-25*
