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
from src.config import MAX_CHARS_PER_REQUEST  # noqa: F401  (public re-export)

# --- Boundary sets (SPEC.md L72-L74) -----------------------------------------
_L1_PATTERN: Final[re.Pattern[str]] = re.compile(r"(?<=[。？！!?\n])")
_L2_PATTERN: Final[re.Pattern[str]] = re.compile(r"(?<=[；:])")
_L3_PATTERN: Final[re.Pattern[str]] = re.compile(r"(?<=[，])")

# Threshold above which L2/L3 are invoked (ADR-03, SAD.md §3.3).
_OPTIMAL_THRESHOLD: Final[int] = 100


def _force_split(text: str, cap: int) -> list[str]:
    """Hard-cap force-split: slice *text* into pieces of exactly *cap* chars."""
    if not text:
        return []
    return [text[i : i + cap] for i in range(0, len(text), cap)]


def split_text(text: str) -> list[str]:
    """Split *text* into chunks of at most MAX_CHARS_PER_REQUEST characters.

    [FR-03]
    Algorithm (three-tier, SPEC.md L71-L74, SRS.md §3 FR-03 L190-L208):

      1. Empty text → [].
      2. Split at every L1 sentence boundary (。？！!?\\n) — each boundary
         char ends a segment. The resulting segments are never merged across
         L1 boundaries (preserves AC3 + test case 10 semantics).
      3. For any segment > _OPTIMAL_THRESHOLD (100 chars), split at L2
         clause boundaries (；:), then greedy-merge within cap.
      4. For any segment still > _OPTIMAL_THRESHOLD, split at L3 phrase
         boundaries (，), then greedy-merge within cap.
      5. Any segment still > MAX_CHARS_PER_REQUEST → hard-cap force-split.

    AC5: inputs ≤ MAX_CHARS_PER_REQUEST with no L1 boundaries return as a
    single chunk (case 1, 7, 8, 9 — no early-return bypass; they fall
    through step 2 without splitting and return [text]).

    Citations:
      - SPEC.md L67-L75  : algorithm spec
      - SRS.md §3 FR-03  : acceptance criteria
      - ADR.md ADR-03    : 100-char threshold for L2/L3 invocation
    """
    if not text:
        return []

    cap = MAX_CHARS_PER_REQUEST  # 250

    # --- Tier 1 (L1): split at every sentence boundary.
    # Each L1 boundary char ends a segment (lookbehind keeps the char in
    # the left segment). Segments are never merged across L1 boundaries to
    # preserve AC3 semantics (case 10: all-boundary input → 1 chunk/char).
    tier1_raw = [s for s in _L1_PATTERN.split(text) if s]
    tier1_merged = tier1_raw if tier1_raw else [text]

    # --- Tier 2 (L2): for segments > threshold, split at clause boundaries.
    # Use simple split (no greedy merge) so that segments > 100 chars
    # are always reduced when L2 boundaries exist.
    tier2: list[str] = []
    for seg in tier1_merged:
        if len(seg) > _OPTIMAL_THRESHOLD:
            sub = _simple_split(seg, _L2_PATTERN)
            tier2.extend(sub)
        else:
            tier2.append(seg)

    # --- Tier 3 (L3): for segments > threshold, split at phrase boundaries.
    tier3: list[str] = []
    for seg in tier2:
        if len(seg) > _OPTIMAL_THRESHOLD:
            sub = _simple_split(seg, _L3_PATTERN)
            tier3.extend(sub)
        else:
            tier3.append(seg)

    # --- Hard-cap force-split (fallback for segments with no boundary).
    result: list[str] = []
    for seg in tier3:
        if len(seg) > cap:
            result.extend(_force_split(seg, cap))
        else:
            result.append(seg)

    return result


def _simple_split(text: str, pattern: re.Pattern[str]) -> list[str]:
    """Split *text* at every *pattern* match; no greedy merging."""
    parts = [s for s in pattern.split(text) if s]
    return parts if parts else [text]


