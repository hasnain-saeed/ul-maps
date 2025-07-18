from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine
from .config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow
)

metadata = MetaData()

async def get_async_connection():
    async with engine.connect() as conn:
        yield conn

async def close_db_connections():
    await engine.dispose()