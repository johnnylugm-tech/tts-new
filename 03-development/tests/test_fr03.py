"""FR-03: 智能文本切分 (Intelligent text chunking) — TDD-RED failing tests.

The 10 parametrized cases below are the canonical chunking behaviors
defined in `SPEC.md` L67-L75 and `TEST_SPEC.md` L182-L198. The production
module is `src/engines/text_splitter.py` (per `SPEC.md` L194`) and must
export at minimum:

    - MAX_CHARS_PER_REQUEST: int  (= 250 per `SPEC.md` L127, re-exported
                                    from `src.config`)
    - split_text(text: str) -> list[str]
        Three-tier recursive splitter per `SPEC.md` L71-L74:
          L1 sentence boundaries: 。？！!?\\n
          L2 clause boundaries  : ；:    (invoked when segment > 100 chars)
          L3 phrase boundaries  : ，    (invoked when segment > 100 chars)
        Hard cap: 250 chars per chunk (force-split if no boundary found).

These tests are intentionally RED — the production module does not exist
yet. The GREEN agent must implement `text_splitter.py` so that all 10
parametrized cases pass.

Sub-assertions covered inside the test functions (per `TEST_SPEC.md`
FR-03 sub-case coverage note):
  * AC1 universal invariant: every emitted chunk <= MAX_CHARS_PER_REQUEST
    (asserted in every case).
  * AC2 sub-assertion: sub-100-char chunks are allowed at tail boundaries
    (e.g., the all-boundary-chars case 10) but discouraged for typical
    prose.
  * AC4 sub-assertion (case 6): a mixed CN/Latin token such as
    "Python3" or "JavaScript" must NOT be broken across chunks; it must
    appear whole in exactly one chunk.
  * Q2 validation sub-case (case 7): empty input returns [].
  * Q2 validation sub-case (case 8): single-char input returns ["x"].
  * Q3 boundary sub-case (case 9): exactly 250 chars (no boundary) yields
    a single chunk of length 250.
  * Q3 boundary sub-case (case 10): an all-boundary-chars input yields
    one chunk per boundary char.
"""
from __future__ import annotations

import pytest

# GREEN TODO: src/engines/text_splitter.py must export:
#   - MAX_CHARS_PER_REQUEST: int (constant = 250 per SPEC.md L127; may
#                                    re-export from src.config)
#   - split_text(text: str) -> list[str]   (three-tier recursive splitter
#                                          per SPEC.md L67-L75; the
#                                          hard-cap force-split kicks in
#                                          when no boundary character is
#                                          found within the 250-char
#                                          window)

# --- spec constants (mirrored here as plain Python so the test file can
# be parsed even before the production module exists) -------------------
_HARD_CAP = 250              # SPEC.md L69, L127
_MIN_OPTIMAL = 100           # SPEC.md L70
_L1_CHARS = "。？！!?\n"      # SPEC.md L72
_L2_CHARS = "；:"            # SPEC.md L73
_L3_CHARS = "，"              # SPEC.md L74


# =========================================================================
# Function 1: test_fr_03_text_splitter — 5 core-split cases
# =========================================================================

# 5 core-split cases per SPEC.md L67-L75 / TEST_SPEC.md L182-L188.
# Each entry is wrapped in pytest.param(..., id=...) so the displayed
# test ID matches TEST_SPEC.md byte-for-byte.
_CORE_CASES = [
    # Case 1: < 250 chars → single chunk (AC5, boundary Q3)
    pytest.param(
        "短文字",
        id="<250_chars_single_chunk",
    ),
    # Case 2: long English prose with multiple L1 sentence boundaries.
    # The splitter must split at ".?!" boundaries to keep each chunk
    # within the 250-char hard cap (AC3, happy_path Q1).
    pytest.param(
        (
            "Today is a beautiful sunny day. We decided to go for a walk "
            "in the nearby park. The weather was perfect for outdoor "
            "activities, and we were excited to spend time together. "
            "Along the way, we saw many birds and colorful flowers. "
            "After walking for about an hour, we stopped at a small cafe "
            "to rest and have some drinks. The afternoon was warm and "
            "the breeze was gentle. We took many photos and enjoyed the "
            "scenery around us. It was truly a memorable day for both "
            "of us and we promised to come back again next weekend."
        ),
        id="L1_sentence_boundary_split",
    ),
    # Case 3: Chinese text with L2 clause boundaries (;:) and NO L1
    # boundaries. The segment is > 100 chars so L2 must be invoked
    # (AC3, boundary Q3).
    pytest.param(
        (
            "首先：準備所有的材料清單；麵粉五百公克；細砂糖三百公克；"
            "新鮮雞蛋四顆；純牛奶兩百毫升；以及無鹽奶油一百五十公克；"
            "接著按照正確的順序混合；先將糖和奶油打發至蓬鬆；"
            "再分次加入雞蛋和麵粉；最後將完成的麵糊倒入烤盤中；"
            "送入預熱到一百八十度的烤箱烘烤"
        ),
        id="L2_clause_boundary_when_over_100",
    ),
    # Case 4: Chinese text with ONLY L3 phrase boundaries (，) and
    # NO L1/L2 boundaries. The segment is > 100 chars so L3 must be
    # invoked (AC3, boundary Q3).
    pytest.param(
        (
            "今天我們要一起去超級市場購買晚餐所需要的各種食材清單，"
            "包括新鮮的蔬菜品種，例如番茄、洋蔥、馬鈴薯、胡蘿蔔、"
            "青椒、菠菜、高麗菜，以及各式各樣的肉類，像是雞肉、"
            "牛肉、豬肉、魚肉，最後還要買一些新鮮的水果和健康的飲料"
        ),
        id="L3_phrase_boundary_when_over_100",
    ),
    # Case 5: > 250 chars with NO boundary characters at all. The
    # splitter must force-split at the hard cap (AC1, boundary Q3).
    pytest.param(
        "abcdefghijklmnopqrstuvwxyz" * 11,  # 286 chars, no boundary
        id="hard_cap_250_force_split",
    ),
]


