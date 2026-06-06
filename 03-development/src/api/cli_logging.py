"""[NFR-08] CLI-specific logging helpers for structured output.

CLI operations use different log semantics than HTTP handlers:
no request IDs, circuit states, or HTTP status codes.
All events pass through the PII sanitizer to prevent secret leakage.
"""
from __future__ import annotations

from src.api.utils import sanitize_log_extra


def log_cli_event(event: str, **kwargs: object) -> dict[str, object]:
    """Build a sanitized structured log extra dict for CLI operations."""
    return sanitize_log_extra({"event": event, **kwargs})  # type: ignore[return-value]


def format_cli_error(code: str, message: str) -> str:
    """Format an error string for CLI stderr output."""
    return f"error [{code}]: {message}"
