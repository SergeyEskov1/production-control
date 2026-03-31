import json
import redis.asyncio as redis
from src.core.config import settings

redis_client = redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)


async def get_cache(key: str):
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception:
        return None


async def set_cache(key: str, value, ttl: int = 60) -> None:
    try:
        await redis_client.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


async def delete_cache(key: str) -> None:
    try:
        await redis_client.delete(key)
    except Exception:
        pass


async def delete_pattern(pattern: str) -> None:
    try:
        async for key in redis_client.scan_iter(pattern):
            await redis_client.delete(key)
    except Exception:
        pass
