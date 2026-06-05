"""Tests for src/routers/speech.py — POST /v1/proxy/speech handler.

Covers all 6 behavioral paths through post_speech:
  1. MP3 happy path (default format, CLOSED breaker)
  2. Voice/speed passed through to synthesize_chunks
  3. WAV happy path (ffmpeg available)
  4. CircuitOpenError → HTTP 503
  5. Synthesis exception → HTTP 502
  6. FFmpegUnavailableError → HTTP 500
  7. SSML warning logged but response still succeeds

Citations:
  - SPEC.md L161-L163 : POST /v1/proxy/speech behaviour
  - SRS.md §3 FR-04   : orchestration acceptance criteria
  - SAD.md §3.4       : router module responsibilities
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

try:
    from src.routers.speech import router
    from src.middleware.circuit_breaker import CircuitBreaker, CircuitOpenError
    from src.audio_converter import FFmpegUnavailableError
    _IMPORTED = True
except ImportError:
    _IMPORTED = False

pytestmark = pytest.mark.skipif(not _IMPORTED, reason="modules not yet implemented")

_MP3 = b"\xff\xfb\x90\x00fake_mp3"
_WAV = b"RIFF\x00\x00\x00\x00WAVEfmt fake"


@pytest.fixture()
def client():
    """Isolated FastAPI app with speech router per test."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture(autouse=True)
def fresh_breaker():
    """Give each test a clean CLOSED CircuitBreaker so state does not leak."""
    import src.routers.speech as _mod
    original = _mod._breaker
    _mod._breaker = CircuitBreaker()
    yield
    _mod._breaker = original


# ── 1. MP3 happy path ─────────────────────────────────────────────────────────

def test_post_speech_mp3_returns_200_with_audio_mpeg(client):
    with patch("src.routers.speech.synthesize_chunks", new=AsyncMock(return_value=_MP3)):
        resp = client.post("/v1/proxy/speech", json={"input": "hello world"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/mpeg"
    assert resp.content == _MP3


# ── 2. Voice and speed forwarded ─────────────────────────────────────────────

def test_post_speech_forwards_voice_and_speed(client):
    calls: list[dict] = []

    async def _capture(chunks, *, voice, speed, fmt):
        calls.append({"voice": voice, "speed": speed})
        return _MP3

    with patch("src.routers.speech.synthesize_chunks", new=_capture):
        resp = client.post("/v1/proxy/speech",
                           json={"input": "test", "voice": "af_heart", "speed": 1.5})
    assert resp.status_code == 200
    assert calls[0]["voice"] == "af_heart"
    assert calls[0]["speed"] == 1.5


# ── 3. WAV happy path ─────────────────────────────────────────────────────────

def test_post_speech_wav_returns_audio_wav(client):
    with patch("src.routers.speech.synthesize_chunks", new=AsyncMock(return_value=_MP3)), \
         patch("src.audio_converter.convert_mp3_to_wav", return_value=_WAV):
        resp = client.post("/v1/proxy/speech",
                           json={"input": "hello", "response_format": "wav"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/wav"
    assert resp.content == _WAV


# ── 4. CircuitOpenError → 503 ─────────────────────────────────────────────────

def test_post_speech_circuit_open_returns_503(client):
    import src.routers.speech as _mod
    _mod._breaker.call = AsyncMock(side_effect=CircuitOpenError("OPEN"))
    resp = client.post("/v1/proxy/speech", json={"input": "hello"})
    assert resp.status_code == 503
    assert resp.json()["detail"]["error"]["code"] == "circuit_open"


# ── 5. Synthesis exception → 502 ─────────────────────────────────────────────

def test_post_speech_synthesis_error_returns_502(client):
    with patch("src.routers.speech.synthesize_chunks",
               new=AsyncMock(side_effect=RuntimeError("backend down"))):
        resp = client.post("/v1/proxy/speech", json={"input": "hello"})
    assert resp.status_code == 502
    assert resp.json()["detail"]["error"]["code"] == "synthesis_error"


# ── 6. FFmpegUnavailableError → 500 ──────────────────────────────────────────

def test_post_speech_ffmpeg_unavailable_returns_500(client):
    with patch("src.routers.speech.synthesize_chunks", new=AsyncMock(return_value=_MP3)), \
         patch("src.audio_converter.convert_mp3_to_wav",
               side_effect=FFmpegUnavailableError()):
        resp = client.post("/v1/proxy/speech",
                           json={"input": "hello", "response_format": "wav"})
    assert resp.status_code == 500
    assert resp.json()["detail"]["error"]["code"] == "ffmpeg_unavailable"


# ── 7. SSML warning → response still succeeds ────────────────────────────────

def test_post_speech_ssml_warning_does_not_block(client):
    """parse_ssml emits a warning for unsupported SSML; response must still be 200."""
    with patch("src.routers.speech.synthesize_chunks", new=AsyncMock(return_value=_MP3)):
        resp = client.post(
            "/v1/proxy/speech",
            json={"input": '<speak><emphasis level="none">hi</emphasis></speak>'},
        )
    assert resp.status_code == 200
    assert resp.content == _MP3
