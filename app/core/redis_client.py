from functools import lru_cache
from redis.asyncio import Redis
from app.core.settings import settings

_redis: Redis | None = None


@lru_cache
def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis
