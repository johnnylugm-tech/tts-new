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

from src.config import DEFAULT_VOICE
from src.engines.ssml_parser import parse_ssml
from src.engines.text_splitter import split_text
from src.engines.synthesis import synthesize_chunks
from src.middleware.circuit_breaker import CircuitBreaker, CircuitOpenError
from src.models import SpeechRequest

log = logging.getLogger(__name__)

router: APIRouter = APIRouter()

_breaker: CircuitBreaker = CircuitBreaker()


@router.post("/v1/proxy/speech")
async def post_speech(req: SpeechRequest) -> Response:
    """Synthesize speech from text or SSML and return audio bytes.

    [FR-04]
    """
    voice = req.voice or DEFAULT_VOICE
    speed = req.speed
    fmt = req.response_format

    parsed = parse_ssml(req.input)
    for w in parsed.warnings:
        log.warning("ssml_warning: %s", w)

    chunks = split_text(parsed.plain_text)

    async def _synthesize() -> bytes:
        return await synthesize_chunks(chunks, voice=voice, speed=speed, fmt="mp3")

    try:
        audio = await _breaker.call(_synthesize())
    except CircuitOpenError as exc:
        raise HTTPException(status_code=503, detail={
            "error": {"code": "circuit_open", "message": str(exc)}
        }) from exc
    except Exception as exc:
        log.error("synthesis_error: %s", exc)
        raise HTTPException(status_code=502, detail={
            "error": {"code": "synthesis_error", "message": str(exc)}
        }) from exc

    if fmt == "wav":
        from src.audio_converter import convert_mp3_to_wav, FFmpegUnavailableError
        try:
            audio = convert_mp3_to_wav(audio)
        except FFmpegUnavailableError as exc:
            raise HTTPException(status_code=500, detail={
                "error": {"code": "ffmpeg_unavailable", "message": str(exc)}
            }) from exc

    media_type = "audio/wav" if fmt == "wav" else "audio/mpeg"
    return Response(content=audio, media_type=media_type)
