"""[NFR-08] CLI-specific logging helpers for structured output.

CLI operations use different log semantics than HTTP handlers:
no request IDs, circuit states, or HTTP status codes.
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def log_cli_event(event: str, **kwargs: object) -> dict[str, object]:
    """Build a structured log extra dict for CLI operations."""
    return {"event": event, **kwargs}


def format_cli_error(code: str, message: str) -> str:
    """Format an error string for CLI stderr output."""
    return f"error [{code}]: {message}"
