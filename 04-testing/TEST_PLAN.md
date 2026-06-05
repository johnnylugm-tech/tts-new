# Test Plan — Kokoro Taiwan Proxy

> **Phase**: 4 — Testing
> **Version**: 1.0.0
> **Date**: 2026-06-05
> **Project**: tts-new (control group — methodology-v2 experiment)
> **Source authority**: SRS.md §3 FR-01..FR-08, §4 NFR-01..NFR-08; TEST_SPEC.md (82 test cases)

---

## 1. Scope

This plan covers functional and non-functional verification of all 8 FRs implemented in Phase 3. Each FR section lists test case IDs (mapped to TEST_SPEC.md), test categories (positive / negative / boundary / edge), and pass criteria derived from SRS.md acceptance criteria.

**Out of scope**: load testing, production deployment, Kokoro Docker backend integration tests against a live instance.

---

## 2. Test Environment

| Item | Requirement |
|------|-------------|
| Python | 3.9+ |
| Test runner | `pytest 8.x` with `pytest-cov`, `pytest-asyncio` |
| Coverage target | 100% (enforced via `--cov-fail-under=100`) |
| ffmpeg | ≥ 5.x on PATH (required for FR-08 WAV tests) |
| Redis | Optional; tests mock the Redis client |
| Mutation testing | `mutmut` (Gate 2 baseline established in P3) |

---

## 3. FR Test Cases

### FR-01: Taiwan-Chinese Vocabulary Mapping

**Implementation**: `src/engines/taiwan_linguistic.py`
**SRS acceptance criteria**: SRS.md §3 FR-01 AC1–AC5

| TC-ID | Category | Description | Input | Expected |
|-------|----------|-------------|-------|----------|
| TC-01-P1 | Positive | LEXICON size meets minimum | `len(LEXICON)` | ≥ 50 |
| TC-01-P2 | Positive | 視頻→影片 mapping | `"視頻教學"` | `"影片教學"` |
| TC-01-P3 | Positive | 地鐵→捷運 mapping | `"搭地鐵上班"` | `"搭捷運上班"` |
| TC-01-P4 | Positive | 垃圾→ㄌㄜˋ ㄙㄜˋ (Bopomofo) | `"倒垃圾"` | `"倒ㄌㄜˋ ㄙㄜˋ"` |
| TC-01-P5 | Positive | 和→ㄏㄢˋ (Bopomofo) | `"他和她"` | `"他ㄏㄢˋ她"` |
| TC-01-P6 | Positive | 菠蘿→鳳梨 | `"菠蘿口味"` | `"鳳梨口味"` |
| TC-01-P7 | Positive | 程序員→工程師 | `"程序員招募"` | `"工程師招募"` |
| TC-01-P8 | Positive | 軟件→軟體, 硬件→硬體 | `"軟件和硬件"` | `"軟體和硬體"` |
| TC-01-P9 | Positive | 互聯網→網際網路 | `"互聯網公司"` | `"網際網路公司"` |
| TC-01-P10 | Positive | 博客→部落格, 網名→暱稱 | `"博客網名"` | `"部落格暱稱"` |
| TC-01-N1 | Negative | Text with no mapped tokens passes unchanged | `"你好世界"` | `"你好世界"` |
| TC-01-E1 | Edge | Empty string input | `""` | `""` |
| TC-01-E2 | Edge | Mixed mapped and unmapped tokens | `"地鐵和公車"` | `"捷運和公車"` |

**Pass criterion**: All 12 canonical mappings present; `len(LEXICON) >= 50`; Bopomofo tokens are space-separated syllables with tone diacritics.

---

### FR-02: SSML Parsing

**Implementation**: `src/engines/ssml_parser.py`
**SRS acceptance criteria**: SRS.md §3 FR-02 AC1–AC5

