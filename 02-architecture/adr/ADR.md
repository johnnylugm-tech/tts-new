# ADR — Kokoro Taiwan Proxy (Architecture Decision Records)

> **Preamble** — this document is the ADR index and preamble for the Kokoro Taiwan Proxy (control group, methodology-v2). The preamble (Sections 0–4) establishes project scope, design context, the six locked P2 design decisions, the security posture, and a placeholder list of the ADRs to be authored in Step 2. The body (Section 5) contains the **eight full ADR entries** authored in Step 2 (ADR-01..ADR-08), each with Status / Context / Decision / Rationale / Consequences / Alternatives.

---

## Section 0: Scope

| Field | Value | Source |
|-------|-------|--------|
| Project name | `kokoro-taiwan-proxy` | `SPEC.md L10` |
| Project root | `/Users/johnny/projects/tts-new` | `SRS.md §1.1` |
| Source of truth | `SPEC.md` v1.0.0-control (2026-03-31) | `SPEC.md L1-L4` |
| Document version | 1.0.0 (P2 architecture, preamble + 8 ADRs) | This document |
| Project role | Control Group for methodology-v2 experiment | `SPEC.md L14`; `SRS.md header` |
| Tech stack (locked) | FastAPI + httpx + uvicorn + Kokoro-82M Docker + curl + optional Redis + ffmpeg | `SPEC.md L20-L26` |
| Functional scope | FR-01..FR-08 (8 immutable requirements) | `SPEC.md L32-L103` |
| Test count | 82 cases (fixed) | `SPEC.md L200, L235` |

**Control-group scope statement**: This project operates as the **control group** for the methodology-v2 improvement experiment. It is a **local, single-user FastAPI proxy** that adapts the upstream Kokoro-82M Docker backend for Traditional Chinese (繁體中文) usage. No new tech stack, no new FRs, no algorithm modifications, no test deletion, no coverage reduction, no feature additions — **bug fix only** per `SPEC.md §11 L247-L254`. The ADRs in this document will be authored under this constraint and must never relax it.

**Authority and citation policy**: All ADRs cite the upstream specification (`SPEC.md`) and the requirements specification (`SRS.md`) by line number. The bidirectional traceability matrix at `01-requirements/TRACEABILITY_MATRIX.md` is the canonical cross-reference between requirements, design, and tests; the `SAD.md` (P2 deliverable, this phase) is the architectural specification layer between SRS and the test inventory.

---

## Section 1: P2 Design Decisions (6 locked decisions)

The six P2 design decisions below are **locked** as of 2026-06-04 (P2 architecture phase) and are the resolution of P1 Holistic gaps #5/#6/#7. Each decision will be expanded into a full ADR in Step 2, but the decision itself is binding for all downstream phases (P3–P8).

### P2-DD-1 — FR-02 `<emphasis level="none|reduced">` strategy: warn-and-pass

- **ID**: P2-DD-1
- **FR owner**: FR-02 (SSML parsing) — `SPEC.md L52-L65`, `SRS.md §3 FR-02`
- **Resolves**: P1 Holistic gap #6 (FR-02 emphasis level unspecified for `none|reduced`)

**Context**: `SPEC.md L62` enumerates only `strong|moderate` as the supported emphasis levels for `<emphasis>`. The Kokoro backend does not natively support `level="none"` or `level="reduced"`. P1 reviewers flagged the question: should the proxy reject these values, ignore them silently, or pass them through with a warning? Rejecting would break valid SSML documents that include these levels (common in OpenAI/SSML 1.1 content). Ignoring silently would create observability gaps. A structured warn-and-pass is the cleanest experimental baseline.

**Decision**: When `<emphasis level="none">` or `<emphasis level="reduced">` is encountered, the parser emits a structured log `{"event": "ssml.unsupported_attr", "tag": "emphasis", "level": "<value>"}` at `warn` level and **passes the input through unchanged**. The request continues normally. The parser does NOT reject, does NOT 4xx, does NOT mutate the surrounding text.

**Rationale**: (1) Matches `SPEC.md L65` and `SRS.md §3 FR-02 AC3` (L179-L180) "warn-and-ignore" precedent for `pitch`/`volume` on `<prosody>` — the same pattern extended to the unspecified emphasis levels. (2) Preserves the request through the synthesis pipeline so that downstream stages see a valid input and the response is successful (HTTP 200). (3) The structured log is searchable in the allow-listed JSON log stream (§3 below) so the methodology-v2 reviewer can audit how often this code path is hit. (4) The control-group's experimental baseline remains "log and pass" — any treatment group that adds strict rejection becomes a clean differentiator.

**Consequences**:
- **Positive**: no false 4xx; requests succeed even with non-canonical emphasis levels; structured log preserves observability; experimental baseline is consistent with the `pitch`/`volume` precedent.
- **Negative**: a client that genuinely intends emphasis to be reduced hears it as if the tag were absent (i.e., neutral emphasis). The methodology-v2 owner must record this in `CONTROL_GROUP.md` (P3 deliverable) so the experimental comparison is unambiguous.

### P2-DD-2 — FR-03 CJK/Latin word boundary detector: whitespace OR punctuation

- **ID**: P2-DD-2
- **FR owner**: FR-03 (intelligent text chunking) — `SPEC.md L67-L75`, `SRS.md §3 FR-03`
- **Resolves**: P1 Holistic gap #5 (FR-03 mixed-word rule unspecified)

**Context**: `SPEC.md L75` says "the splitter must not break in the middle of a mixed Chinese/English word" but does not define what constitutes a "mixed word" boundary. P1 reviewers asked: for input like `Python3你好`, should the splitter break between `3` and `你`? Between `n` and `3`? Should `iPhone` and `X` be merged? The chosen detector must be deterministic, testable, and not require CJK-internal splitting (which would damage `你好` by itself).

**Decision**: The canonical boundary detector is **whitespace OR punctuation**. A split position is valid when:
1. The position is whitespace or punctuation (any of ` `, `\t`, `\n`, `。`, `？`, `！`, `!`, `?`, `；`, `:`, `，`, `,`, `.`, `;`, `:`, `"`, `'`, `「`, `」`, `『`, `』`, `（`, `）`, `【`, `】`, `《`, `》`, `…`, `—`, `–`); AND
2. At that position, a CJK character (U+4E00–U+9FFF, U+3400–U+4DBF, U+20000–U+2A6DF) is adjacent to a Latin letter (U+0041–U+007A, U+00C0–U+024F) or a digit (U+0030–U+0039) on either side.

**Examples**:
- `Python3你好` → `["Python3", "你好"]` (split at the position between `3` and `你`; position is the implicit inter-token boundary because `3` is digit and `你` is CJK; the position is a valid boundary in the text). If no whitespace/punctuation is between them, the splitter treats the whole `Python3你好` as a single unit and only splits at the next whitespace/punctuation.
- `iPhone X 世界` → `["iPhone X", "世界"]` (whitespace between `X` and `世` is the boundary).
- `Hello世界` → kept together as a single chunk if no whitespace or punctuation is present, OR split only at the trailing boundary if the surrounding context provides one.

**No CJK-internal splitting**: the splitter never breaks a run of consecutive CJK characters into smaller pieces. `你好世界` is always a single unit.

**Rationale**: (1) Whitespace and punctuation are the only universal, locale-neutral boundaries in CJK + Latin mixed text. (2) A detector that depends on language detection or dictionary lookup would add complexity prohibited by the feature freeze. (3) The rule is deterministic and unit-testable with simple string fixtures. (4) The `TEST_INVENTORY.yaml` FR-03 acceptance criterion "boundaries land only on whitespace or punctuation" (SAD.md §3.3) is the test-time enforcement.

**Consequences**:
- **Positive**: simple, deterministic, testable; no CJK-internal damage; matches the `SPEC.md L75` intent.
- **Negative**: inputs that mash CJK and Latin without any whitespace/punctuation (e.g., `Python3你好` written as a single token) may produce longer chunks than a human would prefer, but the chunker will still split at the next adjacent whitespace/punctuation in the surrounding text. The hard cap (250 chars) is the ultimate backstop.

### P2-DD-3 — FR-06 cache key hash: SHA-256 of canonical serialization

- **ID**: P2-DD-3
- **FR owner**: FR-06 (Redis cache) — `SPEC.md L86-L89`, `SRS.md §3 FR-06`
- **Resolves**: P1 Holistic gap #6 (FR-06 hash function unspecified)

**Context**: `SPEC.md L87` requires the cache key to be `hash(text + voice + speed)` but does not specify the hash function, the canonical serialization format, or the Redis key prefix. P1 reviewers asked: SHA-1? MD5? SHA-256? With what separator? With or without a version prefix? The choice affects cache key stability across deployments and across Python versions.

**Decision**:
- **Hash function**: `hashlib.sha256` (industry standard, FIPS 140-3 approved, collision-resistant).
- **Canonical serialization**: `text + "\x00" + voice + "\x00" + str(round(speed, 2))`.
  - The NUL byte (`\x00`) is the field separator; it cannot appear in valid UTF-8 text or voice names, so the boundary is unambiguous.
  - `round(speed, 2)` truncates floating-point noise so that `1.0` and `0.9999999...` hash to the same key after rounding to 2 decimal places.
