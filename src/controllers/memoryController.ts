/**
 * Memory Controller
 * 
 * Handles all memory-related API endpoints
 */
import { Request, Response } from 'express';
import { MemoryFactory } from '../services/MemoryFactory';
import { MemoryType } from '../services/MemoryService';
import { createLogger } from '../utils/logger';

// Initialize logger
const logger = createLogger('MemoryController');

/**
 * Memory controller for handling memory-related requests
 */
export class MemoryController {
  /**
   * Constructor
   */
  constructor() {
    // Bind methods to this instance
    this.getItem = this.getItem.bind(this);
    this.setItem = this.setItem.bind(this);
    this.deleteItem = this.deleteItem.bind(this);
    this.listItems = this.listItems.bind(this);
    this.clearNamespace = this.clearNamespace.bind(this);
  }
  
  /**
   * Get an item from memory
   * @param req Request object
   * @param res Response object
   */
  public async getItem(req: Request, res: Response): Promise<void> {
    const { namespace, key } = req.params;
    const memoryType = (req.query.type as string) === MemoryType.LONG_TERM 
      ? MemoryType.LONG_TERM 
      : MemoryType.SHORT_TERM;
    
    logger.debug(`Get item request for key=${key} in namespace=${namespace}, type=${memoryType}`);
    
    try {
      // Get the memory service
      const memory = await MemoryFactory.getMemory(memoryType, namespace);
      
      // Get the item
      const item = await memory.get(key);
      
      if (item === null) {
        logger.debug(`Item not found: key=${key}, namespace=${namespace}, type=${memoryType}`);
        res.status(404).json({
          success: false,
          message: `Item not found: ${key}`,
        });
        return;
      }
      
      logger.debug(`Item retrieved: key=${key}, namespace=${namespace}, type=${memoryType}`);
      res.status(200).json({
        success: true,
        item,
      });
    } catch (error) {
      logger.error(`Error getting item: ${error}`);
      res.status(500).json({
        success: false,
        message: 'Failed to retrieve item',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Set an item in memory
   * @param req Request object
   * @param res Response object
   */
  public async setItem(req: Request, res: Response): Promise<void> {
    const { namespace } = req.params;
    const { key, value, ttl = 0, type = MemoryType.SHORT_TERM } = req.body;
    const memoryType = type === MemoryType.LONG_TERM 
      ? MemoryType.LONG_TERM 
      : MemoryType.SHORT_TERM;
    
    logger.debug(`Set item request for key=${key} in namespace=${namespace}, type=${memoryType}, ttl=${ttl}`);
    
    try {
      // Get the memory service
      const memory = await MemoryFactory.getMemory(memoryType, namespace);
      
      // Set the item
      const success = await memory.set(key, value, ttl);
      
      if (!success) {
        logger.error(`Failed to set item: key=${key}, namespace=${namespace}, type=${memoryType}`);
        res.status(500).json({
          success: false,
          message: 'Failed to store item',
        });
        return;
      }
      
      logger.debug(`Item stored: key=${key}, namespace=${namespace}, type=${memoryType}`);
      res.status(201).json({
        success: true,
        message: 'Item stored successfully',
      });
    } catch (error) {
      logger.error(`Error setting item: ${error}`);
      res.status(500).json({
        success: false,
        message: 'Failed to store item',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Delete an item from memory
   * @param req Request object
   * @param res Response object
   */
  public async deleteItem(req: Request, res: Response): Promise<void> {
    const { namespace, key } = req.params;
    const memoryType = (req.query.type as string) === MemoryType.LONG_TERM 
      ? MemoryType.LONG_TERM 
      : MemoryType.SHORT_TERM;
    
    logger.debug(`Delete item request for key=${key} in namespace=${namespace}, type=${memoryType}`);
    
    try {
      // Get the memory service
      const memory = await MemoryFactory.getMemory(memoryType, namespace);
      
      // Check if the item exists
      const exists = await memory.has(key);
      
      if (!exists) {
        logger.debug(`Item not found for deletion: key=${key}, namespace=${namespace}, type=${memoryType}`);
        res.status(404).json({
          success: false,
          message: `Item not found: ${key}`,
        });
        return;
      }
      
      // Delete the item
      const deleted = await memory.delete(key);
      
      if (!deleted) {
        logger.error(`Failed to delete item: key=${key}, namespace=${namespace}, type=${memoryType}`);
        res.status(500).json({
          success: false,
          message: 'Failed to delete item',
        });
        return;
      }
      
      logger.debug(`Item deleted: key=${key}, namespace=${namespace}, type=${memoryType}`);
      res.status(200).json({
        success: true,
        message: 'Item deleted successfully',
      });
    } catch (error) {
      logger.error(`Error deleting item: ${error}`);
      res.status(500).json({
        success: false,
        message: 'Failed to delete item',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * List all items in a namespace
   * @param req Request object
   * @param res Response object
   */
  public async listItems(req: Request, res: Response): Promise<void> {
    const { namespace } = req.params;
    const memoryType = (req.query.type as string) === MemoryType.LONG_TERM 
      ? MemoryType.LONG_TERM 
      : MemoryType.SHORT_TERM;
    
    logger.debug(`List items request for namespace=${namespace}, type=${memoryType}`);
    
    try {
      // Get the memory service
      const memory = await MemoryFactory.getMemory(memoryType, namespace);
      
      // Get all keys in the namespace
      const keys = await memory.keys();
      
      // Retrieve all items
      const items: Record<string, any> = {};
      for (const key of keys) {
        items[key] = await memory.get(key);
      }
      
      logger.debug(`Listed ${keys.length} items in namespace=${namespace}, type=${memoryType}`);
      res.status(200).json({
        success: true,
        items,
        count: keys.length,
      });
    } catch (error) {
      logger.error(`Error listing items: ${error}`);
      res.status(500).json({
        success: false,
        message: 'Failed to list items',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Clear all items in a namespace
   * @param req Request object
   * @param res Response object
   */
  public async clearNamespace(req: Request, res: Response): Promise<void> {
    const { namespace } = req.params;
    const memoryType = (req.body.type as string) === MemoryType.LONG_TERM 
      ? MemoryType.LONG_TERM 
      : MemoryType.SHORT_TERM;
    
    logger.debug(`Clear namespace request for namespace=${namespace}, type=${memoryType}`);
    
    try {
      // Get the memory service
      const memory = await MemoryFactory.getMemory(memoryType, namespace);
      
      // Clear the namespace
      const cleared = await memory.clear();
      
      logger.debug(`Cleared ${cleared} items from namespace=${namespace}, type=${memoryType}`);
      res.status(200).json({
        success: true,
        message: `Cleared ${cleared} items from namespace`,
        count: cleared,
      });
    } catch (error) {
      logger.error(`Error clearing namespace: ${error}`);
      res.status(500).json({
        success: false,
        message: 'Failed to clear namespace',
        error: (error as Error).message,
      });
    }
  }
} 