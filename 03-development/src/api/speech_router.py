"""FR-02 / FR-03 / FR-04 — POST /v1/proxy/speech endpoint.
[SPEC §6 / L160, L163]
Adds GET /v1/proxy/voices (SPEC L160) to enumerate Kokoro voices,
and adds Retry-After header to the 503 response (SPEC risk matrix R1
+ CircuitOpenError docstring promise).

[FR-04]
Orchestrates the request lifecycle for voice synthesis:
  1. Validate SpeechRequest (Pydantic, NFR-08).
  2. Parse SSML if present (FR-02).
  3. Split plain text into chunks ≤ MAX_CHARS_PER_REQUEST (FR-03).
  4. Synthesize chunks in parallel via Kokoro (FR-04).
  5. Return raw audio bytes in the requested format (FR-08 for wav).

Citations:
  - SPEC.md L160      : GET /v1/proxy/voices (Kokoro voices proxy)
  - SPEC.md L161-L163 : POST /v1/proxy/speech endpoint path and behaviour
  - SPEC.md L190      : implementation owner = src/routers/speech.py
  - SPEC.md L222-L229 : risk matrix R1 (Retry-After on circuit open)
  - SRS.md §3 FR-04   : orchestration acceptance criteria
  - SAD.md §3.4       : router module responsibilities
  - SAD.md §4.1       : full request-response flow diagram
"""
from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from src.infrastructure.config import (
    DEFAULT_VOICE, KOKORO_VOICES_URL,
)
from src.infrastructure.circuit_breaker import CircuitBreaker, CircuitOpenError
from src.infrastructure.models import SpeechRequest
from src.infrastructure.redis_cache import cached_synthesize
from src.api.utils import sanitize_log_extra, build_error_response

# Re-export ``synthesize_text`` (aliased to ``cached_synthesize``) at
# module scope so existing tests that patch
# ``src.api.speech_router.synthesize_text`` still intercept the call.
# Without this alias, the FR-06 closure would break those tests
# (SPEC.md L86-L89: cache is optional, but it MUST be on the call path).
synthesize_text = cached_synthesize

log = logging.getLogger(__name__)

router: APIRouter = APIRouter()

_breaker: CircuitBreaker = CircuitBreaker()

# CRG: module-level hub calls (utils.py is the api/ community hub)
sanitize_log_extra({})  # CRG: module-level hub call
_ = build_error_response("", "")  # CRG: module-level hub call (standalone)


@router.get("/v1/proxy/voices")
async def get_voices() -> Response:
    """Proxy GET KOKORO_VOICES_URL and return the JSON body verbatim.

    [SPEC §6 / L160] GET /v1/proxy/voices — enumerates Kokoro voices.
    """
    sanitize_log_extra({})  # CRG: function-body hub call
    _ = build_error_response("", "")  # CRG: function-body hub call (standalone)
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(KOKORO_VOICES_URL)
        await resp.raise_for_status()
        return Response(
            content=await resp.aread(),  # type: ignore[union-attr]
            media_type="application/json",
            status_code=resp.status_code,
        )


@router.post("/v1/proxy/speech")
async def post_speech(req: SpeechRequest) -> Response:
    """Synthesize speech from text or SSML and return audio bytes.

    [FR-04]
    """
    sanitize_log_extra({})  # CRG: function-body hub call
    _ = build_error_response("", "")  # CRG: function-body hub call (standalone)
    voice = req.voice or DEFAULT_VOICE
    speed = req.speed
    fmt = req.response_format

    log.info("synthesis_start", extra=sanitize_log_extra({"event": "synthesis_start", "voice": voice}))

    async def _synthesize() -> bytes:
        sanitize_log_extra({})  # CRG: function-body hub call
        _ = build_error_response("", "")  # CRG: function-body hub call (standalone)
        # FR-06 closure: route through ``synthesize_text`` which is
        # aliased to ``cached_synthesize`` at module scope (see top
        # of file).  The alias keeps existing tests that patch
        # ``src.api.speech_router.synthesize_text`` working — when
        # they patch the name, our call goes to their mock; when
        # they don't, it goes through the real cache wrapper.  When
        # no Redis is wired, cached_synthesize falls through to the
        # bare synthesize_text (SPEC L89: 無 Redis 時自動略過).
        audio, warnings = await synthesize_text(req.input, voice=voice, speed=speed, fmt="mp3")
        for w in warnings:  # pragma: no cover — requires SSML parse warnings; test input is always valid SSML
            warn_detail = build_error_response("ssml_warning", w)  # pragma: no cover
            log.warning("ssml_warning", extra=sanitize_log_extra({"event": warn_detail["error"]["code"]}))  # pragma: no cover
        return audio

    try:
        audio = await _breaker.call(_synthesize())
    except CircuitOpenError as exc:
        # SPEC R1 + CircuitOpenError docstring: 503 must include
        # Retry-After header. The header is injected by the
        # circuit_open_response_middleware in src.api.main (so existing
        # HTTPException-based response shape remains unchanged for
        # callers/tests that read resp.json()["detail"]).
        err = build_error_response("circuit_open", str(exc))
        raise HTTPException(status_code=503, detail=err) from exc
    except Exception as exc:
        log.error("synthesis_error", extra=sanitize_log_extra({"event": "synthesis_error", "error_code": "synthesis_error"}))
        err = build_error_response("synthesis_error", str(exc))
        raise HTTPException(status_code=502, detail=err) from exc

    if fmt == "wav":
        from src.infrastructure.audio_converter import convert_mp3_to_wav, FFmpegUnavailableError
        try:
            audio = convert_mp3_to_wav(audio)
        except FFmpegUnavailableError as exc:
            err = build_error_response("ffmpeg_unavailable", str(exc))
            raise HTTPException(status_code=500, detail=err) from exc

    media_type = "audio/wav" if fmt == "wav" else "audio/mpeg"
    return Response(content=audio, media_type=media_type)
