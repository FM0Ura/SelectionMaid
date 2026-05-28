# Phase 7: Integration Hardening - Discussion Log

**Date:** 2026-05-24
**Phase:** 07-Integration Hardening

## Summary of Decisions

### Variedade de Fixtures Realistas
- **Options presented:** Básico + Erros Comuns, Adversários de Borda.
- **User selection:** Adversários de Borda.
- **Notes:** Include password-protected PDFs and large (40MB+) files to test boundary conditions of magic bytes, tempfile handling, and memory.

### Estratégia de Regressão de Memória
- **Options presented:** Monitoramento Passivo, Limpeza Proativa, Refresh Strategy.
- **User selection:** Limpeza Proativa.
- **Notes:** Use explicit `gc.collect()` after each processing cycle to mitigate Docling's heavy RAM footprint.

### Escala de Teste de Concorrência
- **Options presented:** Conservador (2 reqs), Moderado (5 reqs).
- **User selection:** Moderado (5 reqs).
- **Notes:** Verify thread safety and RAM stability with 5 simultaneous requests.

### Resiliência e Timeouts Adicionais
- **Options presented:** Recuperação de Erro (Liveness), Validação de Timeout Real.
- **User selection:** Recuperação de Erro (Liveness).
- **Notes:** Focus on ensuring the server remains alive and cleans up all temporary files after failures (corrupt/unsupported files).

## Deferred Ideas
- **Automatic Model Refresh Strategy:** Postponed to v2.
- **Per-core Concurrency Scaling:** Postponed to v2.
- **Real-time 120s Timeout Test:** Postponed to v2.

## Claude's Discretion Items
- Precise location of `gc.collect()` call (Service vs Adapter).
- Implementation of the 20-conversion batch test script.
- Selection of tools to generate/mock adversarial fixtures without external downloads.