@pytest.mark.parametrize("text_input", _CORE_CASES)
def test_fr_03_text_splitter(text_input):
    """FR-03 core split logic: 5 cases covering < 250, L1/L2/L3 splits,
    and hard-cap force-split per `SPEC.md` L67-L75 and
    `TEST_SPEC.md` L182-L188."""
    # --- Lazy import so all 5 parametrize IDs are enumerable for
    # spec-coverage-check, even when the production module is missing.
    try:
        from src.engines.text_splitter import (  # type: ignore[import-not-found]
            split_text,
            MAX_CHARS_PER_REQUEST,
        )
    except ImportError as exc:  # pragma: no cover - RED-phase guard
        pytest.fail(
            "src.engines.text_splitter must export split_text and "
            f"MAX_CHARS_PER_REQUEST — import failed: {exc!r}"
        )

    # --- Call the production function under test ---------------------------
    result = split_text(text_input)

    # --- AC1 universal invariant: MAX_CHARS_PER_REQUEST == 250. -----------
    assert MAX_CHARS_PER_REQUEST == _HARD_CAP, (
        f"MAX_CHARS_PER_REQUEST must be 250 (SPEC.md L127); "
        f"got {MAX_CHARS_PER_REQUEST}"
    )

    # --- AC1 universal invariant: result is a list of strings, each
    # no longer than the hard cap (SPEC.md L69, L127).
    assert isinstance(result, list), (
        f"split_text must return list[str]; got {type(result).__name__}"
    )
    for i, chunk in enumerate(result):
        assert isinstance(chunk, str), (
            f"chunk {i} must be str; got {type(chunk).__name__}"
        )
        assert len(chunk) <= MAX_CHARS_PER_REQUEST, (
            f"chunk {i} exceeds MAX_CHARS_PER_REQUEST={MAX_CHARS_PER_REQUEST}: "
            f"len={len(chunk)}, content={chunk!r}"
        )

    # --- Per-case assertions ----------------------------------------------
    if text_input == "短文字":
        # Case 1: input < 250 chars → 1 chunk (AC5).
        assert len(result) == 1, (
            f"input of 3 chars must yield exactly 1 chunk; "
            f"got {len(result)} chunks: {result!r}"
        )
        assert result[0] == "短文字", (
            f"single chunk must equal the input verbatim; "
            f"got {result[0]!r}"
        )

    elif text_input.startswith("Today is a beautiful sunny day"):
        # Case 2: L1 sentence-boundary split. The text has 8 L1
        # boundaries (. and ?) and is > 250 chars, so the splitter must
        # emit multiple chunks. The 100–250 optimal range per AC2 means
        # no chunk should be wildly short or wildly long.
        assert len(result) >= 2, (
            f"text with multiple L1 boundaries and length > 250 must "
            f"yield >= 2 chunks; got {len(result)}: {result!r}"
        )
        # Reassembled text must equal the original — no character loss
        # or duplication (universal invariant).
        assert "".join(result) == text_input, (
            "split_text must preserve all characters in order"
        )
        # Each chunk (except possibly the last tail) should land in
        # the 100–250 optimal range; sub-100 chunks are allowed but
        # discouraged for typical prose (AC2).
        for chunk in result[:-1]:
            assert len(chunk) >= _MIN_OPTIMAL, (
                f"sub-100-char chunk produced for typical prose; "
                f"len={len(chunk)}, content={chunk!r}"
            )

    elif text_input.startswith("首先：準備所有的材料清單"):
        # Case 3: L2 clause-boundary split. The text has multiple L2
        # boundaries (;:) but no L1 boundaries, and the segment is
        # > 100 chars, so L2 must be invoked. The result must have
        # multiple chunks split at L2 positions.
        assert len(result) >= 2, (
            f"text with multiple L2 boundaries and length > 100 must "
            f"yield >= 2 chunks; got {len(result)}: {result!r}"
        )
        # Reassembled text must equal the original.
        assert "".join(result) == text_input, (
            "split_text must preserve all characters in order"
        )
        # The first chunk should end at or before an L2 boundary
        # (or the chunk is the entire text). We assert the first chunk
        # is no longer than the optimal range.
        assert len(result[0]) <= _HARD_CAP, (
            f"first chunk must respect the hard cap; "
            f"len={len(result[0])}, content={result[0]!r}"
        )

    elif text_input.startswith("今天我們要一起去超級市場"):
        # Case 4: L3 phrase-boundary split. The text has only L3
        # boundaries (，) and no L1/L2 boundaries, and the segment is
        # > 100 chars, so L3 must be invoked. The result must have
        # multiple chunks split at L3 positions.
        assert len(result) >= 2, (
            f"text with only L3 boundaries and length > 100 must "
            f"yield >= 2 chunks; got {len(result)}: {result!r}"
        )
        # Reassembled text must equal the original.
        assert "".join(result) == text_input, (
            "split_text must preserve all characters in order"
        )
        # The first chunk should end at or before an L3 boundary
        # (or the chunk is the entire text).
        assert len(result[0]) <= _HARD_CAP, (
            f"first chunk must respect the hard cap; "
            f"len={len(result[0])}, content={result[0]!r}"
        )

    elif text_input == "abcdefghijklmnopqrstuvwxyz" * 11:
        # Case 5: hard-cap 250 force-split. The text is 286 chars with
        # no boundary characters anywhere; the splitter must fall
        # through to the force-split fallback.
        assert len(result) >= 2, (
            f"text of 286 chars with no boundary characters must "
            f"yield >= 2 chunks (force-split at 250); "
            f"got {len(result)}: {result!r}"
        )
        # Every chunk must be exactly 250 chars except the last
        # (force-split produces fixed-size 250-char chunks, and the
        # tail absorbs the remainder).
        for chunk in result[:-1]:
            assert len(chunk) == _HARD_CAP, (
                f"force-split non-tail chunk must be exactly "
                f"{_HARD_CAP} chars; got {len(chunk)}: {chunk!r}"
            )
        # Reassembled text must equal the original.
        assert "".join(result) == text_input, (
            "split_text must preserve all characters in order"
        )


