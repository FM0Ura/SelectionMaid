# Phase 8: Backend CORS + Project Scaffold - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-25
**Phase:** 08-backend-cors-project-scaffold
**Areas discussed:** CORS origin scope, Frontend repo location, Vite dev proxy, shadcn-vue setup

---

## CORS origin scope

### Pergunta 1: Origens permitidas

| Option | Description | Selected |
|--------|-------------|----------|
| Só localhost:5173 | CORS restrito ao dev local. Em produção, SPA e API na mesma origem ou via proxy reverso. | ✓ |
| localhost:5173 + origem de prod | Já configura a origem de produção via variável de ambiente. | |
| allow_origins=['*'] (dev apenas) | Libera tudo durante dev, restringido antes do deploy. | |

**User's choice:** Só localhost:5173
**Notes:** Ferramenta de uso interno; sem deploy em domínio separado planejado para v2.0.

### Pergunta 2: Métodos liberados

| Option | Description | Selected |
|--------|-------------|----------|
| POST + OPTIONS apenas | A SPA só chama POST /ingest e o preflight OPTIONS. | ✓ |
| Todos os métodos (allow_methods=['*']) | Mais permissivo, menos manutenção. | |

**User's choice:** POST + OPTIONS apenas
**Notes:** Sem necessidade de GET/PUT/DELETE no escopo atual.

---

## Frontend repo location

### Pergunta 1: Onde o frontend mora

| Option | Description | Selected |
|--------|-------------|----------|
| Monorepo /frontend | Pasta frontend/ dentro deste repo. Versionamento conjunto. | ✓ |
| Repo separado | Deploy e histórico completamente independentes. | |

**User's choice:** Monorepo /frontend
**Notes:** Tamanho do projeto não justifica repos separados.

### Pergunta 2: Nome da pasta

| Option | Description | Selected |
|--------|-------------|----------|
| frontend/ | Convém para monorepos; sem ambiguidade. | ✓ |
| web/ | Mais curto; útil se houver múltiplos clientes. | |

**User's choice:** frontend/
**Notes:** Sem outros clientes planejados; frontend/ é mais explícito.

---

## Vite dev proxy

### Pergunta 1: Estratégia de chamada ao backend em dev

| Option | Description | Selected |
|--------|-------------|----------|
| Vite proxy + CORS | vite.config.ts define proxy /api → localhost:8000. Browser nunca vê CORS em dev. | ✓ |
| Só CORS, sem proxy | SPA chama localhost:8000 diretamente. Preflight em toda requisição. | |

**User's choice:** Vite proxy + CORS
**Notes:** Melhor DX em dev; CORS ativo no backend serve para outros clientes.

### Pergunta 2: Prefixo do proxy

| Option | Description | Selected |
|--------|-------------|----------|
| /api | SPA chama /api/ingest; proxy retira /api e repassa para localhost:8000/ingest. | ✓ |
| /ingest direto | SPA chama /ingest; proxy passa sem reescrita. | |

**User's choice:** /api
**Notes:** Isola o namespace do backend na SPA; mais fácil de mudar em produção.

---

## shadcn-vue setup

### Pergunta 1: Método de inicialização

| Option | Description | Selected |
|--------|-------------|----------|
| CLI npx shadcn-vue@latest init | Wizard oficial cria components.json, aliases e utils.ts. | ✓ |
| Setup manual | Instalar dependências e criar arquivos na mão. | |

**User's choice:** CLI npx shadcn-vue@latest init
**Notes:** Segue convenção oficial que documentação assume; menos erro manual.

### Pergunta 2: Componente de validação no scaffold

| Option | Description | Selected |
|--------|-------------|----------|
| Button apenas | Um único componente para confirmar dark mode + Tailwind v4 + shadcn-vue. | ✓ |
| Card + Button | Dois componentes; mais cobertura. | |

**User's choice:** Button apenas
**Notes:** Componentes reais chegam nas fases seguintes; Button é suficiente para validar o setup.

---

## Claude's Discretion

- `allow_headers=["*"]` — usuário não especificou; Claude decidiu liberar todos os headers para suportar multipart/form-data sem declaração manual pelo browser.
- Localização exata do `CORSMiddleware` em `app.py` (dentro de `create_app()` antes do lifespan) — delegado ao planner confirmar o padrão mais idiomático.

## Deferred Ideas

Nenhuma ideia fora de escopo surgiu durante a discussão.
