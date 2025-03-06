/**
 * Long-Term Memory Service
 * 
 * Implementation of the LongTermMemory interface using Redis.
 * This service provides persistent storage with optional TTL.
 */

import { createClient, RedisClientType } from 'redis';
import { BaseMemoryService, LongTermMemoryOptions, LongTermMemoryService, MemoryType } from './MemoryService';
import { createLogger } from '../utils/logger';
import { config } from '../config';

// Initialize logger
const logger = createLogger('LongTermMemoryService');

// Default Redis configuration
const DEFAULT_REDIS_CONFIG = {
  host: config.redis.host || 'localhost',
  port: config.redis.port || 6379,
  password: config.redis.password || undefined,
  db: config.redis.db || 0,
};

/**
 * Redis implementation of LongTermMemoryService
 */
export class RedisLongTermMemoryService extends BaseMemoryService implements LongTermMemoryService {
  private client: RedisClientType;
  private isConnected = false;
  
  /**
   * Create a new Redis long-term memory service
   * @param options Options for the memory service
   */
  constructor(options?: LongTermMemoryOptions) {
    super(options);
    
    // Create Redis client
    const url = `redis://${DEFAULT_REDIS_CONFIG.password ? `:${DEFAULT_REDIS_CONFIG.password}@` : ''}${DEFAULT_REDIS_CONFIG.host}:${DEFAULT_REDIS_CONFIG.port}/${DEFAULT_REDIS_CONFIG.db}`;
    
    this.client = createClient({
      url,
    });
    
    // Set up event handlers
    this.client.on('error', (err) => {
      logger.error(`Redis error: ${err.message}`);
    });
    
    this.client.on('connect', () => {
      logger.debug('Redis connected');
    });
    
    this.client.on('ready', () => {
      logger.debug('Redis ready');
    });
    
    this.client.on('end', () => {
      logger.debug('Redis connection closed');
      this.isConnected = false;
    });
    
    logger.debug(`Created LongTermMemoryService with namespace: ${this.namespace}, Redis: ${DEFAULT_REDIS_CONFIG.host}:${DEFAULT_REDIS_CONFIG.port}`);
  }
  
  /**
   * Initialize the memory service
   */
  public async initialize(): Promise<void> {
    if (this.isConnected) {
      return;
    }
    
    try {
      await this.client.connect();
      this.isConnected = true;
      logger.debug('LongTermMemoryService initialized');
    } catch (error) {
      logger.error(`Failed to connect to Redis: ${error}`);
      throw new Error(`Failed to connect to Redis: ${error}`);
    }
  }
  
  /**
   * Close the memory service
   */
  public async close(): Promise<void> {
    if (!this.isConnected) {
      return;
    }
    
    try {
      await this.client.quit();
      this.isConnected = false;
      logger.debug('LongTermMemoryService closed');
    } catch (error) {
      logger.error(`Error closing Redis connection: ${error}`);
    }
  }
  
  /**
   * Ensure the client is connected
   */
  private async ensureConnected(): Promise<void> {
    if (!this.isConnected) {
      await this.initialize();
    }
  }
  
  /**
   * Set a key-value pair with an optional time to live
   * @param key The key to store the value under
   * @param value The value to store
   * @param ttl Optional time-to-live in seconds (0 means no expiration)
   * @returns True if successful
   */
  public async set<T>(key: string, value: T, ttl: number = 0): Promise<boolean> {
    await this.ensureConnected();
    const namespacedKey = this.getNamespacedKey(key);
    
    try {
      // Convert value to JSON string
      const valueString = JSON.stringify(value);
      
      // Set the value
      if (ttl > 0) {
        await this.client.setEx(namespacedKey, ttl, valueString);
      } else {
        await this.client.set(namespacedKey, valueString);
      }
      
      logger.debug(`Set ${namespacedKey}${ttl > 0 ? ` with TTL ${ttl}s` : ''}: success`);
      return true;
    } catch (error) {
      logger.error(`Error setting ${namespacedKey}: ${error}`);
      return false;
    }
  }
  
  /**
   * Get a value by key
   * @param key The key to retrieve
   * @returns The value or null if not found
   */
  public async get<T>(key: string): Promise<T | null> {
    await this.ensureConnected();
    const namespacedKey = this.getNamespacedKey(key);
    
    try {
      const value = await this.client.get(namespacedKey);
      
      if (value === null) {
        logger.debug(`Get ${namespacedKey}: not found`);
        return null;
      }
      
      // Parse the JSON string
      const parsed = JSON.parse(value) as T;
      logger.debug(`Get ${namespacedKey}: found`);
      return parsed;
    } catch (error) {
      logger.error(`Error getting ${namespacedKey}: ${error}`);
      return null;
    }
  }
  
  /**
   * Check if a key exists
   * @param key The key to check
   * @returns True if the key exists, false otherwise
   */
  public async has(key: string): Promise<boolean> {
    await this.ensureConnected();
    const namespacedKey = this.getNamespacedKey(key);
    
    try {
      const exists = await this.client.exists(namespacedKey);
      const result = exists === 1;
      logger.debug(`Has ${namespacedKey}: ${result}`);
      return result;
    } catch (error) {
      logger.error(`Error checking existence of ${namespacedKey}: ${error}`);
      return false;
    }
  }
  
  /**
   * Delete a key-value pair
   * @param key The key to delete
   * @returns True if the key was deleted, false if it didn't exist
   */
  public async delete(key: string): Promise<boolean> {
    await this.ensureConnected();
    const namespacedKey = this.getNamespacedKey(key);
    
    try {
      const deleted = await this.client.del(namespacedKey);
      const result = deleted === 1;
      logger.debug(`Delete ${namespacedKey}: ${result ? 'deleted' : 'not found'}`);
      return result;
    } catch (error) {
      logger.error(`Error deleting ${namespacedKey}: ${error}`);
      return false;
    }
  }
  
