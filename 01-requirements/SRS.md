# Software Requirements Specification — Kokoro Taiwan Proxy

> **Authoritative source**: `SPEC.md` (Kokoro Taiwan Proxy Specification, v1.0.0-control, updated 2026-03-31).
> **Project role**: Control Group for a methodology-v2 improvement experiment. This SRS is the P1 deliverable and is the canonical statement of requirements for downstream phases P2–P8.
> **Conformance**: All requirements in this SRS are derived from `SPEC.md` and cited by line number. No new requirements, technologies, or design choices are introduced.

---

## 1. Introduction

### 1.1 Project name
- **`kokoro-taiwan-proxy`** (project root: `/Users/johnny/projects/tts-new`).
  **Source**: `SPEC.md L10`.

### 1.2 Purpose
- Transform the upstream **Kokoro-82M Docker backend** into a **Taiwan (繁體中文) optimized TTS service** by inserting a FastAPI proxy layer.
  The proxy receives OpenAI-style requests, performs Taiwan-Chinese vocabulary mapping, SSML parsing, intelligent text chunking, and parallel synthesis, then forwards to the local Kokoro Docker backend (`http://localhost:8880/v1`) to produce MP3/WAV audio.
  **Source**: `SPEC.md L11-L14`.

### 1.3 Scope
- **In scope**:
  - A FastAPI proxy layer (Python 3.10+) exposing OpenAI-style speech endpoints.
  - Taiwan-Chinese linguistic processing (LEXICON mapping, Bopomofo substitution).
  - SSML parsing with a Kokoro-compatible tag subset.
  - Recursive three-tier text chunking with hard upper bound.
  - Parallel synthesis against the Kokoro backend.
  - Circuit breaker fault isolation.
  - Optional Redis caching (graceful no-Redis fallback).
  - `tts-v610` command-line tool for batch / scriptable use.
  - ffmpeg-based MP3 ↔ WAV conversion.
  - 4 preset Persona voice recipes.
  **Source**: `SPEC.md L7-L14, L181-L205`.

- **Out of scope** (per `PROJECT_BRIEF.md` §5):
  - New programming languages, frameworks, or runtime upgrades.
  - Modifying the Kokoro Docker backend.
  - Authentication, multi-tenant support, rate limiting beyond the circuit breaker.
  - PII handling / privacy tooling.
  - Production deployment (CI/CD, k8s, autoscaling).
  - Languages beyond Traditional Chinese.
  - New voice engines beyond Kokoro's preset voices.
  - New frontends (web UI, mobile SDK) — only the FastAPI proxy layer and CLI.
  - Methodology framework modifications (control group baseline).

### 1.4 Definitions, acronyms, abbreviations
| Term | Definition | Source |
|------|------------|--------|
| TTS | Text-to-Speech; the process of converting text into spoken audio output. | `SPEC.md L11` |
| Kokoro | The upstream open-source TTS engine (Kokoro-82M), packaged as a Docker container. | `SPEC.md L13` |
| Proxy | A FastAPI application that mediates between client requests and the Kokoro backend. | `SPEC.md L12` |
| LEXICON | The static mapping table that converts Mainland/Simplified-leaning vocabulary to Taiwan (繁體) vocabulary or to Bopomofo (注音) transcriptions. | `SPEC.md L33` |
| SSML | Speech Synthesis Markup Language; an XML-based markup for controlling prosody, breaks, voices, and pronunciation. | `SPEC.md L52` |
| Chunk | A bounded text segment (≤ 250 characters) produced by the splitter, fed to the backend as one request. | `SPEC.md L69` |
| Circuit Breaker | A fault-isolation state machine (Closed → Open → Half-Open) that short-circuits calls to a failing backend. | `SPEC.md L82-L85` |
| TTFB | Time To First Byte; the latency from request received to first byte of audio returned. | `SPEC.md L110` |
| Persona | A predefined voice + speed recipe encapsulating a desired character (e.g., 極致溫柔助理). | `SPEC.md L145-L150` |
| Methodology-v2 | The improvement-experiment framework under which this project serves as the control group. | `SPEC.md L14` |

### 1.5 References
- `SPEC.md` — Kokoro Taiwan Proxy Specification (v1.0.0-control, 2026-03-31). **Single source of truth** (`SPEC.md L1-L4`).
- `PROJECT_BRIEF.md` — Orchestrator-authored project context summary.
- `README.md` — Operator-facing startup instructions.
- `CONTROL_GROUP.md` — Control-group positioning document (P3+ deliverable; `SPEC.md L201, L242-L243`).
- `requirements.txt` — Python dependency manifest.
- `tests/` — 82 test cases (`SPEC.md L200, L235`).

