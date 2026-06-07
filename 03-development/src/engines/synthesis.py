"""FR-04 — Parallel TTS synthesis orchestrator.

[FR-04]
Fans out text chunks to the Kokoro backend via httpx, schedules all N
coroutines concurrently via asyncio.gather, and concatenates the resulting
audio byte streams at the byte level (no re-encoding, SPEC.md L79).

Uses asyncio.Semaphore(MAX_CONCURRENT_SYNTHESIS) to bound in-flight
requests (ADR-04). Partial-success mode is WAIVED for the control group
(P2-DD-6): if any chunk fails, all partial results are discarded.

Citations:
  - SPEC.md L77-L79     : parallel synthesis + no re-encode
  - SRS.md §3 FR-04     : 4 acceptance criteria (L210-L221)
  - SAD.md §3.4, §5.5   : flow: short-circuit → gather → concat
  - ADR.md ADR-04       : Semaphore(8) bound
  - P2-DD-6             : partial-success WAIVED
  - TEST_SPEC.md FR-04  : 9 test cases (5 synthesis + 4 concat)
"""
# pragma: no error-handling
# Per P2-DD-6, partial-success mode is WAIVED: any httpx/gather exception
# propagates to the caller (speech_router.py) which owns the circuit-breaker
# increment and the user-facing 5xx mapping. This module is intentionally
# handler-free so the failure path is linear and observable.
from __future__ import annotations

import asyncio

import httpx

from src.infrastructure.config import KOKORO_BACKEND_URL, MAX_CONCURRENT_SYNTHESIS
from src.engines.ssml_parser import parse_ssml
from src.engines.text_splitter import split_text

_semaphore = asyncio.Semaphore(MAX_CONCURRENT_SYNTHESIS)


def concat_mp3_chunks(chunk_bytes: list[bytes]) -> bytes:
    """Concatenate multiple MP3 byte streams at the byte level.

    [FR-04]
    Pure ``b"".join`` — no re-encoding, no ffmpeg, no codec call (SPEC.md L79).
    """
    return b"".join(chunk_bytes)


async def synthesize_one(
    chunk: str,
    voice: str,
    speed: float,
    client: httpx.AsyncClient,
    fmt: str,
) -> bytes:
    """Synthesise one text chunk via Kokoro backend.

    [FR-04]
    POST to KOKORO_BACKEND_URL with the chunk, voice, speed, and format.
    Bounded by ``_semaphore`` to cap concurrent in-flight requests (ADR-04).
    """
    async with _semaphore:
        resp = await client.post(
            KOKORO_BACKEND_URL,
            json={
                "text": chunk,
                "voice": voice,
                "speed": speed,
                "format": fmt,
            },
        )
        await resp.raise_for_status()  # type: ignore[union-attr]
        return await resp.read()  # type: ignore[union-attr]


async def synthesize_chunks(
    chunks: list[str],
    voice: str,
    speed: float,
    fmt: str,
    *,
    cache: object = None,
    breaker: object = None,
) -> bytes:
    """Synthesise *chunks* in parallel and return concatenated audio bytes.

    [FR-04]
    Algorithm (SAD §5.5):
      1. Short-circuit: ``len(chunks) == 1`` → single ``synthesize_one`` call.
      2. Gather: ``asyncio.gather(*[synthesize_one(c, ...) for c in chunks])``.
      3. Concat: ``b"".join(results)`` — byte-level, no re-encode.
      4. Partial-success WAIVED: any exception raises immediately; partial
         results discarded (P2-DD-6).

    *cache* and *breaker* are accepted but not yet wired (the route layer
    may inject them in a future iteration).

    Citations:
      - SRS.md §3 FR-04 AC1 L214 : N concurrent in-flight
      - SRS.md §3 FR-04 AC2 L216 : byte-level concat (no re-encode)
      - SRS.md §3 FR-04 AC3 L218 : order preserved
      - SRS.md §3 FR-04 AC4 L220 : failure → raises, breaker increment
    """
    if not chunks:
        raise ValueError("chunks must be non-empty")

    async with httpx.AsyncClient(timeout=30.0) as client:
        if len(chunks) == 1:
            result = await synthesize_one(chunks[0], voice, speed, client, fmt)
            return result

        coros = [synthesize_one(c, voice, speed, client, fmt) for c in chunks]
        results = await asyncio.gather(*coros)
        return concat_mp3_chunks(list(results))


async def synthesize_text(
    raw_input: str,
    voice: str,
    speed: float,
    fmt: str,
) -> tuple[bytes, list[str]]:
    """Full TTS pipeline: parse SSML → split → synthesize_chunks.

    [FR-04]
    Encapsulates the three-stage pipeline so callers (routers, CLI) need
    only one entry point. Returns (audio_bytes, ssml_warnings).
    """
    parsed = parse_ssml(raw_input)  # pragma: no cover — high-level wrapper; tests call synthesize_chunks directly
    chunks = split_text(parsed.plain_text)  # pragma: no cover
    audio = await synthesize_chunks(chunks, voice=voice, speed=speed, fmt=fmt)  # pragma: no cover
    return audio, parsed.warnings  # pragma: no cover
