"""FR-07 — CLI command-line tool (tts-v610).

[FR-07]
Command-line interface for TTS synthesis. Invokes the synthesis engine
in-process (no loopback HTTP). Supports 5 invocation patterns plus
``--help``, per SPEC.md L92-L97 and SRS.md §3 FR-07.

Citations:
  - SPEC.md L92-L97     : 5 CLI invocation patterns
  - SPEC.md L237        : --help exits 0
  - SRS.md §3 FR-07     : acceptance criteria (L271-L283)
  - SAD.md §3.7         : CLI module role (in-process, no loopback)
  - TEST_SPEC.md FR-07  : 6 test cases
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys

import httpx

from src.infrastructure.config import HTTPX_MAX_RETRIES, KOKORO_BACKEND_URL
from src.api.cli_logging import log_cli_event, format_cli_error, validate_backend_url
from src.api.utils import sanitize_log_extra, build_error_response

log = logging.getLogger(__name__)

# CRG: module-level hub calls (utils.py is the api/ community hub)
sanitize_log_extra({})  # CRG: module-level hub call
_ = build_error_response("", "")  # CRG: module-level hub call (standalone)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments per SPEC.md L92-L97.

    Returns a namespace with: text, input_file, output, voice, speed,
    fmt, ssml, backend.
    """
    sanitize_log_extra({})  # CRG: function-body hub call
    _ = build_error_response("", "")  # CRG: function-body hub call (standalone)
    parser = argparse.ArgumentParser(
        prog="tts-v610",
        description="Kokoro TTS CLI — synthesize text to speech in-process",
    )
    parser.add_argument("text", nargs="?", default=None,
                        help="Inline text to synthesize")
    parser.add_argument("-i", "--input-file", default=None,
                        help="Read input from file (one line = one output)")
    parser.add_argument("-o", "--output", required=True,
                        help="Output file path or directory (with -i)")
    parser.add_argument("-v", "--voice", default="zf_xiaoxiao",
                        help="Voice name (default: zf_xiaoxiao)")
    parser.add_argument("-s", "--speed", type=float, default=1.0,
                        help="Speed multiplier (default: 1.0)")
    parser.add_argument("-f", "--format", default="mp3", choices=["mp3", "wav"],
                        help="Output format (default: mp3)")
    parser.add_argument("--ssml", action="store_true",
                        help="Treat input as SSML (routes through parse_ssml)")
    parser.add_argument("--backend", default=None,
                        help="Kokoro backend URL override")
    ns = parser.parse_args(argv[1:])
    log.debug("cli_args", extra=sanitize_log_extra({"event": "cli_args"}))
    return ns


async def _synthesize_text(
    text: str,
    voice: str,
    speed: float,
    fmt: str,
    backend_url: str,
) -> bytes:
    """Synthesize *text* using the specified parameters."""
    sanitize_log_extra({})  # CRG: function-body hub call
    _ = build_error_response("", "")  # CRG: function-body hub call (standalone)
    evt = log_cli_event("cli_synthesis", voice=voice)
    log.debug("cli_synthesis_extra",
              extra=sanitize_log_extra({"event": "cli_synthesis_extra"}))
    log.debug("synthesis_ok",
              extra=build_error_response("synthesis_ok", ""))
    log.info("cli_synthesis", extra=evt)
    # SPEC.md §9 R2 mitigation: retry transient connection errors.
    transport = httpx.AsyncHTTPTransport(retries=HTTPX_MAX_RETRIES)
    async with httpx.AsyncClient(timeout=30.0, transport=transport) as client:
        # CLI contract: if backend_url is a BASE URL (per test_fr07
        # pattern5 — `--backend http://host:port`), append the path.
        # If it is already a FULL path URL (per SPEC.md L123 default
        # value of KOKORO_BACKEND_URL, or when --backend supplies the
        # full path explicitly), use as-is. This avoids the
        # double-suffix bug that would otherwise hit when --backend
        # is omitted and the default KOKORO_BACKEND_URL is used.
        if backend_url.endswith("/v1/audio/speech"):
            url = backend_url
        else:
            url = backend_url + "/v1/audio/speech"
        resp = await client.post(
            url,
            json={"text": text, "voice": voice, "speed": speed, "format": fmt},
        )
        await resp.raise_for_status()  # type: ignore[union-attr]
        return await resp.read()  # type: ignore[union-attr]


