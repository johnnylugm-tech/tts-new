# SPEC_TRACKING — Kokoro Taiwan Proxy

> Per-FR tracking matrix for the 8 pre-defined functional requirements of `kokoro-taiwan-proxy`.
> **Single source of truth**: `SPEC.md` v1.0.0-control (2026-03-31).
> **Authoritative FR list**: `01-requirements/SRS.md` §3 (P1 deliverable, APPROVED).
> **Constraint**: Control group (SPEC §11) — 8 FRs are immutable; no new FRs may be invented.

---

## Project Info

| Field | Value |
|-------|-------|
| **Project name** | `kokoro-taiwan-proxy` |
| **Project root** | `/Users/johnny/projects/tts-new` |
| **Version** | v1.0.0-control |
| **Date** | 2026-06-03 |
| **Document version** | v1.0 |
| **Status** | DRAFT (initial pass; all 8 FRs seeded with `PENDING` acceptance) |
| **Methodology framework** | harness-methodology v2.7.0 |
| **Author** | REQUIREMENTS_ENGINEER (Agent A) |
| **Source of truth** | `SPEC.md` (v1.0.0-control, 2026-03-31) |
| **Canonical FR list** | `01-requirements/SRS.md` §3 (FR-01..FR-08) |
| **Project role** | Control group for methodology-v2 improvement experiment (SPEC.md L14) |
| **Companion docs** | `SRS.md` (P1), `TRACEABILITY_MATRIX.md` (P1) |

---

## Tracking Matrix

> All 8 pre-defined FRs (FR-01..FR-08) are tracked below. Status is `DRAFT` for every row at the
> initial pass; owner is `unassigned` (control group does not assign per-FR owners in P1).
> Acceptance State is `PENDING` until downstream phases (P3+ implementation, P5+ testing) close
> each FR's acceptance criteria defined in `SRS.md` §3.

| FR ID | Description (1 line) | Status | Owner | Acceptance State | SRS Section | Source Citation |
|-------|----------------------|--------|-------|------------------|-------------|-----------------|
| FR-01 | 台灣中文詞彙映射 (LEXICON ≥ 50詞, 覆蓋率 ≥ 95%) | DRAFT | unassigned | PENDING | §3 FR-01 | SPEC.md L32-L51; SRS.md L134-L148 |
| FR-02 | SSML 解析 (speak/break/prosody/emphasis/voice/phoneme/say-as 標籤子集) | DRAFT | unassigned | PENDING | §3 FR-02 | SPEC.md L52-L65; SRS.md L150-L164 |
| FR-03 | 智能文本切分 (三級遞迴, Chunk ≤ 250 字, 不切中英文混合詞) | DRAFT | unassigned | PENDING | §3 FR-03 | SPEC.md L67-L75; SRS.md L166-L180 |
| FR-04 | 並行合成 (httpx.AsyncClient 並發, MP3 直接串接不重新編碼) | DRAFT | unassigned | PENDING | §3 FR-04 | SPEC.md L77-L79; SRS.md L182-L194 |
| FR-05 | 斷路器 (Closed→Open→Half-Open, threshold=3, timeout=10s, Open 回 503) | DRAFT | unassigned | PENDING | §3 FR-05 | SPEC.md L81-L85; SRS.md L196-L209 |
| FR-06 | Redis 快取 (key=hash(text+voice+speed), TTL=24h, 無 Redis 時略過) | DRAFT | unassigned | PENDING | §3 FR-06 | SPEC.md L86-L89; SRS.md L211-L222 |
| FR-07 | CLI 命令列工具 (`tts-v610`, 5 種 invocation, 支援 SSML 與 backend override) | DRAFT | unassigned | PENDING | §3 FR-07 | SPEC.md L91-L98; SRS.md L224-L243 |
| FR-08 | ffmpeg 音訊格式轉換 (MP3↔WAV, 透過 subprocess, 缺 ffmpeg 時明確錯誤) | DRAFT | unassigned | PENDING | §3 FR-08 | SPEC.md L100-L102; SRS.md L245-L255 |

### Matrix key

- **Status**: `DRAFT` (initial) | `READY-FOR-P2` (forward-declared ready) | `IN-P2` | `IN-P3` | `IMPLEMENTED` | `VERIFIED` | `BLOCKED`.
- **Owner**: per-FR owner. In the control group, all FRs start as `unassigned` (no per-FR owner
  has been designated in P1; ownership is assigned in later phases if methodology requires it).
- **Acceptance State**: `PENDING` (initial) | `PARTIAL` (some acceptance criteria met) | `MET` (all
  acceptance criteria from `SRS.md` §3 satisfied) | `WAIVED` (with documented reason).
- **SRS Section**: cross-reference to the FR's section in the authoritative `SRS.md` §3.
- **Source Citation**: SPEC.md line range (authoritative) plus SRS.md line range (P1 deliverable).

---

## Coverage Statistics

### FR count by status

| Status | Count | FR IDs |
|--------|------:|--------|
| DRAFT | 8 | FR-01, FR-02, FR-03, FR-04, FR-05, FR-06, FR-07, FR-08 |
| READY-FOR-P2 | 0 | — |
| IN-P2 | 0 | — |
| IN-P3 | 0 | — |
| IMPLEMENTED | 0 | — |
| VERIFIED | 0 | — |
| BLOCKED | 0 | — |
| **Total tracked** | **8** | — |

### FR count by owner

