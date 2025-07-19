export interface Stop {
  id: string;
  name: string;
  description?: string;
  latitude: number;
  longitude: number;
  zone_id?: string;
  stop_code?: string;
  wheelchair_accessible?: boolean;
}

export interface StopTime {
  trip_id: string;
  stop_id: string;
  arrival_time: string;
  departure_time: string;
  stop_sequence: number;
}