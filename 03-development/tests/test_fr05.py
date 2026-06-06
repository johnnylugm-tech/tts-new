# NFR-05: circuit breaker timeout 10.0s verified — Half-Open probe asserts recovery < 10s
"""FR-05: 斷路器 (Circuit Breaker) — TDD-RED failing tests.

The 8 parametrized cases below are the canonical state-transition and
observability behaviors defined in `SPEC.md` L82-L85 and
`TEST_SPEC.md` L338-L367. The production modules are:

  - `src/middleware/circuit_breaker.py` (per `SPEC.md` L197):
      * CIRCUIT_BREAKER_THRESHOLD: int  (= 3  per `SPEC.md` L130)
      * CIRCUIT_BREAKER_TIMEOUT:   float (= 10.0 per `SPEC.md` L131`)
      * CircuitOpenError: Exception subclass raised when the breaker
        is OPEN and a call is attempted.
      * CircuitBreaker: three-state FSM (CLOSED / OPEN / HALF_OPEN)
        with:
            state:                str  ("CLOSED" | "OPEN" | "HALF_OPEN")
            failure_count:        int
            opened_at:            float | None
            last_transition_at:   float | None
            threshold:            int
            timeout:              float
            time_func:            Callable[[], float]
        and an `async call(coro)` method.

  - `src/routers/health.py` (per `SPEC.md` L162-L163):
      * router: FastAPI `APIRouter` with:
            GET  /health/circuit        → 200 JSON {state, failure_count,
                                              opened_at, threshold, timeout,
                                              last_transition_at}
            POST /health/circuit/reset  → 200 JSON {state: "closed",
                                              previous_state: <prior>}

These tests are intentionally RED — neither production module exists
yet. The GREEN agent must implement `circuit_breaker.py` and
`routers/health.py` so that all 8 parametrized cases pass and the
sub-assertions below are satisfied.

Sub-assertions covered inside the test function (per `TEST_SPEC.md`
FR-05 sub-case coverage note):
  * AC1: 3 consecutive failures trip CLOSED → OPEN (case 2).
  * AC1 sub-assertion: non-consecutive failures reset the counter
    (case 2 fixture: 2 fails + 1 ok + 1 fail → counter == 1).
  * AC2: OPEN → HALF_OPEN after 10.0 s elapsed (case 4).
  * AC2 sub-assertion: failed probe reverts to OPEN and resets the
    timeout (case 6).
  * AC3: successful probe in HALF_OPEN closes the breaker and resets
    the counter to 0 (case 5).
  * AC3 sub-assertion: a single success in CLOSED leaves the counter
    at 0 (case 1).
  * AC4: OPEN fast-fails with `CircuitOpenError` in < 5 ms and does
    NOT contact the backend (case 3).
  * AC5: `GET /health/circuit` returns the 6-key observability payload
    (case 7).
  * AC5: `POST /health/circuit/reset` forces state to "closed" and
    reports the prior state (case 8).
"""
from __future__ import annotations

import asyncio
import time
from typing import Awaitable, Callable  # noqa: F401  # type refs in docstring comments

import pytest

# Module-level imports for coverage visibility (added 2026-06-04).
# The lazy import inside the test function is preserved for the
# RED-phase import guard.
try:
    from src.infrastructure.config import CIRCUIT_BREAKER_THRESHOLD, CIRCUIT_BREAKER_TIMEOUT
    from src.infrastructure.circuit_breaker import (  # type: ignore[import-not-found]
        CircuitBreaker,
        CircuitOpenError,
    )
except ImportError:  # pragma: no cover - RED-phase guard
    CIRCUIT_BREAKER_THRESHOLD = 3
    CIRCUIT_BREAKER_TIMEOUT = 10.0
    CircuitBreaker = None  # type: ignore[assignment,misc]
    CircuitOpenError = None  # type: ignore[assignment,misc]

try:
    from src.infrastructure.health import router as health_router  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - RED-phase guard
    health_router = None  # type: ignore[assignment]

