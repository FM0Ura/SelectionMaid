# Phase 9 Validation: TypeScript Types + API Layer + State Machine

This document maps the requirements for Phase 9 to their automated verification tests, as defined in the Validation Architecture of RESEARCH.md.

## Requirements Mapping

| Req ID | Requirement | Automated Test File | Command |
|--------|-------------|---------------------|---------|
| UPL-03 | File validation (size/type) before upload | `frontend/src/lib/validators.spec.ts` | `cd frontend && npx vitest run src/lib/validators.spec.ts` |
| PROC-01 | State machine transitions and processing feedback | `frontend/src/composables/useUpload.spec.ts` | `cd frontend && npx vitest run src/composables/useUpload.spec.ts` |
| PROC-03 | Timeout handling (130s) and error mapping | `frontend/src/api/errors.spec.ts` | `cd frontend && npx vitest run src/api/errors.spec.ts` |

## Success Criteria Verification

| Criteria | Verification Method | Command |
|----------|--------------------|---------|
| TypeScript interfaces match backend schemas | Type checking | `cd frontend && npx tsc -p tsconfig.app.json --noEmit` |
| postIngest uses FormData & typed response | Type checking + Mock test | `cd frontend && npx tsc -p tsconfig.app.json --noEmit` |
| useUpload state machine transitions | Unit test | `cd frontend && npx vitest run src/composables/useUpload.spec.ts` |
| File validation (50MB/type) before network | Unit test | `cd frontend && npx vitest run src/lib/validators.spec.ts` |
| Fetch timeout 130s with clear message | Unit test | `cd frontend && npx vitest run src/api/errors.spec.ts` |

## Continuous Integration Gates

| Gate | Target | Command |
|------|--------|---------|
| Type Safety | All TS files | `cd frontend && npm run build` |
| Unit Tests | All spec files | `cd frontend && npm run test:unit -- --run` |