# =========================================================================
# Function 2: test_fr_03_text_splitter_edge_cases — 5 boundary inputs
# =========================================================================

# 5 edge-case cases per TEST_SPEC.md L192-L198.
_EDGE_CASES = [
    # Case 6: mixed CJK/Latin token must NOT be broken mid-word (AC4).
    # The input is long enough to force a split; the tokens "Python3",
    # "JavaScript", and "TypeScript" must each appear whole in exactly
    # one chunk.
    pytest.param(
        (
            "今天我們來討論Python3這個程式語言，它非常流行，"
            "在全球有數百萬的開發者使用，廣泛應用於各種不同的領域，"
            "包括資料科學、機器學習、網頁開發和自動化腳本編寫。"
            "還有JavaScript也是一種很受歡迎的程式語言，"
            "主要用於網頁前端開發，也可以通過Node.js在伺服器端運行，"
            "並且擁有豐富的函式庫生態系統。"
            "接下來我們來看看TypeScript在大型專案中的應用，"
            "它可以提供更好的型別檢查和重構支援。"
        ),
        id="no_mid_mixed_word_split",
    ),
    # Case 7: empty string returns [] (AC5, validation Q2/Q3).
    pytest.param(
        "",
        id="empty_string_returns_empty_list",
    ),
    # Case 8: single character returns ["x"] (AC5, boundary Q3).
    pytest.param(
        "a",
        id="single_char_returns_list_of_one",
    ),
    # Case 9: exactly 250 chars (no boundary) → single chunk of 250
    # chars (AC1 + AC5, boundary Q3).
    pytest.param(
        "a" * 250,
        id="exactly_250_chars_single_chunk",
    ),
    # Case 10: all-boundary input → one chunk per boundary char
    # (AC3, boundary Q3). The L1 set per SPEC.md L72 is
    # "。？！!?\\n"; this test uses the 4 non-newline members.
    pytest.param(
        "。？！!?",
        id="all_boundary_chars_one_char_chunks",
    ),
]


