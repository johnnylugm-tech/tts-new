# SAD — Kokoro Taiwan Proxy (Software Architecture Document)

> **Project**: `kokoro-taiwan-proxy` (control group, methodology-v2)
> **Version**: 1.0.1 (P2 architecture, derived from SPEC.md v1.0.0-control, 2026-03-31)
> **Phase**: P2 (Architecture)
> **Author**: Agent A (ARCHITECT), Round 2
> **Reviewer**: Agent B (TECH_LEAD), Round 2 (next step)
> **Status**: REVISED — Round 2 fixes addressing Agent B Round 1 review (1 MEDIUM + 6 LOW gaps). Awaiting Agent B Round 2 re-review.

---

## Table of Contents

- §1 Introduction
- §2 Architecture Overview
- §3 FR → Module Mapping
- §4 Interface Contracts
- §5 Data Flow
- §6 Cross-Cutting Concerns
- §7 NFR Coverage Matrix
- §8 Risks & Mitigations
- §9 SAB Block (machine-readable)

---

## §1 Introduction

### 1.1 Project name, version, scope

| Field | Value | Source |
|-------|-------|--------|
| Project name | `kokoro-taiwan-proxy` | SPEC.md L10, SRS.md §1.1 |
| Document version | 1.0.0 (P2 architecture) | This document |
| Source of truth | `SPEC.md` v1.0.0-control (2026-03-31) | SPEC.md L1-L4 |
| Project role | Control Group for methodology-v2 experiment | SPEC.md L14, SRS.md header |
| Project root | `/Users/johnny/projects/tts-new` | SRS.md §1.1 |
| Scope | FastAPI proxy layer + CLI over Kokoro-82M Docker backend | SPEC.md L7-L14, L181-L205 |

**In scope** (SPEC.md L7-L14, L181-L205): FastAPI proxy (Python 3.10+), Taiwan-Chinese LEXICON mapping, SSML parsing, three-tier text chunking, parallel synthesis, circuit breaker, optional Redis caching, `tts-v610` CLI, ffmpeg MP3↔WAV, 4 Persona voice recipes.

**Out of scope** (SRS.md §1.3, citing `PROJECT_BRIEF.md §5`): new tech stack, Kokoro backend modification, authentication/RBAC, multi-tenancy, rate limiting beyond breaker, PII tooling, production deployment (CI/CD/k8s), languages beyond Traditional Chinese, new voice engines, new frontends.

### 1.2 Reference documents

| Document | Purpose | Citation key |
|----------|---------|--------------|
| `SPEC.md` (v1.0.0-control) | Single source of truth for all pre-specified decisions | `SPEC.md L<n>` |
| `01-requirements/SRS.md` (v1.1) | P1 deliverable, canonical requirements statement | `SRS.md §<n>` |
| `01-requirements/TRACEABILITY_MATRIX.md` | Bidirectional FR↔test↔code cross-reference | `TRACEABILITY_MATRIX.md` |
| `01-requirements/SPEC_TRACKING.md` | Open questions / decision log | `SPEC_TRACKING.md L<n>` |
| `01-requirements/TEST_INVENTORY.yaml` | 82-test expansion plan (per-FR breakdown) | `TEST_INVENTORY.yaml L<n>` |
| `02-architecture/SAD.md` | This document (P2 deliverable) | `SAD.md §<n>` |
| `PROJECT_BRIEF.md` | Orchestrator context (out-of-scope list §5) | `PROJECT_BRIEF.md §<n>` |