| TC-ID | Category | Description | Input | Expected |
|-------|----------|-------------|-------|----------|
| TC-02-P1 | Positive | `<speak>` root wrapper stripped | `<speak>hello</speak>` | plain_text=`"hello"` |
| TC-02-P2 | Positive | `<break time="500ms">` adds pause | `<speak>hi<break time="500ms"/>there</speak>` | text contains pause |
| TC-02-P3 | Positive | `<prosody rate="0.9">` lowers speed | `<speak><prosody rate="0.9">text</prosody></speak>` | speed=0.9 |
| TC-02-P4 | Positive | `<emphasis level="strong">` multiplies speed | `<speak><emphasis level="strong">text</emphasis></speak>` | speed multiplied |
| TC-02-P5 | Positive | `<voice name="af_heart">` switches voice | `<speak><voice name="af_heart">text</voice></speak>` | voice=`"af_heart"` |
| TC-02-P6 | Positive | SSML comments removed | `<speak><!-- comment -->text</speak>` | comment absent |
| TC-02-N1 | Negative | `<prosody pitch>` ignored with warn, request succeeds | `<speak><prosody pitch="+1st">text</prosody></speak>` | warnings non-empty, no exception |
| TC-02-N2 | Negative | `<prosody volume>` ignored with warn | `<speak><prosody volume="loud">text</prosody></speak>` | warnings non-empty |
| TC-02-N3 | Negative | Invalid SSML falls back to plain text | `<unclosed tag` | plain_text = raw input; warnings non-empty |
| TC-02-E1 | Edge | Empty `<speak>` | `<speak></speak>` | plain_text=`""` |
| TC-02-E2 | Edge | Nested `<emphasis>` | `<speak><emphasis level="moderate">a</emphasis></speak>` | speed multiplied; no exception |

**Pass criterion**: Supported tags processed; unsupported attrs logged as warnings; malformed SSML falls back to plain text without 4xx.

---

### FR-03: Intelligent Text Chunking

**Implementation**: `src/engines/text_splitter.py`
**SRS acceptance criteria**: SRS.md §3 FR-03 AC1–AC5

| TC-ID | Category | Description | Input | Expected |
|-------|----------|-------------|-------|----------|
| TC-03-P1 | Positive | Input ≤ 250 chars returns single chunk | 200-char string | 1 chunk |
| TC-03-P2 | Positive | L1 split at `。` | `"第一句。第二句。"` (>250) | chunks at sentence boundaries |
| TC-03-P3 | Positive | L1 split at `\n` | `"line1\nline2\n"` (>250) | chunks at newlines |
| TC-03-P4 | Positive | L2 split at `；` when L1 segment >100 | long clause-separated text | chunks at clause boundaries |
| TC-03-P5 | Positive | L3 split at `，` when L2 segment >100 | long comma-separated text | chunks at comma boundaries |
| TC-03-B1 | Boundary | Exactly 250-char input | 250-char string | 1 chunk |
| TC-03-B2 | Boundary | 251-char input triggers split | 251-char string | ≥2 chunks, each ≤250 |
| TC-03-N1 | Negative | No chunk exceeds 250 chars | arbitrary long text | all `len(c) <= 250` |
| TC-03-E1 | Edge | Empty string | `""` | `[]` or `[""]` |
| TC-03-E2 | Edge | Mixed CJK+Latin never split mid-word | `"用Python寫程式"` (short) | single chunk, not mid-word |

**Pass criterion**: All chunks ≤ 250 chars; split at correct boundaries in priority order.

---

### FR-04: Parallel Synthesis

**Implementation**: `src/engines/synthesis.py`
**SRS acceptance criteria**: SRS.md §3 FR-04 AC1–AC4

| TC-ID | Category | Description | Input | Expected |
|-------|----------|-------------|-------|----------|
| TC-04-P1 | Positive | N chunks → N concurrent requests | 3 chunks | mock called 3× concurrently |
| TC-04-P2 | Positive | Output byte length = sum of chunks | 3 chunks of 10B each | output 30B |
| TC-04-P3 | Positive | Output order matches input order | chunks [A, B, C] | result = A+B+C |
| TC-04-P4 | Positive | Single chunk returns raw bytes | 1 chunk | bytes unchanged |
| TC-04-N1 | Negative | One chunk fail → overall HTTP 5xx | 1 of 3 chunks raises | exception propagated |
| TC-04-N2 | Negative | Empty chunks list raises ValueError | `[]` | `ValueError` |
| TC-04-E1 | Edge | Semaphore limits to MAX_CONCURRENT_SYNTHESIS | 20 chunks | ≤8 in-flight at once |

