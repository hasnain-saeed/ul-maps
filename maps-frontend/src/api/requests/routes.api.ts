import { apiClient } from './base.api';
import type { Route, RouteStop, RouteShape } from '../types/routes';

export const routesApi = {
  getAll: (): Promise<Route[]> => 
    apiClient.get<Route[]>('/routes'),

  getById: (id: string): Promise<Route> => 
    apiClient.get<Route>(`/routes/${id}`),

  getStops: (routeId: string): Promise<RouteStop[]> => 
    apiClient.get<RouteStop[]>(`/routes/${routeId}/stops`),

  getShape: (routeId: string): Promise<RouteShape> => 
    apiClient.get<RouteShape>(`/routes/${routeId}/shape`),
};