  /**
   * Clear all key-value pairs in a namespace
   * @param namespace Optional namespace (defaults to service namespace)
   * @returns Number of items cleared
   */
  public async clear(namespace?: string): Promise<number> {
    await this.ensureConnected();
    const prefix = namespace || this.namespace;
    const pattern = `${prefix}:*`;
    
    try {
      // Get all keys matching the pattern
      const keys = await this.client.keys(pattern);
      
      if (keys.length === 0) {
        logger.debug(`Clear ${prefix}: No keys found`);
        return 0;
      }
      
      // Delete all keys
      const deleted = await this.client.del(keys);
      logger.debug(`Clear ${prefix}: Deleted ${deleted} keys`);
      return deleted;
    } catch (error) {
      logger.error(`Error clearing namespace ${prefix}: ${error}`);
      return 0;
    }
  }
  
  /**
   * Get all keys in a namespace
   * @param namespace Optional namespace (defaults to service namespace)
   * @returns Array of keys without the namespace prefix
   */
  public async keys(namespace?: string): Promise<string[]> {
    await this.ensureConnected();
    const prefix = namespace || this.namespace;
    const pattern = `${prefix}:*`;
    const prefixWithSeparator = `${prefix}:`;
    
    try {
      const allKeys = await this.client.keys(pattern);
      const filteredKeys = allKeys.map(key => key.substring(prefixWithSeparator.length));
      
      logger.debug(`Keys for ${prefix}: Found ${filteredKeys.length} keys`);
      return filteredKeys;
    } catch (error) {
      logger.error(`Error getting keys for namespace ${prefix}: ${error}`);
      return [];
    }
  }
  
  /**
   * Get the number of items in the memory
   * @returns The number of items in the cache that match the service namespace
   */
  public async size(): Promise<number> {
    const keys = await this.keys();
    return keys.length;
  }
  
  /**
   * Search for keys matching a pattern
   * @param pattern The pattern to search for
   * @returns Array of matching keys without the namespace prefix
   */
  public async search(pattern: string): Promise<string[]> {
    await this.ensureConnected();
    const namespacedPattern = this.getNamespacedKey(pattern);
    
    try {
      const allKeys = await this.client.keys(namespacedPattern);
      const prefixWithSeparator = `${this.namespace}:`;
      const filteredKeys = allKeys.map(key => key.substring(prefixWithSeparator.length));
      
      logger.debug(`Search for ${namespacedPattern}: Found ${filteredKeys.length} keys`);
      return filteredKeys;
    } catch (error) {
      logger.error(`Error searching for pattern ${namespacedPattern}: ${error}`);
      return [];
    }
  }
  
  /**
   * Get a range of values (for lists, etc.)
   * @param key The key to retrieve
   * @param start The start index
   * @param end The end index
   * @returns Array of values
   */
  public async getRange<T>(key: string, start: number, end: number): Promise<T[]> {
    await this.ensureConnected();
    const namespacedKey = this.getNamespacedKey(key);
    
    try {
      // Check if the key exists and is a list
      const type = await this.client.type(namespacedKey);
      
      if (type !== 'list') {
        logger.error(`Key ${namespacedKey} is not a list (type: ${type})`);
        return [];
      }
      
      // Get the range
      const values = await this.client.lRange(namespacedKey, start, end);
      
      // Parse the JSON strings
      const parsed = values.map(value => JSON.parse(value) as T);
      
      logger.debug(`GetRange ${namespacedKey}[${start}:${end}]: Found ${parsed.length} items`);
      return parsed;
    } catch (error) {
      logger.error(`Error getting range for ${namespacedKey}: ${error}`);
      return [];
    }
  }
  
  /**
   * Increment a value
   * @param key The key to increment
   * @param value The value to increment by (default: 1)
   * @returns The new value
   */
  public async increment(key: string, value: number = 1): Promise<number> {
    await this.ensureConnected();
    const namespacedKey = this.getNamespacedKey(key);
    
    try {
      const newValue = await this.client.incrBy(namespacedKey, value);
      logger.debug(`Increment ${namespacedKey} by ${value}: New value is ${newValue}`);
      return newValue;
    } catch (error) {
      logger.error(`Error incrementing ${namespacedKey}: ${error}`);
      return 0;
    }
  }
  
  /**
   * Expire a key after a certain number of seconds
   * @param key The key to expire
   * @param ttl The time-to-live in seconds
   * @returns True if successful, false if the key doesn't exist
   */
  public async expire(key: string, ttl: number): Promise<boolean> {
    await this.ensureConnected();
    const namespacedKey = this.getNamespacedKey(key);
    
    try {
      const result = await this.client.expire(namespacedKey, ttl);
      logger.debug(`Expire ${namespacedKey} in ${ttl}s: ${result ? 'success' : 'failed (key may not exist)'}`);
      return result;
    } catch (error) {
      logger.error(`Error setting expiration for ${namespacedKey}: ${error}`);
      return false;
    }
  }
  
  /**
   * Get the memory type
   * @returns 'long-term'
   */
  public getType(): string {
    return MemoryType.LONG_TERM;
  }

  /**
   * Ping the Redis server to check the connection
   * @returns A promise that resolves to 'PONG' if the connection is successful
   */
  public async ping(): Promise<string> {
    try {
      return await this.client.ping();
    } catch (error) {
      const logger = createLogger('LongTermMemoryService');
      logger.error(`Redis ping failed: ${error}`);
      throw new Error('Redis connection failed');
    }
  }
} 