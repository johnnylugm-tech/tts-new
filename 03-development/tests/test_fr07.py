"""FR-07: CLI command-line tool — TDD-RED failing tests.

6 parametrized cases for src/cli.py (SPEC.md L91-L98, SRS.md §3 FR-07).
Tests fail at collection time (ImportError) — valid RED state.

GREEN TODO: implement src/cli.py with:
  - main(argv: list[str] | None = None) -> int
      Parse CLI args, invoke synthesis engine in-process (no loopback HTTP
      per SAD.md §3.7), return 0 on success, non-zero on error.
  - Supported invocations (SPEC.md L92-L97):
      tts-v610 "你好世界" -o output.mp3
      tts-v610 -i input.txt -o output/
      tts-v610 "文字" -v "zf_xiaoxiao" -s 1.0 -f mp3
      tts-v610 --ssml "<speak>...</speak>" -o out.mp3
      tts-v610 --backend "http://localhost:8880" "text" -o out.mp3
  - python -m src.cli --help must exit 0 (SPEC.md L237)
  - --backend flag overrides KOKORO_BACKEND_URL for the call (SPEC.md L97, L123)
  - --ssml flag routes input through parse_ssml() (SPEC.md L96)
  - -i file + -o directory writes one output file per non-blank input line
"""
from __future__ import annotations

import io
import sys
from unittest.mock import AsyncMock, patch

import pytest

# NO try/except — Collection Error (Exit Code 2) is the valid RED state
# per TDD-RED protocol (FORBIDDEN section item 3).
from src.cli import main  # noqa: E402

# ---------------------------------------------------------------------------
# Spec constants & shared fixtures
# ---------------------------------------------------------------------------

_FAKE_MP3 = b"fake_mp3_audio_bytes_for_testing"
_BACKEND_PATH = "/v1/audio/speech"

# ---------------------------------------------------------------------------
# 6 parametrize IDs — MUST match TEST_SPEC.md FR-07 table exactly
# ---------------------------------------------------------------------------

_CASE_IDS = [
    "pattern1_inline_text_with_output",
    "pattern2_file_input_dir_output_one_per_line",
    "pattern3_voice_speed_format_options",
    "pattern4_ssml_routes_through_parser",
    "pattern5_backend_override_loopback_only",
    "--help_exits_0_with_usage_strings",
]


def _make_mock_post():
    """Return an AsyncMock that simulates a successful httpx POST response."""
    mock_post = AsyncMock()
    mock_post.return_value.status_code = 200
    mock_post.return_value.read = AsyncMock(return_value=_FAKE_MP3)
    mock_post.return_value.raise_for_status = AsyncMock()
    return mock_post


