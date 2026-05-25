<!-- generated-by: gsd-doc-writer -->
# Getting Started

This guide takes you from a fresh clone to a running SelectionMaid instance and your first successful document ingestion.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | `>=3.13` | Set in `pyproject.toml` `requires-python` |
| uv | latest | Dependency manager, venv, and lockfile — see [docs.astral.sh/uv](https://docs.astral.sh/uv/) |

uv manages the Python version and virtual environment automatically. You do not need to create a venv manually.

---

## Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd SelectionMaid
```

### 2. Install dependencies

```bash
uv sync
```

`uv sync` reads `pyproject.toml` and `uv.lock`, creates a `.venv` in the project root, and installs all dependencies including dev tools (pytest, ruff, mypy).

> **CPU-only servers:** The project's `pyproject.toml` already pins torch to the CPU wheel via the `pytorch-cpu` index. Running `uv sync` on a machine without a GPU will pull the CPU-only PyTorch build automatically — no extra flags needed.

---

## First run

Start the development server:

```bash
uv run uvicorn selection_maid.adapters.http.app:app --reload
```

Expected output:

```
INFO:     SelectionMaid starting up — loading DocumentConverter...
INFO:     SelectionMaid ready.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

> **Note:** Docling's AI models (DocLayNet, TableFormer) load during startup. The first launch may take 30–60 seconds while model weights are downloaded and cached.

The `--reload` flag watches source files for changes and restarts the server automatically. Omit it in production.

---

## Verify the server is healthy

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status": "ok", "rss_mb": 1024.5, "uptime_seconds": 3.2, "version": "0.1.0"}
```

---

## Send your first document

POST a file to `/ingest` using multipart form data:

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@your-document.pdf;type=application/pdf"
```

Supported formats and their MIME types:

| Format | MIME type |
|--------|-----------|
| PDF | `application/pdf` |
| DOCX | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| HTML | `text/html` |

Maximum file size: **50 MB** per request (default; configurable via `config.toml`).

A successful response returns a JSON envelope with a `chunks` array. Each chunk contains the Markdown text, token count, heading context, and document-level metadata.

---

## Common setup issues

**Wrong Python version**

uv selects the Python version from `pyproject.toml` (`requires-python = ">=3.13"`). If uv cannot find a Python 3.13 interpreter, install one with:

```bash
uv python install 3.13
```

**Models downloading on every restart**

Docling caches model weights in `~/.cache/huggingface/` after the first download. If the cache directory is missing or the disk is full, models re-download on each startup. Ensure the cache directory has sufficient space (~2 GB for default models).

**Port 8000 already in use**

Run the server on an alternate port:

```bash
uv run uvicorn selection_maid.adapters.http.app:app --reload --port 8001
```

**`config.toml` not found warning at startup**

This is expected — `config.toml` is optional. The application uses hardcoded defaults when the file is absent. To customise behaviour, create `config.toml` at the project root. See [CONFIGURATION.md](CONFIGURATION.md) for all available keys.

---

## Running tests

```bash
# Full test suite (unit + integration, excluding slow tests)
uv run pytest

# Skip tests that download real fixtures or run heavy Docling processing
uv run pytest -m "not slow"

# Run only the slow integration tests
uv run pytest -m slow
```

---

## Next steps

- [ARCHITECTURE.md](ARCHITECTURE.md) — hexagonal architecture overview, component diagram, and data flow
- [CONFIGURATION.md](CONFIGURATION.md) — all `config.toml` keys with defaults and descriptions
- [DEVELOPMENT.md](DEVELOPMENT.md) — build commands, linting, formatting, and PR process
