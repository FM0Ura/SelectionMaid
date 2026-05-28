---
status: passed
phase: 06-http-api-layer
source: [06-01-SUMMARY.md, 06-02-SUMMARY.md, 06-03-SUMMARY.md, 06-04-SUMMARY.md]
started: 2026-05-25T17:45:00Z
updated: 2026-05-25T18:30:00Z
---

## Tests

### 1. Health Check Endpoint
expected: GET /health returns 200 OK with JSON containing status, rss_mb, uptime_seconds, and version.
result: [passed] 2026-05-25 - Service responded with status: "ok", rss_mb: ~884MB, uptime: ~28s.

### 2. Ingest Success Path
expected: POST /ingest with a valid PDF/DOCX/HTML file returns 200 OK with the ExtractionResponse (metadata + chunks).
result: [passed] 2026-05-25 - POST /ingest with sample.pdf returned 258 chunks and correct metadata.

### 3. Ingest Failure: Too Large File
expected: POST /ingest with a file exceeding max_file_bytes (default 50MB) returns 413 Payload Too Large with {"error": {"code": "UPLOAD-001", ...}}.
result: [passed] 2026-05-25 - 51MB file rejected with 413 and code "UPLOAD-001".

### 4. Ingest Failure: Unsupported MIME Type
expected: POST /ingest with an unsupported MIME type (e.g. image/png) returns 415 Unsupported Media Type with {"error": {"code": "EXT-002", ...}}.
result: [passed] 2026-05-25 - MIME type 'image/png' rejected with 415 and code "EXT-002".

### 5. Ingest Failure: Magic Bytes Mismatch
expected: POST /ingest with a file whose magic bytes don't match its declared MIME type returns 422 Unprocessable Entity with {"error": {"code": "UPLOAD-002", ...}}.
result: [passed] 2026-05-25 - MIME type mismatch (README.md as application/pdf) rejected with 422 and code "UPLOAD-002".

### 6. Error Mapping: Domain Error
expected: If the service raises a domain error (e.g. ExtractionError), the API returns 500 Internal Server Error (or specific code) with the structured error body.
result: [passed] 2026-05-25 - Broken PDF triggered EXT-001 with 500 status.

### 7. Concurrency Test
expected: Multiple concurrent POST /ingest requests are handled without blocking the event loop (verified by multiple simultaneous requests completing).
result: [passed] 2026-05-25 - /health remained responsive during long-running ingestion. Note: Docling extractions are serialized by design (D-31) but non-blocking (D-88).

### 8. Configuration Overrides
expected: Modifying max_file_bytes in config.toml correctly adjusts the upload size limit.
result: [passed] 2026-05-25 - Configured 100KB limit correctly rejected 211KB file with 413.

## Summary

total: 8
passed: 8
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
