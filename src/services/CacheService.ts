/**
 * Cache Service
 * 
 * A simple in-memory cache service with TTL support.
 * This can be used to cache API responses or any data that needs to be retrieved frequently.
 */

import { createLogger } from '../utils/logger';

// Initialize logger
const logger = createLogger('CacheService');

// Cache item interface
interface CacheItem<T> {
  value: T;
  expiry: number | null; // Timestamp when the item expires, null means never expires
}

/**
 * Cache Service
 * Provides in-memory caching with TTL support
 */
export class CacheService {
  private cache: Map<string, CacheItem<any>> = new Map();
  private namespace: string;
  private defaultTtl: number;
  
  /**
   * Create a new CacheService
   * @param namespace Namespace for the cache keys
   * @param defaultTtl Default TTL in seconds, 0 means no expiry
   */
  constructor(namespace: string, defaultTtl: number = 300) {
    this.namespace = namespace;
    this.defaultTtl = defaultTtl * 1000; // Convert to milliseconds
    
    logger.info(`CacheService initialized for namespace: ${namespace} with default TTL: ${defaultTtl}s`);
    
    // Set up periodic cleanup of expired items
    setInterval(() => this.cleanupExpired(), 60000); // Clean up every minute
  }
  
  /**
   * Get the full key with namespace
   * @param key Cache key
   * @returns Full key with namespace
   */
  private getFullKey(key: string): string {
    return `${this.namespace}:${key}`;
  }
  
  /**
   * Set a value in the cache
   * @param key Cache key
   * @param value Value to cache
   * @param ttl TTL in seconds, 0 means use default TTL, null means no expiry
   */
  public set<T>(key: string, value: T, ttl: number | null = 0): void {
    const fullKey = this.getFullKey(key);
    
    // Calculate expiry timestamp
    let expiry: number | null = null;
    if (ttl === 0) {
      // Use default TTL
      expiry = this.defaultTtl > 0 ? Date.now() + this.defaultTtl : null;
    } else if (ttl !== null) {
      // Use specified TTL
      expiry = Date.now() + ttl * 1000;
    }
    
    // Store in cache
    this.cache.set(fullKey, { value, expiry });
    
    logger.debug(`Cached item set: ${fullKey} ${expiry ? `(expires: ${new Date(expiry).toISOString()})` : '(no expiry)'}`);
  }
  
  /**
   * Get a value from the cache
   * @param key Cache key
   * @returns Cached value or undefined if not found or expired
   */
  public get<T>(key: string): T | undefined {
    const fullKey = this.getFullKey(key);
    const item = this.cache.get(fullKey);
    
    // Check if item exists and is not expired
    if (item) {
      if (item.expiry === null || item.expiry > Date.now()) {
        logger.debug(`Cache hit: ${fullKey}`);
        return item.value as T;
      } else {
        // Item expired, remove it
        logger.debug(`Cache expired: ${fullKey}`);
        this.cache.delete(fullKey);
      }
    }
    
    logger.debug(`Cache miss: ${fullKey}`);
    return undefined;
  }
  
  /**
   * Check if a key exists in the cache and is not expired
   * @param key Cache key
   * @returns True if key exists and is not expired
   */
  public has(key: string): boolean {
    const fullKey = this.getFullKey(key);
    const item = this.cache.get(fullKey);
    
    if (item) {
      if (item.expiry === null || item.expiry > Date.now()) {
        return true;
      } else {
        // Item expired, remove it
        this.cache.delete(fullKey);
      }
    }
    
    return false;
  }
  
  /**
   * Delete a value from the cache
   * @param key Cache key
   * @returns True if item was deleted, false if it didn't exist
   */
  public delete(key: string): boolean {
    const fullKey = this.getFullKey(key);
    const deleted = this.cache.delete(fullKey);
    
    if (deleted) {
      logger.debug(`Cache deleted: ${fullKey}`);
    }
    
    return deleted;
  }
  
  /**
   * Clear all values in this cache namespace
   */
  public clear(): void {
    const keyPrefix = `${this.namespace}:`;
    
    // Delete all keys in this namespace
    for (const key of this.cache.keys()) {
      if (key.startsWith(keyPrefix)) {
        this.cache.delete(key);
      }
    }
    
    logger.debug(`Cache cleared for namespace: ${this.namespace}`);
  }
  
  /**
   * Clean up expired items from cache
   */
  private cleanupExpired(): void {
    const now = Date.now();
    let expiredCount = 0;
    
    for (const [key, item] of this.cache.entries()) {
      if (item.expiry !== null && item.expiry <= now) {
        this.cache.delete(key);
        expiredCount++;
      }
    }
    
    if (expiredCount > 0) {
      logger.debug(`Cleaned up ${expiredCount} expired items from cache`);
    }
  }
}

// Export singleton instance for the Gist cache
export const gistCache = new CacheService('gists', 300); // 5 minutes default TTL 