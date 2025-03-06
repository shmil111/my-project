/**
 * Database Configuration
 * 
 * This module provides configuration settings for database connections
 * based on environment variables.
 */

import { config } from 'dotenv';
import * as path from 'path';
import { DatabaseFactoryConfig, DatabaseImplementation } from '../services/DatabaseFactory';
import { SQLDatabaseConfig } from '../services/SQLDatabaseService';

// Load environment variables
config();

/**
 * Get the database implementation from environment
 */
export function getDatabaseImplementation(): DatabaseImplementation {
  const implementation = process.env.DB_IMPLEMENTATION || 'memory';
  
  switch (implementation.toLowerCase()) {
    case 'sqlite':
      return 'sqlite';
    case 'postgres':
    case 'postgresql':
      return 'postgres';
    case 'mysql':
      return 'mysql';
    case 'memory':
    default:
      return 'memory';
  }
}

/**
 * Get the SQL database configuration based on the implementation
 */
export function getSQLConfig(implementation: DatabaseImplementation): SQLDatabaseConfig | undefined {
  // If not using SQL, return undefined
  if (implementation === 'memory') {
    return undefined;
  }
  
  // Get common settings
  const dbName = process.env.DB_NAME || 'eve_db';
  
  // Implementation-specific configuration
  switch (implementation) {
    case 'sqlite': {
      const dbPath = process.env.DB_PATH || './data/sqlite';
      const filename = path.resolve(process.cwd(), dbPath, `${dbName}.sqlite`);
      
      // Ensure directory exists
      const fs = require('fs');
      const dir = path.dirname(filename);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      
      return {
        client: 'sqlite3',
        connection: {
          filename,
          database: dbName
        },
        useNullAsDefault: true
      };
    }
    
    case 'postgres': {
      return {
        client: 'pg',
        connection: {
          host: process.env.DB_HOST || 'localhost',
          port: parseInt(process.env.DB_PORT || '5432', 10),
          user: process.env.DB_USER || 'postgres',
          password: process.env.DB_PASSWORD || 'password',
          database: dbName
        },
        pool: {
          min: 2,
          max: 10
        }
      };
    }
    
    case 'mysql': {
      return {
        client: 'mysql2',
        connection: {
          host: process.env.DB_HOST || 'localhost',
          port: parseInt(process.env.DB_PORT || '3306', 10),
          user: process.env.DB_USER || 'root',
          password: process.env.DB_PASSWORD || 'password',
          database: dbName
        },
        pool: {
          min: 2,
          max: 10
        }
      };
    }
    
    default:
      return undefined;
  }
}

/**
 * Get the full database factory configuration
 */
export function getDatabaseConfig(): DatabaseFactoryConfig {
  const implementation = getDatabaseImplementation();
  const sqlConfig = getSQLConfig(implementation);
  
  return {
    implementation,
    sqlConfig
  };
} 