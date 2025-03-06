import { SQLDatabaseService } from '../../services/SQLDatabaseService';
import { DatabaseRecord, QueryOptions } from '../../services/DatabaseService';

export abstract class BaseRepository<T extends DatabaseRecord> {
  protected dbService: SQLDatabaseService<T>;

  constructor(collectionName: string, config: any) {
    this.dbService = new SQLDatabaseService<T>(collectionName, config);
  }

  /**
   * Initialize the database connection
   */
  async initialize(): Promise<boolean> {
    return this.dbService.initialize();
  }

  /**
   * Close the database connection
   */
  async close(): Promise<void> {
    await this.dbService.close();
  }

  /**
   * Get all records with optional filtering and pagination
   */
  async getAll(options: QueryOptions = {}): Promise<T[]> {
    return this.dbService.getAll(options);
  }

  /**
   * Get a single record by ID
   */
  async getById(id: number | string): Promise<T | null> {
    return this.dbService.getById(id);
  }

  /**
   * Get multiple records by their IDs
   */
  async getByIds(ids: (number | string)[]): Promise<T[]> {
    return this.dbService.getByIds(ids);
  }

  /**
   * Create a new record
   */
  async create(data: Omit<T, 'id'>): Promise<T & { id: number | string }> {
    return this.dbService.create(data);
  }

  /**
   * Update an existing record
   */
  async update(id: number | string, data: Partial<T>): Promise<T & { id: number | string }> {
    return this.dbService.update(id, data);
  }

  /**
   * Delete a record
   */
  async delete(id: number | string): Promise<boolean> {
    return this.dbService.delete(id);
  }

  /**
   * Check if a record exists
   */
  async exists(id: number | string): Promise<boolean> {
    return this.dbService.exists(id);
  }

  /**
   * Count records with optional filtering
   */
  async count(filter?: Record<string, any>): Promise<number> {
    return this.dbService.count(filter);
  }

  /**
   * Create multiple records in a transaction
   */
  async createBatch(dataArray: Omit<T, 'id'>[]): Promise<(T & { id: number | string })[]> {
    return this.dbService.createBatch(dataArray);
  }

  /**
   * Update multiple records in a transaction
   */
  async updateBatch(updates: { id: number | string; data: Partial<T> }[]): Promise<(T & { id: number | string })[]> {
    return this.dbService.updateBatch(updates);
  }

  /**
   * Delete multiple records in a transaction
   */
  async deleteBatch(ids: (number | string)[]): Promise<number> {
    return this.dbService.deleteBatch(ids);
  }

  /**
   * Begin a transaction
   */
  async beginTransaction(): Promise<void> {
    await this.dbService.beginTransaction();
  }

  /**
   * Commit the current transaction
   */
  async commitTransaction(): Promise<void> {
    await this.dbService.commitTransaction();
  }

  /**
   * Rollback the current transaction
   */
  async rollbackTransaction(): Promise<void> {
    await this.dbService.rollbackTransaction();
  }

  /**
   * Execute a raw SQL query
   */
  async rawQuery(sql: string, params: any[] = []): Promise<any> {
    return this.dbService.rawQuery(sql, params);
  }

  /**
   * Get the underlying database service instance
   */
  getDatabaseService(): SQLDatabaseService<T> {
    return this.dbService;
  }
} 