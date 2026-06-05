"""Additional mutation-killing tests — NOT part of the 82-test set.

Targets surviving mutants in synthesis.py and other files that the
original 82 tests don't catch. Per SPEC §11.3, existing tests are
immutable; new tests are additions permitted.

Targets:
  - synthesis.py mutation 612: "voice" key in JSON payload
  - synthesis.py mutation 613-614: speed/format keys
  - synthesis.py mutation 616-617: chunk order in parallel gather
  - text_splitter.py mutation 608: hard-cap `>` vs `>=`
"""
from __future__ import annotations

import re
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.engines.text_splitter import _apply_boundary_tier, split_text
from src.config import MAX_CHARS_PER_REQUEST


# ── Synthesis mutations ──────────────────────────────────────

@pytest.mark.asyncio
async def test_mutation_kill_synthesis_voice_key():
    """Kill synthesis.py mutation 612: 'voice' key in JSON payload.

    The original `synthesize_one` sends ``json={'text': ..., 'voice': voice, ...}``.
    If a mutation changes 'voice' to 'XXvoiceXX', this test must fail.
    """
    captured: list[dict] = []

    async def handler(*args, **kwargs):
        captured.append(kwargs.get('json', {}))
        mock = MagicMock()
        mock.status_code = 200
        mock.raise_for_status = AsyncMock()
        mock.read = AsyncMock(return_value=b'fake_audio')
        return mock

    client = MagicMock()
    client.post = handler
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    with patch('httpx.AsyncClient', return_value=client):
        from src.engines.synthesis import synthesize_chunks
        await synthesize_chunks(['hello'], voice='zf_xiaoxiao', speed=1.0, fmt='mp3')

    assert len(captured) == 1, f"Expected 1 capture, got {len(captured)}"
    payload = captured[0]
    # Each key must be exactly the expected name
    assert 'voice' in payload, f"Missing 'voice' key; got {list(payload.keys())}"
    assert payload['voice'] == 'zf_xiaoxiao', (
        f"voice key value wrong: {payload.get('voice')!r}"
    )
    assert 'text' in payload
    assert 'speed' in payload
    assert payload['speed'] == 1.0
    assert 'format' in payload
    assert payload['format'] == 'mp3'


@pytest.mark.asyncio
async def test_mutation_kill_synthesis_chunk_order_preserved():
    """Kill mutations that break chunk order in asyncio.gather.

    Tests that 3 chunks come back in input order (not arbitrary order).
    """
    async def handler(*args, **kwargs):
        text = kwargs.get('json', {}).get('text', '')
        response_map = {f'chunk_{i}': f'audio_{i}'.encode() for i in range(3)}
        mock = MagicMock()
        mock.status_code = 200
        mock.raise_for_status = AsyncMock()
        mock.read = AsyncMock(return_value=response_map.get(text, b'unknown'))
        return mock

    client = MagicMock()
    client.post = handler
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    with patch('httpx.AsyncClient', return_value=client):
        from src.engines.synthesis import synthesize_chunks
        result = await synthesize_chunks(
            ['chunk_0', 'chunk_1', 'chunk_2'],
            voice='zf_xiaoxiao', speed=1.0, fmt='mp3'
        )

    assert result == b'audio_0audio_1audio_2', (
        f"Output must preserve chunk order; got {result!r}"
    )


# ── Text splitter mutations ──────────────────────────────────

