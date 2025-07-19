import { useQuery } from '@tanstack/react-query';
import type { VehiclePosition } from '../types/messages';

const fetchInitialVehicles = async (): Promise<Map<string, VehiclePosition>> => {
  const response = await fetch('http://localhost:8000/api/v1/vehicle_positions');
  if (!response.ok) {
    throw new Error('Failed to fetch initial vehicle positions');
  }
  const vehicles: VehiclePosition[] = await response.json();
  return new Map(vehicles.map(v => [v.vehicle_id, v]));
};

export const useVehiclePositions = () => {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['realtime', 'vehicles'],
    queryFn: fetchInitialVehicles,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  });

  return {
    vehiclePositions: data,
    isLoading,
    isError,
    error,
  };
};