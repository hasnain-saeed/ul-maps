from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/schema"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

metadata = MetaData()

async def get_async_connection():
    # with block automatically closes the connection
    async with engine.connect() as conn:
        # gives the connection to the endpoint
        yield conn

async def close_db_connections():
    await engine.dispose()
