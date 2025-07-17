import { useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';

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


const fetchInitialVehicles = async (): Promise<Map<string, VehiclePosition>> => {
  const response = await fetch('http://localhost:8000/api/vehicle_positions');
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  const responseData = await response.json();

  if (responseData && Array.isArray(responseData.data)) {
    const vehicles: VehiclePosition[] = responseData.data;
    return new Map(vehicles.map(v => [v.vehicle_id, v]));
  } else {
    throw new Error('Invalid data structure received from API');
  }
};


export const useVehicles = () => {
  const queryClient = useQueryClient();

  const { data: vehiclePositions, isLoading, isError, error } = useQuery({
    queryKey: ['vehicles'],
    queryFn: fetchInitialVehicles,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  });

  console.log("vehiclePositions in useVehicles", vehiclePositions);

  useEffect(() => {
    const eventSource = new EventSource('http://localhost:8000/api/stream');

    eventSource.onmessage = (event: MessageEvent<string>) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === 'vehicle_positions' && message.data) {
          queryClient.setQueryData(['vehicles'], (oldData: Map<string, VehiclePosition> | undefined) => {
            const newPositions = new Map(oldData);
            message.data.forEach((vehicle: VehiclePosition) => {
              newPositions.set(vehicle.vehicle_id, vehicle);
            });
            return newPositions;
          });
        }
      } catch (err) {
        console.error('Error processing stream message:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('EventSource error:', err);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [queryClient]);

  return { vehiclePositions, isLoading, isError, error };
};
