import { useState, useEffect } from 'react';

export interface VehiclePosition {
    entity_id: string;
    vehicle_id: string;
    latitude: number;
    longitude: number;
    bearing?: number;
    speed?: number;
    trip_id?: string;
    timestamp: number;
}

export interface TripUpdate {
    entity_id: string;
    delay?: number;
    trip_id: string
    vehicle_id: string
    stop_sequence: number;
    stop_id: string;
    arrival_delay?: number;
    arrival_time?: number;
    departure_delay?: number;
    departure_time?: number;
    update_timestamp: number;
}

type StreamEvent =
  | { type: 'heartbeat' }
  | { type: 'vehicle_positions'; data: VehiclePosition[] }
  | { type: 'trip_updates'; data: TripUpdate[] }
  | { type: 'error'; message: string };

interface UseTransitDataReturn {
  vehiclePositions: Map<string, VehiclePosition>;
  tripUpdates: Map<string, TripUpdate>;
  isConnected: boolean;
  error: string | null;
}

export const useTransitData = (): UseTransitDataReturn => {
  const [vehiclePositions, setVehiclePositions] = useState<Map<string, VehiclePosition>>(new Map());
  const [tripUpdates, setTripUpdates] = useState<Map<string, TripUpdate>>(new Map());
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const eventSource = new EventSource('http://localhost:8000/stream');

    eventSource.onopen = () => {
      console.log('✅ Connected to transit data stream');
      setIsConnected(true);
      setError(null);
    };

    eventSource.onmessage = (event: MessageEvent<string>) => {
      try {
        const data = JSON.parse(event.data) as StreamEvent;

        switch (data.type) {
          case 'heartbeat':
            break;

          case 'vehicle_positions':
            setVehiclePositions(prev => {
              const newPositions = new Map(prev);
              data.data.forEach(vehicle => {
                if (vehicle.vehicle_id) {
                  newPositions.set(vehicle.vehicle_id, vehicle);
                }
              });
              return newPositions;
            });
            break;

          case 'trip_updates':
            setTripUpdates(prev => {
              const newUpdates = new Map(prev);
              data.data.forEach(update => {
                if (update.entity_id) {
                  newUpdates.set(update.entity_id, update);
                }
              });
              return newUpdates;
            });
            break;

          case 'error':
            console.error('Stream error:', data.message);
            setError(data.message);
            break;

          default:
            console.warn('Unknown event type received from stream');
        }

      } catch (err) {
        console.error('Error parsing event data:', err);
        setError('Error parsing stream data');
      }
    };

    eventSource.onerror = () => {
      console.error('EventSource connection error.');
      setIsConnected(false);
      setError('Connection to stream failed.');
      eventSource.close();
    };

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, []);

  return {
    vehiclePositions,
    tripUpdates,
    isConnected,
    error,
  };
};
