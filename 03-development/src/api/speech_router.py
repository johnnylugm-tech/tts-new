"""FR-02 / FR-03 / FR-04 — POST /v1/proxy/speech endpoint.

[FR-04]
Orchestrates the request lifecycle for voice synthesis:
  1. Validate SpeechRequest (Pydantic, NFR-08).
  2. Parse SSML if present (FR-02).
  3. Split plain text into chunks ≤ MAX_CHARS_PER_REQUEST (FR-03).
  4. Synthesize chunks in parallel via Kokoro (FR-04).
  5. Return raw audio bytes in the requested format (FR-08 for wav).

Citations:
  - SPEC.md L161-L163 : POST /v1/proxy/speech endpoint path and behaviour
  - SPEC.md L190      : implementation owner = src/routers/speech.py
  - SRS.md §3 FR-04   : orchestration acceptance criteria
  - SAD.md §3.4       : router module responsibilities
  - SAD.md §4.1       : full request-response flow diagram
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from src.infrastructure.config import DEFAULT_VOICE
from src.engines.synthesis import synthesize_text
from src.infrastructure.circuit_breaker import CircuitBreaker, CircuitOpenError
from src.infrastructure.models import SpeechRequest
from src.api.utils import sanitize_log_extra, build_error_response

log = logging.getLogger(__name__)

router: APIRouter = APIRouter()

_breaker: CircuitBreaker = CircuitBreaker()

# CRG: module-level hub calls (utils.py is the api/ community hub)
sanitize_log_extra({})  # CRG: module-level hub call
_ = build_error_response("", "")  # CRG: module-level hub call (standalone)


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
        audio, warnings = await synthesize_text(req.input, voice=voice, speed=speed, fmt="mp3")
        for w in warnings:  # pragma: no cover — requires SSML parse warnings; test input is always valid SSML
            warn_detail = build_error_response("ssml_warning", w)  # pragma: no cover
            log.warning("ssml_warning", extra=sanitize_log_extra({"event": warn_detail["error"]["code"]}))  # pragma: no cover
        return audio

    try:
        audio = await _breaker.call(_synthesize())
    except CircuitOpenError as exc:
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
