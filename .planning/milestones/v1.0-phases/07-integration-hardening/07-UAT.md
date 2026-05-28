# Phase 7 UAT: Integration Hardening

**UAT Session Started:** 2026-05-25

## Test 1: Full Pipeline Verification
**Goal:** Confirm the system can process PDF, DOCX, and HTML documents through the complete HTTP-to-Domain pipeline.

| Step | Action | Expected Result | Status |
|------|--------|-----------------|--------|
| 1.1 | Process `sample.pdf` | HTTP 200, valid JSON response with metadata and chunks | [x] |
| 1.2 | Process `sample.docx` | HTTP 200, valid JSON response with metadata and chunks | [x] |
| 1.3 | Process `sample.html` | HTTP 200, valid JSON response with metadata and chunks | [x] |

---

## Test 2: Concurrency and Resilience
**Goal:** Verify the system handles multiple simultaneous requests and remains alive after failures.

| Step | Action | Expected Result | Status |
|------|--------|-----------------|--------|
| 2.1 | 5 Simultaneous Ingests | All 5 requests return HTTP 200 | [x] |
| 2.2 | Liveness check | `/health` returns 200 after an ingest failure | [x] |

---

## Test 3: Memory Stability
**Goal:** Confirm proactive memory management prevents unbounded RAM growth.

| Step | Action | Expected Result | Status |
|------|--------|-----------------|--------|
| 3.1 | Memory Leak Audit | RSS growth < 2x after 5 consecutive conversions | [x] |

---

## Test 4: Input Hardening & Cleanup
**Goal:** Verify rejection of invalid inputs and consistent tempfile cleanup.

| Step | Action | Expected Result | Status |
|------|--------|-----------------|--------|
| 4.1 | Adversarial Inputs | Corrupt/Empty/Spoofed files return HTTP 422; Protected returns 500 | [x] |
| 4.2 | Tempfile Cleanup | `/tmp/selectionmaid_*` files are removed after processing | [x] |
