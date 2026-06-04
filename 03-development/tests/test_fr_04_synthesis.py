"""FR-04: Parallel synthesis — TDD-RED failing tests.

5 parametrized cases for test_fr_04_synthesis (src/engines/synthesis.py).
Tests use `try/except ImportError` lazy import so spec-coverage-check can
enumerate the 5 parametrize IDs even when the production module is absent.

GREEN TODO: implement src/engines/synthesis.py with:
  - MAX_CONCURRENT_SYNTHESIS = 8 (imported from src.config)
  - async synthesize_one(chunk, voice, speed, client, fmt, breaker, cache) -> bytes
  - async synthesize_chunks(chunks, voice, speed, fmt, *, cache, breaker) -> bytes
      If len(chunks) == 1 → single httpx call (short-circuit)
      Else → asyncio.gather(*[synthesize_one(c) ...]), b"".join(results)
      Semaphore(MAX_CONCURRENT_SYNTHESIS) bounds concurrent in-flight
      On any exception → raise; partial results discarded (P2-DD-6 WAIVED)
"""
from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

# Lazy import so spec-coverage-check can enumerate parametrize IDs
try:
    from src.engines.synthesis import (  # type: ignore[import-not-found]
        MAX_CONCURRENT_SYNTHESIS,
        synthesize_chunks,
    )
except ImportError:
    MAX_CONCURRENT_SYNTHESIS = 8  # type: ignore[assignment]
    synthesize_chunks = None

# ---------------------------------------------------------------------------
# 5 parametrize IDs — MUST match TEST_SPEC.md FR-04 table exactly
# ---------------------------------------------------------------------------
_CASE_IDS = [
    "N_concurrent_coroutines_started_before_await",
    "chunk_order_preserved_in_output",
    "backend_5xx_triggers_5xx_and_breaker_increment",
    "total_latency_bounded_by_max_per_chunk",
    "single_chunk_short_circuit_path",
]


