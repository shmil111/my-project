/**
 * DataModel.ts
 * 
 * This class represents a data model for managing data items.
 * It provides in-memory storage and CRUD operations.
 */

import { MyDataType } from '../types/dataTypes';

export class DataModel {
  private _items: Map<number, MyDataType>;
  private _nextId: number;

  constructor() {
    this._items = new Map<number, MyDataType>();
    this._nextId = 1;
    
    // Initialize with some sample data
    this.addItem({ id: this._nextId++, name: 'Item 1' });
    this.addItem({ id: this._nextId++, name: 'Item 2' });
  }

  /**
   * Get all items
   */
  public getAllItems(): MyDataType[] {
    return Array.from(this._items.values());
  }

  /**
   * Get a single item by ID
   */
  public getItemById(id: number): MyDataType | undefined {
    return this._items.get(id);
  }

  /**
   * Add a new item
   */
  public addItem(item: MyDataType): MyDataType {
    // If no ID is provided or ID already exists, assign a new one
    if (!item.id || this._items.has(item.id)) {
      item.id = this._nextId++;
    }

    this._items.set(item.id, item);
    return item;
  }

  /**
   * Update an existing item
   */
  public updateItem(id: number, item: Partial<MyDataType>): MyDataType | undefined {
    const existingItem = this._items.get(id);
    
    if (!existingItem) {
      return undefined;
    }

    const updatedItem = { ...existingItem, ...item, id };
    this._items.set(id, updatedItem);
    
    return updatedItem;
  }

  /**
   * Delete an item
   */
  public deleteItem(id: number): boolean {
    return this._items.delete(id);
  }
}

export default DataModel; 