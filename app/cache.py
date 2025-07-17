import redis.asyncio as redis
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/1"
)

redis_pool = redis.from_url(
    REDIS_URL,
    encoding="utf-8",
    decode_responses=True
)

async def get_redis():
    yield redis_pool

async def close_redis_pool():
    await redis_pool.close()
