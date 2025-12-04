from cachetools import TTLCache
from src.utils.hashing import sha256_bytes
from datetime import datetime

cache = TTLCache(maxsize=200, ttl=3600)  # 1 hour cache


def get_cache(image_bytes: bytes):
    key = sha256_bytes(image_bytes)
    return cache.get(key)


def set_cache(image_bytes: bytes, result: dict):
    key = sha256_bytes(image_bytes)
    result_with_meta = {
        **result,
        "_cached_at": datetime.utcnow().isoformat()
    }
    cache[key] = result_with_meta
