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

    # --- AC5 (sub-assertion, cases 3 and 8): Bopomofo entries must be
    # emitted as space-separated syllables (SPEC.md L41, L47).
    if source in ("垃圾", "和"):
        assert " " in expected, (
            f"Bopomofo expected value for {source!r} must be "
            f"space-separated (SPEC.md L41, L47); got {expected!r}"
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
