"""FR-08: ffmpeg 音訊格式轉換 (ffmpeg audio format conversion) — TDD-RED failing tests.

21 parametrized cases for src/audio_converter.py (SPEC.md L188).
Tests fail at collection time (ImportError) — valid RED state.

GREEN TODO: implement src/audio_converter.py with:
  - ConversionError(Exception): base exception for all conversion failures
  - FFmpegUnavailableError(ConversionError, RuntimeError): raised when
    shutil.which("ffmpeg") is None; message MUST contain "ffmpeg",
    "unavailable", and "PATH" (P2-DD-4, ADR-07)
  - convert_mp3_to_wav(mp3_bytes: bytes) -> bytes:
      1. shutil.which("ffmpeg") per call (NOT cached — no @lru_cache)
      2. None → raise FFmpegUnavailableError("ffmpeg binary not found on PATH...")
      3. Empty input → raise ConversionError
      4. Write mp3_bytes to temp file; call subprocess.run(
             ["ffmpeg", "-y", "-i", mp3_in_path, wav_out_path],
             check=True, capture_output=True)
      5. On CalledProcessError → raise ConversionError(str(proc.stderr))
      6. Read wav_out_path → return bytes
  - convert_wav_to_mp3(wav_bytes: bytes) -> bytes  (symmetric reverse)
"""
from __future__ import annotations

import struct
from concurrent.futures import ThreadPoolExecutor
from subprocess import CalledProcessError, CompletedProcess
from unittest.mock import patch

import pytest

# NO try/except — collection error (Exit Code 2) is the valid RED state per
# TDD-RED protocol (FORBIDDEN section item 3).
from src.audio_converter import (
    ConversionError,
    FFmpegUnavailableError,
    convert_mp3_to_wav,
    convert_wav_to_mp3,
)

# ---------------------------------------------------------------------------
# In-memory audio fixtures (structural, not acoustically valid)
# ---------------------------------------------------------------------------

def _make_wav(num_data_bytes: int = 1024) -> bytes:
    """Minimal RIFF/WAVE header + silent PCM samples."""
    return (
        b"RIFF"
        + struct.pack("<I", 36 + num_data_bytes)
        + b"WAVE"
        + b"fmt "
        + struct.pack("<IHHIIHH", 16, 1, 1, 44100, 88200, 2, 16)
        + b"data"
        + struct.pack("<I", num_data_bytes)
        + b"\x00" * num_data_bytes
    )


# ~1 KB / ~5 MB pairs for boundary tests (cases 10-13)
_FAKE_WAV_1KB: bytes = _make_wav(1024 - 44)
_FAKE_WAV_5MB: bytes = _make_wav(5 * 1024 * 1024 - 44)

# ID3v2 stub + MPEG frame sync for MP3
_ID3_STUB: bytes = b"ID3\x04\x00\x00" + b"\x00" * 10  # 16 bytes
_FAKE_MP3_1KB: bytes = _ID3_STUB + b"\xff\xfb\x90\x00" + b"\x00" * (1024 - 20)
_FAKE_MP3_5MB: bytes = _ID3_STUB + b"\xff\xfb\x90\x00" + b"\x00" * (5 * 1024 * 1024 - 20)

# Named fixture aliases (cases 16-19)
_FIXTURE_001_MP3: bytes = _FAKE_MP3_1KB
_FIXTURE_002_MP3: bytes = b"\xff\xfb\x90\x00" + b"\x00" * 2048
_FIXTURE_001_WAV: bytes = _FAKE_WAV_1KB
_FIXTURE_002_WAV: bytes = _make_wav(2048)


# ---------------------------------------------------------------------------
# Mock helper: intercepts subprocess.run and writes fake output to the path
# that ffmpeg would normally produce.
# ---------------------------------------------------------------------------

def _ffmpeg_side_effect(output_bytes: bytes):
    """Returns a subprocess.run side_effect that writes *output_bytes* to
    cmd[-1] (the output file path in the ffmpeg argv).

    GREEN TODO: convert_mp3_to_wav / convert_wav_to_mp3 must call
      subprocess.run(["ffmpeg", "-y", "-i", <in_path>, <out_path>], ...)
    so that cmd[-1] is the output file path written by ffmpeg.
    """
    def _run(cmd, **kwargs):
        out_path = cmd[-1]
        with open(out_path, "wb") as fh:
            fh.write(output_bytes)
        return CompletedProcess(args=cmd, returncode=0, stdout=b"", stderr=b"")
    return _run


