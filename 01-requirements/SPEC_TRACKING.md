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
| **Date** | 2026-06-04 |
| **Document version** | v1.1 |
| **Status** | DRAFT (v1.1: updated for SRS.md security content — NFR-08, R5/R6, §2.6 security posture) |
| **Methodology framework** | harness-methodology v2.7.0 |
| **Author** | REQUIREMENTS_ENGINEER (Agent A) |
| **Source of truth** | `SPEC.md` (v1.0.0-control, 2026-03-31) |
| **Canonical FR list** | `01-requirements/SRS.md` §3 (FR-01..FR-08); §4 (NFR-01..NFR-08) |
| **Project role** | Control group for methodology-v2 improvement experiment (SPEC.md L14) |
| **Companion docs** | `SRS.md` (P1), `TRACEABILITY_MATRIX.md` (P1) |

---

## FR Tracking Matrix

> All 8 pre-defined FRs (FR-01..FR-08) are tracked below. Status is `DRAFT` for every row at the
> initial pass; owner is `unassigned` (control group does not assign per-FR owners in P1).
> Acceptance State is `PENDING` until downstream phases (P3+ implementation, P5+ testing) close
> each FR's acceptance criteria defined in `SRS.md` §3.

| FR ID | Description (1 line) | Status | Owner | Acceptance State | SRS Section | Source Citation |
|-------|----------------------|--------|-------|------------------|-------------|-----------------|
| FR-01 | 台灣中文詞彙映射 (LEXICON ≥ 50詞, 覆蓋率 ≥ 95%) | DRAFT | unassigned | PENDING | §3 FR-01 | SPEC.md L32-L51; SRS.md L153-L167 |
| FR-02 | SSML 解析 (speak/break/prosody/emphasis/voice/phoneme/say-as 標籤子集) | DRAFT | unassigned | PENDING | §3 FR-02 | SPEC.md L52-L65; SRS.md L169-L183 |
| FR-03 | 智能文本切分 (三級遞迴, Chunk ≤ 250 字, 不切中英文混合詞) | DRAFT | unassigned | PENDING | §3 FR-03 | SPEC.md L67-L75; SRS.md L185-L199 |
| FR-04 | 並行合成 (httpx.AsyncClient 並發, MP3 直接串接不重新編碼) | DRAFT | unassigned | PENDING | §3 FR-04 | SPEC.md L77-L79; SRS.md L201-L213 |
| FR-05 | 斷路器 (Closed→Open→Half-Open, threshold=3, timeout=10s, Open 回 503) | DRAFT | unassigned | PENDING | §3 FR-05 | SPEC.md L81-L85; SRS.md L215-L228 |
| FR-06 | Redis 快取 (key=hash(text+voice+speed), TTL=24h, 無 Redis 時略過) | DRAFT | unassigned | PENDING | §3 FR-06 | SPEC.md L86-L89; SRS.md L230-L241 |
| FR-07 | CLI 命令列工具 (`tts-v610`, 5 種 invocation, 支援 SSML 與 backend override) | DRAFT | unassigned | PENDING | §3 FR-07 | SPEC.md L91-L98; SRS.md L243-L262 |
| FR-08 | ffmpeg 音訊格式轉換 (MP3↔WAV, 透過 subprocess, 缺 ffmpeg 時明確錯誤) | DRAFT | unassigned | PENDING | §3 FR-08 | SPEC.md L100-L102; SRS.md L264-L274 |

### Matrix key

- **Status**: `DRAFT` (initial) | `READY-FOR-P2` (forward-declared ready) | `IN-P2` | `IN-P3` | `IMPLEMENTED` | `VERIFIED` | `BLOCKED`.
- **Owner**: per-FR owner. In the control group, all FRs start as `unassigned` (no per-FR owner
  has been designated in P1; ownership is assigned in later phases if methodology requires it).
- **Acceptance State**: `PENDING` (initial) | `PARTIAL` (some acceptance criteria met) | `MET` (all
  acceptance criteria from `SRS.md` §3 satisfied) | `WAIVED` (with documented reason).
- **SRS Section**: cross-reference to the FR's section in the authoritative `SRS.md` §3.
- **Source Citation**: SPEC.md line range (authoritative) plus SRS.md line range (P1 deliverable).

---

## NFR Tracking Matrix

