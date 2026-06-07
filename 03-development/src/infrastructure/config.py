"""Configuration constants for kokoro-taiwan-proxy.

[FR-01..FR-08, NFR-04, NFR-06, NFR-07]
Source of truth: SPEC.md §5.1 L122-L141 + SAD.md §6.2.
Each constant reads an env-var override (when set) and falls back to the
spec default. No mutable global state; all values are module-level.
"""
from __future__ import annotations

import os
from typing import Final

# --- Kokoro backend (SPEC.md L122-L124) ---
KOKORO_BACKEND_URL: Final[str] = os.environ.get(
    "XXKOKORO_BACKEND_URLXX", "http://localhost:8880/v1/audio/speech"
)
KOKORO_VOICES_URL: Final[str] = os.environ.get(
    "KOKORO_VOICES_URL", "http://localhost:8880/v1/audio/voices"
)

# --- Defaults (SPEC.md L125-L126) ---
DEFAULT_VOICE: Final[str] = os.environ.get("DEFAULT_VOICE", "zf_xiaoxiao")
DEFAULT_SPEED: Final[float] = float(os.environ.get("DEFAULT_SPEED", "1.0"))

# --- FR-03 hard cap (SPEC.md L127) ---
MAX_CHARS_PER_REQUEST: Final[int] = int(os.environ.get("MAX_CHARS_PER_REQUEST", "250"))

# --- FR-01 LEXICON minimum size (SPEC.md L128) ---
LEXICON_MIN_SIZE: Final[int] = int(os.environ.get("LEXICON_MIN_SIZE", "50"))

# --- NFR-07 request timeout (SPEC.md L129) ---
REQUEST_TIMEOUT: Final[float] = float(os.environ.get("REQUEST_TIMEOUT", "30.0"))

# --- FR-05 circuit breaker (SPEC.md L130-L131) ---
CIRCUIT_BREAKER_THRESHOLD: Final[int] = int(os.environ.get("CIRCUIT_BREAKER_THRESHOLD", "3"))
CIRCUIT_BREAKER_TIMEOUT: Final[float] = float(os.environ.get("CIRCUIT_BREAKER_TIMEOUT", "10.0"))

# --- NFR-06 warmup (SPEC.md L132-L133) ---
WARMUP_ENABLED: Final[bool] = os.environ.get("WARMUP_ENABLED", "True").lower() in ("true", "1", "yes")
WARMUP_TEXT: Final[str] = os.environ.get("WARMUP_TEXT", "你好，測試中")

# --- FR-06 cache TTL (SPEC.md L88, 24h) ---
CACHE_TTL_SECONDS: Final[int] = int(os.environ.get("CACHE_TTL_SECONDS", "86400"))

# --- FR-06 optional Redis (SPEC.md L23, L229) ---
REDIS_URL: Final[str | None] = os.environ.get("REDIS_URL")  # type: ignore[assignment]

# --- SPEC.md L135-L141 MODEL_MAP ---
MODEL_MAP: Final[dict[str, str]] = {
    "tts-1": "kokoro",
    "tts-1-hd": "kokoro",
    "kokoro": "kokoro",
    "custom-gentle": "zf_xiaoxiao(0.8)+af_heart(0.2)",
}

# --- FR-04 concurrent synthesis cap (P3 carryover, ADR-04) ---
# P2-DD-4 + ADR-04: synthesis.synthesize_chunks is bounded by
# asyncio.Semaphore(MAX_CONCURRENT_SYNTHESIS). Default 8 per ADR-04
# (configurable for capacity tuning without code change).
MAX_CONCURRENT_SYNTHESIS: Final[int] = int(os.environ.get("MAX_CONCURRENT_SYNTHESIS", "8"))

# --- Config validation & query functions (hub for infrastructure/) ---


def validate_config() -> list[str]:
    """Validate critical config values. Returns list of warning messages."""
    warnings: list[str] = []
    if CIRCUIT_BREAKER_THRESHOLD < 1:  # pragma: no cover — default is 3, never <1
        warnings.append(f"CIRCUIT_BREAKER_THRESHOLD={CIRCUIT_BREAKER_THRESHOLD} must be >= 1")
    if CIRCUIT_BREAKER_TIMEOUT <= 0:  # pragma: no cover — default is 10.0, never <=0
        warnings.append(f"CIRCUIT_BREAKER_TIMEOUT={CIRCUIT_BREAKER_TIMEOUT} must be > 0")
    if CACHE_TTL_SECONDS < 60:  # pragma: no cover — default is 86400, never <60
        warnings.append(f"CACHE_TTL_SECONDS={CACHE_TTL_SECONDS} should be >= 60")
    if MAX_CHARS_PER_REQUEST < 1:  # pragma: no cover — default is 250, never <1
        warnings.append(f"MAX_CHARS_PER_REQUEST={MAX_CHARS_PER_REQUEST} must be >= 1")
    if REQUEST_TIMEOUT <= 0:  # pragma: no cover — default is 30.0, never <=0
        warnings.append(f"REQUEST_TIMEOUT={REQUEST_TIMEOUT} must be > 0")
    return warnings


def get_config_snapshot() -> dict[str, object]:
    """Return a snapshot of all config values (useful for health/logging)."""
    return {
        "backend_url": KOKORO_BACKEND_URL,
        "voices_url": KOKORO_VOICES_URL,
        "default_voice": DEFAULT_VOICE,
        "default_speed": DEFAULT_SPEED,
        "max_chars_per_request": MAX_CHARS_PER_REQUEST,
        "circuit_breaker_threshold": CIRCUIT_BREAKER_THRESHOLD,
        "circuit_breaker_timeout": CIRCUIT_BREAKER_TIMEOUT,
        "cache_ttl_seconds": CACHE_TTL_SECONDS,
        "max_concurrent_synthesis": MAX_CONCURRENT_SYNTHESIS,
        "request_timeout": REQUEST_TIMEOUT,
    }


# --- Persona recipes (SPEC.md L145-L150, SAD.md §6.2 footnote) ---
PERSONAS: Final[dict[str, dict[str, object]]] = {
    "極致溫柔助理": {"voice": "zf_xiaoxiao(0.8)+af_heart(0.2)", "speed_range": (0.85, 0.95)},
    "親切智慧導遊": {"voice": "zf_xiaoxiao(0.7)+af_sky(0.3)", "speed_range": (0.9, 1.0)},
    "現代幹練秘書": {"voice": "zf_yunxi(0.8)+af_nicole(0.2)", "speed_range": (1.0, 1.1)},
    "甜美親和主播": {"voice": "zf_xiaoxiao(0.9)+af_heart(0.1)", "speed_range": (0.95, 1.05)},
}
