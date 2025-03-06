/**
 * SQL Database Service
 * 
 * This module provides a SQL database implementation of the DatabaseService interface.
 * It supports multiple SQL backends (SQLite, PostgreSQL, MySQL) through a connection
 * configuration.
 */

import { createLogger } from '../utils/logger';
import { DatabaseRecord, DatabaseService, QueryOptions } from './DatabaseService';
import * as Knex from 'knex';

const logger = createLogger('SQLDatabaseService');

/**
 * SQL Database configuration
 */
export interface SQLDatabaseConfig {
  client: 'sqlite3' | 'pg' | 'mysql' | 'mysql2';
  connection: {
    filename?: string;  // For SQLite
    host?: string;      // For PostgreSQL/MySQL
    port?: number;      // For PostgreSQL/MySQL
    user?: string;      // For PostgreSQL/MySQL
    password?: string;  // For PostgreSQL/MySQL
    database: string;   // For PostgreSQL/MySQL
  };
  useNullAsDefault?: boolean; // Recommended for SQLite
  pool?: {
    min?: number;
    max?: number;
  };
  migrations?: {
    directory?: string;
    tableName?: string;
  };
  uniqueKeys?: string[][]; // Array of arrays of column names for compound unique keys
}

/**
 * SQL Database Service implementation
 */
export class SQLDatabaseService<T extends DatabaseRecord> extends DatabaseService<T> {
  private knexInstance: Knex.Knex | null = null;
  private config: SQLDatabaseConfig;
  private currentTransaction: Knex.Knex.Transaction | null = null; // Renamed from transaction
  private queryCache: Map<string, { data: any; timestamp: number }> = new Map();
  private cacheTimeout: number = 5 * 60 * 1000; // 5 minutes default
  private performanceMetrics: Map<string, { count: number; totalTime: number }> = new Map();
  private healthMetrics: Map<string, {
    lastCheck: number;
    status: 'healthy' | 'warning' | 'critical';
    details: any;
  }> = new Map();
  
  /**
   * Constructs a new SQLDatabaseService.
   * @param collectionName The name of the database table.
   * @param config The database configuration.
   */
  constructor(collectionName: string, config: SQLDatabaseConfig) {
    super(collectionName);
    this.config = config;
    logger.debug(`SQLDatabaseService created for collection: ${collectionName}`);
  }
  
  /**
   * Initializes the database connection and creates the table if it doesn't exist.
   * @returns A promise that resolves to true if initialization was successful, false otherwise.
   */
  public async initialize(): Promise<boolean> {
    try {
      this.knexInstance = Knex.default(this.config);
      
      // Check if table exists, if not create it
      const tableExists = await this.knexInstance.schema.hasTable(this.collectionName);
      
      if (!tableExists) {
        await this.knexInstance.schema.createTable(this.collectionName, (table: Knex.Knex.TableBuilder) => {
          // If the id is a string, create a string primary key
          // Otherwise create an auto-incrementing integer primary key
          table.increments('id').primary();
          // We can't predict all columns, so we'll add them dynamically when records are inserted
        });
        logger.info(`Created table: ${this.collectionName}`);
      }
      
      // Add unique constraints if specified
      if (this.config.uniqueKeys && this.config.uniqueKeys.length > 0) {
        await this.addUniqueConstraints(this.config.uniqueKeys);
      }
      
      logger.info(`Initialized SQL database connection for ${this.collectionName}`);
      return true;
    } catch (error) {
      logger.error(`Failed to initialize SQL database: ${(error as Error).message}`);
      return false;
    }
  }
  
