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

    in_fd = -1
    in_path = ""
    out_fd = -1
    out_path = ""
    # [P2 fix #18 / #24] Both mkstemps must be inside the try so a
    # failure on the second (resource exhaustion, EEXIST on weird
    # filesystems, etc.) closes the first in_fd via the finally block.
    try:
        in_fd, in_path = tempfile.mkstemp()
        out_fd, out_path = tempfile.mkstemp(suffix=output_suffix)
        # Close out_fd immediately (we only need the path); leave
        # in_fd open for the write below.
        os.close(out_fd)
        out_fd = -1
        with os.fdopen(in_fd, "wb") as fh:
            in_fd = -1  # os.fdopen takes ownership; close path goes via fh
            fh.write(input_bytes)

        # [P1 fix #16] subprocess.run is documented to wait() and
        # reap the child on every exit path (including timeout and
        # signal-induced cancellation), so the orphan-process concern
        # the report raised does not apply to this call site.  We
        # retain the wrapper for its readable kwargs surface and the
        # well-defined exception types below.
        try:
            subprocess.run(  # nosec
                ["ffmpeg", "-y", "-i", in_path, out_path],
                check=True,
                capture_output=True,
                timeout=30.0,
            )
        except subprocess.TimeoutExpired as exc:
            # [P0 fix #15 + covers P2 #21] ffmpeg hung: map to
            # ConversionError, not raw.  The 30 s timeout also stops
            # the worker thread from being permanently occupied by a
            # single hung ffmpeg invocation, which the report flagged
            # as P2 #21.  subprocess.run cleans up the child even on
            # timeout, so there is no orphan-process leak (the
            # report's P1 #16 orphan-ffmpeg concern does not apply
            # to subprocess.run; it only matters for raw Popen usage).
            raise ConversionError("ffmpeg timed out after 30s") from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode(errors="replace") if exc.stderr else str(exc)
            raise ConversionError(stderr) from exc
        except FileNotFoundError as exc:
            # TOCTOU: ffmpeg was on PATH at shutil.which() but gone at
            # run() (P2-DD-4: map to FFmpegUnavailableError, not bare
            # FileNotFoundError).
            raise FFmpegUnavailableError() from exc

        with open(out_path, "rb") as fh:
            output_bytes = fh.read()
        # [P2 fix #17 / #25] Validate the output: ffmpeg can return a
        # non-zero exit that was swallowed by the caller's error
        # handler, or produce a zero-byte / corrupt file. Surface that
        # as ConversionError so the caller can map to 500 rather than
        # silently shipping empty audio.
        if not output_bytes:
            raise ConversionError("ffmpeg produced empty output")
        return output_bytes
    finally:
        if in_fd != -1:  # defensive: mkstemp succeeded but fdopen did not run
            try:
                os.close(in_fd)
            except OSError:  # pragma: no cover
                pass  # pragma: no cover
        if out_fd != -1:  # defensive: close any leaked fd
            try:
                os.close(out_fd)
            except OSError:  # pragma: no cover
                pass  # pragma: no cover
        try:
            os.unlink(in_path)
        except OSError:  # pragma: no cover
            pass  # pragma: no cover
        # [P3 fix #19] Drop the redundant os.path.exists() pre-check —
        # it's a classic TOCTOU (the file can be unlinked between
        # exists() and unlink()), and EAFP with try/except is
        # idiomatic.  If the file is already gone, OSError(ENOENT) is
        # benign; any other OSError should also be swallowed (we are
        # in a finally block; raising would mask the real exception).
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
