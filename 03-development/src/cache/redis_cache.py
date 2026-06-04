"""FR-06 — Optional Redis cache for TTS audio bytes.

[FR-06]
Cache key is derived via SHA-256 of the canonical form:
  text + "\\x00" + voice + "\\x00" + str(round(speed, 2))
Key format: "tts:cache:<sha256_hex>"  (P2-DD-3, ADR-05)

redis is NOT imported at module level so that the proxy starts without
a live Redis installation (SPEC.md L88-L89, L229).  The caller constructs
and injects the client; this module only holds logic.

Citations:
  - SPEC.md L86-L89     : FR-06 caching requirement
  - SRS.md §3 FR-06     : acceptance criteria (AC1-AC5, L258-L270)
  - SAD.md §3.6         : RedisCache module role
  - ADR.md ADR-05       : SHA-256 key derivation (P2-DD-3)
  - TEST_SPEC.md FR-06  : 7 test cases
"""
from __future__ import annotations

import hashlib
import logging

log = logging.getLogger(__name__)


def make_cache_key(text: str, voice: str, speed: float) -> str:
    """Derive a deterministic Redis key for a (text, voice, speed) tuple.

    [FR-06]
    Canonical form: text + "\\x00" + voice + "\\x00" + str(round(speed, 2))
    Key format:     "tts:cache:<sha256_hex>"

    Citations:
      - SPEC.md L87      : key derivation spec
      - ADR.md ADR-05    : SHA-256 (P2-DD-3)
      - SRS.md FR-06 AC1 : key uniqueness requirement
    """
    canonical = text + "\x00" + voice + "\x00" + str(round(speed, 2))
    sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"tts:cache:{sha}"


class RedisCache:
    """Thin wrapper around a redis client with graceful fallback.

    [FR-06]
    If the redis package is absent or the connection drops, every operation
    degrades to a no-op and ``is_available()`` returns False so the caller
    falls back to the backend without an exception.

    Citations:
      - SPEC.md L88-L89  : optional cache; 24 h TTL; graceful no-Redis
      - SRS.md FR-06 AC2 : SETEX TTL = 86400
      - SRS.md FR-06 AC4 : error → log cache.unavailable + fallback
      - SRS.md FR-06 AC5 : absent redis package → no crash
    """

    def __init__(self, client: object = None) -> None:
        self._client = client
        self._available: bool = client is not None

    def is_available(self) -> bool:
        """Return True only if a client is present AND no error has occurred."""
        return self._client is not None and self._available

    def get(self, key: str) -> bytes | None:
        """Return cached bytes for *key*, or None on miss / error.

        [FR-06]
        On any exception: log {"event": "cache.unavailable", "reason": <exc>}
        at INFO level, mark unavailable, return None.
        """
        if not self.is_available():
            return None
        try:
            return self._client.get(key)  # type: ignore[union-attr]
        except Exception as exc:
            log.info({"event": "cache.unavailable", "reason": str(exc)})
            self._available = False
            return None

    def set(self, key: str, value: bytes, ttl: int = 86400) -> None:
        """Store *value* under *key* with *ttl* seconds expiry.

        [FR-06]
        Uses SETEX so TTL is atomic with the write (SPEC.md L88).
        No-op if unavailable.  On any exception: log + mark unavailable.
        """
        if not self.is_available():
            return
        try:
            self._client.setex(key, ttl, value)  # type: ignore[union-attr]
        except Exception as exc:
            log.info({"event": "cache.unavailable", "reason": str(exc)})
            self._available = False
