"""
Round 3: Rewrite SAD.md section 9 SAB block to use HTML-marker + YAML format
expected by harness/core/quality_gate/sab_parser.py.
"""
from pathlib import Path

SAD_PATH = Path("/Users/johnny/projects/tts-new/02-architecture/SAD.md")

# The new section 9 content (replaces the old JSON code fence)
NEW_SECTION_9 = '''## §9 SAB Block (Machine-Readable)

This block is the machine-readable Software Architecture Baseline (SAB) consumed by the
harness via `harness/core/quality_gate/sab_parser.py`. The block is delimited by
`<!-- SAB:START -->` / `<!-- SAB:END -->` HTML comments and contains a YAML document
whose root key is `sab:` (the parser also accepts the legacy root-data form). All 14
SABSpec dataclass fields are present.

<!-- SAB:START -->
```yaml
sab:
  version: "1.0.0"
  created_at: "2026-06-04"
  phase: 2
  project: "kokoro-taiwan-proxy"
  layers:
    - name: "presentation"
      modules: ["src/main.py", "src/routers/speech.py", "src/cli.py"]
      responsibility: "HTTP/CLI entry; FastAPI app + argparse CLI"
    - name: "business"
      modules: ["src/engines/taiwan_linguistic.py", "src/engines/ssml_parser.py", "src/engines/text_splitter.py", "src/engines/synthesis.py", "src/middleware/circuit_breaker.py", "src/audio_converter.py"]
      responsibility: "TTS transformation; LEXICON, SSML, chunking, synthesis, breaker, ffmpeg wrapper"
    - name: "infrastructure"
      modules: ["src/config.py", "src/models.py", "src/cache/redis_cache.py"]
      responsibility: "Config (env-bound), Pydantic schemas, optional Redis cache"
  allowed_dependencies:
    - from: "presentation"
      to: "business"
    - from: "presentation"
      to: "infrastructure"
    - from: "business"
      to: "infrastructure"
  quality_targets:
    latency_p50_ms: 300
    latency_p95_ms: 800
    availability_pct: 99.0
    lexicon_min_size: 50
    chunk_max_chars: 250
    test_coverage_pct: 100
    test_coverage_pct_note: "100% refers to FR-coverage (all 8 FRs have >=1 test case in TEST_SPEC.md), NOT line coverage"
    required_p2_design_decisions: 6
    nfr_compliance_required: ["NFR-01","NFR-02","NFR-03","NFR-04","NFR-05","NFR-06","NFR-07","NFR-08"]
  nfr_dimension_mapping:
    NFR-01: "correctness"
    NFR-02: "correctness"
    NFR-03: "correctness"
    NFR-04: "operability"
    NFR-05: "correctness"
    NFR-06: "operability"
    NFR-07: "correctness"
    NFR-08: "security"
  nfr_traceability:
    NFR-01:
      type: "latency"
      module: "src/main.py + src/engines/synthesis.py"
      test_file: "tests/test_fr01_perf.py"
      verification: "p50 < 300ms on warm proxy (excludes Kokoro backend network)"
    NFR-02:
      type: "coverage"
      module: "src/engines/taiwan_linguistic.py"
      test_file: "tests/test_fr_01_lexicon_coverage.py"
      verification: "parametrize over LEXICON entries; >=80% coverage on labeled corpus"
      open_question: "Reference corpus not yet named (deferred to P3 - methodology-v2 reviewer must name a corpus like a labeled Taiwan-news sample set before NFR-02 acceptance can move to MET)"
    NFR-03:
      type: "accuracy"
      module: "src/engines/taiwan_linguistic.py"
      test_file: "tests/test_fr_01_tone_sandhi.py"
      verification: "manual A-B audit rubric in CONTROL_GROUP.md (P3) with fixed sample size; >=95% tone sandhi correctness"
    NFR-04:
      type: "availability"
      module: "src/main.py"
      test_file: "N/A - operational SLA"
      verification: "30-day rolling availability of GET /health returning 200; methodology-v2 owner; out-of-scope for proxy implementation"
    NFR-05:
      type: "recovery_time"
      module: "src/middleware/circuit_breaker.py"
      test_file: "tests/test_fr_05_circuit_breaker.py"
      verification: "Half-Open probe after CIRCUIT_BREAKER_TIMEOUT=10s; recovery time < 10s"
    NFR-06:
      type: "warmup"
      module: "src/main.py"
      test_file: "tests/test_warmup.py"
      verification: "WARMUP_ENABLED=True; WARMUP_TEXT='ni-hao, ce-shi-zhong'; on-launch warmup call"
    NFR-07:
      type: "timeout"
      module: "src/config.py + src/middleware/circuit_breaker.py"
      test_file: "tests/test_fr_05_timeout.py"
      verification: "REQUEST_TIMEOUT=30.0; on overrun, breaker counter incremented"
    NFR-08:
      type: "security"
      module: "src/routers/speech.py + src/models.py + src/config.py + structured logger"
      test_file: "tests distributed across test_fr_01..08.py"
      verification: "input validation on SpeechRequest fields; secrets via env vars only; TLS deferred to reverse proxy; no PII in logs (allow-list sanitizer)"
  advisory_only: []
  gate_score_overrides:
    correctness: 100
    security: 100
  fr_module_traceability:
    FR-01:
      module: "src/engines/taiwan_linguistic.py"
      spec: "SPEC.md L33-L34, L128"
      test: "tests/test_fr_01_taiwan_linguistic.py"
    FR-02:
      module: "src/engines/ssml_parser.py"
      spec: "SPEC.md L37-L50, L193"
      test: "tests/test_fr_02_ssml_parser.py"
    FR-03:
      module: "src/engines/text_splitter.py"
      spec: "SPEC.md L52-L74, L194"
      test: "tests/test_fr_03_text_splitter.py + tests/test_fr_03_text_splitter_edge_cases.py"
    FR-04:
      module: "src/engines/synthesis.py"
      spec: "SPEC.md L77-L79, L195"
      test: "tests/test_fr_04_synthesis.py + tests/test_fr_04_synthesis_concat.py"
    FR-05:
      module: "src/middleware/circuit_breaker.py"
      spec: "SPEC.md L81-L85, L197"
      test: "tests/test_fr_05_circuit_breaker.py"
    FR-06:
      module: "src/cache/redis_cache.py"
      spec: "SPEC.md L86-L89, L198"
      test: "tests/test_fr_06_redis_cache.py"
    FR-07:
      module: "src/cli.py"
      spec: "SPEC.md L92-L97, L187"
      test: "tests/test_fr_07_cli.py"
    FR-08:
      module: "src/audio_converter.py"
      spec: "SPEC.md L100-L102, L188"
      test: "tests/test_fr_08_audio_converter.py"
  architecture_constraints:
    - "No new tech stack (FastAPI + httpx + uvicorn + Kokoro Docker + optional Redis + ffmpeg only)"
    - "No core algorithm changes (FR-01..FR-08 logic is immutable)"
    - "No test deletion or modification (82 tests must remain green)"
    - "No coverage reduction"
    - "Feature freeze: bug fix only"
    - "FR-04 partial-success mode WAIVED for control-group scope (P2-DD-6)"
    - "FR-08 ffmpeg-missing: per-call check, FFmpegUnavailableError -> HTTP 500 (P2-DD-4)"
    - "NFR-08 log sanitization: allow-list of safe keys, deny-by-default (P2-DD-5)"
  high_risk_modules:
    - module: "src/engines/synthesis.py"
      risk: "Parallel httpx dispatch + byte-level MP3 concat; P3 must verify no re-encoding"
    - module: "src/middleware/circuit_breaker.py"
      risk: "In-process state; each worker has independent state; P3 must verify Half-Open probe correctness"
    - module: "src/audio_converter.py"
      risk: "Subprocess call to ffmpeg; P3 must verify timeout handling and missing-binary behavior"
    - module: "src/cache/redis_cache.py"
      risk: "Optional dependency; P3 must verify graceful no-Redis fallback"
```
<!-- SAB:END -->
'''

# Read current file
content = SAD_PATH.read_text(encoding="utf-8")
lines = content.splitlines(keepends=False)

# Section 9 boundaries (1-indexed): 847 to 1151 inclusive
# In 0-indexed python: 846 to 1150 inclusive
START = 847
END = 1151

# Sanity check
assert lines[START-1].startswith("## §9 SAB Block"), f"Expected section 9 header at line {START}, got: {lines[START-1]!r}"
assert lines[END-1].strip() == "```", f"Expected closing code fence at line {END}, got: {lines[END-1]!r}"

# Build new content
pre = "\n".join(lines[:START-1])  # lines 1..846
post = "\n".join(lines[END:])     # lines 1152..end

new_content = pre + "\n" + NEW_SECTION_9.rstrip("\n") + "\n" + post
if content.endswith("\n") and not new_content.endswith("\n"):
    new_content += "\n"

SAD_PATH.write_text(new_content, encoding="utf-8")
print(f"Wrote {len(new_content)} bytes to {SAD_PATH}")
print(f"Old: {len(lines)} lines. New line count: {len(new_content.splitlines())}")
