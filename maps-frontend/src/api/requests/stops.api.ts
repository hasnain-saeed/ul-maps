import { apiClient } from './base.api';
import type { Stop, StopTime } from '../types/stops';

export const stopsApi = {
  getAll: (): Promise<Stop[]> => 
    apiClient.get<Stop[]>('/stops'),

  getById: (id: string): Promise<Stop> => 
    apiClient.get<Stop>(`/stops/${id}`),

  getTimes: (stopId: string): Promise<StopTime[]> => 
    apiClient.get<StopTime[]>(`/stops/${stopId}/times`),

  getNearby: (lat: number, lng: number, radius: number = 1000): Promise<Stop[]> => 
    apiClient.get<Stop[]>(`/stops/nearby?lat=${lat}&lng=${lng}&radius=${radius}`),
};