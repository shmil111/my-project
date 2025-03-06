import Knex from 'knex';
import { getSQLConfig } from '../config/database';
import { SQLDatabaseConfig } from '../services/SQLDatabaseService'; // Import the config interface
import dotenv from 'dotenv';

dotenv.config();

let knexInstance: Knex.Knex | null = null;

export function initializeMySQL(): void {
    try {
        const config = getSQLConfig('mysql'); // Use your existing config function

        if (!config) {
            throw new Error('MySQL configuration is missing.');
        }
        knexInstance = Knex.default(config); // Initialize Knex
    } catch (error) {
        console.error('Failed to initialize MySQL connection:', error);
        process.exit(1); // Exit on critical error
    }
}

export function getKnexInstance(): Knex.Knex {
    if (!knexInstance) {
        initializeMySQL(); //lazy initialization
    }
    return knexInstance!;
}

// Remove the query function - we're using SQLDatabaseService now 