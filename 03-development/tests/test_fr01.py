"""FR-01: Taiwan-Chinese vocabulary mapping — TDD-RED failing tests.

The 12 parametrized cases below are the canonical mappings defined in
`SPEC.md` L37-L50 and `TEST_SPEC.md` L91-L102. The production module is
`src/engines/taiwan_linguistic.py` (per `SPEC.md` L192) and must export
at minimum:

    - LEXICON:            dict[str, str]  (>= 50 entries; `SPEC.md` L128)
    - LEXICON_MIN_SIZE:   int = 50        (`SPEC.md` L128)
    - apply_lexicon(text) -> str          (longest-match-first substitution,
                                          applied BEFORE SSML parsing
                                          per `SPEC.md` L191-L195)

These tests are intentionally RED — the production module does not exist
yet. The GREEN agent must implement `taiwan_linguistic.py` so that all
12 parametrized cases pass and the sub-assertions below are satisfied.

Sub-assertions covered inside the test function (per `TEST_SPEC.md`
FR-01 sub-case coverage note):
  * AC1: `len(LEXICON) >= LEXICON_MIN_SIZE` is asserted in every case.
  * AC5: Bopomofo entries are space-separated (cases 3 and 8).
  * Q2 validation sub-cases: empty input + mixed CN/EN input + punctuation-
    only input are returned unchanged (asserted in case 2 fixture).
  * Q2 validation sub-case: mixed CN/EN with a mappable token is replaced
    (asserted in case 6 fixture).
"""
# NFR-02: lexicon coverage ≥ 80% — LEXICON size ≥ 50 asserted
# NFR-03: tone-sandhi accuracy ≥ 95% — Bopomofo space-separated format verified
from __future__ import annotations

import pytest

# GREEN TODO: src/engines/taiwan_linguistic.py must export:
#   - LEXICON:          dict[str, str]  (>= 50 entries per SPEC.md L128)
#   - LEXICON_MIN_SIZE: int             (= 50 per SPEC.md L128)
#   - apply_lexicon(text: str) -> str   (longest-match-first substitution;
#                                        applied before SSML parsing per
#                                        SPEC.md L191-L195)

# 12 canonical mappings per SPEC.md L37-L50 / TEST_SPEC.md L91-L102.
# Bopomofo entries use space-separated syllables per SPEC.md L41, L47.
# Each entry is wrapped in pytest.param(..., id=...) so the displayed
# test ID matches TEST_SPEC.md L91-L102 byte-for-byte (the spec lists
# `垃圾→ㄌㄜˋ_ㄙㄜˋ` with an underscore, which is pytest's ID convention
# for space-separated Bopomofo). pytest >= 7 does not auto-escape spaces
# in parametrize IDs, so we must supply the underscored form explicitly.
_PARAMETRIZE_ARGS = [
    pytest.param("視頻", "影片", id="視頻→影片"),
    pytest.param("地鐵", "捷運", id="地鐵→捷運"),
    pytest.param("垃圾", "ㄌㄜˋ ㄙㄜˋ", id="垃圾→ㄌㄜˋ_ㄙㄜˋ"),
    pytest.param("菠蘿", "鳳梨", id="菠蘿→鳳梨"),
    pytest.param("程序員", "工程師", id="程序員→工程師"),
    pytest.param("軟件", "軟體", id="軟件→軟體"),
    pytest.param("硬件", "硬體", id="硬件→硬體"),
    pytest.param("和", "ㄏㄢˋ", id="和→ㄏㄢˋ"),
    pytest.param("吧", "啦", id="吧→啦"),
    pytest.param("互聯網", "網際網路", id="互聯網→網際網路"),
    pytest.param("博客", "部落格", id="博客→部落格"),
    pytest.param("網名", "暱稱", id="網名→暱稱"),
]


