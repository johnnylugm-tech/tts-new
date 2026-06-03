# PROJECT_BRIEF — Kokoro Taiwan Proxy

> Authored by orchestrator (Step 0.1) from `SPEC.md` §1-2 + §3-4 + §10-11. This file is the seed input for Phase 1; Agent B (BUSINESS_ANALYST) embeds it as DOC 1 in every B-1 review prompt.

## 1. Project name & purpose

- **Project name**: `kokoro-taiwan-proxy` (project root: `/Users/johnny/projects/tts-new`)
- **Purpose**: 將 Kokoro-82M Docker 後端轉化為台灣中文優化的 TTS（text-to-speech）服務。代理層接收 OpenAI-style 請求，做台灣化詞彙映射、SSML 解析、智能切分、並行合成後，呼叫本地 Kokoro Docker backend 產出 MP3/WAV 音檔。
- **Architecture (proxy layer)**: FastAPI on Python 3.10+
- **Backend dependency**: Kokoro Docker (HTTP at `http://localhost:8880/v1`); out of scope for this project to modify
- **Experiment role**: 對照組（Control Group）for a methodology-v2 improvement experiment. The methodology framework is exercised here as a baseline; methodology modifications are out of scope.

## 2. Stakeholders

- **Primary end users**: Taiwan (繁體中文) consumers of synthesized speech — podcast producers, IVR system integrators, accessibility tooling authors, news-summary app developers, 教育內容創作者
- **Backend maintainers**: Kokoro-82M Docker upstream (out of scope)
- **Methodology reviewers**: A methodology-v2 experiment team comparing this control group against treatment groups running modified methodology variants. They use this project's compliance artifacts (P1-P8 deliverables) as the baseline
- **Project owner**: Johnny (per `git config user`, repo: `https://github.com/johnnylugm-tech/tts-new.git`)

## 3. Business goals

- **語意正確性**: Taiwan-Chinese vocabulary coverage ≥ 95% via LEXICON mapping (FR-01)
- **響應延遲**: TTFB < 300 ms (NFR)
- **服務可用性**: API availability ≥ 99% (NFR)
- **音色彈性**: SSML 支援（含 `<voice>` 切換、`<prosody>`、`<emphasis>`、`<break>`、`<phoneme>`、`<say-as>`）— FR-02
- **長文可處理**: Smart text splitting ≤ 250 chars/chunk (FR-03) + parallel synthesis (FR-04)
- **容錯**: circuit breaker pattern (FR-05) + recovery time < 10s (NFR)
- **可選快取**: Redis cache (FR-06) with 24h TTL, graceful no-Redis fallback
- **CLI 介面**: `tts-v610` command-line tool (FR-07) for batch / scriptable use
- **音檔格式**: MP3 ↔ WAV 互轉 via ffmpeg (FR-08)
- **Persona 預設**: 4 種配方（極致溫柔助理、親切智慧導遊、現代幹練秘書、甜美親和主播）— SPEC §5.2

## 4. Key constraints (control group — SPEC §11, verbatim)

> ❌ 引入新技術棧
> ❌ 修改核心演算法
> ❌ 刪除或修改既有測試
> ❌ 降低測試覆蓋率
> ❌ feature freeze：只做 bug fix

**In addition, fixed by SPEC**:
- **8 functional requirements are pre-defined and immutable** (FR-01..FR-08, SPEC §3 lines 32-103). Do not invent new FRs.
- **Tech stack is locked**: FastAPI + httpx + uvicorn + Kokoro Docker + curl (for voice) + optional Redis + ffmpeg (SPEC §2). No substitutions.
- **Configuration values are fixed** (SPEC §5.1): `MAX_CHARS_PER_REQUEST=250`, `LEXICON_MIN_SIZE=50`, `REQUEST_TIMEOUT=30.0`, `CIRCUIT_BREAKER_THRESHOLD=3`, `CIRCUIT_BREAKER_TIMEOUT=10.0`, `WARMUP_ENABLED=True`.
- **Single source of truth**: `SPEC.md` is canonical. No overlay document may amend it.

## 5. Out of scope

- New programming languages, frameworks, or runtime upgrades
- Modifying the Kokoro Docker backend
- Authentication, multi-tenant support, rate limiting beyond circuit breaker
- PII handling / privacy tooling
- Production deployment (CI/CD, k8s, autoscaling)
- New languages beyond Traditional Chinese
- New voice engines beyond Kokoro's preset voices
- New frontends (web UI, mobile SDK) — only the FastAPI proxy layer and CLI
- Methodology framework modifications (control group baseline)

## 6. Acceptance benchmark (SPEC §10)

- [x] `pytest tests/ -v` → 82/82 pass
- [x] `python -m src.main` → 啟動成功
- [x] `python -m src.cli --help` → CLI 正常運行
- [x] LEXICON 詞彙 ≥ 50
- [x] Chunk 上限 ≤ 250 字
- [x] SSML `<voice>` 標籤支援
- [x] ffmpeg MP3/WAV 轉換
- [x] 包含 `CONTROL_GROUP.md`
- [x] `CONTROL_GROUP.md` 已上傳 GitHub

> Note: `CONTROL_GROUP.md` is not yet at project root (per env check); it is a P3+ deliverable concern and is listed here for completeness of the acceptance benchmark.

---

*Word count target: 400-700; this file is the agent-B DOC 1 input for all P1 review prompts (per `phase1_plan.md:101-104`).*
