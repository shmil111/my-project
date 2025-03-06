import { InMemoryShortTermMemoryService } from '../ShortTermMemoryService';

describe('ShortTermMemoryService', () => {
  let memoryService: InMemoryShortTermMemoryService;
  const namespace = 'test-namespace';
  
  beforeEach(async () => {
    // Create a new instance before each test
    memoryService = new InMemoryShortTermMemoryService({ namespace });
    await memoryService.initialize();
  });
  
  afterEach(async () => {
    // Clean up after each test
    await memoryService.close();
  });
  
  describe('set', () => {
    it('should set a value', async () => {
      const key = 'test-key';
      const value = { test: 'data' };
      
      const result = await memoryService.set(key, value);
      expect(result).toBe(true);
    });
    
    it('should set a value with custom TTL', async () => {
      const key = 'ttl-key';
      const value = { test: 'ttl-data' };
      const ttl = 60; // 1 minute
      
      const result = await memoryService.set(key, value, ttl);
      expect(result).toBe(true);
    });
  });
  
  describe('get', () => {
    it('should retrieve a stored value', async () => {
      const key = 'get-key';
      const value = { test: 'get-data' };
      
      await memoryService.set(key, value);
      const retrieved = await memoryService.get(key);
      
      expect(retrieved).toEqual(value);
    });
    
    it('should return null for non-existent key', async () => {
      const retrieved = await memoryService.get('non-existent');
      expect(retrieved).toBeNull();
    });
  });
  
  describe('has', () => {
    it('should return true if key exists', async () => {
      const key = 'has-key';
      await memoryService.set(key, 'value');
      
      const exists = await memoryService.has(key);
      expect(exists).toBe(true);
    });
    
    it('should return false if key does not exist', async () => {
      const exists = await memoryService.has('non-existent');
      expect(exists).toBe(false);
    });
  });
  
  describe('delete', () => {
    it('should delete an existing key', async () => {
      const key = 'delete-key';
      await memoryService.set(key, 'delete-value');
      
      const deleted = await memoryService.delete(key);
      expect(deleted).toBe(true);
      
      const exists = await memoryService.has(key);
      expect(exists).toBe(false);
    });
    
    it('should return false when deleting non-existent key', async () => {
      const deleted = await memoryService.delete('non-existent');
      expect(deleted).toBe(false);
    });
  });
  
  describe('keys', () => {
    it('should return all keys in the namespace', async () => {
      // Add multiple keys
      await memoryService.set('key1', 'value1');
      await memoryService.set('key2', 'value2');
      await memoryService.set('key3', 'value3');
      
      const keys = await memoryService.keys();
      expect(keys).toHaveLength(3);
      expect(keys).toContain('key1');
      expect(keys).toContain('key2');
      expect(keys).toContain('key3');
    });
    
    it('should return empty array for namespace with no keys', async () => {
      // Create a new service with different namespace
      const emptyService = new InMemoryShortTermMemoryService({ namespace: 'empty' });
      await emptyService.initialize();
      
      const keys = await emptyService.keys();
      expect(keys).toHaveLength(0);
      
      await emptyService.close();
    });
  });
  
  describe('clear', () => {
    it('should clear all keys in the namespace', async () => {
      // Add multiple keys
      await memoryService.set('clear1', 'value1');
      await memoryService.set('clear2', 'value2');
      
      const cleared = await memoryService.clear();
      expect(cleared).toBe(2);
      
      const keys = await memoryService.keys();
      expect(keys).toHaveLength(0);
    });
    
    it('should return 0 for empty namespace', async () => {
      const emptyService = new InMemoryShortTermMemoryService({ namespace: 'empty-clear' });
      await emptyService.initialize();
      
      const cleared = await emptyService.clear();
      expect(cleared).toBe(0);
      
      await emptyService.close();
    });
  });
  
  describe('size', () => {
    it('should return the correct number of items', async () => {
      await memoryService.set('size1', 'value1');
      await memoryService.set('size2', 'value2');
      
      const size = await memoryService.size();
      expect(size).toBe(2);
    });
    
    it('should return 0 for empty namespace', async () => {
      const emptyService = new InMemoryShortTermMemoryService({ namespace: 'empty-size' });
      await emptyService.initialize();
      
      const size = await emptyService.size();
      expect(size).toBe(0);
      
      await emptyService.close();
    });
  });
  
  describe('getStats', () => {
    it('should return statistics object', async () => {
      await memoryService.set('stats1', 'value1');
      
      const stats = await memoryService.getStats();
      expect(stats).toBeDefined();
      expect(stats.namespace).toBe(namespace);
      expect(stats.namespaceSize).toBe(1);
      expect(stats.defaultTTL).toBeDefined();
    });
  });
  
  describe('getType', () => {
    it('should return short-term', () => {
      const type = memoryService.getType();
      expect(type).toBe('short-term');
    });
  });
}); 