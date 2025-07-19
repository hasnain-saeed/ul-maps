export interface BaseMessage {
  type: string;
  timestamp: number;
}

export interface VehiclePositionsMessage extends BaseMessage {
  type: 'vehicle_positions';
  data: VehiclePosition[];
}

export interface TripUpdatesMessage extends BaseMessage {
  type: 'trip_updates';
  data: TripUpdate[];
}

export type StreamMessage = VehiclePositionsMessage | TripUpdatesMessage;

export interface VehiclePosition {
  entity_id: string;
  vehicle_id: string;
  trip_id: string | null;
  latitude: number;
  longitude: number;
  bearing: number | null;
  speed: number | null;
  timestamp: number;
}

export interface TripUpdate {
  trip_id: string;
  route_id: string;
  vehicle_id?: string;
  delay: number;
  stop_updates: StopUpdate[];
}

export interface StopUpdate {
  stop_id: string;
  arrival_delay?: number;
  departure_delay?: number;
  sequence: number;
}