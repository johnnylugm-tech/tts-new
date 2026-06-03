# Requirements Traceability Matrix — Kokoro Taiwan Proxy

> **Project**: `kokoro-taiwan-proxy` (control group, methodology-v2 improvement experiment)
> **Document version**: v1.0
> **Date**: 2026-06-03
> **Author**: REQUIREMENTS_ENGINEER (Agent A)
> **Methodology framework**: harness-methodology v2.7.0
> **Authoritative source**: `SPEC.md` v1.0.0-control (2026-03-31) — single source of truth (`SPEC.md L1-L4`).
> **Authoritative FR list**: `01-requirements/SRS.md` §3 (FR-01..FR-08; APPROVED P1 deliverable).
> **Companion documents**: `01-requirements/SRS.md`, `01-requirements/SPEC_TRACKING.md`.

---

## Overview

### Purpose

This document is the **P1 deliverable** `01-requirements/TRACEABILITY_MATRIX.md`. It establishes
**bidirectional traceability** between the 8 pre-defined Functional Requirements (FR-01..FR-08),
their statement in the Software Requirements Specification (`SRS.md` §3), the planned design
elements (Python source files under `src/`), and the planned test files (under `tests/`). The
matrix is the control-group baseline that downstream phases (P2 architecture, P3 implementation,
P5 testing, P6 verification) will fill in and exercise.

### Scope

- **Forward link**: FR → SRS section → Design element (`src/...`) → Test file (`tests/...`).
- **Reverse link**: Test file → FR (so any test can be traced back to the requirement that
  justifies it, and any requirement can be traced to at least one verifying test).
- **In scope** (8 FRs): FR-01..FR-08 (verbatim from `SPEC.md §3, L32-L103`; SRS.md §3).
- **Out of scope**: Non-Functional Requirements (NFRs) are tracked separately in `SRS.md §4`;
  this matrix covers functional traceability only. NFRs map indirectly through the 82-test
  suite (`SPEC.md L200, L235`).

### Methodology & framework conformance

- **Framework**: harness-methodology v2.7.0 (P1 phase).
- **Source-of-truth discipline**: every row below cites `SPEC.md` line numbers for the FR text
  and `SRS.md` line numbers for the section anchor. The 8 FRs are immutable (control group,
  `SPEC.md §11, L247-L254`); no new FRs are introduced.
- **Folder structure discipline**: design-element file paths are the planned files from
  `SPEC.md §7, L181-L205`. These are the canonical homes; no relocation is permitted.
- **Test file naming convention**: `tests/test_fr_<NN>_<slug>.py` (lowercase, snake_case). One
  test file per FR minimum. For FR-03 (multi-tier splitter) and FR-04 (parallel synthesis with
  byte-level concatenation) this matrix optionally proposes two test files each to keep
  fixture setup compact and reduce the risk of one file blowing up in scope.

### ASPICE compliance note

This matrix is a structural prerequisite for **ASPICE SWE.3 (Software Detailed Design and
Unit Construction)** and **SYS.4 (System Integration)** traceability evidence:

| ASPICE capability | How this matrix satisfies it | Reference |
|-------------------|------------------------------|-----------|
| SWE.3.B.SP1 — Task-to-work-product traceability | Each FR row links an SRS section → a `src/` design element → a `tests/` test file. | This document, §"FR ↔ Design ↔ Test Matrix". |
| SWE.3.B.SP2 — Bidirectional traceability | §"Reverse Traceability (Test → FR)" lists every test file and the FR it covers; §"Bidirectional Check" column flags any link that is not reachable from the opposite direction. | This document. |
| SWE.3.B.SP3 — Traceability consistency | All 8 FRs are anchored to a single SPEC.md line range and a single SRS.md section; no invented rows. | `SPEC.md L32-L103`; `SRS.md L134-L255`. |
| SYS.4.B.SP1 — Integration test traceability | Each test file is reachable from exactly one or more FRs; the matrix is the navigation index. | This document, §"Reverse Traceability". |

ASPICE compliance status for this P1 deliverable: **MAPPING DECLARED** — every FR has a
mapped design element and a planned test file. Per-link verification (running the tests,
checking the implementation) is performed in P3+ (implementation) and P5+ (testing) phases.
Until then, the Status column carries `PLANNED` for every row and the Bidirectional Check
column carries `OK` for every link (forward link + reverse link both exist).

---

## FR ↔ Design ↔ Test Matrix

