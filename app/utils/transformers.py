import itertools
import operator
from typing import List, Dict, Any
from schemas.gtfs import RouteShape

def transform_points_to_routes(points) -> list[RouteShape]:
    aggregated_list = []

    for shape_id, group_iterator in itertools.groupby(points, key=operator.attrgetter('shape_id')):
        points_in_group = list(group_iterator)
        first_point = points_in_group[0]

        coords = [[p.shape_pt_lon, p.shape_pt_lat] for p in points_in_group]
        aggregated_list.append(
            RouteShape(
                direction_id=first_point.direction_id,
                shape_id=shape_id,
                coordinates=coords
            )
        )

    return aggregated_list


def transform_vehicle_positions_from_kafka(kafka_data: dict) -> List[Dict[str, Any]]:
    """Transform Kafka vehicle position message to flattened format"""
    vehicles = []
    for entity in kafka_data.get('entity', []):
        vehicle_data = entity.get('vehicle', {})
        position = vehicle_data.get('position', {})
        vehicle_info = vehicle_data.get('vehicle', {})
        trip_info = vehicle_data.get('trip', {})
        
        vehicle_dict = {
            'entity_id': entity.get('id'),
            'vehicle_id': vehicle_info.get('id'),
            'trip_id': trip_info.get('trip_id'),
            'latitude': position.get('latitude'),
            'longitude': position.get('longitude'),
            'bearing': position.get('bearing'),
            'speed': position.get('speed'),
            'timestamp': vehicle_data.get('timestamp')
        }
        vehicles.append(vehicle_dict)
    return vehicles


def transform_trip_updates_from_kafka(kafka_data: dict) -> List[Dict[str, Any]]:
    """Transform Kafka trip update message to flattened format"""
    updates = []
    for entity in kafka_data.get('entity', []):
        trip_data = entity.get('trip_update', {})
        trip_info = trip_data.get('trip', {})
        vehicle_info = trip_data.get('vehicle', {})
        timestamp = trip_data.get('timestamp')
        
        for stop_update in trip_data.get('stop_time_update', []):
            arrival = stop_update.get('arrival', {})
            departure = stop_update.get('departure', {})
            
            update_dict = {
                'entity_id': entity.get('id'),
                'trip_id': trip_info.get('trip_id'),
                'vehicle_id': vehicle_info.get('id'),
                'stop_sequence': stop_update.get('stop_sequence'),
                'stop_id': stop_update.get('stop_id'),
                'arrival_delay': arrival.get('delay'),
                'arrival_time': arrival.get('time'),
                'departure_delay': departure.get('delay'),
                'departure_time': departure.get('time'),
                'update_timestamp': timestamp
            }
            updates.append(update_dict)
    return updates