# ---------------------------------------------------------------------------
# 21 parametrize IDs — must match TEST_SPEC.md §FR-08 table exactly
# ---------------------------------------------------------------------------

_CASE_IDS = [
    "mp3_to_wav_subprocess_argv_shape",
    "wav_to_mp3_subprocess_argv_shape",
    "mp3_to_wav_returns_CompletedProcess_on_success",
    "wav_to_mp3_returns_CompletedProcess_on_success",
    "round_trip_with_known_fixture",
    "byte_prefix_compare_first_1KB_after_round_trip",
    "missing_ffmpeg_raises_FFmpegUnavailableError",
    "missing_ffmpeg_message_contains_ffmpeg_unavailable_and_PATH",
    "concurrent_mp3_to_wav_failures_dont_block_wav_to_mp3",
    "mp3_to_wav_small_input_~1KB",
    "wav_to_mp3_small_input_~1KB",
    "mp3_to_wav_large_input_~5MB",
    "wav_to_mp3_large_input_~5MB",
    "empty_input_rejection",
    "corrupt_input_raises_ConversionError",
    "fixture_001_mp3_input_conversion",
    "fixture_002_mp3_input_conversion",
    "fixture_001_wav_input_conversion",
    "fixture_002_wav_input_conversion",
    "ffmpeg_CalledProcessError_on_bad_exit_code",
    "ffmpeg_stderr_captured_in_ConversionError",
]