> **Reading guide**:
> - **FR ID** — functional requirement identifier from `SPEC.md §3` / `SRS.md §3`.
> - **SRS Section** — anchor in the authoritative `SRS.md §3`.
> - **Design Element (file)** — planned Python source file per `SPEC.md §7, L181-L205`.
> - **Test File (planned)** — planned test path under `tests/` using the convention
>   `tests/test_fr_<NN>_<slug>.py`.
> - **Status** — `PLANNED` (P1 baseline; not yet implemented). Implementation moves rows to
>   `IMPLEMENTED` (P3+) and `VERIFIED` (P5+); see `SPEC_TRACKING.md` for status workflow.
> - **Bidirectional Check** — `OK` if (a) the FR row → test file link is unique, and (b) the
>   test file → FR link in §"Reverse Traceability" exists.

| FR ID | SRS Section | Design Element (file) | Test File (planned) | Status | Bidirectional Check |
|-------|-------------|------------------------|---------------------|--------|---------------------|
| FR-01 台灣中文詞彙映射 | `SRS.md §3 FR-01` (L134-L148) | `src/engines/taiwan_linguistic.py` (`SPEC.md L192`) | `tests/test_fr_01_taiwan_linguistic.py` | PLANNED | OK |
| FR-02 SSML 解析 | `SRS.md §3 FR-02` (L150-L164) | `src/engines/ssml_parser.py` (`SPEC.md L193`) | `tests/test_fr_02_ssml_parser.py` | PLANNED | OK |
| FR-03 智能文本切分 | `SRS.md §3 FR-03` (L166-L180) | `src/engines/text_splitter.py` (`SPEC.md L194`) | `tests/test_fr_03_text_splitter.py` (multi-tier) **+** `tests/test_fr_03_text_splitter_edge_cases.py` (proposed split) | PLANNED | OK |
| FR-04 並行合成 | `SRS.md §3 FR-04` (L182-L194) | `src/engines/synthesis.py` (`SPEC.md L195`) | `tests/test_fr_04_synthesis.py` (concurrency) **+** `tests/test_fr_04_synthesis_concat.py` (byte-level concatenation) | PLANNED | OK |
| FR-05 斷路器 | `SRS.md §3 FR-05` (L196-L209) | `src/middleware/circuit_breaker.py` (`SPEC.md L197`) | `tests/test_fr_05_circuit_breaker.py` | PLANNED | OK |
| FR-06 Redis 快取 (optional) | `SRS.md §3 FR-06` (L211-L222) | `src/cache/redis_cache.py` (`SPEC.md L198`) | `tests/test_fr_06_redis_cache.py` | PLANNED | OK |
| FR-07 CLI 工具 | `SRS.md §3 FR-07` (L224-L243) | `src/cli.py` (`SPEC.md L187`) | `tests/test_fr_07_cli.py` | PLANNED | OK |
| FR-08 ffmpeg 音訊格式轉換 | `SRS.md §3 FR-08` (L245-L255) | `src/audio_converter.py` (`SPEC.md L188`) | `tests/test_fr_08_audio_converter.py` | PLANNED | OK |

**Notes on multi-file FRs (FR-03, FR-04)**:

- **FR-03** — The splitter has three recursive levels (sentence / clause / phrase) plus
  mixed-language boundary detection. A single test file would mix fixtures; splitting it
  keeps each file focused.
  - `tests/test_fr_03_text_splitter.py` — core happy-path chunking (sentence / clause /
    phrase boundaries, ≤ 250 char invariant).
  - `tests/test_fr_03_text_splitter_edge_cases.py` — edge cases: exactly-250-char input,
    no-boundary text, mixed CJK/Latin word boundary (`Hello你好`, `iPhone15`), empty input,
    single-char input, all-boundary input.
- **FR-04** — The two concerns (concurrent dispatch via `httpx.AsyncClient`; byte-level
  concatenation without re-encoding) are independent and have different mocking strategies.
  - `tests/test_fr_04_synthesis.py` — concurrency: asserts N coroutines are scheduled
    before any awaited, asserts order preservation, asserts 5xx → circuit-breaker counter
    increment.
  - `tests/test_fr_04_synthesis_concat.py` — concatenation: asserts concatenated byte
    length equals sum of inputs, asserts no ffmpeg/re-encoding calls, asserts header
    integrity at the slice boundaries.

Both proposed splits remain within the `tests/test_fr_<NN>_<slug>.py` naming convention and
do not invent new FRs; the FR ↔ test relationship is still 1-to-N (one FR, multiple test
files), which is allowed by the test-file naming convention.

### Per-FR forward link detail

> For each FR, the chain FR → SRS §3 → `src/...` → `tests/...` is restated in plain text so
> reviewers can verify the link without re-parsing the table.

- **FR-01** — `SRS.md L134-L148` describes the LEXICON mapping rule with 5 acceptance
  criteria; the design home is `src/engines/taiwan_linguistic.py` (`SPEC.md L192`); the
  planned test file is `tests/test_fr_01_taiwan_linguistic.py`, which must assert
  `len(LEXICON) >= 50`, the 12 canonical mappings, the Bopomofo space-separated form
  (`垃圾 → ㄌㄜˋ ㄙㄜˋ`, `和 → ㄏㄢˋ`), and the ≥ 95% corpus coverage on a labeled set.
