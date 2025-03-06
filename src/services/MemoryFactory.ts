/**
 * Memory Factory
 * 
 * Factory for creating and managing memory service instances
 */
import { 
  MemoryService, 
  MemoryType, 
  ShortTermMemoryOptions, 
  ShortTermMemoryService,
  LongTermMemoryOptions,
  LongTermMemoryService
} from './MemoryService';
import { InMemoryShortTermMemoryService } from './ShortTermMemoryService';
import { RedisLongTermMemoryService } from './LongTermMemoryService';
import { createLogger } from '../utils/logger';

// Initialize logger
const logger = createLogger('MemoryFactory');

/**
 * Memory Factory
 * Provides methods for creating and managing memory service instances
 */
export class MemoryFactory {
  private static shortTermInstances: Map<string, ShortTermMemoryService> = new Map();
  private static longTermInstances: Map<string, LongTermMemoryService> = new Map();
  
  /**
   * Get a short-term memory service instance
   * @param namespace The namespace for the memory service
   * @param options Options for the memory service
   * @returns A short-term memory service instance
   */
  public static async getShortTermMemory(
    namespace: string, 
    options?: ShortTermMemoryOptions
  ): Promise<ShortTermMemoryService> {
    // Check if we already have an instance for this namespace
    const existingInstance = this.shortTermInstances.get(namespace);
    if (existingInstance) {
      logger.debug(`Returning existing short-term memory instance for namespace: ${namespace}`);
      return existingInstance;
    }
    
    // Create a new instance
    const mergedOptions: ShortTermMemoryOptions = {
      ...options,
      namespace,
    };
    
    const instance = new InMemoryShortTermMemoryService(mergedOptions);
    await instance.initialize();
    
    // Store the instance for reuse
    this.shortTermInstances.set(namespace, instance);
    logger.debug(`Created new short-term memory instance for namespace: ${namespace}`);
    
    return instance;
  }
  
  /**
   * Get a long-term memory service instance
   * @param namespace The namespace for the memory service
   * @param options Options for the memory service
   * @returns A long-term memory service instance
   */
  public static async getLongTermMemory(
    namespace: string, 
    options?: LongTermMemoryOptions
  ): Promise<LongTermMemoryService> {
    // Check if we already have an instance for this namespace
    const existingInstance = this.longTermInstances.get(namespace);
    if (existingInstance) {
      logger.debug(`Returning existing long-term memory instance for namespace: ${namespace}`);
      return existingInstance;
    }
    
    // Create a new instance
    const mergedOptions: LongTermMemoryOptions = {
      ...options,
      namespace,
    };
    
    const instance = new RedisLongTermMemoryService(mergedOptions);
    await instance.initialize();
    
    // Store the instance for reuse
    this.longTermInstances.set(namespace, instance);
    logger.debug(`Created new long-term memory instance for namespace: ${namespace}`);
    
    return instance;
  }
  
  /**
   * Get a memory service instance of the specified type
   * @param type The type of memory service to get
   * @param namespace The namespace for the memory service
   * @param options Options for the memory service
   * @returns A memory service instance
   */
  public static async getMemory(
    type: MemoryType, 
    namespace: string, 
    options?: ShortTermMemoryOptions | LongTermMemoryOptions
  ): Promise<MemoryService> {
    switch (type) {
      case MemoryType.SHORT_TERM:
        return this.getShortTermMemory(namespace, options as ShortTermMemoryOptions);
      case MemoryType.LONG_TERM:
        return this.getLongTermMemory(namespace, options as LongTermMemoryOptions);
      default:
        throw new Error(`Invalid memory type: ${type}`);
    }
  }
  
  /**
   * Close all memory service instances
   */
  public static async closeAll(): Promise<void> {
    // Close all short-term memory instances
    for (const [namespace, instance] of this.shortTermInstances.entries()) {
      await instance.close();
      logger.debug(`Closed short-term memory instance for namespace: ${namespace}`);
    }
    this.shortTermInstances.clear();
    
    // Close all long-term memory instances
    for (const [namespace, instance] of this.longTermInstances.entries()) {
      await instance.close();
      logger.debug(`Closed long-term memory instance for namespace: ${namespace}`);
    }
    this.longTermInstances.clear();
    
    logger.debug('All memory instances closed');
  }
} 