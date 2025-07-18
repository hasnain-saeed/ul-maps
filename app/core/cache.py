import redis.asyncio as redis
from .config import get_settings

settings = get_settings()

redis_pool = redis.from_url(settings.redis_url, decode_responses=True)

def get_redis():
    return redis_pool

async def close_redis_pool():
    await redis_pool.close()
