from pydantic import BaseModel, ConfigDict

# Base configuration for all schemas
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class Agency(BaseSchema):
    agency_id: str
    agency_name: str
    agency_url: str
    agency_timezone: str
    agency_lang: str | None
    agency_fare_url: str | None

class Calendar(BaseSchema):
    service_id: str
    monday: int
    tuesday: int
    wednesday: int
    thursday: int
    friday: int
    saturday: int
    sunday: int
    start_date: str
    end_date: str

class CalendarDate(BaseSchema):
    service_id: str
    date: str
    exception_type: int

class Stop(BaseSchema):
    stop_id: str
    stop_name: str
    stop_lat: float | None
    stop_lon: float | None
    location_type: int | None
    parent_station: str | None
    platform_code: str | None

class Shape(BaseSchema):
    shape_id: str
    shape_pt_lat: float
    shape_pt_lon: float
    shape_pt_sequence: int
    shape_dist_traveled: float | None

class RouteShape(BaseSchema):
    direction_id: int | None
    shape_id: str
    coordinates: list[list[float]]

class FeedInfo(BaseSchema):
    feed_id: str | None
    feed_publisher_name: str
    feed_publisher_url: str
    feed_lang: str
    feed_version: str | None

class Attribution(BaseSchema):
    trip_id: str | None
    organization_name: str
    is_operator: int | None

class BookingRule(BaseSchema):
    booking_rule_id: str
    booking_type: int | None
    prior_notice_duration_min: int | None
    prior_notice_last_day: int | None
    prior_notice_last_time: str | None
    message: str | None
    phone_number: str | None

class Route(BaseSchema):
    route_id: str
    agency_id: str
    route_short_name: str | None
    route_long_name: str | None
    route_type: int
    route_desc: str | None

class Trip(BaseSchema):
    route_id: str
    service_id: str
    trip_id: str
    trip_headsign: str | None
    direction_id: int | None
    shape_id: str | None

class StopTime(BaseSchema):
    trip_id: str
    arrival_time: str
    departure_time: str
    stop_id: str
    stop_sequence: int
    stop_headsign: str | None
    pickup_type: int | None
    drop_off_type: int | None
    shape_dist_traveled: float | None
    timepoint: int | None
    pickup_booking_rule_id: str | None
    drop_off_booking_rule_id: str | None

class VehiclePosition(BaseModel):
    entity_id: str
    vehicle_id: str
    trip_id: str | None
    latitude: float
    longitude: float
    bearing: float | None
    speed: float | None
    timestamp: int

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
