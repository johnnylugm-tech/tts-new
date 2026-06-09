# Deferred Gaps — Spec Compliance (P8 post-completion audit)

> Generated: 2026-06-09 during the SPEC.md §6 compliance audit.
> Owner: Johnny | Source: spec-gap-fixes branch audit
> Updated: 2026-06-09 — all 6 gaps closed.

## Status Summary (all closed)

| Gap | Severity | Status | Notes |
|-----|----------|--------|-------|
| Gap 1: GET /health, /ready | [中] | ✅ FIXED | `infrastructure/health.py` |
| Gap 2: GET /v1/proxy/voices | [中] | ✅ FIXED | `api/speech_router.py` |
| Gap 3: Retry-After on 503 | [中] | ✅ FIXED | `CircuitOpenResponseMiddleware` in `api/main.py` |
| Gap 4: KOKORO_BACKEND_URL semantic | [中] | ✅ FIXED | `api/cli.py` — guards against double suffix |
| Gap 5: NFR-04 observability metric | [低] | ✅ FIXED | `infrastructure/metrics.py` + GET /metrics |
| Gap 6: R2 retry handler | [低] | ✅ FIXED | `HTTPX_MAX_RETRIES=3` in synthesis.py + cli.py |

## Gap 4 — KOKORO_BACKEND_URL semantic (FIXED)

**Fix:** `src/api/cli.py::_synthesize_text` now checks if
`backend_url` already ends with `/v1/audio/speech`. If yes, use as-is;
if no, append the path. This satisfies BOTH contracts:

- `test_fr07 pattern5` (`--backend http://localhost:8880`, no path) →
  CLI appends → POST to `http://localhost:8880/v1/audio/speech` ✓
- No-arg CLI (uses `KOKORO_BACKEND_URL` = full path per SPEC L123) →
  CLI does NOT re-append → POST to `http://localhost:8880/v1/audio/speech` ✓

New test: `test_gap_cli_does_not_double_suffix_when_full_path_url` (in
`tests/test_spec_gap_fixes.py`) verifies the full-path case.

## Gap 5 — NFR-04 observability metric (FIXED)

**Fix:** added `src/infrastructure/metrics.py` (in-process counters)
+ `GET /metrics` endpoint (in `infrastructure/health.py`)
+ `MetricsMiddleware` (in `api/main.py`).

Counters exposed:
- `uptime_seconds`
- `total_requests`
- `successful_requests`
- `failed_requests`
- `availability` (= `successful / total`, or 1.0 when no requests yet)

Tests:
- `test_gap_metrics_endpoint_returns_200`
- `test_gap_metrics_counts_requests_and_availability`
- `test_gap_metrics_availability_1_when_no_failures`

## Gap 6 — R2 retry handler (FIXED)

**Fix:** added `HTTPX_MAX_RETRIES=3` config in `infrastructure/config.py`
and configured `httpx.AsyncHTTPTransport(retries=HTTPX_MAX_RETRIES)` in
both `src/engines/synthesis.py::synthesize_chunks` and
`src/api/cli.py::_synthesize_text`.

httpx's transport retries on `ConnectError` / `ReadError` / `WriteError`
only; HTTP 4xx/5xx still fail-fast (no point retrying server-confirmed
errors).

Tests:
- `test_gap_synthesis_uses_httpx_transport_with_retries`
- `test_gap_synthesis_retries_on_transient_connection_error`
- `test_gap_cli_uses_httpx_transport_with_retries`
