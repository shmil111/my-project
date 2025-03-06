import { BaseRepository } from './BaseRepository';
import { DatabaseRecord } from '../../services/DatabaseService';
import { databaseConfig } from '../config/database.config';
import { Post } from './PostRepository';

export interface Tag extends DatabaseRecord {
  name: string;
  slug: string;
  description?: string;
  postCount: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface PostTag {
  postId: number;
  tagId: number;
  createdAt: Date;
}

export class TagRepository extends BaseRepository<Tag> {
  constructor() {
    super('tags', databaseConfig);
  }

  /**
   * Find tag by slug
   */
  async findBySlug(slug: string): Promise<Tag | null> {
    const tags = await this.getAll({
      filter: { slug }
    });
    return tags[0] || null;
  }

  /**
   * Find tags by name (partial match)
   */
  async findByName(name: string): Promise<Tag[]> {
    return this.getAll({
      filter: { name: { $like: `%${name}%` } }
    });
  }

  /**
   * Get tags with post count
   */
  async getTagsWithPostCount(): Promise<(Tag & { postCount: number })[]> {
    const query = `
      SELECT t.*, COUNT(pt.postId) as postCount
      FROM tags t
      LEFT JOIN post_tags pt ON t.id = pt.tagId
      GROUP BY t.id
      ORDER BY postCount DESC
    `;
    return this.rawQuery(query);
  }

  /**
   * Get tags for a specific post
   */
  async getTagsForPost(postId: number): Promise<Tag[]> {
    const query = `
      SELECT t.*
      FROM tags t
      JOIN post_tags pt ON t.id = pt.tagId
      WHERE pt.postId = ?
      ORDER BY t.name ASC
    `;
    return this.rawQuery(query, [postId]);
  }

  /**
   * Add tags to a post
   */
  async addTagsToPost(postId: number, tagIds: number[]): Promise<void> {
    const postTags = tagIds.map(tagId => ({
      postId,
      tagId,
      createdAt: new Date()
    }));

    await this.rawQuery(
      'INSERT INTO post_tags (postId, tagId, createdAt) VALUES ?',
      [postTags.map(pt => [pt.postId, pt.tagId, pt.createdAt])]
    );

    // Update post count for each tag
    await this.rawQuery(
      'UPDATE tags SET postCount = postCount + 1 WHERE id IN ?',
      [[tagIds]]
    );
  }

  /**
   * Remove tags from a post
   */
  async removeTagsFromPost(postId: number, tagIds: number[]): Promise<void> {
    await this.rawQuery(
      'DELETE FROM post_tags WHERE postId = ? AND tagId IN ?',
      [postId, [tagIds]]
    );

    // Update post count for each tag
    await this.rawQuery(
      'UPDATE tags SET postCount = postCount - 1 WHERE id IN ?',
      [[tagIds]]
    );
  }

  /**
   * Create a new tag
   */
  async createTag(tagData: Omit<Tag, 'id' | 'createdAt' | 'updatedAt' | 'postCount'>): Promise<Tag & { id: number | string }> {
    const now = new Date();
    const tagToCreate = {
      ...tagData,
      postCount: 0,
      createdAt: now,
      updatedAt: now
    };
    return this.create(tagToCreate);
  }

  /**
   * Update tag with automatic timestamp update
   */
  async updateTag(id: number | string, data: Partial<Omit<Tag, 'id' | 'createdAt' | 'updatedAt'>>): Promise<Tag & { id: number | string }> {
    const updateData = {
      ...data,
      updatedAt: new Date()
    };
    return this.update(id, updateData);
  }

  /**
   * Get posts with a specific tag
   */
  async getPostsWithTag(tagId: number): Promise<(Post & { postId: number })[]> {
    const query = `
      SELECT p.*, pt.postId
      FROM posts p
      JOIN post_tags pt ON p.id = pt.postId
      WHERE pt.tagId = ?
      ORDER BY p.createdAt DESC
    `;
    return this.rawQuery(query, [tagId]);
  }

  /**
   * Get popular tags (most used)
   */
  async getPopularTags(limit: number = 10): Promise<Tag[]> {
    return this.getAll({
      sort: { postCount: 'desc' },
      limit
    });
  }
} 