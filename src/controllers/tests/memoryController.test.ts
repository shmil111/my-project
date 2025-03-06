import { Request, Response } from 'express';
import { MemoryController } from '../memoryController';
import { MemoryFactory } from '../../services/MemoryFactory';

// Mock the MemoryFactory and its methods
jest.mock('../../services/MemoryFactory', () => ({
  MemoryFactory: {
    getMemory: jest.fn(),
  },
}));

describe('MemoryController', () => {
  let memoryController: MemoryController;
  let req: Partial<Request>;
  let res: Partial<Response>;
  
  // Mock memory service implementation
  const mockMemoryService = {
    initialize: jest.fn().mockResolvedValue(undefined),
    close: jest.fn().mockResolvedValue(undefined),
    set: jest.fn().mockResolvedValue(true),
    get: jest.fn(),
    has: jest.fn(),
    delete: jest.fn(),
    clear: jest.fn(),
    keys: jest.fn(),
    size: jest.fn().mockResolvedValue(0),
    getType: jest.fn().mockReturnValue('short-term')
  };
  
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Create controller instance
    memoryController = new MemoryController();
    
    // Mock request and response objects
    req = {
      params: {},
      query: {},
      body: {}
    };
    
    res = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn()
    };
    
    // Set up default mock implementation
    (MemoryFactory.getMemory as jest.Mock).mockResolvedValue(mockMemoryService);
  });
  
  describe('getItem', () => {
    it('should return 200 and item when found', async () => {
      // Setup
      req.params = { namespace: 'test-ns', key: 'test-key' };
      const mockItem = { foo: 'bar' };
      mockMemoryService.get.mockResolvedValueOnce(mockItem);
      
      // Execute
      await memoryController.getItem(req as Request, res as Response);
      
      // Assert
      expect(MemoryFactory.getMemory).toHaveBeenCalledWith('short-term', 'test-ns');
      expect(mockMemoryService.get).toHaveBeenCalledWith('test-key');
      expect(res.status).toHaveBeenCalledWith(200);
      expect(res.json).toHaveBeenCalledWith({
        success: true,
        item: mockItem
      });
    });
    
    it('should return 404 when item not found', async () => {
      // Setup
      req.params = { namespace: 'test-ns', key: 'missing-key' };
      mockMemoryService.get.mockResolvedValueOnce(null);
      
      // Execute
      await memoryController.getItem(req as Request, res as Response);
      
      // Assert
      expect(res.status).toHaveBeenCalledWith(404);
      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        success: false,
        message: expect.stringContaining('not found')
      }));
    });
    
    it('should return 500 on error', async () => {
      // Setup
      req.params = { namespace: 'test-ns', key: 'error-key' };
      mockMemoryService.get.mockRejectedValueOnce(new Error('Test error'));
      
      // Execute
      await memoryController.getItem(req as Request, res as Response);
      
      // Assert
      expect(res.status).toHaveBeenCalledWith(500);
      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        success: false,
        message: expect.stringContaining('Failed to retrieve')
      }));
    });
  });
  
  describe('setItem', () => {
    it('should return 201 when item is created', async () => {
      // Setup
      req.params = { namespace: 'test-ns' };
      req.body = { key: 'new-key', value: { data: 'test' } };
      
      // Execute
      await memoryController.setItem(req as Request, res as Response);
      
      // Assert
      expect(mockMemoryService.set).toHaveBeenCalledWith('new-key', { data: 'test' }, 0);
      expect(res.status).toHaveBeenCalledWith(201);
      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        success: true
      }));
    });
    
    it('should return 500 when set fails', async () => {
      // Setup
      req.params = { namespace: 'test-ns' };
      req.body = { key: 'fail-key', value: { data: 'test' } };
      mockMemoryService.set.mockResolvedValueOnce(false);
      
      // Execute
      await memoryController.setItem(req as Request, res as Response);
      
      // Assert
      expect(res.status).toHaveBeenCalledWith(500);
      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        success: false
      }));
    });
  });
  
  describe('deleteItem', () => {
    it('should return 200 when item is deleted', async () => {
      // Setup
      req.params = { namespace: 'test-ns', key: 'delete-key' };
      mockMemoryService.has.mockResolvedValueOnce(true);
      mockMemoryService.delete.mockResolvedValueOnce(true);
      
      // Execute
      await memoryController.deleteItem(req as Request, res as Response);
      
      // Assert
      expect(mockMemoryService.has).toHaveBeenCalledWith('delete-key');
      expect(mockMemoryService.delete).toHaveBeenCalledWith('delete-key');
      expect(res.status).toHaveBeenCalledWith(200);
      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        success: true
      }));
    });
    
    it('should return 404 when item does not exist', async () => {
      // Setup
      req.params = { namespace: 'test-ns', key: 'nonexistent-key' };
      mockMemoryService.has.mockResolvedValueOnce(false);
      
      // Execute
      await memoryController.deleteItem(req as Request, res as Response);
      
      // Assert
      expect(mockMemoryService.has).toHaveBeenCalledWith('nonexistent-key');
      expect(mockMemoryService.delete).not.toHaveBeenCalled();
      expect(res.status).toHaveBeenCalledWith(404);
    });
  });
  
  describe('listItems', () => {
    it('should return items in namespace', async () => {
      // Setup
      req.params = { namespace: 'test-ns' };
      const mockKeys = ['key1', 'key2', 'key3'];
      const mockItems = {
        key1: 'value1',
        key2: 'value2',
        key3: 'value3'
      };
      
      mockMemoryService.keys.mockResolvedValueOnce(mockKeys);
      mockMemoryService.get
        .mockResolvedValueOnce('value1')
        .mockResolvedValueOnce('value2')
        .mockResolvedValueOnce('value3');
      
      // Execute
      await memoryController.listItems(req as Request, res as Response);
      
      // Assert
      expect(mockMemoryService.keys).toHaveBeenCalled();
      expect(mockMemoryService.get).toHaveBeenCalledTimes(3);
      expect(res.status).toHaveBeenCalledWith(200);
      expect(res.json).toHaveBeenCalledWith({
        success: true,
        items: mockItems,
        count: 3
      });
    });
  });
  
  describe('clearNamespace', () => {
    it('should clear namespace and return count', async () => {
      // Setup
      req.params = { namespace: 'test-ns' };
      req.body = { type: 'short-term' };
      mockMemoryService.clear.mockResolvedValueOnce(5);
      
      // Execute
      await memoryController.clearNamespace(req as Request, res as Response);
      
      // Assert
      expect(mockMemoryService.clear).toHaveBeenCalled();
      expect(res.status).toHaveBeenCalledWith(200);
      expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
        success: true,
        count: 5
      }));
    });
  });
}); 