from pydantic import BaseModel, Field
from typing import Optional

class VehiclePosition(BaseModel):
    entity_id: str = Field(..., description="Entity ID")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    trip_id: Optional[str] = Field(None, description="Associated trip ID")
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    bearing: Optional[float] = Field(None, description="Bearing in degrees")
    speed: Optional[float] = Field(None, description="Speed in m/s")
    timestamp: int = Field(..., description="Epoch timestamp")

class TripUpdate(BaseModel):
    entity_id: str = Field(..., description="Entity ID from trip update")
    trip_id: str = Field(..., description="Trip ID")
    vehicle_id: str = Field(..., description="Vehicle ID")
    stop_sequence: int = Field(..., description="Sequence index of stop")
    stop_id: str = Field(..., description="Stop identifier")
    arrival_delay: Optional[int] = Field(None, description="Arrival delay in seconds")
    arrival_time: Optional[int] = Field(None, description="Arrival epoch timestamp")
    departure_delay: Optional[int] = Field(None, description="Departure delay in seconds")
    departure_time: Optional[int] = Field(None, description="Departure epoch timestamp")
    update_timestamp: int = Field(..., description="Feed timestamp")
