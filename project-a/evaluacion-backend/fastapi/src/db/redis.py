import redis.asyncio as aioredis
from src.core.config import settings

async def get_redis():
    try:
        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await client.ping()
        return client
    except Exception:
        return None
