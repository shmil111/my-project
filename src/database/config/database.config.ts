import { SQLDatabaseConfig } from '../../services/SQLDatabaseService';

export const databaseConfig: SQLDatabaseConfig = {
  client: 'sqlite3',
  connection: {
    filename: './database.sqlite3'
  },
  useNullAsDefault: true,
  pool: {
    min: 2,
    max: 10
  },
  migrations: {
    directory: './src/database/migrations',
    tableName: 'knex_migrations'
  }
};

export const testDatabaseConfig: SQLDatabaseConfig = {
  client: 'sqlite3',
  connection: {
    filename: './test-database.sqlite3'
  },
  useNullAsDefault: true,
  pool: {
    min: 1,
    max: 3
  }
};

export const productionDatabaseConfig: SQLDatabaseConfig = {
  client: 'pg',
  connection: {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || '',
    database: process.env.DB_NAME || 'production_db'
  },
  pool: {
    min: 5,
    max: 20
  },
  migrations: {
    directory: './src/database/migrations',
    tableName: 'knex_migrations'
  }
}; 