### 1.6 Document structure
- §1 Introduction · §2 Overall Description · §3 Functional Requirements (FR-01..FR-08) · §4 Non-Functional Requirements · §5 External Interface Requirements · §6 Data Model / Configuration · §7 Error Handling · §8 Risks · §9 Acceptance Criteria.

---

## 2. Overall Description

### 2.1 Product perspective
- The product is a **proxy layer** that sits between client applications (CLI, HTTP callers) and the upstream **Kokoro-82M Docker backend**.
  Kokoro is treated as a black box at `http://localhost:8880/v1`; the proxy adds Taiwan-Chinese linguistic value on top of the generic OpenAI-compatible endpoint.
  **Source**: `SPEC.md L11-L14, L122-L124`.

- The product does **not** own the speech-synthesis model itself; it adapts the upstream behavior for a Taiwan audience. Any change to the model is upstream's responsibility and out of scope.

### 2.2 User classes and characteristics
| User class | Description | Primary interface |
|-----------|-------------|-------------------|
| Podcast producers | Build audio articles; need consistent Taiwan pronunciation and SSML control. | `POST /v1/proxy/speech` |
| IVR system integrators | Build telephone-prompt audio; need WAV output and stable TTFB. | `POST /v1/proxy/speech` with `response_format=wav` |
| Accessibility tooling authors | Generate screen-reader audio; need batch CLI and caching. | `tts-v610` CLI (FR-07) |
| News-summary app developers | Produce short newscasts; need the 甜美親和主播 persona. | Persona `甜美親和主播` (`SPEC.md L150`) |
| 教育內容創作者 | Build children's content; need the 極致溫柔助理 persona. | Persona `極致溫柔助理` (`SPEC.md L147`) |
| Methodology reviewers | Compare control group vs. treatment groups; inspect P1–P8 artifacts. | Compliance artifacts (this document and downstream deliverables) |
| Project owner | Johnny (`PROJECT_BRIEF.md §2`); reviews PRs and operates the service. | GitHub + local CLI |

**Source**: `SPEC.md L155-L163, L165-L175`; `PROJECT_BRIEF.md §2`.

### 2.3 Operating environment
- Python 3.10+ runtime.
- Docker engine available locally to run the Kokoro-82M container on port 8880.
- Optional: Redis instance for cache tier (FR-06).
- ffmpeg binary available on `PATH` (FR-08).
- **Source**: `SPEC.md L11, L13, L20-L26`.

### 2.4 Design and implementation constraints

> The following block is reproduced **verbatim** from `SPEC.md §11, L247-L254` and constitutes an immutable control-group constraint set:

> ❌ 引入新技術棧
> ❌ 修改核心演算法
> ❌ 刪除或修改既有測試
> ❌ 降低測試覆蓋率
> ❌ feature freeze：只做 bug fix

**Source**: `SPEC.md L247-L254`.

**Additional constraints derived from `SPEC.md`**:

- **Tech stack is locked** to FastAPI + httpx + uvicorn + Kokoro Docker + curl (voice fetch) + optional Redis + ffmpeg (`SPEC.md L20-L26`). No substitutions are permitted.
- **8 functional requirements are pre-defined and immutable** (FR-01..FR-08, `SPEC.md L32-L103`). Inventing new FRs is prohibited.
- **Configuration values are fixed** (`SPEC.md L122-L141`): `MAX_CHARS_PER_REQUEST=250`, `LEXICON_MIN_SIZE=50`, `REQUEST_TIMEOUT=30.0`, `CIRCUIT_BREAKER_THRESHOLD=3`, `CIRCUIT_BREAKER_TIMEOUT=10.0`, `WARMUP_ENABLED=True`, `WARMUP_TEXT="你好，測試中"`, `DEFAULT_VOICE="zf_xiaoxiao"`, `DEFAULT_SPEED=1.0`.
- **Single source of truth**: `SPEC.md` is canonical. No overlay document may amend it (`SPEC.md L1-L4`).
- **Test count is fixed**: 82 tests must remain green (`SPEC.md L200, L235`).
- **Folder structure is prescribed** in `SPEC.md §7, L181-L205` and must be preserved.

### 2.5 Assumptions and dependencies
- The Kokoro-82M Docker image is available and started on `localhost:8880` before the proxy is launched.
- Redis is optional; the service must start, run, and pass all tests with or without Redis (`SPEC.md L88-L89, L228-L229`).
- ffmpeg is installed on the host and discoverable on `PATH` (`SPEC.md L100-L103, L228`).
- The proxy does not need network access beyond the loopback Kokoro endpoint and the optional Redis.

