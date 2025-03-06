import asyncHandler from 'express-async-handler';
import { DatabaseFactory } from '../services/DatabaseFactory';
import { getDatabaseConfig } from '../config/database';
import { DataItem } from '../types/data'; // Import DataItem from the new location
import { DatabaseService } from '../services/DatabaseService';
import { createLogger } from '../utils/logger';

const logger = createLogger('mysqlController');

// Create a database service instance using the factory
const dbConfig = getDatabaseConfig();
const mySqlService: DatabaseService<DataItem> = DatabaseFactory.createDatabaseService<DataItem>('mytable', dbConfig);

// Initialize the database service
mySqlService.initialize().then(success => {
    if (success) {
        logger.info('MySQL service initialized successfully');
    } else {
        logger.error('Failed to initialize MySQL service');
        // Consider adding more robust error handling here, such as retries or exiting the application
    }
});

export const getMySQLData = asyncHandler(async (req, res) => {
    try {
        const results = await mySqlService.getAll();
        res.status(200).json(results);
    } catch (error) {
        console.error('Error fetching data from MySQL:', error);
        res.status(500).json({ message: 'Error fetching data', error: error.message });
    }
});

export const getMySQLDataById = asyncHandler(async (req, res) => {
    try {
        const id = parseInt(req.params.id, 10);
        if (isNaN(id)) {
            res.status(400).json({ message: 'Invalid ID format' });
            return;
        }
        const result = await mySqlService.getById(id);
        if (!result) {
            res.status(404).json({ message: 'Record not found' });
            return;
        }
        res.status(200).json(result);
    } catch (error) {
        console.error('Error fetching data from MySQL by ID:', error);
        res.status(500).json({ message: "Error fetching data by ID", error: error.message });
    }
});

export const insertMySQLData = asyncHandler(async (req, res) => {
    try {
        const { name, age } = req.body;

        if (!name || !age) {
            res.status(400).json({ message: "Missing required fields: name and age." });
            return;
        }
        //Use DataItem interface
        const newData: Omit<DataItem, 'id'> = { // Exclude ID, as it's auto-generated
            key: name, // Assuming 'name' can be used as 'key'
            value: { age }, // Store other data in 'value'
            createdAt: new Date().toISOString()
        };

        const result = await mySqlService.create(newData);

        res.status(201).json(result); // Return the created record
    } catch (error) {
        console.error('Error inserting data into MySQL', error);
        res.status(500).json({ message: 'Error inserting data', error: error.message });
    }
});

export const updateMySQLData = asyncHandler(async (req, res) => {
    try {
        const id = parseInt(req.params.id, 10);
        if (isNaN(id)) {
            res.status(400).json({ message: 'Invalid ID format' });
            return;
        }

        const { name, age } = req.body;
        const updateData: Partial<DataItem> = {};

        if (name) {
            updateData.key = name;
        }
        if (age) {
            updateData.value = { age };
        }
        updateData.updatedAt = new Date().toISOString();

        const updated = await mySqlService.update(id, updateData);

        if (!updated) {
            res.status(404).json({ message: 'Record not found or no changes made' });
            return;
        }

        res.status(200).json(updated);
    } catch (error) {
        console.error('Error updating data in MySQL', error);
        res.status(500).json({ message: 'Error updating data', error: error.message });
    }
});

export const deleteMySQLData = asyncHandler(async (req, res) => {
    try {
        const id = parseInt(req.params.id, 10);
        if (isNaN(id)) {
            res.status(400).json({ message: 'Invalid ID format' });
            return;
        }

        const deleted = await mySqlService.delete(id);

        if (!deleted) {
            res.status(404).json({ message: 'Record not found' });
            return;
        }

        res.status(204).send(); // No content
    } catch (error) {
        console.error('Error deleting data from MySQL', error);
        res.status(500).json({ message: 'Error deleting data', error: error.message });
    }
}); 