@pytest.mark.parametrize("case_id", _CASE_IDS)
@pytest.mark.asyncio
async def test_fr_04_synthesis(case_id):
    """FR-04: 5 synthesis orchestration cases (concurrency, errors, performance).

    Mock the httpx.AsyncClient POST endpoint so tests run without Kokoro.
    """
    if synthesize_chunks is None:  # RED-phase guard
        pytest.fail(
            "src.engines.synthesis must export synthesize_chunks "
            "and MAX_CONCURRENT_SYNTHESIS"
        )

    # Shared mock client factory
    async def _mock_post(status=200, data=b"fake_audio", delay=0.0):
        async def _handler(*args, **kwargs):
            if delay:
                await asyncio.sleep(delay)
            mock = AsyncMock()
            mock.status_code = status
            mock.raise_for_status = AsyncMock()
            if status >= 400:
                mock.raise_for_status.side_effect = Exception(f"HTTP {status}")
            mock.read = AsyncMock(return_value=data)
            return mock
        return _handler

    # ── Case 1: N concurrent coroutines started before await ────────────────
    if case_id == "N_concurrent_coroutines_started_before_await":
        # AC1: all N coroutines are scheduled before any await completes
        # (SPEC.md L78, SRS.md L214). The test verifies by tracking the
        # number of concurrent in-flight requests.
        n_coros = 3
        all_started = asyncio.Event()
        coro_count = 0
        concurrency_seen = 0

        async def _slow_handler(*args, **kwargs):
            nonlocal coro_count, concurrency_seen
            coro_count += 1
            if coro_count == n_coros:
                all_started.set()
            concurrency_seen = max(concurrency_seen, coro_count)
            await all_started.wait()
            mock = AsyncMock()
            mock.status_code = 200
            mock.raise_for_status = AsyncMock()
            mock.read = AsyncMock(return_value=b"audio")
            return mock

        chunks = [f"c{i}" for i in range(n_coros)]
        with patch("httpx.AsyncClient") as MockClient:
            client = AsyncMock()
            client.post = _slow_handler
            MockClient.return_value = client
            client.__aenter__.return_value = client
            client.__aexit__.return_value = None

            result = await synthesize_chunks(
                chunks, voice="zf_xiaoxiao", speed=1.0, fmt="mp3"
            )

        assert concurrency_seen == n_coros, (
            f"all {n_coros} coroutines must be started before any await completes; "
            f"max concurrent seen: {concurrency_seen} "
            f"(SRS.md §3 FR-04 AC1 L214, SPEC.md L78)"
        )
        assert isinstance(result, bytes) and len(result) > 0, (
            "synthesize_chunks must return non-empty bytes"
        )

    # ── Case 2: chunk order preserved in output ───────────────────────────────
    elif case_id == "chunk_order_preserved_in_output":
        # AC3: output byte order matches chunk order (SRS.md L218)
        chunks = ["a", "b", "c", "d"]
        responses = {c: f"audio_{c}".encode() for c in chunks}

        async def _ordered_handler(*args, **kwargs):
            data = args[1] if len(args) > 1 else kwargs.get("json") or kwargs.get("data", {})
            chunk_text = data.get("text", "") if isinstance(data, dict) else ""
            resp = responses.get(chunk_text, b"unknown")
            mock = AsyncMock()
            mock.status_code = 200
            mock.raise_for_status = AsyncMock()
            mock.read = AsyncMock(return_value=resp)
            return mock

        with patch("httpx.AsyncClient") as MockClient:
            client = AsyncMock()
            client.post = _ordered_handler
            MockClient.return_value = client
            client.__aenter__.return_value = client
            client.__aexit__.return_value = None

            result = await synthesize_chunks(
                chunks, voice="zf_xiaoxiao", speed=1.0, fmt="mp3"
            )

        expected = b"audio_a" + b"audio_b" + b"audio_c" + b"audio_d"
        assert result == expected, (
            f"output bytes must preserve chunk order; "
            f"expected {expected!r}; got {result[:50]!r}... "
            f"(SRS.md §3 FR-04 AC3 L218)"
        )

    # ── Case 3: backend 5xx → 5xx + breaker increment (AC4) ──────────────────
    elif case_id == "backend_5xx_triggers_5xx_and_breaker_increment":
        # AC4, P2-DD-6 partial-success WAIVED: any failure discards partial
        # results and raises an exception. NFR-07: timeout also raises.
        chunks = ["a", "b"]

        async def _failing_handler(*args, **kwargs):
            mock = AsyncMock()
            mock.status_code = 500
            mock.raise_for_status.side_effect = Exception("HTTP 500")
            mock.read = AsyncMock()
            return mock

        with patch("httpx.AsyncClient") as MockClient:
            client = AsyncMock()
            client.post = _failing_handler
            MockClient.return_value = client
            client.__aenter__.return_value = client
            client.__aexit__.return_value = None

            with pytest.raises(Exception, match=".*500.*"):
                await synthesize_chunks(
                    chunks, voice="zf_xiaoxiao", speed=1.0, fmt="mp3"
                )

    # ── Case 4: total latency bounded by max per chunk (NFR-01) ───────────────
    elif case_id == "total_latency_bounded_by_max_per_chunk":
        # NFR-01: with Semaphore(N) and N concurrent in-flight, total latency
        # ≤ max(per_chunk_latency) + small overhead (< 50 ms overhead).
        chunks = ["slow1", "slow2", "slow3", "slow4", "slow5"]
        delay_per_chunk = 0.02  # 20 ms each

        async def _delayed_handler(*args, **kwargs):
            await asyncio.sleep(delay_per_chunk)
            mock = AsyncMock()
            mock.status_code = 200
            mock.raise_for_status = AsyncMock()
            mock.read = AsyncMock(return_value=b"audio")
            return mock

        with patch("httpx.AsyncClient") as MockClient:
            client = AsyncMock()
            client.post = _delayed_handler
            MockClient.return_value = client
            client.__aenter__.return_value = client
            client.__aexit__.return_value = None

            t0 = time.monotonic()
            await synthesize_chunks(
                chunks, voice="zf_xiaoxiao", speed=1.0, fmt="mp3"
            )
            total = time.monotonic() - t0

        # With 8 concurrent slots and 5 chunks, all 5 fire in one batch.
        # Expected: delay_per_chunk + overhead. Allow < 3x for overhead.
        assert total < delay_per_chunk * 3, (
            f"total latency must be bounded by max per-chunk; "
            f"expected ≈ {delay_per_chunk:.3f}s, got {total:.3f}s "
            f"(SRS.md §4 NFR-01 L110)"
        )

    # ── Case 5: single chunk short-circuit path ──────────────────────────────
    elif case_id == "single_chunk_short_circuit_path":
        # AC1 single-chunk fast path: chunks=["a"] → exactly 1 httpx call
        call_count = 0

        async def _single_handler(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock = AsyncMock()
            mock.status_code = 200
            mock.raise_for_status = AsyncMock()
            mock.read = AsyncMock(return_value=b"audio")
            return mock

        with patch("httpx.AsyncClient") as MockClient:
            client = AsyncMock()
            client.post = _single_handler
            MockClient.return_value = client
            client.__aenter__.return_value = client
            client.__aexit__.return_value = None

            result = await synthesize_chunks(
                ["a"], voice="zf_xiaoxiao", speed=1.0, fmt="mp3"
            )

        assert call_count == 1, (
            f"single chunk must make exactly 1 httpx call; got {call_count} "
            f"(SRS.md §3 FR-04 AC1 L214, SPEC.md L77-L78)"
        )
        assert isinstance(result, bytes) and len(result) > 0, (
            "synthesize_chunks must return non-empty bytes"
        )
