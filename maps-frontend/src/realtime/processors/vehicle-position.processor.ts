import { useQueryClient } from '@tanstack/react-query';
import type { VehiclePositionsMessage, VehiclePosition } from '../types/messages';

class VehiclePositionProcessor {
  private queryClient: ReturnType<typeof useQueryClient> | null = null;

  setQueryClient(queryClient: ReturnType<typeof useQueryClient>) {
    this.queryClient = queryClient;
  }

  process(message: VehiclePositionsMessage): void {
    if (!this.queryClient) {
      console.warn('QueryClient not set for VehiclePositionProcessor');
      return;
    }

    this.queryClient.setQueryData(
      ['realtime', 'vehicles'],
      (oldData: Map<string, VehiclePosition> | undefined) => {
        const newPositions = new Map(oldData);
        message.data.forEach((vehicle) => {
          newPositions.set(vehicle.vehicle_id, vehicle);
        });
        return newPositions;
      }
    );
  }
}

export const vehiclePositionProcessor = new VehiclePositionProcessor();