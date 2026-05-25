<!-- generated-by: gsd-doc-writer -->
# Configuration

SelectionMaid reads an optional `config.toml` file at startup. All keys have
hardcoded defaults and no section is required — the application starts
successfully even when the file is absent or unreadable (decision D-38).

There are no environment variables in v1. The sole configuration surface is
`config.toml` plus the module-level constants documented in the
[Enricher constants](#enricher-constants-not-in-configtoml) section below.

---

## Environment variables

SelectionMaid v1 uses **no environment variables**. All runtime parameters are
controlled through `config.toml` or hardcoded defaults.

---

## Config file format

**Location:** `config.toml` in the current working directory when the process
starts. A custom path can be passed programmatically via
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

**All settings are optional.** No missing key causes a startup failure. When
`config.toml` is absent, unreadable, or partially populated, `get_config()`
silently falls back to the hardcoded defaults shown in the tables below.

---

## Defaults

### `[filter]` — HeuristicFilter adapter

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `min_repeat` | `int` | `3` | Minimum number of times a short line must appear in the document to be treated as a header/footer candidate. |
| `max_line_len` | `int` | `80` | Maximum character length for a line to qualify as a header/footer candidate. Lines longer than this are never treated as repeating headers/footers. |

Accessed in code as `cfg.filter.min_repeat` and `cfg.filter.max_line_len`
(dataclass: `FilterConfig`, defined in `src/selection_maid/config.py`).

### `[chunker]` — MarkdownChunker adapter

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `max_tokens` | `int` | `512` | Maximum token budget per chunk for the fixed-size fallback strategy. Also used as the section-subdivision limit when chunking by headings. |

Accessed in code as `cfg.chunker.max_tokens`
(dataclass: `ChunkerConfig`, defined in `src/selection_maid/config.py`).

### `[http]` — FastAPI HTTP adapter

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `max_file_bytes` | `int` | `52428800` | Maximum file size accepted by `POST /ingest` in bytes. Requests whose body exceeds this limit are rejected with HTTP 413. The default is 50 MB (52 428 800 bytes). |
| `allowed_mime_types` | `list[str]` | `["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/html"]` | MIME types accepted by `POST /ingest`. Requests declaring a type outside this list are rejected with HTTP 415. |

Accessed in code as `cfg.http.max_file_bytes` and `cfg.http.allowed_mime_types`
(dataclass: `HttpConfig`, defined in `src/selection_maid/config.py`).

---

## Per-environment overrides

There are no dedicated per-environment config files (`.env.development`,
`.env.production`, etc.) in v1. To apply different settings per environment,
place a `config.toml` with the appropriate values in the working directory of
each deployment.

---

## Enricher constants (not in config.toml)

The MetadataEnricher adapter has two parameters that are not yet exposed through
`config.toml`. They are defined as module-level constants in
`src/selection_maid/adapters/enricher/default.py` and require a code change to
adjust:

| Constant | Value | Description |
|----------|-------|-------------|
| `LANGUAGE_CONFIDENCE_THRESHOLD` | `0.8` | Minimum `langdetect` probability score for a language candidate to be accepted. Scores below this threshold cause the language field to be set to `"und"` (undetermined). |
| `DOC_TYPE_KEYWORDS` | see source | Multilingual keyword lists used for `legal` and `presentation` doc-type inference. |

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
