import redis.asyncio as redis
from app.config import settings
from typing import Optional
import json

redis_client: Optional[redis.Redis] = None
redis_available: bool = True

async def get_redis() -> redis.Redis:
    global redis_client, redis_available

    if not redis_available:
        raise ConnectionError("Redis is not available")

    if redis_client is None:
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1
        )
        try:
            await redis_client.ping()
        except Exception:
            redis_available = False
            redis_client = None
            raise

    return redis_client

async def cache_get(key: str) -> Optional[str]:
    try:
        r = await get_redis()
        return await r.get(key)
    except Exception:
        return None

async def cache_set(key: str, value: str, ttl: int = 300):
    try:
        r = await get_redis()
        await r.setex(key, ttl, value)
    except Exception:
        pass