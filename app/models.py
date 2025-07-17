from sqlalchemy import Table
from sqlalchemy.ext.asyncio import AsyncEngine
from database import engine, metadata

async def reflect_tables(engine: AsyncEngine):
    async with engine.connect() as conn:
        await conn.run_sync(metadata.reflect)