**Pass criterion**: Parallel dispatch verified; byte-level concat (no re-encoding); ordering preserved.

---

### FR-05: Circuit Breaker

**Implementation**: `src/middleware/circuit_breaker.py`
**SRS acceptance criteria**: SRS.md §3 FR-05 AC1–AC5

| TC-ID | Category | Description | Input | Expected |
|-------|----------|-------------|-------|----------|
| TC-05-P1 | Positive | 3 consecutive failures → OPEN | 3 failures | state=OPEN |
| TC-05-P2 | Positive | OPEN after timeout → HALF-OPEN | wait > timeout | state=HALF_OPEN |
| TC-05-P3 | Positive | Successful probe → CLOSED, counter reset | success in HALF-OPEN | state=CLOSED, failures=0 |
| TC-05-P4 | Positive | Failed probe in HALF-OPEN → back to OPEN | failure in HALF-OPEN | state=OPEN |
| TC-05-N1 | Negative | OPEN breaker returns HTTP 503 immediately | request while OPEN | `CircuitOpenError` raised |
| TC-05-N2 | Negative | Only 1 probe allowed in HALF-OPEN | 2 concurrent probes | second queued/blocked |
| TC-05-E1 | Edge | 2 failures then success resets counter | 2 fail, 1 success | failures=0, state=CLOSED |
| TC-05-E2 | Edge | `/health/circuit` returns state JSON | GET /health/circuit | `{"state": "CLOSED", ...}` |

**Pass criterion**: FSM transitions correct at threshold=3, timeout=10.0s; OPEN returns `CircuitOpenError` without backend call.

---

### FR-06: Redis Cache

**Implementation**: `src/cache/redis_cache.py`
**SRS acceptance criteria**: SRS.md §3 FR-06 AC1–AC5

| TC-ID | Category | Description | Input | Expected |
|-------|----------|-------------|-------|----------|
| TC-06-P1 | Positive | Cache key is SHA-256 of `text+voice+speed` | same params twice | same cache key |
| TC-06-P2 | Positive | Cache hit avoids backend call | cached value | audio from cache, no backend |
| TC-06-P3 | Positive | Cache miss proceeds to backend and stores | new key | stored with TTL=86400 |
| TC-06-P4 | Positive | TTL is 86400 seconds | `setex` call | TTL=86400 |
| TC-06-N1 | Negative | Redis unavailable → skip cache, no raise | `client=None` | no exception, proceeds |
| TC-06-N2 | Negative | Redis error during set marks unavailable | `setex` raises | `is_available()` → False |
| TC-06-E1 | Edge | Different speeds produce different keys | speed=1.0 vs 1.1 | different keys |
| TC-06-E2 | Edge | Missing `redis` package → graceful fallback | no redis package | no `ImportError` at startup |

**Pass criterion**: SHA-256 keying; TTL=86400; graceful no-Redis fallback; `setex` failure marks unavailable.

---

### FR-07: CLI Command-Line Tool

**Implementation**: `src/cli.py`
**SRS acceptance criteria**: SRS.md §3 FR-07 AC1–AC5

| TC-ID | Category | Description | Input | Expected |
|-------|----------|-------------|-------|----------|
| TC-07-P1 | Positive | Inline text synthesis | `tts-v610 "text" -o out.mp3` | returns 0, file written |
| TC-07-P2 | Positive | File input to directory | `tts-v610 -i input.txt -o output/` | one file per input line |
| TC-07-P3 | Positive | Voice and speed flags | `-v zf_xiaoxiao -s 1.0 -f mp3` | params forwarded |
| TC-07-P4 | Positive | `--ssml` routes through SSML parser | `--ssml "<speak>...</speak>"` | parsed, not raw |
| TC-07-P5 | Positive | `--backend` overrides default URL | `--backend http://alt:8880` | correct URL used |
| TC-07-P6 | Positive | `--help` exits 0 | `--help` | exit code 0 |
| TC-07-N1 | Negative | No text and no `--input-file` → exit 0 (no-op) | no text arg | exit 0 |
| TC-07-E1 | Edge | `-f wav` format flag | `-f wav` | format=wav passed |