---

## 3. Functional Requirements

> The 8 functional requirements below are reproduced from `SPEC.md §3, L32-L103` and form the **complete and immutable** functional scope of the project. Each FR is restated, assigned testable acceptance criteria, and cited by line.

### FR-01: 台灣中文詞彙映射 (Taiwan-Chinese vocabulary mapping)
- **Description**: The system shall transform Mainland-leaning or ambiguous vocabulary in the input text to Taiwan-Chinese vocabulary or to Bopomofo (注音) transcriptions via a static `LEXICON` table. This is the core linguistic value-add of the proxy and the foundation of "Taiwanization".
  **Source**: `SPEC.md L32-L51`.

- **Acceptance criteria** (all testable, measurable):
  1. The `LEXICON` table must contain **≥ 50 entries** at runtime. **Measured by** `len(LEXICON) >= LEXICON_MIN_SIZE` where `LEXICON_MIN_SIZE = 50` (`SPEC.md L128`).
     **Source**: `SPEC.md L33-L34, L128`.
  2. Mapping coverage of a Taiwan-leaning Chinese corpus must reach **≥ 95%** of known Mainland-leaning tokens.
     **Source**: `SPEC.md L34-L35`.
  3. The minimum required mapping set must include at least the 12 canonical example mappings: `視頻→影片`, `地鐵→捷運`, `垃圾→ㄌㄜˋ ㄙㄜˋ`, `菠蘿→鳳梨`, `程序員→工程師`, `軟件→軟體`, `硬件→硬體`, `和→ㄏㄢˋ`, `吧→啦`, `互聯網→網際網路`, `博客→部落格`, `網名→暱稱`.
     **Source**: `SPEC.md L37-L50`.
  4. Mapping is applied before SSML parsing and before chunking so that downstream stages see normalized text. **Source**: `SPEC.md L191-L195`.
  5. Mappings that yield Bopomofo (e.g., `垃圾`, `和`) must be emitted as the exact Bopomofo string with tone diacritics in the form `ㄌㄜˋ ㄙㄜˋ` (note the space-separated syllables). **Source**: `SPEC.md L41, L47`.

- **Implementation owner (file)**: `src/engines/taiwan_linguistic.py` (`SPEC.md L192`).

### FR-02: SSML 解析 (SSML parsing)
- **Description**: The system shall accept a subset of SSML in the `input` field of `SpeechRequest` and map each supported tag to a Kokoro-compatible behavior. Unsupported tags/attributes shall be ignored with a `warn` log rather than rejected.
  **Source**: `SPEC.md L52-L65`.

- **Acceptance criteria** (all testable, measurable):
  1. The parser must support the following tags with the indicated attributes: `<speak>` (root), `<break time="500ms">` (insert silence via padding character), `<prosody rate="0.9">` (map to Kokoro `speed`), `<emphasis level="strong|moderate">` (multiply `speed` by 1.1), `<voice name="xxx">` (switch voice), `<phoneme alphabet="ipa">` (pass through unchanged), `<say-as interpret-as="...">` (numeric-to-text conversion).
     **Source**: `SPEC.md L55-L63`.
  2. SSML comments `<!-- ... -->` must be removed from the rendered text. **Source**: `SPEC.md L63`.
  3. The attributes `pitch` and `volume` on `<prosody>` are **not supported by Kokoro** and must be ignored with a `warn` log; the request must still succeed.
     **Source**: `SPEC.md L65`.
  4. If the input cannot be parsed as valid SSML, the system must fall back to treating the input as plain text and log a `warn`; it must not return 4xx.
     **Source**: `SPEC.md L213`.
  5. The `<voice>` tag must cause a per-segment voice switch in the synthesized output. **Source**: `SPEC.md L60, L240`.

- **Implementation owner (file)**: `src/engines/ssml_parser.py` (`SPEC.md L193`).

### FR-03: 智能文本切分 (Intelligent text chunking)
- **Description**: The system shall split long input text into chunks of **≤ 250 characters** (per `MAX_CHARS_PER_REQUEST`) using a three-level recursive strategy that prefers sentence boundaries, then clause boundaries, then phrase boundaries. The chunking is mandated to preserve prosody stability.
  **Source**: `SPEC.md L67-L75`.

