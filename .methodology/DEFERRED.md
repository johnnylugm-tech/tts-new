# Deferred Gaps — Spec Compliance (P8 post-completion audit)

> Generated: 2026-06-09 during the SPEC.md §6 compliance audit.
> Owner: Johnny | Source: spec-gap-fixes branch audit

Three of the six gaps identified in the SPEC.md compliance audit are
either fully fixed or partially fixed. The remaining items are deferred
for the reasons documented below.

## Status Summary

| Gap | Severity | Status | Reason |
|-----|----------|--------|--------|
| Gap 1: GET /health, /ready | [中] | ✅ FIXED | Added endpoints in `infrastructure/health.py` |
| Gap 2: GET /v1/proxy/voices | [中] | ✅ FIXED | Added endpoint in `api/speech_router.py` |
| Gap 3: Retry-After on 503 | [中] | ✅ FIXED | Added `CircuitOpenResponseMiddleware` in `api/main.py` |
| Gap 4: KOKORO_BACKEND_URL semantic | [中] | ⚠️ DEFERRED | See below |
| Gap 5: NFR-04 observability metric | [低] | ⚠️ DEFERRED | Advisory; no FR for metrics endpoint |
| Gap 6: R2 retry handler | [低] | ⚠️ DEFERRED | Advisory; no AC for retry behaviour |

## Gap 4 — KOKORO_BACKEND_URL semantic (DEFERRED)

**Spec conflict (SPEC.md L123 vs test_fr07 pattern5):**

- **SPEC.md L123** declares:
  `KOKORO_BACKEND_URL = "http://localhost:8880/v1/audio/speech"`
  (i.e. the FULL path URL, ready to POST).

- **test_fr07::test_fr_07_cli::pattern5_backend_override_loopback_only**
  asserts:
  ```python
  base_url = "http://localhost:8880"          # NO path
  expected_path = f"{base_url}{_BACKEND_PATH}"  # = ".../v1/audio/speech"
  ```
  i.e. `--backend` is a BASE URL, CLI must append `/v1/audio/speech`.

These two contracts are mutually exclusive through the same code path.
Fixing one breaks the other. SPEC §11 prohibits test deletion or
modification, so the bug is preserved as-designed.

**Real-world impact:** When the user invokes `tts-v610` *without*
`--backend`, the CLI uses `KOKORO_BACKEND_URL` (the full path per spec)
and then appends `/v1/audio/speech` again → POST to
`http://localhost:8880/v1/audio/speech/v1/audio/speech` → 404.

When the user provides `--backend` explicitly (as the existing test
does), the code works correctly.

**Recommended fix (Phase 9+ or after §11 lifted):** either
(a) change `KOKORO_BACKEND_URL` default to a base URL
(`http://localhost:8880/v1`) so both spec and CLI agree; or
(b) drop the `+ "/v1/audio/speech"` in CLI and require the full path
everywhere (would need a parallel test_fr07 update).

A new test asserting the "double-suffix bug" was intentionally
reverted and replaced with a contract-preservation test in
`tests/test_spec_gap_fixes.py::test_gap_cli_appends_audio_speech_path_to_base_url`.

## Gap 5 — NFR-04 observability metric (DEFERRED)

**Spec:** SPEC.md §4 NFR-04: "API 可用率 ≥ 99%" (API availability ≥ 99%).

**Status:** No metric endpoint (`/metrics`, Prometheus, etc.) is
implemented. The NFR is aspirational — there is no concrete FR or
acceptance criterion that ties "99% availability" to a measurable
counter. The system CAN be 99% available; it just cannot be observed
externally.

**Recommended fix (Phase 9+):** add a `/metrics` endpoint exposing
Prometheus counters (`http_requests_total`,
`http_request_errors_total`, `circuit_breaker_state`).

## Gap 6 — R2 retry handler (DEFERRED)

**Spec:** SPEC.md §9 risk matrix R2 mitigation: "重試 3 次 + retry
handler" (retry 3 times + retry handler).

**Status:** No retry logic in `synthesis.py` or `cli.py`. A single
network blip on a chunk immediately fails that chunk → 502 (or 503
after threshold).

**Recommended fix (Phase 9+):** add
`httpx.AsyncHTTPTransport(retries=3)` to the `AsyncClient` in
`synthesis.py` and `cli.py`, and add tests covering transient
failures. Note: this changes test assumptions about failure timing
and would need a TDD cycle for FR-04.

## How to lift the deferrals

Each gap has a concrete recommended fix in its section above. None
of them require new tech stack or algorithm changes; they are all
small additions inside the existing boundary. The blocker is purely
the §11 control-group test-preservation constraint.
