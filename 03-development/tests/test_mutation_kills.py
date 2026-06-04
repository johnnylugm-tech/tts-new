"""Mutation-killing supplement — NOT part of the 82-test set.

Per SPEC §11.3, existing 82 tests must not be deleted or modified.
New test functions (additions) are permitted. This file targets
surviving mutmut mutations in text_splitter.py by testing boundary
conditions not covered by the parametrized 82-test suite.

Specifically:
  - mutation 596: ``len(seg) > threshold`` → ``len(seg) >= threshold``
    A segment of exactly 100 chars (L2/L3 threshold, ADR-03) should
    NOT be split (``>``), but IS split under the mutant (``>=``).
"""
from __future__ import annotations

import re

import pytest

from src.engines.text_splitter import _apply_boundary_tier


@pytest.mark.parametrize("case", [
    "L2_threshold_exact_100_not_split",
    "L3_threshold_exact_100_not_split",
])
def test_mutation_kill_boundary_tier(case: str):
    """Kill mutations in _apply_boundary_tier by testing exact-threshold inputs."""
    if case == "L2_threshold_exact_100_not_split":
        # L2: CJK boundary at punctuation. Segment of exactly 100 chars.
        # Original: len(seg) > 100 → False → not split → 1 segment
        # Mutant:   len(seg) >= 100 → True → split by pattern → possibly >1 segment
        seg_100 = "測試" * 50  # 50 × 2 chars = 100 chars (CJK)
        pattern = re.compile(r"[。！？]")
        result = _apply_boundary_tier([seg_100], pattern, threshold=100)
        # With > (original), segment is passed through (not split).
        # With >= (mutant), segment would be split, producing different output.
        assert len(result) == 1, (
            f"Exact-threshold segment must NOT be split with '>' operator. "
            f"Got {len(result)} chunks. If this fails, the mutation survived."
        )
        assert result[0] == seg_100

    elif case == "L3_threshold_exact_100_not_split":
        # L3: CJK/Latin split at boundary. Segment of exactly 100 chars.
        seg_100_cjk = "測試" * 50  # 100 CJK chars
        pattern = re.compile(r"(?<=[一-鿿])(?=[a-zA-Z])")
        result = _apply_boundary_tier([seg_100_cjk], pattern, threshold=100)
        assert len(result) == 1, (
            f"Exact-threshold CJK segment must NOT be split. "
            f"Got {len(result)} chunks."
        )