- **Acceptance criteria** (all testable, measurable):
  1. No chunk emitted by the splitter may exceed **250 characters** (the `MAX_CHARS_PER_REQUEST` constant, `SPEC.md L127`).
     **Source**: `SPEC.md L69, L127`.
  2. Optimal chunk length is in the range **100–250 characters**; the splitter should not produce many sub-100-char chunks for a typical prose input.
     **Source**: `SPEC.md L70`.
  3. Level-1 split is at sentence boundaries: `。`, `？`, `！`, `!`, `?`, `\n`. Level-2 split is at clause boundaries: `；`, `:` (only invoked if the segment is still > 100 chars). Level-3 split is at phrase boundaries: `，` (only invoked if the segment is still > 100 chars).
     **Source**: `SPEC.md L71-L74`.
  4. The splitter must **not** break in the middle of a mixed Chinese/English word. **Source**: `SPEC.md L75`.
  5. Inputs that are themselves ≤ 250 characters must be returned as a single chunk. **Source**: `SPEC.md L127`.

- **Implementation owner (file)**: `src/engines/text_splitter.py` (`SPEC.md L194`).

### FR-04: 並行合成 (Parallel synthesis)
- **Description**: When the input is split into N chunks, the system shall issue all N requests to the Kokoro backend concurrently using `httpx.AsyncClient`, then concatenate the returned MP3 byte streams **without re-encoding**.
  **Source**: `SPEC.md L77-L79`.

- **Acceptance criteria** (all testable, measurable):
  1. For an input split into N chunks, N `httpx.AsyncClient` requests shall be in-flight concurrently (verified via a test mock that asserts all coroutines were started before any awaited).
     **Source**: `SPEC.md L78`.
  2. Concatenation of MP3 byte streams must be done at the byte level — **no re-encoding** is performed. The resulting byte length must equal the sum of the input chunk byte lengths.
     **Source**: `SPEC.md L79`.
  3. The order of chunks in the output must match the order of chunks in the input (no shuffling). **Source**: `SPEC.md L67-L75` (implied by split ordering).
  4. If one chunk's request fails, the overall request must fail with HTTP 5xx and the circuit breaker counter must increment (see FR-05). **Source**: `SPEC.md L215`.

- **Implementation owner (file)**: `src/engines/synthesis.py` (`SPEC.md L195`).

### FR-05: 斷路器 (Circuit breaker)
- **Description**: The system shall wrap backend calls in a circuit breaker to prevent cascading failures. The breaker has three states — **Closed**, **Open**, **Half-Open** — and transitions based on failure counts and timeouts.
  **Source**: `SPEC.md L81-L85`.

- **Acceptance criteria** (all testable, measurable):
  1. When the consecutive-failure count reaches `CIRCUIT_BREAKER_THRESHOLD = 3` (`SPEC.md L130`), the breaker transitions from **Closed** to **Open**.
     **Source**: `SPEC.md L82, L130`.
  2. After being Open for `CIRCUIT_BREAKER_TIMEOUT = 10.0` seconds (`SPEC.md L131`), the breaker transitions to **Half-Open** and allows one probe request.
     **Source**: `SPEC.md L83, L131`.
  3. A successful probe in Half-Open transitions the breaker back to **Closed** and resets the failure counter. **Source**: `SPEC.md L84`.
  4. While the breaker is **Open**, subsequent requests must immediately return **HTTP 503** without contacting the backend. **Source**: `SPEC.md L83, L215`.
  5. The state must be observable via `GET /health/circuit` and resettable via `POST /health/circuit/reset`. **Source**: `SPEC.md L161-L162`.

- **Implementation owner (file)**: `src/middleware/circuit_breaker.py` (`SPEC.md L197`).

### FR-06: Redis 快取 (Redis cache, optional)
- **Description**: The system shall cache successful synthesis results in Redis, keyed by a hash of `(text, voice, speed)`, with a 24-hour TTL. The cache tier is **optional**: if Redis is unreachable, the proxy must continue to operate correctly without it.
  **Source**: `SPEC.md L86-L89`.

- **Acceptance criteria** (all testable, measurable):
  1. The cache key must be of the form `hash(text + voice + speed)`. **Source**: `SPEC.md L87`.
  2. The cache TTL must be **24 hours** (86400 seconds). **Source**: `SPEC.md L88`.
  3. A cache hit must return the previously stored audio bytes **without** contacting the Kokoro backend. **Source**: `SPEC.md L86-L88` (implied).
  4. If Redis is unreachable, the proxy must skip the cache step and proceed to the backend; this must be logged at `info` level and must not raise. **Source**: `SPEC.md L88-L89, L228-L229`.
  5. The cache module is implemented at `src/cache/redis_cache.py`; the absence of the `redis` package or a live Redis server must not break startup or tests. **Source**: `SPEC.md L198, L229`.

- **Implementation owner (file)**: `src/cache/redis_cache.py` (`SPEC.md L198`).

