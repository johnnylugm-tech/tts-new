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

import time
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")

CIRCUIT_BREAKER_THRESHOLD: int = 3
"""Consecutive-failure count that trips the breaker (SPEC.md L130)."""

CIRCUIT_BREAKER_TIMEOUT: float = 10.0
"""Seconds the breaker stays OPEN before allowing a HALF_OPEN probe
(SPEC.md L131)."""


class CircuitOpenError(Exception):
    """Raised when a call is attempted while the breaker is OPEN.

    The route layer maps this to HTTP 503 with a Retry-After header
    (SPEC.md L215).
    """


class CircuitBreaker:
    """Three-state circuit breaker (CLOSED / OPEN / HALF_OPEN).

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
        self.threshold: int = threshold
        self.timeout: float = timeout
        self.time_func: Callable[[], float] = time_func
        self.state: str = "CLOSED"
        self.failure_count: int = 0
        self.opened_at: float | None = None
        self.last_transition_at: float | None = None

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

    async def call(self, coro: Awaitable[T]) -> T:
        """Execute `coro` through the breaker.

        - CLOSED: run the coroutine. Success resets the counter to 0;
          failure increments it; reaching `threshold` trips to OPEN.
        - OPEN: if `timeout` has elapsed, transition to HALF_OPEN and
          admit the coroutine as a probe. Otherwise raise
          `CircuitOpenError` immediately (fast-fail, no backend call).
        - HALF_OPEN: success → CLOSED, failure → OPEN (timeout reset).
        """
        if self.state == "OPEN":
            now = self.time_func()
            if self.opened_at is not None and (now - self.opened_at) >= self.timeout:
                self._transition("HALF_OPEN")
            else:
                if hasattr(coro, "close"):
                    coro.close()
                raise CircuitOpenError(
                    f"circuit breaker is OPEN "
                    f"(opened at {self.opened_at}, timeout {self.timeout}s)"
                )

        try:
            result = await coro
        except BaseException:
            self._on_failure()
            raise

        self._on_success()
        return result

    def _on_success(self) -> None:
        if self.state == "HALF_OPEN":
            self._transition("CLOSED")
            return
        # CLOSED: a single success resets the consecutive-failure
        # counter (AC1 sub-assertion in case 2; AC3 sub-assertion in
        # case 1).
        self.failure_count = 0

    def _on_failure(self) -> None:
        if self.state == "HALF_OPEN":
            # AC2 sub-assertion (case 6): failed probe reverts to OPEN
            # and resets the timeout clock; failure_count becomes 1
            # (HALF_OPEN reset to 0 + this failure). opened_at is
            # refreshed to "now" so the new 10 s window starts here.
            self._transition("OPEN", opened_at=self.time_func())
            self.failure_count = 1
            return
        # CLOSED
        self.failure_count += 1
        if self.failure_count >= self.threshold:
            self._transition("OPEN")

    def reset(self) -> str:
        """Force the breaker to CLOSED; return the prior state string."""
        previous = self.state
        self._transition("CLOSED")
        return previous
