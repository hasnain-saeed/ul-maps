import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from api.deps import get_consumer_service, get_redis_dependency
from services.kafka_consumer import KafkaConsumerService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

async def event_stream(consumer_service: KafkaConsumerService) -> AsyncGenerator[str, None]:
    """Generate SSE stream"""
    client_queue = asyncio.Queue(maxsize=100)
    consumer_service.add_client(client_queue)

    try:
        while True:
            try:
                message = await asyncio.wait_for(client_queue.get(), timeout=30.0)
                yield f"data: {json.dumps(message)}\n\n"
                client_queue.task_done()

            except asyncio.TimeoutError:
                heartbeat = {
                    'type': 'heartbeat',
                    'timestamp': asyncio.get_event_loop().time() * 1000,
                    'clients_connected': len(consumer_service.clients)
                }
                yield f"data: {json.dumps(heartbeat)}\n\n"

            except Exception as e:
                error_msg = {
                    'type': 'error',
                    'message': str(e),
                    'timestamp': asyncio.get_event_loop().time() * 1000
                }
                yield f"data: {json.dumps(error_msg)}\n\n"
                break

    except asyncio.CancelledError:
        logger.info("Client stream cancelled")
    except Exception as e:
        logger.error(f"Error in event stream: {e}")
    finally:
        consumer_service.remove_client(client_queue)

@router.get("/vehicle_positions")
async def get_latest_vehicle_positions(cache=Depends(get_redis_dependency)):
    """Get initial data of the vehicle positions before connecting with the stream"""
    try:
        cached_data = await cache.get("latest_vehicle_positions")
        if cached_data:
            return json.loads(cached_data)
        return {"type": "vehicle_positions", "data": []}
    except Exception as e:
        logger.error(f"Error retrieving cached vehicle positions: {e}")
        return {"type": "vehicle_positions", "data": []}

@router.get("/stream")
async def stream_events(consumer_service: KafkaConsumerService = Depends(get_consumer_service)):
    """Stream real-time transit data via Server-Sent Events"""
    return StreamingResponse(
        event_stream(consumer_service),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )
