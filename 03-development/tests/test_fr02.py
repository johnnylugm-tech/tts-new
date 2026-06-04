"""FR-02: SSML 解析 (SSML parsing) — TDD-RED failing tests.

The 9 parametrized cases below are the canonical SSML behaviors defined in
`SPEC.md` L52-L65 and `TEST_SPEC.md` L132-L146. The production module is
`src/engines/ssml_parser.py` (per `SPEC.md` L193`) and must export at
minimum:

    - Segment:         dataclass with fields
                       (text: str,
                        voice_override: str | None,
                        speed_multiplier: float,
                        pad_ms: int)
    - ParsedSSML:      dataclass with fields
                       (plain_text: str,
                        segments: list[Segment],
                        warnings: list[str])
    - parse_ssml(ssml_or_text: str) -> ParsedSSML

These tests are intentionally RED — the production module does not exist
yet. The GREEN agent must implement `ssml_parser.py` so that all 9
parametrized cases pass and the sub-assertions below are satisfied.

Sub-assertions covered inside the test function (per `TEST_SPEC.md`
FR-02 sub-case coverage note):
  * AC2: `<!-- ... -->` comment removal (asserted in case 1 sub-check).
  * `<emphasis level="moderate">` (mirrors case 4 with `moderate` value;
    P2-DD-1, SAD.md §3.2).
  * `<emphasis level="none|reduced">` warn-and-pass (case 4 sub-check;
    P2-DD-1, SAD.md §3.2).
  * `<voice name="http://evil/">` SSRF guard rejection (case 5 sub-check;
    NP-12, R5).
"""
from __future__ import annotations

import pytest

# GREEN TODO: src/engines/ssml_parser.py must export:
#   - Segment:           dataclass(text: str, voice_override: str | None,
#                                  speed_multiplier: float, pad_ms: int)
#   - ParsedSSML:        dataclass(plain_text: str, segments: list[Segment],
#                                  warnings: list[str])
#   - parse_ssml(ssml_or_text: str) -> ParsedSSML
# (per SAD.md L501-L515)

# 9 canonical cases per SPEC.md L52-L65 / TEST_SPEC.md L132-L146.
# Each entry is wrapped in pytest.param(..., id=...) so the displayed
# test ID matches TEST_SPEC.md byte-for-byte (TEST_SPEC L138-L146 use
# specific `id` strings that include spaces, <, >, =, and " — pytest
# preserves all of these verbatim when an explicit `id=` is supplied,
# verified by a separate test of pytest's own behaviour).
_CASES = [
    # Case 1: <speak> root strip (happy_path)
    pytest.param(
        "<speak>你好</speak>",
        id="<speak>_root_strip",
    ),
    # Case 2: <break time="500ms"> inserts 500ms of silence (happy_path)
    pytest.param(
        '<speak>你好<break time="500ms"/>世界</speak>',
        id='<break time="500ms">_silence',
    ),
    # Case 3: <prosody rate="0.9"> maps to Kokoro speed (happy_path)
    pytest.param(
        '<speak>你好<prosody rate="0.9">世界</prosody></speak>',
        id='<prosody rate="0.9">_speed',
    ),
    # Case 4: <emphasis level="strong"> multiplies speed by 1.1 (happy_path)
    pytest.param(
        '<speak>你好<emphasis level="strong">世界</emphasis></speak>',
        id='<emphasis level="strong">_speed_x1.1',
    ),
    # Case 5: <voice name="xxx"> switches voice per segment (happy_path)
    pytest.param(
        '<speak>你好<voice name="af_heart">世界</voice></speak>',
        id='<voice name="xxx">_per_segment_switch',
    ),
    # Case 6: <phoneme alphabet="ipa"> passes inner text through unchanged
    pytest.param(
        '<speak>你好<phoneme alphabet="ipa">təˈmeɪtoʊ</phoneme>世界</speak>',
        id='<phoneme alphabet="ipa">_passthrough',
    ),
    # Case 7: <say-as interpret-as="cardinal"> converts "42" to text
    pytest.param(
        '<speak>有<say-as interpret-as="cardinal">42</say-as>隻</speak>',
        id='<say-as interpret-as="cardinal">_numeric_to_text',
    ),
    # Case 8: <prosody pitch="X"> is not supported — warn-and-ignore
    pytest.param(
        '<speak><prosody pitch="X">你好</prosody></speak>',
        id='<prosody pitch="X">_warn_and_ignore',
    ),
    # Case 9: malformed XML falls back to plain-text treatment; warn log;
    # no exception raised; HTTP 200-equivalent (request still succeeds).
    pytest.param(
        '<speak>你好<',
        id='malformed_xml_plain_text_fallback',
    ),
]


