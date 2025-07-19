export interface Route {
  id: string;
  name: string;
  description?: string;
  color?: string;
  type: 'bus' | 'train' | 'tram' | 'subway';
  agency_id: string;
}

export interface RouteStop {
  stop_id: string;
  sequence: number;
  arrival_time?: string;
  departure_time?: string;
}

export interface RouteShape {
  id: string;
  route_id: string;
  coordinates: [number, number][];
}