@pytest.mark.parametrize("case_id", _CASE_IDS)
def test_fr_07_cli(case_id, tmp_path):
    """FR-07: CLI command-line tool — 6 cases for 5 invocations + --help."""

    # ── Case 1: inline text with -o output file ──────────────────────
    if case_id == "pattern1_inline_text_with_output":
        out_file = tmp_path / "out.mp3"
        mock_post = _make_mock_post()

        with patch("httpx.AsyncClient.post", mock_post):
            exit_code = main(["tts-v610", "你好世界", "-o", str(out_file)])

        assert exit_code == 0, f"pattern1 must exit 0; got {exit_code}"
        assert out_file.exists(), f"output file {out_file} must exist"
        assert out_file.stat().st_size > 0, "output file must be non-empty"

    # ── Case 2: -i file + -o directory → one output per line ────────
    elif case_id == "pattern2_file_input_dir_output_one_per_line":
        in_file = tmp_path / "in.txt"
        out_dir = tmp_path / "out_dir"
        out_dir.mkdir()

        lines = ["第一行文字", "第二行文字", "第三行文字"]
        in_file.write_text("\n".join(lines), encoding="utf-8")
        non_blank = len(lines)  # no blank lines in fixture

        mock_post = _make_mock_post()
        with patch("httpx.AsyncClient.post", mock_post):
            exit_code = main(["tts-v610", "-i", str(in_file), "-o", str(out_dir)])

        assert exit_code == 0, f"pattern2 must exit 0; got {exit_code}"
        output_files = sorted(out_dir.glob("*.mp3"))
        assert len(output_files) == non_blank, (
            f"must produce one output file per non-blank input line ("
            f"{non_blank}); got {len(output_files)} files: {output_files}"
        )
        for f in output_files:
            assert f.stat().st_size > 0, f"output file {f.name} must be non-empty"

    # ── Case 3: voice / speed / format options ───────────────────────
    elif case_id == "pattern3_voice_speed_format_options":
        out_file = tmp_path / "out.mp3"
        mock_post = _make_mock_post()

        with patch("httpx.AsyncClient.post", mock_post):
            exit_code = main([
                "tts-v610", "文字", "-v", "zf_xiaoxiao",
                "-s", "1.0", "-f", "mp3", "-o", str(out_file),
            ])

        assert exit_code == 0, f"pattern3 must exit 0; got {exit_code}"
        assert mock_post.call_count >= 1, "synthesis httpx POST must be called"
        # GREEN TODO: httpx.AsyncClient.post() json= must contain
        # voice="zf_xiaoxiao", speed=1.0, format="mp3"
        call_kwargs = mock_post.call_args.kwargs
        json_body = call_kwargs.get("json", {})
        assert json_body.get("voice") == "zf_xiaoxiao", (
            f"httpx POST json voice must be 'zf_xiaoxiao'; got {json_body!r}"
        )
        assert json_body.get("speed") == 1.0, (
            f"httpx POST json speed must be 1.0; got {json_body!r}"
        )
        assert json_body.get("format") == "mp3", (
            f"httpx POST json format must be 'mp3'; got {json_body!r}"
        )

    # ── Case 4: --ssml routes through parse_ssml ─────────────────────
    elif case_id == "pattern4_ssml_routes_through_parser":
        out_file = tmp_path / "out.mp3"
        mock_post = _make_mock_post()

        with patch("httpx.AsyncClient.post", mock_post):
            # GREEN TODO: src.cli must call parse_ssml() from
            # src.engines.ssml_parser when --ssml flag is given
            with patch("src.engines.ssml_parser.parse_ssml") as mock_parse:
                from src.engines.ssml_parser import ParsedSSML
                mock_parse.return_value = ParsedSSML(
                    plain_text="你好",
                    segments=[],
                    warnings=[],
                )
                exit_code = main([
                    "tts-v610", "--ssml", "<speak>你好</speak>",
                    "-o", str(out_file),
                ])

        assert exit_code == 0, f"pattern4 must exit 0; got {exit_code}"
        assert mock_parse.call_count >= 1, (
            f"--ssml must route through parse_ssml (call count >= 1); "
            f"got {mock_parse.call_count}"
        )

    # ── Case 5: --backend overrides KOKORO_BACKEND_URL ──────────────
    elif case_id == "pattern5_backend_override_loopback_only":
        out_file = tmp_path / "out.mp3"
        base_url = "http://localhost:8880"
        expected_path = f"{base_url}{_BACKEND_PATH}"
        mock_post = _make_mock_post()

        with patch("httpx.AsyncClient.post", mock_post):
            exit_code = main([
                "tts-v610", "--backend", base_url, "text", "-o", str(out_file),
            ])

        assert exit_code == 0, f"pattern5 must exit 0; got {exit_code}"
        assert mock_post.call_count >= 1, "synthesis httpx POST must be called"
        # GREEN TODO: --backend flag must override KOKORO_BACKEND_URL;
        # the httpx POST url must be the overridden backend + /v1/audio/speech
        post_url = (
            mock_post.call_args.args[0]
            if mock_post.call_args.args
            else mock_post.call_args.kwargs.get("url", "")
        )
        assert post_url == expected_path, (
            f"httpx POST url must be the overridden backend URL "
            f"'{expected_path}'; got '{post_url}'"
        )

    # ── Case 6: --help exits 0 with usage strings ────────────────────
    elif case_id == "--help_exits_0_with_usage_strings":
        captured = io.StringIO()
        exit_code = 1  # sentinel

        with patch.object(sys, "stdout", captured):
            try:
                exit_code = main(["tts-v610", "--help"])
            except SystemExit as e:
                exit_code = e.code if isinstance(e.code, int) else int(e.code or 0)

        stdout_text = captured.getvalue()
        assert exit_code == 0, f"--help must exit 0; got exit_code={exit_code}"
        required_strings = ["tts-v610", "--ssml", "--backend", "-o"]
        for s in required_strings:
            assert s in stdout_text, (
                f"--help output must contain '{s}'; got:\n{stdout_text[:500]}"
            )
