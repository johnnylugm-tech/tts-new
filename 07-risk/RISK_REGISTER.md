# RISK_REGISTER.md — Phase 7 Risk Register

**Project**: tts-new (Kokoro Taiwan TTS Proxy)
**Phase**: 7 — Risk Management
**Date**: 2026-06-08
**Status**: COMPLETE

---

## Scoring Key

| Likelihood | Label |
|------------|-------|
| 1 | Very Low |
| 2 | Low |
| 3 | Medium |
| 4 | High |
| 5 | Very High |

| Impact | Label |
|--------|-------|
| 1 | Low |
| 2 | Medium |
| 3 | High |
| 4 | Critical |

**Score** = Likelihood × Impact. HIGH risk threshold: Score ≥ 9.

---

## Risk Register

| Risk ID | Name | Likelihood (1-5) | Impact (1-5) | Score | Category | Mitigation Approach | Status |
|---------|------|-----------------|-------------|-------|----------|---------------------|--------|
| R-01 | Parallel MP3 Concat Race Condition | 2 | 3 | 6 | Technical / Concurrency | Ordered asyncio gather with deterministic chunk indexing; byte-level concat (no re-encoding); verified by FR-04 mutation tests | Mitigated |
| R-02 | Per-Worker Independent Circuit Breaker State | 2 | 2 | 4 | Architecture / Design | Accepted per P2-DD-6 design decision; Half-Open probe correctness verified by FR-05 tests; single-worker scope per control-group | Accepted |
| R-03 | ffmpeg Subprocess Timeout / Missing Binary | 2 | 2 | 4 | Infrastructure / External | Per-call ffmpeg check (P2-DD-4); FFmpegUnavailableError → HTTP 500; subprocess.run(timeout=…) bounds execution; FR-08 mutation tests cover both paths | Mitigated |
| R-04 | Redis Optional Dependency Fallback | 2 | 1 | 2 | Infrastructure / External | Unit tests mock Redis absence and verify graceful passthrough; cache optional by design (FR-06); no startup dependency | Accepted |
| R-05 | CRG Cohesion Sensitivity to Entry-Point Refactors | 1 | 1 | 1 | Architecture / Quality | Hub-and-spoke CRG design validated in P3; entry points in src/api/ with utils.py hub compensating external edges; score locked at 97.1 | Accepted |

---

## High-Risk Module Source (CLAUDE.md Architecture Constraints)

| Module | Annotated Risk | Resolved By |
|--------|---------------|------------|
| `src/engines/synthesis.py` | Parallel httpx dispatch + byte-level MP3 concat; no re-encoding | R-01 → Mitigated in P3 implementation + FR-04 mutation tests |
| `src/infrastructure/circuit_breaker.py` | In-process state; per-worker independent; Half-Open probe correctness | R-02 → Accepted per P2-DD-6; FR-05 tests verify probe |
| `src/infrastructure/audio_converter.py` | Subprocess call to ffmpeg; timeout handling; missing-binary behavior | R-03 → Mitigated via FFmpegUnavailableError; FR-08 mutation tests |
| `src/infrastructure/redis_cache.py` | Optional dependency; graceful no-Redis fallback | R-04 → Accepted; unit tests verify fallback |

---

## Deferred Fix Status

| Item | Source | Status |
|------|--------|--------|
| mutation_testing score (P3 Gate 2 defer) | deferred_fixes.md | Resolved in P4-P6: test_mutation_kills*.py files added; setup.cfg paths_to_exclude configured; Gate 4 score 97.1 |

---

## Risk Register Summary

| Level | Count | Action |
|-------|-------|--------|
| High (≥9) | 0 | None — no formal mitigation plans required |
| Medium (6-8) | 1 | Mitigated (R-01) |
| Medium (3-5) | 2 | 1 Mitigated (R-03), 1 Accepted (R-02) |
| Low (<3) | 2 | Accepted (R-04, R-05) |
| **Total** | **5** | All addressed |