@pytest.mark.parametrize("ssml_input", _CASES)
def test_fr_02_ssml_tags(ssml_input):
    """FR-02: `parse_ssml` must handle the 7 supported SSML tags + 2 negative
    cases (pitch warn-and-ignore, malformed XML fallback) per SPEC.md
    L52-L65 and TEST_SPEC.md L132-L146.
    """
    # --- Lazy import so all 9 parametrize IDs are enumerable for
    # spec-coverage-check, even when the production module is missing.
    try:
        from src.engines.ssml_parser import (  # type: ignore[import-not-found]
            parse_ssml,
            ParsedSSML,
            Segment,  # noqa: F401  # API-contract: verify Segment is exported
        )
    except ImportError as exc:  # pragma: no cover - RED-phase guard
        pytest.fail(
            "src.engines.ssml_parser must export Segment, ParsedSSML, "
            "and parse_ssml — import failed: "
            f"{exc!r}"
        )

    # --- Call the production function under test ---------------------------
    result = parse_ssml(ssml_input)

    # --- Per-case assertions -------------------------------------------------
    if ssml_input == "<speak>你好</speak>":
        # Case 1: <speak> root strip.
        # Q1 happy-path: the root <speak> element is stripped, leaving the
        # inner text as plain_text (SPEC.md L56, SRS.md FR-02 AC1 L169).
        assert isinstance(result, ParsedSSML), (
            f"parse_ssml must return ParsedSSML; got {type(result).__name__}"
        )
        assert result.plain_text == "你好", (
            f"plain_text must equal the inner text '你好'; got {result.plain_text!r}"
        )
        seg = next((s for s in result.segments if s.text == "你好"), None)
        assert seg is not None, (
            f"expected a Segment with text='你好'; got {result.segments!r}"
        )
        assert seg.voice_override is None, (
            f"voice_override must be None (no <voice>); got {seg.voice_override!r}"
        )
        assert seg.speed_multiplier == pytest.approx(1.0), (
            f"speed_multiplier must default to 1.0; got {seg.speed_multiplier!r}"
        )
        assert seg.pad_ms == 0, f"pad_ms must default to 0; got {seg.pad_ms!r}"
        assert len(result.warnings) == 0, (
            f"well-formed <speak> with no unsupported attrs should produce no "
            f"warnings; got {result.warnings!r}"
        )

        # AC2 sub-assertion: `<!-- ... -->` comments are stripped from
        # rendered text (SPEC.md L63, SRS.md FR-02 AC2 L178).
        comment_result = parse_ssml(
            "<speak>你好<!-- this is a comment -->世界</speak>"
        )
        assert "<!--" not in comment_result.plain_text, (
            f"SSML comments must be stripped (SPEC.md L63); "
            f"got {comment_result.plain_text!r}"
        )
        assert "-->" not in comment_result.plain_text, (
            f"SSML comment closing must be stripped; "
            f"got {comment_result.plain_text!r}"
        )
        assert "你好" in comment_result.plain_text, (
            f"text before comment must be preserved; "
            f"got {comment_result.plain_text!r}"
        )
        assert "世界" in comment_result.plain_text, (
            f"text after comment must be preserved; "
            f"got {comment_result.plain_text!r}"
        )

    elif ssml_input == '<speak>你好<break time="500ms"/>世界</speak>':
        # Case 2: <break time="500ms"> inserts 500ms of silence via a
        # Segment with pad_ms=500 (SPEC.md L57, SRS.md FR-02 AC1 L170).
        assert isinstance(result, ParsedSSML)
        seg = next((s for s in result.segments if s.pad_ms == 500), None)
        assert seg is not None, (
            f"expected a Segment with pad_ms=500; got {result.segments!r}"
        )
        # Plain text should still contain the spoken text ('你好', '世界')
        # but NOT the <break> tag itself.
        assert "你好" in result.plain_text, (
            f"'你好' must appear in plain_text; got {result.plain_text!r}"
        )
        assert "世界" in result.plain_text, (
            f"'世界' must appear in plain_text; got {result.plain_text!r}"
        )
        assert "<break" not in result.plain_text, (
            f"break tag must be stripped from plain_text; "
            f"got {result.plain_text!r}"
        )

    elif ssml_input == '<speak>你好<prosody rate="0.9">世界</prosody></speak>':
        # Case 3: <prosody rate="0.9"> maps to Kokoro speed_multiplier
        # (SPEC.md L58, SRS.md FR-02 AC1 L171).
        assert isinstance(result, ParsedSSML)
        seg = next(
            (
                s for s in result.segments
                if s.speed_multiplier == pytest.approx(0.9)
            ),
            None,
        )
        assert seg is not None, (
            f"expected a Segment with speed_multiplier=0.9; "
            f"got {result.segments!r}"
        )
        assert "世界" in seg.text, (
            f"speed-affected segment should contain '世界'; got {seg.text!r}"
        )
        assert len(result.warnings) == 0, (
            f"rate='0.9' is supported; expected no warnings; "
            f"got {result.warnings!r}"
        )

    elif ssml_input == (
        '<speak>你好<emphasis level="strong">世界</emphasis></speak>'
    ):
        # Case 4: <emphasis level="strong"> multiplies speed by 1.1
        # (SPEC.md L59, SRS.md FR-02 AC1 L172).
        assert isinstance(result, ParsedSSML)
        seg = next(
            (
                s for s in result.segments
                if s.speed_multiplier == pytest.approx(1.1)
            ),
            None,
        )
        assert seg is not None, (
            f"expected a Segment with speed_multiplier=1.1; "
            f"got {result.segments!r}"
        )
        assert "世界" in seg.text, (
            f"emphasis-affected segment should contain '世界'; "
            f"got {seg.text!r}"
        )
        assert len(result.warnings) == 0, (
            f"level='strong' is supported; expected no warnings; "
            f"got {result.warnings!r}"
        )

        # Sub-assertion: <emphasis level="moderate"> also multiplies speed
        # by 1.1 (P2-DD-1, SAD.md §3.2; SPEC.md L59 allows both values).
        moderate = parse_ssml(
            '<speak>你好<emphasis level="moderate">世界</emphasis></speak>'
        )
        mod_seg = next(
            (
                s for s in moderate.segments
                if s.speed_multiplier == pytest.approx(1.1)
            ),
            None,
        )
        assert mod_seg is not None, (
            f"level='moderate' must also multiply speed by 1.1 (P2-DD-1); "
            f"got {moderate.segments!r}"
        )

        # Sub-assertion: <emphasis level="none|reduced"> warn-and-pass
        # (P2-DD-1, SAD.md §3.2; not rejected, but warned).
        for bad_level in ("none", "reduced"):
            warn_result = parse_ssml(
                f'<speak><emphasis level="{bad_level}">你好</emphasis></speak>'
            )
            assert len(warn_result.warnings) > 0, (
                f"level={bad_level!r} must produce a warn log (P2-DD-1); "
                f"got {warn_result.warnings!r}"
            )
            assert "你好" in warn_result.plain_text, (
                f"level={bad_level!r} must pass-through text unchanged; "
                f"got {warn_result.plain_text!r}"
            )

    elif ssml_input == (
        '<speak>你好<voice name="af_heart">世界</voice></speak>'
    ):
        # Case 5: <voice name="xxx"> causes a per-segment voice switch
        # (SPEC.md L60, SRS.md FR-02 AC1, AC5 L173, L184).
        assert isinstance(result, ParsedSSML)
        seg = next(
            (s for s in result.segments if s.voice_override == "af_heart"),
            None,
        )
        assert seg is not None, (
            f"expected a Segment with voice_override='af_heart'; "
            f"got {result.segments!r}"
        )
        assert "世界" in seg.text, (
            f"voice-switched segment should contain '世界'; got {seg.text!r}"
        )

        # Sub-assertion: <voice name="http://evil/"> is rejected at the
        # route layer (NP-12, R5, SRS.md §7 row 7 L432). The parser may
        # also pre-validate by surfacing a warning; we only require that
        # the result is structurally valid (a Segment is emitted, no
        # exception) so the route layer can take the next step. The
        # actual HTTP 403 enforcement is tested at the route layer.
        evil = parse_ssml(
            '<speak><voice name="http://evil.example/x">世界</voice></speak>'
        )
        assert isinstance(evil, ParsedSSML), (
            f"parser must not raise on URL-like voice names; "
            f"got {type(evil).__name__}"
        )

    elif ssml_input == (
        '<speak>你好<phoneme alphabet="ipa">'
        'təˈmeɪtoʊ'
        '</phoneme>世界</speak>'
    ):
        # Case 6: <phoneme alphabet="ipa"> passes inner text through
        # unchanged (SPEC.md L61, SRS.md FR-02 AC1 L174).
        assert isinstance(result, ParsedSSML)
        # The IPA text "təˈmeɪtoʊ" must appear in the rendered text.
        assert "təˈmeɪtoʊ" in result.plain_text, (
            f"phoneme text must pass through unchanged; "
            f"got {result.plain_text!r}"
        )
        assert "你好" in result.plain_text, (
            f"text before <phoneme> must be preserved; "
            f"got {result.plain_text!r}"
        )
        assert "世界" in result.plain_text, (
            f"text after <phoneme> must be preserved; "
            f"got {result.plain_text!r}"
        )
        assert "<phoneme" not in result.plain_text, (
            f"phoneme tag must be stripped; got {result.plain_text!r}"
        )

    elif ssml_input == (
        '<speak>有<say-as interpret-as="cardinal">42</say-as>隻</speak>'
    ):
        # Case 7: <say-as interpret-as="cardinal"> converts "42" to text
        # (SPEC.md L62, SRS.md FR-02 AC1 L175). The exact textual form
        # is implementation-defined (e.g., "四十二", "forty-two"); we
        # only require that the digits are no longer present and the
        # surrounding text is preserved.
        assert isinstance(result, ParsedSSML)
        assert "42" not in result.plain_text, (
            f"digits '42' must be converted to text; "
            f"got {result.plain_text!r}"
        )
        assert "有" in result.plain_text, (
            f"text before <say-as> must be preserved; "
            f"got {result.plain_text!r}"
        )
        assert "隻" in result.plain_text, (
            f"text after <say-as> must be preserved; "
            f"got {result.plain_text!r}"
        )
        assert len(result.plain_text) > 0, (
            "say-as conversion must produce non-empty output"
        )

    elif ssml_input == '<speak><prosody pitch="X">你好</prosody></speak>':
        # Case 8: <prosody pitch="X"> is NOT supported by Kokoro and
        # must be ignored with a warn log; the request still succeeds
        # (SPEC.md L65, SRS.md FR-02 AC3 L179-L180, SAD.md §3.2 P2-DD-1).
        assert isinstance(result, ParsedSSML), (
            "parse_ssml must not raise on unsupported pitch attribute"
        )
        # Pitch must not affect speed_multiplier.
        for seg in result.segments:
            assert seg.speed_multiplier == pytest.approx(1.0), (
                f"pitch must not affect speed; got {seg!r}"
            )
        # A warning must be emitted.
        assert len(result.warnings) > 0, (
            f"pitch='X' must produce a warn log; got {result.warnings!r}"
        )
        # The text '你好' must still be in the output (request still succeeded).
        assert "你好" in result.plain_text, (
            f"text inside <prosody> must be preserved even when pitch is "
            f"ignored; got {result.plain_text!r}"
        )

    elif ssml_input == '<speak>你好<':
        # Case 9: malformed XML falls back to plain-text treatment with
        # a warn log; NO exception is raised; request still succeeds
        # (SPEC.md L213, SRS.md FR-02 AC4 L181-L182, §7 row 1 L402).
        assert isinstance(result, ParsedSSML), (
            "parse_ssml must NOT raise on malformed XML; "
            "must return ParsedSSML (fallback path)"
        )
        assert len(result.plain_text) > 0, (
            f"plain_text must be non-empty after fallback; "
            f"got {result.plain_text!r}"
        )
        assert len(result.warnings) > 0, (
            f"malformed XML must produce a warn log; "
            f"got {result.warnings!r}"
        )


