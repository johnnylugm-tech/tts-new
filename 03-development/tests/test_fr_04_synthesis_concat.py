"""FR-04: Concatenation — TDD-RED failing tests.

4 parametrized cases for test_fr_04_synthesis_concat.
Tests byte-level MP3 concatenation (no re-encoding).

GREEN TODO: src/engines/synthesis.py must export:
  - concat_mp3_chunks(chunk_bytes: list[bytes]) -> bytes
      b"".join(chunk_bytes) — byte-level concat, no re-encode (SPEC.md L79)
"""
from __future__ import annotations

import pytest

# Lazy import so spec-coverage-check can enumerate parametrize IDs
try:
    from src.engines.synthesis import (  # type: ignore[import-not-found]
        concat_mp3_chunks,
    )
except ImportError:
    concat_mp3_chunks = None

# ---------------------------------------------------------------------------
# 4 parametrize IDs — MUST match TEST_SPEC.md FR-04 table exactly
# ---------------------------------------------------------------------------
_CASE_IDS = [
    "concat_byte_length_equals_sum",
    "no_ffmpeg_invocation_in_concat_path",
    "first_chunk_mp3_sync_at_offset_zero",
    "last_chunk_tail_at_end_offset",
]


@pytest.mark.parametrize("case_id", _CASE_IDS)
def test_fr_04_synthesis_concat(case_id):
    """FR-04: 4 concatenation cases (byte-level, no re-encode)."""
    if concat_mp3_chunks is None:  # RED-phase guard
        pytest.fail(
            "src.engines.synthesis must export concat_mp3_chunks"
        )

    from unittest.mock import patch

    # ── Case 6: concat byte length equals sum ────────────────────────────────
    if case_id == "concat_byte_length_equals_sum":
        # AC2: len(concatenated) == sum(len(c) for c in chunk_bytes)
        # Verified across 10 randomized inputs.
        import random
        random.seed(42)
        for _ in range(10):
            n = random.randint(2, 6)
            chunks = [
                bytes(random.randint(0, 255) for _ in range(random.randint(10, 100)))
                for __ in range(n)
            ]
            result = concat_mp3_chunks(chunks)
            expected_len = sum(len(c) for c in chunks)
            assert len(result) == expected_len, (
                f"AC2-byte-len-equals-sum: expected {expected_len}, "
                f"got {len(result)} for chunks with sizes "
                f"{[len(c) for c in chunks]}"
            )

    # ── Case 7: no ffmpeg invocation in concat path ──────────────────────────
    elif case_id == "no_ffmpeg_invocation_in_concat_path":
        # AC2-no-ffmpeg-in-concat: subprocess_run_call_count == 0
        chunk_bytes = [b"ID3", b"\xff\xfb", b"\xff\xfb"]
        with patch("subprocess.run") as mock_run:
            result = concat_mp3_chunks(chunk_bytes)
        assert mock_run.call_count == 0, (
            "concat_mp3_chunks must NOT invoke subprocess (no ffmpeg re-encode); "
            f"subprocess.run was called {mock_run.call_count} times "
            f"(SRS.md §3 FR-04 AC2 L216)"
        )
        assert isinstance(result, bytes), (
            "concat_mp3_chunks must return bytes"
        )

    # ── Case 8: first chunk header at offset zero ────────────────────────────
    elif case_id == "first_chunk_mp3_sync_at_offset_zero":
        # AC2-first-chunk-header-offset-zero: concatenated[:3] == chunk_bytes[0][:3]
        chunk_bytes = [b"ID3\x04\x00\x00\x00\x00\x00\x00\x00payload", b"more"]
        result = concat_mp3_chunks(chunk_bytes)
        assert result[:3] == chunk_bytes[0][:3], (
            f"first chunk's header must appear at offset 0 of concatenated output; "
            f"expected {chunk_bytes[0][:3]!r}, got {result[:3]!r} "
            f"(SRS.md §3 FR-04 AC2 L216)"
        )
        assert result[-4:] == b"more", (
            "last chunk's content must appear at end of concatenated output"
        )

    # ── Case 9: last chunk tail at end offset ────────────────────────────────
    elif case_id == "last_chunk_tail_at_end_offset":
        # AC2-last-chunk-tail-at-end: concatenated[-3:] == chunk_bytes[-1][-3:]
        chunk_bytes = [b"head", b"tail-end"]
        result = concat_mp3_chunks(chunk_bytes)
        assert result[-3:] == chunk_bytes[-1][-3:], (
            f"last chunk's tail must appear at the end of concatenated output; "
            f"expected {chunk_bytes[-1][-3:]!r}, got {result[-3:]!r} "
            f"(SRS.md §3 FR-04 AC2 L216)"
        )
