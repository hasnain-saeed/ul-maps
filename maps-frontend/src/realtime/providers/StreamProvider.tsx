import React, { createContext, useContext, useEffect, type ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { messageRouter } from '../processors/message.router';
import { vehiclePositionProcessor } from '../processors/vehicle-position.processor';
import { tripUpdateProcessor } from '../processors/trip-update.processor';

interface StreamContextType {
  isConnected: boolean;
}

const StreamContext = createContext<StreamContextType | undefined>(undefined);

interface StreamProviderProps {
  children: ReactNode;
  streamUrl?: string;
}

export const StreamProvider = ({
  children,
  streamUrl = 'http://localhost:8000/api/v1/stream'
}: StreamProviderProps) => {
  const queryClient = useQueryClient();
  const [isConnected, setIsConnected] = React.useState(false);

  useEffect(() => {
    vehiclePositionProcessor.setQueryClient(queryClient);
    tripUpdateProcessor.setQueryClient(queryClient);

    const eventSource = new EventSource(streamUrl);

    eventSource.onopen = () => {
      setIsConnected(true);
    };

    eventSource.onmessage = (event: MessageEvent<string>) => {
      messageRouter.processMessage(event.data);
    };

    eventSource.onerror = (error) => {
      console.error('EventSource error:', error);
      setIsConnected(false);
      eventSource.close();
    };

    return () => {
      setIsConnected(false);
      eventSource.close();
    };
  }, [queryClient, streamUrl]);

  const value: StreamContextType = {
    isConnected,
  };

  return (
    <StreamContext.Provider value={value}>
      {children}
    </StreamContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useStreamContext = (): StreamContextType => {
  const context = useContext(StreamContext);
  if (context === undefined) {
    throw new Error('useStreamContext must be used within a StreamProvider');
  }
  return context;
};