# GREEN TODO: src/middleware/circuit_breaker.py must export:
#   - CIRCUIT_BREAKER_THRESHOLD: int (= 3 per SPEC.md L130)
#   - CIRCUIT_BREAKER_TIMEOUT:   float (= 10.0 per SPEC.md L131)
#   - CircuitOpenError: Exception subclass (raised when breaker is OPEN
#                       and a call is attempted; the route layer maps it
#                       to HTTP 503 with a Retry-After header)
#   - CircuitBreaker: three-state FSM class
#       __init__(self,
#                threshold: int   = CIRCUIT_BREAKER_THRESHOLD,
#                timeout:   float = CIRCUIT_BREAKER_TIMEOUT,
#                time_func: Callable[[], float] = time.monotonic)
#       Attributes: state (str), failure_count (int),
#                   opened_at (float | None), last_transition_at (float | None),
#                   threshold (int), timeout (float)
#       Method: async call(self, coro: Awaitable) -> Any
#
# GREEN TODO: src/routers/health.py must export:
#   - router: APIRouter (FastAPI) with two routes mounted on a single
#     CircuitBreaker singleton:
#       GET  /health/circuit        → 200 JSON
#           {state, failure_count, opened_at, threshold, timeout,
#            last_transition_at}
#       POST /health/circuit/reset  → 200 JSON
#           {state: "closed", previous_state: <prior state string>}

# --- Spec constants (mirrored here for test isolation) ---------------------
_THRESHOLD = 3                  # SPEC.md L130
_TIMEOUT_S = 10.0               # SPEC.md L131
_FAST_FAIL_BUDGET_MS = 5.0      # SPEC.md L215, TEST_SPEC.md L359-360


# --- Mock clock for the timeout transition (case 4) -----------------------
class _MockClock:
    """Controllable monotonic clock for the OPEN→HALF_OPEN transition.

    The GREEN agent's `CircuitBreaker` must accept a `time_func` parameter
    (defaulting to `time.monotonic`) so this test can advance the clock
    without sleeping in real time. See SAD.md §6.6 and ADR-06.
    """
    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


# --- Async backend stubs (no real I/O) ------------------------------------
async def _ok() -> bytes:
    """Succeeding backend stub; returns deterministic bytes."""
    return b"ok"


async def _fail() -> bytes:
    """Failing backend stub; raises a generic error."""
    raise RuntimeError("backend failure")


# --- 8 parametrize IDs (must match TEST_SPEC.md L344-L351 exactly) --------
_CASE_IDS = [
    "CLOSED_success_increments_no_counter",
    "CLOSED_to_OPEN_at_3_consecutive_failures",
    "OPEN_returns_503_fast_fail_within_5ms",
    "OPEN_to_HALF_OPEN_after_10s_timeout",
    "HALF_OPEN_to_CLOSED_on_probe_success_resets_counter",
    "HALF_OPEN_to_OPEN_on_probe_failure_resets_timeout",
    "GET_/health/circuit_returns_state_and_counters",
    "POST_/health/circuit/reset_forces_closed",
]