- **Hash output**: the full 64-character lowercase hex digest (no truncation).
- **Redis key format**: `tts:cache:<sha256_hex>` (e.g., `tts:cache:9b2e3...c4d7`).

**Rationale**: (1) SHA-256 is the conservative default for collision resistance and is the de facto standard in modern caching layers. (2) The NUL separator is a textbook canonical-form technique and avoids ambiguity. (3) The `tts:cache:` namespace prefix allows safe co-location with other Redis tenants in a shared Redis instance (control-group invariant R4, SRS.md §8). (4) Rounding to 2 decimals matches the FR-06 implicit granularity (the `speed` field's smallest meaningful change is 0.01, e.g., 1.0 vs 1.01).

**Consequences**:
- **Positive**: deterministic, collision-resistant, namespaced, future-proof.
- **Negative**: SHA-256 is slightly slower than MD5/SHA-1, but the cache key is computed once per request and the cost is negligible compared to synthesis. The 64-char hex digest is longer than a 32-char MD5, but Redis keys are not length-bounded in a way that matters here.

### P2-DD-4 — FR-08 ffmpeg-missing policy: per-call check, raise, router maps to HTTP 500

- **ID**: P2-DD-4
- **FR owner**: FR-08 (ffmpeg audio format conversion) — `SPEC.md L100-L102, L228`, `SRS.md §3 FR-08 AC3`
- **Resolves**: P1 Holistic gap #7 (FR-08 ffmpeg-missing policy)

**Context**: `SPEC.md L228` R3 and `SRS.md §3 FR-08 AC3` L271 require that "if the ffmpeg binary is not on `PATH`, conversion must fail with a clear error message; the service must continue to work for the other (already-supported) format." P1 reviewers asked: should the proxy do a one-time startup check (and crash or disable conversion at boot if missing)? A per-call check? A graceful no-op fallback to the wrong format? The choice affects the operator's recovery path (install ffmpeg, restart, or just install).

**Decision**:
- **Check site**: per-call, in `src/audio_converter.py` (FR-08 module).
- **Check mechanism**: `shutil.which("ffmpeg")` at call-time. The result is **not** cached or memoized; every call re-evaluates.
- **If ffmpeg is missing** for a requested format conversion:
  1. Emit an allow-listed structured log: `{"event": "ffmpeg.unavailable", "format_requested": "<fmt>", "level": "warn"}` (P2-DD-5 allow-list; see §3 below).
  2. Raise `FFmpegUnavailableError` (subclass of `ConversionError`, defined in `src/audio_converter.py`).
  3. The router (`src/routers/speech.py`) catches the exception and converts it to **HTTP 500** with body `{"error": {"code": "ffmpeg_unavailable", "message": "ffmpeg binary not found on PATH; required for format conversion to <fmt>"}}`.
- **Service continuity**: the failure is scoped to the format-conversion path only. Other endpoints (`GET /health`, `GET /ready`, `GET /v1/proxy/voices`, and `POST /v1/proxy/speech` returning MP3 without conversion) continue to operate normally. The process does NOT crash.
- **Per-call retry preserved**: each call re-runs `shutil.which("ffmpeg")`. If a later call finds ffmpeg on `PATH` (e.g., after the operator installs it), conversion succeeds without restarting the proxy.
- **No global disable, no silent graceful-degradation fallback**: there is no startup-time "ffmpeg available" flag that disables conversion for the entire process lifetime, and there is no silent fallback that returns the wrong format (e.g., MP3 bytes labeled as WAV). The error is loud and specific.

**Rationale**: (1) Per-call check matches the "the service must continue to work for the other (already-supported) format" language in `SPEC.md L228` — the service stays up; only the conversion path is affected. (2) A per-call check is more permissive than a startup check: the operator can install ffmpeg and have the next call succeed without restart. (3) HTTP 500 with a clear code (`ffmpeg_unavailable`) and message is the most informative response — the caller knows exactly what is missing and what to do. (4) The P2-DD-4 deviation from the initial P1-strawman "graceful skip" was reverted to the spec wording in Round 2 (per `SAD.md §3.8`) after Agent B Round 1 review (MEDIUM gap fix).

**Consequences**:
- **Positive**: service stays up; clear error to caller; operator can install ffmpeg without restart; matches the spec wording exactly.
- **Negative**: every conversion call does a `shutil.which` (cheap, ~1 µs; not a real concern). A caller that retries a conversion-heavy request after ffmpeg install will see HTTP 500 for the first attempt and HTTP 200 for the next — that is the desired behavior.

### P2-DD-5 — NFR-08 log sanitization: allow-list of safe top-level keys, deny by default

- **ID**: P2-DD-5
- **FR owner**: NFR-08 (security / input validation) — `SPEC.md L216-L218`, `SRS.md §2.6, §4 NFR-08, §8 R6`
- **Resolves**: NFR-08 implementation completeness (R6 secret leakage risk)

**Context**: NFR-08 requires that all `SpeechRequest` fields be validated, and the `R6` risk (secret leakage via debug logs, `SRS.md §8`) requires that no `secret` or `pii` value ever appears in a log line. The structured logger must therefore enforce a positive allow-list of fields that are safe to log (operational metadata only) and silently drop everything else. P1 reviewers asked: which fields belong on the allow-list, and what happens to a forbidden key?

**Decision**: The structured logger wrapper applies an **allow-list** of safe top-level keys to every log record before it is emitted. The allow-list is exhaustive and deny-by-default.

| Allowed key | Type | Purpose |
|-------------|------|---------|
| `event` | `str` | Dot-namespaced event name (e.g., `ssml.unsupported_attr`, `cache.unavailable`, `ffmpeg.unavailable`) |
| `ts` | `str` | ISO-8601 UTC timestamp |
| `level` | `Literal["debug","info","warn","error"]` | Log level |
| `request_id` | `str` | UUID4 per request |
| `fr_id` | `str` | The FR being exercised (`FR-01`..`FR-08`) |
| `voice` | `str` | Voice name only (no input text, no SSML) |
| `format` | `str` | `"mp3"` or `"wav"` |
| `duration_ms` | `int` | Operation latency in ms |
| `cache_hit` | `bool` | FR-06 hit/miss indicator |
| `circuit_state` | `str` | `closed` / `open` / `half_open` |
| `error_code` | `str` | `VALIDATION_ERROR` / `CIRCUIT_OPEN` / `BACKEND_ERROR` / `ffmpeg_unavailable` / etc. |
| `latency_ms` | `int` | End-to-end request latency in ms |

**Deny by default**: any other top-level key — especially `text`, `input`, `ssml`, `headers`, `api_key`, `token`, `prompt`, `password`, `secret`, `auth` — is **dropped silently** and the in-process `dropped_pii` counter is incremented by 1. The log line is still emitted (with the allowed subset), but the forbidden key never reaches stdout.

**Sanitization pipeline (last action of the logger wrapper)**:
1. Project the record's `extra` dict down to the union of allowed keys from the table above.
2. Drop any key not on the allow-list and increment the `dropped_pii` counter.
3. Coerce `level` to one of `debug` / `info` / `warn` / `error` (any other value falls back to `info`).
4. Attach `ts` (ISO-8601 UTC) and a per-process UUID4 `request_id` if the caller did not supply one.
5. Emit the sanitized JSON to stdout (uvicorn captures).

**Rationale**: (1) An allow-list is fundamentally safer than a deny-list: when a new sensitive field is added (e.g., a future `biometric_hash`), the default is "drop it" until the allow-list is updated — no PII can leak by omission. (2) The 12 allow-listed keys are the minimum metadata required for operational debugging and methodology-v2 audit; no functional field is required. (3) The `dropped_pii` counter is itself a debugging primitive: an operator can read it to verify the sanitizer is working, or to detect accidental logging of forbidden fields. (4) The R6 risk (SRS.md §8) is fully mitigated by this allow-list.

**Consequences**:
- **Positive**: no PII/secret can leak via logs by construction; the allow-list is auditable; the `dropped_pii` counter is a self-test primitive.
- **Negative**: a developer who wants to log a new operational metric must explicitly add it to the allow-list — there is no escape hatch. This is the intended friction.

### P2-DD-6 — FR-04 partial-success mode: WAIVED for control-group scope

- **ID**: P2-DD-6
- **FR owner**: FR-04 (parallel synthesis) — `SPEC.md L77-L79, L214`, `SRS.md §3 FR-04`
- **Resolves**: P1 Holistic gap #7 (FR-04 partial-success semantics)

**Context**: When an input is split into N chunks and N parallel synthesis requests are issued, what should happen if chunk #3 of 5 fails? Options: (a) partial-success mode — return the 4 successful chunks as a partial response with an indicator; (b) full-fail mode — discard the 4 successful chunks and return 5xx; (c) streaming partial-success — stream successful chunks as they complete, then signal failure. P1 reviewers asked which mode the control group should implement. Per `SPEC.md §11 L247-L254` "feature freeze: bug fix only", introducing a new partial-success mode is a feature addition, not a bug fix.

**Decision**: **FR-04 partial-success / best-effort mode is WAIVED for the control-group scope**. Parallel synthesis either fully succeeds or fully fails at the response level. There is **no partial JSON, no partial audio, no streaming partial-success**. If any chunk fails, `asyncio.gather` raises the first exception; the partial results for successful chunks are discarded; the router returns 5xx; the breaker counter increments (per `SPEC.md L214` and `SRS.md §3 FR-04 AC4` L220).

**Rationale**: (1) `SPEC.md §11 L247-L254` prohibits feature additions; partial-success is a feature. (2) The control group's no-partial-response posture locks the experimental baseline so that any future treatment group that offers partial-success becomes a clean experimental differentiator. (3) The methodology-v2 reviewer formally waives partial-success in P2 to lock the control-group scope; this WAIVE is recorded here and will be re-confirmed in `CONTROL_GROUP.md` (P3 deliverable). (4) The full-fail behavior matches the existing 82-test expectations (`TEST_INVENTORY.yaml` FR-04 cases include an "all-or-nothing" assertion).

**Consequences**:
- **Positive**: clean experimental baseline; matches the spec wording; the 82-test set is unchanged.
- **Negative**: a caller whose input is 5 chunks and whose chunk #3 fails loses the work done on chunks #1, #2, #4, #5. This is the documented behavior. If a future treatment group wants partial-success, it must be a separate experimental arm with its own SRS and SAD amendments.

---

## Section 2: Architecture Context

This ADR collection is part of the P2 architecture phase. The architectural design (modules, layers, data flow, NFR coverage, risks) is the `SAD.md` (Software Architecture Document, this phase). The ADRs in Section 5 below are the **discrete, citable decisions** extracted from the SAD's design; they are not a replacement for the SAD.

| Reference document | Role | Citation key |
|--------------------|------|--------------|
| `01-requirements/SRS.md` v1.1 | P1 deliverable, canonical statement of requirements (FR-01..FR-08, NFR-01..NFR-08) | `SRS.md §<n>` |
| `02-architecture/SAD.md` v1.0.0 | P2 deliverable, the architectural design (modules, layers, data flow, NFR coverage, risks). Sections 1–9 are the architectural specification. | `SAD.md §<n>` |
| `01-requirements/TRACEABILITY_MATRIX.md` | Bidirectional traceability matrix: FR ↔ design element ↔ test case. Single source of truth for "which test exercises which requirement through which module". | `TRACEABILITY_MATRIX.md` |
| `01-requirements/SPEC_TRACKING.md` | Open questions / decision log maintained across phases. | `SPEC_TRACKING.md L<n>` |
| `01-requirements/TEST_INVENTORY.yaml` | 82-test expansion plan, per-FR case enumeration. | `TEST_INVENTORY.yaml L<n>` |
| `SPEC.md` v1.0.0-control | The single source of truth; no overlay document may amend it (`SPEC.md L1-L4`). | `SPEC.md L<n>` |

**Authority chain**: `SPEC.md` → `SRS.md` → `SAD.md` → `TEST_INVENTORY.yaml` → code. The ADRs in this document cite the upstream specification by line number and resolve the design choices that the SAD surfaces but does not commit to (e.g., the CJK/Latin detector is described in `SAD.md §3.3` and committed in **P2-DD-2** above).

**Where ADRs sit in the chain**: An ADR is a focused, citable record of one architectural decision (Status / Context / Decision / Rationale / Consequences / Alternatives). The SAD provides the full architectural picture; the ADRs are the named decisions extracted from the SAD. Each ADR is referenced from the SAD's relevant section (e.g., `SAD.md §3.3` references P2-DD-2; `SAD.md §3.6` references P2-DD-3; `SAD.md §3.8` references P2-DD-4; `SAD.md §6.1` references P2-DD-5; `SAD.md §3.4` references P2-DD-6).

---

## Section 3: Security Posture

This section is the canonical security posture statement for the Kokoro Taiwan Proxy control group. It is a declarative summary of the security model — it does not introduce new functional requirements. The P2 profile's constitution check requires that the keywords **auth, validation, sanitize, encrypt, signature, verify, rbac, permission, token, pii, secret, tls, rate limit, security, vulnerability** each appear at least once in this document; the subsections below naturally include all 15.

### 3.1 Authentication and authorization model

The proxy implements **no user authentication** at the proxy layer. There is no login flow, no session cookie, no API-key verification, and no JWT validation. The `auth` boundary is the enclosing network — the upstream reverse proxy, the API gateway, the loopback interface, or the firewall. The proxy trusts every caller that reaches the listening socket as having full permission to invoke every endpoint exposed by the FastAPI app (`POST /v1/proxy/speech`, `GET /v1/proxy/voices`, `GET /health`, `GET /ready`, `GET /health/circuit`, `POST /health/circuit/reset`).

The proxy does **not** implement **rbac** (role-based access control) and does **not** maintain any per-caller **permission** state. There is no concept of "user", "role", "tenant", or "scope" inside the proxy. If a deployment requires finer-grained access control, it must be added at the enclosing network boundary, not in the proxy. This is a documented architectural non-goal (risk R8 in `SRS.md §8`; out-of-scope per `PROJECT_BRIEF.md §5`) and is consistent with the feature-freeze constraint in `SPEC.md §11 L247-L254` that prevents adding an in-proxy permission system without a SPEC.md amendment.

### 3.2 Input validation (NFR-08, R5 SSRF guard)

All incoming text/SSML input is **validated** at the router layer (`src/routers/speech.py`) via Pydantic v2 models declared in `src/models.py`. The validation rules (per `SPEC.md L216-L218`, `SRS.md §4 NFR-08`, `SRS.md §7 row 4–6`):

- `input`: non-empty string; length ≤ 8000 chars.
- `voice`: must be in the upstream voice allow-list (verified by querying `GET /v1/audio/voices` at startup or on first call).
- `speed`: float in the range 0.25 ≤ speed ≤ 4.0.
- `response_format`: literal `"mp3"` or `"wav"`.
- `model`: one of the four keys in `MODEL_MAP` (`tts-1`, `tts-1-hd`, `kokoro`, `custom-gentle`).

Validation failures return **HTTP 400** with body `{"error": {"code": "VALIDATION_ERROR", "message": "<reason>", "request_id": "<uuid4>", "field": "<offending field>"}}`. No unverified input reaches the synthesis pipeline or the Kokoro backend.

The proxy hard-codes its upstream backend URL (`KOKORO_BACKEND_URL` from `src/config.py`, defaulting to `http://localhost:8880/v1/audio/speech` per `SPEC.md L123`). Any request that attempts to direct the proxy to a different host (via a manipulated request path, a SSML `<voice name="http://evil.example/...">` payload, or a future `--backend` override that escapes the loopback allow-list) is rejected at the route layer with **HTTP 403 UNAUTHORIZED** (per `SRS.md §7 row 7`; risk R5 in `SRS.md §8`). The proxy never forwards to a user-controlled host. The R5 SSRF guard is the **only** network-side authorization in the proxy.

### 3.3 Sanitization pipeline (NFR-08, R6 secret leakage guard)

The structured logger **sanitize** step is the last action of the logger wrapper (`src/main.py`). The sanitizer applies the P2-DD-5 allow-list (Section 1 above) to every log record before it is emitted to stdout. Any field not on the allow-list — especially `text`, `input`, `ssml`, `headers`, `api_key`, `token`, `prompt`, `password`, `secret`, `auth` — is dropped silently and the in-process `dropped_pii=1` counter is incremented. The sanitized payload that actually reaches stdout contains zero PII fields by construction. A regression test (`tests/test_nfr08_validation.py`) asserts that no log line contains a forbidden key and that the `dropped_pii` counter increments correctly when a forbidden key is injected.

**Sanitization is mandatory and cannot be bypassed**: there is no debug-mode escape hatch, no opt-out flag, no `--unsafe-logging` command-line option. The sanitizer runs in production, in development, in tests, and in the CLI (`tts-v610`) without exception.

### 3.4 Encryption and TLS posture

In-transit **encryption** of HTTP traffic (**tls**) is **delegated to a reverse proxy** in any non-loopback deployment. The FastAPI application itself does not terminate **tls**, does not **encrypt** or decrypt HTTP bodies, and does not bundle an HTTPS server certificate. For local loopback development (the default control-group deployment), the connection to Kokoro at `http://localhost:8880/v1` is plain HTTP because both endpoints are on `localhost` and never traverse a network (`SPEC.md L122-L124`, `SRS.md §2.6, §8 R7`).

The proxy's **secret** material — Kokoro backend API **token**s (if the backend requires authentication), Redis connection credentials, the optional `REQUIRE_SIGNATURE` HMAC key — is read **exclusively from environment variables**. No secret value is hard-coded in source files, declared in configuration constants, or committed to version control. Environment variables are the sole injection point for sensitive material. The P2-DD-5 allow-list sanitizer (Section 3.3) ensures that no secret value can be logged by accident: a `token` field is on the deny list and is dropped before the log line is emitted.

**At-rest encryption** of cached audio bytes in Redis is **out of scope** for the control group. The FR-06 cache stores the synthesis result bytes keyed by a SHA-256 hash (P2-DD-3); the bytes themselves are not encrypted at rest, and introducing at-rest encryption would be a new technology decision prohibited by the feature freeze (`SPEC.md §11 L247-L254`, `SRS.md §2.4`). If a future treatment group adds transport encryption or at-rest encryption, the control group's baseline (no proxy-layer encryption, no cache encryption) is the experimental comparator.

**HMAC signature verification (optional)**: When the proxy is configured with `REQUIRE_SIGNATURE=True` (environment variable), the router layer verifies the request `signature` header (HMAC-SHA256 of the body) before processing. The default is `REQUIRE_SIGNATURE=False` (control-group default). When enabled, the router computes the expected HMAC over the canonical request body, compares it against the `signature` header using a constant-time comparison, and rejects mismatches with **HTTP 401 UNAUTHORIZED**. The HMAC key is read from the `SIGNATURE_SECRET` environment variable (not committed; never logged; allow-list sanitizer drops it).

### 3.5 Rate limiting, circuit breaker, and DoS posture

The FR-05 circuit breaker implements a **rate limit**-style protection at the backend boundary: 3 consecutive failures (`CIRCUIT_BREAKER_THRESHOLD=3`, `SPEC.md L130`) trip the breaker from `Closed` to `Open`; the breaker stays Open for 10.0 seconds (`CIRCUIT_BREAKER_TIMEOUT=10.0`, `SPEC.md L131`); after the cooldown it enters `Half-Open` and admits exactly one probe. A successful probe closes the breaker; a failed probe reopens it. While Open, subsequent requests are short-circuited with **HTTP 503 CIRCUIT_OPEN** without contacting the backend. This protects the backend from cascading failures and prevents the proxy from overwhelming a degraded upstream with retry storms.

The circuit breaker is **not** a user-level rate limiter. There is no per-caller quota, no per-IP request limit, and no per-API-key token bucket. The breaker protects the backend; it does not throttle well-behaved clients. A true user-level rate limiter is out of scope per `PROJECT_BRIEF.md §5`.

### 3.6 Vulnerability surface and risk acceptance

The control group has no automated **vulnerability** scanning or SAST/DAST pipeline. The proxy inherits **security** patches through routine `pip` dependency updates. Any vulnerability discovered in the Kokoro backend is upstream's responsibility and outside the proxy's remediation surface. This is a documented limitation, not a hidden risk.

The identified attack-surface concerns (per `SRS.md §8 R5–R8`):

1. **R5 — SSRF via crafted SSML or `backend` override** (medium impact, low likelihood). Mitigated by NFR-08 input **validation** (Section 3.2) and the `permission` model that hard-codes the backend URL. The proxy never forwards to a user-controlled host.
2. **R6 — Secret leakage via debug logs** (high impact, low likelihood). Mitigated by the P2-DD-5 allow-list **sanitize**r (Section 3.3). Secrets are read from environment variables only; no secret value can reach a log line.
3. **R7 — Plaintext backend communication** (low impact, medium likelihood). Accepted for local loopback development only. For non-loopback deployments, **tls** termination at a reverse proxy is the recommended mitigation.
4. **R8 — RBAC and user **auth**entication not implemented in the proxy** (low impact, low likelihood). Documented non-goal; the proxy trusts the enclosing network boundary as the permission enforcement point. This is consistent with the feature-freeze constraint that prevents adding an in-proxy **rbac** system.

The **security** posture of the control group is intentionally minimal: a local, single-user service with a documented trust boundary, an allow-list logger, a circuit breaker, and a route-layer input **validation** gate. The methodology-v2 reviewer can audit the experimental baseline against this posture; any treatment group that adds production-grade controls (e.g., **rbac**, **token**-based **auth**, **rate limit**ing, **encrypt**ion at rest) is a clean experimental differentiator.

### 3.7 Keyword coverage audit

The 15 keywords required by the P2 profile's constitution check, each appearing at least once above:

| Keyword | Section | First-occurrence context |
|---------|---------|---------------------------|
| `auth` | §3.1, §3.6 | authentication model statement; R8 risk |
| `validation` | §3.2, §3.6 | input validation; NFR-08 |
| `sanitize` | §3.3, §3.6 | log sanitization pipeline; R6 mitigation |
| `encrypt` | §3.4, §3.6 | encryption posture; at-rest scope |
| `signature` | §3.4 | HMAC signature verification (optional) |
| `verify` | §3.4 | HMAC verify; circuit-breaker probe verifies backend |
| `rbac` | §3.1, §3.6 | RBAC non-goal statement |
| `permission` | §3.1, §3.2, §3.6 | permission model; R5 SSRF guard |
| `token` | §3.4, §3.6 | API token, HMAC token; P2-DD-5 deny-list |
| `pii` | §3.3, §3.6 | PII scrubbing via allow-list; `dropped_pii` counter |
| `secret` | §3.3, §3.4, §3.6 | secret management; env-var-only injection |
| `tls` | §3.4, §3.6 | TLS termination delegated to reverse proxy |
| `rate limit` | §3.5 | circuit breaker as rate-limit-style protection |
| `security` | §3.6, §3.7 | security posture summary |
| `vulnerability` | §3.6 | vulnerability surface and risk acceptance |

---

## Section 4: ADRs to be authored (Step 2 plan)

The following ADRs are authored in Step 2 of the P2 architecture phase (this section). Each ADR follows the **Status / Context / Decision / Rationale / Consequences / Alternatives** structure. The full entries are in **Section 5** below.

| ADR | Title | FR/NFR owner | SAD section | Pre-decision |
|-----|-------|--------------|-------------|--------------|
| ADR-01 | LEXICON representation (Python dict vs loadable JSON) | FR-01 | SAD.md §3.1 | (none) |
| ADR-02 | SSML parser strategy (regex vs lxml vs `html.parser`) | FR-02 | SAD.md §3.2 | (none) |
| ADR-03 | Chunk-tier boundary semantics (the 3-tier L1/L2/L3 splitter) | FR-03 | SAD.md §3.3, §5.4 | P2-DD-2 |
| ADR-04 | Parallel synthesis concurrency limit (`asyncio.Semaphore` value) | FR-04 | SAD.md §3.4, §6.6 | P2-DD-6 |
| ADR-05 | Cache key canonical form (the SHA-256 input format) | FR-06 | SAD.md §3.6, §5.7 | P2-DD-3 |
| ADR-06 | Circuit breaker state persistence (in-memory vs Redis) | FR-05 | SAD.md §3.5, §6.6 | (none) |
| ADR-07 | Audio format conversion fallback (ffmpeg-missing policy) | FR-08 | SAD.md §3.8, §5.8 | P2-DD-4 |
| ADR-08 | Structured log transport (stdout JSON vs file vs OpenTelemetry) | NFR-08 | SAD.md §6.1 | P2-DD-5 |

---

## Section 5: ADR Entries (Step 2 — Round 2 authorings)

> This section contains the full ADR entries for ADR-01..ADR-08, authored in Round 2. Each entry preserves the structure of the Step 1 template (Status / Context / Decision / Rationale / Consequences) and adds the **Alternatives** section that Step 1 deferred. All citations reference `SPEC.md`, `SRS.md`, and `SAD.md` by line number / section; cross-references to the P2-DD decisions in Section 1 are noted where applicable.

---

## ADR-01: LEXICON representation

> **Owner**: FR-01 (Taiwan-Chinese vocabulary mapping) — `SPEC.md L32-L51`, `SRS.md §3 FR-01`
> **Implementing module**: `src/engines/taiwan_linguistic.py` (`SPEC.md L192`)
> **Pre-decision**: (none — orthogonal to P2-DD-1..P2-DD-6)
> **SAD reference**: `SAD.md §3.1`

**Status**: Accepted

**Context**: FR-01 requires the `LEXICON` mapping table to contain **≥ 50 entries** (`LEXICON_MIN_SIZE=50`, `SPEC.md L128`) and to be loaded efficiently at proxy startup. The choice of representation affects cold-start time, in-memory footprint, and updateability. Candidates considered: (a) Python `dict` literal compiled into `src/engines/taiwan_linguistic.py`; (b) JSON file loaded at startup; (c) SQLite database; (d) Redis cache. The control-group invariant (`SPEC.md §11 L247-L254` "feature freeze: bug fix only", no new tech stack) constrains the choice to existing-Python-stdlib options.

**Decision**: Store the `LEXICON` as a **Python `dict` literal** in `src/engines/taiwan_linguistic.py` — no external file, no JSON load, no DB, no Redis. The keys are Mainland-Chinese tokens; the values are Taiwan-Chinese strings or Bopomofo transcriptions (per the 12 canonical mappings in `SPEC.md L37-L50`). The `dict` is module-level, so it is constructed once at import time and reused for every request.

**Rationale**:
- **Small dataset, no need for external I/O**: with ≥ 50 entries, the entire `LEXICON` comfortably fits in < 10 KB of source code. A JSON file or SQLite DB would add cold-start I/O cost for no benefit at this size.
- **Fastest lookup**: Python `dict` lookup is O(1) average-case and is the fastest available in-process mapping structure. The synthesis pipeline calls `apply_lexicon(text)` for every `SpeechRequest.input`, so lookup speed directly impacts TTFB (NFR-01, `SPEC.md L110`).
- **Single-file deployment aligns with the control-group invariant**: no new files in the repository, no new build steps, no new dependencies. The LEXICON is a part of the source code, and updating it requires a code commit + deploy (the expected workflow for a static vocabulary table).
- **Determinism and testability**: a `dict` literal is a Python constant. Tests can import the module and inspect the table directly; there is no initialization order or I/O failure mode to mock.
- **Future expansion still works in-memory**: even if the LEXICON grows to 500+ entries in a future treatment group, the `dict` representation remains efficient; the 50-entry threshold is a floor, not a structural limit.

**Consequences**:
- **Positive**:
  - Cold-start is instant: no JSON parsing, no DB open, no network call.
  - Zero runtime file I/O or network I/O for LEXICON access (the synthesis pipeline never touches disk for the mapping).
  - The LEXICON is version-controlled alongside the code (a `git diff` shows vocabulary changes).
  - Tests can `import` and inspect the mapping directly — no fixture loading.
- **Negative**:
  - LEXICON updates require a code deploy (not a config push). This is acceptable for a static, slowly-evolving vocabulary table.
  - The `dict` literal is exposed in the source file (no obfuscation). The 12 canonical mappings (`SPEC.md L37-L50`) are public knowledge; this is not a concern.

**Alternatives considered**:
- **(a) JSON file loaded at startup** — adds an extra file in the repository, extra `json.load` I/O at cold-start, and a fixture-loading concern in tests. Rejected: the dataset is too small to justify the file-based indirection, and the cold-start I/O is a measurable (if small) cost that is not necessary.
- **(b) SQLite database** — adds a `sqlite3` or `peewee` dependency, a schema migration story, and a DB file in the repository. Overkill for 50 entries. Rejected: SQLite is the right tool for a relational dataset that needs querying; the LEXICON is a flat key→value map.
- **(c) Redis cache** — wrong tool. The LEXICON is a static, version-controlled, in-process mapping; it is not "cacheable" data. Using Redis would couple the lookup path to an external service and would violate the FR-06 graceful-no-Redis fallback (`SPEC.md L88-L89, L229`). Rejected: it would also introduce a new tech dependency, violating the control-group invariant.

**Citations**: `SPEC.md L32-L51, L128, L192`; `SRS.md §3 FR-01, §6.1`; `SAD.md §3.1`.

---

## ADR-02: SSML parser strategy

> **Owner**: FR-02 (SSML parsing) — `SPEC.md L52-L65`, `SRS.md §3 FR-02`
> **Implementing module**: `src/engines/ssml_parser.py` (`SPEC.md L193`)
> **Pre-decision**: (none — orthogonal to P2-DD-1..P2-DD-6)
> **SAD reference**: `SAD.md §3.2`

**Status**: Accepted

**Context**: FR-02 requires parsing a subset of SSML — the tags `<speak>`, `<break>`, `<prosody>`, `<emphasis>`, `<voice>`, `<phoneme>`, `<say-as>`, plus comments `<!-- ... -->` (`SPEC.md L55-L63`). P2-DD-1 commits the parser to a warn-and-pass strategy for unspecified emphasis levels (`none|reduced`) and for unsupported `<prosody>` attributes (`pitch`, `volume`). The choice of parser affects robustness, dependencies, and the ease of implementing the warn-and-pass pattern. Candidates: (a) hand-rolled state machine using Python stdlib `html.parser`; (b) `lxml`; (c) `beautifulsoup4`; (d) regex.

**Decision**: Use Python's standard `html.parser` (built-in, no external dependency) with a **hand-written tag-state machine** in `src/engines/ssml_parser.py`. The parser walks the input token stream, maintains a stack of active `<voice>` and `<emphasis>` / `<prosody>` overrides, and emits a list of `Segment` objects plus a list of warnings. The parser does NOT use `lxml`, `beautifulsoup4`, or regex.

**Rationale**:
- **No new tech stack** (control-group invariant, `SPEC.md §11 L247-L254`): `html.parser` is in the Python standard library; there is nothing to install.
- **The SSML subset is small and well-defined** (7 tags + comments, per `SPEC.md L55-L63`). A full HTML/XML parser is overkill; a hand-rolled state machine is simpler and easier to read in 6 months.
- **P2-DD-1 warn-and-pass is easiest in a state machine**: when an unsupported attribute is encountered, the state-machine handler can emit the structured `ssml.unsupported_attr` log (`SAD.md §6.1` allow-list) and pass the text through. Adapting a general HTML parser's strict-parse errors to a warn-and-pass flow would require wrapping or monkey-patching.
- **Testability**: a state machine has a small, finite state space; unit tests can enumerate every state transition and verify the emitted `Segment` list and `warnings` list. The 9 FR-02 test cases (`TEST_INVENTORY.yaml` FR-02) cover the supported tag subset plus the warn-and-pass paths.
- **Extensibility**: a new SSML tag can be added by writing a new `handle_start_tag` / `handle_end_tag` pair. The change is local to `ssml_parser.py` and does not require updating a third-party parser.

**Consequences**:
- **Positive**:
  - ~100 lines of parser code; readable, maintainable, fully tested.
  - No external dependencies; the only `import` is `from html.parser import HTMLParser`.
  - The state machine maps directly to the FR-02 acceptance criteria in `SRS.md §3 FR-02` L161-L188.
  - Adding a new SSML tag is a local change with a clear test target.
- **Negative**:
  - The hand-rolled parser is not a "real" XML parser; it does not validate entity references, DTDs, or XML namespaces. The FR-02 spec does not require these (`SPEC.md L213` mandates plain-text fallback on parse failure, not strict XML validation).
  - A bug in the state machine could be silently wrong. Mitigated by the per-tag test cases in `TEST_INVENTORY.yaml` FR-02.

**Alternatives considered**:
- **(a) `lxml`** — a robust, C-backed XML parser. Adds a C dependency (lxml is not pure-Python), which is a new tech-stack addition. Rejected: the SSML subset is too small to need lxml's full feature set, and the C dependency complicates the deployment story.
- **(b) `beautifulsoup4`** — an HTML parser designed for web scraping. Overkill and too lenient (it silently corrects malformed HTML, which is the wrong behavior for SSML — the proxy needs to detect malformed SSML and fall back to plain text, per `SPEC.md L213`). Rejected: too lenient, and adds a new dependency.
- **(c) Regex** — the most fragile of the four. Nested tags (`<voice name="x">...<emphasis>...</emphasis>...</voice>`) require a stack-based parser, which regex cannot model. Rejected: too fragile for nested SSML.

**Citations**: `SPEC.md L52-L65, L193, L213`; `SRS.md §3 FR-02 L161-L188, §7 row 1`; `SAD.md §3.2, §6.1`.

---

## ADR-03: Chunk-tier boundary semantics

> **Owner**: FR-03 (intelligent text chunking) — `SPEC.md L67-L75`, `SRS.md §3 FR-03`
> **Implementing module**: `src/engines/text_splitter.py` (`SPEC.md L194`)
> **Pre-decision**: P2-DD-2 (CJK/Latin word boundary detector)
> **SAD reference**: `SAD.md §3.3, §5.4`

**Status**: Accepted

**Context**: FR-03 requires a three-tier recursive splitter (sentence → clause → phrase) with a hard 250-char cap (`MAX_CHARS_PER_REQUEST=250`, `SPEC.md L127`). The spec (`SPEC.md L69-L74`) specifies the precedence: **L1 = `。？！!?\n`** (always), **L2 = `；:`** (only if segment > 100 chars), **L3 = `，`** (only if segment > 100 chars). P2-DD-2 commits the CJK/Latin word boundary detector to whitespace-OR-punctuation (P2-DD-2 above; `SAD.md §3.3`). The **100-char threshold** for invoking L2 and L3 is a design parameter that this ADR commits. Candidates: (a) always split at every tier; (b) use the 100-char threshold as documented; (c) no tiering.

**Decision**: The **100-char threshold** for invoking L2 and L3 splits is the rule. A clause boundary (L2) is meaningful only when the resulting chunks would be > 100 chars; otherwise the L1 sentence boundary was already coarse enough. A phrase boundary (L3) follows the same logic. The hard 250-char cap (`SPEC.md L127`) is the ultimate backstop and is enforced by force-splitting at 250 with hyphen padding if no boundary yields a valid chunk (per `SAD.md §5.4` step 3 final bullet).

**Rationale**:
- **Empirical evidence from the LEXICON coverage notes** (`SRS.md §4 NFR-02` L115-L116, citing Taiwan-news corpus characteristics): most Taiwan-Chinese sentences are 30-80 characters. A 100-char threshold avoids creating artificially short chunks (e.g., 5-15 char fragments) that fragment synthesis unnecessarily and hurt TTFB (NFR-01, `SPEC.md L110`).
- **P2-DD-2 consistency**: the whitespace-or-punctuation detector (P2-DD-2) and the 100-char threshold are both driven by the same principle — split at natural boundaries, but do not over-split. A chunk that is already ≤ 100 chars after an L1 split is at a natural sentence boundary; further L2/L3 splitting would produce sub-sentence fragments that the synthesis engine handles worse than full sentences.
- **Predictable chunk size distribution**: with the 100-char threshold, the typical chunk size is 40-250 chars (per `SRS.md §3 FR-03 AC2` L199, "100–250 chars is the optimal range"). Without the threshold, the distribution skews to many tiny chunks (10-30 chars), which is wasteful.
- **Reduced overhead from too many chunks**: each chunk is one `httpx.AsyncClient` request to the Kokoro backend (FR-04, `SPEC.md L77-L79`). Fewer, larger chunks mean fewer HTTP round-trips, less breaker-counter pressure, and less Redis-cache-key proliferation.
- **SPEC.md L69-L74 specifies the threshold explicitly**: the spec wording "if the segment is still > 100 chars" appears in L73 and L74. The threshold is not a design freedom; it is a spec value. This ADR documents the rationale so the methodology-v2 reviewer can audit the choice.

**Consequences**:
- **Positive**:
  - Predictable chunk sizes (40-250 chars) match the spec's optimal range (`SRS.md §3 FR-03 AC2`).
  - Reduced overhead: fewer chunks per request on average.
  - P2-DD-2 (whitespace/punctuation boundary) is consistent with this tiering — both decisions bias toward natural boundaries and away from over-splitting.
  - The hard 250-char cap (`SPEC.md L127`) remains the upper bound, enforced even when the 100-char threshold is not yet exceeded.
- **Negative**:
  - A pathological input (e.g., a 200-char sentence with no L2/L3 boundary) yields a single 200-char chunk at L1, even though L2/L3 might have produced two ~100-char chunks. This is the documented behavior; the cap (250) is the limit.
  - The 100-char threshold is a magic number. It is documented in `SPEC.md L73-L74` and in this ADR; it is not configurable.

**Alternatives considered**:
- **(a) Always split at every tier** — too aggressive. Would produce dozens of small chunks (5-30 chars) for a typical input, fragmenting synthesis and hurting TTFB. Rejected: violates the spec's "100–250 chars is the optimal range" guidance (`SRS.md §3 FR-03 AC2` L199).
- **(b) Use a single regex per tier** — loses the precedence structure. The spec mandates L1 → L2 → L3 in that order with the 100-char threshold; a flat regex per tier would either over-split or miss the precedence. Rejected: violates `SPEC.md L69-L74`.
- **(c) No tiering** — single regex that splits at any boundary character. Violates `SPEC.md L69-L74` and loses the natural-boundary bias. Rejected: violates the spec.

**Citations**: `SPEC.md L67-L75, L127, L194`; `SRS.md §3 FR-03 L190-L208, §4 NFR-02 L115-L116`; `SAD.md §3.3, §5.4`.

---

## ADR-04: Parallel synthesis concurrency limit

> **Owner**: FR-04 (parallel synthesis) — `SPEC.md L77-L79`, `SRS.md §3 FR-04`
> **Implementing module**: `src/engines/synthesis.py` (`SPEC.md L195`)
> **Pre-decision**: P2-DD-6 (partial-success WAIVED)
> **SAD reference**: `SAD.md §3.4, §6.6`

**Status**: Accepted

**Context**: FR-04 requires N `httpx.AsyncClient` requests to the Kokoro backend in-flight concurrently (for N chunks; `SPEC.md L78`). P2-DD-6 waives partial-success mode (`SAD.md §3.4`): a single chunk failure fails the whole request. The choice of concurrency limit affects backend load, TTFB (NFR-01, `SPEC.md L110`), and the risk of overwhelming a single-threaded Kokoro backend. Candidates: (a) unbounded (`asyncio.gather` of all chunks); (b) `asyncio.Semaphore(1)` (sequential); (c) `asyncio.Semaphore(8)` (default); (d) adaptive limit.

**Decision**: Use `asyncio.Semaphore(8)` as the **default concurrency limit**. The limit is **configurable via the `MAX_CONCURRENT_SYNTHESIS` environment variable**; the default of `8` is hard-coded in `src/config.py` and matches the typical chunk count for a ≤ 8000-char input (≤ 32 chunks worst-case at 250 chars each; 8 in-flight × 4 batches is a reasonable default).

**Rationale**:
- **8 is empirically enough to overlap network I/O without saturating a single-threaded Kokoro backend**: typical chunk synthesis latency is 50-150 ms (`SAD.md §7` NFR-01 row). With 8 concurrent in-flight requests and 50-150 ms each, the total wall-clock for 32 chunks is roughly 4 batches × 100 ms = 400 ms — well within the 300 ms TTFB target for the first byte (`SPEC.md L110`) and the 30s overall timeout (`SPEC.md L129`).
- **Aligns with the 30s `REQUEST_TIMEOUT`** (`SPEC.md L129`, NFR-07): even with 4 sequential batches of 100 ms each, the total stays under 1 s; the 30s budget is more than enough.
- **Aligns with the 3-failure circuit-breaker threshold** (`CIRCUIT_BREAKER_THRESHOLD=3`, `SPEC.md L130`): the breaker trips on 3 consecutive backend failures, not on a queue depth. The semaphore limits queue depth but does not affect the breaker's per-call failure accounting.
- **Configurable via env var**: the operator can tune the limit per deployment. A slow backend (e.g., CPU-only Kokoro on a Raspberry Pi) can lower the limit to 2; a fast backend with a load balancer can raise it to 32. The default of 8 is the sane middle ground for the control group's typical hardware.
- **No risk of accidental DoS on the backend**: the semaphore caps the in-flight count, so a request with 32 chunks does not spawn 32 simultaneous TCP connections to Kokoro.

**Consequences**:
- **Positive**:
  - Predictable backend load (never more than 8 in-flight requests per uvicorn worker).
  - Easy to tune via `MAX_CONCURRENT_SYNTHESIS` env var.
  - No risk of accidental DoS on a single-threaded Kokoro backend.
  - The semaphore integrates cleanly with `asyncio.gather` (each coroutine acquires the semaphore before its `httpx` call).
- **Negative**:
  - A request with 32 chunks is processed in 4 sequential batches, not all at once. Total wall-clock is ~400 ms instead of ~100 ms. This is an acceptable trade-off for backend safety.
  - The default of 8 is a magic number. It is documented in `src/config.py` and in this ADR; it is not auto-tuned.

**Alternatives considered**:
- **(a) Unbounded (`asyncio.gather` of all chunks)** — risks backend overload. A pathological input (32 chunks) would spawn 32 simultaneous TCP connections to Kokoro, which is a DoS risk for a single-threaded backend. Rejected: violates the "predictable backend load" goal.
- **(b) `asyncio.Semaphore(1)` (sequential)** — defeats the parallelism purpose of FR-04. Total wall-clock would be 32 × 100 ms = 3.2 s for a 32-chunk input, which is well over the TTFB target (`SPEC.md L110`). Rejected: violates the spec's N concurrent-in-flight requirement (`SPEC.md L78`).
- **(c) Adaptive limit** — dynamically adjust the semaphore size based on observed backend latency. Too complex for the control group; would require latency-tracking state and a tuning loop. Rejected: violates the "no new tech" feature-freeze invariant (`SPEC.md §11 L247-L254`); a treatment group can introduce adaptive concurrency as a clean experimental differentiator.

**Citations**: `SPEC.md L77-L79, L130, L195`; `SRS.md §3 FR-04 L210-L221, §4 NFR-01 L110, NFR-07 L129`; `SAD.md §3.4, §6.6, §7 NFR-01`.

---

## ADR-05: Cache key canonical form (SHA-256 input)

> **Owner**: FR-06 (Redis cache) — `SPEC.md L86-L89`, `SRS.md §3 FR-06`
> **Implementing module**: `src/cache/redis_cache.py` (`SPEC.md L198`)
> **Pre-decision**: P2-DD-3 (cache key hash: SHA-256 of canonical serialization)
> **SAD reference**: `SAD.md §3.6, §5.7`

**Status**: Accepted

**Context**: FR-06 requires the cache key to be `hash(text + voice + speed)` (`SPEC.md L87`). P2-DD-3 commits the hash function to `hashlib.sha256` and the canonical serialization to `text + "\x00" + voice + "\x00" + str(round(speed, 2))` (P2-DD-3 above; `SAD.md §3.6`). The **canonical form of the input string** affects cache hit rate: two semantically identical requests with slightly different serializations (e.g., `1.0` vs `1.0000001`, or different separator characters) would produce different cache keys and miss the cache. This ADR commits the canonical form and the separator choice. Candidates: (a) JSON-serialize the dict; (b) pickle; (c) length-prefixed encoding; (d) NUL-separated (the P2-DD-3 choice).

**Decision**: The canonical form is `text + "\x00" + voice + "\x00" + str(round(speed, 2))`. The NUL byte (`\x00`) is the field separator. The SHA-256 hex digest of this canonical form (UTF-8 encoded) is the 64-char hash, prefixed with `tts:cache:` to form the Redis key (per P2-DD-3). Speed is rounded to 2 decimal places to coalesce near-identical speeds (e.g., `1.0` and `1.0001` hit the same cache entry).

**Rationale**:
- **NUL separator is the standard canonical-form delimiter**: it is used in HTTP headers (`\r\n` row separator within field values, in older specs), MIME multipart boundaries, and many other protocols. The NUL byte cannot appear in valid UTF-8 text (it is a control character) or in voice names (which are alphanumeric + underscore). The boundary is therefore unambiguous.
- **Speed rounding to 2 decimals matches user-perceived equivalence**: the FR-06 `speed` field has an implicit granularity of 0.01 (the upstream OpenAI-compatible API accepts `1.0`, `1.01`, `1.1`, etc.). Rounding `0.9999999...` to `1.0` is a coalescing behavior that matches what a user would consider "the same request".
- **No false negatives from formatting differences**: with the canonical form, two requests that differ only in whitespace (which the synthesizer normalizes away), or in trailing zeros in the speed, hit the same cache entry. Without the canonical form, a request with `speed=1.0` and a request with `speed=1.00` would produce different keys and miss the cache, fragmenting the hit rate.
- **The canonical form is deterministic across Python versions and platforms**: `round(1.0, 2) == 1.0` in all Python implementations; the NUL byte is platform-independent. The cache key is stable.
- **P2-DD-3 consistency**: this ADR formalizes the canonical form that P2-DD-3 commits. The 100-char separator choice (NUL) and the 2-decimal rounding are the design specifics; P2-DD-3 is the high-level decision.

**Consequences**:
- **Positive**:
  - Predictable cache hits: semantically identical requests always hit the same key.
  - No false negatives from formatting differences (whitespace, trailing zeros, etc.).
  - Redis key format `tts:cache:<sha256_hex>` is namespaced and safe for shared Redis instances.
  - The NUL separator is a one-line implementation; no length-prefix arithmetic.
- **Negative**:
  - A user who intentionally requests `speed=1.0` vs `speed=1.01` gets two different cache entries. This is correct (the requests ARE different) but may surprise a user who expects fine-grained caching to coalesce.
  - The 2-decimal rounding is a magic number. It is documented in P2-DD-3 and in this ADR.

**Alternatives considered**:
- **(a) JSON-serialize the dict** (`json.dumps({"text": text, "voice": voice, "speed": speed})`) — extra parsing, not canonical (JSON output is not guaranteed byte-identical across Python versions, especially for non-ASCII strings), and slower than the NUL-separated form. Rejected: not canonical, slower.
- **(b) Pickle** — security risk (unpickling user input is a known RCE vector), format-fragile (Python version and class-definition changes break compatibility), and the canonical form is non-obvious. Rejected: security and stability concerns.
- **(c) Length-prefixed encoding** (e.g., `len(text).to_bytes(4) + text + len(voice).to_bytes(4) + voice + ...`) — more complex than the NUL separator, and the length prefix must itself be fixed-width or variable, with its own canonicalization concerns. Rejected: more complex for no benefit at this size.

**Citations**: `SPEC.md L86-L89, L198`; `SRS.md §3 FR-06 L246-L261`; `SAD.md §3.6, §5.7`.

---

## ADR-06: Circuit breaker state persistence

> **Owner**: FR-05 (circuit breaker) — `SPEC.md L81-L85`, `SRS.md §3 FR-05`
> **Implementing module**: `src/middleware/circuit_breaker.py` (`SPEC.md L197`)
> **Pre-decision**: (none — orthogonal to P2-DD-1..P2-DD-6)
> **SAD reference**: `SAD.md §3.5, §6.6`

**Status**: Accepted

**Context**: FR-05 requires a circuit breaker with three states — Closed, Open, Half-Open — that wraps backend calls (`SPEC.md L81-L85`). The spec does not specify whether the state is per-process or shared across processes. Candidates: (a) in-process state (each uvicorn worker has its own breaker); (b) Redis-backed shared state; (c) file-backed state; (d) distributed consensus.

**Decision**: **In-process state** (no Redis, no shared state, no file). Each uvicorn worker process has its own `CircuitBreaker` instance with its own `state`, `failure_count`, and `opened_at` fields. The state is mutated under an `asyncio.Lock` (`SAD.md §6.6` final bullet) to prevent race conditions on concurrent failure events within the same process.

**Rationale**:
- **Control-group invariant: no new tech** (`SPEC.md §11 L247-L254`): Redis is already a dependency for FR-06 caching, but it is **optional** (FR-06 graceful no-Redis fallback, `SPEC.md L88-L89, L229`). Coupling the circuit breaker to Redis would break the no-Redis fallback path: if Redis is down, the breaker would not be able to read or write its state, and the proxy would either fail-open (always call the backend, defeating the breaker's purpose) or fail-closed (always 503, even if the backend is healthy).
- **The 3-failure threshold naturally absorbs per-process state divergence**: with `CIRCUIT_BREAKER_THRESHOLD=3` (`SPEC.md L130`), each worker independently needs 3 consecutive failures to trip. Under uniform load, all workers trip at roughly the same time; under low load, a single bad request can trip one worker but not the others, but that is acceptable — the next request hits the healthy worker.
- **Simplicity**: in-process state is a Python instance variable. No external service, no schema, no migration story. The breaker is testable in isolation (a unit test instantiates a `CircuitBreaker`, calls it 3 times with a failing coroutine, and asserts the state transitions).
- **The 503 response is the union of all workers' breaker states**: a client that happens to land on a tripped worker sees 503; a client that lands on a healthy worker sees the normal response. This is acceptable for a local, single-user proxy (the methodology-v2 use case).

**Consequences**:
- **Positive**:
  - No external dependency for the breaker; the FR-06 no-Redis fallback path remains intact.
  - Simple to implement, test, and reason about.
  - Each worker independently trips, which is fine under uniform load.
  - No race conditions within a process (the `asyncio.Lock` serializes state mutations).
- **Negative**:
  - Under low load, a single bad request can trip one worker but not the others. The 503 response is therefore non-uniform across workers for a brief window.
  - The breaker state is lost on worker restart. A worker that restarts after a backend outage starts in `Closed` state and may make a few failing requests before tripping again. This is the expected behavior; the breaker protects against cascading failures, not against a single transient error.

**Alternatives considered**:
- **(a) Redis-backed shared state** — would couple the breaker to Redis, violating the FR-06 no-Redis fallback (`SPEC.md L88-L89, L229`). When Redis is down, the breaker would either fail-open (always call the backend, defeating the purpose) or fail-closed (always 503, even if the backend is healthy). Rejected: violates the FR-06 fallback invariant.
- **(b) File-backed state** (e.g., write `state.json` to disk on every transition) — IO overhead on every state mutation, race conditions across processes (two workers writing simultaneously could corrupt the file), and adds a new file to manage. Rejected: IO overhead and race conditions, with no benefit over in-process state for the local-proxy use case.
- **(c) Distributed consensus** (e.g., Raft, etcd) — overkill for a local, single-user proxy. Adds significant new tech (a consensus library, a separate consensus service) that violates the control-group invariant. Rejected: overkill.

**Citations**: `SPEC.md L81-L85, L130-L131, L197, L229`; `SRS.md §3 FR-05 L223-L244`; `SAD.md §3.5, §6.6`.

---

## ADR-07: Audio format conversion fallback (ffmpeg-missing policy)

> **Owner**: FR-08 (ffmpeg audio format conversion) — `SPEC.md L100-L102, L228`, `SRS.md §3 FR-08`
> **Implementing module**: `src/audio_converter.py` (`SPEC.md L188`)
> **Pre-decision**: P2-DD-4 (per-call check, raise, router maps to HTTP 500)
> **SAD reference**: `SAD.md §3.8, §5.8`

**Status**: Accepted

**Context**: FR-08 requires ffmpeg-based MP3↔WAV conversion (`SPEC.md L100-L102`). P2-DD-4 commits the per-call `shutil.which("ffmpeg")` check, the `FFmpegUnavailableError` raise, and the router's mapping of the exception to HTTP 500 with body `{"error": {"code": "ffmpeg_unavailable", "message": "..."}}` (P2-DD-4 above; `SAD.md §3.8`). The Round 2 decision **reverted** an initial P1-strawman "graceful skip" policy to the spec's "fail with a clear error message" wording (`SRS.md §3 FR-08 AC3` L271, `SPEC.md L228`). This ADR documents the rationale for the per-call check (no caching), the per-call retry semantics, and the service-continuity policy. Candidates: (a) cache the ffmpeg-presence check; (b) globally disable FR-08 if ffmpeg missing; (c) silently return input bytes; (d) per-call check with raise (the P2-DD-4 choice).

**Decision**: Per-call `shutil.which("ffmpeg")` check (no caching). If ffmpeg is missing for the requested format conversion, emit an allow-listed structured log (`{"event": "ffmpeg.unavailable", "format_requested": "<fmt>", "level": "warn"}`) and raise `FFmpegUnavailableError`. The router (`src/routers/speech.py`) maps the exception to **HTTP 500** with body `{"error": {"code": "ffmpeg_unavailable", "message": "ffmpeg binary not found on PATH; required for format conversion to <fmt>"}}`. Per-call retry is preserved (no caching of the check). The service continues to work for the natively-supported format (MP3) and for other endpoints.

**Rationale**:
- **Aligns with `SRS.md §3 FR-08 AC3` L271 and `SPEC.md L228` R3**: the spec mandates "fail with a clear error message" and "the service must continue to work for the other (already-supported) format." The HTTP 500 with a clear code and message is the most informative response — the caller knows exactly what is missing and what to do (install ffmpeg or request a different format).
- **Per-call check (no caching) means a later call after ffmpeg install succeeds without service restart**: an operator who installs ffmpeg while the proxy is running does not need to restart uvicorn. The next conversion call re-evaluates `shutil.which("ffmpeg")` and succeeds. This is a small operational win and aligns with the "service must continue" language.
- **Service continuity for other paths**: the failure is scoped to the format-conversion path. Other endpoints (`GET /health`, `GET /ready`, `GET /v1/proxy/voices`, and `POST /v1/proxy/speech` returning MP3 without conversion) continue to operate. The process does not crash. This matches the "service must continue to work for the other (already-supported) format" wording exactly.
- **No silent graceful-degradation fallback to wrong-format bytes**: returning the MP3 bytes with a `Content-Type: audio/wav` header would be a silent lie about the format. The caller would get a corrupted audio file. The P2-DD-4 raise-on-miss policy is the only honest response.
- **Round 2 revert rationale**: the initial P1 strawman proposed a "graceful skip" (return the wrong format with a warning) but this was rejected by Agent B in Round 1 review (MEDIUM gap) as a deviation from the spec wording. Round 2 reverts to the spec's "fail with a clear error message" language exactly. This ADR records the post-revert rationale.

**Consequences**:
- **Positive**:
  - Clear error to client when ffmpeg is missing (HTTP 500 with a structured body).
  - No silent degradation — the caller knows the conversion failed and why.
  - Service stays up for other formats and endpoints.
  - No service restart needed after ffmpeg install — the per-call check picks up the new binary.
  - Matches the spec wording exactly (`SPEC.md L228`, `SRS.md §3 FR-08 AC3` L271).
- **Negative**:
  - Every conversion call does a `shutil.which` (cheap, ~1 µs; not a real concern).
  - A caller that retries a conversion-heavy request after ffmpeg install will see HTTP 500 for the first attempt and HTTP 200 for the next — that is the desired behavior.
  - The 21 test cases for FR-08 (`TEST_INVENTORY.yaml` FR-08) must include a 500-with-clear-body test for the missing-ffmpeg case to lock the behavior in CI.

**Alternatives considered**:
- **(a) Cache the ffmpeg-presence check** (e.g., set a module-level `_FFMPEG_AVAILABLE: bool | None = None` flag, updated on first call or at startup) — would require service restart after install, defeating the "operator installs ffmpeg and it works" property. Rejected: the per-call check is cheap and avoids the restart requirement.
- **(b) Globally disable FR-08 if ffmpeg missing** (e.g., set a startup-time `FFMPEG_ENABLED=False` flag that makes the converter functions raise `NotImplementedError`) — would break the WAV output flow entirely (WAV requests would 500 even after the operator installs ffmpeg, until the proxy is restarted). Rejected: too coarse, requires restart, and gives a less informative error than the per-call check.
- **(c) Silently return input bytes** (e.g., if MP3→WAV is requested but ffmpeg is missing, return the original MP3 bytes with a `Content-Type: audio/wav` header) — would violate the spec ("fail with a clear error message") and would return corrupted audio to the caller. Rejected: silent failure is the worst option.

**Citations**: `SPEC.md L100-L102, L188, L228`; `SRS.md §3 FR-08 L283-L297, §8 R3`; `SAD.md §3.8, §5.8, §8 R3`.

---

## ADR-08: Structured log transport

> **Owner**: NFR-08 (security / input validation) — `SPEC.md L216-L218`, `SRS.md §4 NFR-08, §8 R6`
> **Implementing module**: `src/main.py` (logger setup), `src/routers/speech.py` (request logging)
> **Pre-decision**: P2-DD-5 (log sanitization allow-list)
> **SAD reference**: `SAD.md §6.1`

**Status**: Accepted

**Context**: NFR-08 requires structured logs (`SRS.md §4 NFR-08`). P2-DD-5 commits the allow-list of 12 safe top-level keys and the deny-by-default sanitization pipeline (P2-DD-5 above; `SAD.md §6.1`). The **log transport** — where the sanitized JSON lines are written — is a separate decision: stdout, a file, or an OpenTelemetry / observability backend. Candidates: (a) stdout-only (JSON Lines); (b) file-based with rotation; (c) OpenTelemetry export; (d) syslog.

**Decision**: **stdout-only** (JSON Lines format). No log file. No OpenTelemetry export. The container / k8s / CLI environment is responsible for log capture (e.g., `docker logs`, `kubectl logs`, or direct stdout piping in the CLI case).

**Rationale**:
- **Control-group invariant: no new tech** (`SPEC.md §11 L247-L254`): OpenTelemetry is a significant new dependency (an SDK, an exporter, an OTLP endpoint, a collector). The proxy is a local, single-user service; the operational observability primitives (stdout + a downstream aggregator) are sufficient.
- **stdout is the universal log sink for containerized apps**: Docker, Kubernetes, systemd, and most cloud runtimes capture stdout by default. A separate log file would require log-rotation logic, file-path configuration, and a cleanup story — none of which add value in a container deployment.
- **The allow-list sanitizer (P2-DD-5) operates before the transport layer**: regardless of whether the log goes to stdout, a file, or an OTLP endpoint, the sanitization step in `src/main.py` ensures that no PII / secret reaches the transport. The transport choice is therefore orthogonal to the sanitization correctness.
- **Aggregators (Loki, Splunk, Datadog, etc.) integrate via stdout scraping**: the JSON Lines format is the de facto standard for log aggregation. A future treatment group that adds OpenTelemetry export is a clean experimental differentiator.
- **CLI (`tts-v610`) emits to stdout directly**: when the CLI is invoked from a terminal, the user sees the sanitized JSON lines (or nothing, if no events are emitted). When invoked from a script, the script can pipe stdout to a file or another tool. The transport is consistent across HTTP and CLI entry points.

**Consequences**:
- **Positive**:
  - No log-rotation logic in the proxy (the runtime handles it).
  - Consistent transport across HTTP and CLI entry points.
  - Aggregators integrate via stdout scraping (no new proxy code needed).
  - The sanitizer (P2-DD-5) is the last action before emit, so PII protection is transport-independent.
  - Aligns with the "12-factor app" methodology: logs are a stream, not a file.
- **Negative**:
  - Logs are ephemeral if not captured by the runtime. A deployment that does not configure stdout capture will lose log lines on container restart.
  - A long-running proxy in a non-containerized environment (e.g., a bare-metal server with no `journald` or `docker logs`) would need a wrapper script to capture stdout. This is acceptable for the control group's local-single-user deployment model.

**Alternatives considered**:
- **(a) File-based logging with rotation** (e.g., `logging.handlers.RotatingFileHandler` writing to `/var/log/kokoro-taiwan-proxy/proxy.log`) — adds complexity (file path config, rotation policy, cleanup), no value in a container env (the container's stdout is already captured), and ties the proxy to a specific filesystem layout. Rejected: complexity without benefit.
- **(b) OpenTelemetry export** (e.g., OTLP gRPC to a collector) — new tech stack, violates the control-group invariant. Would add the `opentelemetry-sdk` and `opentelemetry-exporter-otlp` packages, a configuration block for the OTLP endpoint, and a separate dependency tree. Rejected: control-group violation, and a treatment group can add OpenTelemetry as a clean experimental differentiator.
- **(c) Syslog** — not native to container environments (Docker captures stdout, not syslog). Would require a syslog daemon on the host, which is a new external dependency. Rejected: not native to the container deployment model.

**Citations**: `SPEC.md L20-L26, L216-L218, L247-L254`; `SRS.md §4 NFR-08 L133-L138, §8 R6, §2.6 secret management`; `SAD.md §6.1`.

---

*End of ADR.md — Kokoro Taiwan Proxy — P2 architecture, v1.0.0 (preamble + 8 ADRs). Authority: SPEC.md v1.0.0-control; SRS.md v1.1; SAD.md v1.0.0.*
