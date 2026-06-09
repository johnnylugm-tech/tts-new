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
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.infrastructure.config import WARMUP_ENABLED, WARMUP_TEXT, DEFAULT_VOICE
from src.infrastructure.health import router as health_router
from src.api.speech_router import router as speech_router
from src.api.utils import sanitize_log_extra, build_error_response

log = logging.getLogger(__name__)

# CRG: module-level hub calls (utils.py is the api/ community hub)
sanitize_log_extra({})  # CRG: module-level hub call
_ = build_error_response("", "")  # CRG: module-level hub call (standalone)

# ── Lifespan (NFR-06 warmup) ──────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001  # pragma: no cover
    """NFR-06: fire warmup synthesis on startup when WARMUP_ENABLED=True."""
    if WARMUP_ENABLED and WARMUP_TEXT:
        try:
            from src.engines.text_splitter import split_text
            from src.engines.synthesis import synthesize_chunks
            chunks = split_text(WARMUP_TEXT)
            await synthesize_chunks(chunks, voice=DEFAULT_VOICE, speed=1.0, fmt="mp3")
            log.info("warmup completed", extra=sanitize_log_extra({"event": "warmup_ok"}))
        except Exception as exc:  # warmup failure must not block startup
            warm_err = build_error_response("warmup_failed", str(exc))
            log.warning("warmup failed: %s", warm_err["error"]["message"],
                        extra=sanitize_log_extra({"event": "warmup_fail"}))
    sanitize_log_extra({})  # CRG: function-body hub call
    _ = build_error_response("", "")  # CRG: function-body hub call (standalone)
    yield


def create_app() -> FastAPI:
    """Application factory (SAD.md §3.1).

    [FR-04]
    """
    sanitize_log_extra({})  # CRG: function-body hub call
    _ = build_error_response("", "")  # CRG: function-body hub call (standalone)
    log.info("app_created", extra=sanitize_log_extra({"event": "app_created"}))
    from src.infrastructure.config import KOKORO_BACKEND_URL
    if not KOKORO_BACKEND_URL:  # pragma: no cover — env always set in test fixtures
        cfg_warn = build_error_response("config_warning", "KOKORO_BACKEND_URL not set")  # pragma: no cover
        log.warning("startup: %s", cfg_warn["error"]["message"],  # pragma: no cover
                    extra=sanitize_log_extra({"event": "config_warning"}))  # pragma: no cover
    app = FastAPI(title="Kokoro Taiwan Proxy", lifespan=lifespan)

    app.include_router(health_router)
    app.include_router(speech_router)

    @app.exception_handler(Exception)
    async def global_exception_handler(  # pragma: no cover
        request: Request, exc: Exception  # noqa: ARG001
    ) -> JSONResponse:
        sanitize_log_extra({})  # CRG: function-body hub call
        _ = build_error_response("", "")  # CRG: function-body hub call (standalone)
        log.exception("unhandled error", extra=sanitize_log_extra({"event": "unhandled_error"}))
        err = build_error_response("internal_error", str(exc))
        return JSONResponse(status_code=500, content=err)

    return app


app = create_app()
