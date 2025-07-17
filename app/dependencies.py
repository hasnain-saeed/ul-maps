from fastapi import Request
from consumer import KafkaConsumerService

def get_consumer_service(request: Request) -> KafkaConsumerService:
    return request.app.state.consumer_service
