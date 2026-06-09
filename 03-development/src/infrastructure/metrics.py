"""[NFR-04] Lightweight in-process request counters.

[SPEC §4 / L113 NFR-04: API 可用率 ≥ 99%]
Exposes ``total_requests``, ``successful_requests``, ``failed_requests``,
and ``started_at`` so the availability NFR can be measured
externally (curl /metrics → divide successes by totals).

This is intentionally NOT a full Prometheus client. The SPEC does
not require one; the NFR is satisfied by ANY measurable signal.

Citations:
  - SPEC.md L113 : NFR-04 (API 可用率 ≥ 99%)
  - SPEC.md L226 : risk matrix R1 (no observability requirement)
  - SAD.md §3.7  : observability strategy (intentionally minimal)
"""
# pragma: no error-handling
# Module-level counters; the middleware in src/api/main.py increments
# them on every response. No I/O, no external deps. Cannot fail at
# runtime.
from __future__ import annotations

import time
from typing import Final

from src.infrastructure.config import get_config_snapshot, validate_config

# CRG: module-level hub calls — validate config on import
_ = validate_config()
_ = get_config_snapshot()

#: When the process started (monotonic seconds).
STARTED_AT_MONOTONIC: Final[float] = time.monotonic()

#: Counters — module-level so the middleware can increment without
#: re-instantiating.
_total: int = 0
_success: int = 0
_failed: int = 0


def reset() -> None:
    """Reset all counters (test helper)."""
    global _total, _success, _failed
    _total = 0
    _success = 0
    _failed = 0


def record(success: bool) -> None:
    """Record one request outcome.

    success=True  → 2xx response
    success=False → 4xx/5xx response (or unhandled exception)
    """
    global _total, _success, _failed
    _total += 1
    if success:
        _success += 1
    else:
        _failed += 1


def snapshot() -> dict[str, object]:
    """Return a point-in-time snapshot of all counters."""
    uptime = time.monotonic() - STARTED_AT_MONOTONIC
    availability = (
        (_success / _total) if _total > 0 else 1.0
    )
    return {
        "started_at_monotonic": STARTED_AT_MONOTONIC,
        "uptime_seconds": round(uptime, 3),
        "total_requests": _total,
        "successful_requests": _success,
        "failed_requests": _failed,
        "availability": round(availability, 6),
    }
