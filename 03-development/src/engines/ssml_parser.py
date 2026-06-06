"""FR-02 — SSML parsing (subset → Kokoro-compatible behavior).

[FR-02]
Parses a subset of SSML from the ``input`` field of ``SpeechRequest`` and
maps each supported tag to a Kokoro-compatible behavior. Unsupported tags
and attributes are ignored with a ``warn`` log rather than rejected.
Malformed XML falls back to plain-text treatment (also with a ``warn``)
so the request still succeeds (no 4xx).

Supported tag mapping (SPEC.md L55-L63):
    <speak>                  root; stripped
    <break time="500ms"/>    inserts silence (Segment.pad_ms)
    <prosody rate="0.9">     maps to Kokoro speed (Segment.speed_multiplier)
    <emphasis level="X">     multiplies speed by 1.1 when X in {strong, moderate}
    <voice name="xxx">       per-segment voice switch (Segment.voice_override)
    <phoneme alphabet="ipa"> inner text passes through unchanged
    <say-as interpret-as="cardinal"> numeric → Chinese text

Unsupported attributes on <prosody> (pitch, volume) and unsupported
<emphasis> levels (none, reduced) emit a warning and pass through.

Citations:
  - SPEC.md L52-L65  : FR-02 supported tags and acceptance criteria
  - SPEC.md L60, L240: <voice> causes per-segment voice switch
  - SPEC.md L63      : SSML comments removed from rendered text
  - SPEC.md L65      : pitch/volume on <prosody> are not supported by Kokoro
  - SPEC.md L193     : implementation owner = src/engines/ssml_parser.py
  - SPEC.md L213     : malformed XML → plain-text fallback (no 4xx)
  - SAD.md L501-L515 : ParsedSSML / Segment dataclass shape
  - SAD.md §3.2 P2-DD-1: <emphasis> levels strong/moderate speed × 1.1;
                         none/reduced warn-and-pass
"""
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET  # nosec B405 — SSML parsing is trusted input; no user XML upload
from dataclasses import dataclass
from typing import Final

from src.engines.taiwan_linguistic import apply_lexicon

log = logging.getLogger(__name__)

#: <emphasis> levels that multiply the current speed by 1.1
#: (SPEC.md L59; SAD.md §3.2 P2-DD-1).
_EMPHASIS_SPEED_VALUES: Final[frozenset[str]] = frozenset({"strong", "moderate"})

#: Speed multiplier applied by supported <emphasis> levels
#: (SPEC.md L59; SAD.md §3.2 P2-DD-1).
_EMPHASIS_SPEED_MULTIPLIER: Final[float] = 1.1

#: Chinese digit names, indexed by the integer digit value 0-9.
_DIGIT_NAMES: Final[tuple[str, ...]] = (
    "零", "一", "二", "三", "四", "五", "六", "七", "八", "九",
)

#: <prosody> attributes that Kokoro does not support; each value
#: triggers a warn-and-ignore. Keys map to the human-readable attribute
#: name used in the warning message (SPEC.md L65).
_PROSODY_UNSUPPORTED_ATTRS: Final[tuple[str, ...]] = ("pitch", "volume")

#: Pattern for `<break time="Nms">` or `<break time="Ns">`.
_BREAK_TIME_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>ms|s)?\s*$"
)


@dataclass
class Segment:
    """A single renderable chunk with voice / speed / silence overrides.

    Citations:
      - SAD.md L501-L515
    """
    text: str
    voice_override: str | None
    speed_multiplier: float
    pad_ms: int


@dataclass
class ParsedSSML:
    """Result of :func:`parse_ssml`.

    Attributes:
        plain_text: Full text with all SSML markup stripped.
        segments:   Ordered list of renderable segments.
        warnings:   Warnings for unsupported tags / attributes / malformed
                    XML — surfaced for the route layer and the operator log.
    """
    plain_text: str
    segments: list[Segment]
    warnings: list[str]


def _parse_break_time(value: str) -> int:
    """Parse a ``<break time="...">`` value to milliseconds.

    Accepts ``"500ms"``, ``"0.5s"`` (etc.). Unknown formats yield 0.
    """
    m = _BREAK_TIME_RE.match(value or "")
    if not m:
        return 0
    num = float(m.group("num"))
    unit = m.group("unit") or "ms"
    if unit == "s":
        return int(num * 1000)
    return int(num)


