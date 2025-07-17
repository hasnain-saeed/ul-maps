import asyncio
import json
import logging
import os
from typing import Dict, Any, Set
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from schemas import VehiclePosition, TripUpdate
from cache import redis_pool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaConsumerService:
    def __init__(self):
        self.consumer = None
        self.topics = ['gtfs_vehicle_positions', 'gtfs_trip_updates']
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

        # Create list to avoid modification during iteration
        clients_to_remove = []

        for client_queue in self.clients.copy():
            try:
                await asyncio.wait_for(client_queue.put(message), timeout=0.1)
            except (asyncio.TimeoutError, asyncio.QueueFull):
                # Client queue is full or slow, remove it
                clients_to_remove.append(client_queue)
                logger.warning("Removing slow/full client queue")
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                clients_to_remove.append(client_queue)

        # Remove problematic clients
        for client_queue in clients_to_remove:
            self.remove_client(client_queue)

    async def start(self):
        """Start the Kafka consumer"""
        try:
            # Get Kafka bootstrap servers from environment or default to localhost
            bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

            self.consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=bootstrap_servers,
                group_id='transit_streaming_group',
                auto_offset_reset='latest',
                enable_auto_commit=True,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else None
            )

            await self.consumer.start()
            self.running = True
            logger.info(f"Started consuming from topics: {self.topics}")

            await self._consume_loop()

        except Exception as e:
            logger.error(f"Error starting consumer: {e}")
        finally:
            await self.stop()

    async def _consume_loop(self):
        """Main consumption loop"""
        try:
            async for message in self.consumer:
                if not self.running:
                    break

                try:
                    processed_data = await self._process_message(message)
                    if processed_data:
                        await self._cache_latest_data(processed_data)
                        await self.broadcast_message(processed_data)

                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except KafkaError as e:
            logger.error(f"Kafka error: {e}")

    async def _cache_latest_data(self, processed_data: Dict[str, Any]):
        """Cache the latest vehicle positions and trip updates in Redis"""
        try:
            data_type = processed_data.get('type')
            
            if data_type == 'vehicle_positions':
                await redis_pool.set("latest_vehicle_positions", json.dumps(processed_data))
            
            elif data_type == 'trip_updates':
                await redis_pool.set("latest_trip_updates", json.dumps(processed_data))
                
        except Exception as e:
            logger.error(f"Error caching data: {e}")

    async def _process_message(self, message) -> Dict[str, Any]:
        """Process Kafka message and return formatted data"""
        try:
            topic = message.topic
            value = message.value
            timestamp = message.timestamp or asyncio.get_event_loop().time() * 1000

            if not value:
                return None

            base_data = {
                'topic': topic,
                'kafka_timestamp': timestamp,
                'processed_at': asyncio.get_event_loop().time() * 1000
            }

            if topic == 'gtfs_vehicle_positions':
                try:
                    # Parse GTFS vehicle position entity
                    entities = value.get('entity', [])
                    processed_vehicles = []

                    for entity in entities:
                        if 'vehicle' in entity:
                            vehicle_data = entity['vehicle']
                            position = vehicle_data.get('position', {})
                            vehicle_info = vehicle_data.get('vehicle', {})
                            trip_info = vehicle_data.get('trip', {})

                            vehicle_pos = VehiclePosition(
                                entity_id=entity['id'],
                                vehicle_id=vehicle_info.get('id', ''),
                                trip_id=trip_info.get('trip_id'),
                                latitude=position.get('latitude'),
                                longitude=position.get('longitude'),
                                bearing=position.get('bearing'),
                                speed=position.get('speed'),
                                timestamp=vehicle_data.get('timestamp')
                            )
                            processed_vehicles.append(vehicle_pos.model_dump())

                    return {
                        **base_data,
                        'type': 'vehicle_positions',
                        'data': processed_vehicles
                    }
                except Exception as e:
                    logger.warning(f"Invalid vehicle position data: {e}")
                    return None

            elif topic == 'gtfs_trip_updates':
                try:
                    # Parse GTFS trip update entity
                    entities = value.get('entity', [])
                    processed_updates = []

                    for entity in entities:
                        if 'trip_update' in entity:
                            trip_update = entity['trip_update']
                            trip_info = trip_update.get('trip', {})
                            vehicle_info = trip_update.get('vehicle', {})
                            stop_updates = trip_update.get('stop_time_update', [])

                            for stop_update in stop_updates:
                                arrival = stop_update.get('arrival', {})
                                departure = stop_update.get('departure', {})

                                update = TripUpdate(
                                    entity_id=entity['id'],
                                    trip_id=trip_info.get('trip_id', ''),
                                    vehicle_id=vehicle_info.get('id', ''),
                                    stop_sequence=stop_update.get('stop_sequence'),
                                    stop_id=stop_update.get('stop_id'),
                                    arrival_delay=arrival.get('delay'),
                                    arrival_time=arrival.get('time'),
                                    departure_delay=departure.get('delay'),
                                    departure_time=departure.get('time'),
                                    update_timestamp=trip_update.get('timestamp')
                                )
                                processed_updates.append(update.model_dump())

                    return {
                        **base_data,
                        'type': 'trip_updates',
                        'data': processed_updates
                    }
                except Exception as e:
                    logger.warning(f"Invalid trip update data: {e}")
                    return None
            else:
                # Handle unknown topics
                return {
                    **base_data,
                    'type': 'raw',
                    'data': value
                }

        except Exception as e:
            logger.error(f"Error in _process_message: {e}")
            return None

    async def stop(self):
        """Stop the consumer"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")
