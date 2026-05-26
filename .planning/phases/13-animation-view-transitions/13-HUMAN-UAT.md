---
status: partial
phase: 13-animation-view-transitions
source: [13-VERIFICATION.md]
started: 2026-05-26T00:00:00.000Z
updated: 2026-05-26T00:00:00.000Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Global fade transition
expected: clicking "Novo Upload" triggers a sequential fade-out of results and fade-in of upload view with no simultaneous view overlap (mode="wait")
result: [pending]

### 2. Drag glow + glassmorphism
expected: holding a file over the drop zone shows pulsing OKLCH glow border and frosted backdrop-blur overlay
result: [pending]

### 3. Processing→Metadata card morph
expected: after upload completes, the processing indicator appears to expand/transform into the metadata card as a single continuous spatial element (layoutId morph)
result: [pending]

### 4. Staggered chunk cascade
expected: chunk cards enter one-by-one with a perceptible ~70ms cascade delay after the metadata card appears
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
