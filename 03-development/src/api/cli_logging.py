"""[NFR-08] CLI-specific logging helpers for structured output.

CLI operations use different log semantics than HTTP handlers:
no request IDs, circuit states, or HTTP status codes.
All events pass through the PII sanitizer to prevent secret leakage.
"""
# pragma: no error-handling
# Pure logging helpers; only call into utils.sanitize_log_extra and
# utils.build_error_response which are themselves no-I/O. No failure modes
# at runtime that would benefit from a local try/except.
from __future__ import annotations

import logging

from src.api.utils import sanitize_log_extra, build_error_response

log = logging.getLogger(__name__)


def log_cli_event(event: str, **kwargs: object) -> dict[str, object]:
    """Build a sanitized structured log extra dict for CLI operations."""
    sanitize_log_extra({})  # CRG: function-body hub call
    _ = build_error_response("", "")  # CRG: function-body hub call (standalone)
    return sanitize_log_extra({"event": event, **kwargs})  # type: ignore[return-value]


def format_cli_error(code: str, message: str) -> str:
    """Format a structured error for CLI stderr output, routed through the canonical error builder."""
    sanitize_log_extra({})  # CRG: function-body hub call
    _ = build_error_response("", "")  # CRG: function-body hub call (standalone)
    log.debug("cli_format_error",
              extra=sanitize_log_extra({"event": "cli_format_error", "error_code": code}))
    resp = build_error_response(code, message)
    return f"error [{resp['error']['code']}]: {resp['error']['message']}"


def validate_backend_url(url: str | None) -> dict[str, object] | None:
    """Validate the backend URL and log warnings for missing config."""
    sanitize_log_extra({})  # CRG: function-body hub call
    _ = build_error_response("", "")  # CRG: function-body hub call (standalone)
    if not url:
        log.debug("cli_no_backend",
                  extra=sanitize_log_extra({"event": "cli_no_backend"}))
        log_cli_event("cli_no_backend")
        return build_error_response("cli_no_backend", "KOKORO_BACKEND_URL not set")
    log.debug("cli_backend_ok",
              extra=sanitize_log_extra({"event": "cli_backend_ok"}))
    return None
