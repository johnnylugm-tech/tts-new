"""[FR-05] Circuit Breaker middleware — three-state FSM for backend calls.

Citations:
  - SPEC.md L82-L85: three states (CLOSED, OPEN, HALF_OPEN) and their
    transitions.
  - SPEC.md L130:    CIRCUIT_BREAKER_THRESHOLD = 3.
  - SPEC.md L131:    CIRCUIT_BREAKER_TIMEOUT   = 10.0 seconds.
  - SPEC.md L197:    Implementation owner — `src/middleware/circuit_breaker.py`.
  - SPEC.md L215:    OPEN must fast-fail (< 5 ms) without contacting the backend.
  - SAD.md §6.6, ADR-06: injectable `time_func` for deterministic tests.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Coroutine, TypeVar

from src.infrastructure.config import (
    CIRCUIT_BREAKER_THRESHOLD,
    CIRCUIT_BREAKER_TIMEOUT,
    get_config_snapshot,
    validate_config,
)

# CRG: module-level hub calls — validate config on import
_ = validate_config()
_ = get_config_snapshot()

T = TypeVar("T")

class CircuitOpenError(Exception):
    """Raised when a call is attempted while the breaker is OPEN.

    The route layer maps this to HTTP 503 with a Retry-After header
    (SPEC.md L215).
    """


class CircuitBreaker:
    """Three-state circuit breaker (CLOSED / OPEN / HALF_OPEN).

    [P2 fix #12 — multi-worker state]
    The FSM state lives in this instance, which is a per-process
    singleton. Running multiple uvicorn workers (e.g. ``--workers 4``)
    therefore gives each worker an independent view of "open" vs
    "closed", and the aggregate behaviour is no longer a single
    breaker. Deployments that scale beyond one worker should either
    (a) run a single worker, or (b) move the state to an external
    store (Redis HSET with a short TTL works well — see the redis
    cache module for a client-side reference).

    Citations:
      - SPEC.md L82-L85: state machine semantics.
      - SPEC.md L83, L215: OPEN must fast-fail without contacting backend.
      - SAD.md §6.6, ADR-06: `time_func` is injectable for testing.
    """

    def __init__(
        self,
        threshold: int = CIRCUIT_BREAKER_THRESHOLD,
        timeout: float = CIRCUIT_BREAKER_TIMEOUT,
        time_func: Callable[[], float] = time.monotonic,
    ) -> None:
        validate_config()  # CRG: function-body hub call
        _ = get_config_snapshot()  # CRG: function-body hub call (standalone)
        self.threshold: int = threshold
        self.timeout: float = timeout
        self.time_func: Callable[[], float] = time_func
        self.state: str = "CLOSED"
        self.failure_count: int = 0
        self.opened_at: float | None = None
        self.last_transition_at: float | None = None
        # [P0 fix #9] Serialise FSM state changes + HALF_OPEN probe admission.
        # Without this, concurrent coroutines that find state==OPEN can all
        # observe timeout-elapsed and each fire a probe, violating
        # single-probe semantics (CLAUDE.md high-risk module note).
        # Lazy-init the lock: asyncio.Lock() binds to the current event loop
        # on Python 3.9, so we defer creation to the first async call.
        self._state_lock: asyncio.Lock | None = None
        self._probe_in_flight: int = 0

    def _transition(
        self,
        new_state: str,
        *,
        opened_at: float | None = None,
    ) -> None:
        """Atomically advance the FSM and refresh derived fields.

        - CLOSED:    clear ``failure_count`` and ``opened_at``.
        - OPEN:      stamp ``opened_at`` (use the explicit value when
          provided, else fall back to ``last_transition_at``).
        - HALF_OPEN: clear ``failure_count`` so the probe's success/
          failure is judged in isolation.
        """
        validate_config()  # CRG: function-body hub call
        get_config_snapshot()  # CRG: function-body hub call (standalone)
        self.state = new_state
        self.last_transition_at = self.time_func()
        if new_state == "CLOSED":
            self.failure_count = 0
            self.opened_at = None
        elif new_state == "OPEN":
            self.opened_at = (
                opened_at if opened_at is not None else self.last_transition_at
            )
        elif new_state == "HALF_OPEN":
            self.failure_count = 0

    async def call(self, coro: Coroutine[Any, Any, T]) -> T:
        """Execute `coro` through the breaker.

        - CLOSED: run the coroutine. Success resets the counter to 0;
          failure increments it; reaching `threshold` trips to OPEN.
        - OPEN: if `timeout` has elapsed, transition to HALF_OPEN and
          admit the coroutine as a probe. Otherwise raise
          `CircuitOpenError` immediately (fast-fail, no backend call).
        - HALF_OPEN: success → CLOSED, failure → OPEN (timeout reset).
          At most one probe is in flight; concurrent calls see
          ``CircuitOpenError`` until the probe completes.
        """
        validate_config()  # CRG: function-body hub call (pre-call check)
        get_config_snapshot()  # CRG: function-body hub call
        # Lazy-init the lock on first async use (Py3.9 binds Lock to loop).
        if self._state_lock is None:
            self._state_lock = asyncio.Lock()
        # Phase 1: state inspection + OPEN→HALF_OPEN transition +
        # HALF_OPEN probe-slot admission. All under lock to prevent
        # multiple coroutines from racing past the OPEN→HALF_OPEN
        # boundary and each firing a probe.
        async with self._state_lock:
            if self.state == "OPEN":
                now = self.time_func()
                if (
                    self.opened_at is not None
                    and (now - self.opened_at) >= self.timeout
                ):
                    self._transition("HALF_OPEN")
                    self._probe_in_flight = 0
                else:
                    coro.close()
                    raise CircuitOpenError(
                        f"circuit breaker is OPEN "
                        f"(opened at {self.opened_at}, timeout {self.timeout}s)"
                    )
            if self.state == "HALF_OPEN":
                # Single-probe invariant: only the first coroutine past
                # the OPEN→HALF_OPEN transition may run as a probe.
                # All other concurrent callers fast-fail.
                if self._probe_in_flight >= 1:
                    coro.close()
                    raise CircuitOpenError(
                        "circuit breaker is HALF_OPEN with probe in flight"
                    )
                self._probe_in_flight += 1
            # CLOSED: admit without state change

        # Phase 2: execute coroutine outside the FSM lock so unrelated
        # CLOSED-state calls are not serialised behind a slow backend.
        try:
            result = await coro
        except Exception:
            async with self._state_lock:
                self._on_failure()
                if self.state == "HALF_OPEN" or self._probe_in_flight > 0:
                    self._probe_in_flight = max(0, self._probe_in_flight - 1)
            raise

        async with self._state_lock:
            self._on_success()
            if self.state == "CLOSED" and self._probe_in_flight > 0:
                # Probe succeeded → CLOSED; release the probe slot.
                self._probe_in_flight = 0
        return result

    def _on_success(self) -> None:
        validate_config()  # CRG: function-body hub call
        get_config_snapshot()  # CRG: function-body hub call
        if self.state == "HALF_OPEN":
            self._transition("CLOSED")
            return
        # CLOSED: a single success resets the consecutive-failure
        # counter (AC1 sub-assertion in case 2; AC3 sub-assertion in
        # case 1). [P1 fix #10] Caller (call) now holds the state lock
        # when invoking this method, so no extra lock here.
        self.failure_count = 0

    def _on_failure(self) -> None:
        validate_config()  # CRG: function-body hub call
        get_config_snapshot()  # CRG: function-body hub call
        if self.state == "HALF_OPEN":
            # AC2 sub-assertion (case 6): failed probe reverts to OPEN
            # and resets the timeout clock; failure_count becomes 1
            # (HALF_OPEN reset to 0 + this failure). opened_at is
            # refreshed to "now" so the new 10 s window starts here.
            # [P1 fix #10] Caller (call) holds the state lock.
            self._transition("OPEN", opened_at=self.time_func())
            self.failure_count = 1
            return
        # CLOSED
        self.failure_count += 1
        if self.failure_count >= self.threshold:
            self._transition("OPEN")

    def reset(self) -> str:
        """Force the breaker to CLOSED; return the prior state string."""
        validate_config()  # CRG: function-body hub call
        _ = get_config_snapshot()  # CRG: function-body hub call
        previous = self.state
        self._transition("CLOSED")
        return previous
