import { BaseRepository } from './BaseRepository';
import { DatabaseRecord } from '../../services/DatabaseService';
import { databaseConfig } from '../config/database.config';

export interface User extends DatabaseRecord {
  username: string;
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
  role: 'admin' | 'user' | 'guest';
  isActive: boolean;
  lastLogin?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export class UserRepository extends BaseRepository<User> {
  constructor() {
    super('users', databaseConfig);
  }

  /**
   * Find user by email
   */
  async findByEmail(email: string): Promise<User | null> {
    const users = await this.getAll({
      filter: { email }
    });
    return users[0] || null;
  }

  /**
   * Find user by username
   */
  async findByUsername(username: string): Promise<User | null> {
    const users = await this.getAll({
      filter: { username }
    });
    return users[0] || null;
  }

  /**
   * Find active users
   */
  async findActiveUsers(): Promise<User[]> {
    return this.getAll({
      filter: { isActive: true }
    });
  }

  /**
   * Update user's last login time
   */
  async updateLastLogin(id: number | string): Promise<User & { id: number | string }> {
    return this.update(id, {
      lastLogin: new Date()
    });
  }

  /**
   * Deactivate user
   */
  async deactivateUser(id: number | string): Promise<User & { id: number | string }> {
    return this.update(id, {
      isActive: false
    });
  }

  /**
   * Activate user
   */
  async activateUser(id: number | string): Promise<User & { id: number | string }> {
    return this.update(id, {
      isActive: true
    });
  }

  /**
   * Create a new user with password hashing
   */
  async createUser(userData: Omit<User, 'id' | 'createdAt' | 'updatedAt'>): Promise<User & { id: number | string }> {
    const now = new Date();
    const userToCreate = {
      ...userData,
      createdAt: now,
      updatedAt: now
    };
    return this.create(userToCreate);
  }

  /**
   * Update user with automatic timestamp update
   */
  async updateUser(id: number | string, data: Partial<Omit<User, 'id' | 'createdAt' | 'updatedAt'>>): Promise<User & { id: number | string }> {
    const updateData = {
      ...data,
      updatedAt: new Date()
    };
    return this.update(id, updateData);
  }

  /**
   * Search users by name or email
   */
  async searchUsers(searchTerm: string): Promise<User[]> {
    const query = `
      SELECT * FROM users 
      WHERE username LIKE ? 
      OR email LIKE ? 
      OR firstName LIKE ? 
      OR lastName LIKE ?
    `;
    const searchPattern = `%${searchTerm}%`;
    return this.rawQuery(query, [searchPattern, searchPattern, searchPattern, searchPattern]);
  }
} 