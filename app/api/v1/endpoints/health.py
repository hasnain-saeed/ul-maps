import asyncio
from fastapi import APIRouter, Depends
from api.deps import get_consumer_service
from services.kafka_consumer import KafkaConsumerService

router = APIRouter()

@router.get("/stats")
async def get_stats(consumer_service: KafkaConsumerService = Depends(get_consumer_service)):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "consumer_running": consumer_service.running if consumer_service else False,
        "connected_clients": len(consumer_service.clients) if consumer_service else 0,
        "topics": consumer_service.topics if consumer_service else [],
        "timestamp": asyncio.get_event_loop().time() * 1000
    }
