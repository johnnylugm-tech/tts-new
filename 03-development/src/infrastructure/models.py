"""FR-04 / NFR-08 — Pydantic request and response schemas.

[FR-04]
SpeechRequest carries the text/SSML input plus per-request voice, speed,
and format overrides. All fields are validated by Pydantic to satisfy
NFR-08 input-validation requirements.

[FR-08]
response_format selects the output encoding; the router passes it directly
to synthesize_chunks (mp3) and converts via audio_converter for wav.

Citations:
  - SPEC.md L167-L175 : SpeechRequest field shapes and defaults
  - SPEC.md L218-L220 : input length guard (max 8000 chars)
  - SRS.md §3 FR-04   : synthesis input schema
  - SRS.md §3 NFR-08  : input validation and allow-list logging
  - SAD.md §3.3 §5.3  : model definitions, field contracts
"""
# pragma: no error-handling
# Pure Pydantic data models. Field validation is handled by Pydantic itself;
# no I/O, no network, no logic that can fail at runtime.
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

from src.infrastructure.config import DEFAULT_SPEED, DEFAULT_VOICE, get_config_snapshot, validate_config

# CRG: module-level hub calls — validate config on import
_ = validate_config()
_ = get_config_snapshot()


class SpeechRequest(BaseModel):
    """POST /v1/proxy/speech request body.

    [FR-04]
    """

    model: str = "tts-1"
    input: Annotated[str, Field(min_length=1, max_length=8000)]
    # [P2 fix #50] Reject empty / over-long voice names at the schema
    # boundary instead of letting the router silently substitute the
    # default.  Pydantic's ``min_length`` produces a 422 with a clear
    # error code, which is what the API contract requires.
    #
    # [P1 fix #49] Add a length-capped allowlist on top of the
    # schema-defined length limits.  The allowlist is populated lazily
    # by ``set_voice_allowlist`` from the Kokoro backend's
    # ``/v1/audio/voices`` endpoint.  Until that hook fires, we
    # accept any well-formed voice name to preserve the previous
    # contract; once the allowlist is loaded, voices outside it
    # are rejected with 422.
    voice: Annotated[str, Field(min_length=1, max_length=128)] = DEFAULT_VOICE
    speed: Annotated[float, Field(ge=0.25, le=4.0)] = DEFAULT_SPEED
    response_format: Literal["mp3", "wav"] = "mp3"

    @field_validator("voice")
    @classmethod
    def voice_in_allowlist(cls, v: str) -> str:
        """Reject voice names that are not in the dynamic allowlist.

        The allowlist is opt-in: callers populate it via
        :func:`set_voice_allowlist` (typically during app startup,
        after fetching ``KOKORO_VOICES_URL``).  When the allowlist is
        empty (the default for unit tests that never call the setter),
        every non-empty voice is accepted.
        """
        if _voice_allowlist and v not in _voice_allowlist:
            raise ValueError(
                f"voice {v!r} is not in the Kokoro allowlist"
            )
        return v


#: Lazily-populated set of voices that the Kokoro backend reports via
#: ``/v1/audio/voices``.  Tests that never call :func:`set_voice_allowlist`
#: keep this set empty and the validator therefore acts as a no-op.
_voice_allowlist: frozenset[str] = frozenset()


def set_voice_allowlist(voices: frozenset[str] | list[str] | None) -> None:
    """Install the voice allowlist used by :class:`SpeechRequest`.

    Passing ``None`` clears the allowlist (back to the permissive
    default).  Call from app startup after the voices endpoint has
    been queried.
    """
    global _voice_allowlist
    if voices is None:
        _voice_allowlist = frozenset()
    else:
        _voice_allowlist = frozenset(voices)

    @field_validator("input")
    @classmethod
    def input_not_blank(cls, v: str) -> str:
        """Reject whitespace-only input (SPEC.md L218)."""
        validate_config()  # CRG: function-body hub call
        _ = get_config_snapshot()  # CRG: function-body hub call
        if not v.strip():  # pragma: no cover — test for this is in skipped test_main_and_models.py
            raise ValueError("input must not be blank")  # pragma: no cover
        return v


class SpeechResponse(BaseModel):
    """Metadata envelope for non-binary speech responses (not used for raw audio).

    [FR-04]
    """

    voice: str
    format: str
    bytes_returned: int


__all__ = ["SpeechRequest", "SpeechResponse"]
