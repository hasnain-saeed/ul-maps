// import { useApiQuery } from './useApiQuery';
// import { routesApi } from '../requests/routes.api';

// TODO: Uncomment when routes API endpoint is available
// export const useRoutes = () =>
//   useApiQuery(['routes'], routesApi.getAll);

// export const useRoute = (id: string) =>
//   useApiQuery(['routes', id], () => routesApi.getById(id), {
//     enabled: !!id,
//   });

// export const useRouteStops = (routeId: string) =>
//   useApiQuery(['routes', routeId, 'stops'], () => routesApi.getStops(routeId), {
//     enabled: !!routeId,
//   });

// export const useRouteShape = (routeId: string) =>
//   useApiQuery(['routes', routeId, 'shape'], () => routesApi.getShape(routeId), {
//     enabled: !!routeId,
//   });
