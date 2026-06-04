"""FR-06: Redis 快取 (Redis cache, optional) — TDD-RED failing tests.

7 parametrized cases for src/cache/redis_cache.py (SPEC.md L198).
Tests fail at collection time (ImportError) — valid RED state.

GREEN TODO: implement src/cache/redis_cache.py with:
  - make_cache_key(text: str, voice: str, speed: float) -> str
      canonical form: text + "\\x00" + voice + "\\x00" + str(round(speed, 2))
      key format: f"tts:cache:{sha256_hex}"
      where sha256_hex = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
      (SPEC.md L87; SAD.md §3.6; ADR.md P2-DD-3, ADR-05)
  - RedisCache class:
      __init__(self, client=None)
          Accept an injected redis client (for testing); if None, is_available()
          returns False. For production, build the client from REDIS_URL env var.
      get(self, key: str) -> bytes | None
          - Call client.get(key); return bytes on hit, None on miss
          - Catch ALL exceptions (incl. redis.exceptions.ConnectionError);
            on error: log {"event": "cache.unavailable", "reason": <exc>}
            at INFO level via stdlib logging, set _available=False, return None
      set(self, key: str, value: bytes, ttl: int = 86400) -> None
          - Call client.setex(key, ttl, value)
            (SETEX = SET + EXpire; TTL = 86400 = 24 h, SPEC.md L88)
          - No-op if client is None or not available
          - Catch ALL exceptions, log at INFO, set _available=False
      is_available(self) -> bool
          Return False if client is None or last operation raised an error.
"""
from __future__ import annotations

import hashlib
import importlib
import logging
import sys
from unittest.mock import MagicMock

import pytest

# NO try/except — collection error (Exit Code 2) is the valid RED state per
# TDD-RED protocol (FORBIDDEN section item 3).
from src.cache.redis_cache import RedisCache, make_cache_key

# ---------------------------------------------------------------------------
# Spec constants & shared fixtures
# ---------------------------------------------------------------------------

_TTL_SECONDS = 86400  # 24 h — SPEC.md L88
_TEXT = "你好"
_VOICE = "zf_xiaoxiao"
_SPEED = 1.0
_AUDIO_BYTES = b"fake_audio_bytes_for_testing"

# Sentinel for sys.modules manipulation (case 7)
_ABSENT = object()


def _expected_key(text: str, voice: str, speed: float) -> str:
    """Reference implementation of make_cache_key for assertion parity."""
    canonical = text + "\x00" + voice + "\x00" + str(round(speed, 2))
    sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"tts:cache:{sha}"


# ---------------------------------------------------------------------------
# 7 parametrize IDs — MUST match TEST_SPEC.md FR-06 table exactly
# ---------------------------------------------------------------------------

_CASE_IDS = [
    "cache_hit_returns_stored_bytes_no_backend_call",
    "cache_miss_returns_None_backend_invoked",
    "SETEX_TTL_equals_86400_on_every_write",
    "ConnectionError_falls_back_to_backend_with_info_log",
    "key_derivation_sha256_canonical_form",
    "different_tuple_different_key",
    "absent_redis_package_does_not_break_startup",
]


