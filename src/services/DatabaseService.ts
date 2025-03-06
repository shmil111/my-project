/**
 * Database Service
 * 
 * This module provides an abstract database service that can be implemented
 * for different database backends.
 */

import { createLogger } from '../utils/logger';

const logger = createLogger('DatabaseService');

/**
 * Interface for a database record
 */
export interface DatabaseRecord {
  id: number | string;
  [key: string]: any;
}

/**
 * Database query options
 */
export interface QueryOptions {
  limit?: number;
  offset?: number;
  sortBy?: string;
  sortDirection?: 'asc' | 'desc';
  filter?: Record<string, any>;
}

/**
 * Abstract database service
 */
export abstract class DatabaseService<T extends DatabaseRecord> {
  protected collectionName: string;
  
  constructor(collectionName: string) {
    this.collectionName = collectionName;
    logger.info(`Initializing database service for collection: ${collectionName}`);
  }
  
  /**
   * Initialize the database connection
   */
  public abstract initialize(): Promise<boolean>;
  
  /**
   * Close the database connection
   */
  public abstract close(): Promise<void>;
  
  /**
   * Get all records
   */
  public abstract getAll(options?: QueryOptions): Promise<T[]>;
  
  /**
   * Get a record by ID
   */
  public abstract getById(id: number | string): Promise<T | null>;
  
  /**
   * Create a new record
   */
  public abstract create(data: Partial<T>): Promise<T>;
  
  /**
   * Update a record
   */
  public abstract update(id: number | string, data: Partial<T>): Promise<T | null>;
  
  /**
   * Delete a record
   */
  public abstract delete(id: number | string): Promise<boolean>;
  
  /**
   * Check if a record exists
   */
  public abstract exists(id: number | string): Promise<boolean>;
  
  /**
   * Count records
   */
  public abstract count(filter?: Record<string, any>): Promise<number>;
}

/**
 * In-memory database service implementation
 */
export class InMemoryDatabaseService<T extends DatabaseRecord> extends DatabaseService<T> {
  private data: Map<string | number, T>;
  private nextId: number;
  
  constructor(collectionName: string) {
    super(collectionName);
    this.data = new Map<string | number, T>();
    this.nextId = 1;
  }
  
  /**
   * Initialize the in-memory database
   */
  public async initialize(): Promise<boolean> {
    logger.info(`Initialized in-memory database for ${this.collectionName}`);
    return true;
  }
  
  /**
   * Close connection (no-op for in-memory)
   */
  public async close(): Promise<void> {
    logger.info(`Closed in-memory database for ${this.collectionName}`);
  }
  
  /**
   * Get all records with options
   */
  public async getAll(options: QueryOptions = {}): Promise<T[]> {
    let records = Array.from(this.data.values());
    
    // Apply filtering
    if (options.filter) {
      records = records.filter(record => {
        return Object.entries(options.filter || {}).every(([key, value]) => {
          return record[key] === value;
        });
      });
    }
    
    // Apply sorting
    if (options.sortBy) {
      records.sort((a, b) => {
        const sortField = options.sortBy as keyof T;
        const sortOrder = options.sortDirection === 'desc' ? -1 : 1;
        
        if (a[sortField] < b[sortField]) return -1 * sortOrder;
        if (a[sortField] > b[sortField]) return 1 * sortOrder;
        return 0;
      });
    }
    
    // Apply pagination
    if (options.offset !== undefined) {
      records = records.slice(options.offset);
    }
    
    if (options.limit !== undefined) {
      records = records.slice(0, options.limit);
    }
    
    return records;
  }
  
  /**
   * Get a record by ID
   */
  public async getById(id: number | string): Promise<T | null> {
    const record = this.data.get(id);
    return record || null;
  }
  
  /**
   * Create a new record
   */
  public async create(data: Partial<T>): Promise<T> {
    const id = data.id !== undefined ? data.id : this.nextId++;
    const record = { ...data, id } as T;
    
    this.data.set(id, record);
    logger.debug(`Created record in ${this.collectionName} with ID: ${id}`);
    
    return record;
  }
  
  /**
   * Update a record
   */
  public async update(id: number | string, data: Partial<T>): Promise<T | null> {
    const existingRecord = this.data.get(id);
    
    if (!existingRecord) {
      return null;
    }
    
    const updatedRecord = { ...existingRecord, ...data, id };
    this.data.set(id, updatedRecord as T);
    
    logger.debug(`Updated record in ${this.collectionName} with ID: ${id}`);
    return updatedRecord as T;
  }
  
  /**
   * Delete a record
   */
  public async delete(id: number | string): Promise<boolean> {
    const result = this.data.delete(id);
    
    if (result) {
      logger.debug(`Deleted record in ${this.collectionName} with ID: ${id}`);
    }
    
    return result;
  }
  
  /**
   * Check if a record exists
   */
  public async exists(id: number | string): Promise<boolean> {
    return this.data.has(id);
  }
  
  /**
   * Count records
   */
  public async count(filter?: Record<string, any>): Promise<number> {
    if (!filter) {
      return this.data.size;
    }
    
    const records = await this.getAll({ filter });
    return records.length;
  }
} 