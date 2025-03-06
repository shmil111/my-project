/**
 * Short-Term Memory Service
 * 
 * Implementation of the ShortTermMemory interface using node-cache.
 * This service provides fast in-memory caching with optional TTL.
 */

import NodeCache from 'node-cache';
import { BaseMemoryService, MemoryOptions, MemoryType, ShortTermMemoryOptions, ShortTermMemoryService } from './MemoryService';
import { createLogger } from '../utils/logger';

// Initialize logger
const logger = createLogger('ShortTermMemoryService');

/**
 * In-memory implementation of ShortTermMemoryService using node-cache
 */
export class InMemoryShortTermMemoryService extends BaseMemoryService implements ShortTermMemoryService {
  private cache: NodeCache;
  private readonly defaultTTL: number;
  
  /**
   * Create a new in-memory short-term memory service
   * @param options Options for the memory service
   */
  constructor(options?: ShortTermMemoryOptions) {
    super(options);
    this.defaultTTL = options?.ttl || 3600; // Default TTL: 1 hour
    
    this.cache = new NodeCache({
      stdTTL: this.defaultTTL,
      checkperiod: Math.min(this.defaultTTL / 10, 600), // Check for expired keys at most every 10 minutes
      useClones: false, // Don't clone objects (better performance)
    });
    
    logger.debug(`Created ShortTermMemoryService with namespace: ${this.namespace}, defaultTTL: ${this.defaultTTL}s`);
  }
  
  /**
   * Initialize the memory service
   */
  public async initialize(): Promise<void> {
    logger.debug('ShortTermMemoryService initialized');
    return Promise.resolve();
  }
  
  /**
   * Close the memory service
   */
  public async close(): Promise<void> {
    this.cache.close();
    logger.debug('ShortTermMemoryService closed');
    return Promise.resolve();
  }
  
  /**
   * Set a key-value pair with an optional time to live
   * @param key The key to store the value under
   * @param value The value to store
   * @param ttl Optional time-to-live in seconds (0 means use default)
   * @returns True if successful
   */
  public async set<T>(key: string, value: T, ttl: number = this.defaultTTL): Promise<boolean> {
    const namespacedKey = this.getNamespacedKey(key);
    const effectiveTTL = ttl === 0 ? this.defaultTTL : ttl;
    
    try {
      const success = this.cache.set(namespacedKey, value, effectiveTTL);
      logger.debug(`Set ${namespacedKey} with TTL ${effectiveTTL}s: ${success ? 'success' : 'failed'}`);
      return success;
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
    const namespacedKey = this.getNamespacedKey(key);
    
    try {
      const value = this.cache.get<T>(namespacedKey);
      logger.debug(`Get ${namespacedKey}: ${value !== undefined ? 'found' : 'not found'}`);
      return value !== undefined ? value : null;
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
    const namespacedKey = this.getNamespacedKey(key);
    const exists = this.cache.has(namespacedKey);
    logger.debug(`Has ${namespacedKey}: ${exists}`);
    return exists;
  }
  
  /**
   * Delete a key-value pair
   * @param key The key to delete
   * @returns True if the key was deleted, false if it didn't exist
   */
  public async delete(key: string): Promise<boolean> {
    const namespacedKey = this.getNamespacedKey(key);
    const deleted = this.cache.del(namespacedKey) === 1;
    logger.debug(`Delete ${namespacedKey}: ${deleted ? 'deleted' : 'not found'}`);
    return deleted;
  }
  
  /**
   * Clear all key-value pairs in a namespace
   * @param namespace Optional namespace (defaults to service namespace)
   * @returns Number of items cleared
   */
  public async clear(namespace?: string): Promise<number> {
    const prefix = namespace || this.namespace;
    const allKeys = this.cache.keys();
    const keysToDelete = allKeys.filter(key => key.startsWith(`${prefix}:`));
    
    if (keysToDelete.length === 0) {
      logger.debug(`Clear ${prefix}: No keys found`);
      return 0;
    }
    
    const deleted = this.cache.del(keysToDelete);
    logger.debug(`Clear ${prefix}: Deleted ${deleted} keys`);
    return deleted;
  }
  
  /**
   * Get all keys in a namespace
   * @param namespace Optional namespace (defaults to service namespace)
   * @returns Array of keys without the namespace prefix
   */
  public async keys(namespace?: string): Promise<string[]> {
    const prefix = namespace || this.namespace;
    const prefixWithSeparator = `${prefix}:`;
    
    const allKeys = this.cache.keys();
    const filteredKeys = allKeys
      .filter(key => key.startsWith(prefixWithSeparator))
      .map(key => key.substring(prefixWithSeparator.length));
    
    logger.debug(`Keys for ${prefix}: Found ${filteredKeys.length} keys`);
    return filteredKeys;
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
   * Get memory usage statistics
   * @returns Object containing statistics
   */
  public async getStats(): Promise<Record<string, any>> {
    const stats = this.cache.getStats();
    const size = await this.size();
    
    const enhancedStats = {
      ...stats,
      namespace: this.namespace,
      namespaceSize: size,
      defaultTTL: this.defaultTTL,
    };
    
    logger.debug(`Stats for ${this.namespace}: ${JSON.stringify(enhancedStats)}`);
    return enhancedStats;
  }
  
  /**
   * Get the memory type
   * @returns 'short-term'
   */
  public getType(): string {
    return MemoryType.SHORT_TERM;
  }
} 