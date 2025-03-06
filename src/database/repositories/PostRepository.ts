import { BaseRepository } from './BaseRepository';
import { DatabaseRecord } from '../../services/DatabaseService';
import { databaseConfig } from '../config/database.config';
import { User } from './UserRepository';
import { Category } from './CategoryRepository';
import { Tag } from './TagRepository';

export interface Post extends DatabaseRecord {
  userId: number;
  categoryId?: number;
  title: string;
  content: string;
  slug: string;
  isPublished: boolean;
  publishedAt?: Date;
  viewCount: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface PostWithRelations extends Post {
  author: User;
  category?: Category;
  tags: Tag[];
}

export class PostRepository extends BaseRepository<Post> {
  constructor() {
    super('posts', databaseConfig);
  }

  /**
   * Find posts by user ID
   */
  async findByUserId(userId: number): Promise<Post[]> {
    return this.getAll({
      filter: { userId }
    });
  }

  /**
   * Find posts by category ID
   */
  async findByCategoryId(categoryId: number): Promise<Post[]> {
    return this.getAll({
      filter: { categoryId }
    });
  }

  /**
   * Find published posts
   */
  async findPublished(): Promise<Post[]> {
    return this.getAll({
      filter: { isPublished: true },
      sort: { publishedAt: 'desc' }
    });
  }

  /**
   * Find posts by slug
   */
  async findBySlug(slug: string): Promise<Post | null> {
    const posts = await this.getAll({
      filter: { slug }
    });
    return posts[0] || null;
  }

  /**
   * Publish a post
   */
  async publish(id: number | string): Promise<Post & { id: number | string }> {
    return this.update(id, {
      isPublished: true,
      publishedAt: new Date()
    });
  }

  /**
   * Unpublish a post
   */
  async unpublish(id: number | string): Promise<Post & { id: number | string }> {
    return this.update(id, {
      isPublished: false,
      publishedAt: null
    });
  }

  /**
   * Increment view count
   */
  async incrementViewCount(id: number | string): Promise<Post & { id: number | string }> {
    const post = await this.getById(id);
    if (!post) {
      throw new Error('Post not found');
    }
    return this.update(id, {
      viewCount: post.viewCount + 1
    });
  }

  /**
   * Create a new post with slug generation
   */
  async createPost(postData: Omit<Post, 'id' | 'createdAt' | 'updatedAt' | 'viewCount'>): Promise<Post & { id: number | string }> {
    const now = new Date();
    const postToCreate = {
      ...postData,
      viewCount: 0,
      createdAt: now,
      updatedAt: now
    };
    return this.create(postToCreate);
  }

  /**
   * Update post with automatic timestamp update
   */
  async updatePost(id: number | string, data: Partial<Omit<Post, 'id' | 'createdAt' | 'updatedAt'>>): Promise<Post & { id: number | string }> {
    const updateData = {
      ...data,
      updatedAt: new Date()
    };
    return this.update(id, updateData);
  }

  /**
   * Search posts by title or content
   */
  async searchPosts(searchTerm: string): Promise<Post[]> {
    const query = `
      SELECT * FROM posts 
      WHERE title LIKE ? 
      OR content LIKE ?
    `;
    const searchPattern = `%${searchTerm}%`;
    return this.rawQuery(query, [searchPattern, searchPattern]);
  }

  /**
   * Get post with all relations (author, category, tags)
   */
  async getPostWithRelations(id: number | string): Promise<PostWithRelations | null> {
    const query = `
      SELECT p.*, 
             u.username, u.email, u.firstName, u.lastName,
             c.name as categoryName, c.slug as categorySlug,
             GROUP_CONCAT(t.id) as tagIds,
             GROUP_CONCAT(t.name) as tagNames,
             GROUP_CONCAT(t.slug) as tagSlugs
      FROM posts p
      JOIN users u ON p.userId = u.id
      LEFT JOIN categories c ON p.categoryId = c.id
      LEFT JOIN post_tags pt ON p.id = pt.postId
      LEFT JOIN tags t ON pt.tagId = t.id
      WHERE p.id = ?
      GROUP BY p.id
    `;
    const results = await this.rawQuery(query, [id]);
    if (!results[0]) {
      return null;
    }

    const post = results[0];
    const tagIds = post.tagIds ? post.tagIds.split(',').map(Number) : [];
    const tagNames = post.tagNames ? post.tagNames.split(',') : [];
    const tagSlugs = post.tagSlugs ? post.tagSlugs.split(',') : [];

    const tags = tagIds.map((id, index) => ({
      id,
      name: tagNames[index],
      slug: tagSlugs[index]
    }));

    return {
      ...post,
      author: {
        username: post.username,
        email: post.email,
        firstName: post.firstName,
        lastName: post.lastName
      },
      category: post.categoryName ? {
        name: post.categoryName,
        slug: post.categorySlug
      } : undefined,
      tags
    };
  }

  /**
   * Get posts with author information
   */
  async getPostsWithAuthor(): Promise<(Post & { author: User })[]> {
    const query = `
      SELECT p.*, u.username, u.email, u.firstName, u.lastName
      FROM posts p
      JOIN users u ON p.userId = u.id
      ORDER BY p.createdAt DESC
    `;
    return this.rawQuery(query);
  }

  /**
   * Get posts by tag
   */
  async getPostsByTag(tagId: number): Promise<Post[]> {
    const query = `
      SELECT p.*
      FROM posts p
      JOIN post_tags pt ON p.id = pt.postId
      WHERE pt.tagId = ?
      ORDER BY p.createdAt DESC
    `;
    return this.rawQuery(query, [tagId]);
  }

  /**
   * Get posts by multiple tags
   */
  async getPostsByTags(tagIds: number[]): Promise<Post[]> {
    const query = `
      SELECT DISTINCT p.*
      FROM posts p
      JOIN post_tags pt ON p.id = pt.postId
      WHERE pt.tagId IN ?
      ORDER BY p.createdAt DESC
    `;
    return this.rawQuery(query, [[tagIds]]);
  }
} 