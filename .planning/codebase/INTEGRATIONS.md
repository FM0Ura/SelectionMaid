# External Integrations

**Analysis Date:** 2026-05-27

## APIs & External Services

**Frontend-to-backend API:**
- SelectionMaid FastAPI backend - The Vue SPA uploads files to the backend ingestion endpoint.
  - SDK/Client: Browser `fetch` in `frontend/src/api/ingest.ts`.
  - Auth: Not applicable; no token or session auth is implemented.
  - Endpoint: `POST /api/ingest` from the browser, proxied by `frontend/vite.config.ts` to backend `POST /ingest`.
  - Timeout: `AbortSignal.timeout(130000)` in `frontend/src/api/ingest.ts`.

**Backend HTTP API:**
- FastAPI service - Exposes document ingestion and health checks.
  - SDK/Client: FastAPI / Starlette, Uvicorn ASGI.
  - Auth: None.
  - Endpoints: `GET /health` and `POST /ingest` in `src/selection_maid/adapters/http/router.py`.
  - CORS: `src/selection_maid/adapters/http/app.py` allows `http://localhost:5173` with `POST` and `OPTIONS`.

**Document AI / extraction:**
- Docling - Converts uploaded PDF, DOCX, and HTML files to Markdown.
  - SDK/Client: `docling.document_converter.DocumentConverter` instantiated in `src/selection_maid/adapters/http/app.py`.
  - Auth: Not applicable.
  - Boundary: Runtime Docling usage is isolated to `src/selection_maid/adapters/extractor/docling.py` and startup wiring in `src/selection_maid/adapters/http/app.py`.
  - Model/runtime source: Docling uses model/runtime dependencies including CPU PyTorch wheels resolved through `pyproject.toml` and `uv.lock`.

**Package/model indexes:**
- PyTorch CPU wheel index - Supplies CPU-only `torch` and `torchvision` wheels.
  - SDK/Client: uv package resolver via `[tool.uv.sources]` and `[[tool.uv.index]]` in `pyproject.toml`.
  - Auth: None detected.
  - URL: `https://download.pytorch.org/whl/cpu` configured in `pyproject.toml`.

**Browser asset services:**
- Google Fonts - Loads Inter font CSS in the frontend.
  - SDK/Client: CSS `@import` in `frontend/src/assets/index.css`.
  - Auth: None.
  - URL: `https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap`.

**Test fixture downloads:**
- External sample documents - Integration fixtures can be downloaded on demand for tests.
  - SDK/Client: `urllib.request.urlretrieve` in `tests/conftest.py` and `tests/adapters/extractor/conftest.py`.
  - Auth: None.
  - URLs: `https://www.orimi.com/pdf-test.pdf`, `https://calibre-ebook.com/downloads/demos/demo.docx`, and `https://www.w3.org/TR/WCAG20/`.
  - Runtime impact: Test-only; production code does not fetch these URLs.

## Data Storage

**Databases:**
- Not detected.
  - Connection: Not applicable.
  - Client: Not applicable.
  - Notes: `README.md` states output is ready for vector database ingestion, but this repository does not include a vector store client or persistence layer.

**File Storage:**
- Local filesystem only.
  - Uploads: `src/selection_maid/adapters/http/router.py` writes each `UploadFile` to a restricted temporary file with `tempfile.NamedTemporaryFile(delete=False, prefix="selectionmaid_")`, then deletes it in `finally`.
  - Fixtures: Tests use committed/generated files under `tests/fixtures/`.
  - Frontend assets: Static assets live under `frontend/src/assets/`.

**Caching:**
- No application cache service detected.
- Test fixture caching is local filesystem based in `tests/fixtures/`, managed by `tests/conftest.py` and `tests/adapters/extractor/conftest.py`.

## Authentication & Identity

**Auth Provider:**
- None.
  - Implementation: `src/selection_maid/adapters/http/router.py` endpoints accept unauthenticated requests.
  - Environment: No auth-related environment variables detected.
  - Project note: `.planning/REQUIREMENTS.md` marks authentication/authorization as deployment infrastructure rather than application code.

## Monitoring & Observability

**Error Tracking:**
- None detected.

**Logs:**
- Python standard logging.
  - Startup/shutdown logs in `src/selection_maid/adapters/http/app.py`.
  - Upload and processing errors logged in `src/selection_maid/adapters/http/router.py`.
  - No structured logging, external log aggregation, metrics exporter, or tracing SDK detected.

**Health:**
- `GET /health` in `src/selection_maid/adapters/http/router.py` reports `status`, RSS memory via `psutil`, uptime, and package version.

## CI/CD & Deployment

**Hosting:**
- Not detected.
  - No deployment manifest found for Docker, Compose, Vercel, Netlify, Render, Fly, or Procfile.
  - Backend deployment entry point is `selection_maid.adapters.http.app:app`.
  - Frontend production artifact is `frontend/dist/` after `cd frontend && npm run build`.

**CI Pipeline:**
- None detected.
  - No `.github/workflows/` files found.
  - Verification commands are documented in `README.md`: `uv run pytest`, `uv run ruff check src tests`, `uv run mypy src`, and `cd frontend && npm run test:unit`.

## Environment Configuration

**Required env vars:**
- None detected.

**Secrets location:**
- Not applicable.
  - No `.env*` files detected.
  - No package-manager auth files such as `.npmrc` detected in the scan.
  - Runtime settings live in `config.toml`, which contains non-secret filter/chunker/upload options.

**Runtime config files:**
- `config.toml` - Optional backend runtime settings for `[filter]`, `[chunker]`, and `[http]`.
- `pyproject.toml` - Python dependencies, tooling, uv indexes, and package metadata.
- `frontend/vite.config.ts` - Frontend dev proxy, Vue plugin, Tailwind plugin, and `@` alias.
- `frontend/vitest.config.ts` - Frontend test environment and `@` alias.

## Webhooks & Callbacks

**Incoming:**
- None detected.
  - `src/selection_maid/adapters/http/router.py` exposes direct request/response endpoints only: `GET /health` and `POST /ingest`.

**Outgoing:**
- None detected in production application code.
  - Test-only outbound downloads use `urllib.request.urlretrieve` in `tests/conftest.py` and `tests/adapters/extractor/conftest.py`.
  - Frontend browser outbound production path is limited to same-origin `/api/ingest` in `frontend/src/api/ingest.ts`.

---

*Integration audit: 2026-05-27*
