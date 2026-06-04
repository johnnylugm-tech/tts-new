# Control Group Manifest — Kokoro Taiwan Proxy

> **Status**: Living document · **Created**: 2026-06-04 · **Phase 3 Implementation**
> **Source authority**: SPEC.md §11 L247-L254 (control group invariants, immutable)
> **Related**: SAD.md §6.4 Permission model + Encryption posture; §7 NFR-02/03 `open_question`; ADR-04 (Semaphore), ADR-07 (ffmpeg)

## 1. Purpose

This document records the **methodology-v2 control group** decisions for the
`kokoro-taiwan-proxy` project. Anything declared here is the **experimental
baseline** that any future treatment group in the methodology-v2 experiment
will be compared against. Items are deliberately non-features (controls) and
must not be changed without amending SPEC.md.

## 2. Phase 2 → Phase 3 Carryover Status

| # | Carryover | Owner | Status (2026-06-04) |
|---|-----------|-------|---------------------|
| C-1 | `MAX_CONCURRENT_SYNTHESIS` env var (default 8) in `src/config.py` | Orchestrator | **CLOSED in Step 4b** |
| C-2 | FR-01 reference corpus naming (NFR-02 ≥ 80% coverage gate) | methodology-v2 reviewer | **OPEN** — placeholder, see §3 |
| C-3 | NFR-03 tone-sandhi ≥ 95% audit rubric | methodology-v2 reviewer | **OPEN** — template, see §4 |
| C-4 | FR-04 partial-success WAIVE confirmation | P2 decision (P2-DD-6) | **CLOSED**, restated in §5 |

## 3. C-2 — FR-01 Reference Corpus (NFR-02)

**P2 architecture position (SAD.md §7 NFR-02)**: The reference corpus is
**not named in P2 architecture** — corpus selection is a **P3 action owned by
the methodology-v2 reviewer**. Until a fixed corpus is named, the ≥ 80%
coverage target is **not verifiable in CI**. The SAB `open_question` flag for
NFR-02 captures this (SAD §9 `nfr_traceability.NFR-02.open_question`).

**P3 placeholder** (TO BE FILLED BY methodology-v2 REVIEWER):

```yaml
corpus_name: "<TBD — labeled Taiwan-Chinese sample set, e.g. 100-500 sentences
              from a Taiwan news source or the Sinica corpus Taiwan-subset>"
corpus_size: <int>           # recommended 100-500 sentences
corpus_source: "<URL or path>"
corpus_format: "<text/jsonl/csv>"
expected_coverage: ">= 80% of LEXICON entries must appear >= 1 time"
reviewer: "<name>            # methodology-v2 experimental design owner"
reviewer_signed_off_at: <ISO8601>
```

**Acceptance gate** (unlocks NFR-02 = MET): reviewer signs §3 and the
`tests/test_fr_01_lexicon_coverage.py` test parametrize ids match the corpus
naming scheme. Until then, NFR-02 is **OPEN** in SAB.

## 4. C-3 — NFR-03 Tone-Sandhi Audit Rubric

**P2 architecture position (SAD.md §7 NFR-03)**: The audit rubric
(sample size, reviewer assignment, scoring scale) is **not defined in P2
architecture** — it is a P3 deliverable. The ≥ 95% acceptance gate is
**unmeasurable** until the rubric exists. The proxy implementation **cannot
own this gate** (manual A-B audit).

**P3 template** (TO BE FILLED BY methodology-v2 REVIEWER):

```yaml
sample_size: <int>           # recommended 200-500 sentences with tone-sandhi contexts
reviewer: "<name>            # must be a Mandarin-fluent Taiwan linguist"
scoring_scale: "binary correct/incorrect per sandhi site; 1 minor = 0.5"
acceptance_threshold: ">= 95% correct (or 0.5-weighted) per reviewer"
review_cadence: "<e.g., one-shot before P3 exit, or quarterly>"
reviewer_signed_off_at: <ISO8601>
```

**Acceptance gate** (unlocks NFR-03 = MET): reviewer signs §4 and the
`tests/test_fr_01_tone_sandhi.py` corpus is sourced from the audit sample.
Until then, NFR-03 is **OPEN** in SAB.

## 5. C-4 — FR-04 Partial-Success WAIVE (restated)

