from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import asyncio
import json
from typing import AsyncGenerator
import uvicorn
import logging

from consumer import KafkaConsumerService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global consumer service instance
consumer_service: KafkaConsumerService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_service
    consumer_service = KafkaConsumerService()
    consumer_task = asyncio.create_task(consumer_service.start())
    logger.info("Application started - Kafka consumer running")
    yield
    await consumer_service.stop()
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
    logger.info("Application shutdown - Kafka consumer stopped")

app = FastAPI(
    title="Transit Real-time Data Streaming API",
    description="Streams processed transit data via Server-Sent Events from Kafka topics",
    version="1.0.0",
    lifespan=lifespan
)

async def event_stream() -> AsyncGenerator[str, None]:
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

@app.get("/stream")
async def stream_events():
    """Stream real-time transit data via Server-Sent Events"""
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "consumer_running": consumer_service.running if consumer_service else False,
        "connected_clients": len(consumer_service.clients) if consumer_service else 0,
        "topics": ["gtfs_vehicle_positions", "gtfs_trip_updates"]
    }

@app.get("/stats")
async def get_stats():
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