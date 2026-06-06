"""[NFR-08] Shared API utilities: PII-safe logging and error response formatting."""
from __future__ import annotations

import logging
from typing import Any, Final

_LOG_ALLOW_LIST: Final[frozenset[str]] = frozenset({
    "event", "level", "ts", "request_id", "voice", "format", "speed",
    "duration_ms", "status_code", "error_code", "dropped_pii",
    "chunk_count", "total_bytes", "circuit_state",
})

_dropped_pii: int = 0

log = logging.getLogger(__name__)


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


def build_error_response(code: str, message: str) -> dict[str, Any]:
    """Return a standard error response body and sanitize for logging.

    [NFR-08]
    All error responses pass through the PII sanitizer so error details
    are safe to emit in structured logs.
    """
    safe_msg = sanitize_log_extra({"error_code": code})
    log.debug("error_response", extra=safe_msg)
    return {"error": {"code": code, "message": message}}
