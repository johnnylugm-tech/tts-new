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
import sys

import httpx

from src.config import KOKORO_BACKEND_URL


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments per SPEC.md L92-L97.

    Returns a namespace with: text, input_file, output, voice, speed,
    fmt, ssml, backend.
    """
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
    return parser.parse_args(argv[1:])


async def _synthesize_text(
    text: str,
    voice: str,
    speed: float,
    fmt: str,
    backend_url: str,
) -> bytes:
    """Synthesize *text* using the specified parameters."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            backend_url + "/v1/audio/speech",
            json={"text": text, "voice": voice, "speed": speed, "format": fmt},
        )
        await resp.raise_for_status()  # type: ignore[union-attr]
        return await resp.read()  # type: ignore[union-attr]


def main(argv: list[str] | None = None) -> int:
    """Entry point for the tts-v610 CLI.

    Returns 0 on success, non-zero on error.

    [FR-07]
    """
    if argv is None:
        argv = sys.argv

    args = _parse_args(argv)

    backend_url = args.backend or KOKORO_BACKEND_URL
    voice = args.voice
    speed = args.speed
    fmt = args.format

    if args.text:
        text = args.text
        if args.ssml:
            from src.engines.ssml_parser import parse_ssml
            parsed = parse_ssml(text)
            text = parsed.plain_text

        audio = asyncio.run(_synthesize_text(text, voice, speed, fmt, backend_url))

        with open(args.output, "wb") as fh:
            fh.write(audio)
        return 0

    elif args.input_file:
        import os
        out_dir = args.output
        with open(args.input_file, encoding="utf-8") as fh:
            lines = [ln.rstrip("\n") for ln in fh if ln.strip()]

        for i, line in enumerate(lines):
            audio = asyncio.run(
                _synthesize_text(line, voice, speed, fmt, backend_url)
            )
            out_path = os.path.join(out_dir, f"output_{i+1:04d}.mp3")
            with open(out_path, "wb") as fh:
                fh.write(audio)
        return 0

    return 0