@pytest.mark.parametrize("case_id", _CASE_IDS)
def test_fr_08_audio_converter(case_id):  # noqa: C901
    """FR-08: 21 audio converter cases (subprocess argv, error paths, fixtures).

    All cases dispatch to dedicated helpers below.  The shutil.which patch is
    applied in every happy-path helper so tests do not depend on ffmpeg being
    present in the test environment.
    """
    if case_id == "mp3_to_wav_subprocess_argv_shape":
        _case_argv(convert_mp3_to_wav, _FAKE_MP3_1KB, _FAKE_WAV_1KB)

    elif case_id == "wav_to_mp3_subprocess_argv_shape":
        _case_argv(convert_wav_to_mp3, _FAKE_WAV_1KB, _FAKE_MP3_1KB)

    elif case_id == "mp3_to_wav_returns_CompletedProcess_on_success":
        # AC1-mp3-to-wav-completedprocess: subprocess.run returns CompletedProcess
        # GREEN TODO: convert_mp3_to_wav must call subprocess.run internally;
        # subprocess.run returns CompletedProcess on success (returncode == 0).
        captured: dict = {}

        def _capturing_run(cmd, **kwargs):
            with open(cmd[-1], "wb") as fh:
                fh.write(_FAKE_WAV_1KB)
            proc = CompletedProcess(cmd, returncode=0, stdout=b"", stderr=b"")
            captured["proc"] = proc
            return proc

        with patch("subprocess.run", side_effect=_capturing_run), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            convert_mp3_to_wav(_FAKE_MP3_1KB)

        assert isinstance(captured.get("proc"), CompletedProcess), (
            "subprocess.run must return subprocess.CompletedProcess on success "
            "(SRS.md §3 FR-08 AC1 L289, AC2 L291; TEST_SPEC.md AC1-mp3-to-wav-completedprocess)"
        )

    elif case_id == "wav_to_mp3_returns_CompletedProcess_on_success":
        # AC1-wav-to-mp3-completedprocess (symmetric)
        captured2: dict = {}

        def _capturing_run2(cmd, **kwargs):
            with open(cmd[-1], "wb") as fh:
                fh.write(_FAKE_MP3_1KB)
            proc = CompletedProcess(cmd, returncode=0, stdout=b"", stderr=b"")
            captured2["proc"] = proc
            return proc

        with patch("subprocess.run", side_effect=_capturing_run2), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            convert_wav_to_mp3(_FAKE_WAV_1KB)

        assert isinstance(captured2.get("proc"), CompletedProcess), (
            "subprocess.run must return subprocess.CompletedProcess on success "
            "(SRS.md §3 FR-08 AC1 L289; TEST_SPEC.md AC1-wav-to-mp3-completedprocess)"
        )

    elif case_id == "round_trip_with_known_fixture":
        # AC1-round-trip-success: mp3 → wav → mp3 completes without exception
        # GREEN TODO: both conversion directions must be implemented
        with patch("subprocess.run", side_effect=_ffmpeg_side_effect(_FAKE_WAV_1KB)), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            wav_result = convert_mp3_to_wav(_FIXTURE_001_MP3)

        assert wav_result is not None and len(wav_result) > 0, (
            "mp3→wav conversion must return non-empty bytes (round-trip step 1)"
        )

        with patch("subprocess.run", side_effect=_ffmpeg_side_effect(_FIXTURE_001_MP3)), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            mp3_result = convert_wav_to_mp3(wav_result)

        assert mp3_result is not None and len(mp3_result) > 0, (
            "wav→mp3 conversion must return non-empty bytes (round-trip step 2)"
        )

    elif case_id == "byte_prefix_compare_first_1KB_after_round_trip":
        # AC1-round-trip-success: original[:1024] == round_tripped[:1024]
        # The mock makes the round-trip deterministic: wav→mp3 returns the
        # original fixture bytes, so the prefix check always passes.
        original = _FIXTURE_001_MP3

        with patch("subprocess.run", side_effect=_ffmpeg_side_effect(_FAKE_WAV_1KB)), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            wav_bytes = convert_mp3_to_wav(original)

        with patch("subprocess.run", side_effect=_ffmpeg_side_effect(original)), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            round_tripped = convert_wav_to_mp3(wav_bytes)

        assert original[:1024] == round_tripped[:1024], (
            "after mp3→wav→mp3 round-trip, first 1 KB of output must match "
            "first 1 KB of original (TEST_SPEC.md AC1-round-trip-success)"
        )

    elif case_id == "missing_ffmpeg_raises_FFmpegUnavailableError":
        # AC3-missing-ffmpeg-raises-FFmpegUnavailableError
        # Also verifies per-call check (AC3-per-call-shutil-which-not-cached):
        # after patching which back, a second call succeeds.
        with patch("shutil.which", return_value=None):
            with pytest.raises(FFmpegUnavailableError):
                convert_mp3_to_wav(_FAKE_MP3_1KB)

        # Per-call check — later call with ffmpeg present must succeed
        with patch("subprocess.run", side_effect=_ffmpeg_side_effect(_FAKE_WAV_1KB)), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            result = convert_mp3_to_wav(_FAKE_MP3_1KB)
        assert len(result) > 0, (
            "after ffmpeg becomes available, convert_mp3_to_wav must succeed "
            "(AC3-per-call-shutil-which-not-cached: no @lru_cache allowed)"
        )

    elif case_id == "missing_ffmpeg_message_contains_ffmpeg_unavailable_and_PATH":
        # AC3-missing-ffmpeg-message-substrings: ["ffmpeg", "unavailable", "PATH"]
        with patch("shutil.which", return_value=None):
            with pytest.raises(FFmpegUnavailableError) as exc_info:
                convert_mp3_to_wav(_FAKE_MP3_1KB)

        msg = str(exc_info.value)
        for substring in ("ffmpeg", "unavailable", "PATH"):
            assert substring in msg, (
                f"FFmpegUnavailableError message must contain {substring!r}; "
                f"full message: {msg!r} "
                f"(TEST_SPEC.md AC3-missing-ffmpeg-message-substrings, ADR-07)"
            )

    elif case_id == "concurrent_mp3_to_wav_failures_dont_block_wav_to_mp3":
        # R3-concurrent-isolated-failures: mp3_to_wav raises FFmpegUnavailableError
        # while wav_to_mp3 succeeds concurrently.
        mp3_exc: list = []
        wav_results: list = []

        def _mp3_to_wav_task():
            try:
                with patch("shutil.which", return_value=None):
                    convert_mp3_to_wav(_FAKE_MP3_1KB)
            except FFmpegUnavailableError as exc:
                mp3_exc.append(exc)

        def _wav_to_mp3_task():
            with patch("subprocess.run", side_effect=_ffmpeg_side_effect(_FAKE_MP3_1KB)), \
                 patch("shutil.which", return_value="/usr/bin/ffmpeg"):
                result = convert_wav_to_mp3(_FAKE_WAV_1KB)
            wav_results.append(result)

        with ThreadPoolExecutor(max_workers=4) as pool:
            f1 = pool.submit(_mp3_to_wav_task)
            f2 = pool.submit(_wav_to_mp3_task)
            f1.result()
            f2.result()

        assert len(mp3_exc) == 1 and isinstance(mp3_exc[0], FFmpegUnavailableError), (
            "convert_mp3_to_wav must raise FFmpegUnavailableError when ffmpeg is missing "
            "(R3-concurrent-isolated-failures)"
        )
        assert len(wav_results) == 1 and len(wav_results[0]) > 0, (
            "convert_wav_to_mp3 must succeed concurrently even when "
            "convert_mp3_to_wav fails (R3-concurrent-isolated-failures)"
        )

    elif case_id == "mp3_to_wav_small_input_~1KB":
        # AC1-small-input-1KB: len(wav_bytes) > 0
        with patch("subprocess.run", side_effect=_ffmpeg_side_effect(_FAKE_WAV_1KB)), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            wav_bytes = convert_mp3_to_wav(_FAKE_MP3_1KB)
        assert len(wav_bytes) > 0, (
            "convert_mp3_to_wav with ~1 KB input must return non-empty WAV bytes "
            "(TEST_SPEC.md AC1-small-input-1KB)"
        )

    elif case_id == "wav_to_mp3_small_input_~1KB":
        # AC1-small-wav-1KB: len(mp3_bytes) > 0
        with patch("subprocess.run", side_effect=_ffmpeg_side_effect(_FAKE_MP3_1KB)), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            mp3_bytes = convert_wav_to_mp3(_FAKE_WAV_1KB)
        assert len(mp3_bytes) > 0, (
            "convert_wav_to_mp3 with ~1 KB input must return non-empty MP3 bytes "
            "(TEST_SPEC.md AC1-small-wav-1KB)"
        )

    elif case_id == "mp3_to_wav_large_input_~5MB":
        # AC1-large-input-5MB: len(wav_bytes) > 0
        with patch("subprocess.run", side_effect=_ffmpeg_side_effect(_FAKE_WAV_5MB)), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            wav_bytes = convert_mp3_to_wav(_FAKE_MP3_5MB)
        assert len(wav_bytes) > 0, (
            "convert_mp3_to_wav with ~5 MB input must return non-empty WAV bytes "
            "(TEST_SPEC.md AC1-large-input-5MB)"
        )

    elif case_id == "wav_to_mp3_large_input_~5MB":
        # AC1-large-wav-5MB: len(mp3_bytes) > 0
        with patch("subprocess.run", side_effect=_ffmpeg_side_effect(_FAKE_MP3_5MB)), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            mp3_bytes = convert_wav_to_mp3(_FAKE_WAV_5MB)
        assert len(mp3_bytes) > 0, (
            "convert_wav_to_mp3 with ~5 MB input must return non-empty MP3 bytes "
            "(TEST_SPEC.md AC1-large-wav-5MB)"
        )

    elif case_id == "empty_input_rejection":
        # AC2-empty-input-conversion-error: empty bytes → ConversionError
        with pytest.raises(ConversionError):
            convert_mp3_to_wav(b"")

    elif case_id == "corrupt_input_raises_ConversionError":
        # AC2-corrupt-input-conversion-error: garbage bytes → ConversionError
        # The mock simulates ffmpeg failing on corrupt input.
        corrupt = b"\x00\x01\x02\x03\xff\xfe"

        def _failing_run(cmd, **kwargs):
            raise CalledProcessError(1, cmd, stderr=b"Invalid data found when processing input")

        with patch("subprocess.run", side_effect=_failing_run), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            with pytest.raises(ConversionError):
                convert_mp3_to_wav(corrupt)

    elif case_id == "fixture_001_mp3_input_conversion":
        # AC1-fixture-001-mp3: len(wav_bytes) > 0
        with patch("subprocess.run", side_effect=_ffmpeg_side_effect(_FAKE_WAV_1KB)), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            wav_bytes = convert_mp3_to_wav(_FIXTURE_001_MP3)
        assert len(wav_bytes) > 0, "fixture_001 MP3 → WAV must produce non-empty output"

    elif case_id == "fixture_002_mp3_input_conversion":
        # AC1-fixture-002-mp3: len(wav_bytes) > 0
        with patch("subprocess.run", side_effect=_ffmpeg_side_effect(_FAKE_WAV_1KB)), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            wav_bytes = convert_mp3_to_wav(_FIXTURE_002_MP3)
        assert len(wav_bytes) > 0, "fixture_002 MP3 → WAV must produce non-empty output"

    elif case_id == "fixture_001_wav_input_conversion":
        # AC1-fixture-001-wav: len(mp3_bytes) > 0
        with patch("subprocess.run", side_effect=_ffmpeg_side_effect(_FAKE_MP3_1KB)), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            mp3_bytes = convert_wav_to_mp3(_FIXTURE_001_WAV)
        assert len(mp3_bytes) > 0, "fixture_001 WAV → MP3 must produce non-empty output"

    elif case_id == "fixture_002_wav_input_conversion":
        # AC1-fixture-002-wav: len(mp3_bytes) > 0
        with patch("subprocess.run", side_effect=_ffmpeg_side_effect(_FAKE_MP3_1KB)), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            mp3_bytes = convert_wav_to_mp3(_FIXTURE_002_WAV)
        assert len(mp3_bytes) > 0, "fixture_002 WAV → MP3 must produce non-empty output"

    elif case_id == "ffmpeg_CalledProcessError_on_bad_exit_code":
        # AC2-bad-exit-conversion-error: non-zero exit → ConversionError
        # GREEN TODO: subprocess.CalledProcessError must be caught and
        # re-raised as ConversionError (not propagated directly).
        def _bad_exit_run(cmd, **kwargs):
            raise CalledProcessError(returncode=1, cmd=cmd, stderr=b"ffmpeg error")

        with patch("subprocess.run", side_effect=_bad_exit_run), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            with pytest.raises(ConversionError):
                convert_mp3_to_wav(_FAKE_MP3_1KB)

    elif case_id == "ffmpeg_stderr_captured_in_ConversionError":
        # AC2-stderr-captured: ffmpeg stderr text must appear in ConversionError message
        stderr_text = "Invalid data found when processing input"

        def _stderr_run(cmd, **kwargs):
            raise CalledProcessError(
                returncode=1, cmd=cmd, stderr=stderr_text.encode()
            )

        with patch("subprocess.run", side_effect=_stderr_run), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            with pytest.raises(ConversionError) as exc_info:
                convert_mp3_to_wav(_FAKE_MP3_1KB)

        assert stderr_text in str(exc_info.value), (
            f"ConversionError message must contain ffmpeg stderr text {stderr_text!r}; "
            f"got {str(exc_info.value)!r} "
            f"(TEST_SPEC.md AC2-stderr-captured)"
        )

    else:
        pytest.fail(f"Unhandled case_id: {case_id!r}")


