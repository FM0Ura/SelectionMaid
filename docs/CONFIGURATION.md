<!-- generated-by: gsd-doc-writer -->
# Configuration

SelectionMaid has two configuration surfaces:

- **Backend** — an optional `config.toml` file read at startup. All keys have
  hardcoded defaults and no section is required — the application starts
  successfully even when the file is absent or unreadable (decision D-38).
- **Frontend** — compile-time constants in `frontend/vite.config.ts` (dev-server
  proxy) and `frontend/src/lib/validators.ts` (client-side upload validation).
  The frontend uses no `.env` files; all values are committed directly to source.

---

## Environment variables

### Backend environment variables

SelectionMaid v1 uses **no environment variables** on the backend. All runtime
parameters are controlled through `config.toml` or hardcoded defaults.

### Frontend environment variables

The frontend uses **no `.env` files**. There are no `VITE_*` variables. All
configuration is expressed as TypeScript constants committed to source (see
[Frontend configuration](#frontend-configuration) below).

---

## Config file format

**Location:** `config.toml` in the current working directory when the backend
process starts. A custom path can be passed programmatically via
`get_config(config_path=Path(...))`.

**Format:** [TOML](https://toml.io/) — parsed with `tomllib` from the Python
3.11+ standard library (no extra dependency required).

Minimal working example (all four sections are independent; omit any you do not
need to override):

```toml
# SelectionMaid configuration
# All keys are optional — omitting a key uses the hardcoded default (D-38).

[filter]
min_repeat = 3
max_line_len = 80

[chunker]
max_tokens = 512

[http]
max_file_bytes = 52428800
allowed_mime_types = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/html",
]
```

---

## Required vs optional settings

**All backend settings are optional.** No missing key causes a startup failure.
When `config.toml` is absent, unreadable, or partially populated, `get_config()`
silently falls back to the hardcoded defaults shown in the tables below.

---

## Defaults

### `[filter]` — HeuristicFilter adapter

| Key             | Type    | Default | Description                                                                                              |
|-----------------|---------|---------|----------------------------------------------------------------------------------------------------------|
| `min_repeat`    | `int`   | `3`     | Minimum repetitions of a short line for it to be treated as a header/footer candidate.                   |
| `max_line_len`  | `int`   | `80`    | Maximum character length for a header/footer candidate. Longer lines are never treated as repeat noise.  |

Accessed in code as `cfg.filter.min_repeat` and `cfg.filter.max_line_len`
(dataclass: `FilterConfig`, defined in `src/selection_maid/config.py`).

### `[chunker]` — MarkdownChunker adapter

| Key           | Type    | Default | Description                                                                                               |
|---------------|---------|---------|-----------------------------------------------------------------------------------------------------------|
| `max_tokens`  | `int`   | `512`   | Maximum token budget per chunk. Also used as the subdivision limit for heading-based chunking strategies. |

Accessed in code as `cfg.chunker.max_tokens`
(dataclass: `ChunkerConfig`, defined in `src/selection_maid/config.py`).

### `[http]` — FastAPI HTTP adapter

| Key                    | Type          | Default         | Description                                                                              |
|------------------------|---------------|-----------------|------------------------------------------------------------------------------------------|
| `max_file_bytes`       | `int`         | `52428800`      | Maximum upload size in bytes for `POST /ingest`. Exceeds limit -> HTTP 413.               |
| `allowed_mime_types`   | `list[str]`   | *(see below)*   | MIME types accepted by `POST /ingest`. Unlisted types -> HTTP 415.                       |

The default for `max_file_bytes` is 52 428 800 bytes (50 MB). Default value for
`allowed_mime_types`:

```toml
allowed_mime_types = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/html",
]
```

Accessed in code as `cfg.http.max_file_bytes` and `cfg.http.allowed_mime_types`
(dataclass: `HttpConfig`, defined in `src/selection_maid/config.py`).

---

## Per-environment overrides

### Backend per-environment overrides

There are no dedicated per-environment config files (`.env.development`,
`.env.production`, etc.) in v1. To apply different settings per environment,
place a `config.toml` with the appropriate values in the working directory of
each deployment.

### Frontend per-environment overrides

The frontend has no per-environment overrides. The dev-server proxy
(`vite.config.ts`) is only active during `npm run dev` and is not bundled into
the production build.

---

## Frontend configuration

The Vue 3 SPA has two compile-time configuration surfaces.

### Dev-server proxy (`frontend/vite.config.ts`)

During local development (`npm run dev` inside `frontend/`), Vite proxies all
requests prefixed with `/api` to the backend running on `http://localhost:8000`,
stripping the `/api` prefix before forwarding:

```ts
// frontend/vite.config.ts (server.proxy section)
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  },
},
```

Effect: a fetch to `/api/ingest` in the browser becomes a request to
`http://localhost:8000/ingest` on the backend. This proxy is only used in
development; in production the SPA and API must be served from the same origin
or a reverse proxy must be configured separately. <!-- VERIFY: production serving arrangement (same-origin reverse proxy vs. separate origins with CORS) -->

### Client-side upload validation (`frontend/src/lib/validators.ts`)

The `validateFile` function enforces a 50 MB size cap and an allowlist of
accepted MIME types before the file is submitted to the backend. These values
mirror the backend `[http]` defaults and must be kept in sync manually if either
side changes.

| Constant              | Value                  | Description                                              |
|-----------------------|------------------------|----------------------------------------------------------|
| `MAX_FILE_BYTES`      | `52428800` (50 MB)     | Files larger than this are rejected before upload.       |
| `ALLOWED_MIME_TYPES`  | *(see below)*          | Files with a type outside this set are rejected.         |

Rejection messages (Portuguese, shown in the UI):

- `MAX_FILE_BYTES` exceeded: `"Arquivo muito grande. O limite máximo é 50MB."`
- `ALLOWED_MIME_TYPES` mismatch: `"Formato não suportado. Envie um arquivo PDF, DOCX ou HTML."`

Accepted MIME types for `ALLOWED_MIME_TYPES`:

- `application/pdf`
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- `text/html`

These constants are exported from `validators.ts` and can be imported by other
modules that need to reference the same limits (e.g., for UI hints):

```ts
import { MAX_FILE_BYTES, ALLOWED_MIME_TYPES, validateFile } from '@/lib/validators'

const error = validateFile(file) // returns string | null
```

---

## Enricher constants (not in config.toml)

The MetadataEnricher adapter has two parameters that are not yet exposed through
`config.toml`. They are defined as module-level constants in
`src/selection_maid/adapters/enricher/default.py` and require a code change to
adjust:

| Constant                         | Value       | Description                                                      |
|----------------------------------|-------------|------------------------------------------------------------------|
| `LANGUAGE_CONFIDENCE_THRESHOLD`  | `0.8`       | Minimum `langdetect` score; below threshold language is `"und"`. |
| `DOC_TYPE_KEYWORDS`              | see source  | Keyword lists for `legal` and `presentation` doc-type inference. |

`EnricherConfig` (the corresponding config dataclass) exists in
`src/selection_maid/config.py` but is empty in v1 — it is defined to establish
the config pattern for future extensibility.

---

## Programmatic usage

```python
from selection_maid.config import get_config
from pathlib import Path

# Read config.toml from the current working directory
cfg = get_config()

# Read from an explicit path
cfg = get_config(config_path=Path("/etc/selectionmaid/config.toml"))

# Access individual settings
threshold = cfg.filter.min_repeat      # int, default 3
max_bytes = cfg.http.max_file_bytes    # int, default 52_428_800
```
