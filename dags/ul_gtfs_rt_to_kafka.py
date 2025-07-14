from airflow.sdk import DAG
from airflow.providers.apache.kafka.operators.produce import ProduceToTopicOperator
from airflow.sdk import Variable
from datetime import datetime
import requests, json, time
from google.transit import gtfs_realtime_pb2

# Airflow Variables
API_KEY    = Variable.get("REALTIME_API_KEY", default_var=None)
FEED_URL   = Variable.get("FEED_URL")

# Construct endpoint URLs
VEHICLE_POSITIONS_URL = f"{FEED_URL.rstrip('/')}/VehiclePositions.pb"
TRIP_UPDATES_URL      = f"{FEED_URL.rstrip('/')}/TripUpdates.pb"

# Kafka topics
VEHICLE_POSITIONS_TOPIC = "gtfs_vehicle_positions"
TRIP_UPDATES_TOPIC      = "gtfs_trip_updates"

def fetch_and_decode_feed(url):
    """Fetch and decode GTFS-RT feed"""
    params = {"key": API_KEY} if API_KEY else {}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)
    return feed

def produce_vehicle_positions():
    """Producer function for vehicle positions"""
    feed = fetch_and_decode_feed(VEHICLE_POSITIONS_URL)

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

    # Yield single message with all entities
    if entities:
        payload = {"entity": entities}
        yield ("vehicle_positions", json.dumps(payload))

def produce_trip_updates():
    """Producer function for trip updates"""
    feed = fetch_and_decode_feed(TRIP_UPDATES_URL)

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

    # Yield single message with all entities
    if entities:
        payload = {"entity": entities}
        yield ("trip_updates", json.dumps(payload))

with DAG(
    dag_id="ul_gtfs_rt_to_kafka",
    schedule="*/1 * * * *",  # Every minute
    start_date=datetime(2025, 7, 12),
    catchup=False,
    tags=["gtfs-rt", "kafka", "ul"],
    description="Produces GTFS-RT data from UL to Kafka topics"
) as dag:

    # Vehicle positions task
    vehicle_positions_task = ProduceToTopicOperator(
        task_id="produce_vehicle_positions",
        kafka_config_id="kafka_default",
        topic=VEHICLE_POSITIONS_TOPIC,
        producer_function=produce_vehicle_positions,
        synchronous=True,
        poll_timeout=1.0,
    )

    # Trip updates task
    trip_updates_task = ProduceToTopicOperator(
        task_id="produce_trip_updates",
        kafka_config_id="kafka_default",
        topic=TRIP_UPDATES_TOPIC,
        producer_function=produce_trip_updates,
        synchronous=True,
        poll_timeout=1.0,
    )

    # Run both tasks in parallel
    [vehicle_positions_task, trip_updates_task]
