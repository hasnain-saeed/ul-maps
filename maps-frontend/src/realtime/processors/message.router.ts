import type { StreamMessage } from '../types/messages';
import { vehiclePositionProcessor } from './vehicle-position.processor';
// import { tripUpdateProcessor } from './trip-update.processor';

interface MessageProcessor {
  process: (message: unknown) => void;
}

export class MessageRouter {
  private processors = new Map<string, MessageProcessor>([
    ['vehicle_positions', vehiclePositionProcessor as MessageProcessor],
    // ['trip_updates', tripUpdateProcessor], // TODO: Uncomment when trip updates are supported
  ]);

  processMessage(rawMessage: string): void {
    try {
      const message: StreamMessage = JSON.parse(rawMessage);
      const processor = this.processors.get(message.type);
      
      if (processor) {
        processor.process(message);
      } else {
        console.warn(`No processor found for message type: ${message.type}`);
      }
    } catch (error) {
      console.error('Error processing stream message:', error);
    }
  }

  registerProcessor(type: string, processor: MessageProcessor) {
    this.processors.set(type, processor);
  }
}

export const messageRouter = new MessageRouter();