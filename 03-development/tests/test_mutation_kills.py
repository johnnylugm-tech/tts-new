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
        # Construct 100-char input that CONTAINS pattern but is NOT split
        # under original (>). Under mutant (>=), it IS split → different result.
        # 98 chars of CJK + 2 punctuation chars = 100 chars
        seg_100 = "。" + "測試" * 49 + "？"  # 100 chars with CJK punctuation
        assert len(seg_100) == 100, f"Expected 100 chars, got {len(seg_100)}"
        pattern = re.compile(r"[。！？]")
        result = _apply_boundary_tier([seg_100], pattern, threshold=100)
        # Original (>):   len(100) > 100 → False → pass-through → [seg_100] unchanged
        # Mutant (>=):    len(100) >= 100 → True → split by pattern → punctuation removed
        # The critical assertion: the segment content must be PRESERVED (not split)
        assert result == [seg_100], (
            f"Exact-threshold segment must NOT be split with '>' operator. "
            f"Mutation to '>=' would split and remove punctuation. "
            f"Got: {result}"
        )

    elif case == "L3_threshold_exact_100_not_split":
        # 100-char string with a CJK→Latin boundary.
        # Under original (>): not split. Under mutant (>=): split by boundary.
        seg_100 = "試" * 99 + "A"  # 99 CJK + 1 Latin = 100 chars
        assert len(seg_100) == 100, f"Expected 100 chars, got {len(seg_100)}"
        pattern = re.compile(r"(?<=[一-鿿])(?=[a-zA-Z])")
        result = _apply_boundary_tier([seg_100], pattern, threshold=100)
        # Original (>):  len(100) > 100 → False → pass-through → [seg_100]
        # Mutant (>=):   len(100) >= 100 → True → split at CJK-Latin boundary → 2 parts
        assert result == [seg_100], (
            f"Exact-threshold CJK segment must NOT be split. "
            f"Mutation to '>=' would split at CJK-Latin boundary. "
            f"Got: {result}"
        )