> The 8 non-functional requirements (NFR-01..NFR-08) from `SRS.md` §4 are tracked below.
> NFR-08 (Security) was added in SRS.md v1.1 alongside the security posture statement in §2.6
> and the expanded risk matrix (R5–R8). All NFRs are derived from `SPEC.md` and are traceable
> by line number; no new NFRs are invented.

| NFR ID | Category | Requirement (1 line) | Status | Acceptance State | SRS Section | Source Citation |
|--------|----------|----------------------|--------|------------------|-------------|-----------------|
| NFR-01 | Performance | TTFB < 300 ms (warm proxy, excl. network to Kokoro) | DRAFT | PENDING | §4 | SPEC.md L110; SRS.md L284 |
| NFR-02 | Linguistic coverage | LEXICON coverage of Mainland-leaning tokens ≥ 80% | DRAFT | PENDING | §4 | SPEC.md L111; SRS.md L285 |
| NFR-03 | Linguistic accuracy | Tone (變調) correctness ≥ 95% | DRAFT | PENDING | §4 | SPEC.md L112; SRS.md L286 |
| NFR-04 | Reliability | API availability ≥ 99% (30-day rolling) | DRAFT | PENDING | §4 | SPEC.md L113; SRS.md L287 |
| NFR-05 | Reliability | Error recovery time < 10 s | DRAFT | PENDING | §4 | SPEC.md L114; SRS.md L288 |
| NFR-06 | Operability | Cold-start readiness (warmup on launch) | DRAFT | PENDING | §4 | SPEC.md L132-L133; SRS.md L289 |
| NFR-07 | Robustness | Request timeout 30.0 s | DRAFT | PENDING | §4 | SPEC.md L129; SRS.md L290 |
| NFR-08 | Security | Input validation on all user-supplied fields; secrets via env vars; no PII in logs | DRAFT | PENDING | §4; §2.6 | SPEC.md L216-L218, L167-L175, L20-L26; SRS.md L291, L129-L146 |

### NFR matrix key

- **Status**: same lifecycle as FR matrix (`DRAFT` → `VERIFIED`).
- **Acceptance State**: `PENDING` until measurable targets are verified in P5+ testing.
- **SRS Section**: cross-reference to the NFR's row in `SRS.md` §4.
- **Source Citation**: SPEC.md line(s) for the target value plus SRS.md line(s) for the NFR definition and (for NFR-08) the security posture in §2.6.

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
| **FR subtotal** | **8** | — |

### NFR count by status

| Status | Count | NFR IDs |
|--------|------:|--------|
| DRAFT | 8 | NFR-01, NFR-02, NFR-03, NFR-04, NFR-05, NFR-06, NFR-07, NFR-08 |
| READY-FOR-P2 | 0 | — |
| IN-P2 | 0 | — |
| IN-P3 | 0 | — |
| IMPLEMENTED | 0 | — |
| VERIFIED | 0 | — |
| BLOCKED | 0 | — |
| **NFR subtotal** | **8** | — |

### FR count by owner

| Owner | Count | FR IDs |
|-------|------:|--------|
| unassigned | 8 | FR-01, FR-02, FR-03, FR-04, FR-05, FR-06, FR-07, FR-08 |
| (any other) | 0 | — |
| **FR subtotal** | **8** | — |

### NFR count by owner

| Owner | Count | NFR IDs |
|-------|------:|--------|
| unassigned | 8 | NFR-01, NFR-02, NFR-03, NFR-04, NFR-05, NFR-06, NFR-07, NFR-08 |
| (any other) | 0 | — |
| **NFR subtotal** | **8** | — |

### FR count by acceptance state

| Acceptance State | Count | FR IDs |
|------------------|------:|--------|
| PENDING | 8 | FR-01, FR-02, FR-03, FR-04, FR-05, FR-06, FR-07, FR-08 |
| PARTIAL | 0 | — |
| MET | 0 | — |
| WAIVED | 0 | — |
| **FR subtotal** | **8** | — |

### NFR count by acceptance state

| Acceptance State | Count | NFR IDs |
|------------------|------:|--------|
| PENDING | 8 | NFR-01, NFR-02, NFR-03, NFR-04, NFR-05, NFR-06, NFR-07, NFR-08 |
| PARTIAL | 0 | — |
| MET | 0 | — |
| WAIVED | 0 | — |
| **NFR subtotal** | **8** | — |

### Combined totals

| Category | Tracked |
|----------|--------:|
| Functional Requirements (FR) | 8 |
| Non-Functional Requirements (NFR) | 8 |
| **Total tracked items** | **16** |

