# Phase 10: Upload Interaction - Validation

**Created:** 2026-05-26
**Status:** DRAFT

## Goal
Verify that the Upload Interaction (Phase 10) meets all success criteria and requirements, focusing on the drag-and-drop feedback, file selection, and error handling.

## Requirements Coverage

| Req ID | Description | Validation Method | Automated Test |
|--------|-------------|-------------------|----------------|
| UPL-01 | Drag and drop with animated feedback (border pulse, overlay). | Component Test (Vitest) | `DropZone.spec.ts` |
| UPL-02 | Manual file selection button. | Component Test (Vitest) | `DropZone.spec.ts` |
| NAV-02 | Structured error banner with retry. | Component Test (Vitest) | `ErrorBanner.spec.ts` |
| NAV-03 | Welcome/idle state. | Component Test (Vitest) | `DropZone.spec.ts` |

## Success Criteria Verification

| Criterion | Method | Target Output |
|-----------|--------|---------------|
| Dragging shows active state + overlay | Automated | `DropZone` shows `DropOverlay` when state is `dragging`. |
| Dropping starts upload | Automated | `useUpload.startUpload` is called on drop. |
| Button selection starts upload | Automated | `useUpload.startUpload` is called after file selection. |
| Welcome state is visible initially | Automated | `DropZone` shows welcome CTA when state is `idle`. |
| Error banner shows on failure | Automated | `DropZone` renders `ErrorBanner` when state is `error`. |
| Multiple file drop is blocked (D-04) | Automated | Error state triggered if multiple files dropped. |

## Test Scenarios

### 1. Initial State (Welcome)
- **Given** the application is loaded.
- **When** the state is `idle`.
- **Then** the `DropZone` should display the welcome message and "Select File" button.

### 2. Drag Interaction
- **Given** a user is dragging a file over the `DropZone`.
- **When** the dragging state is active.
- **Then** the `DropZone` should show the pulse animation and `DropOverlay`.

### 3. File Selection (Picker)
- **Given** the `DropZone` is in `idle` state.
- **When** the "Select File" button is clicked and a valid file is chosen.
- **Then** `startUpload` should be called with the selected file.

### 4. File Drop (Single)
- **Given** the user drops a single valid file onto the `DropZone`.
- **When** the drop occurs.
- **Then** `startUpload` should be called with the file.

### 5. File Drop (Multiple)
- **Given** the user drops multiple files onto the `DropZone`.
- **When** the drop occurs.
- **Then** an error state should be triggered (D-04) and no upload should start.

### 6. Error and Retry
- **Given** the state is `error`.
- **When** the `ErrorBanner` is visible and the "Retry" button is clicked.
- **Then** the `retry` event should be emitted and the state should return to `idle`.

## Automated Verification Commands
```bash
cd frontend
npm run test:unit src/components/upload/__tests__/DropZone.spec.ts
npm run test:unit src/components/upload/__tests__/ErrorBanner.spec.ts
```
