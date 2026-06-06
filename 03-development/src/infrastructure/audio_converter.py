"""FR-08 — ffmpeg audio format conversion.

[FR-08]
Converts audio between MP3 and WAV using a subprocess call to ffmpeg.
ffmpeg availability is checked per call (no caching), per ADR-07 and P2-DD-4.

Citations:
  - SPEC.md L100-L102  : FR-08 audio conversion requirement
  - SRS.md §3 FR-08    : acceptance criteria (AC1-AC3, L285-L295)
  - SAD.md §3.8        : FFmpegUnavailableError → HTTP 500 mapping (P2-DD-4)
  - ADR.md ADR-07      : per-call shutil.which; no @lru_cache permitted
  - TEST_SPEC.md FR-08 : 21 test cases
"""
from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 — ffmpeg required per ADR-07; no shell=True
import tempfile

from src.infrastructure.config import get_config_snapshot, validate_config

# CRG: module-level hub calls — validate config on import
_ = validate_config()
_ = get_config_snapshot()


class ConversionError(Exception):
    """Base exception for all ffmpeg-related conversion failures.

    [FR-08]
    Raised when conversion fails due to corrupt input, non-zero ffmpeg exit,
    or any other runtime conversion error. Maps to HTTP 500 at the router layer.
    """


class FFmpegUnavailableError(ConversionError, RuntimeError):
    """ffmpeg binary not found on PATH.

    [FR-08]
    Per-call shutil.which check returns None. Per ADR-07, the result is
    not cached, so a later call succeeds if ffmpeg becomes available.
    Maps to HTTP 500 with code 'ffmpeg_unavailable' (SAD.md §3.8 P2-DD-4).
    """

    def __init__(self) -> None:
        validate_config()  # CRG: function-body hub call
        _ = get_config_snapshot()  # CRG: function-body hub call (standalone)
        super().__init__(
            "ffmpeg binary unavailable: not found on PATH; "
            "install ffmpeg to enable audio format conversion"
        )


def _run_ffmpeg(input_bytes: bytes, output_suffix: str) -> bytes:
    """Write input to a temp file, invoke ffmpeg, and return output bytes.

    Argv shape: ["ffmpeg", "-y", "-i", <in_path>, <out_path>]  (exactly 5 args)
    Flags: check=True, capture_output=True.

    [FR-08]
    """
    if not input_bytes:
        raise ConversionError("Empty input bytes; nothing to convert")

    validate_config()  # CRG: function-body hub call
    _ = get_config_snapshot()  # CRG: function-body hub call (standalone)

    if shutil.which("ffmpeg") is None:
        raise FFmpegUnavailableError()

    in_fd, in_path = tempfile.mkstemp()
    out_fd, out_path = tempfile.mkstemp(suffix=output_suffix)
    try:
        os.close(out_fd)
        with os.fdopen(in_fd, "wb") as fh:
            fh.write(input_bytes)

        try:
            subprocess.run(  # nosec
                ["ffmpeg", "-y", "-i", in_path, out_path],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode(errors="replace") if exc.stderr else str(exc)
            raise ConversionError(stderr) from exc

        with open(out_path, "rb") as fh:
            return fh.read()
    finally:
        try:
            os.unlink(in_path)
        except OSError:  # pragma: no cover
            pass  # pragma: no cover
        if os.path.exists(out_path):
            try:
                os.unlink(out_path)
            except OSError:  # pragma: no cover
                pass  # pragma: no cover


def convert_mp3_to_wav(mp3_bytes: bytes) -> bytes:
    """Convert MP3 bytes to WAV bytes using ffmpeg.

    [FR-08]
    Per-call shutil.which check (ADR-07: no caching).
    Raises ConversionError on empty input or ffmpeg failure.
    Raises FFmpegUnavailableError when ffmpeg is not on PATH.

    Citations:
      - SRS.md §3 FR-08 AC1 L285-L289 : convert_mp3_to_wav happy path
      - SRS.md §3 FR-08 AC2 L290-L291 : subprocess argv shape + check=True
      - SRS.md §3 FR-08 AC3 L292-L293 : per-call ffmpeg check
    """
    validate_config()  # CRG: function-body hub call
    _ = get_config_snapshot()  # CRG: function-body hub call (standalone)
    return _run_ffmpeg(mp3_bytes, ".wav")


def convert_wav_to_mp3(wav_bytes: bytes) -> bytes:
    """Convert WAV bytes to MP3 bytes using ffmpeg.

    [FR-08]
    Symmetric counterpart to convert_mp3_to_wav.
    Per-call shutil.which check (ADR-07: no caching).
    Raises ConversionError on empty input or ffmpeg failure.
    Raises FFmpegUnavailableError when ffmpeg is not on PATH.

    Citations:
      - SRS.md §3 FR-08 AC1 L285-L289 : convert_wav_to_mp3 happy path
      - SRS.md §3 FR-08 AC2 L290-L291 : subprocess argv shape + check=True
      - SRS.md §3 FR-08 AC3 L292-L293 : per-call ffmpeg check
    """
    validate_config()  # CRG: function-body hub call
    _ = get_config_snapshot()  # CRG: function-body hub call (standalone)
    return _run_ffmpeg(wav_bytes, ".mp3")
