# Codebase Structure

**Analysis Date:** 2026-05-27

## Directory Layout

```text
SelectionMaid/
├── src/selection_maid/              # Python backend package
│   ├── domain/                      # Pure domain dataclasses and port protocols
│   ├── adapters/                    # Concrete infrastructure adapters
│   │   ├── extractor/               # Docling extraction adapter
│   │   ├── filter/                  # Heuristic Markdown cleanup adapter
│   │   ├── chunker/                 # Markdown chunking adapter
│   │   ├── enricher/                # Metadata enrichment adapter
│   │   └── http/                    # FastAPI app, router, schemas, error mapping
│   ├── config.py                    # Backend TOML config loader and config dataclasses
│   ├── errors.py                    # Backend domain error hierarchy
│   ├── service.py                   # ExtractionService pipeline orchestration
│   └── py.typed                     # PEP 561 typing marker
├── frontend/                        # Vite + Vue 3 SPA
│   ├── src/
│   │   ├── api/                     # Browser HTTP client and API error mapping
│   │   ├── assets/                  # CSS and static image assets
│   │   ├── components/              # Vue UI, upload, and result components
│   │   ├── composables/             # Vue composition functions/state machines
│   │   ├── lib/                     # Frontend utilities and validators
│   │   └── types/                   # TypeScript API/domain types
│   ├── public/                      # Public SVG assets
│   ├── package.json                 # Frontend scripts and dependencies
│   └── vite.config.ts               # Vue/Tailwind plugins, alias, and dev proxy
├── tests/                           # Backend pytest suite
│   ├── domain/                      # Domain model and service tests
│   ├── adapters/                    # Adapter-specific backend tests
│   ├── stubs/                       # Structural port stubs for backend tests
│   └── fixtures/                    # Backend fixture generation helpers
├── docs/                            # Human-facing project docs
├── .planning/                       # GSD planning state and generated codebase maps
│   └── codebase/                    # Generated mapper outputs
├── .codex/                          # Local Codex/GSD agents, skills, hooks, workflows
├── .claude/                         # Local Claude/GSD agents, commands, hooks, workflows
├── .gemini/                         # Local Gemini/GSD agents, commands, hooks, workflows
├── pyproject.toml                   # Python package, dependencies, ruff, mypy, pytest config
├── uv.lock                          # Python lockfile
├── config.toml                      # Backend runtime configuration
├── README.md                        # Project overview and quickstart
└── CLAUDE.md                        # Repository guidance for Claude-based workflows
```

## Directory Purposes

**`src/selection_maid/`:**
- Purpose: Python backend package.
- Contains: Domain contracts, application service, infrastructure adapters, configuration, and errors.
- Key files: `src/selection_maid/service.py`, `src/selection_maid/config.py`, `src/selection_maid/errors.py`, `src/selection_maid/py.typed`.

**`src/selection_maid/domain/`:**
- Purpose: Pure backend domain layer.
- Contains: Frozen dataclasses in `models.py` and `Protocol` port contracts in `ports.py`.
- Key files: `src/selection_maid/domain/models.py`, `src/selection_maid/domain/ports.py`.

**`src/selection_maid/adapters/`:**
- Purpose: Infrastructure implementations for domain ports and HTTP transport.
- Contains: Extractor, filter, chunker, enricher, and FastAPI HTTP adapter packages.
- Key files: `src/selection_maid/adapters/extractor/docling.py`, `src/selection_maid/adapters/filter/heuristic.py`, `src/selection_maid/adapters/chunker/markdown.py`, `src/selection_maid/adapters/enricher/default.py`, `src/selection_maid/adapters/http/router.py`.

**`src/selection_maid/adapters/http/`:**
- Purpose: Backend HTTP boundary.
- Contains: FastAPI app factory, router factory, Pydantic response schemas, error-code to HTTP-status mapping.
- Key files: `src/selection_maid/adapters/http/app.py`, `src/selection_maid/adapters/http/router.py`, `src/selection_maid/adapters/http/schemas.py`, `src/selection_maid/adapters/http/error_map.py`.

