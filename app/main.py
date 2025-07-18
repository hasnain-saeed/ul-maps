import asyncio
import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import get_settings
from core.database import close_db_connections
from models.base import reflect_tables
from services.kafka_consumer import KafkaConsumerService
from core.cache import close_redis_pool
from core.database import engine
from api.v1.api import api_router

settings = get_settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup: Reflecting database tables...")
    await reflect_tables(engine)

    app.state.consumer_service = KafkaConsumerService()
    app.state.consumer_task = asyncio.create_task(app.state.consumer_service.start())
    logger.info("Application started - Kafka consumer running")

    yield

    await app.state.consumer_service.stop()
    app.state.consumer_task.cancel()
    try:
        await app.state.consumer_task
    except asyncio.CancelledError:
        pass
    logger.info("Application shutdown - Kafka consumer stopped")
    await close_db_connections()
    await close_redis_pool()

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": settings.api_title,
        "description": settings.api_description,
        "endpoints": {
            "/api/v1/stream": "Server-Sent Events stream of transit data",
            "/api/v1/health": "Health check and service status",
            "/api/v1/stats": "Consumer statistics",
            "/api/v1/routes/{route_name}/shape": "Get route shape data"
        },
        "topics": settings.kafka_topics
    }

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run("main_new:app", host="0.0.0.0", port=8000, reload=True)
