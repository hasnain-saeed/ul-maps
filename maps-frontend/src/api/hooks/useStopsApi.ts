// import { useApiQuery } from './useApiQuery';
// import { stopsApi } from '../requests/stops.api';

// TODO: Uncomment when stops API endpoints are available
// export const useStops = () =>
//   useApiQuery(['stops'], stopsApi.getAll);

// export const useStop = (id: string) =>
//   useApiQuery(['stops', id], () => stopsApi.getById(id), {
//     enabled: !!id,
//   });

// export const useStopTimes = (stopId: string) =>
//   useApiQuery(['stops', stopId, 'times'], () => stopsApi.getTimes(stopId), {
//     enabled: !!stopId,
//   });

// export const useNearbyStops = (lat?: number, lng?: number, radius: number = 1000) =>
//   useApiQuery(
//     ['stops', 'nearby', lat ?? 0, lng ?? 0, radius],
//     () => stopsApi.getNearby(lat!, lng!, radius),
//     {
//       enabled: lat !== undefined && lng !== undefined,
//     }
//   );
