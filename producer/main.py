import asyncio
import json
import logging
import os
import time
from typing import Dict, Any, List
import aiohttp
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from google.transit import gtfs_realtime_pb2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GTFSRealtimeProducer:
    def __init__(self):
        # Environment variables
        self.api_key = os.getenv('REALTIME_API_KEY', '')
        self.feed_url = os.getenv('FEED_URL', '')
        self.kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9093')
        self.poll_interval = int(os.getenv('POLL_INTERVAL', '10'))  # seconds

        # Kafka topics
        self.vehicle_positions_topic = 'gtfs_vehicle_positions'
        self.trip_updates_topic = 'gtfs_trip_updates'

        # URLs
        self.vehicle_positions_url = f'{self.feed_url}/VehiclePositions.pb'
        self.trip_updates_url = f'{self.feed_url}/TripUpdates.pb'

        # Kafka producer
        self.producer = None

        # HTTP session
        self.session = None

        # Running state
        self.running = False

        logger.info(f"Initialized GTFS-RT Producer")
        logger.info(f"Vehicle Positions URL: {self.vehicle_positions_url}")
        logger.info(f"Trip Updates URL: {self.trip_updates_url}")
        logger.info(f"Kafka Servers: {self.kafka_servers}")
        logger.info(f"Poll Interval: {self.poll_interval}s")

    async def start(self):
        """Start the producer service"""
        try:
            # Initialize Kafka producer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.kafka_servers,
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                compression_type='gzip',
                max_batch_size=16384,
                linger_ms=10  # Small delay to batch messages
            )

            # Initialize HTTP session
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)

            await self.producer.start()
            self.running = True

            logger.info("GTFS-RT Producer started successfully")

            # Start the main loop
            await self._run_loop()

        except Exception as e:
            logger.error(f"Error starting producer: {e}")
            raise
        finally:
            await self.stop()

    async def stop(self):
        """Stop the producer service"""
        self.running = False

        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")

        if self.session:
            await self.session.close()
            logger.info("HTTP session closed")

    async def _run_loop(self):
        """Main execution loop"""
        logger.info("Starting continuous data fetching loop")

        while self.running:
            loop_start = time.time()

            try:
                # Fetch both feeds concurrently
                tasks = [
                    self._fetch_and_produce_vehicle_positions(),
                    self._fetch_and_produce_trip_updates()
                ]

                await asyncio.gather(*tasks, return_exceptions=True)

                # Calculate sleep time to maintain consistent intervals
                loop_duration = time.time() - loop_start
                sleep_time = max(0, self.poll_interval - loop_duration)

                if sleep_time > 0:
                    logger.debug(f"Loop took {loop_duration:.2f}s, sleeping {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
                else:
                    logger.warning(f"Loop took {loop_duration:.2f}s, longer than interval {self.poll_interval}s")

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(self.poll_interval)

    async def _fetch_gtfs_feed(self, url: str) -> gtfs_realtime_pb2.FeedMessage:
        """Fetch and decode GTFS-RT feed"""
        params = {"key": self.api_key} if self.api_key else {}

        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            content = await response.read()

            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(content)
            return feed

    async def _fetch_and_produce_vehicle_positions(self):
        """Fetch vehicle positions and send to Kafka"""
        try:
            feed = await self._fetch_gtfs_feed(self.vehicle_positions_url)
            entities = []

            for entity in feed.entity:
                if entity.HasField("vehicle"):
                    v = entity.vehicle
                    entity_dict = {
                        "id": entity.id,
                        "vehicle": {
                            "timestamp": v.timestamp if v.HasField("timestamp") else int(time.time())
                        }
                    }

                    # Position data
                    if v.HasField("position"):
                        entity_dict["vehicle"]["position"] = {
                            "latitude": v.position.latitude,
                            "longitude": v.position.longitude,
                            "bearing": v.position.bearing if v.position.HasField("bearing") else None,
                            "speed": v.position.speed if v.position.HasField("speed") else None
                        }

                    # Vehicle info
                    if v.HasField("vehicle"):
                        entity_dict["vehicle"]["vehicle"] = {"id": v.vehicle.id}

                    # Trip info
                    if v.HasField("trip"):
                        entity_dict["vehicle"]["trip"] = {
                            "trip_id": v.trip.trip_id,
                            "schedule_relationship": v.trip.schedule_relationship if v.trip.HasField("schedule_relationship") else None
                        }

                    entities.append(entity_dict)

            if entities:
                payload = {"entity": entities}
                await self.producer.send(self.vehicle_positions_topic, payload)
                logger.info(f"Sent {len(entities)} vehicle positions to Kafka")
            else:
                logger.debug("No vehicle positions found")

        except Exception as e:
            logger.error(f"Error fetching vehicle positions: {e}")

    async def _fetch_and_produce_trip_updates(self):
        """Fetch trip updates and send to Kafka"""
        try:
            feed = await self._fetch_gtfs_feed(self.trip_updates_url)
            entities = []

            for entity in feed.entity:
                if entity.HasField("trip_update"):
                    tu = entity.trip_update
                    entity_dict = {
                        "id": entity.id,
                        "trip_update": {
                            "timestamp": tu.timestamp if tu.HasField("timestamp") else int(time.time())
                        }
                    }

                    # Trip info
                    if tu.HasField("trip"):
                        entity_dict["trip_update"]["trip"] = {
                            "trip_id": tu.trip.trip_id,
                            "start_date": tu.trip.start_date if tu.trip.HasField("start_date") else None,
                            "schedule_relationship": tu.trip.schedule_relationship if tu.trip.HasField("schedule_relationship") else None
                        }

                    # Vehicle info
                    if tu.HasField("vehicle"):
                        entity_dict["trip_update"]["vehicle"] = {"id": tu.vehicle.id}

                    # Stop time updates
                    stop_time_updates = []
                    for stu in tu.stop_time_update:
                        stop_update = {
                            "stop_sequence": stu.stop_sequence,
                            "stop_id": stu.stop_id
                        }

                        if stu.HasField("arrival"):
                            stop_update["arrival"] = {
                                "delay": stu.arrival.delay if stu.arrival.HasField("delay") else None,
                                "time": stu.arrival.time if stu.arrival.HasField("time") else None,
                                "uncertainty": stu.arrival.uncertainty if stu.arrival.HasField("uncertainty") else None
                            }

                        if stu.HasField("departure"):
                            stop_update["departure"] = {
                                "delay": stu.departure.delay if stu.departure.HasField("delay") else None,
                                "time": stu.departure.time if stu.departure.HasField("time") else None,
                                "uncertainty": stu.departure.uncertainty if stu.departure.HasField("uncertainty") else None
                            }

                        stop_time_updates.append(stop_update)

                    entity_dict["trip_update"]["stop_time_update"] = stop_time_updates
                    entities.append(entity_dict)

            if entities:
                payload = {"entity": entities}
                await self.producer.send(self.trip_updates_topic, payload)
                logger.info(f"Sent {len(entities)} trip updates to Kafka")
            else:
                logger.debug("No trip updates found")

        except Exception as e:
            logger.error(f"Error fetching trip updates: {e}")

async def main():
    """Main entry point"""
    producer = GTFSRealtimeProducer()

    try:
        await producer.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(main())
