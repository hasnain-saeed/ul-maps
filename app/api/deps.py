from fastapi import Request
from services.kafka_consumer import KafkaConsumerService
from core.cache import get_redis

def get_consumer_service(request: Request) -> KafkaConsumerService:
    return request.app.state.consumer_service

def get_redis_dependency():
    return get_redis()
