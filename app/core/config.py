from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""

    # Database settings
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/schema"

    # Redis settings
    redis_url: str = "redis://localhost:6379"

    # Kafka settings
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topics: list[str] = ["gtfs_vehicle_positions", "gtfs_trip_updates"]

    # API settings
    api_title: str = "Transit Real-time Data Streaming API"
    api_description: str = "Streams processed transit data via Server-Sent Events from Kafka topics"
    api_version: str = "1.0.0"

    # CORS settings
    cors_origins: list[str] = ["http://localhost:5173"]

    # Database connection pool settings
    db_pool_size: int = 10
    db_max_overflow: int = 20

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()
