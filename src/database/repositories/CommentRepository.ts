import { BaseRepository } from './BaseRepository';
import { DatabaseRecord } from '../../services/DatabaseService';
import { databaseConfig } from '../config/database.config';
import { User } from './UserRepository';
import { Post } from './PostRepository';

export interface Comment extends DatabaseRecord {
  postId: number;
  userId: number;
  content: string;
  parentId?: number;
  isApproved: boolean;
  approvedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export class CommentRepository extends BaseRepository<Comment> {
  constructor() {
    super('comments', databaseConfig);
  }

  /**
   * Find comments by post ID
   */
  async findByPostId(postId: number): Promise<Comment[]> {
    return this.getAll({
      filter: { postId },
      sort: { createdAt: 'asc' }
    });
  }

  /**
   * Find comments by user ID
   */
  async findByUserId(userId: number): Promise<Comment[]> {
    return this.getAll({
      filter: { userId },
      sort: { createdAt: 'desc' }
    });
  }

  /**
   * Find approved comments
   */
  async findApproved(): Promise<Comment[]> {
    return this.getAll({
      filter: { isApproved: true },
      sort: { createdAt: 'asc' }
    });
  }

  /**
   * Find replies to a comment
   */
  async findReplies(parentId: number): Promise<Comment[]> {
    return this.getAll({
      filter: { parentId },
      sort: { createdAt: 'asc' }
    });
  }

  /**
   * Approve a comment
   */
  async approve(id: number | string): Promise<Comment & { id: number | string }> {
    return this.update(id, {
      isApproved: true,
      approvedAt: new Date()
    });
  }

  /**
   * Unapprove a comment
   */
  async unapprove(id: number | string): Promise<Comment & { id: number | string }> {
    return this.update(id, {
      isApproved: false,
      approvedAt: null
    });
  }

  /**
   * Create a new comment
   */
  async createComment(commentData: Omit<Comment, 'id' | 'createdAt' | 'updatedAt'>): Promise<Comment & { id: number | string }> {
    const now = new Date();
    const commentToCreate = {
      ...commentData,
      createdAt: now,
      updatedAt: now
    };
    return this.create(commentToCreate);
  }

  /**
   * Update comment with automatic timestamp update
   */
  async updateComment(id: number | string, data: Partial<Omit<Comment, 'id' | 'createdAt' | 'updatedAt'>>): Promise<Comment & { id: number | string }> {
    const updateData = {
      ...data,
      updatedAt: new Date()
    };
    return this.update(id, updateData);
  }

  /**
   * Get comment with author and post information
   */
  async getCommentWithDetails(id: number | string): Promise<(Comment & { author: User; post: Post }) | null> {
    const query = `
      SELECT c.*, 
             u.username, u.email, u.firstName, u.lastName,
             p.title as postTitle, p.slug as postSlug
      FROM comments c
      JOIN users u ON c.userId = u.id
      JOIN posts p ON c.postId = p.id
      WHERE c.id = ?
    `;
    const results = await this.rawQuery(query, [id]);
    return results[0] || null;
  }

  /**
   * Get comment thread (comment with all its replies)
   */
  async getCommentThread(id: number | string): Promise<(Comment & { author: User; replies: Comment[] }) | null> {
    const comment = await this.getCommentWithDetails(id);
    if (!comment) {
      return null;
    }

    const replies = await this.findReplies(Number(id));
    const repliesWithAuthors = await Promise.all(
      replies.map(reply => this.getCommentWithDetails(reply.id))
    );

    return {
      ...comment,
      replies: repliesWithAuthors.filter((reply): reply is Comment & { author: User; post: Post } => reply !== null)
    };
  }
} 