### FR-07: CLI 命令列工具 (Command-line tool)
- **Description**: The system shall ship a `tts-v610` CLI for batch and scriptable use. The CLI must support inline text, file input, voice selection, speed, output format, SSML, and a configurable backend URL.
  **Source**: `SPEC.md L91-L98`.

- **Acceptance criteria** (all testable, measurable):
  1. The CLI must support the following invocations verbatim:
     ```bash
     tts-v610 "你好世界" -o output.mp3
     tts-v610 -i input.txt -o output/
     tts-v610 "文字" -v "zf_xiaoxiao" -s 1.0 -f mp3
     tts-v610 --ssml "<speak>...</speak>" -o out.mp3
     tts-v610 --backend "http://localhost:8880" "text" -o out.mp3
     ```
     **Source**: `SPEC.md L92-L97`.
  2. `python -m src.cli --help` must exit 0 and print usage information. **Source**: `SPEC.md L237`.
  3. When `-i` is given a text file and `-o` is a directory, the CLI must write one output file per input line. **Source**: `SPEC.md L93`.
  4. The `--ssml` flag must route the input through the SSML parser (FR-02). **Source**: `SPEC.md L96`.
  5. The `--backend` flag must override the default `KOKORO_BACKEND_URL` for the duration of the call. **Source**: `SPEC.md L97, L123`.

- **Implementation owner (file)**: `src/cli.py` (`SPEC.md L187`).

### FR-08: ffmpeg 音訊格式轉換 (ffmpeg audio format conversion)
- **Description**: The system shall convert synthesized audio between **MP3** and **WAV** using the `ffmpeg` command-line tool invoked via `subprocess`.
  **Source**: `SPEC.md L100-L102`.

- **Acceptance criteria** (all testable, measurable):
  1. The conversion must support **MP3 → WAV** and **WAV → MP3** in both directions. **Source**: `SPEC.md L101`.
  2. ffmpeg must be invoked via Python's `subprocess` module — not a third-party Python binding. **Source**: `SPEC.md L102`.
  3. If the ffmpeg binary is not on `PATH`, conversion must fail with a clear error message; the service must continue to work for the other (already-supported) format. **Source**: `SPEC.md L228` (R3 mitigation).
  4. The conversion function must be implemented in `src/audio_converter.py`. **Source**: `SPEC.md L188`.

- **Implementation owner (file)**: `src/audio_converter.py` (`SPEC.md L188`).

---

## 4. Non-Functional Requirements

> All NFR targets in this section are taken **verbatim** from `SPEC.md §4, L108-L114`. The NFR IDs below are introduced here for traceability only; the underlying values are unchanged.

| ID | Category | Requirement | Target | Measurement method | Source |
|----|----------|-------------|--------|--------------------|--------|
| NFR-01 | Performance | Time to first byte (TTFB) | **< 300 ms** | Wall-clock from `SpeechRequest` received to first MP3 byte returned, measured on a warm proxy. Excludes network to Kokoro. | `SPEC.md L110` |
| NFR-02 | Linguistic coverage | LEXICON coverage of Mainland-leaning tokens | **≥ 80%** | Automated corpus test over a labeled Taiwan-news corpus; report the percentage of expected tokens that map. | `SPEC.md L111` |
| NFR-03 | Linguistic accuracy | Tone (變調) correctness | **≥ 95%** | Manual / A-B audit of synthesized output against expected tone sandhi. | `SPEC.md L112` |
| NFR-04 | Reliability | API availability | **≥ 99%** | 30-day rolling uptime of `GET /health` returning 200. | `SPEC.md L113` |
| NFR-05 | Reliability | Error recovery time | **< 10 s** | Wall-clock from backend-5xx detection to successful next request after circuit-breaker Half-Open probe. | `SPEC.md L114` |
| NFR-06 | Operability | Cold-start readiness | Warmup on launch | `WARMUP_ENABLED=True`; warmup text is `"你好，測試中"` (`SPEC.md L132-L133`). | `SPEC.md L132-L133` |
| NFR-07 | Robustness | Request timeout | 30.0 s | `REQUEST_TIMEOUT = 30.0` (`SPEC.md L129`); backend calls that exceed this must raise and increment the breaker counter. | `SPEC.md L129` |

**Notes**:
- The NFR-02 ≥ 80% threshold is the corpus coverage floor; FR-01 still requires the **mapping table** itself to be ≥ 50 entries with **per-token coverage** ≥ 95% on the test corpus. The two are distinct metrics and both must be satisfied.
- All NFRs are measurable through the existing 82 tests plus the operational metrics listed in the "Measurement method" column.

---

## 5. External Interface Requirements

