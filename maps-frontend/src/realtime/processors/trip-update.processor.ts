import { useQueryClient } from '@tanstack/react-query';
import type { TripUpdatesMessage, TripUpdate } from '../types/messages';

class TripUpdateProcessor {
  private queryClient: ReturnType<typeof useQueryClient> | null = null;

  setQueryClient(queryClient: ReturnType<typeof useQueryClient>) {
    this.queryClient = queryClient;
  }

  process(message: TripUpdatesMessage): void {
    if (!this.queryClient) {
      console.warn('QueryClient not set for TripUpdateProcessor');
      return;
    }

    this.queryClient.setQueryData(
      ['realtime', 'trips'],
      (oldData: Map<string, TripUpdate> | undefined) => {
        const newUpdates = new Map(oldData);
        message.data.forEach((trip) => {
          newUpdates.set(trip.trip_id, trip);
        });
        return newUpdates;
      }
    );
  }
}

export const tripUpdateProcessor = new TripUpdateProcessor();