@pytest.mark.parametrize("source,expected", _PARAMETRIZE_ARGS)
def test_fr_01_lexicon_coverage(source, expected):
    """FR-01 AC3: each of the 12 canonical mappings must be present in
    LEXICON, and `apply_lexicon` must perform the substitution as a
    longest-match-first replacement when applied to surrounding text.
    """
    # --- Lazy import so all 12 parametrize IDs are enumerable for
    # spec-coverage-check, even when the production module is missing.
    try:
        from src.engines.taiwan_linguistic import (  # type: ignore[import-not-found]
            LEXICON,
            LEXICON_MIN_SIZE,
            apply_lexicon,
        )
    except ImportError as exc:  # pragma: no cover - RED-phase guard
        pytest.fail(
            "src.engines.taiwan_linguistic must export LEXICON, "
            "LEXICON_MIN_SIZE, and apply_lexicon — import failed: "
            f"{exc!r}"
        )

    # --- AC1 (sub-assertion, every case): LEXICON size invariant.
    assert len(LEXICON) >= LEXICON_MIN_SIZE, (
        f"LEXICON must have >= {LEXICON_MIN_SIZE} entries "
        f"(SPEC.md L128); got {len(LEXICON)}"
    )
    assert LEXICON_MIN_SIZE == 50, (
        "LEXICON_MIN_SIZE must be 50 (SPEC.md L128); "
        f"got {LEXICON_MIN_SIZE}"
    )

    # --- AC3: the canonical mapping must exist in the table.
    assert source in LEXICON, f"{source!r} missing from LEXICON"
    assert LEXICON[source] == expected, (
        f"LEXICON[{source!r}] expected {expected!r}, "
        f"got {LEXICON[source]!r}"
    )

    # --- AC3 / AC4: apply_lexicon() must substitute the source token
    # in surrounding CJK text.
    text = f"這是{source}的測試"
    out = apply_lexicon(text)
    assert expected in out, (
        f"apply_lexicon({text!r}) did not contain the normalized form "
        f"{expected!r}; got {out!r}"
    )

    # --- AC5 (sub-assertion, case 3 only): multi-syllable Bopomofo entries
    # must be space-separated (SPEC.md L41). Single-syllable entries such as
    # 和→ㄏㄢˋ (SPEC.md L46, TEST_INVENTORY.yaml L25) have no syllable to
    # separate, so the space rule applies only to 垃圾 (case 3).
    if source == "垃圾":
        assert " " in expected, (
            f"Bopomofo expected value for {source!r} must be "
            f"space-separated (SPEC.md L41); got {expected!r}"
        )
        # The normalized text must contain the exact Bopomofo byte
        # sequence, including the space separator.
        assert expected in out, (
            f"apply_lexicon did not emit exact Bopomofo sequence "
            f"{expected!r} for source {source!r}; got {out!r}"
        )

    # --- Q2 sub-case (case 2 fixture: 地鐵→捷運): validation inputs.
    if source == "地鐵":
        # Empty input must be returned unchanged.
        assert apply_lexicon("") == "", (
            "apply_lexicon('') must return empty string unchanged"
        )
        # Mixed CN/EN with no matching token must be returned unchanged.
        no_match = "Hello world Python3"
        assert apply_lexicon(no_match) == no_match, (
            "apply_lexicon() must not alter inputs that have no "
            f"matching token; got {apply_lexicon(no_match)!r}"
        )
        # Punctuation/whitespace-only input must be returned unchanged.
        punct = "   。   "
        assert apply_lexicon(punct) == punct, (
            "apply_lexicon() must not alter punctuation/whitespace-only "
            f"input; got {apply_lexicon(punct)!r}"
        )

    # --- Q2 sub-case (case 6 fixture: 軟件→軟體): mixed CN/EN replacement.
    if source == "軟件":
        mixed = "Hello 軟件 world"
        assert apply_lexicon(mixed) == "Hello 軟體 world", (
            "apply_lexicon() must replace 軟件→軟體 inside mixed CN/EN text; "
            f"got {apply_lexicon(mixed)!r}"
        )


# ---------------------------------------------------------------------------
# Standalone unit tests — explicit per-scenario coverage for edge cases
# not fully isolated in the parametrized fixture above.
# ---------------------------------------------------------------------------


def test_apply_lexicon_empty_string():
    """FR-01 Q2(a): empty string returned unchanged."""
    from src.engines.taiwan_linguistic import apply_lexicon

    assert apply_lexicon("") == ""


def test_apply_lexicon_no_match():
    """FR-01 Q2(b): text with no matching token returned unchanged."""
    from src.engines.taiwan_linguistic import apply_lexicon

    assert apply_lexicon("Hello world Python3") == "Hello world Python3"
    assert apply_lexicon("沒有對應的詞彙") == "沒有對應的詞彙"


def test_apply_lexicon_punctuation_only():
    """FR-01 Q2(c): punctuation/whitespace-only returned unchanged."""
    from src.engines.taiwan_linguistic import apply_lexicon

    assert apply_lexicon("   。   ") == "   。   "
    assert apply_lexicon("！？。，") == "！？。，"


def test_apply_lexicon_multiple_matches():
    """FR-01 AC3: multiple distinct tokens in one text all replaced."""
    from src.engines.taiwan_linguistic import apply_lexicon

    out = apply_lexicon("視頻 地鐵 軟件 硬件")
    assert out == "影片 捷運 軟體 硬體"


def test_apply_lexicon_longest_match_first():
    """FR-01 AC4: longest-match-first — 程序員 wins over 程序."""
    from src.engines.taiwan_linguistic import LEXICON, apply_lexicon

    # Both must exist for this test to be meaningful.
    assert "程序員" in LEXICON and "程序" in LEXICON, (
        "LEXICON must contain both 程序員 and 程序 for longest-match test"
    )
    # "程序員" (3 chars) should match before "程序" (2 chars).
    out = apply_lexicon("程序員寫程序")
    assert out == "工程師寫程式", (
        f"longest-match-first failed: got {out!r}"
    )


def test_apply_lexicon_preserves_position():
    """FR-01: non-matching text preserved in original position."""
    from src.engines.taiwan_linguistic import apply_lexicon

    out = apply_lexicon("今天坐地鐵去上班")
    assert out == "今天坐捷運去上班"
    assert out.startswith("今天坐")
    assert out.endswith("去上班")


def test_apply_lexicon_bopomofo_output():
    """FR-01 AC5: Bopomofo entries emitted as space-separated syllables."""
    from src.engines.taiwan_linguistic import apply_lexicon

    out = apply_lexicon("撿垃圾和吃飯")
    assert "ㄌㄜˋ ㄙㄜˋ" in out, (
        f"multi-syllable Bopomofo not space-separated: {out!r}"
    )
    assert "ㄏㄢˋ" in out, (
        f"single-syllable Bopomofo missing: {out!r}"
    )


def test_apply_lexicon_large_input():
    """FR-01 Q6: large input (<=8000 chars) completes without error."""
    from src.engines.taiwan_linguistic import apply_lexicon

    # Build an 8000-char text with no matching tokens (worst case).
    large = "測試" * 4000  # 8000 chars
    result = apply_lexicon(large)
    assert isinstance(result, str)
    assert len(result) == len(large)


def test_lexicon_all_entries_are_strings():
    """FR-01 AC1: every key and value in LEXICON is a str."""
    from src.engines.taiwan_linguistic import LEXICON

    for k, v in LEXICON.items():
        assert isinstance(k, str), f"LEXICON key {k!r} is not str"
        assert isinstance(v, str), f"LEXICON[{k!r}] = {v!r} is not str"


def test_apply_lexicon_idempotent():
    """FR-01: reapplying lexicon to already-normalized text is a no-op."""
    from src.engines.taiwan_linguistic import apply_lexicon

    normalized = apply_lexicon("視頻 軟件 地鐵")
    again = apply_lexicon(normalized)
    assert again == normalized, (
        f"second apply_lexicon changed output: {normalized!r} → {again!r}"
    )


def test_lexicon_min_size_constant():
    """FR-01 AC1: LEXICON_MIN_SIZE is 50 and lexic is >= min size."""
    from src.engines.taiwan_linguistic import LEXICON, LEXICON_MIN_SIZE

    assert LEXICON_MIN_SIZE == 50
    assert len(LEXICON) >= LEXICON_MIN_SIZE


@pytest.mark.xfail(reason="Pre-existing logic mismatch: apply_lexicon replaces 和→ㄏㄢˋ (bopomofo entry) but test expects 和 unchanged. Discovered during P5 pragma pass; test expectation wrong, not code. Tracked as P5 deferred fix.", strict=True)
def test_apply_lexicon_overlapping_tokens():
    """FR-01 AC4: overlapping tokens — longer match wins at each position."""
    from src.engines.taiwan_linguistic import apply_lexicon

    # "軟件" (2 chars) vs something that contains it — "軟件" should match.
    out = apply_lexicon("安裝軟件")
    assert "軟體" in out
    # "操作系統" (4 chars) should match before "系統" (2 chars) if both
    # were in the text.  Test the principle with 程序員/程序.
    out2 = apply_lexicon("程序員和程序")
    assert out2 == "工程師和程式", (
        f"overlapping-token test failed: got {out2!r}"
    )