**`frontend/`:**
- Purpose: Independent frontend Node/Vite project.
- Contains: Vue app source, package files, TypeScript config, Vite config, public assets, and tests.
- Key files: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/src/main.ts`, `frontend/src/App.vue`.

**`frontend/src/api/`:**
- Purpose: Frontend HTTP boundary.
- Contains: `postIngest()` fetch wrapper and API error mapping.
- Key files: `frontend/src/api/ingest.ts`, `frontend/src/api/errors.ts`.

**`frontend/src/components/`:**
- Purpose: Vue presentation components.
- Contains: Feature components under `upload/` and `result/`, reusable UI primitives under `ui/`, and an unused Vite starter component.
- Key files: `frontend/src/components/upload/DropZone.vue`, `frontend/src/components/upload/ProcessingCard.vue`, `frontend/src/components/result/ResultView.vue`, `frontend/src/components/result/ChunkCard.vue`, `frontend/src/components/result/MarkdownRenderer.vue`, `frontend/src/components/ui/button/Button.vue`.

**`frontend/src/composables/`:**
- Purpose: Vue composition/state logic.
- Contains: Upload workflow state machine.
- Key files: `frontend/src/composables/useUpload.ts`.

**`frontend/src/lib/`:**
- Purpose: Frontend helper functions.
- Contains: CSS class merge helper, file validators, date/duration/page/filename formatters.
- Key files: `frontend/src/lib/utils.ts`, `frontend/src/lib/validators.ts`, `frontend/src/lib/formatters.ts`.

**`frontend/src/types/`:**
- Purpose: TypeScript contract types shared by frontend features.
- Contains: API response interfaces and upload state union.
- Key files: `frontend/src/types/api.ts`.

**`tests/`:**
- Purpose: Backend pytest suite.
- Contains: Domain tests, adapter tests, HTTP tests, stubs, fixtures, memory regression tests, and shared test config.
- Key files: `tests/domain/test_service.py`, `tests/domain/test_models.py`, `tests/adapters/http/test_router.py`, `tests/adapters/http/conftest.py`, `tests/stubs/adapters.py`, `tests/test_config.py`, `tests/test_memory_regression.py`.

**`docs/`:**
- Purpose: Human-facing project documentation.
- Contains: API, architecture, configuration, development, getting-started, and testing docs.
- Key files: `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/CONFIGURATION.md`, `docs/DEVELOPMENT.md`, `docs/GETTING-STARTED.md`, `docs/TESTING.md`.

**`.planning/`:**
- Purpose: GSD workflow state and generated planning artifacts.
- Contains: Project state, requirements, roadmap, phase plans, milestone artifacts, research docs, and codebase maps.
- Key files: `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md`.

**`.codex/skills/`:**
- Purpose: Local Codex skill definitions for GSD workflows.
- Contains: `SKILL.md` indexes for GSD commands and supporting workflow rules.
- Key files: `.codex/skills/gsd-map-codebase/SKILL.md`, `.codex/skills/gsd-plan-phase/SKILL.md`, `.codex/skills/gsd-execute-phase/SKILL.md`.

## Key File Locations

**Entry Points:**
- `src/selection_maid/adapters/http/app.py`: Backend FastAPI app factory, lifespan wiring, CORS config, and uvicorn target.
- `src/selection_maid/adapters/http/router.py`: Backend HTTP routes for `GET /health` and `POST /ingest`.
- `frontend/src/main.ts`: Frontend Vue app bootstrap.
- `frontend/src/App.vue`: Frontend root view switcher.

**Configuration:**
- `pyproject.toml`: Python project metadata, runtime dependencies, dev dependencies, mypy strict mode, ruff rules, pytest options.
- `uv.lock`: Python dependency lockfile.
- `config.toml`: Backend runtime settings consumed by `src/selection_maid/config.py`.
- `frontend/package.json`: Frontend scripts and dependencies.
- `frontend/vite.config.ts`: Vite plugin setup, `@` alias, and `/api` dev proxy.
- `frontend/tsconfig.json`, `frontend/tsconfig.app.json`, `frontend/tsconfig.node.json`: Frontend TypeScript project config.
- `frontend/vitest.config.ts`: Frontend Vitest configuration.
- `frontend/components.json`: shadcn-vue component configuration.

**Core Logic:**
- `src/selection_maid/service.py`: Backend extraction pipeline orchestration.
- `src/selection_maid/domain/models.py`: Backend value-object schema.
- `src/selection_maid/domain/ports.py`: Backend port contracts.
- `src/selection_maid/errors.py`: Backend domain error taxonomy.
- `src/selection_maid/config.py`: Backend config dataclasses and TOML parsing.
- `frontend/src/composables/useUpload.ts`: Frontend upload state machine.
- `frontend/src/api/ingest.ts`: Frontend ingestion request function.
- `frontend/src/types/api.ts`: Frontend representation of backend response shape.

**Backend Adapters:**
- `src/selection_maid/adapters/extractor/docling.py`: Docling-backed extractor implementation.
- `src/selection_maid/adapters/filter/heuristic.py`: Heuristic document cleanup implementation.
- `src/selection_maid/adapters/chunker/markdown.py`: Markdown chunking implementation.
- `src/selection_maid/adapters/enricher/default.py`: Metadata enrichment implementation.
- `src/selection_maid/adapters/http/app.py`: FastAPI app and startup wiring.
- `src/selection_maid/adapters/http/router.py`: HTTP route logic and request/response flow.
- `src/selection_maid/adapters/http/schemas.py`: Pydantic schemas.
- `src/selection_maid/adapters/http/error_map.py`: HTTP status mapping.

**Frontend Components:**
- `frontend/src/components/upload/DropZone.vue`: Drag/drop and file picker interaction.
- `frontend/src/components/upload/ProcessingCard.vue`: Processing status display.
- `frontend/src/components/upload/ErrorBanner.vue`: Upload error display.
- `frontend/src/components/upload/SkeletonChunk.vue`: Processing skeleton preview.
- `frontend/src/components/result/ResultView.vue`: Result screen and bulk Markdown download.
- `frontend/src/components/result/MetadataCard.vue`: Document metadata summary.
- `frontend/src/components/result/ChunkCard.vue`: Per-chunk display and actions.
- `frontend/src/components/result/MarkdownRenderer.vue`: Markdown rendering and sanitization.

**Testing:**
- `tests/domain/test_models.py`: Backend domain model tests.
- `tests/domain/test_service.py`: Backend application service tests.
- `tests/adapters/http/test_router.py`: Backend router unit tests.
- `tests/adapters/http/test_integration.py`: Backend HTTP integration tests.
- `tests/adapters/extractor/test_docling_adapter.py`: Backend extractor tests.
- `tests/adapters/filter/test_heuristic_filter.py`: Backend filter tests.
- `tests/adapters/chunker/test_markdown_chunker.py`: Backend chunker tests.
- `tests/adapters/enricher/test_metadata_enricher.py`: Backend enricher tests.
- `frontend/src/**/*.spec.ts`: Frontend Vitest tests co-located with source.
- `frontend/src/components/upload/__tests__/*.spec.ts`: Frontend upload component tests.

**Documentation:**
- `README.md`: Main project overview and setup.
- `docs/API.md`: HTTP API documentation.
- `docs/ARCHITECTURE.md`: Human-facing architecture guide.
- `docs/DEVELOPMENT.md`: Development workflow and conventions.
- `docs/TESTING.md`: Test workflow and strategy.
- `.planning/codebase/ARCHITECTURE.md`: Generated architecture map for GSD planners/executors.
- `.planning/codebase/STRUCTURE.md`: Generated structure map for GSD planners/executors.

## Naming Conventions

**Files:**
- Backend modules use lowercase snake_case: `src/selection_maid/service.py`, `src/selection_maid/adapters/http/error_map.py`.
- Backend adapter implementation modules are named for the concrete strategy: `docling.py`, `heuristic.py`, `markdown.py`, `default.py`.
- Backend test files use `test_*.py`: `tests/adapters/http/test_router.py`.
- Vue single-file components use PascalCase: `frontend/src/components/result/ResultView.vue`, `frontend/src/components/upload/DropZone.vue`.
- Frontend TypeScript utilities use camelCase or domain nouns: `frontend/src/composables/useUpload.ts`, `frontend/src/api/ingest.ts`, `frontend/src/lib/formatters.ts`.
- Frontend test files use `*.spec.ts`: `frontend/src/api/ingest.spec.ts`, `frontend/src/components/result/ResultView.spec.ts`.
- Component barrel files use `index.ts`: `frontend/src/components/ui/button/index.ts`.

**Directories:**
- Backend package directories use lowercase names: `src/selection_maid/domain/`, `src/selection_maid/adapters/http/`.
- Backend adapter directories are grouped by port/transport: `extractor/`, `filter/`, `chunker/`, `enricher/`, `http/`.
- Backend tests mirror backend layers: `tests/domain/`, `tests/adapters/http/`, `tests/adapters/chunker/`.
- Frontend feature components are grouped by workflow: `frontend/src/components/upload/`, `frontend/src/components/result/`.
- Frontend reusable primitives live under `frontend/src/components/ui/<component>/`.
- GSD-generated codebase maps live under `.planning/codebase/`.

## Where to Add New Code

**New Backend Use Case:**
- Primary code: add or extend services under `src/selection_maid/` while keeping orchestration outside `src/selection_maid/domain/`.
- HTTP route: add to `src/selection_maid/adapters/http/router.py` or create a new router factory under `src/selection_maid/adapters/http/` with explicit dependency injection.
- Tests: add domain/application tests under `tests/domain/` and HTTP tests under `tests/adapters/http/`.

**New Backend Domain Data:**
- Primary code: add frozen dataclasses to `src/selection_maid/domain/models.py`.
- Port contracts: add or update `Protocol`s in `src/selection_maid/domain/ports.py`.
- Tests: add model/contract tests under `tests/domain/`.

**New Backend Adapter:**
- Implementation: add a focused module under the relevant adapter directory, for example `src/selection_maid/adapters/extractor/<strategy>.py`.
- Factory: expose a `build_*` function from that module and wire it in `src/selection_maid/adapters/http/app.py`.
- Tests: add adapter tests under the matching `tests/adapters/<adapter>/` directory.

**New Backend Configuration:**
- Primary code: add fields to config dataclasses in `src/selection_maid/config.py`.
- Runtime values: add documented defaults or overrides to `config.toml`.
- Tests: update `tests/test_config.py`.

**New Backend HTTP Response Field:**
- Domain source: update `src/selection_maid/domain/models.py`.
- HTTP schema: update `src/selection_maid/adapters/http/schemas.py`.
- Frontend type: update `frontend/src/types/api.ts`.
- Rendering: update result components under `frontend/src/components/result/`.
- Tests: update backend schema tests under `tests/adapters/http/test_schemas.py` and frontend type/component tests under `frontend/src/`.

**New Frontend API Call:**
- Primary code: add a file under `frontend/src/api/`.
- Types: add or update interfaces in `frontend/src/types/api.ts`.
- State integration: add composable logic under `frontend/src/composables/`.
- Tests: add `*.spec.ts` next to the API/composable file.

**New Frontend Feature View:**
- Primary code: add Vue components under `frontend/src/components/<feature>/`.
- State: keep workflow logic in a composable under `frontend/src/composables/`.
- Utilities: put reusable pure helpers in `frontend/src/lib/`.
- Tests: co-locate component specs or use `frontend/src/components/<feature>/__tests__/` for grouped component tests.

**New UI Primitive:**
- Implementation: add `frontend/src/components/ui/<primitive>/<Primitive>.vue`.
- Barrel export: add `frontend/src/components/ui/<primitive>/index.ts`.
- Utility dependencies: use `frontend/src/lib/utils.ts` for class merging.

**Utilities:**
- Backend shared helpers: prefer module-local helpers first; promote to a shared backend module under `src/selection_maid/` only when multiple backend modules need them.
- Frontend shared helpers: add to `frontend/src/lib/`.
- Test stubs: add backend port stubs to `tests/stubs/adapters.py`.

## Special Directories

**`.planning/`:**
- Purpose: GSD project state, roadmap, requirements, phase artifacts, research, and generated codebase documents.
- Generated: Yes.
- Committed: Yes.

**`.planning/codebase/`:**
- Purpose: Generated mapper documents consumed by GSD planning/execution workflows.
- Generated: Yes.
- Committed: Yes.

**`.codex/`:**
- Purpose: Local Codex agents, skills, hooks, and GSD workflow definitions.
- Generated: Yes.
- Committed: Project-specific tooling appears in the workspace; treat modifications as workflow/tooling changes.

**`.claude/`:**
- Purpose: Local Claude agents, commands, hooks, and GSD workflow definitions.
- Generated: Yes.
- Committed: Project-specific tooling appears in the workspace; treat modifications as workflow/tooling changes.

**`.gemini/`:**
- Purpose: Local Gemini agents, commands, hooks, and GSD workflow definitions.
- Generated: Yes.
- Committed: Project-specific tooling appears in the workspace; treat modifications as workflow/tooling changes.

**`frontend/public/`:**
- Purpose: Static assets served directly by Vite.
- Generated: No.
- Committed: Yes.

**`frontend/src/assets/`:**
- Purpose: Frontend CSS and imported image assets.
- Generated: No.
- Committed: Yes.

**`tests/fixtures/`:**
- Purpose: Backend fixture generation helpers and test data support.
- Generated: Mixed; helper scripts are committed and may create local fixture outputs.
- Committed: Yes for source helpers.

**`.mypy_cache/`:**
- Purpose: Local mypy cache.
- Generated: Yes.
- Committed: No.

---

*Structure analysis: 2026-05-27*
