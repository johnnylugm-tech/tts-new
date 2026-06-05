"""Supplementary tests to reach 100% coverage on lines not hit by FR tests.

These tests cover the defensive/error-path code that the FR-scoped tests
don't exercise: Redis unavailable fallback, empty-chunks guard, and CLI
no-op fallthrough.
"""
from __future__ import annotations

import asyncio
import pytest

try:
    from src.cache.redis_cache import RedisCache
    from src.engines.synthesis import synthesize_chunks
    from src.cli import main
    _IMPORTED = True
except ImportError:
    _IMPORTED = False

pytestmark = pytest.mark.skipif(not _IMPORTED, reason="modules not yet implemented")


# ── RedisCache unavailable paths ──────────────────────────────────────────────

def test_redis_cache_get_returns_none_when_unavailable():
    cache = RedisCache(client=None)
    assert cache.get("any-key") is None


def test_redis_cache_set_noop_when_unavailable():
    cache = RedisCache(client=None)
    # Must not raise; must silently do nothing
    cache.set("any-key", b"data")


def test_redis_cache_set_exception_marks_unavailable():
    class _FailingClient:
        def get(self, key):
            return None

        def setex(self, key, ttl, value):
            raise OSError("redis connection lost")

    cache = RedisCache(client=_FailingClient())
    assert cache.is_available()
    cache.set("key", b"value")
    assert not cache.is_available()


# ── synthesize_chunks empty guard ─────────────────────────────────────────────

def test_synthesize_chunks_raises_on_empty():
    with pytest.raises(ValueError, match="non-empty"):
        asyncio.run(synthesize_chunks([], voice="zf_xiaoxiao", speed=1.0, fmt="mp3"))


# ── CLI no-op fallthrough ──────────────────────────────────────────────────────

def test_cli_main_no_text_no_file_returns_0():
    # No --text and no --input-file → main falls through to return 0
    result = main(argv=["tts-v610", "--output", "/tmp/unused_out.mp3"])
    assert result == 0
