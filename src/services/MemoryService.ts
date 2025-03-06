/**
 * Memory Service
 * 
 * Defines interfaces for memory services, providing both short-term
 * and long-term memory storage capabilities.
 */

import { createLogger } from '../utils/logger';

// Initialize logger
const logger = createLogger('MemoryService');

/**
 * Memory types supported by the application
 */
export enum MemoryType {
  SHORT_TERM = 'short-term',
  LONG_TERM = 'long-term',
}

/**
 * Base memory options
 */
export interface MemoryOptions {
  namespace?: string;
}

/**
 * Short-term memory options
 */
export interface ShortTermMemoryOptions extends MemoryOptions {
  ttl?: number; // Time to live in seconds
}

/**
 * Long-term memory options
 */
export interface LongTermMemoryOptions extends MemoryOptions {
  persistent?: boolean; // Whether to persist to disk
}

/**
 * Memory service interface
 * Defines common functionality for all memory services
 */
export interface MemoryService {
  /**
   * Initialize the memory service
   */
  initialize(): Promise<void>;
  
  /**
   * Close the memory service
   */
  close(): Promise<void>;
  
  /**
   * Set a key-value pair with an optional time to live
   * @param key The key to store the value under
   * @param value The value to store
   * @param ttl Optional time-to-live in seconds (0 means no expiration)
   * @returns True if successful
   */
  set<T>(key: string, value: T, ttl?: number): Promise<boolean>;
  
  /**
   * Get a value by key
   * @param key The key of the item to retrieve
   * @returns The stored value or null if not found
   */
  get<T>(key: string): Promise<T | null>;
  
  /**
   * Check if a key exists
   * @param key The key to check
   * @returns True if the key exists, false otherwise
   */
  has(key: string): Promise<boolean>;
  
  /**
   * Delete a key-value pair
   * @param key The key of the item to delete
   * @returns True if successful, false if the item doesn't exist
   */
  delete(key: string): Promise<boolean>;
  
  /**
   * Clear all key-value pairs in a namespace
   * @param namespace Optional namespace to clear (defaults to service namespace)
   * @returns Number of items cleared
   */
  clear(namespace?: string): Promise<number>;
  
  /**
   * Get all keys in a namespace
   * @param namespace Optional namespace to list keys from (defaults to service namespace)
   * @returns Array of keys
   */
  keys(namespace?: string): Promise<string[]>;
  
  /**
   * Get the number of items in the memory
   */
  size(): Promise<number>;
  
  /**
   * Get the memory type name (short-term or long-term)
   * @returns The memory type name
   */
  getType(): string;
}

/**
 * Short-term memory service interface
 */
export interface ShortTermMemoryService extends MemoryService {
  /**
   * Get statistics about the memory usage
   */
  getStats(): Promise<Record<string, any>>;
}

/**
 * Long-term memory service interface
 */
export interface LongTermMemoryService extends MemoryService {
  /**
   * Search for keys matching a pattern
   */
  search(pattern: string): Promise<string[]>;
  
  /**
   * Get a range of values (for lists, etc.)
   */
  getRange<T>(key: string, start: number, end: number): Promise<T[]>;
  
  /**
   * Increment a value
   */
  increment(key: string, value?: number): Promise<number>;
  
  /**
   * Expire a key after a certain number of seconds
   */
  expire(key: string, ttl: number): Promise<boolean>;

  /**
   * Ping the underlying database service to check connection
   * @returns A promise that resolves to a string indicating the service is connected
   */
  ping(): Promise<string>;
}

/**
 * Abstract base class for memory services
 * Provides common functionality and utility methods
 */
export abstract class BaseMemoryService implements MemoryService {
  protected readonly namespace: string;
  
  constructor(options?: MemoryOptions) {
    this.namespace = options?.namespace || 'default';
    logger.debug(`Initializing memory service with namespace: ${this.namespace}`);
  }
  
  /**
   * Initialize the memory service
   */
  public abstract initialize(): Promise<void>;
  
  /**
   * Close the memory service
   */
  public abstract close(): Promise<void>;
  
  /**
   * Set a key-value pair
   */
  public abstract set<T>(key: string, value: T, ttl?: number): Promise<boolean>;
  
  /**
   * Get a value by key
   */
  public abstract get<T>(key: string): Promise<T | null>;
  
  /**
   * Check if a key exists
   */
  public abstract has(key: string): Promise<boolean>;
  
  /**
   * Delete a key-value pair
   */
  public abstract delete(key: string): Promise<boolean>;
  
  /**
   * Clear all key-value pairs
   */
  public abstract clear(namespace?: string): Promise<number>;
  
  /**
   * Get all keys
   */
  public abstract keys(namespace?: string): Promise<string[]>;
  
  /**
   * Get the number of items in the memory
   */
  public abstract size(): Promise<number>;
  
  /**
   * Get the memory type
   */
  public abstract getType(): string;
  
  /**
   * Generate a namespaced key
   */
  protected getNamespacedKey(key: string): string {
    return `${this.namespace}:${key}`;
  }
} 