// TODO: Uncomment when trip_updates API endpoint is available
// import { useQuery } from '@tanstack/react-query';
// import type { TripUpdate } from '../types/messages';

// const fetchInitialTripUpdates = async (): Promise<Map<string, TripUpdate>> => {
//   const response = await fetch('http://localhost:8000/api/v1/trip_updates');
//   if (!response.ok) {
//     throw new Error('Failed to fetch initial trip updates');
//   }
//   const trips: TripUpdate[] = await response.json();
//   return new Map(trips.map(t => [t.trip_id, t]));
// };

// export const useTripUpdates = () => {
//   const { data, isLoading, isError, error } = useQuery({
//     queryKey: ['realtime', 'trips'],
//     queryFn: fetchInitialTripUpdates,
//     staleTime: Infinity,
//     refetchOnWindowFocus: false,
//   });

//   return {
//     tripUpdates: data,
//     isLoading,
//     isError,
//     error,
//   };
// };