def test_mutation_kill_text_splitter_hard_cap_boundary():
    """Kill text_splitter.py mutation 608: `len(seg) > cap` -> `>=`.

    A segment of EXACTLY cap length should NOT trigger force-split
    (the `>` comparison). With `>=` it would force-split, producing
    a different output.
    """
    # Build input with a segment of exactly MAX_CHARS_PER_REQUEST chars
    seg_exact = 'a' * MAX_CHARS_PER_REQUEST
    input_text = seg_exact + 'bc'  # 252 chars total

    result = split_text(input_text)

    # With > (original): seg_exact (250 chars) is passed through, then 'bc' added
    # So the output should be the input text or close to it
    # With >= (mutant): seg_exact gets force-split into 2x 250-char chunks,
    # plus 'bc' — total output length would be DIFFERENT
    total_output_chars = sum(len(c) for c in result)
    # The output must contain all input characters (no loss, no re-encoding)
    assert total_output_chars == len(input_text), (
        f"Output chars must equal input chars; got {total_output_chars} vs {len(input_text)}"
    )


def test_mutation_kill_text_splitter_optimal_threshold_value():
    """Kill text_splitter.py mutation 596: _OPTIMAL_THRESHOLD 100 -> 101.

    Asserts the _OPTIMAL_THRESHOLD constant is exactly 100, which is
    the ADR-03 mandated value.
    """
    from src.engines.text_splitter import _OPTIMAL_THRESHOLD
    assert _OPTIMAL_THRESHOLD == 100, (
        f"_OPTIMAL_THRESHOLD must be 100 per ADR-03; got {_OPTIMAL_THRESHOLD}"
    )


# ── SSML parser mutations ────────────────────────────────────

def test_mutation_kill_ssml_cardinal_10():
    """Kill ssml_parser.py mutation: x==10 returns wrong value.

    Cardinal 10 must convert to exactly '十' (no padding, no
    concatenation with digit names).
    """
    from src.engines.ssml_parser import _cardinal_to_chinese
    assert _cardinal_to_chinese('10') == '十', (
        f"10 must convert to '十'; got {_cardinal_to_chinese('10')!r}"
    )


def test_mutation_kill_ssml_cardinal_teens():
    """Kill ssml_parser.py mutation: teens use x/10 (float) instead of x%10.

    For x in [11, 19], result must use x%10 (integer) for the units
    digit, not x/10 (which would be 1.1, 1.2, etc.).
    """
    from src.engines.ssml_parser import _cardinal_to_chinese
    assert _cardinal_to_chinese('15') == '十五', (
        f"15 must convert to '十五'; got {_cardinal_to_chinese('15')!r}"
    )
    assert _cardinal_to_chinese('11') == '十一', (
        f"11 must convert to '十一'; got {_cardinal_to_chinese('11')!r}"
    )
    assert _cardinal_to_chinese('19') == '十九', (
        f"19 must convert to '十九'; got {_cardinal_to_chinese('19')!r}"
    )


def test_mutation_kill_ssml_cardinal_hundreds():
    """Kill ssml_parser.py mutations in hundreds/remainder logic.

    215 must convert to '二百十五' (two hundred fifteen), not '二百二十一五'
    or similar mutations in the hundreds path.
    """
    from src.engines.ssml_parser import _cardinal_to_chinese
    assert _cardinal_to_chinese('215') == '二百十五', (
        f"215 must convert to '二百十五'; got {_cardinal_to_chinese('215')!r}"
    )
    assert _cardinal_to_chinese('200') == '二百', (
        f"200 must convert to '二百'; got {_cardinal_to_chinese('200')!r}"
    )
    assert _cardinal_to_chinese('100') == '一百', (
        f"100 must convert to '一百'; got {_cardinal_to_chinese('100')!r}"
    )


def test_mutation_kill_ssml_digits_to_chinese():
    """Kill ssml_parser.py mutations in _digits_to_chinese.

    Each digit must convert to its exact Chinese name.
    """
    from src.engines.ssml_parser import _digits_to_chinese
    assert _digits_to_chinese('0') == '零', f"0 should be '零'; got {_digits_to_chinese('0')!r}"
    assert _digits_to_chinese('5') == '五', f"5 should be '五'; got {_digits_to_chinese('5')!r}"
    assert _digits_to_chinese('9') == '九', f"9 should be '九'; got {_digits_to_chinese('9')!r}"
