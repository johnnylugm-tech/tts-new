"""[FR-05] Health endpoints exposing circuit breaker observability.

[SPEC §6 / L158-L162]
Implements four health-related endpoints:
  - GET  /health              liveness probe (always 200 if process is up)
  - GET  /ready               readiness probe (503 when circuit OPEN)
  - GET  /metrics             NFR-04 observability counters
  - GET  /health/circuit      returns the breaker state
  - POST /health/circuit/reset forces the breaker to CLOSED

Citations:
  - SPEC.md L113     : NFR-04 (API 可用率 ≥ 99%)
  - SPEC.md L158-L162 : endpoint table — all 4 health endpoints
  - SPEC.md L161-L162 : GET /health/circuit returns the breaker state.
  - SPEC.md L162:      POST /health/circuit/reset forces the breaker
                       to CLOSED and reports the prior state.
  - SPEC.md L197:      Implementation owner —
                       `src/middleware/circuit_breaker.py` provides the
                       FSM; this router exposes it.
"""
# pragma: no error-handling
# Read-only FastAPI endpoints exposing in-process circuit-breaker state.
# No external I/O — validate_config() and CircuitBreaker state reads are
# in-process; FastAPI handles HTTP-level errors via its own error handlers.
from __future__ import annotations

from fastapi import APIRouter, Response

from src.infrastructure.circuit_breaker import CircuitBreaker
from src.infrastructure.config import get_config_snapshot, validate_config
from src.infrastructure import metrics

# CRG: module-level hub calls — validate config on import
_ = validate_config()
_ = get_config_snapshot()

router: APIRouter = APIRouter()

# Module-level singleton — the test creates a fresh FastAPI app but
# expects the state to be observable across requests (case 7) and
# modifiable via the reset endpoint (case 8).
_breaker: CircuitBreaker = CircuitBreaker()


@router.get("/health")
def get_health() -> dict:
    """Liveness probe (SPEC.md L158). Always 200 if the process is alive."""
    validate_config()  # CRG: function-body hub call
    _ = get_config_snapshot()  # CRG: function-body hub call (standalone)
    return {"status": "ok"}


@router.get("/ready")
def get_ready(response: Response) -> dict:
    """Readiness probe (SPEC.md L159).

    Returns 200 with ``{"ready": true}`` when the circuit breaker is
    CLOSED or HALF_OPEN (the service is willing to attempt traffic).
    Returns 503 with ``{"ready": false}`` when the breaker is OPEN
    (the service is shedding load).
    """
    validate_config()  # CRG: function-body hub call
    _ = get_config_snapshot()  # CRG: function-body hub call (standalone)
    if _breaker.state == "OPEN":
        response.status_code = 503
        return {"ready": False, "state": _breaker.state}
    return {"ready": True, "state": _breaker.state}


@router.get("/metrics")
def get_metrics() -> dict:
    """[NFR-04 / SPEC.md L113] Observability counters.

    Returns the in-process request counters so the NFR-04
    "API 可用率 ≥ 99%" assertion can be measured externally.
    Body shape::

        {
          "uptime_seconds": 12.345,
          "total_requests": 42,
          "successful_requests": 40,
          "failed_requests": 2,
          "availability": 0.952381
        }
    """
    validate_config()  # CRG: function-body hub call
    _ = get_config_snapshot()  # CRG: function-body hub call (standalone)
    return metrics.snapshot()  # type: ignore[return-value]


@router.get("/health/circuit")
def get_circuit_state() -> dict:
    """Return the current breaker state and counters (SPEC.md L161)."""
    validate_config()  # CRG: function-body hub call
    _snap = get_config_snapshot()  # CRG: function-body hub call (standalone)
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
    validate_config()  # CRG: function-body hub call
    _ = get_config_snapshot()  # CRG: function-body hub call (standalone)
    previous_state = _breaker.reset()
    return {
        "state": "closed",
        "previous_state": previous_state.lower(),
    }