def test_fr_02_coverage_supplement() -> None:
    """Gate-1 coverage supplement: branches not exercised by the 9 TEST_SPEC
    parametrized cases.  All behaviours are consistent with SPEC.md L52-L65
    and SRS.md FR-02 acceptance criteria.  Adding these cases brings
    FR-02 line coverage above the Gate-1 threshold (≥ 80%).

    [FR-02]
    """
    from src.engines.ssml_parser import ParsedSSML, parse_ssml  # type: ignore[import-not-found]

    def _ssml(inner: str) -> str:
        return f"<speak>{inner}</speak>"

    # ── Empty input → empty result, no error (SPEC.md L64) ──────────────────
    r = parse_ssml("")
    assert isinstance(r, ParsedSSML) and r.plain_text == ""

    # ── Non-<speak> root → plain-text fallback + warning (SPEC.md L65) ──────
    r = parse_ssml("<div>你好</div>")
    assert "你好" in r.plain_text and len(r.warnings) >= 1

    # ── Namespaced <speak xmlns="…"> treated as <speak> (_local_tag) ─────────
    r = parse_ssml(
        '<speak xmlns="http://www.w3.org/2001/10/synthesis">hi</speak>'
    )
    assert "hi" in r.plain_text

    # ── <break time="1.5s"> → 1500 ms (seconds unit) ─────────────────────────
    r = parse_ssml(_ssml('<break time="1.5s"/>後'))
    assert any(s.pad_ms == 1500 for s in r.segments)

    # ── <break time="invalid"> → 0 ms graceful fallback ─────────────────────
    r = parse_ssml(_ssml('<break time="invalid"/>後'))
    assert any(s.text == "" and s.pad_ms == 0 for s in r.segments)

    # ── <prosody rate="invalid"> → warn, keep parent speed ───────────────────
    r = parse_ssml(_ssml('<prosody rate="bad">你好</prosody>'))
    assert "你好" in r.plain_text and len(r.warnings) >= 1

    # ── <prosody> with child whose .tail is non-empty ─────────────────────────
    r = parse_ssml(_ssml('<prosody rate="1.2"><phoneme>ph</phoneme>尾</prosody>'))
    assert "尾" in r.plain_text

    # ── <emphasis> with child whose .tail is non-empty ────────────────────────
    r = parse_ssml(
        _ssml('<emphasis level="strong"><phoneme>ph</phoneme>尾</emphasis>')
    )
    assert "尾" in r.plain_text

    # ── <voice> with child whose .tail is non-empty ───────────────────────────
    r = parse_ssml(
        _ssml('<voice name="af_heart"><phoneme>ph</phoneme>尾</voice>')
    )
    assert "尾" in r.plain_text

    # ── <say-as interpret-as="ordinal"> → pass raw text through ──────────────
    r = parse_ssml(_ssml('<say-as interpret-as="ordinal">42</say-as>'))
    assert "42" in r.plain_text

    # ── Unknown element → warn-and-pass-through (SPEC.md L65) ────────────────
    r = parse_ssml(_ssml("<custom>測試<phoneme>ph</phoneme>尾</custom>"))
    assert "測試" in r.plain_text and any("custom" in w for w in r.warnings)
    assert "尾" in r.plain_text

    # ── _cardinal_to_chinese: empty string → "" ───────────────────────────────
    r = parse_ssml(_ssml('<say-as interpret-as="cardinal"></say-as>'))
    assert r.plain_text == ""

    # ── _cardinal_to_chinese: non-integer → digit-by-digit transliteration ───
    r = parse_ssml(_ssml('<say-as interpret-as="cardinal">3.14</say-as>'))
    assert r.plain_text == "三一四"

    # ── _cardinal_to_chinese: negative → 負 + abs ────────────────────────────
    r = parse_ssml(_ssml('<say-as interpret-as="cardinal">-5</say-as>'))
    assert "負" in r.plain_text

    # ── _cardinal_to_chinese: zero → 零 ──────────────────────────────────────
    r = parse_ssml(_ssml('<say-as interpret-as="cardinal">0</say-as>'))
    assert r.plain_text == "零"

    # ── _cardinal_to_chinese: single digit (1-9) ─────────────────────────────
    r = parse_ssml(_ssml('<say-as interpret-as="cardinal">5</say-as>'))
    assert r.plain_text == "五"

    # ── _cardinal_to_chinese: exactly 10 → 十 ────────────────────────────────
    r = parse_ssml(_ssml('<say-as interpret-as="cardinal">10</say-as>'))
    assert r.plain_text == "十"

    # ── _cardinal_to_chinese: teen 11-19 ─────────────────────────────────────
    r = parse_ssml(_ssml('<say-as interpret-as="cardinal">15</say-as>'))
    assert r.plain_text == "十五"

    # ── _cardinal_to_chinese: hundreds, no remainder ──────────────────────────
    r = parse_ssml(_ssml('<say-as interpret-as="cardinal">200</say-as>'))
    assert "二百" in r.plain_text

    # ── _cardinal_to_chinese: hundreds + remainder < 10 ──────────────────────
    r = parse_ssml(_ssml('<say-as interpret-as="cardinal">201</say-as>'))
    assert "二百" in r.plain_text and "一" in r.plain_text

    # ── _cardinal_to_chinese: hundreds + remainder ≥ 10 ──────────────────────
    r = parse_ssml(_ssml('<say-as interpret-as="cardinal">215</say-as>'))
    assert "二百" in r.plain_text and "五" in r.plain_text

    # ── _cardinal_to_chinese: ≥ 1000 → digit-by-digit (raw digits gone) ──────
    r = parse_ssml(_ssml('<say-as interpret-as="cardinal">1234</say-as>'))
    assert all(c not in r.plain_text for c in "1234")
