import { Knex } from 'knex';
import { databaseConfig } from '../config/database.config';
import * as fs from 'fs';
import * as path from 'path';

export interface MigrationStatus {
  name: string;
  batch: number;
  migration_time: Date;
}

export class MigrationManager {
  private knex: Knex;
  private migrationsDir: string;

  constructor() {
    this.knex = require('knex')(databaseConfig);
    this.migrationsDir = path.resolve(__dirname);
  }

  /**
   * Run all pending migrations
   */
  async migrate(): Promise<void> {
    try {
      await this.knex.migrate.latest();
      console.log('Migrations completed successfully');
    } catch (error) {
      console.error('Migration failed:', error);
      throw error;
    }
  }

  /**
   * Rollback the last batch of migrations
   */
  async rollback(): Promise<void> {
    try {
      await this.knex.migrate.rollback();
      console.log('Rollback completed successfully');
    } catch (error) {
      console.error('Rollback failed:', error);
      throw error;
    }
  }

  /**
   * Reset the database by rolling back all migrations and then running them again
   */
  async reset(): Promise<void> {
    try {
      await this.knex.migrate.rollback(undefined, true);
      await this.knex.migrate.latest();
      console.log('Database reset completed successfully');
    } catch (error) {
      console.error('Database reset failed:', error);
      throw error;
    }
  }

  /**
   * Get the current migration status
   */
  async getMigrationStatus(): Promise<MigrationStatus[]> {
    try {
      const status = await this.knex.migrate.list();
      return status.map(item => ({
        ...item,
        migration_time: new Date(item.migration_time)
      }));
    } catch (error) {
      console.error('Failed to get migration status:', error);
      throw error;
    }
  }

  /**
   * Create a new migration file
   */
  async createMigration(name: string): Promise<string> {
    const timestamp = new Date().toISOString().replace(/[^0-9]/g, '').slice(0, 14);
    const fileName = `${timestamp}_${name}.ts`;
    const filePath = path.join(this.migrationsDir, fileName);

    const template = `import { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  // Add your migration logic here
}

export async function down(knex: Knex): Promise<void> {
  // Add your rollback logic here
}
`;

    fs.writeFileSync(filePath, template);
    return fileName;
  }

  /**
   * Check if there are any pending migrations
   */
  async hasPendingMigrations(): Promise<boolean> {
    const status = await this.getMigrationStatus();
    const files = fs.readdirSync(this.migrationsDir)
      .filter(file => file.endsWith('.ts') && file !== 'MigrationManager.ts');
    
    return files.length > status.length;
  }

  /**
   * Get the current migration batch number
   */
  async getCurrentBatch(): Promise<number> {
    const status = await this.getMigrationStatus();
    return status.length > 0 ? status[0].batch : 0;
  }

  /**
   * Close the database connection
   */
  async close(): Promise<void> {
    await this.knex.destroy();
  }
} 