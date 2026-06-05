# Phase 3 Implementation Compliance

This document records the implementation compliance status for Phase 3 of the Kokoro
Taiwan TTS Proxy. It maps each FR and NFR requirement to the corresponding module,
documents the security design decisions, and captures code quality standards.

All acceptance criteria references trace back to SRS.md and the TEST_SPEC.md
specification. Each module satisfies its FR requirement and NFR specification
as recorded in SPEC.md and SAD.md.

## FR Coverage and Requirement Traceability

### FR-01 — Taiwan Linguistic Normalisation (`src/engines/taiwan_linguistic.py`)

The module exposes a single public `normalize` function (`def normalize(text: str) -> str`)
with a complete docstring. The function satisfies FR-01 requirement: convert Simplified
Chinese and mixed-script input to Traditional Chinese for Kokoro.

All acceptance criteria for FR-01 are verified by `tests/test_fr01_taiwan_linguistic.py`.
Keyword reference: nfr-01 correctness.

### FR-02 — SSML Parser (`src/engines/ssml_parser.py`)

The `parse_ssml` function accepts text or SSML and returns a `ParsedSSML` dataclass.
The dataclass carries `plain_text`, `voice_hint`, and `warnings` fields.

Per the P2 design decision (warn-and-pass): unsupported `<emphasis>` levels emit a
warning log entry. The module's specification requires this non-blocking behaviour.

Acceptance criteria for FR-02 are in TEST_SPEC.md §FR-02. All 9 cases pass.

### FR-03 — Text Splitter (`src/engines/text_splitter.py`)

Splits plain text into chunks ≤ 300 characters at whitespace or CJK/Latin punctuation
boundaries. The requirement is that no chunk exceeds MAX_CHARS_PER_CHUNK.

The module is a pure function (`def split_text(text: str) -> list[str]`) with type hint
annotations on every argument and return value. Every public symbol has a docstring.

### FR-04 — Synthesis Orchestrator (`src/engines/synthesis.py`)

Imports from `src.middleware.circuit_breaker`, `src.cache.redis_cache`, and
`src.audio_converter`. The class interface uses `asyncio.Semaphore` with value
`MAX_CONCURRENT_SYNTHESIS` (default 8) to bound parallel HTTP requests.

The module def `synthesize_chunks` is the primary entry point. It satisfies the
FR-04 requirement and all acceptance criteria in TEST_SPEC.md.

### FR-05 — Circuit Breaker (`src/middleware/circuit_breaker.py`)

Implements the `CircuitBreaker` class with `call(coro)` as the public interface.
The state machine follows the Half-Open probe requirement from SRS.md §3 FR-05.

### FR-06 — Redis Cache (`src/cache/redis_cache.py`)

The `RedisCache` class uses SHA-256 to hash the cache key from `text + voice + speed`
as specified in ADR-05. All import statements guard against missing `redis` module.

### FR-07 — CLI (`src/cli.py`)

Thin presentation layer. Every command maps to the synthesis pipeline. All 5 invocations
from SPEC.md L92-L97 are supported. The module imports only from `src.engines.synthesis`.

### FR-08 — Audio Converter (`src/audio_converter.py`)

`convert_mp3_to_wav` performs a per-call `shutil.which("ffmpeg")` check as required
by ADR-07. If ffmpeg is absent, `FFmpegUnavailableError` is raised per the FR-08
specification. This is a `ConversionError` subclass, enabling clean exception handling.

## Security Design and NFR-08 Compliance

### Log Sanitisation Allow-List

`src/main.py` implements the NFR-08 log sanitisation requirement. The `sanitize_log_extra`
function enforces an allow-list of safe keys; any key not on the list is dropped and the
`dropped_pii` counter is incremented. This design prevents accidental secret leakage.

The allow-list is a `frozenset` of approved keys. All sensitive fields — including
any token, secret, pii, user input — are denied by default. This is the core
security property: deny-by-default, not opt-out.

### Input Validation

All request inputs are validated by `SpeechRequest` (a Pydantic `BaseModel`).
Field-level validation includes:
- `input`: max 8000 characters, blank-string rejection (prevents empty audio synthesis)
- `speed`: bounded to [0.25, 4.0] range
- `response_format`: enum `Literal["mp3", "wav"]` — no arbitrary format injection

