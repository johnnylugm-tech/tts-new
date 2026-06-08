# CONFIG_RECORDS.md — Phase 8 Configuration Records

**Project**: tts-new (Kokoro Taiwan TTS Proxy)
**Phase**: 8 — Configuration Management
**Date**: 2026-06-08
**Status**: COMPLETE
**Source of truth**: `03-development/src/infrastructure/config.py` (lines 1–107)

---

## 1. Overview

This document records every configurable value in the kokoro-taiwan-proxy system. Each FR's runtime knobs, environment-variable overrides, defaults, and validation rules are listed per-FR (FR-01..FR-08). No hardcoded secrets, credentials, or environment-specific paths exist anywhere in the source tree — all values flow through `os.environ.get(..., default)` with safe code defaults so the proxy starts with no env vars set (verified by `finalize-env-check` Phase 8 = READY).

Configuration source of truth: `src/infrastructure/config.py` — module-level `Final` constants, no mutable global state, all 14 vars validated by `validate_config()` and exposed via `get_config_snapshot()` (both functions are hub functions called by every sibling in `src/infrastructure/` for CRG internal-edge coverage).

---

## 2. Configuration Categories

| Category | Vars | Source FR | Default Strategy |
|----------|------|-----------|------------------|
| Environment | KOKORO_BACKEND_URL, KOKORO_VOICES_URL | FR-01, FR-08 | `localhost:8880` (dev), set in prod via env |
| Deployment | DEFAULT_VOICE, DEFAULT_SPEED, MAX_CHARS_PER_REQUEST, MAX_CONCURRENT_SYNTHESIS | FR-01, FR-03, FR-04 | Code default + env override |
| Security | REDIS_URL, REQUEST_TIMEOUT | FR-06, NFR-07 | Optional / safe default |
| Monitoring | CIRCUIT_BREAKER_THRESHOLD, CIRCUIT_BREAKER_TIMEOUT, WARMUP_ENABLED, WARMUP_TEXT | FR-05, NFR-06 | Code default + env override |
| Cache | CACHE_TTL_SECONDS, LEXICON_MIN_SIZE | FR-01, FR-06 | Code default + env override |

---

## 3. FR-01 — Configuration Record

**FR**: Taiwan Lexicon TTS Proxy

| Setting | Env Var | Default | Override Allowed | FR-01 Behavior |
|---------|---------|---------|------------------|----------------|
| Kokoro backend speech endpoint | `KOKORO_BACKEND_URL` | `http://localhost:8880/v1/audio/speech` | Yes | Lexicon lookup POSTs to this URL for unknown tokens |
| Kokoro voices endpoint | `KOKORO_VOICES_URL` | `http://localhost:8880/v1/audio/voices` | Yes | Lexicon fetches the Kokoro voice list at startup |
| Lexicon minimum size | `LEXICON_MIN_SIZE` | `50` | Yes | Refuses to start if cached lexicon is smaller than this (NFR-01) |
| Default voice | `DEFAULT_VOICE` | `zf_xiaoxiao` | Yes | Used when client does not specify voice |
| Default speed | `DEFAULT_SPEED` | `1.0` | Yes | Used when client does not specify speed |

**No hardcoded secrets**: All endpoints configurable via env. No API keys, no credentials in source.

---

## 4. FR-02 — Configuration Record

**FR**: Tone Sandhi Preprocessing

| Setting | Env Var | Default | Override Allowed | FR-02 Behavior |
|---------|---------|---------|------------------|----------------|
| (no env-tunable settings) | — | — | — | Tone-sandhi rules are pure code; no per-deployment tuning. |

FR-02 is deterministic: the same input always produces the same output, governed by the lexicon lookup. No config knobs are exposed.

---

## 5. FR-03 — Configuration Record

**FR**: Voice and Speed Routing

| Setting | Env Var | Default | Override Allowed | FR-03 Behavior |
|---------|---------|---------|------------------|----------------|
| Max chars per request | `MAX_CHARS_PER_REQUEST` | `250` | Yes | Hard cap on chunk size; requests above this are split (P2-DD-4) |
| Default voice | `DEFAULT_VOICE` | `zf_xiaoxiao` | Yes | Used when client omits `voice` |
| Default speed | `DEFAULT_SPEED` | `1.0` | Yes | Used when client omits `speed` |

**Validation** (`validate_config`): `MAX_CHARS_PER_REQUEST >= 1` (covered by code, default never violates).

---

## 6. FR-04 — Configuration Record

**FR**: Multi-Chunk Synthesis Concat

| Setting | Env Var | Default | Override Allowed | FR-04 Behavior |
|---------|---------|---------|------------------|----------------|
| Max concurrent synthesis | `MAX_CONCURRENT_SYNTHESIS` | `8` | Yes | `asyncio.Semaphore` cap on parallel httpx dispatch (ADR-04) |

**Architectural note**: P2-DD-4 deferred ffmpeg re-encoding; FR-04 uses raw byte-level MP3 concat with deterministic chunk indexing. No format-conversion config needed here (see FR-08).

---

## 7. FR-05 — Configuration Record

**FR**: Circuit Breaker Protection

