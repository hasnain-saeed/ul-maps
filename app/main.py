import asyncio
import json
import uvicorn
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncConnection
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import schemas
import crud
from dependencies import get_consumer_service
from consumer import KafkaConsumerService
from cache import close_redis_pool, get_redis
from database import engine, get_async_connection, close_db_connections
from models import reflect_tables

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
    close_db_connections()
    close_redis_pool()

app = FastAPI(
    title="Transit Real-time Data Streaming API",
    description="Streams processed transit data via Server-Sent Events from Kafka topics",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def event_stream(consumer_service: KafkaConsumerService) -> AsyncGenerator[str, None]:
    """Generate SSE stream for individual client"""
    client_queue = asyncio.Queue(maxsize=100)
    consumer_service.add_client(client_queue)

    try:
        while True:
            try:
                # Get message from client-specific queue
                message = await asyncio.wait_for(client_queue.get(), timeout=30.0)
                yield f"data: {json.dumps(message)}\n\n"
                client_queue.task_done()

            except asyncio.TimeoutError:
                # Send heartbeat every 30 seconds
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
        # Clean up client queue
        consumer_service.remove_client(client_queue)

@app.get("/")
async def root():
    return {
        "message": "Transit Real-time Data Streaming API",
        "description": "Consumes from Kafka topics and streams via SSE",
        "endpoints": {
            "/stream": "Server-Sent Events stream of transit data",
            "/health": "Health check and service status",
            "/stats": "Consumer statistics"
        },
        "topics": ["gtfs_vehicle_positions", "gtfs_trip_updates"]
    }

@app.get("/api/vehicle_positions")
async def get_latest_vehicle_positions(cache=Depends(get_redis)):
    """Get initial data of the vehicle positions before connecting with the stream"""
    try:
        cached_data = await cache.get("latest_vehicle_positions")
        if cached_data:
            return json.loads(cached_data)
        return {"type": "vehicle_positions", "data": []}
    except Exception as e:
        logger.error(f"Error retrieving cached vehicle positions: {e}")
        return {"type": "vehicle_positions", "data": []}

@app.get("/api/stream")
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

@app.get(
    "/routes/{route_name}/shape",
    response_model=list[schemas.RouteShape]
)
async def get_route_shape_endpoint(route_name: str, conn: AsyncConnection = Depends(get_async_connection)):
    """
    API endpoint to get the shapes for a given route.
    This endpoint returns a JSON array of shape points.
    """
    validated_shapes = await crud.get_all_shapes_by_route_name(conn, route_name)
    return validated_shapes

@app.get("/health")
async def health_check(consumer_service: KafkaConsumerService = Depends(get_consumer_service)):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "consumer_running": consumer_service.running if consumer_service else False,
        "connected_clients": len(consumer_service.clients) if consumer_service else 0,
        "topics": ["gtfs_vehicle_positions", "gtfs_trip_updates"]
    }

@app.get("/stats")
async def get_stats(consumer_service: KafkaConsumerService = Depends(get_consumer_service)):
    """Get consumer statistics"""
    if not consumer_service:
        return {"error": "Consumer service not initialized"}

    return {
        "consumer_running": consumer_service.running,
        "connected_clients": len(consumer_service.clients),
        "topics_subscribed": consumer_service.topics,
        "timestamp": asyncio.get_event_loop().time() * 1000
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
