# Kokoro Taiwan Proxy — 規格文件（單一事實來源）

> 本文件為 `kokoro-taiwan-proxy` 的完整規格，合併原始 docx 規格與 SRS.md 優化版。  
> **所有實作以此文件為準。**

---

## 1. 概述

- **專案名稱**：`kokoro-taiwan-proxy`
- **目的**：將 Kokoro-82M Docker 後端轉化為台灣中文優化的 TTS 服務
- **代理層**：FastAPI（Python 3.10+）
- **後端**：Kokoro Docker（`http://localhost:8880/v1`）
- **角色**：methodology-v2 改進實驗的**對照組**（Control Group）

---

## 2. 技術架構

| 元件 | 技術 |
|------|------|
| 框架 | FastAPI + httpx + uvicorn |
| 後端 | Kokoro Docker |
| 音色處理 | curl（繞過 Python SSL 問題） |
| 可選快取 | Redis |
| 格式轉換 | ffmpeg |

---

## 3. 功能需求（Functional Requirements）

### FR-01：台灣中文詞彙映射
- LEXICON 映射表 **≥ 50 詞彙**
- 覆蓋率目標：**≥ 95%**
- 典型詞彙：

| 原始詞 | 台灣化 |
|--------|--------|
| 視頻 | 影片 |
| 地鐵 | 捷運 |
| 垃圾 | ㄌㄜˋ ㄙㄜˋ |
| 菠蘿 | 鳳梨 |
| 程序員 | 工程師 |
| 軟件 | 軟體 |
| 硬件 | 硬體 |
| 和（連接詞） | ㄏㄢˋ |
| 吧（語氣） | 啦 |
| 互聯網 | 網際網路 |
| 博客 | 部落格 |
| 網名 | 暱稱 |

### FR-02：SSML 解析

| 標籤 | 屬性 | 處理策略 |
|------|------|---------|
| `<speak>` | — | 根元素 |
| `<break>` | `time="500ms"` | 插入停頓（墊片字元） |
| `<prosody>` | `rate="0.9"` | 映射 Kokoro speed |
| `<emphasis>` | `level="strong/moderate"` | speed ×1.1 |
| `<voice>` | `name="xxx"` | 音色切換 |
| `<phoneme>` | `alphabet="ipa"` | 保留原生 |
| `<say-as>` | `interpret-as` | 數值轉文字 |
| `<!-- -->` | — | 移除 |

**pitch / volume**：Kokoro 不支援，印 warn 忽略。

### FR-03：智能文本切分

- **Chunk 上限**：**≤ 250 字**（確保語調穩定）
- 最優區段：100–250 字
- 三級遞迴：
  1. 句級（`。？！!?\n`）
  2. 子句級（`；：`）（若 >100 字）
  3. 詞組級（`，`）（若仍 >100 字）
- 不在中英文混合字中間切斷

### FR-04：並行合成
- httpx.AsyncClient 同時發出 N 個請求
- MP3 直接串接（無需重新編碼）

### FR-05：斷路器
- 失敗計數 ≥ threshold → Open
- Open 後 timeout 秒 → Half-Open
- 成功 → Closed

### FR-06：Redis 快取（可選）
- Key：`hash(text + voice + speed)`
- TTL：24 小時
- 無 Redis 時自動略過

### FR-07：CLI 命令列工具
```bash
tts-v610 "你好世界" -o output.mp3
tts-v610 -i input.txt -o output/
tts-v610 "文字" -v "zf_xiaoxiao" -s 1.0 -f mp3
tts-v610 --ssml "<speak>...</speak>" -o out.mp3
tts-v610 --backend "http://localhost:8880" "text" -o out.mp3
```

### FR-08：ffmpeg 音訊格式轉換
- 支援：MP3 ↔ WAV
- 使用 `subprocess` 呼叫 ffmpeg

---

## 4. 非功能需求（Non-Functional Requirements）

| 指標 | 目標 |
|------|------|
| TTFB | < 300ms |
| LEXICON 覆蓋率 | ≥ 80% |
| 變調正確率 | ≥ 95% |
| API 可用率 | ≥ 99% |
| 錯誤恢復時間 | < 10s |

---

## 5. 參數配置

