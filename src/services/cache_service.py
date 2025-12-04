from cachetools import TTLCache
from src.utils.hashing import sha256_bytes
from datetime import datetime, timezone
from src.config import settings

cache = TTLCache(maxsize=settings.CACHE_MAXSIZE, ttl=settings.CACHE_TTL)


def get_cache(image_bytes: bytes):
    key = sha256_bytes(image_bytes)
    return cache.get(key)


def set_cache(image_bytes: bytes, result: dict):
    key = sha256_bytes(image_bytes)
    result_with_meta = {**result, "_cached_at": datetime.now(timezone.utc).isoformat()}
    cache[key] = result_with_meta
