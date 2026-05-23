# Phase 2: Docling Extraction Adapter - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-23
**Phase:** 02-Docling Extraction Adapter
**Areas discussed:** Singleton ownership, Timeout mechanism, Integration test fixtures, Docling output mapping

---

## Singleton Ownership

### Como o DoclingAdapter deve receber o DocumentConverter?

| Option | Description | Selected |
|--------|-------------|----------|
| Injeção via construtor | `DoclingAdapter.__init__(self, converter: DocumentConverter)` — recebe converter pronto. Phase 6 cria no lifespan e injeta. Testável. | ✓ |
| Adapter cria internamente | `__init__` instancia `DocumentConverter`. Simples, mas lifespan do FastAPI fica redundante. | |
| Singleton de módulo | Criado no import time. Impossível de trocar em testes sem monkey-patching. | |

**User's choice:** Injeção via construtor
**Notes:** —

---

### Formatos aceitos: configuráveis ou hardcoded?

| Option | Description | Selected |
|--------|-------------|----------|
| Hardcoded internamente | Constante de módulo: PDF, DOCX, HTML. Simples. Formatos v2 entram como extensão futura. | ✓ |
| Configurável no construtor | `allowed_formats: set[str] | None = None`. Flexível mas complexidade desnecessária para v1. | |
| Você decide | Deixar como detalhe de implementação. | |

**User's choice:** Hardcoded internamente

---

### Como expor DoclingAdapter para consumidores?

| Option | Description | Selected |
|--------|-------------|----------|
| Classe direta + factory function | `build_docling_adapter(converter)` — padrão consistente com `build_router(service)` de Phase 6. | ✓ |
| Classe direta apenas | Sem factory. Suficiente mas menos padronizado. | |
| Você decide | Deixar como detalhe de implementação. | |

**User's choice:** Classe direta + factory function

---

## Timeout Mechanism

### Como implementar o timeout de 120s?

| Option | Description | Selected |
|--------|-------------|----------|
| ThreadPoolExecutor + future.result(timeout=120) | Portável (Windows + Linux). Thread pode continuar em background após timeout — aceito para v1 on-demand. | ✓ |
| signal.alarm (UNIX only) | Cancelamento mais limpo, mas não funciona no Windows e é unsafe em threads. | |
| multiprocessing.Process | Isolamento real, processo terminado via kill. Overhead de startup (~2-5s) e serialização complexa. | |

**User's choice:** ThreadPoolExecutor + future.result(timeout=120)
**Notes:** Thread que lingers após timeout é aceita explicitamente para v1 (low-traffic, on-demand).

---

### Timeout configurável ou fixo?

| Option | Description | Selected |
|--------|-------------|----------|
| Configurável via construtor | `timeout_seconds: int = 120` no construtor. Testes podem usar valores menores sem esperar 120s. | ✓ |
| Constante de módulo fixo | `EXTRACTION_TIMEOUT_SECONDS = 120`. Mais simples, mas exige mock para testes de timeout. | |

**User's choice:** Configurável via construtor, padrão 120s

---

## Integration Test Fixtures

### Como fornecer arquivos de fixture?

| Option | Description | Selected |
|--------|-------------|----------|
| Binários mínimos commitados em tests/fixtures/ | PDF ~10KB, DOCX ~15KB, HTML simples. Versionados no git. Rápidos e reproduzíveis. | |
| Gerados programaticamente no setup | reportlab para PDF, python-docx para DOCX. Sem binários no repo, mas adiciona dependências. | |
| Fixtures públicos baixados na primeira execução | Download on-demand com cache local (gitignored). Sem binários no repo. | ✓ |

**User's choice:** Fixtures públicos baixados na primeira execução

---

### Como gerenciar o cache das fixtures?

| Option | Description | Selected |
|--------|-------------|----------|
| pytest fixture session scope + cache local em tests/fixtures/ | Baixa uma vez, reutiliza nas execuções seguintes. tests/fixtures/ gitignored. | ✓ |
| tmp_path_factory — baixa sempre | Sem cache. Mais lento em CI repetitivo. | |
| Variável de ambiente FIXTURE_DIR | Flexível mas requer config adicional. | |

**User's choice:** pytest fixture session scope + cache local em tests/fixtures/

---

### O que acontece se o download falhar?

| Option | Description | Selected |
|--------|-------------|----------|
| pytest.skip() com mensagem clara | "Integration fixtures unavailable — skipping". Sem falha de CI por conectividade. | ✓ |
| pytest.fail() — falha explícita | Download falhou = teste falha. Força CI a garantir conectividade. | |
| Fallback para fixture mínima gerada | Complexidade maior, duas dependências. | |

**User's choice:** pytest.skip() com mensagem clara

---

## Docling Output Mapping

### Qual método do DoclingDocument usar para Markdown?

| Option | Description | Selected |
|--------|-------------|----------|
| export_to_markdown() | Método nativo. Bug #1023 (headings achatados para H2) aceito no v1. | ✓ |
| export_to_json() + parse manual | Mais controle, mas reimplementa o que export_to_markdown() já faz. Muito mais complexo. | |
| Você decide | Deixar como detalhe de implementação. | |

**User's choice:** export_to_markdown()
**Notes:** Bug de headings H2 documentado em STATE.md como concern conhecido — aceitar no v1.

---

### Como preencher page_count para HTML?

| Option | Description | Selected |
|--------|-------------|----------|
| page_count=0 para HTML, len(doc.pages) para PDF/DOCX | Explícito, compatível com D-06. | ✓ |
| Tentar extrair count de todos os formatos, 0 como fallback | Frágil e sem valor prático para HTML. | |
| Você decide | Deixar como detalhe. | |

**User's choice:** page_count=0 para HTML, len(doc.pages) para PDF/DOCX

---

### Quando lançar UnsupportedFormatError?

| Option | Description | Selected |
|--------|-------------|----------|
| Validar mime_type no início de extract() antes de chamar Docling | Rápido, explícito. Sem chamada desnecessária ao Docling. | ✓ |
| Deixar Docling falhar e capturar a exceção | Reativo, menos explorável em testes. | |

**User's choice:** Validar mime_type no início de extract() antes de chamar Docling

---

## Claude's Discretion

Nenhuma área foi delegada ao Claude — todas as decisões foram feitas pelo usuário.

## Deferred Ideas

- **multiprocessing para timeout** — Isolamento real. Descartado para v1, candidato se thread-lingering se tornar problema.
- **Formatos configuráveis via construtor** — Flexibilidade para v2 (PPTX, XLSX). Descartado para v1 (hardcoded suficiente).
- **Fixtures binárias no repo** — Descartado em favor de download on-demand.
