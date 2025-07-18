import asyncio
import json
import logging
import os
from typing import Dict, Any, Set
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from utils.transformers import transform_vehicle_positions_from_kafka, transform_trip_updates_from_kafka
from core.cache import redis_pool
from core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

class KafkaConsumerService:
    def __init__(self):
        self.consumer = None
        self.topics = settings.kafka_topics
        self.running = False
        self.clients: Set[asyncio.Queue] = set()

    def add_client(self, client_queue: asyncio.Queue):
        """Add a client queue for broadcasting"""
        self.clients.add(client_queue)
        logger.info(f"Client added. Total clients: {len(self.clients)}")

    def remove_client(self, client_queue: asyncio.Queue):
        """Remove a client queue"""
        self.clients.discard(client_queue)
        logger.info(f"Client removed. Total clients: {len(self.clients)}")

    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.clients:
            return

        clients_to_remove = []

        for client_queue in self.clients.copy():
            try:
                await asyncio.wait_for(client_queue.put(message), timeout=0.1)
            except (asyncio.TimeoutError, asyncio.QueueFull):
                clients_to_remove.append(client_queue)
                logger.warning("Removing slow/full client queue")
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                clients_to_remove.append(client_queue)

        for client_queue in clients_to_remove:
            self.remove_client(client_queue)

    async def start(self):
        """Start the Kafka consumer"""
        try:
            self.consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id="fastapi-consumer-group",
                auto_offset_reset="latest",
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )

            await self.consumer.start()
            self.running = True
            logger.info(f"Kafka consumer started, subscribed to: {self.topics}")

            async for message in self.consumer:
                if not self.running:
                    break

                try:
                    await self.process_message(message)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except Exception as e:
            logger.error(f"Error starting consumer: {e}")
            self.running = False
        finally:
            await self.stop()

    async def process_message(self, message):
        """Process incoming Kafka message"""
        try:
            topic = message.topic
            data = message.value

            if topic == 'gtfs_vehicle_positions':
                await self.handle_vehicle_positions(data)
            elif topic == 'gtfs_trip_updates':
                await self.handle_trip_updates(data)

        except Exception as e:
            logger.error(f"Error processing message from topic {message.topic}: {e}")

    async def handle_vehicle_positions(self, data):
        """Handle vehicle position updates"""
        try:
            # Transform Kafka data to flattened format
            flattened_vehicles = transform_vehicle_positions_from_kafka(data)

            # Store in Redis
            if redis_pool:
                await redis_pool.set(
                    "latest_vehicle_positions",
                    json.dumps(flattened_vehicles),
                    ex=300
                )

            # Broadcast flattened data
            broadcast_message = {
                'type': 'vehicle_positions',
                'data': flattened_vehicles,
                'timestamp': asyncio.get_event_loop().time() * 1000
            }

            await self.broadcast_message(broadcast_message)

        except Exception as e:
            logger.error(f"Error handling vehicle positions: {e}")

    async def handle_trip_updates(self, data):
        """Handle trip update messages"""
        try:
            # Transform Kafka data to flattened format
            flattened_updates = transform_trip_updates_from_kafka(data)

            # Store in Redis
            if redis_pool:
                await redis_pool.set(
                    "latest_trip_updates",
                    json.dumps(flattened_updates),
                    ex=300
                )

            # Broadcast flattened data
            broadcast_message = {
                'type': 'trip_updates',
                'data': flattened_updates,
                'timestamp': asyncio.get_event_loop().time() * 1000
            }

            await self.broadcast_message(broadcast_message)

        except Exception as e:
            logger.error(f"Error handling trip updates: {e}")

    async def stop(self):
        """Stop the Kafka consumer"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")
