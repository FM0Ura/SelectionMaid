# Phase 8 Validation Strategy

This document defines the verification strategy for Phase 8: Backend CORS + Project Scaffold, mapping requirements to specific automated and manual checks.

## Requirements Mapping

| Req ID | Description | Verification Type | Strategy |
|--------|-------------|-------------------|----------|
| **INT-01** | Configure CORS in FastAPI for local SPA development | Automated | Run `pytest tests/adapters/http/test_cors.py`. Verify `OPTIONS` preflight and `POST` requests include correct `Access-Control-Allow-Origin` headers for `http://localhost:5173`. |
| **UI-01** | Initialize Vue 3 project with Vite, TS, and Tailwind v4 | Automated | Run `cd frontend && npm run build`. Verify that the build completes without errors and produces assets. |
| **UI-02** | Setup shadcn-vue with Button component | Automated | Verify existence of `frontend/components.json` and `frontend/src/components/ui/button/Button.vue`. |
| **UI-03** | Configure Vite Proxy for `/api` requests | Manual/Automated | Start backend on port 8000 and frontend on 5173. Verify that a request to `http://localhost:5173/api/health` (or similar) is successfully proxied to the backend and returns the expected response without CORS errors in the browser console. |

## Verification Procedures

### Automated Tests (Regression)
Run the following command to verify backend CORS compliance:
```bash
pytest tests/adapters/http/test_cors.py
```

Run the following to verify frontend build health:
```bash
cd frontend && npm run build
```

### Manual Verification (End-to-End)
1. **Start Backend**:
   ```bash
   uvicorn selection_maid.adapters.http.app:app --port 8000
   ```
2. **Start Frontend**:
   ```bash
   cd frontend && npm run dev
   ```
3. **Check Browser**:
   - Visit `http://localhost:5173`.
   - Confirm "SelectionMaid is ready." heading is visible.
   - Confirm "Upload Document" button is visible and styled correctly (shadcn-vue).
   - Verify page background is dark (fixed dark mode).
4. **Inspect Console**:
   - Open browser developer tools.
   - Verify no 404 or CORS errors for assets or proxy attempts.