- **FR-02** — `SRS.md L150-L164` describes the SSML tag subset; design home
  `src/engines/ssml_parser.py` (`SPEC.md L193`); planned test
  `tests/test_fr_02_ssml_parser.py` covers each tag, comments stripping, the `warn`-and-pass
  behavior for `pitch`/`volume`, and the parse-failure fallback to plain text.
- **FR-03** — `SRS.md L166-L180` describes the three-level recursive chunker with the 250-char
  cap (`MAX_CHARS_PER_REQUEST`); design home `src/engines/text_splitter.py` (`SPEC.md L194`);
  planned tests `tests/test_fr_03_text_splitter.py` (core) and
  `tests/test_fr_03_text_splitter_edge_cases.py` (boundaries).
- **FR-04** — `SRS.md L182-L194` describes concurrent dispatch and byte-level MP3
  concatenation; design home `src/engines/synthesis.py` (`SPEC.md L195`); planned tests
  `tests/test_fr_04_synthesis.py` and `tests/test_fr_04_synthesis_concat.py`.
- **FR-05** — `SRS.md L196-L209` describes the Closed → Open → Half-Open state machine with
  threshold=3 and timeout=10.0s; design home `src/middleware/circuit_breaker.py`
  (`SPEC.md L197`); planned test `tests/test_fr_05_circuit_breaker.py` exercises all three
  transitions, the 503 fast-fail response, and the `/health/circuit` + reset endpoints
  (`SPEC.md L161-L162`).
- **FR-06** — `SRS.md L211-L222` describes the optional Redis tier with 24h TTL; design
  home `src/cache/redis_cache.py` (`SPEC.md L198`); planned test
  `tests/test_fr_06_redis_cache.py` covers the key form, TTL, hit fast-path, and the
  no-Redis graceful skip.
- **FR-07** — `SRS.md L224-L243` describes the 5 invocation patterns; design home
  `src/cli.py` (`SPEC.md L187`); planned test `tests/test_fr_07_cli.py` invokes each
  pattern end-to-end and asserts the `--help` exit-0 behavior.
- **FR-08** — `SRS.md L245-L255` describes MP3 ↔ WAV via ffmpeg `subprocess`; design home
  `src/audio_converter.py` (`SPEC.md L188`); planned test
  `tests/test_fr_08_audio_converter.py` covers both directions, the subprocess call shape,
  and the missing-ffmpeg error path.

---

## Reverse Traceability (Test → FR)

> Every test file listed below must be reachable from the FR rows above, and every FR row
> above must be reachable from at least one test file in this list. This is the reverse
> traversal of the matrix.

| Test file (planned) | FR(s) covered | SRS sections | Notes |
|---------------------|---------------|--------------|-------|
| `tests/test_fr_01_taiwan_linguistic.py` | FR-01 | `SRS.md §3 FR-01` (L134-L148) | Asserts LEXICON size, the 12 canonical mappings, the Bopomofo form, and corpus coverage. |
| `tests/test_fr_02_ssml_parser.py` | FR-02 | `SRS.md §3 FR-02` (L150-L164) | One test per supported tag; comment-stripping; `pitch`/`volume` warn; fallback on parse failure. |
| `tests/test_fr_03_text_splitter.py` | FR-03 | `SRS.md §3 FR-03` (L166-L180) | Core: sentence / clause / phrase tiering; ≤ 250 invariant; optimal-range preference. |
| `tests/test_fr_03_text_splitter_edge_cases.py` | FR-03 | `SRS.md §3 FR-03` (L166-L180) | Boundary inputs: exactly-250, no-boundary, mixed CJK/Latin words, empty, single-char. |
| `tests/test_fr_04_synthesis.py` | FR-04 | `SRS.md §3 FR-04` (L182-L194) | Concurrency: N coroutines in flight; order preserved; 5xx → breaker counter increments. |
| `tests/test_fr_04_synthesis_concat.py` | FR-04 | `SRS.md §3 FR-04` (L182-L194) | Concatenation: byte length = sum; no re-encoding; header integrity at slice boundaries. |
| `tests/test_fr_05_circuit_breaker.py` | FR-05 | `SRS.md §3 FR-05` (L196-L209) | All three state transitions; 503 in Open; `/health/circuit` observability; reset endpoint. |
| `tests/test_fr_06_redis_cache.py` | FR-06 | `SRS.md §3 FR-06` (L211-L222) | Key form, TTL, hit fast-path, no-Redis graceful skip. |
| `tests/test_fr_07_cli.py` | FR-07 | `SRS.md §3 FR-07` (L224-L243) | All 5 invocation patterns from `SPEC.md L92-L97`; `--help` exit 0. |
| `tests/test_fr_08_audio_converter.py` | FR-08 | `SRS.md §3 FR-08` (L245-L255) | MP3→WAV, WAV→MP3; `subprocess` invocation; missing-ffmpeg error path. |