# ---------------------------------------------------------------------------
# Shared argv-shape helper (cases 1 and 2)
# ---------------------------------------------------------------------------

def _case_argv(convert_fn, input_bytes: bytes, output_bytes: bytes) -> None:
    """Verify ffmpeg subprocess argv shape and check=True/capture_output=True."""
    with patch("subprocess.run", side_effect=_ffmpeg_side_effect(output_bytes)) as mock_run, \
         patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        convert_fn(input_bytes)

    assert mock_run.called, "convert function must call subprocess.run"
    argv = mock_run.call_args[0][0]

    assert argv[0] == "ffmpeg", (
        f"argv[0] must be 'ffmpeg' (SRS.md §3 FR-08 AC2 L291); got {argv[0]!r}"
    )
    assert argv[1] == "-y", (
        f"argv[1] must be '-y' (overwrite flag); got {argv[1]!r}"
    )
    assert argv[2] == "-i", (
        f"argv[2] must be '-i' (input flag); got {argv[2]!r}"
    )
    assert len(argv) == 5, (
        f"argv must be exactly [ffmpeg, -y, -i, <in_path>, <out_path>] "
        f"(5 elements); got {len(argv)}: {argv}"
    )

    kw = mock_run.call_args[1]
    assert kw.get("check") is True, (
        "subprocess.run must be called with check=True "
        "(TEST_SPEC.md AC2-subprocess-check-true)"
    )
    assert kw.get("capture_output") is True, (
        "subprocess.run must be called with capture_output=True "
        "(TEST_SPEC.md AC2-subprocess-check-true)"
    )
