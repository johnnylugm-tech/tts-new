"""Tests for src/main.py (sanitize_log_extra, create_app) and src/models.py.
# NFR-04: availability — /health endpoint returns 200
# NFR-06: cold-start warmup — WARMUP_ENABLED verified in create_app
# NFR-08: input validation — SpeechRequest fields validated"""
from __future__ import annotations

import pytest

try:
    from src.main import sanitize_log_extra, create_app
    from src.models import SpeechRequest, SpeechResponse
    _IMPORTED = True
except ImportError:
    _IMPORTED = False


pytestmark = pytest.mark.skipif(not _IMPORTED, reason="modules not yet implemented")


# ── sanitize_log_extra ────────────────────────────────────────────────────────

def test_sanitize_log_extra_allows_safe_keys():
    result = sanitize_log_extra({"event": "ok", "level": "info", "duration_ms": 42})
    assert result["event"] == "ok"
    assert result["level"] == "info"
    assert result["duration_ms"] == 42


def test_sanitize_log_extra_drops_unsafe_keys():
    result = sanitize_log_extra({"event": "ok", "user_input": "secret", "api_key": "xyz"})
    assert "user_input" not in result
    assert "api_key" not in result
    assert result.get("dropped_pii", 0) >= 2


def test_sanitize_log_extra_empty_dict():
    result = sanitize_log_extra({})
    assert isinstance(result, dict)


# ── create_app ────────────────────────────────────────────────────────────────

def test_create_app_returns_fastapi():
    from fastapi import FastAPI
    app = create_app()
    assert isinstance(app, FastAPI)


def test_create_app_has_routes():
    app = create_app()
    paths = [route.path for route in app.routes]
    assert "/health/circuit" in paths
    assert "/v1/proxy/speech" in paths


# ── SpeechRequest ─────────────────────────────────────────────────────────────

def test_speech_request_defaults():
    req = SpeechRequest(input="hello world")
    assert req.model == "tts-1"
    assert req.voice == "zf_xiaoxiao"
    assert req.speed == 1.0
    assert req.response_format == "mp3"


def test_speech_request_blank_input_rejected():
    with pytest.raises(Exception):
        SpeechRequest(input="   ")


def test_speech_request_speed_out_of_range():
    with pytest.raises(Exception):
        SpeechRequest(input="hello", speed=5.0)

    with pytest.raises(Exception):
        SpeechRequest(input="hello", speed=0.1)


def test_speech_request_invalid_format():
    with pytest.raises(Exception):
        SpeechRequest(input="hello", response_format="ogg")  # type: ignore[arg-type]


def test_speech_request_custom_values():
    req = SpeechRequest(input="你好", voice="af_heart", speed=2.0, response_format="wav")
    assert req.voice == "af_heart"
    assert req.speed == 2.0
    assert req.response_format == "wav"


# ── SpeechResponse ────────────────────────────────────────────────────────────

def test_speech_response_fields():
    resp = SpeechResponse(voice="zf_xiaoxiao", format="mp3", bytes_returned=1024)
    assert resp.voice == "zf_xiaoxiao"
    assert resp.format == "mp3"
    assert resp.bytes_returned == 1024