### Coverage checks (control group invariants)

- ✅ **FR coverage = 8/8** (100%); all FRs in SPEC.md §3 (L32-L103) are tracked; no gaps.
- ✅ **NFR coverage = 8/8** (100%); all NFRs in SRS.md §4 (L278-L298) are tracked; no gaps.
- ✅ **Combined FR+NFR coverage = 16/16** (100%); all requirements from SRS.md §3–§4 are tracked.
- ✅ **No duplicate FR IDs** in the matrix (FR-01..FR-08 appear exactly once each).
- ✅ **No duplicate NFR IDs** in the matrix (NFR-01..NFR-08 appear exactly once each).
- ✅ **No invented FRs** — every row is anchored to a SPEC.md line range and an SRS.md section.
- ✅ **No invented NFRs** — NFR-08 is derived from existing SPEC.md source lines (L216-L218, L167-L175, L20-L26); no new SPEC requirements were created.
- ✅ **Every row has all 7 required columns** populated (ID, Description/Category+Requirement, Status, Owner, Acceptance State, SRS Section, Source Citation).
- ✅ **Orphan check** = 0 orphans: 8 FRs in SPEC ↔ 8 FRs in SRS §3 ↔ 8 FR rows in this matrix; 8 NFRs in SRS §4 ↔ 8 NFR rows in this matrix.

---

## Open Questions

> The following questions are flagged for downstream reviewers (Agent B / methodology-v2
> reviewers). They do **not** block P1 sign-off — every FR and NFR is fully tracked above.
> Each item is a candidate clarification for P2 (architecture) or P3+ (implementation) phases.

### FR-specific

- **FR-01** — Does the "≥ 95% mapping coverage" target apply to a specific reference corpus, or
  to any Taiwan-leaning Chinese text submitted to the proxy? SRS.md §3 FR-01 AC2 says "a
  Taiwan-leaning Chinese corpus" but does not name one. **Need**: a reference corpus choice
  (e.g., 中央社 sample set) for the corpus coverage test. Source: `SRS.md L158`.
- **FR-01** — The Bopomofo output format for tokens like `垃圾 → ㄌㄜˋ ㄙㄜˋ` uses a space
  between syllables. Is the space required, or may it be omitted / replaced by a different
  separator? SRS.md §3 FR-01 AC5 states the space-separated form is the expected form.
  Source: `SPEC.md L41, L47`; `SRS.md L165`.
- **FR-02** — The exact list of supported `<emphasis>` levels — `strong` / `moderate` — and
  the `1.1×` speed multiplier is a single example; are `level="none"` and `level="reduced"`
  to be supported, ignored with a `warn`, or rejected? SPEC.md is silent. Source: `SPEC.md L59`.
- **FR-03** — The "do not break in the middle of a mixed Chinese/English word" rule (SPEC.md L75)
  has no concrete rule for what counts as a "mixed word" boundary (e.g., `Python3`, `iPhone`,
  `Hello你好`). Needs a concrete boundary-detection rule in P2 design. Source: `SPEC.md L75`;
  `SRS.md L196`.
- **FR-04** — If one chunk's request fails, the entire request fails with 5xx and the breaker
  counter increments. Is there a partial-success / best-effort mode? (Control-group scope
  suggests **no** — but worth flagging for reviewer confirmation.) Source: `SRS.md L211`.
- **FR-06** — The cache key form is `hash(text + voice + speed)`. Which hash function
  (SHA-256, MD5, xxhash) and which serialization form (`+` as literal char, or struct
  serialization)? SPEC.md does not specify. Source: `SPEC.md L87`.
- **FR-07** — When `-i input.txt -o output/` is given, "one output file per input line" is
  stated. Should blank lines be skipped? Should very long lines be split? (Likely out of
  scope for the CLI flag itself — splitting is FR-03 — but worth confirming the policy.)
  Source: `SRS.md L259`; `SPEC.md L93`.
- **FR-08** — If `ffmpeg` is not on `PATH`, FR-08 AC3 says "conversion must fail with a clear
  error message; the service must continue to work for the other (already-supported) format."
  Does "other format" mean: (a) MP3-only requests succeed while WAV requests fail, or
  (b) once an ffmpeg call fails, all subsequent conversions are also disabled? Clarification
  needed in P2 design. Source: `SRS.md L272`; `SPEC.md L228` (R3).