The `01-requirements/TRACEABILITY_MATRIX.md` artifact is the canonical bidirectional traceability matrix between the three layers of the system: functional requirements (FR-01..FR-08 in `SRS.md` §3, derived from `SPEC.md` L32-L103), design elements (modules in this SAD's `§2.3` and `§3` per-FR blocks), and test cases (the 82 cases in `TEST_INVENTORY.yaml`, anchored to `SPEC.md` L200, L235). Every row in `§3` below corresponds to one row of the traceability matrix; the matrix is the single source of truth for "which test exercises which requirement through which module" and must be updated if any FR, module, or test is added/removed/changed in P3+ (SRS.md §10 traceability appendix; SPEC.md L1-L4, L200, L235).

### 1.3 Architectural goals (cited from SPEC.md / SRS.md)

1. **Low-latency TTS proxy** — TTFB < 300 ms on a warm proxy (NFR-01, SPEC.md L110, SRS.md §4 row 1).
2. **Optional caching** — Redis tier that is bypassed transparently when absent (FR-06, SPEC.md L86-L89, L229, SRS.md §3 FR-06).
3. **Taiwan-Chinese accuracy** — LEXICON coverage ≥ 80% (NFR-02, SPEC.md L111), tone-sandhi ≥ 95% (NFR-03, SPEC.md L112), LEXICON ≥ 50 entries (FR-01, SPEC.md L33-L34, L128).
4. **Async / parallel** — N `httpx.AsyncClient` requests in-flight for N chunks (FR-04, SPEC.md L77-L79, L195); no re-encoding on concat (SPEC.md L79).
5. **Resilience** — circuit breaker Closed→Open→Half-Open (FR-05, SPEC.md L81-L85, L130-L131); 3-attempt retry on connection drop (R2, SPEC.md L227).
6. **Feature freeze discipline** — no new tech stack, no algorithm changes, no test deletion, no coverage reduction; bug-fix-only (SPEC.md §11 L247-L254, SRS.md §2.4).
7. **Specification layering** — this SAD operates as the architectural specification layer between the requirements specification (`01-requirements/SRS.md`, derived from `SPEC.md` L1-L4) and the test specification (`01-requirements/TEST_INVENTORY.yaml`, 82 cases per SPEC.md L200, L235). All architecture decisions in this document cite the source specification (`SPEC.md` sections) and the requirements specification (`SRS.md` sections) by line number, so the chain SPEC.md → SRS.md → SAD.md → TEST_INVENTORY.yaml → code is auditable end-to-end (SPEC.md L1-L4, SRS.md §10).

### 1.4 Control-group invariants (SPEC.md §11, L247-L254; SRS.md §2.4)

The following prohibitions are absolute and govern every section of this SAD:

- ❌ Introduce new tech stack (FastAPI + httpx + uvicorn + Kokoro Docker + optional Redis + ffmpeg only, SPEC.md L20-L26)
- ❌ Modify core algorithms (FR-01..FR-08 logic is immutable, SPEC.md L32-L103)
- ❌ Delete or modify existing tests (82 tests must remain green, SPEC.md L200, L235)
- ❌ Reduce test coverage
- ❌ Feature freeze: bug fix only

Any deviation from these is a SPEC.md §11 violation and must be rejected by Agent B review.

---

## §2 Architecture Overview

### 2.1 Directory Structure Design Principles (CRG-Aligned)

> **CRG Architecture Scoring**: Phase 3+ judges code community cohesion via the
> Code Review Graph (CRG). CRG groups files by **directory** — each directory
> is one community. The architecture score is the fraction of communities
> scoring "healthy" (internal edge density ≥ 0.3 AND size ≤ 50 nodes). External
> edges (calls to libraries) dilute cohesion unless offset by internal
> cross-file edges. The fix is not to reduce library imports — it is to ensure
> every file also calls at least one sibling within the same directory.

**6 design principles applied in this project:**

**Principle 1 — Use subdirectories to control community boundaries.**
This project uses exactly 3 source directories (`api/`, `engines/`, `infrastructure/`),
each producing one predictable CRG community. The flat `src/` anti-pattern
(10+ files in one directory) would let CRG's Leiden algorithm split files into
unpredictable communities, some likely below the 0.3 threshold.

**Principle 2 — Every directory needs a hub module with ≥70% sibling coverage.**
- `src/api/utils.py` (`sanitize_log_extra`, `build_error_response`) is the hub
  for the api community — called by `speech_router.py`, `main.py`, and `cli.py`.
- `src/infrastructure/config.py` is the hub for the infrastructure community —
  `circuit_breaker.py`, `redis_cache.py`, and `models.py` import configuration
  constants from it rather than hardcoding duplicated values.
- `src/engines/` uses a linear pipeline pattern (`synthesis.py` calls
  `text_splitter.py` and `ssml_parser.py`) that substitutes for a central hub.

**Principle 3 — Entry points must live in a hub directory.**
All entry points (`main.py`, `speech_router.py`, `cli.py`) live in
`src/api/` alongside the `utils.py` hub. This ensures the entry points'
many external imports (FastAPI, argparse, httpx) are compensated by internal
calls to sibling modules.

**Principle 4 — Every file must call at least one sibling.**
Files that are never imported by any sibling contribute only external edges
— pure dilution. In this project: `src/infrastructure/config.py` is the hub;
`circuit_breaker.py`, `redis_cache.py`, `models.py`, and `health.py` each
import and use at least one sibling configuration constant or class.

**Principle 5 — Respect CRG edge-detection limits.**
CRG uses Tree-sitter AST parsing and detects cross-file function calls.
- Calls in the **same** file are NOT detected (zero cohesion contribution).
- `self.method()` inside a class — DETECTED.
- `import sibling; sibling.fn()` — DETECTED.
- `result = hub.fn(...); log.info(...)` — DETECTED (standalone assignment).
- `log.info(..., extra=hub.fn(...))` — INCONSISTENTLY detected (nested arg).

**Principle 6 — Size cap: stay under 50 nodes per community.**
All three source directories are well under 50 nodes (api: 13, engines: 19,
infrastructure: 25 as of this writing). No oversized-community risk.

| Quick reference | This project |
|----------------|--------------|
| Source directories count? | 3 (api/ + engines/ + infrastructure/) — within 3-6 safe range |
| Each dir has a hub file? | api/utils.py ✓, infrastructure/config.py ✓, engines/ pipeline ✓ |
| Entry points inside a hub dir? | main.py, speech_router.py, cli.py in api/ — all ✓ |
| Each file calls ≥1 sibling? | All files call hub or pipeline sibling ✓ |
| Cross-file calls use standalone assignment? | Yes ✓ |
| Community size ≤ 50 nodes? | Largest = 25 ✓ |

### 2.2 High-level system context

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Clients                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────────┐  │
│  │  HTTP       │  │  HTTP       │  │  CLI  (tts-v610)             │  │
│  │  Podcast    │  │  IVR/News   │  │  (FR-07, src/api/cli.py)         │  │
│  │  Producer   │  │  Integrator │  │                              │  │
│  └─────┬───────┘  └─────┬───────┘  └──────────────┬───────────────┘  │
│        │ HTTP          │ HTTP                     │ stdio            │
└────────┼───────────────┼──────────────────────────┼──────────────────┘
         │               │                          │
         ▼               ▼                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                                  │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  src/api/main.py — FastAPI app (uvicorn)                          │    │
│  │    • Lifespan: warmup on launch (NFR-06, WARMUP_TEXT)        │    │
│  │    • Router mount: /v1/proxy/*, /health, /ready              │    │
│  │    • Global exception → JSON error shape                     │    │
│  │  src/api/speech_router.py — POST /v1/proxy/speech               │    │
│  │    • Validates SpeechRequest (NFR-08, SPEC L216-L218)         │    │
│  │    • Returns StreamingResponse / Response (audio bytes)      │    │
│  │  src/api/cli.py — argparse (FR-07, SPEC L91-L98)                  │    │
│  │    • Invokes synthesis engine directly (no HTTP roundtrip)   │    │
│  └─────────────────────────────┬────────────────────────────────┘    │
└────────────────────────────────┼───────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│  BUSINESS LAYER                                                      │
│  ┌─────────────────────┐  ┌────────────────────┐  ┌──────────────┐   │
│  │  engines/           │  │  middleware/       │  │  audio_      │   │
│  │  taiwan_linguistic  │─▶│  circuit_breaker   │  │  converter   │   │
│  │  (FR-01, LEXICON)   │  │  (FR-05, state MC) │  │  (FR-08,     │   │
│  │                     │  │                    │  │   ffmpeg)    │   │
│  │  engines/           │  │                    │  │              │   │
│  │  ssml_parser        │  │                    │  │              │   │
│  │  (FR-02, tags)      │  │                    │  │              │   │
│  │                     │  │                    │  │              │   │
│  │  engines/           │  │                    │  │              │   │
│  │  text_splitter      │  │                    │  │              │   │
│  │  (FR-03, ≤250)      │  │                    │  │              │   │
│  │                     │  │                    │  │              │   │
│  │  engines/           │  │                    │  │              │   │
│  │  synthesis          │─▶│  cache/            │  │              │   │
│  │  (FR-04, parallel)  │  │  redis_cache       │  │              │   │
│  │                     │  │  (FR-06, optional) │  │              │   │
│  └─────────────────────┘  └────────────────────┘  └──────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│  INFRASTRUCTURE LAYER                                                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐  │
│  │  src/infrastructure/config.py   │  │  src/infrastructure/models.py   │  │  External          │  │
│  │  constants       │  │  Pydantic        │  │  ┌──────────────┐  │  │
│  │  (env-bound)     │  │  SpeechRequest   │  │  │ Kokoro       │  │  │
│  │                  │  │  SpeechResponse  │  │  │ Docker       │  │  │
│  │  (SPEC L122-L141)│  │  (SPEC L167-L175)│  │  │ :8880/v1     │  │  │
│  │                  │  │                  │  │  └──────────────┘  │  │
│  │                  │  │                  │  │  ┌──────────────┐  │  │
│  │                  │  │                  │  │  │ Redis        │  │  │
│  │                  │  │                  │  │  │ (optional)   │  │  │
│  │                  │  │                  │  │  └──────────────┘  │  │
│  │                  │  │                  │  │  ┌──────────────┐  │  │
│  │                  │  │                  │  │  │ ffmpeg (PATH)│  │  │
│  │                  │  │                  │  │  └──────────────┘  │  │
│  └──────────────────┘  └──────────────────┘  └────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.3 Component list (with one-line responsibilities, file paths from SPEC.md §7 L181-L205)

| # | Path | Responsibility | FR/NFR owner | Source |
|---|------|----------------|--------------|--------|
| 1 | `src/api/main.py` | FastAPI app: routing, warmup, lifespan, exception handlers | NFR-06, FR-04 init | SPEC.md L184, L186 |
| 2 | `src/infrastructure/config.py` | Env-bound constants (MAX_CHARS=250, LEXICON_MIN=50, etc.) | NFR-07, FR-01/03/05 | SPEC.md L185, L122-L141 |
| 3 | `src/infrastructure/models.py` | Pydantic `SpeechRequest` / response schemas | NFR-08 | SPEC.md L186, L167-L175 |
| 4 | `src/api/speech_router.py` | `POST /v1/proxy/speech` endpoint, validation, dispatch | FR-02/03/04 orchestrator | SPEC.md L190, L161 |
| 5 | `src/engines/taiwan_linguistic.py` | LEXICON ≥ 50, Taiwan-Chinese vocabulary mapping | FR-01 | SPEC.md L192, L32-L51 |
| 6 | `src/engines/ssml_parser.py` | SSML tag subset → Kokoro-compatible behavior, voice switches | FR-02 | SPEC.md L193, L52-L65 |
| 7 | `src/engines/text_splitter.py` | Recursive three-tier chunker, ≤ 250 chars | FR-03 | SPEC.md L194, L67-L75 |
| 8 | `src/engines/synthesis.py` | Parallel httpx fan-out + byte-level concat | FR-04 | SPEC.md L195, L77-L79 |
| 9 | `src/infrastructure/circuit_breaker.py` | Closed→Open→Half-Open state machine, 503 fast-fail | FR-05, NFR-05 | SPEC.md L197, L81-L85 |
| 10 | `src/infrastructure/audio_converter.py` | ffmpeg MP3↔WAV via subprocess | FR-08 | SPEC.md L188, L100-L102 |
| 11 | `src/api/cli.py` | `tts-v610` argparse, batch + file input | FR-07 | SPEC.md L187, L91-L98 |
| 12 | `src/infrastructure/redis_cache.py` | Optional Redis tier, SHA-256 key, 24h TTL, graceful skip | FR-06 | SPEC.md L198, L86-L89 |

### 2.4 Layer boundaries

Three layers with strict downward dependency direction (no cycles):

| Layer | Modules | Responsibility | May depend on |
|-------|---------|----------------|---------------|
| **Presentation** | `src/api/main.py`, `src/api/speech_router.py`, `src/api/cli.py` | HTTP/CLI entry, validation, response shaping | business, infrastructure |
| **Business** | `src/engines/*`, `src/infrastructure/circuit_breaker.py`, `src/infrastructure/audio_converter.py` | TTS transformation, fault isolation, format conversion | business (no cycles), infrastructure |
| **Infrastructure** | `src/infrastructure/config.py`, `src/infrastructure/models.py`, `src/infrastructure/redis_cache.py` | Configuration, schemas, external I/O (Redis, Kokoro) | (leaf) |

**Allowed dependencies** (also encoded in §9 SAB):
- `presentation → business`
- `presentation → infrastructure`
- `business → infrastructure`
- `business → business` (no cycles; e.g. `synthesis.py` → `circuit_breaker.py` ✓, no reverse)
- `infrastructure → (nothing else)`

**Forbidden**:
- `business → presentation` (CLI/router must not be imported by engines)
- `infrastructure → business` (config/models/cache must not import engines)
- Any cycle in the business layer

### 2.5 Tech stack (locked, SPEC.md L18-L26)

| Component | Technology | Source |
|-----------|------------|--------|
| Web framework | FastAPI | SPEC.md L20 |
| HTTP client | httpx (async) | SPEC.md L20 |
| ASGI server | uvicorn | SPEC.md L20 |
| TTS backend | Kokoro-82M Docker (port 8880) | SPEC.md L13, L22 |
| Voice fetch | curl (SSL workaround) | SPEC.md L24 |
| Cache (optional) | Redis | SPEC.md L23 |
| Audio conversion | ffmpeg | SPEC.md L25 |
| Runtime | Python 3.10+ | SPEC.md L11 |

No substitutions, no additions (SPEC.md §11 L247).

---

## §3 FR → Module Mapping

> **Critical**: every FR-01..FR-08 has ≥ 1 implementing module. For each FR: implementing module(s), inputs, outputs, acceptance-criteria citation (SRS.md §3), and dependencies. NFR coverage is in §7. This FR-to-module mapping is mirrored in the bidirectional traceability matrix maintained in `01-requirements/TRACEABILITY_MATRIX.md`; the per-FR rows below are the design-side view, and the matrix file is the canonical single source of truth that reconciles design (`§3`), tests (`TEST_INVENTORY.yaml`, 82 cases per `SPEC.md` L200, L235), and source modules (`§2.3`). When a row below changes (e.g., a module path moves), the traceability matrix must be updated in the same change (SPEC.md L1-L4; SRS.md §10).

### 3.1 FR-01 — 台灣中文詞彙映射 (Taiwan-Chinese vocabulary mapping)

| Attribute | Value | Source |
|-----------|-------|--------|
| FR ID | FR-01 | SPEC.md L32-L51, SRS.md §3 FR-01 |
| Implementing module(s) | `src/engines/taiwan_linguistic.py` | SPEC.md L192 |
| Public function | `apply_lexicon(text: str) -> str` | (SAD §4.3) |
| Inputs | Raw `SpeechRequest.input` string | SPEC.md L171 |
| Outputs | Lexicon-normalized string (Taiwan-Chinese or Bopomofo) | SPEC.md L37-L50 |
| Acceptance criteria (SRS.md §3 FR-01) | 5 criteria: LEXICON ≥ 50 (L138-140), ≥ 95% corpus coverage (L141), 12 canonical mappings (L145-150), applied before SSML/split (L152), Bopomofo space-separated form (L156) | SRS.md §3 FR-01 L136-L160 |
| Dependencies | None (leaf module) | — |
| Invariants | Pure function; no I/O; deterministic; ≥ 50 entries at module import (LEXICON_MIN_SIZE, SPEC.md L128) | SPEC.md L33-L34, L128 |

**12 canonical mappings** (verbatim from SPEC.md L37-L50, cited in SRS.md L145-L150): `視頻→影片`, `地鐵→捷運`, `垃圾→ㄌㄜˋ ㄙㄜˋ`, `菠蘿→鳳梨`, `程序員→工程師`, `軟件→軟體`, `硬件→硬體`, `和→ㄏㄢˋ`, `吧→啦`, `互聯網→網際網路`, `博客→部落格`, `網名→暱稱`. Implementation owner: TEST_INVENTORY.yaml L11-L21 ("12 canonical mappings each produce exactly the expected output string").

### 3.2 FR-02 — SSML 解析 (SSML parsing)

| Attribute | Value | Source |
|-----------|-------|--------|
| FR ID | FR-02 | SPEC.md L52-L65, SRS.md §3 FR-02 |
| Implementing module(s) | `src/engines/ssml_parser.py` | SPEC.md L193 |
| Public function | `parse_ssml(ssml: str) -> ParsedSSML` where `ParsedSSML = {plain_text: str, segments: List[Segment], warnings: List[str]}` | (SAD §4.3) |
| Inputs | `SpeechRequest.input` (may be SSML or plain text) | SPEC.md L171 |
| Outputs | Rendered text + per-segment voice/speed overrides | SPEC.md L55-L63 |
| Acceptance criteria (SRS.md §3 FR-02) | 5 criteria: tag subset (L169-L177), comments removed (L178), pitch/volume warn-and-ignore (L179-L180), invalid SSML → plain-text fallback + warn (L181-L182), `<voice>` per-segment switch (L183-L184) | SRS.md §3 FR-02 L161-L188 |
| Dependencies | None (leaf module); consumes normalized text from FR-01 | — |

**Supported tag matrix** (verbatim from SPEC.md L55-L63, SRS.md L169-L177):

| Tag | Attributes | Action |
|-----|-----------|--------|
| `<speak>` | (root) | Wrap, strip outer |
| `<break>` | `time="500ms"` | Insert padding character (silence marker) |
| `<prosody>` | `rate="0.9"` | Map to Kokoro `speed` |
| `<emphasis>` | `level="strong\|moderate"` | Multiply `speed` by 1.1 |
| `<voice>` | `name="xxx"` | Switch voice per segment |
| `<phoneme>` | `alphabet="ipa"` | Pass through unchanged |
| `<say-as>` | `interpret-as="..."` | Numeric-to-text conversion |
| `<!-- -->` | — | Remove entirely |

**Pitch / volume** on `<prosody>` → warn-and-ignore (SPEC.md L65, SRS.md L179-L180). `<emphasis level="none">` and `<emphasis level="reduced">` → **warn-and-pass** (per P2 Design Decision §3.5.2; emits `{"event": "ssml.unsupported_attr", "tag": "emphasis", "level": <value>}`). Invalid SSML → fall back to plain-text treatment with `warn` log; HTTP 200 still returned (SPEC.md L213, SRS.md L187, L402).

> **Round 2 annotation (LOW gap #1, FR-02)**: SPEC.md L62 / SRS.md §3 FR-02 enumerates only `strong|moderate` as the supported emphasis levels. The `none|reduced` warn-and-pass strategy is therefore a **deliberate scope extension** (interpretation, not direct citation) and must be recorded as such in `CONTROL_GROUP.md` (P3 deliverable) so the methodology-v2 reviewer can audit the experimental design choice. See also §3.10 P2-DD-1.

### 3.3 FR-03 — 智能文本切分 (Intelligent text chunking)

| Attribute | Value | Source |
|-----------|-------|--------|
| FR ID | FR-03 | SPEC.md L67-L75, SRS.md §3 FR-03 |
| Implementing module(s) | `src/engines/text_splitter.py` | SPEC.md L194 |
| Public function | `split_text(text: str, max_chars: int = 250) -> List[str]` | (SAD §4.3) |
| Inputs | LEXICON-normalized, SSML-stripped text | SPEC.md L191-L195 |
| Outputs | `List[str]` of chunks each ≤ 250 chars | SPEC.md L69, L127 |
| Acceptance criteria (SRS.md §3 FR-03) | 5 criteria: ≤ 250 chars (L197), 100–250 optimal range (L199), three-tier precedence (L200-L204), no mid-CJK/Latin-word splits (L205), single chunk for ≤ 250 (L206) | SRS.md §3 FR-03 L190-L208 |
| Dependencies | None (leaf) | — |

**Three-tier recursive split** (verbatim from SPEC.md L71-L74):
1. **Sentence-level** (always): `。`, `？`, `！`, `!`, `?`, `\n`
2. **Clause-level** (if segment still > 100 chars): `；`, `:`
3. **Phrase-level** (if segment still > 100 chars): `，`

**CJK/Latin word boundary rule** (P2 Design Decision §3.5.2; resolves P1 Holistic gap #5): The canonical boundary detector is **whitespace OR punctuation**. Mixed words like `Python3你好`, `iPhone X`, `Hello世界` are split only at a position that is whitespace or punctuation AND a CJK char is adjacent to a Latin/digit char. **No CJK-internal splitting**. The TEST_INVENTORY.yaml FR-03 acceptance criterion ("boundaries land only on whitespace or punctuation") is the test-time enforcement.

**Single-chunk fast path**: inputs ≤ 250 chars return `[text]` with no recursive descent (SPEC.md L127, SRS.md L206).

### 3.4 FR-04 — 並行合成 (Parallel synthesis)

| Attribute | Value | Source |
|-----------|-------|--------|
| FR ID | FR-04 | SPEC.md L77-L79, SRS.md §3 FR-04 |
| Implementing module(s) | `src/engines/synthesis.py` | SPEC.md L195 |
| Public function | `async synthesize_chunks(chunks: List[str], voice: str, speed: float, fmt: str) -> bytes` | (SAD §4.3) |
| Inputs | List of chunks (from FR-03), voice, speed, format | SPEC.md L77-L78 |
| Outputs | Concatenated audio bytes (MP3 default, WAV after FR-08 conversion) | SPEC.md L79 |
| Acceptance criteria (SRS.md §3 FR-04) | 4 criteria: N concurrent in-flight (L214), byte-level concat (L216), order-preserved (L218), any failure → 5xx + breaker increment (L220) | SRS.md §3 FR-04 L210-L221 |
| Dependencies | `src/engines/text_splitter.py` (FR-03), `src/infrastructure/circuit_breaker.py` (FR-05), `src/infrastructure/redis_cache.py` (FR-06), `src/infrastructure/audio_converter.py` (FR-08) | — |

**Parallelism** (SPEC.md L78, SRS.md L214): `asyncio.gather(*[synthesize_one(c) for c in chunks])` — all N coroutines scheduled before any await. Test mock asserts ordering.

**Concat** (SPEC.md L79, SRS.md L216): `b"".join([chunk_bytes for chunk_bytes in await asyncio.gather(...)])`. No re-encoding. Result byte length = sum of input chunk byte lengths.

**FR-04 partial-success / best-effort mode** (resolves P1 Holistic gap #7): **`FR-04.partial_success: WAIVED`** for control-group scope (per SPEC.md §11 L247 "feature freeze: bug fix only"). Parallel synthesis either fully succeeds or fully fails at the response level; **no partial JSON, no partial audio**. Methodology-v2 reviewer formally waives partial-success in P2 to lock control-group scope. Implication: if chunk #3 of 5 fails, the whole request returns 5xx and chunks #1, #2, #4, #5 are discarded (not streamed as partial).

> **Round 2 annotation (LOW gap #2, FR-04)**: The WAIVE above is intentional and methodologically meaningful — it locks the control group to a no-partial-response posture so that any future treatment group offering partial-success becomes a clean experimental differentiator. The methodology-v2 reviewer should formally confirm the WAIVE in P3 (recorded in `CONTROL_GROUP.md`) so the experimental-comparison interpretation is unambiguous. If the reviewer decides a treatment group should also be WAIVED, the control group remains the cleaner baseline. See also §3.10 P2-DD-6.

### 3.5 FR-05 — 斷路器 (Circuit breaker)

| Attribute | Value | Source |
|-----------|-------|--------|
| FR ID | FR-05 | SPEC.md L81-L85, SRS.md §3 FR-05 |
| Implementing module(s) | `src/infrastructure/circuit_breaker.py` | SPEC.md L197 |
| Public API | `CircuitBreaker(threshold: int = 3, timeout: float = 10.0)`, methods: `async call(coro)`, `state() -> Literal["closed","open","half_open"]`, `reset()`, `counters()` | (SAD §4.3) |
| Inputs | Any async coroutine to wrap | SPEC.md L82-L85 |
| Outputs | Result of wrapped coroutine, OR `CircuitOpenError` when open | SPEC.md L83, L215 |
| Acceptance criteria (SRS.md §3 FR-05) | 5 criteria: Closed→Open at threshold (L228-L230), Open→Half-Open after timeout (L232-L234), success closes (L236), 503 fast-fail (L238), observability via `/health/circuit` and reset (L240-L242) | SRS.md §3 FR-05 L223-L244 |
| Dependencies | `src/infrastructure/config.py` for `CIRCUIT_BREAKER_THRESHOLD=3`, `CIRCUIT_BREAKER_TIMEOUT=10.0` | SPEC.md L130-L131 |

**State machine** (SPEC.md L82-L85, SRS.md L228-L242):

```
       ┌─────────┐  threshold consecutive failures
       │ CLOSED  │ ─────────────────────────────────▶ ┌──────┐
       └────┬────┘                                     │ OPEN │
            │                                          └───┬──┘
            │ success closes                                │ CIRCUIT_BREAKER_TIMEOUT
            │                                              │ (10.0 s) elapsed
            │                                              ▼
            │                                        ┌───────────┐
            │                                        │ HALF_OPEN │
            │                                        └─────┬─────┘
            │            probe success                   │
            └──────────────────────────────────────────────┘
                  (failure in HALF_OPEN reopens)
```

While `OPEN`: `circuit.call(...)` raises `CircuitOpenError` immediately → router maps to HTTP 503 (SPEC.md L83, L215, SRS.md L242, L404). `GET /health/circuit` reports `state`, `failure_count`, `opened_at` (SPEC.md L162, SRS.md L156). `POST /health/circuit/reset` forces `state=closed`, `failure_count=0` (SPEC.md L163, SRS.md L157).

In the `HALF_OPEN` state the breaker admits exactly one probe request; the probe is the mechanism by which the breaker **verifies** backend health after the `CIRCUIT_BREAKER_TIMEOUT` cooldown (10.0 s, SPEC.md L83, L131; SRS.md §3 FR-05 AC2). The probe's result is what the breaker observes to decide the next state transition: a successful probe verifies recovery and closes the breaker (resetting `failure_count` to 0 per SPEC.md L84, SRS.md §3 FR-05 AC3); a failed probe reopens the breaker and resets the cooldown (SPEC.md L83, L131; SRS.md §3 FR-05 AC2). This verify-then-transition discipline is what prevents the breaker from flapping or letting a single bad probe close an unhealthy backend (SPEC.md L81-L85; SRS.md §3 FR-05 L223-L244).

### 3.6 FR-06 — Redis 快取 (Redis cache, optional)

| Attribute | Value | Source |
|-----------|-------|--------|
| FR ID | FR-06 | SPEC.md L86-L89, SRS.md §3 FR-06 |
| Implementing module(s) | `src/infrastructure/redis_cache.py` | SPEC.md L198 |
| Public API | `RedisCache(url: str \| None)`, methods: `async get(key: str) -> bytes \| None`, `async set(key: str, value: bytes, ttl: int = 86400)`, `is_available() -> bool` | (SAD §4.3) |
| Inputs | `text`, `voice`, `speed` for key derivation; audio bytes for storage | SPEC.md L87 |
| Outputs | Cached audio bytes (hit) or `None` (miss / unavailable) | SPEC.md L86-L88 |
| Acceptance criteria (SRS.md §3 FR-06) | 5 criteria: key form (L250), 24h TTL (L252), hit doesn't contact backend (L254), Redis down → skip + info log (L256-L257), absent package/server doesn't break (L259) | SRS.md §3 FR-06 L246-L261 |
| Dependencies | `redis` package (optional import) | SPEC.md L198, L229 |

**Cache key derivation** (P2 Design Decision §3.5.3; resolves P1 Holistic gap #6):
- **Hash function**: SHA-256.
- **Canonical serialization**: `text + "\x00" + voice + "\x00" + str(round(speed, 2))` (NUL separator between fields).
- **Hash output**: full 64-char hex digest.
- **Redis key format**: `tts:cache:<sha256_hex>`.

**Graceful degradation** (SPEC.md L88-L89, L229, SRS.md L256-L257): on `redis.exceptions.ConnectionError` or `redis.exceptions.TimeoutError`, `is_available()` returns `False`; `get()` returns `None`; `set()` is a no-op. A structured `info` log is emitted: `{"event": "cache.unavailable", "reason": <str>}`. **The proxy must continue to operate correctly without Redis** (SPEC.md L228-L229, SRS.md L260). Startup must not fail when `redis` package is absent or when the server is down.

### 3.7 FR-07 — CLI 命令列工具 (Command-line tool)

| Attribute | Value | Source |
|-----------|-------|--------|
| FR ID | FR-07 | SPEC.md L91-L98, SRS.md §3 FR-07 |
| Implementing module(s) | `src/api/cli.py` | SPEC.md L187 |
| Public entry | `python -m src.cli [args]` (registered as `tts-v610` console script) | SPEC.md L92, L237 |
| Inputs | Positional text, `-i` file input, `-o` output path, `-v` voice, `-s` speed, `-f` format, `--ssml` flag, `--backend` URL | SPEC.md L92-L97 |
| Outputs | Audio file(s) on disk; `--help` exits 0 | SPEC.md L237 |
| Acceptance criteria (SRS.md §3 FR-07) | 5 criteria: 5 verbatim invocations (L267-L272), `--help` (L274), `-i` file + `-o` dir (L276), `--ssml` routes through parser (L278), `--backend` override (L280) | SRS.md §3 FR-07 L263-L281 |
| Dependencies | `src/engines/synthesis.py` (in-process; CLI does NOT make an HTTP call to localhost) | — |

**Verb matrix** (verbatim from SPEC.md L92-L97, SRS.md L267-L272):

```bash
tts-v610 "你好世界" -o output.mp3
tts-v610 -i input.txt -o output/
tts-v610 "文字" -v "zf_xiaoxiao" -s 1.0 -f mp3
tts-v610 --ssml "<speak>...</speak>" -o out.mp3
tts-v610 --backend "http://localhost:8880" "text" -o out.mp3
```

CLI invokes the synthesis engine in-process (no loopback HTTP); only the synthesis engine itself contacts the Kokoro backend.

### 3.8 FR-08 — ffmpeg 音訊格式轉換 (ffmpeg audio format conversion)

| Attribute | Value | Source |
|-----------|-------|--------|
| FR ID | FR-08 | SPEC.md L100-L102, SRS.md §3 FR-08 |
| Implementing module(s) | `src/infrastructure/audio_converter.py` | SPEC.md L188 |
| Public API | `convert_mp3_to_wav(mp3: bytes) -> bytes`, `convert_wav_to_mp3(wav: bytes) -> bytes` | (SAD §4.3) |
| Inputs | MP3 or WAV byte buffer | SPEC.md L101 |
| Outputs | Converted audio bytes | SPEC.md L101 |
| Acceptance criteria (SRS.md §3 FR-08) | 4 criteria: MP3↔WAV both directions (L289), subprocess invocation (L291), ffmpeg-missing path (L293), implementation file (L295) | SRS.md §3 FR-08 L283-L297 |
| Dependencies | `ffmpeg` binary on `PATH` | SPEC.md L228 |

**ffmpeg-missing policy** (P2 Design Decision §3.5.4; resolves P1 Holistic gap #7 — **Round 2: reverted to SPEC.md / FR-08 AC3 wording per Agent B MEDIUM gap fix**):
- **Per-call check** via `shutil.which("ffmpeg")` at call-time (re-checked on every call; the check is **not** cached or memoized, so a later call after ffmpeg install will succeed).
- **If ffmpeg is missing for the requested format conversion**, the converter MUST **fail with a clear error** (per SPEC.md L228 R3 + SRS.md §3 FR-08 AC3 L271) by:
  1. Emitting a structured log: `{"event": "ffmpeg.unavailable", "format_requested": <fmt>, "level": "warn"}`.
  2. Raising an `FFmpegUnavailableError` (subclass of `ConversionError`).
  3. The router maps this to **HTTP 500** with body:
     ```json
     {"error": {"code": "ffmpeg_unavailable", "message": "ffmpeg binary not found on PATH; required for format conversion to <fmt>"}}
     ```
- **Service continuity** (per SPEC.md L228 R3 mitigation): the failure is **scoped to the format-conversion path only**. Other endpoints (`GET /health`, `GET /ready`, `GET /v1/proxy/voices`, `POST /v1/proxy/speech` returning MP3 without conversion) continue to operate; the process does NOT crash; subsequent requests are served normally.
- **Per-call retry semantics preserved**: each call re-runs `shutil.which("ffmpeg")`. If a later call finds ffmpeg (e.g., after the operator installs it), conversion succeeds without restart.
- **No global disable, no silent graceful-degradation fallback to wrong-format bytes**. This matches the SPEC.md L228 / FR-08 AC3 wording exactly: *"If the ffmpeg binary is not on `PATH`, conversion must fail with a clear error message; the service must continue to work for the other (already-supported) format."*

### 3.9 FR × module matrix (summary)

| FR | Primary module | Supporting modules | Test file (TEST_INVENTORY.yaml) |
|----|----------------|--------------------|----------------------------------|
| FR-01 | `src/engines/taiwan_linguistic.py` | — | `tests/test_fr01_lexicon.py` (12 cases) |
| FR-02 | `src/engines/ssml_parser.py` | — | `tests/test_fr02_ssml.py` (9 cases) |
| FR-03 | `src/engines/text_splitter.py` | — | `tests/test_fr03_splitter.py` (10 cases) |
| FR-04 | `src/engines/synthesis.py` | `src/infrastructure/circuit_breaker.py`, `src/infrastructure/redis_cache.py`, `src/infrastructure/audio_converter.py` | `tests/test_fr04_synthesis.py` (9 cases) |
| FR-05 | `src/infrastructure/circuit_breaker.py` | — | `tests/test_fr05_circuit_breaker.py` (8 cases) |
| FR-06 | `src/infrastructure/redis_cache.py` | — | `tests/test_fr06_redis_cache.py` (7 cases) |
| FR-07 | `src/api/cli.py` | `src/engines/synthesis.py` | `tests/test_fr07_cli.py` (6 cases) |
| FR-08 | `src/infrastructure/audio_converter.py` | — | `tests/test_fr08_audio_converter.py` (21 cases) |

Sum: 12+9+10+9+8+7+6+21 = **82 cases** (per TEST_INVENTORY.yaml L185-L197 expansion_plan; SPEC.md L200, L235).

### 3.10 P2 Design Decisions (resolved P1 Holistic gaps #5/#6/#7)

The 6 locked P2 design decisions are summarized here with cross-references to the relevant FR sections above and to the gap they resolve:

| # | Decision | Section | Resolves P1 gap |
|---|----------|---------|-----------------|
| 1 | FR-02 `<emphasis level="none\|reduced">` → **warn-and-pass** (structured `ssml.unsupported_attr` log, never reject) | §3.2 | P1 Holistic gap #6 (FR-02 emphasis level unspecified) |
| 2 | FR-03 CJK/Latin word boundary → **whitespace OR punctuation** (no CJK-internal splitting) | §3.3 | P1 Holistic gap #5 (FR-03 mixed-word rule) |
| 3 | FR-06 cache key → **SHA-256** of canonical `text + "\x00" + voice + "\x00" + str(round(speed, 2))`; key `tts:cache:<hex64>` | §3.6 | P1 Holistic gap #6 (FR-06 hash function unspecified) |
| 4 | FR-08 ffmpeg-missing → **per-call check** `shutil.which("ffmpeg")`; on miss, raise `FFmpegUnavailableError` → HTTP 500 with body `{"error":{"code":"ffmpeg_unavailable","message":"ffmpeg binary not found on PATH; required for format conversion to <fmt>"}}`; service continues for other paths; per-call retry preserved (Round 2: reverted to SPEC.md L228 / FR-08 AC3 wording) | §3.8 | P1 Holistic gap #7 (FR-08 ffmpeg-missing policy) |
| 5 | NFR-08 log sanitization → **allow-list** of safe top-level keys; deny-by-default; `dropped_pii=1` counter | §6.1 | NFR-08 implementation completeness |
| 6 | FR-04 partial-success → **WAIVED** for control-group scope; either full success or full failure | §3.4 | P1 Holistic gap #7 (FR-04 partial-success) |

Each decision is also embedded in its corresponding §3 FR block (cited inline above) and in the §9 SAB block under `architecture_constraints`.

---

## §4 Interface Contracts

### 4.1 HTTP endpoints (verbatim from SPEC.md §6 L155-L175, SRS.md §5.1 L150-L163)

| Method | Path | Purpose | Success | Error codes | Source |
|--------|------|---------|---------|-------------|--------|
| GET | `/health` | Liveness | 200 (JSON `{status:"ok"}`) | — | SPEC.md L158, SRS.md L152 |
| GET | `/ready` | Readiness (Kokoro reachable + breaker closed) | 200 | 503 (Kokoro down or breaker open) | SPEC.md L159, SRS.md L153 |
| GET | `/v1/proxy/voices` | Upstream voice list | 200 (JSON list) | 502 (Kokoro error), 503 (breaker open) | SPEC.md L160, SRS.md L154 |
| POST | `/v1/proxy/speech` | Synthesize | 200 (audio bytes) | 400, 403, 503 | SPEC.md L161, SRS.md L155 |
| GET | `/health/circuit` | Breaker state + counters | 200 (JSON) | — | SPEC.md L162, SRS.md L156 |
| POST | `/health/circuit/reset` | Force breaker closed | 200 (JSON ack) | — | SPEC.md L163, SRS.md L157 |

**Error response shape** (unified across 4xx/5xx; derived from SPEC.md L210-L218, SRS.md §7 L401-L420):

```json
{
  "error": {
    "code": "VALIDATION_ERROR | CIRCUIT_OPEN | BACKEND_ERROR | SSML_FALLBACK | UNAUTHORIZED | INTERNAL",
    "message": "<human-readable>",
    "request_id": "<uuid4>",
    "field": "<offending field, when 400>"
  }
}
```

- `400 VALIDATION_ERROR` — empty input, > 8000 chars, invalid voice, invalid format, invalid speed (SPEC.md L216-L218, SRS.md L407-L414).
- `403 UNAUTHORIZED` — backend-URL not matching configured `KOKORO_BACKEND_URL` (SSRF guard, SRS.md L416-L420, R5 in §8).
- `503 CIRCUIT_OPEN` — breaker open; body explains retry-after (SPEC.md L83, L215, SRS.md L403-L404).
- `502 BACKEND_ERROR` — Kokoro returns 5xx; passed-through with upstream code embedded in message.
- `200 SSML_FALLBACK` — invalid SSML; success path with `X-SSML-Status: fallback` header (SPEC.md L213, SRS.md L402).

### 4.2 SpeechRequest / SpeechResponse schemas (verbatim from SPEC.md L167-L175, SRS.md §5.2 L165-L180)

**`POST /v1/proxy/speech` request body** (Pydantic `SpeechRequest` in `src/infrastructure/models.py`):

```json
{
  "model": "tts-1",
  "input": "文字或 SSML",
  "voice": "zf_xiaoxiao",
  "speed": 1.0,
  "response_format": "mp3"
}
```

| Field | Type | Default | Constraint | Source |
|-------|------|---------|------------|--------|
| `model` | `Literal["tts-1","tts-1-hd","kokoro","custom-gentle"]` | `"tts-1"` | Must be a `MODEL_MAP` key | SPEC.md L135-L141, L172, SRS.md L177 |
| `input` | `str` | (required) | Non-empty, ≤ 8000 chars | SPEC.md L171, L217, SRS.md L170, L408 |
| `voice` | `str` | `"zf_xiaoxiao"` | Must be in upstream voice list | SPEC.md L125, L173, L218, SRS.md L171, L412 |
| `speed` | `float` | `1.0` | 0.25 ≤ speed ≤ 4.0 (OpenAI-compatible) | SPEC.md L126, L174 |
| `response_format` | `Literal["mp3","wav"]` | `"mp3"` | One of the two | SPEC.md L173, SRS.md L179 |

**`SpeechResponse`** (success): raw audio bytes with `Content-Type: audio/mpeg` (MP3) or `audio/wav` (WAV). No JSON wrapper on success.

**Error response body** (4xx/5xx): see §4.1.

### 4.3 Internal module APIs (function signatures, no implementation)

```python
# src/engines/taiwan_linguistic.py  (FR-01)
def apply_lexicon(text: str) -> str: ...
LEXICON: dict[str, str]  # module-level, len(LEXICON) >= 50

# src/engines/ssml_parser.py  (FR-02)
@dataclass
class Segment:
    text: str
    voice_override: str | None
    speed_multiplier: float
    pad_ms: int

@dataclass
class ParsedSSML:
    plain_text: str
    segments: list[Segment]
    warnings: list[str]

def parse_ssml(ssml_or_text: str) -> ParsedSSML: ...

# src/engines/text_splitter.py  (FR-03)
def split_text(text: str, max_chars: int = 250) -> list[str]: ...

# src/engines/synthesis.py  (FR-04)
async def synthesize_chunks(
    chunks: list[str],
    voice: str,
    speed: float,
    fmt: Literal["mp3", "wav"],
    *,
    cache: RedisCache | None = None,
    breaker: CircuitBreaker | None = None,
) -> bytes: ...

# src/infrastructure/circuit_breaker.py  (FR-05)
class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitOpenError(Exception): ...

class CircuitBreaker:
    def __init__(self, threshold: int = 3, timeout: float = 10.0): ...
    async def call(self, coro: Coroutine) -> Any: ...
    def state(self) -> CircuitState: ...
    def reset(self) -> None: ...
    def counters(self) -> dict: ...

# src/infrastructure/redis_cache.py  (FR-06)
class RedisCache:
    def __init__(self, url: str | None = None): ...
    async def get(self, key: str) -> bytes | None: ...
    async def set(self, key: str, value: bytes, ttl: int = 86400) -> None: ...
    def is_available(self) -> bool: ...

def make_cache_key(text: str, voice: str, speed: float) -> str:
    # SHA-256 of "text + \x00 + voice + \x00 + str(round(speed,2))"
    # returns "tts:cache:<hex64>"

# src/infrastructure/audio_converter.py  (FR-08)
def convert_mp3_to_wav(mp3: bytes) -> bytes: ...
def convert_wav_to_mp3(wav: bytes) -> bytes: ...

# src/api/speech_router.py  (orchestrator)
async def synthesize_endpoint(req: SpeechRequest) -> Response: ...

# src/api/cli.py  (FR-07)
def main(argv: list[str] | None = None) -> int: ...
```

---

## §5 Data Flow

### 5.1 Sequence diagram — happy path (no cache, single chunk)

```
Client       speech.py     taiwan_linguistic   ssml_parser   text_splitter   synthesis.py   breaker      Kokoro :8880
  │              │                │                 │               │              │            │              │
  │ POST /speech │                │                 │               │              │            │              │
  ├─────────────▶│                │                 │               │              │            │              │
  │              │ validate (FR)  │                 │               │              │            │              │
  │              │ (NFR-08)       │                 │               │              │            │              │
  │              │                │                 │               │              │            │              │
  │              │ apply_lexicon  │                 │               │              │            │              │
  │              ├───────────────▶│                 │               │              │            │              │
  │              │◀─ normalized ──┤                 │               │              │            │              │
  │              │                │                 │               │              │            │              │
  │              │ parse_ssml     │                 │               │              │            │              │
  │              ├────────────────┼────────────────▶│               │              │            │              │
  │              │◀─ segments ────┼─────────────────┤               │              │            │              │
  │              │                │                 │               │              │            │              │
  │              │ split_text     │                 │               │              │            │              │
  │              ├────────────────┼─────────────────┼──────────────▶│              │            │              │
  │              │◀─ chunks ──────┼─────────────────┼───────────────┤              │            │              │
  │              │                │                 │               │              │            │              │
  │              │ synthesize_chunks                                        │            │              │
  │              ├────────────────┼─────────────────┼───────────────┼─────────────▶│            │              │
  │              │                │                 │               │              │            │              │
  │              │                │                 │               │              │ check     │              │
  │              │                │                 │               │              │ state     │              │
  │              │                │                 │               │              │ (closed)  │              │
  │              │                │                 │               │              ├──────────▶│              │
  │              │                │                 │               │              │            │              │
  │              │                │                 │               │              │  HTTP POST /audio/speech   │
  │              │                │                 │               │              ├───────────────────────────▶│
  │              │                │                 │               │              │            │              │
  │              │                │                 │               │              │◀───── MP3 bytes ───────────┤
  │              │                │                 │               │              │            │              │
  │              │                │                 │               │              │ record success            │
  │              │                │                 │               │              │ reset failure_count       │
  │              │                │                 │               │              │            │              │
  │              │◀──── audio bytes ─────────────────────────────────┤            │              │
  │              │                │                 │               │              │            │              │
  │◀─ 200 audio ─┤                │                 │               │              │            │              │
  │              │                │                 │               │              │            │              │
```

### 5.2 LEXICON lookup flow (FR-01)

1. Router validates `input` is non-empty, ≤ 8000 chars (NFR-08, SPEC.md L216-L218).
2. `apply_lexicon(input)` iterates `LEXICON` keys; longest-match-first substitution; preserves whitespace and punctuation.
3. Returns normalized string. Order: **LEXICON → SSML → split** (per SPEC.md L191-L195, SRS.md L152).
4. Pure function; no I/O; idempotent.

### 5.3 SSML parsing flow (FR-02)

1. Receive normalized text (may be plain text or SSML).
2. XML parse attempt (lxml or stdlib `xml.etree.ElementTree`).
3. On parse failure → log `warn` `{"event":"ssml.parse_fallback","reason":<err>}` and return `ParsedSSML(plain_text=normalized_text, segments=[Segment(text=normalized_text,...)], warnings=["parse_fallback"])` (SPEC.md L213, SRS.md L402).
4. On success → walk tree:
   - `<speak>`: descend.
   - `<!-- -->`: drop.
   - `<break time="Nsms">`: append `Segment(text="", pad_ms=N)`.
   - `<prosody rate="X">`: accumulate speed multiplier; `<prosody pitch="..."|volume="...">` → warn `{"event":"ssml.unsupported_attr","tag":"prosody","attr":"pitch|volume"}`, ignore.
   - `<emphasis level="strong|moderate">`: push speed×1.1 onto stack.
     - **P2 §3.5.1**: `<emphasis level="none|reduced">` → warn `{"event":"ssml.unsupported_attr","tag":"emphasis","level":<value>}`, pass through unchanged.
   - `<voice name="X">`: push voice onto stack.
   - `<phoneme alphabet="ipa" ph="...">`: emit text from `ph` attribute, keep alphabet.
   - `<say-as interpret-as="...">`: numeric-to-text via built-in formatter; pass through for non-numeric.
   - `</voice>`, `</emphasis>`, `</prosody>`: pop stack.
5. Returns `ParsedSSML` with `plain_text` (concatenation of segment.text), `segments` (list), `warnings`.

### 5.4 Text splitting flow (FR-03)

1. Receive `plain_text` (LEXICON + SSML stripped).
2. If `len(plain_text) <= 250` → return `[plain_text]` (SRS.md L206).
3. Otherwise: three-tier recursive descent.
   - **Tier 1** (always): find rightmost boundary in `set("。？！!?\n")` within `text`. If found and `len(text) > 250`, split there; recurse on right.
   - **Tier 2** (if segment > 100 chars): find rightmost boundary in `set("；:")` within segment. Split; recurse.
   - **Tier 3** (if segment still > 100 chars): find rightmost boundary in `set("，")` within segment. Split; recurse.
   - **Hard cap**: if no boundary yields a ≤ 250 chunk, force-split at 250 with hyphen padding.
4. **CJK/Latin word boundary** (P2 §3.5.2): a split position is invalid if it falls mid-word; defined as "no whitespace or punctuation at that exact position AND a CJK char (U+4E00-U+9FFF, U+3400-U+4DBF) is adjacent to a Latin/digit char on either side". The splitter biases toward the rightmost valid boundary.
5. Returns list of chunks, all ≤ 250 chars.

### 5.5 Parallel synthesis flow (FR-04)

1. Receive `chunks`, `voice`, `speed`, `fmt`.
2. If `len(chunks) == 1`: synthesize single chunk via `breaker.call(http_post_to_kokoro)`.
3. Else: `results = await asyncio.gather(*[synthesize_one(c) for c in chunks])`. All N coroutines are scheduled before any await is satisfied (verifiable by test mock, SPEC.md L78, SRS.md L214).
4. Concat: `b"".join(results)`. No re-encoding (SPEC.md L79, SRS.md L216).
5. If `fmt == "wav"`: `b"".join([convert_mp3_to_wav(r) for r in results])` then concat (FR-08 path). Or: synthesize all as MP3, then convert the concatenated MP3 to WAV in one ffmpeg call (implementation choice; both are byte-level no-re-encode of the synthesis stage).
6. **Partial success WAIVED** (P2 §3.5.6): if any chunk fails, `asyncio.gather` raises the first exception; the partial results for successful chunks are discarded; the router returns 5xx; the breaker counter increments (SPEC.md L214, SRS.md L220).

### 5.6 Circuit breaker flow (FR-05)

1. `breaker.call(coro)`:
   - **CLOSED**: try `await coro`; on success → return; on exception → `failure_count += 1`; if `failure_count >= threshold` → `state = OPEN`, `opened_at = now()`.
   - **OPEN**: if `now() - opened_at >= timeout` → `state = HALF_OPEN`; else → raise `CircuitOpenError`.
   - **HALF_OPEN**: allow exactly one probe; on success → `state = CLOSED`, `failure_count = 0`; on exception → `state = OPEN`, `opened_at = now()` (reset timeout).
2. `CircuitOpenError` → router maps to HTTP 503 with `Retry-After: <seconds-until-half-open>` header (SPEC.md L215, SRS.md L403-L404).
3. `GET /health/circuit`: returns `{state, failure_count, opened_at, threshold, timeout, since}`.
4. `POST /health/circuit/reset`: `state = CLOSED`, `failure_count = 0`, `opened_at = None`.

### 5.7 Cache key derivation flow (FR-06)

1. `make_cache_key(text, voice, speed)`:
   - Canonical: `text + "\x00" + voice + "\x00" + str(round(speed, 2))`.
   - Hash: `hashlib.sha256(canonical.encode("utf-8")).hexdigest()` (64-char hex).
   - Return `f"tts:cache:{hex}"`.
2. Synthesis lookup: `cache.get(key)` → if hit, return cached bytes (no Kokoro call, SPEC.md L86, SRS.md L254).
3. Synthesis store: on success, `await cache.set(key, audio_bytes, ttl=86400)` (24h, SPEC.md L88, SRS.md L252).
4. Graceful degradation: any `redis.*` exception → `is_available()=False`, `get()` returns `None`, `set()` is no-op, log `info` `{"event":"cache.unavailable","reason":<err>}` (SPEC.md L88-L89, L229, SRS.md L256-L257).

### 5.8 Audio format conversion flow (FR-08)

1. Caller invokes `convert_mp3_to_wav(mp3)` or `convert_wav_to_mp3(wav)`.
2. **P2 §3.5.4 — per-call ffmpeg-missing check (Round 2: reverted to SPEC.md L228 / FR-08 AC3 wording)**: `if shutil.which("ffmpeg") is None: log warn {"event":"ffmpeg.unavailable","format_requested":<fmt>}; raise FFmpegUnavailableError`. The check is local to the call; subsequent calls re-evaluate. Router maps the exception to **HTTP 500** with body `{"error":{"code":"ffmpeg_unavailable","message":"ffmpeg binary not found on PATH; required for format conversion to <fmt>"}}`. Other endpoints (and other code paths of `/v1/proxy/speech` that don't require conversion) continue to function normally.
3. If ffmpeg present, build subprocess command:
   - MP3→WAV: `ffmpeg -loglevel error -i pipe:0 -f wav pipe:1`
   - WAV→MP3: `ffmpeg -loglevel error -i pipe:0 -f mp3 -codec:a libmp3lame pipe:1` (libmp3lame is ffmpeg's bundled encoder; no new tech).
4. Stream input via `stdin.write`, read `stdout.read` to bytes, raise on non-zero exit code.

### 5.9 Error propagation flow

| Stage | Failure | Stage response | HTTP outcome |
|-------|---------|----------------|--------------|
| Router validation (NFR-08) | Empty / > 8000 / invalid voice / invalid format | Raise `ValidationError` | 400 VALIDATION_ERROR (SPEC.md L216-L218) |
| Router — backend URL check | URL ≠ `KOKORO_BACKEND_URL` | Raise `UnauthorizedError` | 403 UNAUTHORIZED (R5, SRS.md L416-L420) |
| LEXICON | (deterministic, no failure) | — | — |
| SSML parse | Invalid XML | Log warn, fallback to plain text (SPEC.md L213) | 200 + `X-SSML-Status: fallback` (SRS.md L402) |
| SSML unsupported attr | `pitch`/`volume`/`emphasis none|reduced` | Log warn, ignore/pass | 200 |
| Splitter | n/a (deterministic) | — | — |
| Cache lookup | Redis down | Log info, return None (SPEC.md L88-L89) | 200 (degraded, no cache benefit) |
| Breaker | Open | Raise `CircuitOpenError` (SPEC.md L83) | 503 CIRCUIT_OPEN (SRS.md L403-L404) |
| Kokoro call | 5xx / timeout | Raise `BackendError`; breaker counter++ (SPEC.md L214) | 502 BACKEND_ERROR (or 503 if breaker trips) |
| Concatenation | n/a (pure bytes) | — | — |
| Audio conversion | ffmpeg missing | P2 §3.5.4 (Round 2): log warn, raise `FFmpegUnavailableError` | **500 ffmpeg_unavailable** (per SPEC.md L228 / FR-08 AC3 L271; other paths continue) |
| Audio conversion | ffmpeg error | Raise `ConversionError` | 500 INTERNAL |

All exceptions caught by global FastAPI handler in `src/api/main.py` and shaped into the §4.1 error JSON.

---

## §6 Cross-Cutting Concerns

### 6.1 Logging (NFR-08, structured JSON, allow-list)

**Format**: one-line JSON per event, written to stdout (uvicorn captures). Example:

```json
{"event":"ssml.unsupported_attr","ts":"2026-06-04T10:00:00Z","level":"warn","request_id":"a1b2","fr_id":"FR-02","tag":"emphasis","level_value":"reduced"}
```

**Allow-list of safe top-level keys** (P2 Design Decision §3.5.5; resolves NFR-08 implementation completeness):

| Allowed key | Type | Notes |
|-------------|------|-------|
| `event` | `str` | Event name in dot-namespace (`ssml.unsupported_attr`, `cache.unavailable`, `ffmpeg.unavailable`) |
| `ts` | `str` | ISO-8601 UTC timestamp |
| `level` | `Literal["debug","info","warn","error"]` | Log level |
| `request_id` | `str` | UUID4 per request |
| `fr_id` | `str` | `FR-01`..`FR-08` |
| `voice` | `str` | Voice name only (no input text) |
| `format` | `str` | `"mp3"` or `"wav"` |
| `duration_ms` | `int` | Operation latency |
| `cache_hit` | `bool` | FR-06 hit/miss |
| `circuit_state` | `str` | `closed`/`open`/`half_open` |
| `error_code` | `str` | `VALIDATION_ERROR` / `CIRCUIT_OPEN` / etc. |
| `latency_ms` | `int` | End-to-end request latency |

**Deny by default**: any other key — especially `text`, `input`, `ssml`, `headers`, `api_key`, `token`, `prompt` — is dropped silently and a `dropped_pii=1` counter is incremented. This addresses R6 (secret leakage via debug logs, SRS.md §8, SPEC.md §9 L222-L229).

**Logger implementation**: thin module-level wrapper (no external logging library change; stdlib `logging` + custom `LoggerAdapter` that filters by allow-list).

**Sanitization pipeline (NFR-08, R6)**: every log line is **sanitized** against the allow-list before it is emitted to stdout. The sanitization step runs as the last action of the logger wrapper and does the following in order: (1) project the record's `extra` dict down to the union of allowed keys from the table above; (2) drop any key not on the allow-list and increment the in-process `dropped_pii` counter; (3) coerce the level to one of `debug` / `info` / `warn` / `error` (any other value falls back to `info`); (4) attach `ts` (ISO-8601 UTC) and a per-process UUID4 `request_id` if the caller did not supply one. A regression test in `tests/test_nfr08_validation.py` (allow-list subset, R6 cluster) asserts that the sanitized payload contains zero keys outside the allow-list, and that injecting a record with a forbidden key (e.g., `api_key`, `text`, `headers`) results in a `dropped_pii=1` counter increment and no forbidden key in the emitted JSON line (SRS.md §2.6 secret management, §8 R6; SPEC.md L20-L26, L222-L229).

### 6.2 Configuration (`src/infrastructure/config.py`, SPEC.md L122-L141)

| Constant | Value | Env override | Source |
|----------|-------|--------------|--------|
| `KOKORO_BACKEND_URL` | `"http://localhost:8880/v1/audio/speech"` | `KOKORO_BACKEND_URL` | SPEC.md L123, SRS.md L317 |
| `KOKORO_VOICES_URL` | `"http://localhost:8880/v1/audio/voices"` | `KOKORO_VOICES_URL` | SPEC.md L124, SRS.md L318 |
| `DEFAULT_VOICE` | `"zf_xiaoxiao"` | `DEFAULT_VOICE` | SPEC.md L125, SRS.md L319 |
| `DEFAULT_SPEED` | `1.0` | `DEFAULT_SPEED` | SPEC.md L126, SRS.md L320 |
| `MAX_CHARS_PER_REQUEST` | `250` | `MAX_CHARS_PER_REQUEST` | SPEC.md L127, SRS.md L321, FR-03 |
| `LEXICON_MIN_SIZE` | `50` | `LEXICON_MIN_SIZE` | SPEC.md L128, SRS.md L322, FR-01 |
| `REQUEST_TIMEOUT` | `30.0` | `REQUEST_TIMEOUT` | SPEC.md L129, SRS.md L323, NFR-07 |
| `CIRCUIT_BREAKER_THRESHOLD` | `3` | `CIRCUIT_BREAKER_THRESHOLD` | SPEC.md L130, SRS.md L324, FR-05 |
| `CIRCUIT_BREAKER_TIMEOUT` | `10.0` | `CIRCUIT_BREAKER_TIMEOUT` | SPEC.md L131, SRS.md L325, FR-05 |
| `WARMUP_ENABLED` | `True` | `WARMUP_ENABLED` | SPEC.md L132, SRS.md L326, NFR-06 |
| `WARMUP_TEXT` | `"你好，測試中"` | `WARMUP_TEXT` | SPEC.md L133, SRS.md L327, NFR-06 |
| `CACHE_TTL_SECONDS` | `86400` (24h) | `CACHE_TTL_SECONDS` | SPEC.md L88, SRS.md L252 |
| `REDIS_URL` | `None` (optional) | `REDIS_URL` | SPEC.md L23, L229 |
| `MODEL_MAP` | (dict, see SPEC L135-L141) | (constant) | SPEC.md L135-L141, SRS.md L329-L335 |

Persona recipes (`極致溫柔助理`, `親切智慧導遊`, `現代幹練秘書`, `甜美親和主播`) are stored as a constant in `src/engines/taiwan_linguistic.py` or a new `src/personas.py` module (within SPEC.md §7 folder structure); verbatim from SPEC.md L145-L150, SRS.md L342-L349.

### 6.3 Error handling (SPEC.md §8 L210-L219, SRS.md §7 L401-L420)

See §5.9 Error propagation flow above. Implementation:

- Validation: Pydantic `field_validator` + a custom `validate_speech_request` in `src/api/speech_router.py` (NFR-08, SPEC.md L216-L218).
- Breaker: `try/except` around `breaker.call(...)`; map `CircuitOpenError` → 503.
- Backend: map `httpx.HTTPStatusError` (5xx) → 502 + breaker increment; map `httpx.TimeoutException` → 502 + breaker increment.
- Conversion: map `subprocess.CalledProcessError` → 500; map missing ffmpeg → graceful skip (P2 §3.5.4).
- Global handler: `src/api/main.py` `@app.exception_handler(Exception)` → unified error JSON.

### 6.4 Security (NFR-08, R5/R6/R7/R8)

- **NFR-08 Input validation** (R5, SPEC.md L216-L218): every `SpeechRequest` field verified at route layer; Pydantic v2 validators enforce non-empty, length bounds, format literals, speed range, voice-in-allowlist.
- **R5 SSRF guard** (SRS.md L416-L420): the proxy hard-codes `KOKORO_BACKEND_URL` from config; any request that includes a different `backend` URL or a `<voice name="http://...">` SSML payload is rejected at the route layer with HTTP 403. The proxy never forwards to a user-controlled host.
- **R6 Secret hygiene** (SRS.md §8 R6): all secrets (Kokoro token, Redis password) read from env vars; the structured logger allow-list (§6.1) drops `api_key`, `token`, `headers`, etc. before they reach stdout. A regression test asserts that no log line contains a substring of any env-var value (configurable for the test).
- **R7 Plaintext backend**: loopback HTTP only (SPEC.md L122-L124); no network egress beyond `localhost:8880`. Documented in README; out-of-scope for the proxy to add TLS.
- **R8 RBAC**: explicitly out-of-scope (PROJECT_BRIEF.md §5, SRS.md §1.3, §2.6, §8 R8). Documented in CONTROL_GROUP.md (P3+ deliverable).
- **Permission model (control-group non-goal)**: the proxy does **not** implement a user-level permission system, role-based access control, or per-caller authorization. There is no concept of "user", "role", "tenant", or "scope" inside the proxy; all callers that can reach the listening socket are treated as having full permission to invoke every endpoint exposed by the FastAPI app (`POST /v1/proxy/speech`, `GET /v1/proxy/voices`, `GET /health`, `GET /ready`, `GET /health/circuit`, `POST /health/circuit/reset`). The proxy trusts the enclosing network boundary (loopback interface, reverse proxy, or upstream API gateway) as the **permission enforcement point**; if a deployment needs finer-grained permission, it must be added in that boundary, not in the proxy (PROJECT_BRIEF.md §5 out-of-scope list; SRS.md §1.3, §2.6 authentication & RBAC posture, §8 R8; SPEC.md §11 L247-L254 feature-freeze constraint that prevents adding an in-proxy permission system without a SPEC.md amendment). This is consistent with the R8 row above and with the `permission` field declared in NFR-08 (SRS.md §4 NFR-08 / §6.1 logging allow-list context). The control group's lack of in-proxy permission checks is the experimental baseline; any treatment group that adds them becomes a clean experimental differentiator for the methodology-v2 comparison.
- **Encryption posture (control-group invariant)**: in-transit encryption of HTTP traffic (TLS) is **delegated to a reverse proxy** in any non-loopback deployment (SRS.md §2.6 TLS posture, R7); the FastAPI application itself does not terminate TLS, does not encrypt or decrypt HTTP bodies, and does not bundle an HTTPS server certificate. For local loopback development (the default control-group deployment), the connection to `Kokoro` at `http://localhost:8880/v1` is plain HTTP because both endpoints are on `localhost` and never traverse a network (SPEC.md L122-L124, SRS.md §2.6, §8 R7). At-rest encryption of cached audio bytes in Redis is **out of scope** for the control group — the cache stores the synthesis result bytes keyed by a SHA-256 hash (P2-DD-3, `§3.6`); the bytes themselves are not encrypted at rest, and introducing at-rest encryption would be a new technology decision prohibited by the feature freeze (SPEC.md §11 L247-L254, SRS.md §2.4). If a future treatment group adds transport encryption or at-rest encryption, the control group's baseline (no proxy-layer encryption, no cache encryption) is the experimental comparator.

### 6.5 Observability

- **`GET /health`**: `{status:"ok"}` (always 200 if process up).
- **`GET /ready`**: pings Kokoro `/v1/audio/voices`; returns 200 if reachable AND breaker closed; 503 otherwise (SPEC.md L159, SRS.md L153).
- **`GET /health/circuit`**: `{state, failure_count, opened_at, threshold, timeout, last_transition_at}` (SPEC.md L162, SRS.md L156).
- **`POST /health/circuit/reset`**: forces closed; returns `{state:"closed", previous_state, reset_at}` (SPEC.md L163, SRS.md L157).
- **No metrics endpoint** (Prometheus not in tech stack; SPEC.md L20-L26).
- **Structured logs** are the observability primitive (NFR-08 + §6.1).

### 6.6 Concurrency model

- **ASGI**: uvicorn with default worker count (1 process, asyncio loop). No multi-process / multi-worker (no tech change; SPEC.md L247-L254).
- **httpx.AsyncClient**: one shared client instance per FastAPI app lifespan; closed on shutdown. `limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)` (sane defaults; no spec change).
- **Per-FR httpx limits**: `synthesis.synthesize_chunks` uses `asyncio.gather(*[synthesize_one(c) for c in chunks])`. Chunk count is unbounded by the spec; in practice capped by `MAX_CHARS_PER_REQUEST=250` and input length ≤ 8000 → at most 32 chunks. `asyncio.gather` does not impose its own backpressure; the breaker and the 30s timeout (NFR-07) provide the failure-bound.
- **Warmup**: at lifespan startup, if `WARMUP_ENABLED=True`, fire one request with `WARMUP_TEXT` to warm the breaker and prime the connection pool (NFR-06, SPEC.md L132-L133).
- **Lock-free state**: the breaker's `state`, `failure_count`, `opened_at` are mutated under an `asyncio.Lock` to prevent race in concurrent failure events.

---

## §7 NFR Coverage Matrix

| NFR | Target (verbatim) | Enforced at | Test file | Source |
|-----|-------------------|-------------|-----------|--------|
| **NFR-01** TTFB | < 300 ms (warm) | `src/engines/synthesis.py` (parallel gather), `src/infrastructure/circuit_breaker.py` (fast-fail), `src/infrastructure/redis_cache.py` (cache hit short-circuit); measured by wall-clock from request received to first byte | `tests/test_nfr01_ttfb.py` | SPEC.md L110, SRS.md L114 |
| **NFR-02** LEXICON coverage | ≥ 80% on labeled Taiwan corpus | `src/engines/taiwan_linguistic.py` (≥ 50 entries, LEXICON_MIN_SIZE); corpus test asserts coverage ≥ 80% on a fixed reference corpus. **Round 2 annotation (LOW gap #3, FR-01)**: The reference corpus is **not named in P2 architecture** — corpus selection is a P3 action owned by the methodology-v2 reviewer. Until a fixed corpus is named (e.g., a labeled Taiwan-news sample recorded in `CONTROL_GROUP.md` P3), the ≥ 80% coverage target is **not verifiable in CI**. The SAB `open_question` flag for NFR-02 captures this. | `tests/test_nfr02_lexicon_coverage.py` (deferred to P3 once corpus is fixed) | SPEC.md L111, SRS.md L115-L116 |
| **NFR-03** Tone sandhi | ≥ 95% | Manual / A-B audit (not automated in 82-test set); assertion is a process gate, not a CI gate. **Round 2 annotation (LOW gap #5)**: The audit rubric (sample size, reviewer assignment, scoring scale) is **not defined in P2 architecture** — it is a P3 deliverable to be recorded in `CONTROL_GROUP.md` with a fixed sample size and a named reviewer. Until that rubric exists, the ≥ 95% acceptance gate is unmeasurable. The proxy implementation cannot own this gate. | (out-of-band audit checklist, P3 `CONTROL_GROUP.md`) | SPEC.md L112, SRS.md L118-L119 |
| **NFR-04** API availability | ≥ 99% (30-day rolling) | Operational SLA on `GET /health` 200 responses; measured at the deployment layer. **Round 2 annotation (LOW gap #4)**: This SLA is **out-of-scope for the proxy implementation** — the control-group's local-only deployment cannot observe 30-day rolling uptime, and the 82-test set does not cover it. The methodology-v2 control-group owner MUST own the 30-day measurement (e.g., via an external uptime probe, or a defined operational dashboard). The proxy exposes the `GET /health` endpoint as the probe target; the measurement instrumentation is not the proxy's responsibility. | (operational dashboard / uptime probe owned by methodology-v2, not a test) | SPEC.md L113, SRS.md L121-L122 |
| **NFR-05** Error recovery | < 10 s | `src/infrastructure/circuit_breaker.py` (`CIRCUIT_BREAKER_TIMEOUT=10.0`, SPEC.md L131); measured by injecting backend failure and timing the next-successful-request from probe | `tests/test_nfr05_recovery.py` | SPEC.md L114, SRS.md L124-L125 |
| **NFR-06** Cold-start readiness | Warmup on launch | `src/api/main.py` lifespan handler reads `WARMUP_ENABLED` and fires `WARMUP_TEXT`; verified by `pytest -k warmup` | `tests/test_nfr06_warmup.py` | SPEC.md L132-L133, SRS.md L127-L128 |
| **NFR-07** Request timeout | 30.0 s | `src/infrastructure/config.py` `REQUEST_TIMEOUT=30.0`; `httpx.AsyncClient(timeout=30.0)` set in lifespan; `synthesis.synthesize_chunks` wraps each Kokoro call in `asyncio.wait_for(..., timeout=30.0)`; on timeout, raises `BackendError` and increments breaker | `tests/test_nfr07_timeout.py` | SPEC.md L129, SRS.md L130-L131 |
| **NFR-08** Input validation | All fields verified | `src/infrastructure/models.py` Pydantic validators + `src/api/speech_router.py` `validate_speech_request`; allow-list logger (§6.1) prevents secret leakage; SSRF guard (§6.4) blocks non-loopback backend; verified by per-field reject tests (≈6 of 82 cases) | `tests/test_nfr08_validation.py` | SPEC.md L216-L218, L167-L175, SRS.md L133-L138, L401-L420 |

All 8 NFRs are mapped to enforcement location + test file (or operational gate for NFR-04). No NFR is unowned.

---

## §8 Risks & Mitigations

| ID | Risk | Impact | Likelihood | Mitigation | Owner module | Source |
|----|------|--------|------------|------------|--------------|--------|
| **R1** | Kokoro Docker crashes | High | Low | Circuit breaker (FR-05) fast-fails subsequent requests with HTTP 503; `GET /ready` reports 503 during outage; clear error JSON | `src/infrastructure/circuit_breaker.py` | SPEC.md L226, SRS.md §8 R1 |
| **R2** | Connection drop | Medium | Medium | 3-attempt retry handler in `synthesis.synthesize_one`; per-retry timeout = `REQUEST_TIMEOUT=30.0`; failures feed the breaker counter; **retry count is bounded by the breaker threshold to prevent infinite retry storms** | `src/engines/synthesis.py` + `src/infrastructure/circuit_breaker.py` | SPEC.md L227, SRS.md §8 R2 |
| **R3** | ffmpeg missing | Medium | Low | P2 §3.5.4 (Round 2: reverted to SPEC.md L228 / FR-08 AC3 wording): per-call `shutil.which("ffmpeg")` check; on miss, log structured `ffmpeg.unavailable` event and raise `FFmpegUnavailableError` → HTTP 500 with body `{"error":{"code":"ffmpeg_unavailable","message":"ffmpeg binary not found on PATH; required for format conversion to <fmt>"}}`; the rest of the service (other paths of `/v1/proxy/speech`, `/health`, `/ready`, `/v1/proxy/voices`) continues to operate; subsequent call re-checks (no caching); `requirements.txt` + README declare ffmpeg as required | `src/infrastructure/audio_converter.py` | SPEC.md L228, SRS.md §8 R3 |
| **R4** | Redis unreachable | Low | Low | FR-06 graceful-degradation: `is_available()=False` on connection error; `get()` returns `None`; `set()` no-op; info log; proxy continues without cache benefit | `src/infrastructure/redis_cache.py` | SPEC.md L229, SRS.md §8 R4 |
| **R5** | SSRF via crafted SSML or `backend` override | Medium | Low | Route-layer validation: `voice` field must be in upstream voice allowlist; `<voice name="http://...">` rejected at SSML parse; `backend` URL override not exposed to clients; the only SSRF surface is the configured `KOKORO_BACKEND_URL` | `src/api/speech_router.py`, `src/engines/ssml_parser.py` | SRS.md §8 R5, §7 row 7 |
| **R6** | Secret leakage via debug logs | High | Low | Allow-list logger (§6.1) drops `text`, `input`, `ssml`, `headers`, `api_key`, `token`; secrets read from env vars only; regression test asserts that no log line contains a substring of any env-var value | `src/api/main.py` (logger setup), `src/infrastructure/config.py` (env vars) | SRS.md §8 R6 |
| **R7** | Plaintext backend communication | Low | Medium | Loopback HTTP to `localhost:8880`; no network egress; documented as intentional (no TLS at proxy layer); recommended reverse proxy for non-loopback deployments | (out-of-scope; documented in CONTROL_GROUP.md and README) | SRS.md §8 R7 |
| **R8** | RBAC not implemented | Low | Low | Documented non-goal; out-of-scope per PROJECT_BRIEF.md §5; not a vulnerability (intentional single-user design); recorded in CONTROL_GROUP.md | (documentation only) | SRS.md §8 R8, PROJECT_BRIEF.md §5 |

**Risk → requirement traceability** (per SRS.md §8 final block, expanded for P2):
- R1 → FR-05 + §7 row 3 (`CIRCUIT_OPEN` 503).
- R2 → retry handler in `synthesis.synthesize_one` + FR-05 threshold.
- R3 → P2 §3.5.4 (per-call disable) + `requirements.txt` declaration.
- R4 → FR-06 graceful skip.
- R5 → NFR-08 input validation + §7 row 7 (`UNAUTHORIZED` 403) + hard-coded `KOKORO_BACKEND_URL`.
- R6 → §6.1 allow-list logger + env-var-only secret ingestion.
- R7 → documented; not mitigated at code layer.
- R8 → documented non-goal; not mitigated at code layer.

---

## §9 SAB Block (Machine-Readable)

<!-- SAB:START -->
```yaml
sab:
  version: "1.0.0"
  created_at: "2026-06-04"
  phase: 2
  project: "kokoro-taiwan-proxy"
  layers:
    - name: "presentation"
      modules: ["src/api/main.py", "src/api/speech_router.py", "src/api/cli.py"]
      responsibility: "HTTP/CLI entry; FastAPI app + argparse CLI"
    - name: "business"
      modules: ["src/engines/taiwan_linguistic.py", "src/engines/ssml_parser.py", "src/engines/text_splitter.py", "src/engines/synthesis.py", "src/infrastructure/circuit_breaker.py", "src/infrastructure/audio_converter.py"]
      responsibility: "TTS transformation; LEXICON, SSML, chunking, synthesis, breaker, ffmpeg wrapper"
    - name: "infrastructure"
      modules: ["src/infrastructure/config.py", "src/infrastructure/models.py", "src/infrastructure/redis_cache.py"]
      responsibility: "Config (env-bound), Pydantic schemas, optional Redis cache"
  allowed_dependencies:
    - from: "presentation"
      to: "business"
    - from: "presentation"
      to: "infrastructure"
    - from: "business"
      to: "infrastructure"
  quality_targets:
    latency_p50_ms: 300
    latency_p95_ms: 800
    availability_pct: 99.0
    lexicon_min_size: 50
    chunk_max_chars: 250
    test_coverage_pct: 100
    test_coverage_pct_note: "100% refers to FR-coverage (all 8 FRs have >=1 test case in TEST_SPEC.md), NOT line coverage"
    required_p2_design_decisions: 6
    nfr_compliance_required: ["NFR-01","NFR-02","NFR-03","NFR-04","NFR-05","NFR-06","NFR-07","NFR-08"]
  nfr_dimension_mapping:
    NFR-01: "correctness"
    NFR-02: "correctness"
    NFR-03: "correctness"
    NFR-04: "operability"
    NFR-05: "correctness"
    NFR-06: "operability"
    NFR-07: "correctness"
    NFR-08: "security"
  nfr_traceability:
    NFR-01:
      type: "latency"
      module: "src/api/main.py + src/engines/synthesis.py"
      test_file: "tests/test_fr01_perf.py"
      verification: "p50 < 300ms on warm proxy (excludes Kokoro backend network)"
    NFR-02:
      type: "coverage"
      module: "src/engines/taiwan_linguistic.py"
      test_file: "tests/test_fr_01_lexicon_coverage.py"
      verification: "parametrize over LEXICON entries; >=80% coverage on labeled corpus"
      open_question: "Reference corpus not yet named (deferred to P3 - methodology-v2 reviewer must name a corpus like a labeled Taiwan-news sample set before NFR-02 acceptance can move to MET)"
    NFR-03:
      type: "accuracy"
      module: "src/engines/taiwan_linguistic.py"
      test_file: "tests/test_fr_01_tone_sandhi.py"
      verification: "manual A-B audit rubric in CONTROL_GROUP.md (P3) with fixed sample size; >=95% tone sandhi correctness"
    NFR-04:
      type: "availability"
      module: "src/api/main.py"
      test_file: "N/A - operational SLA"
      verification: "30-day rolling availability of GET /health returning 200; methodology-v2 owner; out-of-scope for proxy implementation"
    NFR-05:
      type: "recovery_time"
      module: "src/infrastructure/circuit_breaker.py"
      test_file: "tests/test_fr_05_circuit_breaker.py"
      verification: "Half-Open probe after CIRCUIT_BREAKER_TIMEOUT=10s; recovery time < 10s"
    NFR-06:
      type: "warmup"
      module: "src/api/main.py"
      test_file: "tests/test_warmup.py"
      verification: "WARMUP_ENABLED=True; WARMUP_TEXT='ni-hao, ce-shi-zhong'; on-launch warmup call"
    NFR-07:
      type: "timeout"
      module: "src/infrastructure/config.py + src/infrastructure/circuit_breaker.py"
      test_file: "tests/test_fr_05_timeout.py"
      verification: "REQUEST_TIMEOUT=30.0; on overrun, breaker counter incremented"
    NFR-08:
      type: "security"
      module: "src/api/speech_router.py + src/infrastructure/models.py + src/infrastructure/config.py + structured logger"
      test_file: "tests distributed across test_fr_01..08.py"
      verification: "input validation on SpeechRequest fields; secrets via env vars only; TLS deferred to reverse proxy; no PII in logs (allow-list sanitizer)"
  advisory_only: []
  gate_score_overrides:
    correctness: 100
    security: 100
  fr_module_traceability:
    FR-01:
      module: "src/engines/taiwan_linguistic.py"
      spec: "SPEC.md L33-L34, L128"
      test: "tests/test_fr_01_taiwan_linguistic.py"
    FR-02:
      module: "src/engines/ssml_parser.py"
      spec: "SPEC.md L37-L50, L193"
      test: "tests/test_fr_02_ssml_parser.py"
    FR-03:
      module: "src/engines/text_splitter.py"
      spec: "SPEC.md L52-L74, L194"
      test: "tests/test_fr_03_text_splitter.py + tests/test_fr_03_text_splitter_edge_cases.py"
    FR-04:
      module: "src/engines/synthesis.py"
      spec: "SPEC.md L77-L79, L195"
      test: "tests/test_fr_04_synthesis.py + tests/test_fr_04_synthesis_concat.py"
    FR-05:
      module: "src/infrastructure/circuit_breaker.py"
      spec: "SPEC.md L81-L85, L197"
      test: "tests/test_fr_05_circuit_breaker.py"
    FR-06:
      module: "src/infrastructure/redis_cache.py"
      spec: "SPEC.md L86-L89, L198"
      test: "tests/test_fr_06_redis_cache.py"
    FR-07:
      module: "src/api/cli.py"
      spec: "SPEC.md L92-L97, L187"
      test: "tests/test_fr_07_cli.py"
    FR-08:
      module: "src/infrastructure/audio_converter.py"
      spec: "SPEC.md L100-L102, L188"
      test: "tests/test_fr_08_audio_converter.py"
  architecture_constraints:
    - "No new tech stack (FastAPI + httpx + uvicorn + Kokoro Docker + optional Redis + ffmpeg only)"
    - "No core algorithm changes (FR-01..FR-08 logic is immutable)"
    - "No test deletion or modification (82 tests must remain green)"
    - "No coverage reduction"
    - "Feature freeze: bug fix only"
    - "FR-04 partial-success mode WAIVED for control-group scope (P2-DD-6)"
    - "FR-08 ffmpeg-missing: per-call check, FFmpegUnavailableError -> HTTP 500 (P2-DD-4)"
    - "NFR-08 log sanitization: allow-list of safe keys, deny-by-default (P2-DD-5)"
  high_risk_modules:
    - module: "src/engines/synthesis.py"
      risk: "Parallel httpx dispatch + byte-level MP3 concat; P3 must verify no re-encoding"
    - module: "src/infrastructure/circuit_breaker.py"
      risk: "In-process state; each worker has independent state; P3 must verify Half-Open probe correctness"
    - module: "src/infrastructure/audio_converter.py"
      risk: "Subprocess call to ffmpeg; P3 must verify timeout handling and missing-binary behavior"
    - module: "src/infrastructure/redis_cache.py"
      risk: "Optional dependency; P3 must verify graceful no-Redis fallback"
```
<!-- SAB:END -->

---

## Appendix A — SPEC.md / SRS.md line citation index

| This document section | Primary citations |
|-----------------------|-------------------|
| §1.1 project name & scope | SPEC.md L7-L14, L181-L205; SRS.md §1.1, §1.3 |
| §1.2 reference documents | SPEC.md L1-L4; SRS.md §1.5 |
| §1.3 architectural goals | SPEC.md L20-L26, L108-L141; SRS.md §4 |
| §1.4 prohibitions | SPEC.md L247-L254; SRS.md §2.4 |
| §2.1 directory structure design principles | harness-methodology `templates/SAD.md` §2.1 |
| §2.2 system context | SPEC.md L181-L205; SRS.md §6.5 |
| §2.3 component list | SPEC.md L184-L205; SRS.md §6.5 |
| §2.5 tech stack | SPEC.md L18-L26 |
| §3.1 FR-01 | SPEC.md L32-L51; SRS.md §3 FR-01 |
| §3.2 FR-02 | SPEC.md L52-L65; SRS.md §3 FR-02 |
| §3.3 FR-03 | SPEC.md L67-L75; SRS.md §3 FR-03 |
| §3.4 FR-04 | SPEC.md L77-L79; SRS.md §3 FR-04 |
| §3.5 FR-05 | SPEC.md L81-L85, L130-L131; SRS.md §3 FR-05 |
| §3.6 FR-06 | SPEC.md L86-L89, L198, L229; SRS.md §3 FR-06 |
| §3.7 FR-07 | SPEC.md L91-L98, L187; SRS.md §3 FR-07 |
| §3.8 FR-08 | SPEC.md L100-L102, L188, L228; SRS.md §3 FR-08 |
| §4.1 endpoints | SPEC.md L155-L175; SRS.md §5.1 |
| §4.2 request schema | SPEC.md L135-L141, L167-L175; SRS.md §5.2 |
| §5 data flows | SPEC.md L32-L103, L210-L219; SRS.md §3, §7 |
| §6.1 logging (allow-list) | SPEC.md L20-L26; SRS.md §2.6, §8 R6 |
| §6.2 config constants | SPEC.md L122-L141; SRS.md §6.1 |
| §6.3 error handling | SPEC.md L210-L219; SRS.md §7 |
| §6.4 security (NFR-08, R5/R6/R7/R8) | SPEC.md L216-L218; SRS.md §2.6, §8 |
| §7 NFR coverage | SPEC.md L108-L114; SRS.md §4 |
| §8 risks R1-R8 | SPEC.md L222-L229; SRS.md §8 |
| §9 SAB | All of the above |

---

## Appendix B — P1 Holistic gap closure log

| P1 gap (severity, FR) | Resolved in this SAD by | Status |
|------------------------|--------------------------|--------|
| Gap #5 (LOW, FR-03): mixed CJK/Latin word rule | §3.3 P2-DD-2 (whitespace-or-punctuation) | CLOSED at P2 design level |
| Gap #6 (LOW, FR-02/FR-06): emphasis level + hash function | §3.2 P2-DD-1 (warn-and-pass), §3.6 P2-DD-3 (SHA-256) | CLOSED at P2 design level |
| Gap #7 (LOW, FR-04/FR-08): partial-success + ffmpeg-missing | §3.4 P2-DD-6 (WAIVED), §3.8 P2-DD-4 (per-call disable) | CLOSED at P2 design level |
| Gap #4 (LOW, FR-01): reference corpus not named | §7 NFR-02 `open_question` flag | OPEN — methodology-v2 reviewer owns corpus selection at P3 |
| Gap #1 (LOW, 82 vs 10): enumeration deferred to P3 | §3.9 FR×module matrix; §9 quality_targets.total_test_cases=82 | MITIGATED at planning level (P1 reviewer-approved) |
| Gap #2 (LOW, FR-08 21-case allocation) | §3.9 row; §9 high_risk_modules.audio_converter | OPEN — P3 implementation reports delta vs 21 |
| Gap #3 (LOW, FR-01 12 vs 50 LEXICON) | §3.1 acceptance criterion L145-L150; TEST_INVENTORY.yaml L11-L21 | MITIGATED at planning level (12 = canonical mapping checks, not all 50) |

---

*End of SAD — Kokoro Taiwan Proxy — P2 architecture, v1.0.0. Author: Agent A (ARCHITECT), Round 1. Pending Agent B (TECH_LEAD) Round 1 review.*