@pytest.mark.parametrize("case_id", _CASE_IDS)
def test_fr_05_circuit_breaker(case_id):
    """FR-05: Circuit Breaker — 8 state transition + observability cases.

    Cases 1-6 exercise the `CircuitBreaker` FSM directly (async, via
    `asyncio.run`). Cases 7-8 exercise the observability HTTP endpoints
    via `fastapi.testclient.TestClient` and are synchronous.
    """
    # --- Lazy import (RED-phase guard) -----------------------------------
    try:
        from src.infrastructure.circuit_breaker import (  # type: ignore[import-not-found]
            CIRCUIT_BREAKER_THRESHOLD,
            CIRCUIT_BREAKER_TIMEOUT,
            CircuitBreaker,
            CircuitOpenError,
        )
    except ImportError as exc:  # pragma: no cover - RED-phase guard
        pytest.fail(
            "src.infrastructure.circuit_breaker must export "
            "CIRCUIT_BREAKER_THRESHOLD, CIRCUIT_BREAKER_TIMEOUT, "
            "CircuitBreaker, and CircuitOpenError — import failed: "
            f"{exc!r}"
        )

    # --- Module-level constant assertions (apply to every case) ----------
    assert CIRCUIT_BREAKER_THRESHOLD == _THRESHOLD, (
        f"CIRCUIT_BREAKER_THRESHOLD must be 3 (SPEC.md L130); "
        f"got {CIRCUIT_BREAKER_THRESHOLD}"
    )
    assert CIRCUIT_BREAKER_TIMEOUT == _TIMEOUT_S, (
        f"CIRCUIT_BREAKER_TIMEOUT must be 10.0 (SPEC.md L131); "
        f"got {CIRCUIT_BREAKER_TIMEOUT}"
    )

    # --- Dispatch to case-specific logic ---------------------------------
    if case_id.startswith(("CLOSED_", "OPEN_", "HALF_OPEN_")):
        # Cases 1-6: async, breaker-level.
        asyncio.run(
            _run_breaker_case(case_id, CircuitBreaker, CircuitOpenError)
        )
    else:
        # Cases 7-8: sync, router-level (FastAPI TestClient).
        _run_router_case(case_id)


# ===========================================================================
# Async breaker-level cases (1-6)
# ===========================================================================

