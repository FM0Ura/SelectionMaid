# Phase 8: Backend CORS + Project Scaffold - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 8 entrega dois resultados independentes mas necessários para que o v2.0 comece:

1. **Backend CORS**: `CORSMiddleware` configurado no FastAPI em `app.py` para aceitar requisições de `http://localhost:5173`. Requerimento INT-01.
2. **Frontend scaffold**: Projeto Vue 3 + Vite inicializado em `frontend/`, com Tailwind CSS v4, shadcn-vue e um componente Button renderizando em dark mode.

**Critério de sucesso (da ROADMAP):**
- Preflight `OPTIONS` de `localhost:5173` retorna `Access-Control-Allow-Origin` sem erro.
- `npm run dev` sobe a SPA em `localhost:5173` com Vue 3 visível no browser.
- Vite proxy roteia `/api/ingest` → `localhost:8000/ingest` sem CORS error no console.
- Tailwind CSS v4 + shadcn-vue inicializados; Button dark-mode renderiza corretamente.

</domain>

<decisions>
## Implementation Decisions

### CORS Origin Scope

- **D-01:** `CORSMiddleware` permite apenas `allow_origins=["http://localhost:5173"]`. Nenhuma wildcard; nenhuma origem de produção por ora. Em produção, a SPA e a API estarão atrás do mesmo proxy reverso ou mesma origem.
- **D-02:** `allow_methods=["POST", "OPTIONS"]`. A SPA só chama `POST /ingest`; OPTIONS é o preflight. Não há razão para liberar GET/PUT/DELETE na Phase 8.
- **D-03:** `allow_headers=["*"]` para headers (necessário para `Content-Type: multipart/form-data` enviado pelo browser sem declaração manual).

### Frontend Repo Location

- **D-04:** O frontend mora em `frontend/` dentro deste repo (monorepo). Versionamento conjunto com o backend.
- **D-05:** Nome exato da pasta: `frontend/` (sem subpasta adicional). Estrutura esperada: `frontend/src/`, `frontend/public/`, `frontend/vite.config.ts`, `frontend/package.json`.

### Vite Dev Proxy

- **D-06:** Vite proxy configurado em `frontend/vite.config.ts` com `server.proxy`: `/api` → `http://localhost:8000`, com `rewrite: (path) => path.replace(/^\/api/, '')`. Assim a SPA chama `/api/ingest` e o proxy repassa para `localhost:8000/ingest`.
- **D-07:** O prefixo escolhido é `/api`. Isso isola o namespace de backend na SPA e facilita trocar de endpoint em produção via variável de ambiente.
- **D-08:** CORS continua ativo no FastAPI (D-01) mesmo com o proxy. O proxy é só para dev local; em produção a chamada vai direto para o backend (mesmo domínio via reverse proxy, ou CORS explícito se necessário).

### shadcn-vue Setup

- **D-09:** Inicializar via CLI oficial: `npx shadcn-vue@latest init` dentro de `frontend/`. O wizard cria `components.json`, configura `@/` aliases e gera `lib/utils.ts`.
- **D-10:** Instalar apenas o componente `Button` na Phase 8, via `npx shadcn-vue@latest add button`. Suficiente para validar dark mode + Tailwind v4 + shadcn-vue. Componentes reais (DropZone, SkeletonCard, ChunkCard) chegam nas fases seguintes.
- **D-11:** Dark mode via Tailwind CSS v4 class strategy (`darkMode: 'class'`). Aplicar `class="dark"` no `<html>` do `index.html` para o scaffold — a SPA terá dark mode fixo no v2.0.

### Stack confirmada (prior decisions, não re-discutidas)

- Vue 3.5 + TypeScript 5.5 + Vite 6
- Tailwind CSS v4
- shadcn-vue (componentes isolados, não instalar todos de vez)
- motion-v v2.2 (instalado agora, usado a partir da Phase 13)
- @vueuse/core (instalado agora, usado a partir da Phase 9)
- Sem Pinia; sem Axios

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 8 goal, success criteria, e dependências (Phase 8 → Phase 9).
- `.planning/REQUIREMENTS.md` — INT-01: único requerimento desta fase.

### Backend — CORS target
- `src/selection_maid/adapters/http/app.py` — `create_app()` e `_lifespan()`. CORSMiddleware é adicionado aqui, antes de `app.include_router(router)`, mas depois da wiring dos adapters no lifespan. Seguir o padrão D-83/D-84/D-85 já estabelecido.

### Tech Stack (decisões de milestone já fixadas)
- `.planning/STATE.md` §Accumulated Context → Decisions — lista completa das decisões de stack do v2.0 (Vue 3.5, Vite 6, Tailwind v4, shadcn-vue, motion-v, @vueuse/core, fetch nativo, etc.). Downstream agents devem confirmar essas versões antes de gerar qualquer `package.json`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/selection_maid/adapters/http/app.py`: `create_app()` é o ponto de entrada. CORSMiddleware é adicionado chamando `app.add_middleware(CORSMiddleware, ...)` dentro de `create_app()` antes do `lifespan` ser registrado, ou diretamente no `FastAPI(...)` constructor — verificar qual é mais idiomático com a estrutura atual (D-83).
- `pyproject.toml`: Dependências backend já fixadas; não há `httpx-cors` ou similar — usar `fastapi`'s built-in CORSMiddleware (`from starlette.middleware.cors import CORSMiddleware`).

### Established Patterns
- **Lifespan pattern (D-84):** O lifespan faz toda a wiring. CORSMiddleware NÃO deve ser adicionado dentro do lifespan — middleware é configurado na criação do app, não em startup.
- **`build_router` closure (D-85):** O router é incluído dentro do lifespan após a wiring. CORSMiddleware precisa estar no app antes disso.
- **Monorepo com `uv`:** Backend usa `uv` e `pyproject.toml`. Frontend usa `npm` / `node`. São toolchains separados — o `package.json` do frontend não interfere no `pyproject.toml` do backend.

### Integration Points
- `frontend/vite.config.ts` → `localhost:8000` (backend dev server). O planner deve garantir que o `uvicorn` sobe na porta 8000 por padrão (já é o caso).
- `frontend/src/` → estrutura vazia a ser criada. Phase 9 vai popular `src/types/`, `src/api/`, `src/composables/`.

</code_context>

<specifics>
## Specific Ideas

- O `Button` dark-mode do shadcn-vue deve aparecer renderizado em `App.vue` como prova de que o scaffold está funcional — não apenas instalado.
- O `index.html` deve ter `class="dark"` no `<html>` desde o início (dark mode fixo para o v2.0).

</specifics>

<deferred>
## Deferred Ideas

Nenhuma — a discussão ficou dentro do escopo da Phase 8.

</deferred>

---

*Phase: 08-Backend CORS + Project Scaffold*
*Context gathered: 2026-05-25*