  /**
   * Adds unique constraints to the table.
   * @param uniqueKeys An array of arrays of column names for the unique constraints.
   */
  private async addUniqueConstraints(uniqueKeys: string[][]): Promise<void> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }
    
    for (const keyGroup of uniqueKeys) {
      const constraintName = `${this.collectionName}_${keyGroup.join('_')}_unique`;
      
      // Check if the constraint already exists using a raw SQL query
      let constraintExists = false;
      try {
        const client = this.knexInstance.client.config.client;
        let queryResult;
        
        if (client === 'sqlite3') {
          queryResult = await this.knexInstance.raw(`PRAGMA index_list('${this.collectionName}')`);
          constraintExists = queryResult.some((index: any) => index.name === constraintName && index.unique === 1);
        } else if (client === 'pg') {
          queryResult = await this.knexInstance.raw(`
            SELECT 1
            FROM   pg_constraint
            WHERE  conname = ?
            AND    conrelid = ?::regclass
          `, [constraintName, this.collectionName]);
          constraintExists = queryResult.rows.length > 0;
        } else if (client === 'mysql2' || client === 'mysql') {
          queryResult = await this.knexInstance.raw(`
            SHOW KEYS FROM \`${this.collectionName}\` WHERE Key_name = ?
          `, [constraintName]);
          constraintExists = queryResult[0].length > 0;
        } else {
          logger.warn(`Unsupported database client: ${client}. Cannot check for unique constraint existence.`);
          continue; // Skip adding the constraint
        }
      } catch (error) {
        logger.error(`Error checking for unique constraint existence: ${error}`);
        throw error; // Re-throw to handle upstream
      }
      
      if (!constraintExists) {
        try {
          await this.knexInstance.schema.alterTable(this.collectionName, (table: Knex.Knex.TableBuilder) => {
            table.unique(keyGroup, constraintName);
            logger.info(`Added unique constraint ${constraintName} to table ${this.collectionName}`);
          });
        } catch(error) {
          logger.error(`Could not add unique constraint: ${error}`);
          throw error; //Important to throw here, so we don't continue if the constraint isn't added.
        }
      } else {
        logger.warn(`Unique constraint ${constraintName} already exists on table ${this.collectionName}`);
      }
    }
  }
  
  /**
   * Closes the database connection.
   */
  public async close(): Promise<void> {
    if (this.knexInstance) {
      await this.knexInstance.destroy();
      this.knexInstance = null;
      logger.info(`Closed SQL database connection for ${this.collectionName}`);
    }
  }
  
  /**
   * Begins a new database transaction.
   * @throws {Error} If the database is not initialized or a transaction is already in progress.
   */
  public async beginTransaction(): Promise<void> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }
    if (this.currentTransaction) {
      throw new Error('Transaction already in progress');
    }
    this.currentTransaction = await this.knexInstance.transaction();
    logger.debug('Transaction started');
  }
  
  /**
   * Commits the current database transaction.
   * @throws {Error} If there is no transaction to commit.
   */
  public async commitTransaction(): Promise<void> {
    if (!this.currentTransaction) {
      throw new Error('No transaction to commit');
    }
    await this.currentTransaction.commit();
    this.currentTransaction = null;
    logger.debug('Transaction committed');
  }
  
  /**
   * Rolls back the current database transaction.
   * @throws {Error} If there is no transaction to rollback.
   */
  public async rollbackTransaction(): Promise<void> {
    if (!this.currentTransaction) {
      throw new Error('No transaction to rollback');
    }
    await this.currentTransaction.rollback();
    this.currentTransaction = null;
    logger.debug('Transaction rolled back');
  }
  
  /**
   * Retrieves all records from the collection.
   * @param options Query options for filtering, sorting, and pagination.
   * @returns A promise that resolves to an array of records.
   * @throws {Error} If the database is not initialized.
   */
  public async getAll(options: QueryOptions = {}): Promise<T[]> {
    try {
      const query = this.buildQuery(options);
      const records = await query.select('*');
      logger.debug(`Retrieved ${records.length} records from ${this.collectionName}`);
      return records as T[];
    } catch (error) {
      throw new Error(this.handleDatabaseError(error, 'getAll'));
    }
  }
  
  /**
   * Retrieves a single record by its ID.
   * @param id The ID of the record to retrieve.
   * @returns A promise that resolves to the record, or null if not found.
   * @throws {Error} If the database is not initialized.
   */
  public async getById(id: number | string): Promise<T | null> {
    try {
      const query = this.buildQuery()
        .where({ id })
        .first();
      
      const record = await query;
      logger.debug(`Retrieved record with ID ${id} from ${this.collectionName}`);
      return record as T || null;
    } catch (error) {
      throw new Error(this.handleDatabaseError(error, 'getById'));
    }
  }
  
  /**
   * Creates a new record in the collection.
   * @param data The data to insert.
   * @returns A promise that resolves to the created record.
   */
  public async create(data: Partial<T>): Promise<T> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }
    
    try {
      // Validate the record data
      this.validateRecord(data);
      
      // Ensure all columns exist
      await this.ensureColumnsExist(data);
      
      // Insert the record
      const [id] = await this.knexInstance(this.collectionName).insert(data);
      
      // Return the created record
      const createdRecord = await this.getById(id);
      if (!createdRecord) {
        throw new Error('Failed to retrieve created record');
      }
      
      logger.debug(`Created record with ID ${id} in ${this.collectionName}`);
      return createdRecord;
    } catch (error) {
      if (this.handleUniqueConstraintViolation(error)) {
        throw new Error('Unique constraint violation');
      }
      throw new Error(this.handleDatabaseError(error, 'create'));
    }
  }
  
  /**
   * Updates an existing record in the collection.
   * @param id The ID of the record to update.
   * @param data The data to update.
   * @returns A promise that resolves to the updated record.
   * @throws {Error} If the database is not initialized.
   */
  public async update(id: number | string, data: Partial<T>): Promise<T & { id: number | string }> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }
    
    try {
      // Validate the record data
      this.validateRecord(data);
      
      // Ensure all columns exist
      await this.ensureColumnsExist(data);
      
      // Update the record
      const updated = await this.knexInstance(this.collectionName)
        .where({ id })
        .update(data);
      
      if (!updated) {
        throw new Error('Record not found');
      }
      
      // Return the updated record
      const updatedRecord = await this.getById(id);
      if (!updatedRecord) {
        throw new Error('Failed to retrieve updated record');
      }
      
      logger.debug(`Updated record with ID ${id} in ${this.collectionName}`);
      return updatedRecord as T & { id: number | string };
    } catch (error) {
      if (this.handleUniqueConstraintViolation(error)) {
        throw new Error('Unique constraint violation');
      }
      throw new Error(this.handleDatabaseError(error, 'update'));
    }
  }
  
  /**
   * Deletes a record from the collection.
   * @param id The ID of the record to delete.
   * @returns A promise that resolves to true if the record was deleted, false otherwise.
   * @throws {Error} If the database is not initialized.
   */
  public async delete(id: number | string): Promise<boolean> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }
    
    try {
      const deleted = await this.knexInstance(this.collectionName)
        .where({ id })
        .delete();
      
      logger.debug(`Deleted record with ID ${id} from ${this.collectionName}`);
      return deleted > 0;
    } catch (error) {
      throw new Error(this.handleDatabaseError(error, 'delete'));
    }
  }
  
  /**
   * Executes multiple operations in a transaction.
   * @param operations Array of functions that take a transaction object and return a promise.
   * @returns A promise that resolves to an array of results from the operations.
   */
  public async executeTransaction<R>(operations: ((trx: Knex.Knex.Transaction) => Promise<R>)[]): Promise<R[]> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }
    
    const trx = await this.knexInstance.transaction();
    try {
      const results = await Promise.all(operations.map(op => op(trx)));
      await trx.commit();
      return results;
    } catch (error) {
      await trx.rollback();
      throw error;
    }
  }
  
  /**
   * Ensures that the table has columns for all keys present in the provided data.
   * Adds any missing columns dynamically.
   * @param data The data object.
   */
  private async ensureColumnsExist(data: Partial<T>): Promise<void> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }
    
    const columns = await this.knexInstance.table(this.collectionName).columnInfo();
    const missingColumns = Object.keys(data)
      .filter(key => key !== 'id' && !columns[key]);
    
    if (missingColumns.length > 0) {
      try { // Added try-catch for error handling
        await this.knexInstance.schema.alterTable(this.collectionName, (table) => {
          missingColumns.forEach(columnName => {
            // Infer column type based on data
            const columnValue = data[columnName];
            let columnType: Knex.Knex.ColumnBuilder;
            
            if (columnValue === null || columnValue === undefined) {
              columnType = table.string(columnName).nullable(); // Default to nullable string
            } else if (typeof columnValue === 'number') {
              // Further differentiate between integers and floating-point numbers
              if (Number.isInteger(columnValue)) {
                columnType = table.integer(columnName); // Use integer for whole numbers
              } else {
                columnType = table.float(columnName); // Use float for decimals
              }
            } else if (typeof columnValue === 'boolean') {
              columnType = table.boolean(columnName);
            } else if (typeof columnValue === 'string') {
              // Check if the string might be a date
              if (!isNaN(Date.parse(columnValue))) {
                columnType = table.dateTime(columnName); // Use dateTime for date strings
              } else {
                columnType = table.text(columnName); // Use text for long strings
              }
            } else if (columnValue instanceof Date) {
              columnType = table.dateTime(columnName); // Use dateTime for Date objects
            } else if (typeof columnValue === 'object') {
              columnType = table.json(columnName); // Use JSON for objects
            } else {
              columnType = table.string(columnName); // Default to string
            }
            
            logger.info(`Added column ${columnName} to table ${this.collectionName}`);
          });
        });
      } catch (error) {
        logger.error(`Error altering table ${this.collectionName}: ${error}`);
        throw error; // Re-throw the error to be handled by the caller
      }
    }
  }
  
  /**
   * Handles unique constraint violation errors.  This is database-specific.
   * @param error The error object.
   * @returns True if the error is a unique constraint violation, false otherwise.
   */
  private handleUniqueConstraintViolation(error: any): boolean {
    if (!this.knexInstance) {
      throw new Error ("Database not initialized");
    }
    const client = this.knexInstance.client.config.client;
    
    if (client === 'sqlite3') {
      return error.code === 'SQLITE_CONSTRAINT' && error.message.includes('UNIQUE constraint failed');
    } else if (client === 'pg') {
      return error.code === '23505' && error.detail?.includes('already exists'); // PostgreSQL unique violation error code and message
    } else if (client === 'mysql2' || client === 'mysql') {
      return error.code === 'ER_DUP_ENTRY' && error.sqlMessage?.includes('Duplicate entry'); // MySQL unique violation error code and message
    }
    return false; // Not a unique constraint violation or unknown database client
  }
  
  /**
   * Executes a raw SQL query.
   * @param sql The SQL query string.
   * @param params Optional parameters for the query.
   * @returns A promise that resolves to the query result.
   * @throws {Error} If the database is not initialized.
   */
  public async rawQuery(sql: string, params: any[] = []): Promise<any> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }
    
    let query = this.knexInstance.raw(sql, params);
    
    if(this.currentTransaction) {
      query = query.transacting(this.currentTransaction);
    }
    logger.debug(`Executing raw SQL query: ${sql} with params: ${JSON.stringify(params)}`);
    return query;
  }
  
  /**
   * Retrieves the underlying Knex instance for advanced operations.
   * @returns The Knex instance.
   * @throws {Error} If the database is not initialized.
   */
  public getKnexInstance(): Knex.Knex {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }
    
    return this.knexInstance;
  }

  /**
   * Creates multiple records in a single transaction.
   * @param dataArray Array of records to create.
   * @returns Promise that resolves to an array of created records.
   */
  public async createBatch(dataArray: Omit<T, 'id'>[]): Promise<(T & { id: number | string })[]> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    // Start a transaction for the batch operation
    const trx = await this.knexInstance.transaction();
    try {
      const createdRecords: (T & { id: number | string })[] = [];
      
      for (const data of dataArray) {
        // Check unique constraints for each record
        if (this.config.uniqueKeys && this.config.uniqueKeys.length > 0) {
          for (const keyGroup of this.config.uniqueKeys) {
            const whereClause: Record<string, any> = {};
            let hasAllKeys = true;
            for (const key of keyGroup) {
              if (data[key] !== undefined && data[key] !== null) {
                whereClause[key] = data[key];
              } else {
                hasAllKeys = false;
                break;
              }
            }
            
            if (hasAllKeys) {
              const existingRecord = await trx(this.collectionName)
                .where(whereClause)
                .first();
              
              if (existingRecord) {
                throw new Error(`A record with the same unique key '${keyGroup.join(', ')}' already exists.`);
              }
            }
          }
        }

        // Ensure columns exist for the record
        await this.ensureColumnsExist(data);

        // Insert the record
        const [newId] = await trx(this.collectionName)
          .insert(data)
          .returning('id');

        let idToReturn: number | string;
        if (typeof newId === 'object' && newId !== null) {
          if ('id' in newId) {
            idToReturn = newId.id;
          } else {
            throw new Error("Could not retrieve ID");
          }
        } else {
          idToReturn = newId;
        }

        const createdRecord = await trx(this.collectionName)
          .where({ id: idToReturn })
          .first();

        if (!createdRecord) {
          throw new Error("Could not retrieve newly created record");
        }

        createdRecords.push(createdRecord as T & { id: number | string });
      }

      await trx.commit();
      logger.debug(`Created ${createdRecords.length} records in batch`);
      return createdRecords;
    } catch (error) {
      await trx.rollback();
      throw error;
    }
  }

  /**
   * Updates multiple records in a single transaction.
   * @param updates Array of {id, data} objects to update.
   * @returns Promise that resolves to an array of updated records.
   */
  public async updateBatch(updates: { id: number | string; data: Partial<T> }[]): Promise<(T & { id: number | string })[]> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    const trx = await this.knexInstance.transaction();
    try {
      const updatedRecords: (T & { id: number | string })[] = [];

      for (const { id, data } of updates) {
        // Check if record exists
        const exists = await trx(this.collectionName)
          .where({ id })
          .first();

        if (!exists) {
          throw new Error(`Record with ID ${id} not found`);
        }

        // Ensure columns exist
        await this.ensureColumnsExist(data);

        // Remove id from data to prevent updating primary key
        const updateData = { ...data };
        delete updateData.id;

        // Update the record
        const updated = await trx(this.collectionName)
          .where({ id })
          .update(updateData);

        if (updated === 0) {
          throw new Error(`Failed to update record with ID ${id}`);
        }

        // Get the updated record
        const updatedRecord = await trx(this.collectionName)
          .where({ id })
          .first();

        if (!updatedRecord) {
          throw new Error(`Could not retrieve updated record with ID ${id}`);
        }

        updatedRecords.push(updatedRecord as T & { id: number | string });
      }

      await trx.commit();
      logger.debug(`Updated ${updatedRecords.length} records in batch`);
      return updatedRecords;
    } catch (error) {
      await trx.rollback();
      throw error;
    }
  }

  /**
   * Deletes multiple records in a single transaction.
   * @param ids Array of record IDs to delete.
   * @returns Promise that resolves to the number of deleted records.
   */
  public async deleteBatch(ids: (number | string)[]): Promise<number> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    const trx = await this.knexInstance.transaction();
    try {
      const deleted = await trx(this.collectionName)
        .whereIn('id', ids)
        .delete();

      await trx.commit();
      logger.debug(`Deleted ${deleted} records in batch`);
      return deleted;
    } catch (error) {
      await trx.rollback();
      throw error;
    }
  }

  /**
   * Builds a query with the given options.
   * @param options Query options for filtering, sorting, and pagination.
   * @returns A Knex query builder.
   */
  private buildQuery(options: QueryOptions = {}): Knex.Knex.QueryBuilder {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    let query = this.knexInstance(this.collectionName);

    if (this.currentTransaction) {
      query = query.transacting(this.currentTransaction);
    }

    // Apply filtering
    if (options.filter) {
      if (typeof options.filter === 'function') {
        query = query.where(options.filter);
      } else {
        query = query.where(options.filter);
      }
    }

    // Apply sorting
    if (options.sortBy) {
      const direction = options.sortDirection === 'desc' ? 'desc' : 'asc';
      query = query.orderBy(options.sortBy, direction);
    }

    // Apply pagination
    if (options.offset !== undefined) {
      query = query.offset(options.offset);
    }

    if (options.limit !== undefined) {
      query = query.limit(options.limit);
    }

    return query;
  }

  /**
   * Handles database errors and provides meaningful error messages.
   * @param error The error object.
   * @param operation The operation that failed.
   * @returns A formatted error message.
   */
  private handleDatabaseError(error: any, operation: string): string {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    const client = this.knexInstance.client.config.client;
    let errorMessage = `Database error during ${operation}: `;

    // Handle connection errors
    if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
      errorMessage += 'Could not connect to the database. Please check your connection settings.';
    }
    // Handle authentication errors
    else if (error.code === 'ER_ACCESS_DENIED_ERROR' || error.code === '28P01') {
      errorMessage += 'Authentication failed. Please check your credentials.';
    }
    // Handle table not found errors
    else if (error.code === 'ER_NO_SUCH_TABLE' || error.code === '42P01') {
      errorMessage += `Table '${this.collectionName}' does not exist.`;
    }
    // Handle column not found errors
    else if (error.code === 'ER_BAD_FIELD_ERROR' || error.code === '42703') {
      errorMessage += 'One or more columns do not exist in the table.';
    }
    // Handle syntax errors
    else if (error.code === 'ER_SYNTAX_ERROR' || error.code === '42601') {
      errorMessage += 'Invalid SQL syntax.';
    }
    // Handle unique constraint violations
    else if (this.handleUniqueConstraintViolation(error)) {
      errorMessage += 'A record with the same unique key already exists.';
    }
    // Handle foreign key constraint violations
    else if (error.code === 'ER_NO_REFERENCED_ROW' || error.code === '23503') {
      errorMessage += 'Referenced record does not exist.';
    }
    // Default error message
    else {
      errorMessage += error.message || 'Unknown database error occurred.';
    }

    logger.error(errorMessage);
    return errorMessage;
  }

  /**
   * Validates a record against the schema with advanced validation rules.
   * @param data The record data to validate.
   * @param schema Optional schema definition for validation.
   * @throws {Error} If the record is invalid.
   */
  private validateRecord(data: Partial<T>, schema?: Record<string, {
    type: 'string' | 'number' | 'boolean' | 'date' | 'object' | 'array';
    required?: boolean;
    min?: number;
    max?: number;
    pattern?: RegExp;
    enum?: any[];
    custom?: (value: any) => boolean;
  }>): void {
    if (!data) {
      throw new Error('Record data is required');
    }

    if (schema) {
      for (const [field, rules] of Object.entries(schema)) {
        const value = data[field];
        
        // Check required fields
        if (rules.required && (value === undefined || value === null)) {
          throw new Error(`Field ${field} is required`);
        }

        if (value !== undefined && value !== null) {
          // Type validation
          switch (rules.type) {
            case 'string':
              if (typeof value !== 'string') {
                throw new Error(`Field ${field} must be a string`);
              }
              if (rules.min && value.length < rules.min) {
                throw new Error(`Field ${field} must be at least ${rules.min} characters`);
              }
              if (rules.max && value.length > rules.max) {
                throw new Error(`Field ${field} must be at most ${rules.max} characters`);
              }
              if (rules.pattern && !rules.pattern.test(value)) {
                throw new Error(`Field ${field} does not match required pattern`);
              }
              break;

            case 'number':
              if (typeof value !== 'number') {
                throw new Error(`Field ${field} must be a number`);
              }
              if (rules.min !== undefined && value < rules.min) {
                throw new Error(`Field ${field} must be at least ${rules.min}`);
              }
              if (rules.max !== undefined && value > rules.max) {
                throw new Error(`Field ${field} must be at most ${rules.max}`);
              }
              break;

            case 'boolean':
              if (typeof value !== 'boolean') {
                throw new Error(`Field ${field} must be a boolean`);
              }
              break;

            case 'date':
              if (!(value instanceof Date) && isNaN(Date.parse(value))) {
                throw new Error(`Field ${field} must be a valid date`);
              }
              break;

            case 'object':
              if (typeof value !== 'object' || value === null) {
                throw new Error(`Field ${field} must be an object`);
              }
              break;

            case 'array':
              if (!Array.isArray(value)) {
                throw new Error(`Field ${field} must be an array`);
              }
              break;
          }

          // Enum validation
          if (rules.enum && !rules.enum.includes(value)) {
            throw new Error(`Field ${field} must be one of: ${rules.enum.join(', ')}`);
          }

          // Custom validation
          if (rules.custom && !rules.custom(value)) {
            throw new Error(`Field ${field} failed custom validation`);
          }
        }
      }
    }
  }

  /**
   * Gets the column information for the table.
   * @returns Promise that resolves to the column information.
   */
  public async getColumnInfo(): Promise<Record<string, Knex.Knex.ColumnInfo>> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    try {
      const columns = await this.knexInstance.table(this.collectionName).columnInfo();
      return columns;
    } catch (error) {
      throw new Error(this.handleDatabaseError(error, 'getColumnInfo'));
    }
  }

  /**
   * Gets the table schema information.
   * @returns Promise that resolves to the table schema information.
   */
  public async getTableSchema(): Promise<{
    columns: Record<string, Knex.Knex.ColumnInfo>;
    indexes: any[];
    constraints: any[];
  }> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    try {
      const client = this.knexInstance.client.config.client;
      const columns = await this.getColumnInfo();
      let indexes: any[] = [];
      let constraints: any[] = [];

      // Get indexes and constraints based on the database client
      if (client === 'pg') {
        const indexResult = await this.knexInstance.raw(`
          SELECT
            i.relname as index_name,
            a.attname as column_name,
            ix.indisunique as is_unique
          FROM
            pg_class t,
            pg_class i,
            pg_index ix,
            pg_attribute a
          WHERE
            t.oid = ix.indrelid
            AND i.oid = ix.indexrelid
            AND a.attrelid = t.oid
            AND a.attnum = ANY(ix.indkey)
            AND t.relkind = 'r'
            AND t.relname = ?
        `, [this.collectionName]);

        indexes = indexResult.rows;

        const constraintResult = await this.knexInstance.raw(`
          SELECT
            conname as constraint_name,
            pg_get_constraintdef(oid) as constraint_definition
          FROM
            pg_constraint
          WHERE
            conrelid = ?::regclass
        `, [this.collectionName]);

        constraints = constraintResult.rows;
      } else if (client === 'mysql2' || client === 'mysql') {
        const indexResult = await this.knexInstance.raw(`
          SHOW INDEX FROM \`${this.collectionName}\`
        `);
        indexes = indexResult[0];

        const constraintResult = await this.knexInstance.raw(`
          SELECT
            CONSTRAINT_NAME as constraint_name,
            CONSTRAINT_TYPE as constraint_type
          FROM
            information_schema.TABLE_CONSTRAINTS
          WHERE
            TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = ?
        `, [this.collectionName]);
        constraints = constraintResult[0];
      }

      return {
        columns,
        indexes,
        constraints
      };
    } catch (error) {
      throw new Error(this.handleDatabaseError(error, 'getTableSchema'));
    }
  }

  /**
   * Executes a complex query with joins and conditions.
   * @param options Query options including joins, conditions, and selections.
   * @returns Promise that resolves to the query results.
   */
  public async complexQuery(options: {
    joins?: Array<{
      table: string;
      type?: 'inner' | 'left' | 'right' | 'full';
      on: string | ((builder: Knex.Knex.QueryBuilder) => void);
    }>;
    conditions?: Array<{
      column: string;
      operator: string;
      value: any;
    }>;
    selections?: string[];
    groupBy?: string[];
    having?: Array<{
      column: string;
      operator: string;
      value: any;
    }>;
    orderBy?: Array<{
      column: string;
      direction?: 'asc' | 'desc';
    }>;
    limit?: number;
    offset?: number;
  }): Promise<any[]> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    try {
      let query = this.knexInstance(this.collectionName);

      // Apply joins
      if (options.joins) {
        for (const join of options.joins) {
          const joinType = join.type || 'inner';
          query = query[`${joinType}Join`](join.table, join.on);
        }
      }

      // Apply conditions
      if (options.conditions) {
        for (const condition of options.conditions) {
          query = query.where(condition.column, condition.operator, condition.value);
        }
      }

      // Apply selections
      if (options.selections) {
        query = query.select(options.selections);
      } else {
        query = query.select('*');
      }

      // Apply group by
      if (options.groupBy) {
        query = query.groupBy(options.groupBy);
      }

      // Apply having
      if (options.having) {
        for (const having of options.having) {
          query = query.having(having.column, having.operator, having.value);
        }
      }

      // Apply order by
      if (options.orderBy) {
        for (const order of options.orderBy) {
          query = query.orderBy(order.column, order.direction || 'asc');
        }
      }

      // Apply pagination
      if (options.offset !== undefined) {
        query.offset(options.offset);
      }
      if (options.limit !== undefined) {
        query.limit(options.limit);
      }

      // Apply transaction if exists
      if (this.currentTransaction) {
        query = query.transacting(this.currentTransaction);
      }

      const results = await query;
      logger.debug(`Executed complex query returning ${results.length} results`);
      return results;
    } catch (error) {
      throw new Error(this.handleDatabaseError(error, 'complexQuery'));
    }
  }

  /**
   * Runs a database migration.
   * @param migrationFn Function that performs the migration.
   * @returns Promise that resolves when the migration is complete.
   */
  public async migrate(migrationFn: (knex: Knex.Knex) => Promise<void>): Promise<void> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    const trx = await this.knexInstance.transaction();
    try {
      await migrationFn(trx);
      await trx.commit();
      logger.info('Migration completed successfully');
    } catch (error) {
      await trx.rollback();
      throw new Error(this.handleDatabaseError(error, 'migrate'));
    }
  }

  /**
   * Configures the connection pool settings.
   * @param settings Pool configuration settings.
   */
  public async configurePool(settings: {
    min?: number;
    max?: number;
    idleTimeoutMillis?: number;
    acquireTimeoutMillis?: number;
    createTimeoutMillis?: number;
    destroyTimeoutMillis?: number;
    reapIntervalMillis?: number;
    createRetryIntervalMillis?: number;
  }): Promise<void> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    try {
      await this.knexInstance.destroy();
      this.config.pool = settings;
      this.knexInstance = Knex.default(this.config);
      logger.info('Connection pool configured successfully');
    } catch (error) {
      throw new Error(this.handleDatabaseError(error, 'configurePool'));
    }
  }

  /**
   * Gets the current connection pool status.
   * @returns Promise that resolves to the pool status information.
   */
  public async getPoolStatus(): Promise<{
    total: number;
    idle: number;
    waiting: number;
    expired: number;
  }> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    try {
      const pool = (this.knexInstance.client as any).pool;
      if (!pool) {
        throw new Error('Connection pool not available');
      }

      return {
        total: pool.totalCount,
        idle: pool.idleCount,
        waiting: pool.waitingCount,
        expired: pool.expiredCount
      };
    } catch (error) {
      throw new Error(this.handleDatabaseError(error, 'getPoolStatus'));
    }
  }

  /**
   * Sets the cache timeout in milliseconds.
   * @param timeout Timeout in milliseconds.
   */
  public setCacheTimeout(timeout: number): void {
    this.cacheTimeout = timeout;
    logger.info(`Cache timeout set to ${timeout}ms`);
  }

  /**
   * Clears the query cache.
   */
  public clearCache(): void {
    this.queryCache.clear();
    logger.info('Query cache cleared');
  }

  /**
   * Gets performance metrics for database operations.
   * @returns Object containing performance metrics.
   */
  public getPerformanceMetrics(): Record<string, { count: number; averageTime: number }> {
    const metrics: Record<string, { count: number; averageTime: number }> = {};
    
    for (const [operation, data] of this.performanceMetrics) {
      metrics[operation] = {
        count: data.count,
        averageTime: data.totalTime / data.count
      };
    }
    
    return metrics;
  }

  /**
   * Creates a backup of the database table.
   * @param backupPath Path where the backup should be stored.
   * @returns Promise that resolves when backup is complete.
   */
  public async createBackup(backupPath: string): Promise<void> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    const trx = await this.knexInstance.transaction();
    try {
      const client = this.knexInstance.client.config.client;
      let backupQuery: string;

      if (client === 'sqlite3') {
        backupQuery = `VACUUM INTO '${backupPath}'`;
      } else if (client === 'pg') {
        backupQuery = `COPY ${this.collectionName} TO '${backupPath}' WITH CSV HEADER`;
      } else if (client === 'mysql2' || client === 'mysql') {
        backupQuery = `SELECT * INTO OUTFILE '${backupPath}' FROM ${this.collectionName}`;
      } else {
        throw new Error(`Backup not supported for client: ${client}`);
      }

      await trx.raw(backupQuery);
      await trx.commit();
      logger.info(`Backup created successfully at ${backupPath}`);
    } catch (error) {
      await trx.rollback();
      throw new Error(this.handleDatabaseError(error, 'createBackup'));
    }
  }

  /**
   * Restores the database table from a backup.
   * @param backupPath Path to the backup file.
   * @returns Promise that resolves when restore is complete.
   */
  public async restoreBackup(backupPath: string): Promise<void> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    const trx = await this.knexInstance.transaction();
    try {
      const client = this.knexInstance.client.config.client;
      let restoreQuery: string;

      if (client === 'sqlite3') {
        restoreQuery = `RESTORE FROM '${backupPath}'`;
      } else if (client === 'pg') {
        restoreQuery = `COPY ${this.collectionName} FROM '${backupPath}' WITH CSV HEADER`;
      } else if (client === 'mysql2' || client === 'mysql') {
        restoreQuery = `LOAD DATA INFILE '${backupPath}' INTO TABLE ${this.collectionName}`;
      } else {
        throw new Error(`Restore not supported for client: ${client}`);
      }

      await trx.raw(restoreQuery);
      await trx.commit();
      logger.info(`Backup restored successfully from ${backupPath}`);
    } catch (error) {
      await trx.rollback();
      throw new Error(this.handleDatabaseError(error, 'restoreBackup'));
    }
  }

  /**
   * Executes a query with caching.
   * @param key Cache key for the query.
   * @param queryFn Function that returns the query promise.
   * @returns Promise that resolves to the query result.
   */
  private async executeWithCache<T>(key: string, queryFn: () => Promise<T>): Promise<T> {
    const cached = this.queryCache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      logger.debug(`Cache hit for key: ${key}`);
      return cached.data;
    }

    const startTime = Date.now();
    const result = await queryFn();
    const endTime = Date.now();

    // Update performance metrics
    const metrics = this.performanceMetrics.get(key) || { count: 0, totalTime: 0 };
    metrics.count++;
    metrics.totalTime += endTime - startTime;
    this.performanceMetrics.set(key, metrics);

    // Update cache
    this.queryCache.set(key, {
      data: result,
      timestamp: Date.now()
    });

    logger.debug(`Cache miss for key: ${key}, query took ${endTime - startTime}ms`);
    return result;
  }

  /**
   * Creates a full-text search index on specified columns.
   * @param columns Array of column names to include in the full-text index.
   * @returns Promise that resolves when the index is created.
   */
  public async createFullTextIndex(columns: string[]): Promise<void> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    const trx = await this.knexInstance.transaction();
    try {
      const client = this.knexInstance.client.config.client;
      const indexName = `${this.collectionName}_${columns.join('_')}_fts`;

      if (client === 'pg') {
        // PostgreSQL full-text search
        await trx.raw(`
          CREATE INDEX ${indexName} ON ${this.collectionName} 
          USING gin(to_tsvector('english', ${columns.map(col => `COALESCE(${col}::text, '')`).join(" || ' ' || ")}))
        `);
      } else if (client === 'mysql2' || client === 'mysql') {
        // MySQL full-text search
        await trx.raw(`
          ALTER TABLE ${this.collectionName} 
          ADD FULLTEXT INDEX ${indexName} (${columns.join(', ')})
        `);
      } else {
        throw new Error(`Full-text search not supported for client: ${client}`);
      }

      await trx.commit();
      logger.info(`Created full-text index ${indexName} on columns: ${columns.join(', ')}`);
    } catch (error) {
      await trx.rollback();
      throw new Error(this.handleDatabaseError(error, 'createFullTextIndex'));
    }
  }

  /**
   * Performs a full-text search on indexed columns.
   * @param searchTerm The search term to look for.
   * @param options Search options including ranking and pagination.
   * @returns Promise that resolves to matching records with relevance scores.
   */
  public async fullTextSearch(searchTerm: string, options: {
    columns?: string[];
    minScore?: number;
    limit?: number;
    offset?: number;
  } = {}): Promise<Array<T & { score: number }>> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    try {
      const client = this.knexInstance.client.config.client;
      let query: Knex.Knex.QueryBuilder;

      if (client === 'pg') {
        // PostgreSQL full-text search
        const searchVector = options.columns
          ? options.columns.map(col => `to_tsvector('english', COALESCE(${col}::text, ''))`).join(" || ' ' || ")
          : `to_tsvector('english', ${Object.keys(this.knexInstance.table(this.collectionName).columnInfo())
              .filter(col => col !== 'id')
              .map(col => `COALESCE(${col}::text, '')`)
              .join(" || ' ' || ")}`;

        query = this.knexInstance(this.collectionName)
          .select('*')
          .select(this.knexInstance.raw(`ts_rank_cd(${searchVector}, to_tsquery('english', ?)) as score`, [searchTerm]))
          .where(this.knexInstance.raw(`${searchVector} @@ to_tsquery('english', ?)`, [searchTerm]))
          .orderBy('score', 'desc');

        if (options.minScore) {
          query.having('score', '>=', options.minScore);
        }
      } else if (client === 'mysql2' || client === 'mysql') {
        // MySQL full-text search
        const columns = options.columns || Object.keys(this.knexInstance.table(this.collectionName).columnInfo())
          .filter(col => col !== 'id');
        
        query = this.knexInstance(this.collectionName)
          .select('*')
          .select(this.knexInstance.raw(`MATCH(${columns.join(', ')}) AGAINST(? IN BOOLEAN MODE) as score`, [searchTerm]))
          .where(this.knexInstance.raw(`MATCH(${columns.join(', ')}) AGAINST(? IN BOOLEAN MODE)`, [searchTerm]))
          .orderBy('score', 'desc');

        if (options.minScore) {
          query.having('score', '>=', options.minScore);
        }
      } else {
        throw new Error(`Full-text search not supported for client: ${client}`);
      }

      if (options.offset !== undefined) {
        query.offset(options.offset);
      }
      if (options.limit !== undefined) {
        query.limit(options.limit);
      }

      const results = await query;
      logger.debug(`Full-text search returned ${results.length} results`);
      return results as Array<T & { score: number }>;
    } catch (error) {
      throw new Error(this.handleDatabaseError(error, 'fullTextSearch'));
    }
  }

  /**
   * Creates an advanced index with specific options.
   * @param columns Array of column names to include in the index.
   * @param options Index options including type and properties.
   * @returns Promise that resolves when the index is created.
   */
  public async createAdvancedIndex(columns: string[], options: {
    type?: 'btree' | 'hash' | 'gist' | 'gin';
    unique?: boolean;
    partial?: string;
    include?: string[];
  } = {}): Promise<void> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    const trx = await this.knexInstance.transaction();
    try {
      const client = this.knexInstance.client.config.client;
      const indexName = `${this.collectionName}_${columns.join('_')}_idx`;

      if (client === 'pg') {
        // PostgreSQL advanced indexing
        let indexQuery = `CREATE ${options.unique ? 'UNIQUE ' : ''}INDEX ${indexName} ON ${this.collectionName} `;
        if (options.type) {
          indexQuery += `USING ${options.type} `;
        }
        indexQuery += `(${columns.join(', ')})`;
        
        if (options.include) {
          indexQuery += ` INCLUDE (${options.include.join(', ')})`;
        }
        
        if (options.partial) {
          indexQuery += ` WHERE ${options.partial}`;
        }

        await trx.raw(indexQuery);
      } else if (client === 'mysql2' || client === 'mysql') {
        // MySQL advanced indexing
        let indexQuery = `CREATE ${options.unique ? 'UNIQUE ' : ''}INDEX ${indexName} ON ${this.collectionName} `;
        if (options.type) {
          indexQuery += `USING ${options.type} `;
        }
        indexQuery += `(${columns.join(', ')})`;
        
        if (options.partial) {
          indexQuery += ` WHERE ${options.partial}`;
        }

        await trx.raw(indexQuery);
      } else {
        throw new Error(`Advanced indexing not supported for client: ${client}`);
      }

      await trx.commit();
      logger.info(`Created advanced index ${indexName} on columns: ${columns.join(', ')}`);
    } catch (error) {
      await trx.rollback();
      throw new Error(this.handleDatabaseError(error, 'createAdvancedIndex'));
    }
  }

  /**
   * Adds query optimization hints to a query.
   * @param query The query builder to optimize.
   * @param hints Optimization hints to apply.
   * @returns The optimized query builder.
   */
  private addQueryHints(query: Knex.Knex.QueryBuilder, hints: {
    index?: string;
    forceIndex?: string;
    ignoreIndex?: string;
    limit?: number;
    timeout?: number;
  }): Knex.Knex.QueryBuilder {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    const client = this.knexInstance.client.config.client;
    
    if (client === 'pg') {
      if (hints.index) {
        query.hint(hints.index);
      }
      if (hints.timeout) {
        query.timeout(hints.timeout);
      }
    } else if (client === 'mysql2' || client === 'mysql') {
      let hintString = '';
      if (hints.forceIndex) {
        hintString += `FORCE INDEX (${hints.forceIndex})`;
      }
      if (hints.ignoreIndex) {
        hintString += `IGNORE INDEX (${hints.ignoreIndex})`;
      }
      if (hintString) {
        query.hint(hintString);
      }
      if (hints.timeout) {
        query.timeout(hints.timeout);
      }
    }

    return query;
  }

  /**
   * Checks the health of the database connection and table.
   * @param options Health check options.
   * @returns Promise that resolves to health check results.
   */
  public async checkHealth(options: {
    checkConnections?: boolean;
    checkTableSize?: boolean;
    checkIndexes?: boolean;
    checkConstraints?: boolean;
  } = {}): Promise<{
    status: 'healthy' | 'warning' | 'critical';
    details: Record<string, any>;
  }> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }

    try {
      const client = this.knexInstance.client.config.client;
      const details: Record<string, any> = {};
      let status: 'healthy' | 'warning' | 'critical' = 'healthy';

      // Check connection pool
      if (options.checkConnections) {
        const poolStatus = await this.getPoolStatus();
        details.connections = poolStatus;
        
        if (poolStatus.waiting > 10 || poolStatus.expired > 5) {
          status = 'warning';
        }
        if (poolStatus.waiting > 50 || poolStatus.expired > 20) {
          status = 'critical';
        }
      }

      // Check table size and growth
      if (options.checkTableSize) {
        let sizeQuery: string;
        if (client === 'pg') {
          sizeQuery = `
            SELECT pg_size_pretty(pg_total_relation_size($1)) as size,
                   pg_size_pretty(pg_relation_size($1)) as table_size,
                   pg_size_pretty(pg_total_relation_size($1) - pg_relation_size($1)) as index_size
          `;
        } else if (client === 'mysql2' || client === 'mysql') {
          sizeQuery = `
            SELECT data_length + index_length as size,
                   data_length as table_size,
                   index_length as index_size
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name = ?
          `;
        } else {
          sizeQuery = `PRAGMA page_count, page_size`;
        }

        const sizeResult = await this.knexInstance.raw(sizeQuery, [this.collectionName]);
        details.size = sizeResult.rows?.[0] || sizeResult[0];
      }

      // Check index usage
      if (options.checkIndexes) {
        let indexQuery: string;
        if (client === 'pg') {
          indexQuery = `
            SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE tablename = ?
          `;
        } else if (client === 'mysql2' || client === 'mysql') {
          indexQuery = `
            SELECT index_name, stat_name, stat_value
            FROM mysql.index_statistics
            WHERE table_schema = DATABASE()
            AND table_name = ?
          `;
        } else {
          indexQuery = `PRAGMA index_info(${this.collectionName})`;
        }

        const indexResult = await this.knexInstance.raw(indexQuery, [this.collectionName]);
        details.indexes = indexResult.rows || indexResult;
      }

      // Check constraints
      if (options.checkConstraints) {
        const schema = await this.getTableSchema();
        details.constraints = schema.constraints;
      }

      // Update health metrics
      this.healthMetrics.set('lastCheck', {
        lastCheck: Date.now(),
        status,
        details
      });

      return { status, details };
    } catch (error) {
      throw new Error(this.handleDatabaseError(error, 'checkHealth'));
    }
  }

  /**
   * Gets the current health status of the database.
   * @returns The current health status and details.
   */
  public getHealthStatus(): {
    status: 'healthy' | 'warning' | 'critical';
    details: any;
    lastCheck: number;
  } | null {
    const lastCheck = this.healthMetrics.get('lastCheck');
    if (!lastCheck) {
      return null;
    }

    return {
      status: lastCheck.status,
      details: lastCheck.details,
      lastCheck: lastCheck.lastCheck
    };
  }

  /**
   * Check if a record exists
   * @param id The ID of the record to check
   * @returns A promise that resolves to a boolean indicating if the record exists
   */
  public async exists(id: number | string): Promise<boolean> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }
    
    try {
      const result = await this.knexInstance(this.collectionName)
        .where('id', id)
        .first();
      
      return !!result;
    } catch (error) {
      throw new Error(this.handleDatabaseError(error, 'exists'));
    }
  }
  
  /**
   * Count records that match a filter
   * @param filter Optional filter to count specific records
   * @returns A promise that resolves to the count of records
   */
  public async count(filter?: Record<string, any>): Promise<number> {
    if (!this.knexInstance) {
      throw new Error('Database not initialized');
    }
    
    try {
      let query = this.knexInstance(this.collectionName);
      
      if (filter) {
        Object.entries(filter).forEach(([key, value]) => {
          query = query.where(key, value);
        });
      }
      
      const result = await query.count('id as count').first();
      return result ? Number(result.count) : 0;
    } catch (error) {
      throw new Error(this.handleDatabaseError(error, 'count'));
    }
  }
} 