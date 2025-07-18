from pydantic import BaseModel
from typing import List

class VehiclePosition(BaseModel):
    entity_id: str
    vehicle_id: str
    trip_id: str | None
    latitude: float
    longitude: float
    bearing: float | None
    speed: float | None
    timestamp: int
    
    @classmethod
    def from_kafka_to_broadcast_format(cls, kafka_data: dict) -> List[dict]:
        """Transform Kafka message to flattened VehiclePosition dicts"""
        vehicles = []
        for entity in kafka_data.get('entity', []):
            vehicle_data = entity.get('vehicle', {})
            position = vehicle_data.get('position', {})
            vehicle_info = vehicle_data.get('vehicle', {})
            trip_info = vehicle_data.get('trip', {})
            
            vehicle = cls(
                entity_id=entity.get('id'),
                vehicle_id=vehicle_info.get('id'),
                trip_id=trip_info.get('trip_id'),
                latitude=position.get('latitude'),
                longitude=position.get('longitude'),
                bearing=position.get('bearing'),
                speed=position.get('speed'),
                timestamp=vehicle_data.get('timestamp')
            )
            vehicles.append(vehicle.model_dump())
        return vehicles

class TripUpdate(BaseModel):
    entity_id: str
    trip_id: str
    vehicle_id: str
    stop_sequence: int
    stop_id: str
    arrival_delay: int | None
    arrival_time: int | None
    departure_delay: int | None
    departure_time: int | None
    update_timestamp: int
    
    @classmethod
    def from_kafka_to_broadcast_format(cls, kafka_data: dict) -> List[dict]:
        """Transform Kafka message to flattened TripUpdate dicts"""
        updates = []
        for entity in kafka_data.get('entity', []):
            trip_data = entity.get('trip_update', {})
            trip_info = trip_data.get('trip', {})
            vehicle_info = trip_data.get('vehicle', {})
            timestamp = trip_data.get('timestamp')
            
            for stop_update in trip_data.get('stop_time_update', []):
                arrival = stop_update.get('arrival', {})
                departure = stop_update.get('departure', {})
                
                update = cls(
                    entity_id=entity.get('id'),
                    trip_id=trip_info.get('trip_id'),
                    vehicle_id=vehicle_info.get('id'),
                    stop_sequence=stop_update.get('stop_sequence'),
                    stop_id=stop_update.get('stop_id'),
                    arrival_delay=arrival.get('delay'),
                    arrival_time=arrival.get('time'),
                    departure_delay=departure.get('delay'),
                    departure_time=departure.get('time'),
                    update_timestamp=timestamp
                )
                updates.append(update.model_dump())
        return updates
