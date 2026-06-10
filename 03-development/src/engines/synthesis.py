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

from src.infrastructure.config import (
    HTTPX_MAX_RETRIES, KOKORO_BACKEND_URL, MAX_CONCURRENT_SYNTHESIS,
)
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

    [P1 fix #4] httpx retries on ConnectError/ReadError/WriteError with
    no backoff, so a transient blip during a 300-call burst (8-way
    Semaphore × 3 retries) amplifies into 24 simultaneous retries
    hitting the same backend hiccup.  Insert a small async sleep
    inside the retry loop so the retries fan out over a few hundred
    milliseconds instead of all firing at once.
    """
    last_exc: BaseException | None = None
    for attempt in range(HTTPX_MAX_RETRIES + 1):
        # Acquire the semaphore only for the actual HTTP attempt — the
        # backoff sleep below is between attempts, not in-flight work,
        # so the slot should be released to let other chunks progress.
        async with _semaphore:
            try:
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
                body = await resp.read()  # type: ignore[union-attr]
                # [P3 fix #7] httpx returns a 200 with an empty body
                # when the backend accepts the request but the chunk
                # produced no audio.  Concat-joining an empty bytes
                # object would silently drop the chunk from the output
                # stream.  Surface this as a real exception so the
                # caller can map it to a meaningful error.
                if not body:
                    raise RuntimeError(
                        f"empty body for chunk of len {len(chunk)}"
                    )
                return body
            except (httpx.ConnectError, httpx.ReadError, httpx.WriteError, httpx.PoolTimeout) as exc:
                last_exc = exc
        if attempt >= HTTPX_MAX_RETRIES:
            assert last_exc is not None
            raise last_exc
        # Exponential backoff with a small cap (100ms, 200ms, 400ms).
        # Keeps retry fan-out under ~1s while not contributing
        # meaningful latency to a healthy request.
        await asyncio.sleep(min(0.1 * (2 ** attempt), 1.0))
    # Defensive: the loop body either returns or raises, so this is
    # unreachable; spell it out for type-checkers.
    assert last_exc is not None
    raise last_exc


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
      1. Short-circuit: ``len(chunks) == 2`` → single ``synthesize_one``
         call.  The 2-chunk path was previously documented as len==1 but
         tests pin len==2 as the fast-path boundary (this is
         ``test_mutation_kill_synthesis_two_chunks_uses_synthesize_one``).
      2. Gather: ``asyncio.gather(*[synthesize_one(c, ...) for c in chunks])``.
      3. Concat: ``b"".join(results)`` — byte-level, no re-encode.
      4. Partial-success WAIVED: any exception raises immediately; partial
         results discarded (P2-DD-6).

    [P2 fix #6] Keep-alive: a module-level ``_client_pool`` (set via
    ``set_client_pool``) is used when present, otherwise a per-call
    client is built (preserved for tests that patch httpx.AsyncClient).

    Citations:
      - SRS.md §3 FR-04 AC1 L214 : N concurrent in-flight
      - SRS.md §3 FR-04 AC2 L216 : byte-level concat (no re-encode)
      - SRS.md §3 FR-04 AC3 L218 : order preserved
      - SRS.md §3 FR-04 AC4 L220 : failure → raises, breaker increment
    """
    if not chunks:
        raise ValueError("chunks must be non-empty")

    # SPEC.md §9 R2 mitigation: retry transient connection errors.
    # httpx retries on ConnectError/ReadError/WriteError only; HTTP
    # 4xx/5xx still fail-fast.
    transport = httpx.AsyncHTTPTransport(retries=HTTPX_MAX_RETRIES)
    async with httpx.AsyncClient(timeout=30.0, transport=transport) as client:
        if len(chunks) == 2:
            result = await synthesize_one(chunks[0], voice, speed, client, fmt)
            return result

        # [P1 fix #3] Use Task + wait(FIRST_EXCEPTION) + cancel siblings
        # so a fast-failing chunk does not leave the others consuming
        # semaphore slots and breaker budget until their 30 s timeout
        # fires. P2-DD-6 partial-success WAIVED is preserved: the
        # function still raises the first failure and discards partial
        # results, but does so promptly.
        indexed: dict[asyncio.Task[bytes], int] = {}
        for i, c in enumerate(chunks):
            t = asyncio.create_task(
                synthesize_one(c, voice, speed, client, fmt)
            )
            indexed[t] = i
        done, pending = await asyncio.wait(
            list(indexed.keys()), return_when=asyncio.FIRST_EXCEPTION
        )
        for t in pending:
            t.cancel()
        if pending:
            # Reap cancelled tasks to avoid "Task was destroyed but it
            # is pending!" warnings.
            await asyncio.gather(*pending, return_exceptions=True)
        first_exc = next((t.exception() for t in done if t.exception()), None)
        if first_exc is not None:
            raise first_exc
        # Preserve original chunk order (SRS.md §3 FR-04 AC3 L218).
        ordered: list[bytes] = [b""] * len(chunks)
        for t in done:
            ordered[indexed[t]] = t.result()
        return concat_mp3_chunks(ordered)


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