**P2 Design Decision 6 (P2-DD-6)**: partial-success mode is **WAIVED for
control-group scope** (locked at P2 advance, see `git log e89c0f9`).

**Implementation contract** (`src/engines/synthesis.py`):

- `asyncio.gather(*[synthesize_one(c) for c in chunks])` raises on the **first**
  failed coroutine and **discards all partial results**.
- No fallback aggregation, no `[partial_success=true]` response body, no
  best-effort return of successful chunks.
- A single failed chunk fails the entire request with HTTP 500 + the
  underlying `BackendError` / `httpx.TimeoutException` / `CircuitOpenError`.

**Why this is a control invariant**: methodology-v2 treatments may add
partial-success aggregation; the control group's "all-or-nothing" baseline
is the experimental comparator.

## 6. R8 — RBAC / Permission Model (NFR-08)

**Explicit non-feature** (PROJECT_BRIEF.md §5, SRS.md §1.3 / §2.6 / §8 R8;
restated in SAD.md §6.4 Permission model).

The proxy does **not** implement:

- User-level authentication
- Role-based access control (RBAC)
- Per-caller authorization
- Tenancy / quota
- API key issuance

All callers that can reach the listening socket are treated as having
**full permission** to invoke every endpoint. The proxy trusts the
**enclosing network boundary** (loopback interface, reverse proxy, or
upstream API gateway) as the permission enforcement point. If a deployment
needs finer-grained permission, it must be added in that boundary, **not
in the proxy** (SPEC.md §11 L247-L254 feature-freeze constraint).

## 7. R7 — Transport / At-Rest Encryption

**Explicit non-feature** (SAD.md §6.4 Encryption posture).

- **In-transit TLS**: delegated to a reverse proxy; the FastAPI app does
  **not** terminate TLS and does not bundle an HTTPS server certificate.
  Loopback HTTP to `Kokoro` is plain text (both endpoints on `localhost`).
- **At-rest encryption** of cached audio bytes in Redis: **out of scope**.
  Cache stores synthesis result bytes keyed by SHA-256 hash (P2-DD-3); bytes
  are not encrypted at rest. Introducing at-rest encryption would be a new
  technology decision prohibited by the feature freeze (SPEC.md §11).

## 8. NFR-08 Log Sanitization (Allow-List)

Implemented in `src/main.py` (or `src/logging_sanitizer.py` per SAD §6.1).
The 12 allowed keys are:

| Key | Type | Notes |
|-----|------|-------|
| `event` | `str` | e.g. `ssml.unsupported_attr`, `cache.unavailable`, `ffmpeg.unavailable` |
| `ts` | `str` | ISO-8601 UTC |
| `level` | `Literal["debug","info","warn","error"]` | |
| `request_id` | `str` | UUID4 per request |
| `fr_id` | `str` | `FR-01`..`FR-08` |
| `voice` | `str` | voice name only |
| `format` | `str` | `mp3` or `wav` |
| `duration_ms` | `int` | operation latency |
| `cache_hit` | `bool` | FR-06 hit/miss |
| `circuit_state` | `str` | `closed`/`open`/`half_open` |
| `error_code` | `str` | `VALIDATION_ERROR` / `CIRCUIT_OPEN` / ... |
| `latency_ms` | `int` | end-to-end |

**Deny by default** (P2-DD-5): any other key (`text`, `input`, `ssml`,
`headers`, `api_key`, `token`, `prompt`) is dropped silently and a
`dropped_pii=1` counter is incremented.

## 9. Test Inventory Lock (SPEC §11.3)

The **82-test set** enumerated in `01-requirements/TEST_INVENTORY.yaml`
(P1 naming authority) and `02-architecture/TEST_SPEC.md` (P2 single source
of truth) is **immutable** for this control group:

- No test deletion
- No test modification (parametrize ids, function names, expected values
  are frozen)
- No coverage reduction

Additions to the test set are **permitted** (e.g. `tests/test_nfr08_*.py`
sanitizer regression, FR-04 micro-benchmark) but are **out of scope for
the 82-count invariant**. The 82-count must remain green throughout P3-P8.

## 10. Revision Log

| Date | Change | Author | Commit |
|------|--------|--------|--------|
| 2026-06-04 | Initial document; C-1 + C-4 closed; C-2 + C-3 templates; R7/R8 restated | Orchestrator | (P3 init) |
