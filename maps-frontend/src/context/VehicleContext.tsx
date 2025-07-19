import { createContext, useContext, type ReactNode } from 'react';
import { useVehiclePositions } from '../realtime/hooks/useVehiclePositions';
import type { VehiclePosition } from '../realtime/types/messages';

interface VehicleContextType {
  vehiclePositions: Map<string, VehiclePosition> | undefined;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}

const VehicleContext = createContext<VehicleContextType | undefined>(undefined);

interface VehicleProviderProps {
  children: ReactNode;
}

export const VehicleProvider = ({ children }: VehicleProviderProps) => {
  const { vehiclePositions, isLoading, isError, error } = useVehiclePositions();

  const value: VehicleContextType = {
    vehiclePositions,
    isLoading,
    isError,
    error,
  };

  return (
    <VehicleContext.Provider value={value}>
      {children}
    </VehicleContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useVehicleContext = (): VehicleContextType => {
  const context = useContext(VehicleContext);
  if (context === undefined) {
    throw new Error('useVehicleContext must be used within a VehicleProvider');
  }
  return context;
};
