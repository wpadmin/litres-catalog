import redis.asyncio as redis
from app.config import settings
from typing import Optional
import json

redis_client: Optional[redis.Redis] = None

async def get_redis() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client

async def cache_get(key: str) -> Optional[str]:
    r = await get_redis()
    return await r.get(key)

async def cache_set(key: str, value: str, ttl: int = 300):
    r = await get_redis()
    await r.setex(key, ttl, value)