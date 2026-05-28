# Technology Stack

**Analysis Date:** 2026-05-27

## Languages

**Primary:**
- Python 3.13 - Backend package in `src/selection_maid/`, configured by `pyproject.toml` and `.python-version`.
- TypeScript 5.5.0 - Frontend Vue SPA in `frontend/src/`, configured by `frontend/tsconfig.json`.

**Secondary:**
- Vue SFC templates/CSS - UI components in `frontend/src/**/*.vue` and Tailwind/CSS in `frontend/src/assets/index.css`.
- TOML - Runtime configuration in `config.toml` and project metadata in `pyproject.toml`.
- Markdown - Project and planning documentation in `README.md` and `.planning/`.

## Runtime

**Environment:**
- Python 3.13+ - Required by `pyproject.toml` (`requires-python = ">=3.13"`) and `.python-version`.
- Node.js 18+ - Required for the frontend according to `README.md`.
- Browser runtime - Vue SPA served by Vite from `frontend/`, with API calls proxied to the backend.

**Package Manager:**
- uv - Backend dependency manager; lockfile: `uv.lock` present.
- npm - Frontend package manager; lockfile: `frontend/package-lock.json` present.

## Frameworks

**Core:**
- FastAPI 0.136.3 - Backend HTTP framework in `src/selection_maid/adapters/http/app.py` and `src/selection_maid/adapters/http/router.py`.
- Uvicorn 0.48.0 - ASGI server used by `README.md` command `uv run uvicorn selection_maid.adapters.http.app:app --reload`.
- Vue 3.5.34 - Frontend framework for `frontend/src/App.vue` and component tree under `frontend/src/components/`.
- Vite 6.4.2 - Frontend dev/build tool configured in `frontend/vite.config.ts`.
- Tailwind CSS 4.3.0 - Styling system loaded via `@tailwindcss/vite` in `frontend/vite.config.ts` and CSS in `frontend/src/assets/index.css`.

**Testing:**
- pytest 9.0.3 - Backend test runner configured in `pyproject.toml` with tests under `tests/`.
- pytest-asyncio 1.3.0 - Async test support configured by `asyncio_mode = "auto"` in `pyproject.toml`.
- Vitest 4.1.7 - Frontend unit test runner configured in `frontend/vitest.config.ts`.
- jsdom 29.1.1 - Frontend DOM test environment configured in `frontend/vitest.config.ts`.
- @vue/test-utils 2.4.10 - Vue component testing used by `frontend/src/**/*.spec.ts`.

**Build/Dev:**
- Hatchling - Python build backend configured in `pyproject.toml`.
- Ruff 0.15.14 - Python lint/format tool configured in `pyproject.toml`.
- mypy 2.1.0 - Strict Python type checker configured in `pyproject.toml`.
- vue-tsc 3.2.8 - Frontend type checker used by `frontend/package.json` build script.
- TypeScript 5.5.0 - Frontend compiler dependency in `frontend/package-lock.json`.

## Key Dependencies

**Critical:**
- docling 2.95.0 - Document extraction engine wrapped only by `src/selection_maid/adapters/extractor/docling.py`; instantiated at FastAPI lifespan startup in `src/selection_maid/adapters/http/app.py`.
- torch 2.12.0 / torchvision 0.27.0 - Transitive AI/model runtime dependencies resolved from the CPU-only PyTorch index configured in `pyproject.toml`.
- pydantic 2.13.4 - Response schemas in `src/selection_maid/adapters/http/schemas.py`.
- python-magic 0.4.27 - MIME/magic-byte validation in `src/selection_maid/adapters/http/router.py`.
- python-multipart 0.0.29 - Multipart upload support for FastAPI `UploadFile` in `src/selection_maid/adapters/http/router.py`.
- tiktoken 0.13.0 - Token-aware markdown chunking in `src/selection_maid/adapters/chunker/markdown.py`.
- langdetect 1.0.9 - Metadata language detection in `src/selection_maid/adapters/enricher/default.py`.

**Infrastructure:**
- psutil 7.2.2 - `/health` memory reporting in `src/selection_maid/adapters/http/router.py` and memory regression tests in `tests/test_memory_regression.py`.
- httpx 0.28.1 - Backend HTTP test client dependency declared in `pyproject.toml`.
- anyio 4.13.0 - Async test/runtime support declared in `pyproject.toml`.
- pypdf 6.12.1 - Test fixture generation/support dependency declared in `pyproject.toml`.
- @vueuse/core 14.3.0 - Upload/dropzone and clipboard helpers used in `frontend/src/composables/useUpload.ts`, `frontend/src/components/upload/DropZone.vue`, and `frontend/src/components/result/ChunkCard.vue`.
- markdown-it 14.2.0 + markdown-it-highlightjs 4.3.0 + highlight.js 11.11.1 - Markdown rendering and syntax highlighting in `frontend/src/components/result/MarkdownRenderer.vue`.
- dompurify 3.4.6 - Sanitizes rendered Markdown HTML in `frontend/src/components/result/MarkdownRenderer.vue`.
- lucide-vue-next 1.0.0 - UI icons in `frontend/src/components/`.
- motion-v 2.2.1 - Vue animations in `frontend/src/App.vue` and result/upload components.
- reka-ui 2.9.8, class-variance-authority 0.7.1, clsx 2.1.1, tailwind-merge 3.6.0, shadcn-vue 2.7.3 - shadcn-style component primitives in `frontend/src/components/ui/`.

## Configuration

**Environment:**
- Backend runtime configuration is file-based via `config.toml`; `src/selection_maid/config.py` reads `[filter]`, `[chunker]`, and `[http]` and falls back to hardcoded defaults when the file is missing or unreadable.
- No `.env*` files detected in the repository root or `frontend/`; no application code references `os.environ`, `os.getenv`, `process.env`, or `import.meta.env`.
- Backend upload settings are `http.max_file_bytes` and `http.allowed_mime_types` in `config.toml`.
- Frontend API routing is environment-independent in dev: `frontend/vite.config.ts` proxies `/api/*` to `http://localhost:8000` and rewrites the `/api` prefix.

**Build:**
- Backend project metadata, dependency groups, mypy, ruff, pytest, and uv index configuration live in `pyproject.toml`.
- Backend lockfile is `uv.lock`; use uv-managed commands from `README.md`.
- Frontend scripts and dependencies live in `frontend/package.json`; exact npm resolution lives in `frontend/package-lock.json`.
- Frontend TypeScript path alias `@/* -> frontend/src/*` is configured in `frontend/tsconfig.json`, `frontend/vite.config.ts`, and `frontend/vitest.config.ts`.
- Vite build outputs to `frontend/dist/` according to `README.md`.

## Platform Requirements

**Development:**
- Python 3.13+ with uv for backend setup: run `uv sync` and `uv run uvicorn selection_maid.adapters.http.app:app --reload`.
- Node.js 18+ with npm for frontend setup: run `cd frontend && npm install && npm run dev`.
- libmagic/system magic database must be available for `python-magic` used by `src/selection_maid/adapters/http/router.py`.
- CPU-only PyTorch wheels are pulled from the explicit `pytorch-cpu` index in `pyproject.toml`.
- Docling model initialization happens during FastAPI lifespan startup in `src/selection_maid/adapters/http/app.py`; startup may load large model assets.

**Production:**
- Deployment target not detected; no Dockerfile, compose file, Procfile, Vercel, Netlify, Render, Fly, or GitHub Actions deployment workflow is present.
- Backend is an ASGI app at `selection_maid.adapters.http.app:app`.
- Frontend is a static Vite build from `frontend/`; production hosting must route API traffic to the FastAPI backend because source code uses `/api/ingest`.

---

*Stack analysis: 2026-05-27*
