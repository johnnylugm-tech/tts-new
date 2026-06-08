# RISK_MITIGATION_PLANS.md — Phase 7 Formal Mitigation Plans

**Project**: tts-new (Kokoro Taiwan TTS Proxy)
**Phase**: 7 — Risk Management
**Date**: 2026-06-08
**Status**: COMPLETE

---

## Scope

Formal mitigation plans are required for HIGH risks only (Likelihood × Impact ≥ 9).

Per `RISK_REGISTER.md`: No risks in the current register have Score ≥ 9.

| Risk ID | Score | Level | Formal Plan Required? |
|---------|-------|-------|-----------------------|
| R-01 | 6 | Medium | No (score < 9) |
| R-02 | 4 | Medium | No (score < 9) |
| R-03 | 4 | Medium | No (score < 9) |
| R-04 | 2 | Low | No (score < 9) |
| R-05 | 1 | Low | No (score < 9) |

**Conclusion**: No formal mitigation plans required for Phase 7.

---

## Medium-Risk Mitigations (Informational)

These risks were addressed during P3–P6 implementation and are documented here for traceability. They do not require formal plan tracking.

### R-01: Parallel MP3 Concat Race Condition (Score: 6)

**Risk**: Parallel httpx dispatch to Kokoro backend across multiple synthesis chunks could produce out-of-order byte concatenation under high concurrency, resulting in corrupted MP3 output.

**Mitigation implemented in P3**:
- `synthesis.py` uses `asyncio.gather(*tasks)` with results collected in submission order (not completion order).
- Chunk indices are derived from request position — deterministic regardless of backend response latency.
- Raw byte concat (no re-encoding): ordering error in concat would produce playback artifacts, not silent corruption.
- FR-04 tests verify multi-chunk output has correct byte structure.
- FR-04 mutation tests (P6 Gate 4) confirm concat path is exercised by killed mutants.

**Residual risk**: Negligible — mitigated by design and verified by mutation testing.
**Owner**: Dev team
**Review date**: N/A (resolved, no further action)

---

### R-03: ffmpeg Subprocess Timeout / Missing Binary (Score: 4)

**Risk**: `audio_converter.py` calls `ffmpeg` as a subprocess. If ffmpeg is not installed (new deployment) or hangs on slow host, the per-call detection may surface as an unhandled exception.

**Mitigation implemented in P3 per P2-DD-4**:
- Per-call `shutil.which("ffmpeg")` check before any subprocess invocation.
- `FFmpegUnavailableError` raised → FastAPI exception handler maps to HTTP 500 with structured error body.
- `subprocess.run(timeout=30)` bounds execution; `subprocess.TimeoutExpired` caught and re-raised as HTTP 500.
- FR-08 tests cover both `ffmpeg-missing` and `timeout` code paths.
- FR-08 mutation tests confirm error-path branches are kill-verified.

**Residual risk**: Low — binary detection is per-call (not cached at startup), which is the intended behavior per P2-DD-4 waiver.
**Owner**: Dev team
**Review date**: N/A (resolved, no further action)

---

## No HIGH Risks — Register Closed

All risks identified from CLAUDE.md architecture constraints, Gate 3/4 reviews, and `deferred_fixes.md` have been resolved or accepted at Medium/Low level. No formal HIGH-risk mitigation plans are required or pending.
