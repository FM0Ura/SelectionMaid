<!-- generated-by: gsd-doc-writer -->
# API Reference

SelectionMaid exposes a minimal HTTP API with two endpoints: one for document ingestion and one for liveness checks. There is no authentication — the service is designed for internal/local use on a trusted network.

## Base URL

```
http://localhost:8000
```

<!-- VERIFY: base URL when deployed to a non-local environment -->

## Authentication

None. All endpoints are open.

## CORS

CORS is enabled for the following origin only:

| Allowed Origin | Allowed Methods |
|---|---|
| `http://localhost:5173` | `POST`, `OPTIONS` |

All request headers are allowed (`allow_headers: ["*"]`). Credentials are permitted.

---

## Endpoints

### POST /ingest

Upload a document for processing. The service extracts content via Docling, filters noise, splits into structure-aware Markdown chunks, and enriches each chunk with metadata.

#### Request

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | binary | Yes | Document to ingest. Accepted formats: PDF, DOCX, HTML. Maximum size: 50 MB. |

**Accepted MIME types:**

| MIME Type | Format |
|---|---|
| `application/pdf` | PDF |
| `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | DOCX |
| `text/html` | HTML |

The endpoint applies three validation layers before any domain processing:

1. **Size check** — `Content-Length` header is checked first. If the declared size exceeds 50 MB, the request is rejected immediately with `UPLOAD-001` (HTTP 413).
2. **MIME type check** — The `content_type` declared by the client is verified against the allowed list. If not accepted, the request is rejected with `EXT-002` (HTTP 415).
3. **Magic bytes check** — The first 2048 bytes of the file are read and the actual MIME type is detected via libmagic. If the detected type does not match the declared type, the request is rejected with `UPLOAD-002` (HTTP 422).

#### Response — 200 OK

Returns an `ExtractionResponse` object.

```json
{
  "metadata": {
    "doc_id": "a1b2c3d4-...",
    "source_filename": "report.pdf",
    "title": "Annual Report 2024",
    "author": "Acme Corp",
    "language": "en",
    "doc_type": "pdf",
    "page_count": 12,
    "chunk_count": 8,
    "ingested_at": "2024-11-15T10:30:00.000000+00:00"
  },
  "chunks": [
    {
      "chunk_id": "a1b2c3d4-...-0",
      "content": "## Introduction\n\nThis report covers...",
      "page_start": 1,
      "page_end": 2,
      "section_title": "Introduction",
      "chunk_index": 0,
      "total_chunks": 8,
      "word_count": 142
    }
  ]
}
```

**`metadata` fields:**

| Field | Type | Description |
|---|---|---|
| `doc_id` | `string` (UUID) | Unique identifier for this ingestion. |
| `source_filename` | `string` | Original filename as uploaded. |
| `title` | `string` | Extracted or inferred document title. Empty string if not detected. |
| `author` | `string` | Extracted or inferred author. Empty string if not detected. |
| `language` | `string` | ISO 639-1 language code (e.g., `"en"`, `"pt"`). Empty string if not detected. |
| `doc_type` | `string` | Lowercase format identifier: `"pdf"`, `"docx"`, or `"html"`. |
| `page_count` | `integer` | Number of pages in the document. `0` when unknown. |
| `chunk_count` | `integer` | Total number of chunks produced. Equal to `len(chunks)`. |
| `ingested_at` | `string` (ISO 8601) | UTC timestamp of when ingestion completed. |

**`chunks` array — each item:**

| Field | Type | Description |
|---|---|---|
| `chunk_id` | `string` | Unique identifier for this chunk. |
| `content` | `string` | Markdown text of the chunk. |
| `page_start` | `integer` | First page number this chunk originates from (1-based). |
| `page_end` | `integer` | Last page number this chunk originates from (1-based). |
| `section_title` | `string` | Heading context from which this chunk was derived. Empty string if the chunk has no heading ancestor. |
| `chunk_index` | `integer` | Zero-based position of this chunk within the document. |
| `total_chunks` | `integer` | Total number of chunks in the document. Same as `metadata.chunk_count`. |
| `word_count` | `integer` | Number of words in `content`. |

#### Example

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@/path/to/document.pdf;type=application/pdf"
```

---

### GET /health

Liveness check. Returns current process memory usage, uptime, and the installed package version.

#### Request

No parameters or body required.

#### Response — 200 OK

Returns a `HealthResponse` object. The `status` field is always `"ok"` when the service is running.

```json
{
  "status": "ok",
  "rss_mb": 312.5,
  "uptime_seconds": 4823.17,
  "version": "0.1.0"
}
```

**Fields:**

| Field | Type | Description |
|---|---|---|
| `status` | `string` | Always `"ok"` when the service is alive. |
| `rss_mb` | `float` | Resident set size of the process in megabytes (from `psutil`). |
| `uptime_seconds` | `float` | Seconds elapsed since the server started. |
| `version` | `string` | Installed package version from `importlib.metadata`. `"unknown"` if the package metadata is not available. |

#### Example

```bash
curl http://localhost:8000/health
```

---

## Error Response Format

All errors return a JSON body with the following structure:

```json
{
  "error": {
    "code": "UPLOAD-001",
    "message": "File size declared in Content-Length (60000000 bytes) exceeds maximum allowed size (52428800 bytes)."
  }
}
```

| Field | Type | Description |
|---|---|---|
| `error.code` | `string` | Machine-readable error code. |
| `error.message` | `string` | Human-readable description of the error. |

### Error Codes

| Code | HTTP Status | Meaning |
|---|---|---|
| `UPLOAD-001` | 413 Content Too Large | File size declared in `Content-Length` exceeds the 50 MB limit. |
| `UPLOAD-002` | 422 Unprocessable Entity | Magic bytes detected MIME type does not match the declared `content_type`. |
| `EXT-001` | 500 Internal Server Error | Generic extraction failure, or unexpected error during processing. |
| `EXT-002` | 415 Unsupported Media Type | Declared MIME type is not in the accepted list (PDF, DOCX, HTML). |
| `EXT-003` | 504 Gateway Timeout | Docling extraction timed out. |
| `FILT-001` | 500 Internal Server Error | Internal failure in the heuristic content filter. |
| `CHUNK-001` | 500 Internal Server Error | Internal failure during document chunking. |
| `ENRICH-001` | 500 Internal Server Error | Internal failure during metadata enrichment. |

---

## Interactive Documentation

FastAPI generates interactive API docs automatically at runtime:

| URL | Interface |
|---|---|
| `http://localhost:8000/docs` | Swagger UI |
| `http://localhost:8000/redoc` | ReDoc |
