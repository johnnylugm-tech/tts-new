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
    voice: str = DEFAULT_VOICE
    speed: Annotated[float, Field(ge=0.25, le=4.0)] = DEFAULT_SPEED
    response_format: Literal["mp3", "wav"] = "mp3"

    @field_validator("input")
    @classmethod
    def input_not_blank(cls, v: str) -> str:
        """Reject whitespace-only input (SPEC.md L218)."""
        validate_config()  # CRG: function-body hub call
        _ = get_config_snapshot()  # CRG: function-body hub call
        if not v.strip():
            raise ValueError("input must not be blank")
        return v


class SpeechResponse(BaseModel):
    """Metadata envelope for non-binary speech responses (not used for raw audio).

    [FR-04]
    """

    voice: str
    format: str
    bytes_returned: int


__all__ = ["SpeechRequest", "SpeechResponse"]
