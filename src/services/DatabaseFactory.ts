/**
 * Database Factory
 * 
 * This module provides a factory for creating database service instances
 * with different implementations (in-memory, SQL, etc.)
 */

import { DatabaseRecord, DatabaseService } from './DatabaseService';
import { InMemoryDatabaseService } from './DatabaseService';
import { SQLDatabaseService, SQLDatabaseConfig } from './SQLDatabaseService';
import { createLogger } from '../utils/logger';

const logger = createLogger('DatabaseFactory');

/**
 * Database implementation type
 */
export type DatabaseImplementation = 'memory' | 'sqlite' | 'postgres' | 'mysql';

/**
 * Database factory configuration
 */
export interface DatabaseFactoryConfig {
  implementation: DatabaseImplementation;
  sqlConfig?: SQLDatabaseConfig;
}

/**
 * Database factory class
 */
export class DatabaseFactory {
  /**
   * Create a database service instance
   */
  public static createDatabaseService<T extends DatabaseRecord>(
    collectionName: string,
    config: DatabaseFactoryConfig
  ): DatabaseService<T> {
    logger.info(`Creating database service for ${collectionName} using ${config.implementation} implementation`);
    
    switch (config.implementation) {
      case 'memory':
        return new InMemoryDatabaseService<T>(collectionName);
      
      case 'sqlite':
        if (!config.sqlConfig) {
          throw new Error('SQL configuration is required for SQLite implementation');
        }
        return new SQLDatabaseService<T>(collectionName, {
          ...config.sqlConfig,
          client: 'sqlite3',
          useNullAsDefault: true
        });
      
      case 'postgres':
        if (!config.sqlConfig) {
          throw new Error('SQL configuration is required for PostgreSQL implementation');
        }
        return new SQLDatabaseService<T>(collectionName, {
          ...config.sqlConfig,
          client: 'pg'
        });
      
      case 'mysql':
        if (!config.sqlConfig) {
          throw new Error('SQL configuration is required for MySQL implementation');
        }
        return new SQLDatabaseService<T>(collectionName, {
          ...config.sqlConfig,
          client: 'mysql2'
        });
      
      default:
        logger.warn(`Unknown implementation: ${config.implementation}, falling back to in-memory database`);
        return new InMemoryDatabaseService<T>(collectionName);
    }
  }
} 