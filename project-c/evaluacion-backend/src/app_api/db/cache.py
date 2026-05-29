from typing import Optional
from redis.asyncio import Redis

redis_client: Optional[Redis] = None

async def get_redis() -> Redis:
    return redis_client