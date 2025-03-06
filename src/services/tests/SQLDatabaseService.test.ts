/**
 * SQLDatabaseService Tests
 * 
 * This file contains tests for the SQLDatabaseService implementation.
 * It tests the service with SQLite, which doesn't require external servers.
 */

import { SQLDatabaseService, SQLDatabaseConfig } from '../SQLDatabaseService';
import * as fs from 'fs';
import * as path from 'path';

// Define a test data interface
interface TestItem {
  id: number;
  name: string;
  value: number;
  tags?: string[];
  metadata?: Record<string, any>;
  extraField?: string;
  nested?: {
    count: number;
  };
}

describe('SQLDatabaseService', () => {
  const dbPath = path.join(__dirname, 'test.sqlite');
  let service: SQLDatabaseService<TestItem>;
  
  const config: SQLDatabaseConfig = {
    client: 'sqlite3',
    connection: {
      filename: dbPath,
      database: 'test'
    },
    useNullAsDefault: true
  };
  
  beforeAll(async () => {
    // Make sure the database file doesn't exist before tests
    if (fs.existsSync(dbPath)) {
      fs.unlinkSync(dbPath);
    }
    
    // Create a new service instance
    service = new SQLDatabaseService<TestItem>('test_items', config);
    await service.initialize();
  });
  
  afterAll(async () => {
    // Clean up
    await service.close();
    
    // Remove test database file
    if (fs.existsSync(dbPath)) {
      fs.unlinkSync(dbPath);
    }
  });
  
  it('should create and retrieve items', async () => {
    // Create a test item
    const item = await service.create({ name: 'Test Item', value: 42 });
    
    // Verify it was created with an ID
    expect(item).toBeDefined();
    expect(item.id).toBeDefined();
    expect(item.name).toBe('Test Item');
    expect(item.value).toBe(42);
    
    // Retrieve the item by ID
    const retrieved = await service.getById(item.id);
    
    // Verify it matches
    expect(retrieved).toEqual(item);
  });
  
  it('should update items', async () => {
    // Create a test item
    const item = await service.create({ name: 'Update Test', value: 100 });
    
    // Update the item
    const updated = await service.update(item.id, { value: 200, tags: ['test', 'update'] });
    
    // Verify the update worked
    expect(updated).toBeDefined();
    expect(updated?.id).toBe(item.id);
    expect(updated?.name).toBe('Update Test');
    expect(updated?.value).toBe(200);
    expect(updated?.tags).toEqual(['test', 'update']);
    
    // Verify by retrieving again
    const retrieved = await service.getById(item.id);
    expect(retrieved).toEqual(updated);
  });
  
  it('should delete items', async () => {
    // Create a test item
    const item = await service.create({ name: 'Delete Test', value: 50 });
    
    // Verify it exists
    expect(await service.exists(item.id)).toBe(true);
    
    // Delete the item
    const deleted = await service.delete(item.id);
    expect(deleted).toBe(true);
    
    // Verify it no longer exists
    expect(await service.exists(item.id)).toBe(false);
    expect(await service.getById(item.id)).toBeNull();
  });
  
  it('should query with filters and options', async () => {
    // Create multiple test items
    await service.create({ name: 'Item 1', value: 10 });
    await service.create({ name: 'Item 2', value: 20 });
    await service.create({ name: 'Item 3', value: 30 });
    await service.create({ name: 'Other 1', value: 40 });
    await service.create({ name: 'Other 2', value: 50 });
    
    // Query with filter
    const itemsOnly = await service.getAll({ filter: { name: 'Item 2' } });
    expect(itemsOnly.length).toBe(1);
    expect(itemsOnly[0].name).toBe('Item 2');
    
    // Query with sort
    const sortedDesc = await service.getAll({ 
      sortBy: 'value', 
      sortDirection: 'desc' 
    });
    expect(sortedDesc.length).toBeGreaterThanOrEqual(5);
    expect(sortedDesc[0].value).toBeGreaterThanOrEqual(sortedDesc[1].value);
    
    // Query with pagination
    const paged = await service.getAll({ limit: 2, offset: 1 });
    expect(paged.length).toBe(2);
  });
  
  it('should handle dynamic schema updates', async () => {
    // Create an item with basic fields
    const item = await service.create({ name: 'Schema Test', value: 75 });
    
    // Update with new fields that weren't in the original schema
    const updated = await service.update(item.id, { 
      metadata: { created: new Date().toISOString(), important: true } 
    });
    
    // Verify new fields were added and saved
    expect(updated).toBeDefined();
    expect(updated?.metadata).toBeDefined();
    expect(updated?.metadata?.important).toBe(true);
    
    // Create a new item with additional fields
    const newItem = await service.create({
      name: 'New Schema Item',
      value: 85,
      extraField: 'This is a new field',
      nested: { count: 1 }
    });
    
    // Verify it saved correctly
    expect(newItem.extraField).toBe('This is a new field');
  });
  
  it('should count items', async () => {
    // Get total count
    const totalCount = await service.count();
    expect(totalCount).toBeGreaterThan(0);
    
    // Count with filter
    const filteredCount = await service.count({ name: 'Item 1' });
    expect(filteredCount).toBe(1);
  });
}); 