### 5.1 HTTP API surface
- All endpoints are served by the FastAPI app started via `python -m src.main` (`SPEC.md L236`).

| Method | Path | Purpose | Success status | Source |
|--------|------|---------|----------------|--------|
| GET | `/health` | Liveness check | 200 | `SPEC.md L158` |
| GET | `/ready` | Readiness check (Kokoro backend reachable, breaker closed) | 200 / 503 | `SPEC.md L159` |
| GET | `/v1/proxy/voices` | List of available voices from the upstream Kokoro | 200 | `SPEC.md L160` |
| POST | `/v1/proxy/speech` | Synthesize speech from text or SSML | 200 (audio bytes) | `SPEC.md L161` |
| GET | `/health/circuit` | Report circuit-breaker state and counters | 200 | `SPEC.md L162` |
| POST | `/health/circuit/reset` | Force the circuit breaker back to Closed | 200 | `SPEC.md L163` |

### 5.2 `POST /v1/proxy/speech` request schema
```json
{
  "model": "tts-1",
  "input": "文字或 SSML",
  "voice": "zf_xiaoxiao",
  "speed": 1.0,
  "response_format": "mp3"
}
```
**Source**: `SPEC.md L167-L175`.

Field constraints (derived from SPEC and FRs):
- `model`: One of `"tts-1"`, `"tts-1-hd"`, `"kokoro"`, `"custom-gentle"`. Maps via `MODEL_MAP` (`SPEC.md L135-L141`).
- `input`: Non-empty string, ≤ 8000 chars (`SPEC.md L217`); may contain SSML (`SPEC.md L171`).
- `voice`: Defaults to `"zf_xiaoxiao"` (`SPEC.md L125`); must be a valid upstream voice or HTTP 400 (`SPEC.md L218`).
- `speed`: Float, default `1.0` (`SPEC.md L126`).
- `response_format`: `"mp3"` (default) or `"wav"` (`SPEC.md L173`).

### 5.3 Response (success)
- HTTP 200 with `Content-Type: audio/mpeg` (MP3) or `audio/wav` (WAV).
- Body is the raw audio byte stream, either produced by single-shot synthesis (input ≤ 250 chars) or by concatenation of N chunks (input > 250 chars, FR-04).

### 5.4 CLI interface
- See FR-07 acceptance criteria for the exact invocation grammar (`SPEC.md L92-L97`).

### 5.5 Upstream interface
- The proxy speaks HTTP/1.1 to the Kokoro-82M Docker backend at `http://localhost:8880/v1`:
  - `POST http://localhost:8880/v1/audio/speech` (synthesize; `SPEC.md L123`)
  - `GET  http://localhost:8880/v1/audio/voices` (list voices; `SPEC.md L124`)
- Voice binaries (when needed) are fetched via `curl` to work around Python SSL issues (`SPEC.md L24`).

---

## 6. Data Model / Configuration

### 6.1 `src/config.py` constants (verbatim from `SPEC.md §5.1, L122-L141`)

| Constant | Value | Purpose | Source |
|----------|-------|---------|--------|
| `KOKORO_BACKEND_URL` | `"http://localhost:8880/v1/audio/speech"` | Kokoro synthesis endpoint | `SPEC.md L123` |
| `KOKORO_VOICES_URL` | `"http://localhost:8880/v1/audio/voices"` | Kokoro voice-list endpoint | `SPEC.md L124` |
| `DEFAULT_VOICE` | `"zf_xiaoxiao"` | Default voice for `SpeechRequest` | `SPEC.md L125` |
| `DEFAULT_SPEED` | `1.0` | Default `speed` for `SpeechRequest` | `SPEC.md L126` |
| `MAX_CHARS_PER_REQUEST` | `250` | Hard chunk cap (FR-03) | `SPEC.md L127` |
| `LEXICON_MIN_SIZE` | `50` | Minimum LEXICON entries (FR-01) | `SPEC.md L128` |
| `REQUEST_TIMEOUT` | `30.0` | Per-request timeout (s) | `SPEC.md L129` |
| `CIRCUIT_BREAKER_THRESHOLD` | `3` | Failure-count threshold (FR-05) | `SPEC.md L130` |
| `CIRCUIT_BREAKER_TIMEOUT` | `10.0` | Open → Half-Open delay (s) (FR-05) | `SPEC.md L131` |
| `WARMUP_ENABLED` | `True` | Run warmup on launch | `SPEC.md L132` |
| `WARMUP_TEXT` | `"你好，測試中"` | Warmup phrase | `SPEC.md L133` |