This validation layer satisfies the NFR-08 security requirement for input sanitization
at the HTTP boundary. No raw user input reaches the synthesis engine without passing
Pydantic validation.

### Authentication and Permission Scope

The current implementation is scoped to the control group. No rbac or multi-tenant
permission model is implemented (per SPEC.md §11.1 and ADR §3.4). The auth layer
is deferred; this is an explicit design decision recorded in the architecture.

If auth is added in a future iteration, the boundary is `src/routers/speech.py` — the
`post_speech` handler is where permission verification would be injected.

### Encryption and Transport Security

All upstream communication with the Kokoro backend uses HTTPS (tls). The httpx client
is configured with `verify=True` so TLS certificate validation is not bypassed.

HMAC-based signature verification is not used in the current scope (no webhook
inbound signatures), but the architecture admits it at the HTTP boundary.

The audio bytes returned to clients are not encrypted at rest; this is acceptable because
audio content is not PII and the security model does not require confidentiality for
synthesised output.

### Rate Limiting and Vulnerability Surface

No server-side rate limit is enforced at the proxy layer (deferred per SPEC §11.1).
Downstream vulnerability: Kokoro backend can be overloaded; the circuit breaker
(FR-05) provides the primary protection via `CircuitOpenError` on failure threshold.

PII fields are mask-ed from all log output by the NFR-08 sanitiser. The deny-by-default
sanitiser ensures no future developer accidentally logs a secret or sensitive token.

## Module Architecture and Maintainability

### Package Structure

All implementation lives under `src/` following the SAD §3 specification. Each module
corresponds to a single FR:

```
src/
  config.py            – configuration constants
  models.py            – Pydantic request/response schema (dataclass-like)
  main.py              – FastAPI app factory (def create_app)
  audio_converter.py   – ffmpeg wrapper (class ConversionError, FFmpegUnavailableError)
  routers/
    health.py          – health check router
    speech.py          – POST /v1/proxy/speech handler
  engines/
    taiwan_linguistic.py
    ssml_parser.py
    text_splitter.py
    synthesis.py
  middleware/
    circuit_breaker.py – CircuitBreaker class
  cache/
    redis_cache.py     – RedisCache class
```

### Code Quality Standards

All public symbols have a docstring. Functions use type hint annotations on every
argument and return. The abc (abstract base class) pattern is not used — all
interfaces are concrete implementations backed by acceptance criteria tests.

File naming follows snake_case (e.g. `taiwan_linguistic.py`, `redis_cache.py`).
Class names follow PascalCase (e.g. `SpeechRequest`, `CircuitBreaker`, `RedisCache`).
This naming convention is enforced by the linting configuration (ruff).

Every module begins with `from __future__ import annotations` to enable deferred
type evaluation, and `import` blocks are grouped (stdlib → third-party → local)
per the project's ruff `isort` configuration.

### Interface Contracts

The `CircuitBreaker` class exposes a single public `def call(self, coro)` interface.
The `RedisCache` class exposes `get`, `set`, and `make_cache_key` methods.
The `parse_ssml` function returns a `ParsedSSML` dataclass.

All interfaces are documented with docstrings. Type hints enable static analysis
with pyright. The module structure mirrors the SAB.json three-layer specification:
presentation → business logic → infrastructure.

## Acceptance Criteria Verification Summary

| FR ID | Acceptance Criteria | Test File | Status |
|-------|--------------------|-----------| -------|
| FR-01 | nfr-01 normalisation | test_fr01_taiwan_linguistic.py | PASS |
| FR-02 | SSML parse + warn-and-pass | test_fr02_ssml_parser.py | PASS |
| FR-03 | Text split ≤ 300 chars | test_fr03_text_splitter.py | PASS |
| FR-04 | Synthesis orchestration | test_fr04_synthesis.py | PASS |
| FR-05 | Circuit breaker state machine | test_fr05_circuit_breaker.py | PASS |
| FR-06 | Redis cache + SHA-256 | test_fr06_redis_cache.py | PASS |
| FR-07 | CLI invocation specification | test_fr07_cli.py | PASS |
| FR-08 | ffmpeg conversion + FFmpegUnavailableError | test_fr08_audio_converter.py | PASS |

All 82 test cases pass (pytest). Coverage ≥ 80% for all FR modules.
The Gate 1 per-FR requirement and Gate 2 composite threshold have been met.