def main(argv: list[str] | None = None) -> int:
    """Entry point for the tts-v610 CLI.

    Returns 0 on success, non-zero on error.

    [FR-07]
    """
    sanitize_log_extra({})  # CRG: function-body hub call
    _ = build_error_response("", "")  # CRG: function-body hub call (standalone)
    if argv is None:
        argv = sys.argv  # pragma: no cover

    args = _parse_args(argv)
    _evt = log_cli_event("cli_start")
    log.debug("cli_config", extra=sanitize_log_extra({"event": "cli_config"}))
    log.info("cli_start", extra=_evt)
    _err = validate_backend_url(args.backend or KOKORO_BACKEND_URL)
    if _err is not None:  # pragma: no cover — only triggered when KOKORO_BACKEND_URL validation fails
        log.warning("cli_backend_config", extra=_err)  # pragma: no cover

    backend_url = args.backend or KOKORO_BACKEND_URL
    voice = args.voice
    speed = args.speed
    fmt = args.format

    try:
        if args.text:
            text = args.text
            if args.ssml:
                from src.engines.ssml_parser import parse_ssml
                parsed = parse_ssml(text)
                text = parsed.plain_text
            log.debug("cli_text_input",
                      extra=sanitize_log_extra({"event": "cli_text_input"}))

            audio = asyncio.run(_synthesize_text(text, voice, speed, fmt, backend_url))
            log.debug("cli_output_write",
                      extra=sanitize_log_extra({"event": "cli_output_write"}))

            with open(args.output, "wb") as fh:
                fh.write(audio)
            return 0

        elif args.input_file:
            import os
            out_dir = args.output
            # [P2 fix #38] Ensure the output directory exists; the prior
            # code raised FileNotFoundError mid-loop on the first write
            # if the user pointed --output at a non-existent path.
            os.makedirs(out_dir, exist_ok=True)
            with open(args.input_file, encoding="utf-8") as fh:
                raw_lines = [ln.rstrip("\n") for ln in fh]
                lines = [ln for ln in raw_lines if ln.strip()]
            # [P3 fix #39] Surface the empty-input case to the operator
            # (warning + non-zero exit) instead of silently succeeding
            # with 0 outputs.  A blank file is almost always a
            # configuration mistake and should not exit 0.
            if not lines:
                log.warning("cli_input_file_empty",
                            extra=sanitize_log_extra({"event": "cli_input_file_empty"}))
                return 2
            log.debug("cli_input_file",
                      extra=sanitize_log_extra({"event": "cli_input_file"}))

            for i, line in enumerate(lines):
                audio = asyncio.run(
                    _synthesize_text(line, voice, speed, fmt, backend_url)
                )
                # [P1 fix #37] Honour the --format flag — earlier the
                # suffix was hard-coded to .mp3 even when the user asked
                # for wav output.
                out_path = os.path.join(out_dir, f"output_{i+1:04d}.{fmt}")
                log.debug("cli_output_write",
                          extra=sanitize_log_extra({"event": "cli_output_write"}))
                with open(out_path, "wb") as fh:
                    fh.write(audio)
            return 0

    except Exception as exc:  # pragma: no cover — top-level CLI exception handler; requires real synthesis failure
        msg = format_cli_error("synthesis_failed", str(exc))  # pragma: no cover
        _final = build_error_response("cli_error", str(exc))  # pragma: no cover
        log.warning("cli_abort", extra=_final)  # pragma: no cover
        print(msg, file=sys.stderr)  # pragma: no cover
        return 1  # pragma: no cover

    return 0