### 6.2 `MODEL_MAP` (verbatim from `SPEC.md §5.1, L135-L141`)
```python
MODEL_MAP = {
    "tts-1":         "kokoro",
    "tts-1-hd":      "kokoro",
    "kokoro":        "kokoro",
    "custom-gentle": "zf_xiaoxiao(0.8)+af_heart(0.2)",
}
```

### 6.3 Persona presets (verbatim from `SPEC.md §5.2, L145-L150`)

| Persona | Voice recipe | Speed range | Application |
|---------|--------------|-------------|-------------|
| 極致溫柔助理 | `zf_xiaoxiao(0.8)+af_heart(0.2)` | 0.85 – 0.95 | 睡前故事 |
| 親切智慧導遊 | `zf_xiaoxiao(0.7)+af_sky(0.3)` | 0.9 – 1.0 | 展場導覽 |
| 現代幹練秘書 | `zf_yunxi(0.8)+af_nicole(0.2)` | 1.0 – 1.1 | 行事曆提醒 |
| 甜美親和主播 | `zf_xiaoyi(0.6)+zf_xiaoxiao(0.4)` | 1.0 – 1.1 | 新聞摘要 |

**Source**: `SPEC.md L145-L150`.

### 6.4 Pydantic models
- Pydantic models live in `src/models.py` (`SPEC.md L186`) and define the `SpeechRequest` schema shown in §5.2.

### 6.5 Folder structure (verbatim from `SPEC.md §7, L181-L205`)
```
kokoro-taiwan-proxy/
├── src/
│   ├── main.py                   # FastAPI 應用（暖機、路由）
│   ├── config.py                 # 集中設定（MAX_CHARS=250）
│   ├── models.py                 # Pydantic 模型
│   ├── cli.py                    # CLI 工具（FR-07）
│   ├── audio_converter.py        # ffmpeg 轉換（FR-08）
│   ├── routers/
│   │   └── speech.py             # /v1/proxy/speech 端點
│   ├── engines/
│   │   ├── taiwan_linguistic.py  # LEXICON 74+ 詞（FR-01）
│   │   ├── ssml_parser.py        # SSML + <voice>（FR-02）
│   │   ├── text_splitter.py      # 三級切分 ≤250（FR-03）
│   │   └── synthesis.py          # 並行合成（FR-04）
│   ├── middleware/
│   │   └── circuit_breaker.py   # 斷路器（FR-05）
│   └── cache/
│       └── redis_cache.py        # Redis 快取（FR-06，可選）
├── tests/                        # 82 個測試
├── CONTROL_GROUP.md              # 對照組定位文件
├── README.md                     # 啟動說明
├── SPEC.md                       # 本文件（單一事實來源）
└── requirements.txt
```

---

## 7. Error Handling

> The error-handling table below is taken **verbatim** from `SPEC.md §8, L210-L219`.

| Situation | Response | HTTP status | Source |
|-----------|----------|-------------|--------|
| SSML parse failure | Fallback to plain-text treatment; log at `warn` level | 200 (success path) | `SPEC.md L213` |
| Backend 5xx | Increment circuit-breaker failure counter | n/a (internal) → eventual 503 | `SPEC.md L214, L83` |
| Circuit breaker Open | Immediate refusal | **HTTP 503** | `SPEC.md L215` |
| Empty input | Reject | **HTTP 400** | `SPEC.md L216` |
| Input too long (> 8000 chars) | Reject | **HTTP 400** | `SPEC.md L217` |
| Invalid voice | Reject | **HTTP 400** | `SPEC.md L218` |

**Error-handling rules (derived from FR-05)**:
- A 5xx from the Kokoro backend causes the failure counter to increment (`SPEC.md L214`).
- When the counter reaches `CIRCUIT_BREAKER_THRESHOLD = 3` the breaker opens, and subsequent requests are answered with **HTTP 503** without contacting the backend (`SPEC.md L82-L83, L130, L215`).
- After `CIRCUIT_BREAKER_TIMEOUT = 10.0` seconds the breaker enters Half-Open and admits one probe (`SPEC.md L83, L131`). A successful probe closes the breaker (`SPEC.md L84`).

---

## 8. Risks

> The risk matrix below is reproduced **verbatim** from `SPEC.md §9, L222-L229`.

| ID | Risk | Impact | Likelihood | Mitigation | Source |
|----|------|--------|------------|------------|--------|
| R1 | Kokoro Docker crashes | 高 (High) | 低 (Low) | Circuit breaker + clear error messages | `SPEC.md L226` |
| R2 | Connection drop | 中 (Medium) | 中 (Medium) | Retry 3 times + retry handler | `SPEC.md L227` |
| R3 | ffmpeg missing | 中 (Medium) | 低 (Low) | Declared as required dependency | `SPEC.md L228` |
| R4 | Redis unreachable | 低 (Low) | 低 (Low) | Optional decorator; skip when absent | `SPEC.md L229` |

