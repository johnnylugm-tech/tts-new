"""[FR-05] Health endpoints exposing circuit breaker observability.

Citations:
  - SPEC.md L161-L162: GET /health/circuit returns the breaker state.
  - SPEC.md L162:      POST /health/circuit/reset forces the breaker
                       to CLOSED and reports the prior state.
  - SPEC.md L197:      Implementation owner —
                       `src/middleware/circuit_breaker.py` provides the
                       FSM; this router exposes it.
"""
from __future__ import annotations

from fastapi import APIRouter

from src.infrastructure.circuit_breaker import CircuitBreaker

router: APIRouter = APIRouter()

# Module-level singleton — the test creates a fresh FastAPI app but
# expects the state to be observable across requests (case 7) and
# modifiable via the reset endpoint (case 8).
_breaker: CircuitBreaker = CircuitBreaker()


@router.get("/health/circuit")
def get_circuit_state() -> dict:
    """Return the current breaker state and counters (SPEC.md L161)."""
    return {
        "state": _breaker.state,
        "failure_count": _breaker.failure_count,
        "opened_at": _breaker.opened_at,
        "threshold": _breaker.threshold,
        "timeout": _breaker.timeout,
        "last_transition_at": _breaker.last_transition_at,
    }


@router.post("/health/circuit/reset")
def post_circuit_reset() -> dict:
    """Force the breaker to CLOSED (SPEC.md L162)."""
    previous_state = _breaker.reset()
    return {
        "state": "closed",
        "previous_state": previous_state.lower(),
    }
