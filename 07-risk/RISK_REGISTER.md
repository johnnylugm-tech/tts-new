# RISK_REGISTER.md — Phase 7 Risk Register

**Project**: tts-new (Kokoro Taiwan TTS Proxy)
**Phase**: 7 — Risk Management
**Date**: 2026-06-08
**Status**: COMPLETE

---

## Active Risks

| Risk ID | Description | Probability | Impact | Score | Owner | Status |
|---------|-------------|-------------|--------|-------|-------|--------|
| R-01 | Parallel httpx dispatch race on MP3 concat (`synthesis.py`) | Low | High | 6 | Dev | Mitigated |
| R-02 | Per-worker independent circuit breaker state (`circuit_breaker.py`) | Low | Medium | 4 | Dev | Accepted |
| R-03 | ffmpeg subprocess timeout / missing-binary per-call (`audio_converter.py`) | Low | Medium | 4 | Dev | Mitigated |
| R-04 | Redis optional dependency fallback not integration-tested | Low | Low | 2 | Dev | Accepted |
| R-05 | CRG cohesion sensitivity to entry-point refactors | Very Low | Low | 1 | Dev | Accepted |

---

## Mitigation Plans

### R-01: Parallel MP3 Concat Race Condition
**Mitigation**: P3 implementation uses ordered asyncio gather with deterministic chunk indexing. Byte-level concat verified correct in FR-04 mutation tests. No re-encoding risk (raw byte concat, not transcoding).
**Status**: Mitigated — residual risk = Negligible.

### R-02: Per-Worker Circuit Breaker State
**Mitigation**: Architecture decision (P2-DD-6) accepted per-worker state as scope limitation for control-group. Half-Open probe correctness verified by FR-05 tests.
**Status**: Accepted — no further action required given single-worker test scope.

### R-03: ffmpeg Timeout and Missing Binary
**Mitigation**: P2-DD-4 mandated per-call ffmpeg check with `FFmpegUnavailableError → HTTP 500`. Subprocess timeout is bounded via Python `subprocess.run(timeout=...)`. FR-08 mutation tests cover both paths.
**Status**: Mitigated — residual risk = Low.

### R-04: Redis Fallback Not Integration-Tested
**Mitigation**: Unit tests mock Redis absence and verify graceful passthrough. Integration environment (Kokoro Docker) does not provide Redis — by design, cache is optional.
**Status**: Accepted — unit test coverage sufficient for optional dependency.

### R-05: CRG Cohesion Sensitivity
**Mitigation**: CRG hub-and-spoke design validated in P3. Entry points (cli.py, main.py) reside in `src/api/` with hub (`utils.py`) compensating external edges.
**Status**: Accepted — CRG score locked in P6 Gate 4 (97.1).

---

## Closed Risks

No risks were closed during Phase 7 — all risks identified were either mitigated in prior phases or accepted as residual.

---

## Risk Register Summary

| Level | Count | Action |
|-------|-------|--------|
| High | 1 | Mitigated (R-01) |
| Medium | 2 | 1 Mitigated (R-03), 1 Accepted (R-02) |
| Low | 2 | Accepted (R-04, R-05) |
| **Total** | **5** | All addressed |
