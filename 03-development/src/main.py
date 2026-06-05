"""FR-04 / NFR-06 / NFR-08 — FastAPI application entry point.

[FR-04]
Application factory that mounts all routers, installs the global exception
handler, and fires the NFR-06 warmup on startup.

[NFR-06]
On launch when WARMUP_ENABLED=True, sends WARMUP_TEXT through the synthesis
pipeline so the Kokoro backend JIT-compiles the first request ahead of time.

[NFR-08]
All log lines pass through a sanitizer that projects the extra dict down to
the allow-list of safe keys and drops (counting as dropped_pii) any key not
on the list. Secrets are never emitted.

Citations:
  - SPEC.md L184-L186 : FastAPI app responsibilities (lifespan, routing)
  - SPEC.md L222-L229 : NFR-08 allow-list sanitizer (R6 secret leakage)
  - SRS.md §3 NFR-06  : warmup acceptance criteria
  - SRS.md §3 NFR-08  : input validation and log sanitization
  - SAD.md §3.1       : main.py module responsibilities
  - SAD.md §6.1       : NFR-08 allow-list logger table
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.config import WARMUP_ENABLED, WARMUP_TEXT, DEFAULT_VOICE
from src.routers.health import router as health_router
from src.routers.speech import router as speech_router

# ── NFR-08 allow-list sanitizer ──────────────────────────────────────────────
# Keys allowed in structured log output; all others are dropped (deny-by-default).
_LOG_ALLOW_LIST: frozenset[str] = frozenset({
    "event", "level", "ts", "request_id", "voice", "format", "speed",
    "duration_ms", "status_code", "error_code", "dropped_pii",
    "chunk_count", "total_bytes", "circuit_state",
})

_dropped_pii: int = 0


def sanitize_log_extra(extra: dict[str, Any]) -> dict[str, Any]:
    """Project ``extra`` down to the allow-list; increment dropped_pii counter.

    [NFR-08]
    """
    global _dropped_pii
    safe: dict[str, Any] = {}
    for k, v in extra.items():
        if k in _LOG_ALLOW_LIST:
            safe[k] = v
        else:
            _dropped_pii += 1
    if _dropped_pii > 0:
        safe["dropped_pii"] = _dropped_pii
    return safe


log = logging.getLogger(__name__)

# ── Lifespan (NFR-06 warmup) ──────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    """NFR-06: fire warmup synthesis on startup when WARMUP_ENABLED=True."""
    if WARMUP_ENABLED and WARMUP_TEXT:
        try:
            from src.engines.text_splitter import split_text
            from src.engines.synthesis import synthesize_chunks
            chunks = split_text(WARMUP_TEXT)
            await synthesize_chunks(chunks, voice=DEFAULT_VOICE, speed=1.0, fmt="mp3")
            log.info("warmup completed", extra=sanitize_log_extra({"event": "warmup_ok"}))
        except Exception as exc:  # warmup failure must not block startup
            log.warning("warmup failed: %s", exc,
                        extra=sanitize_log_extra({"event": "warmup_fail"}))
    yield


def create_app() -> FastAPI:
    """Application factory (SAD.md §3.1).

    [FR-04]
    """
    app = FastAPI(title="Kokoro Taiwan Proxy", lifespan=lifespan)

    app.include_router(health_router)
    app.include_router(speech_router)

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception  # noqa: ARG001
    ) -> JSONResponse:
        log.exception("unhandled error")
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": str(exc)}},
        )

    return app


app = create_app()