@pytest.mark.parametrize("case_id", _CASE_IDS)
def test_fr_06_redis_cache(case_id, caplog):
    """FR-06: Redis cache — 7 cases for key derivation, TTL, hit/miss, and fallback."""

    key = make_cache_key(_TEXT, _VOICE, _SPEED)

    if case_id == "cache_hit_returns_stored_bytes_no_backend_call":
        # AC3: cache hit returns stored bytes; caller skips backend (returns non-None)
        mock_client = MagicMock()
        mock_client.get.return_value = _AUDIO_BYTES
        cache = RedisCache(client=mock_client)

        result = cache.get(key)

        assert result == _AUDIO_BYTES, (
            f"cache hit must return the stored bytes; got {result!r}"
        )
        mock_client.get.assert_called_once_with(key)
        # backend_call_count == 0: the non-None result signals the caller
        # to skip the backend entirely (the test verifies the cache returns
        # the bytes; no backend mock is needed here).

    elif case_id == "cache_miss_returns_None_backend_invoked":
        # AC3: cache miss returns None; caller then invokes the backend
        mock_client = MagicMock()
        mock_client.get.return_value = None  # Redis reports key absent
        cache = RedisCache(client=mock_client)

        result = cache.get(key)

        assert result is None, (
            f"cache miss must return None so the caller knows to invoke the "
            f"backend; got {result!r}"
        )
        mock_client.get.assert_called_once_with(key)

    elif case_id == "SETEX_TTL_equals_86400_on_every_write":
        # AC2: every write uses SETEX with TTL = 86400 s (24 h — SPEC.md L88)
        mock_client = MagicMock()
        cache = RedisCache(client=mock_client)

        cache.set(key, _AUDIO_BYTES)

        # GREEN TODO: set() must call client.setex(key, 86400, value)
        mock_client.setex.assert_called_once_with(key, _TTL_SECONDS, _AUDIO_BYTES)

        # Second write must also use TTL=86400 ("on every write")
        cache.set(key + ":v2", b"second_write")
        assert mock_client.setex.call_count == 2, (
            "set() must call setex on every write, not just the first"
        )
        second_args = mock_client.setex.call_args_list[1]
        assert second_args.args[1] == _TTL_SECONDS or second_args.kwargs.get("time") == _TTL_SECONDS, (
            f"second write TTL must also be {_TTL_SECONDS}; got {second_args}"
        )

    elif case_id == "ConnectionError_falls_back_to_backend_with_info_log":
        # AC4: redis.exceptions.ConnectionError → cache.get() returns None,
        # is_available() == False, info log emitted with event "cache.unavailable"
        mock_client = MagicMock()
        # Raise a generic ConnectionError; GREEN must catch all exceptions
        # including redis.exceptions.ConnectionError (which inherits from Exception)
        mock_client.get.side_effect = ConnectionError("connection refused")
        cache = RedisCache(client=mock_client)

        with caplog.at_level(logging.INFO):
            result = cache.get(key)  # must NOT raise

        assert result is None, (
            "ConnectionError must be caught; get() must return None so the "
            "caller falls back to the backend (SPEC.md L228-L229)"
        )
        assert not cache.is_available(), (
            "after a ConnectionError, is_available() must return False "
            "(AC4-connection-error-fallback)"
        )
        # Log must contain "cache.unavailable" event (P2-DD-5 allow-list)
        all_messages = " ".join(r.getMessage() for r in caplog.records)
        assert "cache.unavailable" in all_messages, (
            f"must log event='cache.unavailable' at INFO level "
            f"(SPEC.md L228-L229); captured log: {all_messages!r}"
        )

    elif case_id == "key_derivation_sha256_canonical_form":
        # AC1: key = f"tts:cache:{sha256_hex}"
        # where canonical form = text + "\x00" + voice + "\x00" + str(round(speed,2))
        expected = _expected_key(_TEXT, _VOICE, _SPEED)
        assert key == expected, (
            f"make_cache_key must produce 'tts:cache:<sha256>'; "
            f"expected {expected!r}, got {key!r}"
        )
        assert key.startswith("tts:cache:"), (
            f"key must have 'tts:cache:' prefix (P2-DD-3); got {key!r}"
        )
        # AC1 sub-assertion: speed rounds to 2 decimals (1.0 == 1.0000001)
        key_rounded = make_cache_key(_TEXT, _VOICE, 1.0000001)
        assert key == key_rounded, (
            "make_cache_key must round speed to 2 decimal places; "
            "make_cache_key(speed=1.0) must equal make_cache_key(speed=1.0000001)"
        )

    elif case_id == "different_tuple_different_key":
        # AC1 / AC2: different (text, voice, speed) tuples → different keys
        key_base = make_cache_key(_TEXT, _VOICE, _SPEED)

        key_diff_voice = make_cache_key(_TEXT, "zf_yunxi", _SPEED)
        assert key_base != key_diff_voice, (
            "different voice must produce a different cache key "
            f"(base={key_base!r}, diff={key_diff_voice!r})"
        )

        key_diff_text = make_cache_key("世界", _VOICE, _SPEED)
        assert key_base != key_diff_text, (
            "different text must produce a different cache key "
            f"(base={key_base!r}, diff={key_diff_text!r})"
        )

        key_diff_speed = make_cache_key(_TEXT, _VOICE, 1.1)
        assert key_base != key_diff_speed, (
            "different speed must produce a different cache key "
            f"(base={key_base!r}, diff={key_diff_speed!r})"
        )

    elif case_id == "absent_redis_package_does_not_break_startup":
        # AC5: absent redis package → is_available() returns False; no crash
        # (SPEC.md L88-L89, L229)
        cache = RedisCache(client=None)
        assert not cache.is_available(), (
            "RedisCache(client=None).is_available() must return False; "
            "the proxy must start without a live Redis connection"
        )

        # Simulate absent redis package: set sys.modules["redis"] = None so
        # any 'import redis' inside the module raises ImportError.
        saved = sys.modules.get("redis", _ABSENT)
        sys.modules["redis"] = None  # type: ignore[assignment]
        try:
            import src.cache.redis_cache as _rcm
            importlib.reload(_rcm)
            _cache2 = _rcm.RedisCache(client=None)
            assert not _cache2.is_available(), (
                "RedisCache(client=None).is_available() must return False "
                "even after the redis package is removed from sys.modules"
            )
        except ImportError as exc:
            pytest.fail(
                "src.cache.redis_cache must NOT raise ImportError when the "
                f"redis package is absent (SPEC.md L229); got: {exc!r}"
            )
        finally:
            if saved is _ABSENT:
                sys.modules.pop("redis", None)
            else:
                sys.modules["redis"] = saved  # type: ignore[assignment]
