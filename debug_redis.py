import sys
sys.path.insert(0, '03-development')
from src.cache.redis_cache import RedisCache
from unittest.mock import MagicMock
import logging

logging.basicConfig(level=logging.INFO)
mock_client = MagicMock()
mock_client.get.return_value = b"test"
cache = RedisCache(client=mock_client)
print("Available:", cache.is_available())
res = cache.get("key")
print("Result:", res)
print("Call count:", mock_client.get.call_count)