### NFR-specific (security/NFR-08)

- **NFR-08** — The SRS states "logging framework must sanitize or redact env-var values" (R6
  mitigation, `SRS.md L457`) but does not specify the redaction mechanism (regex-based
  stripping? allow-list of safe keys?). P2 design must choose a concrete log-sanitization
  strategy. Source: `SRS.md L457`; `SRS.md L142` (§2.6 secret management).
- **NFR-08** — Input validation coverage is specified for `SpeechRequest` fields (`input`,
  `voice`, `speed`, `response_format`, `model`). Should the CLI (`tts-v610`) also perform the
  same validation before forwarding to the proxy, or is CLI input trusted? SRS.md §7 rows 4–6
  scope validation to the route layer only. Source: `SRS.md L431-L432`; `SRS.md L439-L441`.
- **NFR-08** — The security posture in §2.6 is declarative (TLS not implemented, RBAC out of
  scope). If a methodology reviewer in a later phase requires measurable acceptance criteria
  for "security posture," what form should those criteria take (e.g., attestation that no
  secrets appear in `git grep` output, or that TLS is documented as deferred)? The posture
  items are currently untestable by the existing 82-test framework. Source: `SRS.md L129-L146`
  (§2.6); `SPEC.md L200, L235`.
- **R5/R6** — The new SSRF risk (R5, `SRS.md L455`) and secret-leakage risk (R6, `SRS.md L456`)
  are both rated "Low" likelihood. Should the P3+ test plan include explicit adversarial test
  cases for crafted SSML payloads (R5) and debug-log inspection (R6), or are these covered by
  the existing input-validation tests? Source: `SRS.md L455-L456`.

### Cross-cutting

- **Cross-cutting** — The control-group constraint "feature freeze: only bug fixes" (SPEC §11)
  forbids any new feature work but does not explicitly forbid refactors for clarity. If a
  refactor is proposed in P3+, does it require methodology-v2 reviewer approval first?
  Source: `SPEC.md L247-L254`.
- **Cross-cutting** — The 82-test count is fixed (SPEC §10, L200, L235). If a new test is added
  (e.g., for a bug fix), does the 82 number need to update to 83, or must the new test replace
  an existing one? Source: `SPEC.md L200, L235`; `SRS.md L491`.
- **Cross-cutting** — Security vocabulary (input validation, permission model, PII logging, TLS,
  secrets management) is now present in SRS.md via NFR-08, §2.6, R5–R6, and §7 rows 6–7. These
  are derived from existing SPEC.md source lines — no new SPEC requirements were created.
  However, the expanded risk matrix (R5–R8) and security posture statement add content not
  previously tracked. Does this expansion require a formal SPEC.md amendment, or is the SRS.md
  derivation sufficient under methodology-v2 rules? Source: `SRS.md L129-L146` (§2.6);
  `SRS.md L449-L458` (§8 risks).

---

## Change Log

| Version | Date | Change | Author |
|---------|------|--------|--------|
| v1.0 | 2026-06-03 | Initial creation. All 8 FRs (FR-01..FR-08) seeded with `DRAFT` status, `unassigned` owner, and `PENDING` acceptance state. Cites SPEC.md L32-L103 (authoritative FR list) and SRS.md §3 (P1 deliverable). Authored as P1 deliverable `01-requirements/SPEC_TRACKING.md` (Spec Tracking Matrix) for the kokoro-taiwan-proxy control group. | REQUIREMENTS_ENGINEER (Agent A) |
| v1.1 | 2026-06-04 | **SRS.md security content sync.** Updated all SRS.md source citations to reflect line-number shift (496→531 lines). Added NFR Tracking Matrix section covering NFR-01..NFR-08 (including new NFR-08 Security). Expanded Coverage Statistics with NFR-specific breakdowns and combined FR+NFR totals (16 items). Updated Open Questions with four security-specific items (NFR-08 testability gaps, R5/R6 adversarial testing, security posture measurability). No FR descriptions changed — all 8 FR rows are identical to v1.0 except for updated SRS.md line ranges. New content derived from SRS.md v1.1: §2.6 (security posture, L129-L146), §4 NFR-08 (L291), §7 rows 6–7 (L431-L432), §8 R5–R8 (L455-L458). | REQUIREMENTS_ENGINEER (Agent A) |

---

*End of SPEC_TRACKING — Kokoro Taiwan Proxy — v1.1 — harness-methodology v2.7.0.*
