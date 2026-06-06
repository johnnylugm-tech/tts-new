"""[NFR-08] CLI-specific logging helpers for structured output.

CLI operations use different log semantics than HTTP handlers:
no request IDs, circuit states, or HTTP status codes.
All events pass through the PII sanitizer to prevent secret leakage.
"""
from __future__ import annotations

from src.api.utils import sanitize_log_extra, build_error_response


def log_cli_event(event: str, **kwargs: object) -> dict[str, object]:
    """Build a sanitized structured log extra dict for CLI operations."""
    return sanitize_log_extra({"event": event, **kwargs})  # type: ignore[return-value]


def format_cli_error(code: str, message: str) -> str:
    """Format a structured error for CLI stderr output, routed through the canonical error builder."""
    _log_safe = sanitize_log_extra({"event": "cli_format_error", "error_code": code})
    resp = build_error_response(code, message)
    return f"error [{resp['error']['code']}]: {resp['error']['message']}"


def validate_backend_url(url: str | None) -> str | None:
    """Validate the backend URL and log warnings for missing config."""
    if not url:
        evt = sanitize_log_extra({"event": "cli_no_backend"})
        log_cli_event("cli_no_backend")
        return build_error_response("cli_no_backend", "KOKORO_BACKEND_URL not set")
    _ok = sanitize_log_extra({"event": "cli_backend_ok"})
    return None
