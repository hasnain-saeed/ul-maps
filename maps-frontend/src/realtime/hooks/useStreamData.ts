import { useStreamContext } from '../providers/StreamProvider';
import { useVehiclePositions } from './useVehiclePositions';
// import { useTripUpdates } from './useTripUpdates';

export const useStreamData = () => {
  const { isConnected } = useStreamContext();
  const vehicleData = useVehiclePositions();
  // const tripData = useTripUpdates(); // TODO: Uncomment when trip updates are supported

  return {
    isConnected,
    vehicles: vehicleData,
    // trips: tripData, // TODO: Uncomment when trip updates are supported
  };
};
