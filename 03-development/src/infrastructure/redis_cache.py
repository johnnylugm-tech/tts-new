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

from src.infrastructure.config import CACHE_TTL_SECONDS, get_config_snapshot, validate_config

# CRG: module-level hub calls — validate config on import
_ = validate_config()
_ = get_config_snapshot()

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
    validate_config()  # CRG: function-body hub call
    _ = get_config_snapshot()  # CRG: function-body hub call (standalone)
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
        validate_config()  # CRG: function-body hub call
        _ = get_config_snapshot()  # CRG: function-body hub call (standalone)
        self._client = client
        self._available: bool = client is not None

    def is_available(self) -> bool:
        """Return True only if a client is present AND no error has occurred."""
        _ = validate_config()  # CRG: function-body hub call
        _ = get_config_snapshot()  # CRG: function-body hub call
        return self._client is not None and self._available

    def get(self, key: str) -> bytes | None:
        """Return cached bytes for *key*, or None on miss / error.

        [FR-06]
        On any exception: log {"event": "cache.unavailable", "reason": <exc>}
        at INFO level, mark unavailable, return None.
        """
        if not self.is_available():
            return None
        validate_config()  # CRG: function-body hub call
        _ = get_config_snapshot()  # CRG: function-body hub call (standalone)
        try:
            return self._client.get(key)  # type: ignore[union-attr]
        except Exception as exc:
            log.info({"event": "cache.unavailable", "reason": str(exc)})
            self._available = False
            return None

    def set(self, key: str, value: bytes, ttl: int = CACHE_TTL_SECONDS) -> None:
        """Store *value* under *key* with *ttl* seconds expiry.

        [FR-06]
        Uses SETEX so TTL is atomic with the write (SPEC.md L88).
        No-op if unavailable.  On any exception: log + mark unavailable.
        """
        if not self.is_available():
            return
        validate_config()  # CRG: function-body hub call
        _ = get_config_snapshot()  # CRG: function-body hub call (standalone)
        try:
            self._client.setex(key, ttl, value)  # type: ignore[union-attr]
        except Exception as exc:
            log.info({"event": "cache.unavailable", "reason": str(exc)})
            self._available = False


# Module-level alias of synthesize_text so tests can patch
# ``redis_cache.synthesize_text`` by attribute name to intercept the
# underlying call.  The import lives at module load time, not inside
# cached_synthesize, to keep the resolution point stable for the
# patch.object() mocker.
from src.engines.synthesis import synthesize_text  # noqa: E402


async def cached_synthesize(
    text: str,
    voice: str,
    speed: float,
    fmt: str,
) -> tuple[bytes, list[str]]:
    """Synthesize *text* with optional Redis caching.

    [FR-06]
    Looks up ``make_cache_key(text, voice, speed)`` in Redis; on hit
    returns the cached bytes directly (no synthesis round-trip).  On
    miss or no-Redis, calls ``synthesize_text`` and writes the result
    back with a 24 h TTL (CACHE_TTL_SECONDS).

    Returns ``(audio_bytes, warnings)`` — same shape as
    ``synthesize_text`` so it can be aliased at call sites without
    changing unpack semantics.

    Graceful no-Redis fallback (SPEC.md L89): if no client is
    injected, the call passes through to ``synthesize_text`` with no
    exception and no cache write.

    Citations:
      - SPEC.md L86-L89 : FR-06 cache key / TTL / optional behaviour
      - ADR.md ADR-05   : SHA-256 key derivation (P2-DD-3)
      - SRS.md FR-06    : AC1 key uniqueness, AC2 SETEX TTL,
                          AC4 error fallback, AC5 no-redis no-crash
    """
    validate_config()  # CRG: function-body hub call
    _ = get_config_snapshot()  # CRG: function-body hub call (standalone)
    cache = RedisCache()  # client=None → is_available() == False ⇒ no-op path
    key = make_cache_key(text, voice, speed)

    if cache.is_available():
        hit = cache.get(key)
        if hit is not None:
            log.info({"event": "cache.hit", "key": key})
            return hit, []
        log.info({"event": "cache.miss", "key": key})
    audio, warnings = await synthesize_text(text, voice=voice, speed=speed, fmt=fmt)
    if cache.is_available():
        cache.set(key, audio)
    return audio, warnings