**Pass criterion**: All 5 SPEC.md L92-L97 invocation patterns supported; `--help` exits 0.

---

### FR-08: ffmpeg Audio Format Conversion

**Implementation**: `src/audio_converter.py`
**SRS acceptance criteria**: SRS.md §3 FR-08 AC1–AC4

| TC-ID | Category | Description | Input | Expected |
|-------|----------|-------------|-------|----------|
| TC-08-P1 | Positive | MP3 → WAV conversion | valid MP3 bytes | WAV bytes returned |
| TC-08-P2 | Positive | WAV → MP3 conversion | valid WAV bytes | MP3 bytes returned |
| TC-08-P3 | Positive | subprocess invocation (not binding) | conversion call | `subprocess.run` used |
| TC-08-N1 | Negative | ffmpeg not on PATH → `FFmpegUnavailableError` | `PATH` without ffmpeg | `FFmpegUnavailableError` raised |
| TC-08-N2 | Negative | per-call `shutil.which` check (no cache) | call after PATH change | fresh check each call |
| TC-08-N3 | Negative | HTTP 500 when ffmpeg unavailable for WAV request | WAV request, no ffmpeg | HTTP 500 response |
| TC-08-N4 | Negative | Conversion failure raises `ConversionError` | corrupt input | `ConversionError` raised |
| TC-08-E1 | Edge | `FFmpegUnavailableError` is subclass of `ConversionError` | `isinstance` check | True |
| TC-08-E2 | Edge | Temp files cleaned up after success | conversion | no temp files left |
| TC-08-E3 | Edge | Temp files cleaned up after failure | conversion fail | no temp files left |

**Pass criterion**: Both conversion directions work; per-call PATH check (no cache); `FFmpegUnavailableError` → HTTP 500; temp file cleanup always runs.

---

## 4. NFR Coverage

| NFR-ID | Measurement | Test approach |
|--------|-------------|---------------|
| NFR-01 | TTFB < 300ms | Mocked backend; assert wall-clock from request to first byte |
| NFR-02 | LEXICON coverage ≥ 80% | `len(LEXICON) >= 50`; AC1 token coverage on corpus |
| NFR-03 | Tone sandhi ≥ 95% | Manual A-B audit (CONTROL_GROUP.md rubric) |
| NFR-04 | Availability ≥ 99% | `/health` endpoint always returns 200 in test |
| NFR-05 | Recovery < 10s | `CIRCUIT_BREAKER_TIMEOUT = 10.0` asserted in tests |
| NFR-06 | Cold-start warmup | `WARMUP_ENABLED=True` config asserted |
| NFR-07 | Timeout 30s | `REQUEST_TIMEOUT = 30.0` asserted |
| NFR-08 | Input validation | Empty input → 400; >8000 chars → 400; invalid voice → 400 |

---

## 5. Pass Criteria Summary

| Dimension | Threshold | Measurement |
|-----------|-----------|-------------|
| All 82 baseline tests | 100% pass | `pytest tests/ -q` |
| Code coverage | 100% | `--cov-fail-under=100` |
| Mutation kill rate | ≥ 70% | `mutmut run` (Gate 2 baseline) |
| Linting | ≥ 90 | `ruff check .` |
| Type safety | ≥ 85 | `pyright src/` |

---

## 6. Traceability

All test case IDs above map to TEST_SPEC.md test cases and SRS.md acceptance criteria. Traceability matrix is auto-generated by the harness at `build-trace-attestation`.

**Citations**:
- SRS.md §3 FR-01..FR-08 acceptance criteria
- SPEC.md L32-L103, L127-L133
- TEST_SPEC.md (82 canonical test cases)
- SAD.md §3.4, §6.2 (module map)