### 5.1 config.py

```python
KOKORO_BACKEND_URL = "http://localhost:8880/v1/audio/speech"
KOKORO_VOICES_URL  = "http://localhost:8880/v1/audio/voices"
DEFAULT_VOICE      = "zf_xiaoxiao"
DEFAULT_SPEED      = 1.0
MAX_CHARS_PER_REQUEST = 250          # ≤ 250（FR-03）
LEXICON_MIN_SIZE   = 50               # ≥ 50（FR-01）
REQUEST_TIMEOUT    = 30.0
CIRCUIT_BREAKER_THRESHOLD = 3
CIRCUIT_BREAKER_TIMEOUT   = 10.0
WARMUP_ENABLED     = True
WARMUP_TEXT        = "你好，測試中"

MODEL_MAP = {
    "tts-1":         "kokoro",
    "tts-1-hd":      "kokoro",
    "kokoro":        "kokoro",
    "custom-gentle": "zf_xiaoxiao(0.8)+af_heart(0.2)",
}
```

### 5.2 Persona 預設配方

| Persona | 音色配方 | Speed | 應用 |
|---------|---------|-------|------|
| 極致溫柔助理 | `zf_xiaoxiao(0.8)+af_heart(0.2)` | 0.85–0.95 | 睡前故事 |
| 親切智慧導遊 | `zf_xiaoxiao(0.7)+af_sky(0.3)` | 0.9–1.0 | 展場導覽 |
| 現代幹練秘書 | `zf_yunxi(0.8)+af_nicole(0.2)` | 1.0–1.1 | 行事曆提醒 |
| 甜美親和主播 | `zf_xiaoyi(0.6)+zf_xiaoxiao(0.4)` | 1.0–1.1 | 新聞摘要 |

---

## 6. API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/health` | 健康檢查 |
| GET | `/ready` | 就緒檢查 |
| GET | `/v1/proxy/voices` | 音色列表 |
| POST | `/v1/proxy/speech` | 語音合成 |
| GET | `/health/circuit` | 斷路器狀態 |
| POST | `/health/circuit/reset` | 重置斷路器 |

### SpeechRequest

```json
{
  "model": "tts-1",
  "input": "文字或 SSML",
  "voice": "zf_xiaoxiao",
  "speed": 1.0,
  "response_format": "mp3"
}
```

---

## 7. 資料夾結構

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

## 8. 錯誤處理

| 情況 | 回應 |
|------|------|
| SSML 解析失敗 | Fallback 純文字，log warn |
| 後端 5xx 錯誤 | 觸發斷路器 |
| 斷路器 Open | HTTP 503 |
| 空輸入 | HTTP 400 |
| 輸入過長（>8000字） | HTTP 400 |
| 無效音色 | HTTP 400 |

---

## 9. 風險矩陣（來自 SRS.md）

| ID | 風險 | 影響 | 可能性 | 緩解 |
|----|------|------|--------|------|
| R1 | Kokoro Docker 崩潰 | 高 | 低 | 斷路器 + 錯誤訊息 |
| R2 | 連線中斷 | 中 | 中 | 重試 3 次 + retry handler |
| R3 | ffmpeg 缺失 | 中 | 低 | 必要依賴聲明 |
| R4 | Redis 無法連線 | 低 | 低 | Optional 裝飾，無 Redis 時略過 |

---

## 10. 驗收標準

- [x] `pytest tests/ -v` → 82/82 通過
- [x] `python -m src.main` → 啟動成功
- [x] `python -m src.cli --help` → CLI 正常運行
- [x] LEXICON 詞彙 ≥ 50
- [x] Chunk 上限 ≤ 250 字
- [x] SSML `<voice>` 標籤支援
- [x] ffmpeg MP3/WAV 轉換
- [x] 包含 `CONTROL_GROUP.md`
- [x] `CONTROL_GROUP.md` 已上傳 GitHub

---

## 11. 禁止事項（對照組）

- ❌ 引入新技術棧
- ❌ 修改核心演算法
- ❌ 刪除或修改既有測試
- ❌ 降低測試覆蓋率
- ❌ feature freeze：只做 bug fix

---

*文件版本：v1.0.0-control | 更新時間：2026-03-31*
