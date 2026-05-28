# Requirements: SelectionMaid

**Defined:** 2026-05-25
**Milestone:** v2.0 Frontend
**Core Value:** Documentos entram em qualquer formato, chunks Markdown normalizados saem via uma interface estável — independente da biblioteca de extração ou do protocolo de entrada usado.

## v2.0 Requirements

### Upload Interaction

- [ ] **UPL-01**: Usuário pode arrastar e soltar um arquivo na drop zone e receber feedback visual animado (border pulse, overlay com ícone) durante o drag
- [ ] **UPL-02**: Usuário pode selecionar um arquivo via botão de input clicável como alternativa ao drag-and-drop
- [ ] **UPL-03**: Usuário vê mensagem de erro imediata se tentar enviar arquivo com tipo inválido (não PDF/DOCX/HTML) ou maior que 50MB

### Processing Feedback

- [ ] **PROC-01**: Usuário vê spinner de carregamento enquanto o arquivo é enviado e o backend processa
- [ ] **PROC-02**: Usuário vê skeleton shimmer animado no lugar dos chunks enquanto aguarda a resposta da API
- [ ] **PROC-03**: Usuário recebe mensagem de erro clara se o processamento exceder 120 segundos (timeout)

### Result Display

- [x] **RES-01**: Usuário vê os chunks do documento renderizados como Markdown (não texto raw)
- [x] **RES-02**: Usuário vê os chunks revelados com stagger animation em sequência após a resposta chegar
- [x] **RES-03**: Usuário pode copiar o texto de cada chunk individualmente com um botão de copy-to-clipboard
- [x] **RES-04**: Usuário vê painel de metadados com tipo de documento, idioma, título inferido e tempo de processamento

### Navigation & Polish

- [x] **NAV-01**: Usuário experimenta transição de view animada e suave entre a tela de upload e a tela de resultado
- [ ] **NAV-02**: Usuário vê mensagem de erro estruturada com botão de retry em caso de falha na API
- [ ] **NAV-03**: Usuário vê tela de boas-vindas (estado vazio) na primeira visita antes do primeiro upload

### Backend Integration

- [ ] **INT-01**: Backend FastAPI expõe CORS configurado para a origem da SPA (CORSMiddleware em `app.py`)

## v3.0 Requirements (deferred)

### Extended Formats

- **FMT-01**: Suporte a OCR para PDFs escaneados e imagens via Docling OCR
- **FMT-02**: Suporte a PPTX e XLSX

### Configurability

- **CFG-01**: Parâmetros de chunking configuráveis por request (max_tokens, estratégia)

### Observability

- **OBS-01**: Logging estruturado com rastreamento de requests
- **OBS-02**: Métricas de processamento (tempo, tokens) expostas via endpoint

### Advanced Metadata

- **META-01**: Scores de confiança para campos inferidos
- **META-02**: Extração de metadados XMP/EXIF de imagens

## Out of Scope

| Feature | Reason |
| --- | --- |
| Autenticação / autorização | Ferramenta interna; infraestrutura do ambiente de deploy |
| Upload queue / multi-arquivo simultâneo | API backend é síncrona e processa um arquivo por vez; v1.0 não suporta |
| Barra de progresso de upload em bytes | `fetch` nativo não expõe eventos de progresso de upload; XHR adiciona complexidade desnecessária para v2.0 |
| Virtualization de lista de chunks | Listas esperadas são pequenas; adiar para v3.0 se volumes maiores surgirem |
| Markdown sanitization (DOMPurify) | Ferramenta interna; sem risco de XSS de terceiros; pode ser adicionado antes de qualquer uso compartilhado |
| SSR / Next.js / Nuxt | SPA estática é suficiente para ferramenta de uso interno |
| Acessibilidade WCAG | Uso interno; não é requisito; boas práticas de HTML semântico serão seguidas |

## Traceability

| Requirement | Phase | Status |
| --- | --- | --- |
| INT-01 | Phase 8 | Pending |
| UPL-03 | Phase 9 | Pending |
| PROC-01 | Phase 9 | Pending |
| PROC-03 | Phase 9 | Pending |
| UPL-01 | Phase 10 | Pending |
| UPL-02 | Phase 10 | Pending |
| NAV-02 | Phase 10 | Pending |
| NAV-03 | Phase 10 | Pending |
| PROC-02 | Phase 11 | Pending |
| RES-01 | Phase 12 | Complete |
| RES-03 | Phase 12 | Complete |
| RES-04 | Phase 12 | Complete |
| RES-02 | Phase 13 | Complete |
| NAV-01 | Phase 13 | Complete |

**Coverage:**

- v2.0 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0 ✓

---

Requirements defined: 2026-05-25
Last updated: 2026-05-25 after roadmap creation (traceability complete)