**Risk → requirement traceability**:
- R1 is mitigated by FR-05 (circuit breaker) and the 503 fast-fail response in §7 (`SPEC.md L215`).
- R2 is mitigated by a retry handler (3 attempts) layered on top of FR-05 — the retry counter feeds the breaker threshold (`SPEC.md L130`).
- R3 is mitigated by `requirements.txt` + README guidance, plus the ffmpeg-abstraction in `src/audio_converter.py` (`SPEC.md L188, L228`).
- R4 is mitigated by FR-06's optional Redis tier and the "skip on absent" behavior in `src/cache/redis_cache.py` (`SPEC.md L88-L89, L198, L229`).

---

## 9. Acceptance Criteria

> The acceptance benchmark below is reproduced **verbatim** from `SPEC.md §10, L233-L243`. Every box is the contractual bar for delivery and methodology reviewers will check them in order.

- [x] `pytest tests/ -v` → 82/82 通過
- [x] `python -m src.main` → 啟動成功
- [x] `python -m src.cli --help` → CLI 正常運行
- [x] LEXICON 詞彙 ≥ 50
- [x] Chunk 上限 ≤ 250 字
- [x] SSML `<voice>` 標籤支援
- [x] ffmpeg MP3/WAV 轉換
- [x] 包含 `CONTROL_GROUP.md`
- [x] `CONTROL_GROUP.md` 已上傳 GitHub

**Source**: `SPEC.md L235-L243`.

### 9.1 Cross-reference: acceptance checks → FRs / NFRs
| Acceptance check | Satisfies | Source |
|------------------|-----------|--------|
| `pytest tests/ -v` → 82/82 pass | All FRs (covered by tests); NFR-01..NFR-05 (covered by perf/reliability tests) | `SPEC.md L200, L235` |
| `python -m src.main` starts | FR-04, FR-05, FR-06 (warmup, breaker init) | `SPEC.md L132-L133, L236` |
| `python -m src.cli --help` | FR-07 | `SPEC.md L92-L97, L237` |
| LEXICON ≥ 50 | FR-01 | `SPEC.md L33-L34, L128, L238` |
| Chunk ≤ 250 | FR-03 | `SPEC.md L69, L127, L239` |
| SSML `<voice>` support | FR-02 | `SPEC.md L60, L240` |
| ffmpeg MP3/WAV | FR-08 | `SPEC.md L100-L103, L241` |
| `CONTROL_GROUP.md` present | Control-group positioning artifact | `SPEC.md L201, L242` |
| `CONTROL_GROUP.md` on GitHub | Methodology-v2 baseline publication | `SPEC.md L243` |

---

## 10. Traceability appendix

> A short, non-normative cross-reference to assist downstream phases (P2–P8). All rows cite `SPEC.md` line numbers.

| Spec block | Where in this SRS |
|------------|-------------------|
| SPEC §1 Overview (L7-L14) | §1.1, §1.2, §1.3 |
| SPEC §2 Tech stack (L18-L26) | §2.3, §2.4 |
| SPEC §3 FR-01 (L32-L51) | §3 FR-01 |
| SPEC §3 FR-02 (L52-L65) | §3 FR-02 |
| SPEC §3 FR-03 (L67-L75) | §3 FR-03 |
| SPEC §3 FR-04 (L77-L79) | §3 FR-04 |
| SPEC §3 FR-05 (L81-L85) | §3 FR-05 |
| SPEC §3 FR-06 (L86-L89) | §3 FR-06 |
| SPEC §3 FR-07 (L91-L98) | §3 FR-07 |
| SPEC §3 FR-08 (L100-L102) | §3 FR-08 |
| SPEC §4 NFRs (L108-L114) | §4 NFR-01..NFR-07 |
| SPEC §5.1 config (L122-L141) | §6.1, §6.2 |
| SPEC §5.2 personas (L145-L150) | §6.3 |
| SPEC §6 endpoints (L155-L175) | §5.1, §5.2, §5.3 |
| SPEC §7 folder structure (L181-L205) | §6.5 |
| SPEC §8 errors (L210-L219) | §7 |
| SPEC §9 risks (L222-L229) | §8 |
| SPEC §10 acceptance (L233-L243) | §9 |
| SPEC §11 prohibitions (L247-L254) | §2.4 (verbatim) |

---

*End of SRS — Kokoro Taiwan Proxy — v1.0 derived from SPEC.md v1.0.0-control (2026-03-31).*
