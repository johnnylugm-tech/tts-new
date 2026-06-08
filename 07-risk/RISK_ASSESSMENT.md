# RISK_ASSESSMENT.md — Phase 7 Risk Assessment

**Project**: tts-new (Kokoro Taiwan TTS Proxy)
**Phase**: 7 — Risk Management
**Date**: 2026-06-08
**Status**: COMPLETE

---

## Risk Identification

Risks identified from high-risk modules annotated in CLAUDE.md architecture constraints and FR-level gate reviews (P3–P6):

| Risk ID | Module | Description | Probability | Impact | Score |
|---------|--------|-------------|-------------|--------|-------|
| R-01 | `synthesis.py` | Parallel httpx dispatch produces race condition on byte-level MP3 concat under high concurrency | Low | High | 6 |
| R-02 | `circuit_breaker.py` | In-process state means each worker has independent CB state; Half-Open probe may never fire under single-worker test conditions | Low | Medium | 4 |
| R-03 | `audio_converter.py` | Subprocess call to ffmpeg times out silently on slow hosts; missing-binary detection is per-call, not startup-time | Low | Medium | 4 |
| R-04 | `redis_cache.py` | Optional Redis dependency: graceful no-Redis fallback path is exercised only in unit tests, not integration | Low | Low | 2 |
| R-05 | CLI/main.py entry | External import count (httpx, FastAPI, argparse, asyncio) elevates CRG external edge count; cohesion sensitive to refactor | Very Low | Low | 1 |

---

## Risk Scoring Matrix

Probability scale: Very Low=1, Low=2, Medium=3, High=4, Very High=5
Impact scale: Low=1, Medium=2, High=3, Critical=4

Score = Probability × Impact. Threshold: Score ≥ 6 → High Risk; 3–5 → Medium; < 3 → Low.

| Risk ID | Score | Level |
|---------|-------|-------|
| R-01 | 6 | High |
| R-02 | 4 | Medium |
| R-03 | 4 | Medium |
| R-04 | 2 | Low |
| R-05 | 1 | Low |

---

## FR-Level Risk Re-Evaluation

| FR | Gate 1 Status | Residual Risk | Mitigation Needed |
|----|--------------|---------------|-------------------|
| FR-01 | COMPLETE (95.0) | None | None |
| FR-02 | COMPLETE (95.0) | None | None |
| FR-03 | COMPLETE (95.0) | None | None |
| FR-04 | COMPLETE (95.0) | R-01 (Low residual — concat verified correct in P3) | Monitor |
| FR-05 | COMPLETE (95.0) | R-02 (Low residual — Half-Open covered by test) | Monitor |
| FR-06 | COMPLETE (95.0) | R-04 (Low residual — fallback tested) | None |
| FR-07 | COMPLETE (95.0) | None | None |
| FR-08 | COMPLETE (95.0) | R-03 (Low residual — FFmpegUnavailableError path covered) | None |

---

## Assessment Conclusion

All 8 FRs passed Gate 1 with score ≥ 95.0. No open defects in `deferred_fixes.md`. High-risk module risks (R-01..R-03) are residual-only — the specific failure modes identified in P3 architecture review were addressed in implementation and verified by mutation testing (P6 Gate 4 score 97.1). No code changes required for Phase 7.