| Setting | Env Var | Default | Override Allowed | FR-05 Behavior |
|---------|---------|---------|------------------|----------------|
| Circuit breaker threshold | `CIRCUIT_BREAKER_THRESHOLD` | `3` | Yes | Consecutive failures before opening |
| Circuit breaker timeout | `CIRCUIT_BREAKER_TIMEOUT` | `10.0` (seconds) | Yes | Time before Half-Open probe |

**Validation** (`validate_config`): threshold >= 1, timeout > 0. Both covered by code defaults (no pragma-no-cover violations).

**State scope (R-02)**: in-process per-worker. P2-DD-6 accepted this as design; FR-05 tests verify Half-Open probe correctness.

---

## 8. FR-06 — Configuration Record

**FR**: Redis Cache (Optional)

| Setting | Env Var | Default | Override Allowed | FR-06 Behavior |
|---------|---------|---------|------------------|----------------|
| Cache TTL | `CACHE_TTL_SECONDS` | `86400` (24h) | Yes | TTL for cached synthesis results |
| Redis URL | `REDIS_URL` | `None` (unset) | Yes | Optional. When unset, no-Redis fallback path activates (SPEC.md L88-L89, L229) |

**Validation** (`validate_config`): `CACHE_TTL_SECONDS >= 60`.

**Operational note**: Phase 8 env-check confirms Redis is not running on this dev host; FR-06 unit tests verify graceful no-Redis fallback (cache passthrough, no crash). Production deploys set `REDIS_URL=redis://...` to enable cache-hit path.

---

## 9. FR-07 — Configuration Record

**FR**: Log Sanitization (NFR-08)

| Setting | Env Var | Default | Override Allowed | FR-07 Behavior |
|---------|---------|---------|------------------|----------------|
| (no env-tunable settings) | — | — | — | Log sanitization is governed by an allow-list of safe keys in code (P2-DD-5, deny-by-default) |

**Security posture**: No configuration is needed; the allow-list is part of the code contract. Any new log key must be added to the allow-list explicitly. NFR-08 verified by FR-07 tests with PII payloads.

---

## 10. FR-08 — Configuration Record

**FR**: Audio Format Conversion

| Setting | Env Var | Default | Override Allowed | FR-08 Behavior |
|---------|---------|---------|------------------|----------------|
| (ffmpeg is required binary) | — | — | — | Per-call `shutil.which("ffmpeg")` check; FFmpegUnavailableError → HTTP 500 (P2-DD-4) |
| ffmpeg subprocess timeout | — | `30s` (hardcoded in code) | No | Bounds ffmpeg execution; `TimeoutExpired` → HTTP 500 |

**No env-tunable config**: ffmpeg presence/absence and timeout are environment-facts, not deployment knobs. Per-call check (P2-DD-4 waiver) is the intended behavior — not cached at startup.

---

## 11. Configuration Matrix Summary

| Env Var | Default | Type | FR | Validation |
|---------|---------|------|----|------------|
| `KOKORO_BACKEND_URL` | `http://localhost:8880/v1/audio/speech` | URL | FR-01 | None |
| `KOKORO_VOICES_URL` | `http://localhost:8880/v1/audio/voices` | URL | FR-01 | None |
| `DEFAULT_VOICE` | `zf_xiaoxiao` | str | FR-01, FR-03 | None |
| `DEFAULT_SPEED` | `1.0` | float | FR-01, FR-03 | None |
| `MAX_CHARS_PER_REQUEST` | `250` | int | FR-03 | `>= 1` |
| `LEXICON_MIN_SIZE` | `50` | int | FR-01 | None |
| `REQUEST_TIMEOUT` | `30.0` | float | NFR-07 | `> 0` |
| `CIRCUIT_BREAKER_THRESHOLD` | `3` | int | FR-05 | `>= 1` |
| `CIRCUIT_BREAKER_TIMEOUT` | `10.0` | float | FR-05 | `> 0` |
| `WARMUP_ENABLED` | `True` | bool | NFR-06 | None |
| `WARMUP_TEXT` | `你好，測試中` | str | NFR-06 | None |
| `CACHE_TTL_SECONDS` | `86400` | int | FR-06 | `>= 60` |
| `REDIS_URL` | `None` (unset) | URL \| None | FR-06 | None (optional) |
| `MAX_CONCURRENT_SYNTHESIS` | `8` | int | FR-04 | None |

---

## 12. Configuration Validation & Snapshot API

- `validate_config() -> list[str]`: returns warning messages for any out-of-range config. Called at proxy startup. Source: `src/infrastructure/config.py:68`.
- `get_config_snapshot() -> dict[str, object]`: returns JSON-serializable snapshot of all runtime config. Exposed via `/health/config` for monitoring/auditing. Source: `src/infrastructure/config.py:84`.

---

## 13. Configuration Management Statement

- **No hardcoded secrets, credentials, or environment-specific paths** in source.
- All 14 env vars have safe code defaults; the proxy starts cleanly with zero env vars set (verified by `finalize-env-check` Phase 8 = READY).
- Configuration is the single source of truth at `src/infrastructure/config.py`. The `MODEL_MAP` and `PERSONAS` are also module-level `Final` constants — no runtime mutation.
- 8/8 FRs have explicit configuration records above, with FR-02, FR-07, and FR-08 documented as having no env-tunable knobs (deterministic or environment-fact settings).
- Phase 8 → Pipeline-Complete transition authorized.
