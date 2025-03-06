import { BaseRepository } from './BaseRepository';
import { DatabaseRecord } from '../../services/DatabaseService';
import { databaseConfig } from '../config/database.config';
import { Post } from './PostRepository';

export interface Category extends DatabaseRecord {
  name: string;
  slug: string;
  description?: string;
  parentId?: number;
  postCount: number;
  level: number;
  order: number;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface CategoryTree extends Category {
  children: CategoryTree[];
}

export class CategoryRepository extends BaseRepository<Category> {
  constructor() {
    super('categories', databaseConfig);
  }

  /**
   * Find category by slug
   */
  async findBySlug(slug: string): Promise<Category | null> {
    const categories = await this.getAll({
      filter: { slug }
    });
    return categories[0] || null;
  }

  /**
   * Find categories by parent ID
   */
  async findByParentId(parentId: number): Promise<Category[]> {
    return this.getAll({
      filter: { parentId },
      sort: { order: 'asc' }
    });
  }

  /**
   * Find root categories (no parent)
   */
  async findRootCategories(): Promise<Category[]> {
    return this.getAll({
      filter: { parentId: null },
      sort: { order: 'asc' }
    });
  }

  /**
   * Get category tree (hierarchical structure)
   */
  async getCategoryTree(): Promise<CategoryTree[]> {
    const categories = await this.getAll({
      sort: { level: 'asc', order: 'asc' }
    });

    const categoryMap = new Map<number, CategoryTree>();
    const rootCategories: CategoryTree[] = [];

    // First pass: create category objects with empty children arrays
    categories.forEach(category => {
      categoryMap.set(category.id, { ...category, children: [] });
    });

    // Second pass: build the tree structure
    categories.forEach(category => {
      const categoryWithChildren = categoryMap.get(category.id)!;
      if (category.parentId) {
        const parent = categoryMap.get(category.parentId);
        if (parent) {
          parent.children.push(categoryWithChildren);
        }
      } else {
        rootCategories.push(categoryWithChildren);
      }
    });

    return rootCategories;
  }

  /**
   * Get all descendants of a category
   */
  async getDescendants(categoryId: number): Promise<Category[]> {
    const query = `
      WITH RECURSIVE descendants AS (
        SELECT c.*, 1 as depth
        FROM categories c
        WHERE c.parentId = ?
        
        UNION ALL
        
        SELECT c.*, d.depth + 1
        FROM categories c
        JOIN descendants d ON c.parentId = d.id
        WHERE d.depth < 10
      )
      SELECT * FROM descendants
      ORDER BY level, order
    `;
    return this.rawQuery(query, [categoryId]);
  }

  /**
   * Get all ancestors of a category
   */
  async getAncestors(categoryId: number): Promise<Category[]> {
    const query = `
      WITH RECURSIVE ancestors AS (
        SELECT c.*, 1 as depth
        FROM categories c
        WHERE c.id = ?
        
        UNION ALL
        
        SELECT c.*, a.depth + 1
        FROM categories c
        JOIN ancestors a ON c.id = a.parentId
        WHERE a.depth < 10
      )
      SELECT * FROM ancestors
      ORDER BY level
    `;
    return this.rawQuery(query, [categoryId]);
  }

  /**
   * Create a new category
   */
  async createCategory(categoryData: Omit<Category, 'id' | 'createdAt' | 'updatedAt' | 'postCount' | 'level'>): Promise<Category & { id: number | string }> {
    const now = new Date();
    let level = 0;

    // Calculate level if parent is specified
    if (categoryData.parentId) {
      const parent = await this.getById(categoryData.parentId);
      if (parent) {
        level = parent.level + 1;
      }
    }

    const categoryToCreate = {
      ...categoryData,
      level,
      postCount: 0,
      createdAt: now,
      updatedAt: now
    };
    return this.create(categoryToCreate);
  }

  /**
   * Update category with automatic timestamp update
   */
  async updateCategory(id: number | string, data: Partial<Omit<Category, 'id' | 'createdAt' | 'updatedAt'>>): Promise<Category & { id: number | string }> {
    const updateData = {
      ...data,
      updatedAt: new Date()
    };
    return this.update(id, updateData);
  }

  /**
   * Move category to a new parent
   */
  async moveCategory(categoryId: number, newParentId: number | null): Promise<Category & { id: number | string }> {
    const category = await this.getById(categoryId);
    if (!category) {
      throw new Error('Category not found');
    }

    // Get new level
    let newLevel = 0;
    if (newParentId) {
      const newParent = await this.getById(newParentId);
      if (newParent) {
        newLevel = newParent.level + 1;
      }
    }

    // Update category
    return this.update(categoryId, {
      parentId: newParentId,
      level: newLevel,
      updatedAt: new Date()
    });
  }

  /**
   * Get posts in a category
   */
  async getPostsInCategory(categoryId: number): Promise<Post[]> {
    const query = `
      SELECT p.*
      FROM posts p
      WHERE p.categoryId = ?
      ORDER BY p.createdAt DESC
    `;
    return this.rawQuery(query, [categoryId]);
  }

  /**
   * Get posts in a category and all its subcategories
   */
  async getPostsInCategoryTree(categoryId: number): Promise<Post[]> {
    const descendants = await this.getDescendants(categoryId);
    const categoryIds = [categoryId, ...descendants.map(d => d.id)];
    
    const query = `
      SELECT p.*
      FROM posts p
      WHERE p.categoryId IN ?
      ORDER BY p.createdAt DESC
    `;
    return this.rawQuery(query, [[categoryIds]]);
  }

  /**
   * Update post count for a category
   */
  async updatePostCount(categoryId: number): Promise<void> {
    const query = `
      UPDATE categories c
      SET postCount = (
        SELECT COUNT(*)
        FROM posts p
        WHERE p.categoryId = c.id
      )
      WHERE c.id = ?
    `;
    await this.rawQuery(query, [categoryId]);
  }
} 