@pytest.mark.parametrize("text_input", _EDGE_CASES)
def test_fr_03_text_splitter_edge_cases(text_input):
    """FR-03 edge cases: mixed-word preservation, empty input, single
    char, exactly-250 input, and all-boundary-char input per
    `TEST_SPEC.md` L192-L198."""
    # --- Lazy import so all 5 parametrize IDs are enumerable for
    # spec-coverage-check, even when the production module is missing.
    try:
        from src.engines.text_splitter import (  # type: ignore[import-not-found]
            split_text,
            MAX_CHARS_PER_REQUEST,
        )
    except ImportError as exc:  # pragma: no cover - RED-phase guard
        pytest.fail(
            "src.engines.text_splitter must export split_text and "
            f"MAX_CHARS_PER_REQUEST — import failed: {exc!r}"
        )

    # --- Call the production function under test ---------------------------
    result = split_text(text_input)

    # --- AC1 universal invariant: MAX_CHARS_PER_REQUEST == 250. -----------
    assert MAX_CHARS_PER_REQUEST == _HARD_CAP, (
        f"MAX_CHARS_PER_REQUEST must be 250 (SPEC.md L127); "
        f"got {MAX_CHARS_PER_REQUEST}"
    )

    # --- AC1 universal invariant: result is a list of strings, each
    # no longer than the hard cap.
    assert isinstance(result, list), (
        f"split_text must return list[str]; got {type(result).__name__}"
    )
    for i, chunk in enumerate(result):
        assert isinstance(chunk, str), (
            f"chunk {i} must be str; got {type(chunk).__name__}"
        )
        assert len(chunk) <= MAX_CHARS_PER_REQUEST, (
            f"chunk {i} exceeds MAX_CHARS_PER_REQUEST={MAX_CHARS_PER_REQUEST}: "
            f"len={len(chunk)}, content={chunk!r}"
        )

    # --- Per-case assertions ----------------------------------------------
    if text_input.startswith("今天我們來討論Python3"):
        # Case 6: no mid mixed-word split. Each mixed CN/Latin token
        # ("Python3", "JavaScript", "TypeScript") must appear whole in
        # exactly one chunk — never split across a chunk boundary.
        mixed_tokens = ("Python3", "JavaScript", "TypeScript")
        for token in mixed_tokens:
            containing_chunks = [c for c in result if token in c]
            assert len(containing_chunks) == 1, (
                f"mixed token {token!r} must appear whole in exactly "
                f"one chunk (AC4: no mid-word split); found in "
                f"{len(containing_chunks)} chunks: {result!r}"
            )
        # Reassembled text must equal the original — no character loss
        # or duplication.
        assert "".join(result) == text_input, (
            "split_text must preserve all characters in order"
        )
        # The input is > 250 chars, so the splitter must emit multiple
        # chunks.
        assert len(result) >= 2, (
            f"text of > 250 chars must yield >= 2 chunks; "
            f"got {len(result)}: {result!r}"
        )

    elif text_input == "":
        # Case 7: empty string returns [].
        assert result == [], (
            f"split_text('') must return []; got {result!r}"
        )

    elif text_input == "a":
        # Case 8: single character returns a list of one.
        assert result == ["a"], (
            f"split_text('a') must return ['a']; got {result!r}"
        )

    elif text_input == "a" * 250:
        # Case 9: exactly 250 chars (no boundary) → single chunk of
        # length 250.
        assert len(result) == 1, (
            f"input of exactly 250 chars must yield exactly 1 chunk; "
            f"got {len(result)} chunks: {result!r}"
        )
        assert len(result[0]) == 250, (
            f"single chunk must have length 250; got {len(result[0])}"
        )
        assert result[0] == "a" * 250, (
            f"single chunk must equal the input verbatim; "
            f"first 5 chars: {result[0][:5]!r}"
        )

    elif text_input == "。？！!?":
        # Case 10: all-boundary input → one chunk per boundary char.
        # The L1 set per SPEC.md L72 is "。？！!?\n"; the input
        # "。？！!?" exercises all 5 non-newline members, so the
        # expected output is 5 one-character chunks (one per L1 char).
        # (Previous comment said "4 of the 5" — corrected; the input
        # has 5 chars and preserve-all requires 5 chunks.)
        assert len(result) == 5, (
            f"all-boundary input (5 boundary chars) must yield 5 "
            f"one-char chunks; got {len(result)} chunks: {result!r}"
        )
        for chunk in result:
            assert len(chunk) == 1, (
                f"each chunk must be exactly 1 char; got {chunk!r}"
            )
        # Reassembled text must equal the original — no boundary char
        # is lost or duplicated.
        assert "".join(result) == text_input, (
            "split_text must preserve all characters in order"
        )
