from sqlalchemy.ext.asyncio import AsyncEngine
from core.database import metadata

async def reflect_tables(engine: AsyncEngine):
    async with engine.connect() as conn:
        await conn.run_sync(metadata.reflect)