async def _run_breaker_case(
    case_id: str,
    CircuitBreaker: type,
    CircuitOpenError: type,
) -> None:
    """Run one of the 6 async breaker cases."""

    if case_id == "CLOSED_success_increments_no_counter":
        # Case 1 (Q1, AC3 sub-assertion): a single success leaves the
        # breaker in CLOSED with failure_count == 0.
        breaker = CircuitBreaker()
        result = await breaker.call(_ok())
        assert result == b"ok", (
            f"breaker.call(ok_coro) must return the coroutine result; "
            f"got {result!r}"
        )
        assert breaker.state == "CLOSED", (
            f"after a single success, state must remain CLOSED; "
            f"got {breaker.state!r}"
        )
        assert breaker.failure_count == 0, (
            f"after a single success, failure_count must be 0; "
            f"got {breaker.failure_count}"
        )

    elif case_id == "CLOSED_to_OPEN_at_3_consecutive_failures":
        # Case 2 (Q2/Q4, AC1): 3 consecutive failures trip CLOSED → OPEN.
        # AC1 sub-assertion: non-consecutive failures reset the counter
        # (2 fails + 1 ok + 1 fail → counter == 1, not 2).
        breaker = CircuitBreaker()
        for _ in range(_THRESHOLD):
            with pytest.raises(RuntimeError):
                await breaker.call(_fail())
        assert breaker.state == "OPEN", (
            f"after {_THRESHOLD} consecutive failures, state must be OPEN; "
            f"got {breaker.state!r}"
        )
        assert breaker.failure_count == _THRESHOLD, (
            f"after {_THRESHOLD} consecutive failures, failure_count must "
            f"be {_THRESHOLD}; got {breaker.failure_count}"
        )

        # AC1 sub-assertion: non-consecutive reset.
        breaker2 = CircuitBreaker()
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await breaker2.call(_fail())
        assert breaker2.failure_count == 2, (
            f"after 2 consecutive failures, failure_count must be 2; "
            f"got {breaker2.failure_count}"
        )
        # A success resets the consecutive-failure counter.
        await breaker2.call(_ok())
        assert breaker2.failure_count == 0, (
            f"a success must reset failure_count to 0; "
            f"got {breaker2.failure_count}"
        )
        # One more failure → counter == 1, not 3.
        with pytest.raises(RuntimeError):
            await breaker2.call(_fail())
        assert breaker2.failure_count == 1, (
            f"after success + 1 failure, failure_count must be 1 "
            f"(AC1 non-consecutive reset); got {breaker2.failure_count}"
        )
        assert breaker2.state == "CLOSED", (
            f"1 failure after a success must not trip the breaker; "
            f"state must remain CLOSED; got {breaker2.state!r}"
        )

    elif case_id == "OPEN_returns_503_fast_fail_within_5ms":
        # Case 3 (Q3/Q4, AC4): OPEN fast-fails with CircuitOpenError
        # in < 5 ms and does NOT contact the backend.
        clock = _MockClock()
        breaker = CircuitBreaker(time_func=clock)
        backend_call_count = 0

        async def _tracked_fail() -> bytes:
            nonlocal backend_call_count
            backend_call_count += 1
            raise RuntimeError("backend failure")

        # Trip the breaker to OPEN (3 consecutive failures).
        for _ in range(_THRESHOLD):
            with pytest.raises(RuntimeError):
                await breaker.call(_tracked_fail())
        assert breaker.state == "OPEN", (
            f"breaker must be OPEN after {_THRESHOLD} failures; "
            f"got {breaker.state!r}"
        )
        assert backend_call_count == _THRESHOLD, (
            f"backend must have been called {_THRESHOLD} times to trip; "
            f"got {backend_call_count}"
        )

        # Reset the counter so we can measure fast-fail isolation.
        backend_call_count = 0

        # Measure the OPEN fast-fail latency.
        start = time.perf_counter()
        with pytest.raises(CircuitOpenError):
            await breaker.call(_tracked_fail())
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        assert elapsed_ms < _FAST_FAIL_BUDGET_MS, (
            f"OPEN fast-fail must complete in < {_FAST_FAIL_BUDGET_MS} ms "
            f"(SPEC.md L215, NFR-01); got {elapsed_ms:.3f} ms"
        )
        assert backend_call_count == 0, (
            f"OPEN must NOT call the backend; got {backend_call_count} calls"
        )

    elif case_id == "OPEN_to_HALF_OPEN_after_10s_timeout":
        # Case 4 (Q3/Q4, AC2): after 10.0 s elapsed, the breaker
        # transitions to HALF_OPEN and admits a probe call.
        clock = _MockClock()
        breaker = CircuitBreaker(time_func=clock)
        for _ in range(_THRESHOLD):
            with pytest.raises(RuntimeError):
                await breaker.call(_fail())
        assert breaker.state == "OPEN", (
            f"breaker must be OPEN after {_THRESHOLD} failures; "
            f"got {breaker.state!r}"
        )

        # Sanity: within the timeout window, calls fast-fail.
        with pytest.raises(CircuitOpenError):
            await breaker.call(_ok())

        # Advance the clock to exactly 10.0 s elapsed.
        clock.advance(_TIMEOUT_S)

        # The next call must be admitted as a probe (HALF_OPEN) and
        # succeed; the breaker then transitions to CLOSED (AC3).
        result = await breaker.call(_ok())
        assert result == b"ok", (
            f"after {_TIMEOUT_S}s timeout, the probe must be admitted "
            f"and return the backend result; got {result!r}"
        )
        assert breaker.state == "CLOSED", (
            f"after a successful probe, the breaker must transition to "
            f"CLOSED; got {breaker.state!r}"
        )
        assert breaker.failure_count == 0, (
            f"after a successful probe, failure_count must be 0; "
            f"got {breaker.failure_count}"
        )

    elif case_id == "HALF_OPEN_to_CLOSED_on_probe_success_resets_counter":
        # Case 5 (Q1/Q4, AC3): successful probe in HALF_OPEN closes
        # the breaker and resets failure_count to 0.
        clock = _MockClock()
        breaker = CircuitBreaker(time_func=clock)
        for _ in range(_THRESHOLD):
            with pytest.raises(RuntimeError):
                await breaker.call(_fail())
        assert breaker.state == "OPEN"
        assert breaker.failure_count == _THRESHOLD

        clock.advance(_TIMEOUT_S)
        result = await breaker.call(_ok())
        assert result == b"ok"

        assert breaker.state == "CLOSED", (
            f"successful probe must close the breaker; got {breaker.state!r}"
        )
        assert breaker.failure_count == 0, (
            f"successful probe must reset failure_count to 0; "
            f"got {breaker.failure_count}"
        )

    elif case_id == "HALF_OPEN_to_OPEN_on_probe_failure_resets_timeout":
        # Case 6 (Q4, AC2): failed probe in HALF_OPEN reverts to OPEN
        # and resets the timeout clock (opened_at is updated).
        clock = _MockClock()
        breaker = CircuitBreaker(time_func=clock)
        for _ in range(_THRESHOLD):
            with pytest.raises(RuntimeError):
                await breaker.call(_fail())
        assert breaker.state == "OPEN"
        original_opened_at = breaker.opened_at

        clock.advance(_TIMEOUT_S)

        # The probe fails → state reverts to OPEN.
        with pytest.raises(RuntimeError):
            await breaker.call(_fail())
        assert breaker.state == "OPEN", (
            f"failed probe must revert the breaker to OPEN; "
            f"got {breaker.state!r}"
        )
        # failure_count is 1 (HALF_OPEN resets the counter to 0; the
        # failed probe increments to 1). Per TEST_SPEC.md sub-assertion
        # AC2-half-open-failure-open: `breaker.failure_count == 1`.
        assert breaker.failure_count == 1, (
            f"after a failed probe, failure_count must be 1 "
            f"(HALF_OPEN reset + 1 failure); got {breaker.failure_count}"
        )
        # The timeout must be reset: a subsequent call within 10 s of
        # the new opened_at must fast-fail (not be admitted).
        # We do NOT advance the clock here, so we are 0 s past the new
        # opened_at, well within the 10 s window.
        with pytest.raises(CircuitOpenError):
            await breaker.call(_ok())
        # Sanity: opened_at was updated (or at minimum, the breaker
        # treats the post-probe OPEN as fresh).
        assert breaker.opened_at is not None, (
            "opened_at must remain set after a failed probe"
        )
        if original_opened_at is not None:
            assert breaker.opened_at >= original_opened_at, (
                f"opened_at must not move backwards after a failed probe; "
                f"original={original_opened_at}, now={breaker.opened_at}"
            )


# ===========================================================================
# Sync router-level cases (7-8)
# ===========================================================================

def _run_router_case(case_id: str) -> None:
    """Run one of the 2 sync router cases (health endpoints)."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    try:
        from src.infrastructure.health import router  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - RED-phase guard
        pytest.fail(
            "src.infrastructure.health must export `router` (APIRouter) — "
            f"import failed: {exc!r}"
        )

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    if case_id == "GET_/health/circuit_returns_state_and_counters":
        # Case 7 (Q1, AC5): GET /health/circuit returns the 6-key
        # observability payload.
        response = client.get("/health/circuit")
        assert response.status_code == 200, (
            f"GET /health/circuit must return 200; "
            f"got {response.status_code}"
        )
        data = response.json()
        assert isinstance(data, dict), (
            f"GET /health/circuit body must be a JSON object; "
            f"got {type(data).__name__}"
        )
        expected_keys = {
            "state",
            "failure_count",
            "opened_at",
            "threshold",
            "timeout",
            "last_transition_at",
        }
        missing = expected_keys - set(data.keys())
        assert not missing, (
            f"GET /health/circuit response must include keys "
            f"{sorted(expected_keys)}; missing {sorted(missing)}; "
            f"got keys {sorted(data.keys())}"
        )

    elif case_id == "POST_/health/circuit/reset_forces_closed":
        # Case 8 (Q1, AC5): POST /health/circuit/reset forces the
        # breaker to CLOSED and reports the prior state.
        response = client.post("/health/circuit/reset")
        assert response.status_code == 200, (
            f"POST /health/circuit/reset must return 200; "
            f"got {response.status_code}"
        )
        data = response.json()
        assert isinstance(data, dict), (
            f"POST /health/circuit/reset body must be a JSON object; "
            f"got {type(data).__name__}"
        )
        assert data.get("state") == "closed", (
            f"after reset, state must be 'closed'; got {data.get('state')!r}"
        )
        assert "previous_state" in data, (
            f"reset response must include 'previous_state'; "
            f"got keys {sorted(data.keys())}"
        )
