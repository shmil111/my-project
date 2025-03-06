/**
 * Data Controller
 * 
 * This controller handles CRUD operations for data entities.
 */

import { Request, Response, NextFunction } from 'express';
import { DatabaseService } from '../services/DatabaseService';
import { DatabaseFactory } from '../services/DatabaseFactory';
import { getDatabaseConfig } from '../config/database';
import { createLogger } from '../utils/logger';
import { ApiError, asyncHandler } from '../middleware/errorHandler';

// Create logger
const logger = createLogger('DataController');

/**
 * Data item interface
 */
export interface DataItem {
  id: number | string;
  key: string;
  value: any;
  createdAt: string;
  updatedAt?: string;
  metadata?: Record<string, any>;
}

/**
 * Data controller for managing data items
 */
export class DataController {
  private dataService: DatabaseService<DataItem>;
  
  constructor() {
    // Initialize the database service using the factory
    logger.info('Initializing data controller');
    
    const dbConfig = getDatabaseConfig();
    this.dataService = DatabaseFactory.createDatabaseService<DataItem>('data', dbConfig);
    
    // Initialize the database
    this.dataService.initialize().then(success => {
      if (success) {
        logger.info('Data service initialized successfully');
      } else {
        logger.error('Failed to initialize data service');
      }
    });
  }
  
  /**
   * Get all data items
   */
  public async getAllItems(req: Request, res: Response): Promise<void> {
    try {
      const items = await this.dataService.getAll();
      res.json({ success: true, data: items });
    } catch (error) {
      logger.error(`Error getting all items: ${(error as Error).message}`);
      res.status(500).json({ success: false, error: 'Failed to retrieve items' });
    }
  }
  
  /**
   * Get a data item by ID
   */
  public async getItemById(req: Request, res: Response): Promise<void> {
    try {
      const id = req.params.id;
      const item = await this.dataService.getById(id);
      
      if (!item) {
        res.status(404).json({ success: false, error: 'Item not found' });
        return;
      }
      
      res.json({ success: true, data: item });
    } catch (error) {
      logger.error(`Error getting item by ID: ${(error as Error).message}`);
      res.status(500).json({ success: false, error: 'Failed to retrieve item' });
    }
  }
  
  /**
   * Create a new data item
   */
  public async createItem(req: Request, res: Response): Promise<void> {
    try {
      const { key, value, metadata } = req.body;
      
      if (!key || value === undefined) {
        res.status(400).json({ success: false, error: 'Key and value are required' });
        return;
      }
      
      const newItem = await this.dataService.create({
        key,
        value,
        metadata,
        createdAt: new Date().toISOString()
      });
      
      res.status(201).json({ success: true, data: newItem });
    } catch (error) {
      logger.error(`Error creating item: ${(error as Error).message}`);
      res.status(500).json({ success: false, error: 'Failed to create item' });
    }
  }
  
  /**
   * Update a data item
   */
  public async updateItem(req: Request, res: Response): Promise<void> {
    try {
      const id = req.params.id;
      const { key, value, metadata } = req.body;
      
      if (!key && value === undefined && !metadata) {
        res.status(400).json({ success: false, error: 'At least one field to update is required' });
        return;
      }
      
      const updateData: Partial<DataItem> = {
        updatedAt: new Date().toISOString()
      };
      
      if (key !== undefined) updateData.key = key;
      if (value !== undefined) updateData.value = value;
      if (metadata !== undefined) updateData.metadata = metadata;
      
      const updatedItem = await this.dataService.update(id, updateData);
      
      if (!updatedItem) {
        res.status(404).json({ success: false, error: 'Item not found' });
        return;
      }
      
      res.json({ success: true, data: updatedItem });
    } catch (error) {
      logger.error(`Error updating item: ${(error as Error).message}`);
      res.status(500).json({ success: false, error: 'Failed to update item' });
    }
  }
  
  /**
   * Delete a data item
   */
  public async deleteItem(req: Request, res: Response): Promise<void> {
    try {
      const id = req.params.id;
      const deleted = await this.dataService.delete(id);
      
      if (!deleted) {
        res.status(404).json({ success: false, error: 'Item not found' });
        return;
      }
      
      res.json({ success: true, message: 'Item deleted successfully' });
    } catch (error) {
      logger.error(`Error deleting item: ${(error as Error).message}`);
      res.status(500).json({ success: false, error: 'Failed to delete item' });
    }
  }
  
  /**
   * Close the database connection when shutting down
   */
  public async close(): Promise<void> {
    try {
      await this.dataService.close();
      logger.info('Data service closed successfully');
    } catch (error) {
      logger.error(`Error closing data service: ${(error as Error).message}`);
    }
  }
} 