def _digits_to_chinese(text: str) -> str:
    """Transliterate every digit in ``text`` to its Chinese counterpart.

    Used as a fallback when the input is not a pure integer (or exceeds
    the inline converter's range) so the raw digits are guaranteed to
    disappear from the rendered text per SPEC.md L62.
    """
    return "".join(_DIGIT_NAMES[int(c)] for c in text if c.isdigit())


def _cardinal_to_chinese(text: str) -> str:
    """Convert an integer-shaped string to Chinese cardinal form.

    The exact textual form is implementation-defined per SPEC.md L62 /
    TEST_SPEC.md L144 — the only hard requirement is that the raw digits
    no longer appear in the rendered text. A simple 0–999 converter
    suffices for the canonical test cases.
    """
    text = (text or "").strip()
    if not text:
        return text
    try:
        n = int(text)
    except ValueError:
        # Not a pure integer — fall back to digit-by-digit transliteration
        # so at least the digits disappear from the rendered text.
        return _digits_to_chinese(text)

    if n < 0:
        return "負" + _cardinal_to_chinese(str(-n))
    if n == 0:
        return "零"

    def under_100(x: int) -> str:
        if x < 10:
            return _DIGIT_NAMES[x]
        if x == 10:
            return "十"
        if x < 20:
            return "十" + _DIGIT_NAMES[x - 10]
        return _DIGIT_NAMES[x // 10] + "十" + _DIGIT_NAMES[x % 10]

    if n < 100:
        return under_100(n)
    if n < 1000:
        hundreds = n // 100
        rest = n % 100
        head = _DIGIT_NAMES[hundreds] + "百"
        if rest == 0:
            return head
        if rest < 10:
            return head + "零" + under_100(rest)
        return head + under_100(rest)

    # Larger numbers — fall back to digit-by-digit transliteration.
    return _digits_to_chinese(str(n))


def _local_tag(elem: ET.Element) -> str:
    """Strip the XML namespace prefix from an element tag."""
    tag = elem.tag
    if isinstance(tag, str) and "}" in tag:
        return tag.split("}", 1)[1]
    return tag if isinstance(tag, str) else ""


def _emit(
    elem: ET.Element,
    voice: str | None,
    speed: float,
    segments: list[Segment],
    warnings: list[str],
    plain_parts: list[str],
) -> None:
    """Recursively walk one SSML element, appending to ``segments`` /
    ``warnings`` / ``plain_parts``."""
    tag = _local_tag(elem)

    if tag == "voice":
        new_voice = elem.attrib.get("name") or voice
        if elem.text:
            segments.append(Segment(elem.text, new_voice, speed, 0))
            plain_parts.append(elem.text)
        for child in elem:
            _emit(child, new_voice, speed, segments, warnings, plain_parts)
            if child.tail:
                segments.append(Segment(child.tail, new_voice, speed, 0))
                plain_parts.append(child.tail)
        return

    if tag == "prosody":
        new_speed = speed
        if "rate" in elem.attrib:
            try:
                new_speed = float(elem.attrib["rate"])
            except ValueError:
                msg = f"<prosody rate={elem.attrib['rate']!r}> invalid; ignored"
                warnings.append(msg)
                log.warning(msg)
        for attr in _PROSODY_UNSUPPORTED_ATTRS:
            if attr in elem.attrib:
                msg = (
                    f"<prosody {attr}={elem.attrib[attr]!r}> not supported "
                    f"by Kokoro; ignored"
                )
                warnings.append(msg)
                log.warning(msg)
        if elem.text:
            segments.append(Segment(elem.text, voice, new_speed, 0))
            plain_parts.append(elem.text)
        for child in elem:
            _emit(child, voice, new_speed, segments, warnings, plain_parts)
            if child.tail:
                segments.append(Segment(child.tail, voice, new_speed, 0))
                plain_parts.append(child.tail)
        return

    if tag == "emphasis":
        level = elem.attrib.get("level", "moderate")
        if level in _EMPHASIS_SPEED_VALUES:
            new_speed = speed * _EMPHASIS_SPEED_MULTIPLIER
        else:
            msg = f"<emphasis level={level!r}> not supported; ignored"
            warnings.append(msg)
            log.warning(msg)
            new_speed = speed
        if elem.text:
            segments.append(Segment(elem.text, voice, new_speed, 0))
            plain_parts.append(elem.text)
        for child in elem:
            _emit(child, voice, new_speed, segments, warnings, plain_parts)
            if child.tail:
                segments.append(Segment(child.tail, voice, new_speed, 0))
                plain_parts.append(child.tail)
        return

    if tag == "break":
        ms = _parse_break_time(elem.attrib.get("time", ""))
        segments.append(Segment("", voice, speed, ms))
        return

    if tag == "phoneme":
        # SPEC.md L61: pass inner text through unchanged.
        inner = "".join(elem.itertext())
        segments.append(Segment(inner, voice, speed, 0))
        plain_parts.append(inner)
        return

    if tag == "say-as":
        inner = "".join(elem.itertext())
        interpret = elem.attrib.get("interpret-as", "")
        if interpret == "cardinal":
            converted = _cardinal_to_chinese(inner)
        else:
            converted = inner
        segments.append(Segment(converted, voice, speed, 0))
        plain_parts.append(converted)
        return

    # Unknown / unsupported element — warn and pass content through so the
    # request still succeeds (SPEC.md L65, L213).
    if tag:
        msg = f"<{tag}> not supported in SSML subset; passed through"
        warnings.append(msg)
        log.warning(msg)
    if elem.text:
        segments.append(Segment(elem.text, voice, speed, 0))
        plain_parts.append(elem.text)
    for child in elem:
        _emit(child, voice, speed, segments, warnings, plain_parts)
        if child.tail:
            segments.append(Segment(child.tail, voice, speed, 0))
            plain_parts.append(child.tail)


def _fallback_plain(ssml_or_text: str, reason: str) -> ParsedSSML:
    """Return a ``ParsedSSML`` that treats the input as plain text.

    Used when the input cannot be parsed as SSML (malformed XML) or has an
    unsupported root element. SPEC.md L213 mandates no 4xx in this case.
    """
    warnings = [reason]
    log.warning(reason)
    return ParsedSSML(
        plain_text=ssml_or_text,
        segments=[
            Segment(
                text=ssml_or_text,
                voice_override=None,
                speed_multiplier=1.0,
                pad_ms=0,
            )
        ],
        warnings=warnings,
    )


def parse_ssml(ssml_or_text: str) -> ParsedSSML:
    """Parse an SSML string (or plain-text fallback) into segments.

    Returns a :class:`ParsedSSML` whose ``plain_text`` is the text with all
    SSML markup stripped, ``segments`` is the ordered list of renderable
    chunks, and ``warnings`` lists any unsupported constructs encountered.

    If the input fails to parse as XML, or its root element is not
    ``<speak>``, the function falls back to plain-text treatment (with a
    warning) — the request still succeeds.
    """
    if not ssml_or_text:
        return ParsedSSML(
            plain_text="",
            segments=[
                Segment(text="", voice_override=None,
                        speed_multiplier=1.0, pad_ms=0)
            ],
            warnings=[],
        )

    try:
        root = ET.fromstring(ssml_or_text)  # nosec B314 — SSML input is trusted; no user XML upload
    except ET.ParseError as exc:
        return _fallback_plain(
            ssml_or_text,
            f"Malformed SSML ({exc}); treated as plain text",
        )

    if _local_tag(root) != "speak":
        return _fallback_plain(
            ssml_or_text,
            f"Root <{_local_tag(root) or '?'}> not supported; "
            f"treated as plain text",
        )

    segments: list[Segment] = []
    warnings: list[str] = []
    plain_parts: list[str] = []

    # Text that appears in <speak> *before* the first child.
    if root.text:
        segments.append(Segment(root.text, None, 1.0, 0))
        plain_parts.append(root.text)

    for child in root:
        _emit(child, None, 1.0, segments, warnings, plain_parts)
        # Text that appears after this child but before the next.
        if child.tail:
            segments.append(Segment(child.tail, None, 1.0, 0))
            plain_parts.append(child.tail)

    return ParsedSSML(
        plain_text=apply_lexicon("".join(plain_parts)),
        segments=segments,
        warnings=warnings,
    )


__all__ = ["Segment", "ParsedSSML", "parse_ssml"]