| Owner | Count | FR IDs |
|-------|------:|--------|
| unassigned | 8 | FR-01, FR-02, FR-03, FR-04, FR-05, FR-06, FR-07, FR-08 |
| (any other) | 0 | — |
| **Total tracked** | **8** | — |

### FR count by acceptance state

| Acceptance State | Count | FR IDs |
|------------------|------:|--------|
| PENDING | 8 | FR-01, FR-02, FR-03, FR-04, FR-05, FR-06, FR-07, FR-08 |
| PARTIAL | 0 | — |
| MET | 0 | — |
| WAIVED | 0 | — |
| **Total tracked** | **8** | — |

### Coverage checks (control group invariants)

- ✅ **FR coverage = 8/8** (100%); all FRs in SPEC.md §3 (L32-L103) are tracked; no gaps.
- ✅ **No duplicate FR IDs** in the matrix (FR-01..FR-08 appear exactly once each).
- ✅ **No invented FRs** — every row is anchored to a SPEC.md line range and an SRS.md section.
- ✅ **Every row has all 7 required columns** populated (FR ID, Description, Status, Owner, Acceptance State, SRS Section, Source Citation).
- ✅ **Orphan check** = 0 orphans: 8 FRs in SPEC ↔ 8 FRs in SRS §3 ↔ 8 rows in this matrix.

---

## Open Questions

> The following questions are flagged for downstream reviewers (Agent B / methodology-v2
> reviewers). They do **not** block P1 sign-off — every FR is fully tracked above. Each item
> is a candidate clarification for P2 (architecture) or P3+ (implementation) phases.

- **FR-01** — Does the "≥ 95% mapping coverage" target apply to a specific reference corpus, or
  to any Taiwan-leaning Chinese text submitted to the proxy? SRS.md §3 FR-01 AC2 says "a
  Taiwan-leaning Chinese corpus" but does not name one. **Need**: a reference corpus choice
  (e.g., 中央社 sample set) for the corpus coverage test. Source: `SRS.md L141`.
- **FR-01** — The Bopomofo output format for tokens like `垃圾 → ㄌㄜˋ ㄙㄜˋ` uses a space
  between syllables. Is the space required, or may it be omitted / replaced by a different
  separator? SRS.md §3 FR-01 AC5 states the space-separated form is the expected form.
  Source: `SPEC.md L41, L47`; `SRS.md L146`.
- **FR-02** — The exact list of supported `<emphasis>` levels — `strong` / `moderate` — and
  the `1.1×` speed multiplier is a single example; are `level="none"` and `level="reduced"`
  to be supported, ignored with a `warn`, or rejected? SPEC.md is silent. Source: `SPEC.md L59`.
- **FR-03** — The "do not break in the middle of a mixed Chinese/English word" rule (SPEC.md L75)
  has no concrete rule for what counts as a "mixed word" boundary (e.g., `Python3`, `iPhone`,
  `Hello你好`). Needs a concrete boundary-detection rule in P2 design. Source: `SPEC.md L75`;
  `SRS.md L177`.
- **FR-04** — If one chunk's request fails, the entire request fails with 5xx and the breaker
  counter increments. Is there a partial-success / best-effort mode? (Control-group scope
  suggests **no** — but worth flagging for reviewer confirmation.) Source: `SRS.md L192`.
- **FR-06** — The cache key form is `hash(text + voice + speed)`. Which hash function
  (SHA-256, MD5, xxhash) and which serialization form (`+` as literal char, or struct
  serialization)? SPEC.md does not specify. Source: `SPEC.md L87`.
- **FR-07** — When `-i input.txt -o output/` is given, "one output file per input line" is
  stated. Should blank lines be skipped? Should very long lines be split? (Likely out of
  scope for the CLI flag itself — splitting is FR-03 — but worth confirming the policy.)
  Source: `SRS.md L239`; `SPEC.md L93`.
- **FR-08** — If `ffmpeg` is not on `PATH`, FR-08 AC3 says "conversion must fail with a clear
  error message; the service must continue to work for the other (already-supported) format."
  Does "other format" mean: (a) MP3-only requests succeed while WAV requests fail, or
  (b) once an ffmpeg call fails, all subsequent conversions are also disabled? Clarification
  needed in P2 design. Source: `SRS.md L252`; `SPEC.md L228` (R3).
- **Cross-cutting** — The control-group constraint "feature freeze: only bug fixes" (SPEC §11)
  forbids any new feature work but does not explicitly forbid refactors for clarity. If a
  refactor is proposed in P3+, does it require methodology-v2 reviewer approval first?
  Source: `SPEC.md L247-L254`.
- **Cross-cutting** — The 82-test count is fixed (SPEC §10, L200, L235). If a new test is added
  (e.g., for a bug fix), does the 82 number need to update to 83, or must the new test replace
  an existing one? Source: `SPEC.md L200, L235`; `SRS.md L457`.

---

## Change Log

| Version | Date | Change | Author |
|---------|------|--------|--------|
| v1.0 | 2026-06-03 | Initial creation. All 8 FRs (FR-01..FR-08) seeded with `DRAFT` status, `unassigned` owner, and `PENDING` acceptance state. Cites SPEC.md L32-L103 (authoritative FR list) and SRS.md §3 (P1 deliverable). Authored as P1 deliverable `01-requirements/SPEC_TRACKING.md` (Spec Tracking Matrix) for the kokoro-taiwan-proxy control group. | REQUIREMENTS_ENGINEER (Agent A) |

---

*End of SPEC_TRACKING — Kokoro Taiwan Proxy — v1.0 — harness-methodology v2.7.0.*
