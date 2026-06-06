"""FR-03 — Intelligent text chunking (three-tier recursive splitter).

[FR-03]
Splits input text into chunks ≤ MAX_CHARS_PER_REQUEST characters using a
three-tier boundary strategy (L1 sentence → L2 clause → L3 phrase) with a
hard-cap force-split fallback. Pure function; no I/O; no network access.

Citations:
  - SPEC.md L67-L75  : three-tier splitter algorithm (L1/L2/L3 + hard cap)
  - SPEC.md L127     : MAX_CHARS_PER_REQUEST = 250
  - SRS.md §3 FR-03  : 5 acceptance criteria (L190-L208)
  - SAD.md §3.3, §5.4: module role and data flow
  - ADR.md ADR-03    : 100-char threshold for L2/L3 invocation (P2-DD-2)
"""
from __future__ import annotations

import re
from typing import Final

# Re-export so tests can import MAX_CHARS_PER_REQUEST directly from this module.
from src.infrastructure.config import MAX_CHARS_PER_REQUEST  # noqa: F401  (public re-export)

# --- Boundary sets (SPEC.md L72-L74) -----------------------------------------
_L1_PATTERN: Final[re.Pattern[str]] = re.compile(r"(?<=[。？！!?\n])")
_L2_PATTERN: Final[re.Pattern[str]] = re.compile(r"(?<=[；:])")
_L3_PATTERN: Final[re.Pattern[str]] = re.compile(r"(?<=[，])")

# Threshold above which L2/L3 are invoked (ADR-03, SAD.md §3.3).
_OPTIMAL_THRESHOLD: Final[int] = 100


def _force_split(text: str, cap: int) -> list[str]:
    """Hard-cap force-split: slice *text* into pieces of exactly *cap* chars."""
    return [text[i : i + cap] for i in range(0, len(text), cap)]


def _simple_split(text: str, pattern: re.Pattern[str]) -> list[str]:
    """Split *text* at every *pattern* match; no greedy merging."""
    return [s for s in pattern.split(text) if s]


def _apply_boundary_tier(
    segments: list[str], pattern: re.Pattern[str], threshold: int
) -> list[str]:
    """Split each segment longer than *threshold* at *pattern*; pass others through."""
    result: list[str] = []
    for seg in segments:
        if len(seg) > threshold:
            result.extend(_simple_split(seg, pattern))
        else:
            result.append(seg)
    return result


def split_text(text: str) -> list[str]:
    """Split *text* into chunks of at most MAX_CHARS_PER_REQUEST characters.

    [FR-03]
    Algorithm (three-tier, SPEC.md L71-L74, SRS.md §3 FR-03 L190-L208):

      1. Empty text → [].
      2. Split at every L1 sentence boundary (。？！!?\\n).
      3. For any segment > _OPTIMAL_THRESHOLD, split at L2 clause boundaries (；:).
      4. For any segment still > _OPTIMAL_THRESHOLD, split at L3 phrase boundaries (，).
      5. Any segment still > MAX_CHARS_PER_REQUEST → hard-cap force-split.

    Citations:
      - SPEC.md L67-L75  : algorithm spec
      - SRS.md §3 FR-03  : acceptance criteria
      - ADR.md ADR-03    : 100-char threshold for L2/L3 invocation
    """
    if not text:
        return []

    cap = MAX_CHARS_PER_REQUEST

    # Tier 1: split at L1 sentence boundaries (lookbehind keeps boundary char
    # in left segment; never merge across L1 to preserve case-10 semantics).
    segments = [s for s in _L1_PATTERN.split(text) if s]

    # Tiers 2 and 3: progressively refine oversized segments.
    segments = _apply_boundary_tier(segments, _L2_PATTERN, _OPTIMAL_THRESHOLD)
    segments = _apply_boundary_tier(segments, _L3_PATTERN, _OPTIMAL_THRESHOLD)

    # Hard-cap fallback for segments with no boundary at all.
    result: list[str] = []
    for seg in segments:
        if len(seg) > cap:
            result.extend(_force_split(seg, cap))
        else:
            result.append(seg)

    return result