**Reverse-link summary**:

- 10 test files planned across 8 FRs.
- All 8 FRs are reachable from at least one test file (FR-03 and FR-04 each have 2 test
  files, as noted in the matrix above).
- All 10 test files map to a unique FR row in the forward matrix (no test file is
  unowned).

---

## Coverage Analysis

### FR coverage

| Metric | Target | Actual | Status |
|--------|--------|-------:|--------|
| FRs in scope | 8 (FR-01..FR-08) | 8 | ✅ 100% |
| FRs with ≥ 1 design element link | 8 | 8 | ✅ 100% |
| FRs with ≥ 1 test file link | 8 | 8 | ✅ 100% |
| FRs with bidirectional links (forward + reverse) | 8 | 8 | ✅ 100% |
| Invented FRs (must be 0) | 0 | 0 | ✅ |
| Duplicate FR IDs in matrix (must be 0) | 0 | 0 | ✅ |
| Orphan FRs (in SPEC, not in matrix, or vice versa) | 0 | 0 | ✅ |

### Bidirectional-link percentage

- **Forward links declared**: 8 (one per FR, pointing to ≥ 1 design element and ≥ 1 test file).
- **Reverse links declared**: 10 (one per test file, pointing to exactly one FR).
- **Bidirectional pairs**: 8 (every FR has a test-file link in the forward matrix AND every
  test file in the reverse matrix is reachable from its FR).
- **% bidirectional links**: **8 / 8 = 100%**.
- **% test files reachable from a FR**: **10 / 10 = 100%**.
- **% FRs reachable from a test file**: **8 / 8 = 100%**.

### Gaps and known unknowns

- **No implementation yet** — All `Status` values are `PLANNED`. This is expected at P1; the
  matrix declares the *links* but not yet the *evidence* (i.e., tests not yet written,
  implementations not yet coded). P3+ (implementation) and P5+ (testing) will move rows to
  `IMPLEMENTED` and `VERIFIED` per `SPEC_TRACKING.md` workflow.
- **FR-04 partial-success mode** — `SRS.md L192` says "if one chunk's request fails, the
  overall request must fail with HTTP 5xx." The control group has not added a partial-success
  mode; this is consistent with the SPEC §11 feature-freeze. Cross-reference
  `SPEC_TRACKING.md` "Open Questions" entry for FR-04.
- **FR-08 ffmpeg-missing policy** — `SRS.md L252` says "the service must continue to work for
  the other (already-supported) format." The exact policy (per-call vs. global disable) is
  deferred to P2 design; see `SPEC_TRACKING.md` "Open Questions" entry for FR-08.
- **FR-06 hash function** — `SPEC.md L87` specifies the form `hash(text + voice + speed)` but
  not the hash algorithm. This is a P2 design choice; see `SPEC_TRACKING.md` "Open Questions"
  entry for FR-06.
- **FR-03 mixed-language boundary rule** — `SPEC.md L75` forbids breaking inside a mixed
  Chinese/English word but does not define the boundary rule. P2 design must specify
  (e.g., "whitespace or punctuation"); see `SPEC_TRACKING.md` "Open Questions" entry for
  FR-03.

These gaps do **not** block P1 sign-off: every FR has a planned design home and a planned
test file, and every test file has a planned FR owner. They are flagged here so P2
(architecture) and P3+ (implementation) reviewers know what needs design-time decisions
before the rows can move to `IMPLEMENTED`.

---

## Change Log

| Version | Date | Change | Author |
|---------|------|--------|--------|
| v1.0 | 2026-06-03 | Initial creation. Authored as P1 deliverable `01-requirements/TRACEABILITY_MATRIX.md` for the kokoro-taiwan-proxy control group. Establishes bidirectional traceability for all 8 FRs (FR-01..FR-08) linking each to its `SRS.md §3` section, planned design element under `src/` (per `SPEC.md §7, L181-L205`), and planned test file under `tests/` (per the `tests/test_fr_<NN>_<slug>.py` convention). FR-03 and FR-04 each have a proposed second test file to keep fixtures focused; all 8 FRs reach 100% bidirectional coverage (8/8 forward, 10/10 reverse test-file links). Cites `SPEC.md L1-L254` (authoritative) and `SRS.md §1-L497` (P1 deliverable). | REQUIREMENTS_ENGINEER (Agent A) |

---

*End of TRACEABILITY_MATRIX — Kokoro Taiwan Proxy — v1.0 — harness-methodology v2.7.0.*
