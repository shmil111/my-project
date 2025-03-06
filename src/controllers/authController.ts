/**
 * Authentication Controller
 * 
 * Handles user authentication and authorization
 */

import { Request, Response } from 'express';
import bcrypt from 'bcrypt';
import { v4 as uuidv4 } from 'uuid';
import { generateToken, verifyToken, AuthUser } from '../middleware/auth';
import { createLogger } from '../utils/logger';
import { MemoryFactory } from '../services/MemoryFactory';
import { MemoryType } from '../services/MemoryService';

// Initialize logger
const logger = createLogger('AuthController');

// Memory namespace for users
const USER_NAMESPACE = 'users';

/**
 * User for authentication
 */
interface User {
  id: string;
  username: string;
  email: string;
  passwordHash: string;
  roles: string[];
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Authentication controller
 */
export class AuthController {
  constructor() {
    // Bind methods to this instance
    this.login = this.login.bind(this);
    this.register = this.register.bind(this);
    this.validateToken = this.validateToken.bind(this);
    this.getProfile = this.getProfile.bind(this);
  }
  
  /**
   * Login user
   * @param req Request
   * @param res Response
   */
  public async login(req: Request, res: Response): Promise<void> {
    const { username, password } = req.body;
    
    logger.debug(`Login attempt for user: ${username}`);
    
    try {
      // Get user from memory
      const memory = await MemoryFactory.getLongTermMemory(USER_NAMESPACE);
      const user = await memory.get<User>(username);
      
      if (!user) {
        logger.debug(`User not found: ${username}`);
        res.status(401).json({
          success: false,
          message: 'Invalid username or password',
        });
        return;
      }
      
      // Compare passwords
      const isPasswordValid = await bcrypt.compare(password, user.passwordHash);
      
      if (!isPasswordValid) {
        logger.debug(`Invalid password for user: ${username}`);
        res.status(401).json({
          success: false,
          message: 'Invalid username or password',
        });
        return;
      }
      
      // Generate token
      const tokenUser: AuthUser = {
        id: user.id,
        username: user.username,
        roles: user.roles,
      };
      
      const token = generateToken(tokenUser);
      
      logger.info(`User logged in: ${username}`);
      res.status(200).json({
        success: true,
        message: 'Login successful',
        token,
        user: {
          id: user.id,
          username: user.username,
          email: user.email,
          roles: user.roles,
        },
      });
    } catch (error) {
      logger.error(`Login error: ${error}`);
      res.status(500).json({
        success: false,
        message: 'Failed to login',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Register new user
   * @param req Request
   * @param res Response
   */
  public async register(req: Request, res: Response): Promise<void> {
    const { username, email, password } = req.body;
    
    logger.debug(`Registration attempt for user: ${username}`);
    
    try {
      // Get memory service
      const memory = await MemoryFactory.getLongTermMemory(USER_NAMESPACE);
      
      // Check if username already exists
      const existingUser = await memory.get<User>(username);
      
      if (existingUser) {
        logger.debug(`Username already exists: ${username}`);
        res.status(409).json({
          success: false,
          message: 'Username already exists',
        });
        return;
      }
      
      // Hash password
      const saltRounds = 10;
      const passwordHash = await bcrypt.hash(password, saltRounds);
      
      // Create new user
      const newUser: User = {
        id: uuidv4(),
        username,
        email,
        passwordHash,
        roles: ['user'], // Default role
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      
      // Store user in memory
      const success = await memory.set(username, newUser);
      
      if (!success) {
        throw new Error('Failed to store user');
      }
      
      // Generate token
      const tokenUser: AuthUser = {
        id: newUser.id,
        username: newUser.username,
        roles: newUser.roles,
      };
      
      const token = generateToken(tokenUser);
      
      logger.info(`User registered: ${username}`);
      res.status(201).json({
        success: true,
        message: 'Registration successful',
        token,
        user: {
          id: newUser.id,
          username: newUser.username,
          email: newUser.email,
          roles: newUser.roles,
        },
      });
    } catch (error) {
      logger.error(`Registration error: ${error}`);
      res.status(500).json({
        success: false,
        message: 'Failed to register',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Validate a token
   * @param req Request
   * @param res Response
   */
  public validateToken(req: Request, res: Response): void {
    const { token } = req.body;
    
    logger.debug('Token validation request');
    
    if (!token) {
      res.status(400).json({
        success: false,
        message: 'Token is required',
      });
      return;
    }
    
    const user = verifyToken(token);
    
    if (!user) {
      res.status(401).json({
        success: false,
        message: 'Invalid or expired token',
      });
      return;
    }
    
    logger.debug(`Token validated for user: ${user.username}`);
    res.status(200).json({
      success: true,
      message: 'Token is valid',
      user,
    });
  }
  
  /**
   * Get user profile
   * @param req Request (with user from JWT authentication)
   * @param res Response
   */
  public async getProfile(req: Request, res: Response): Promise<void> {
    // This endpoint requires authentication, so user should be available
    const currentUser = req.user;
    
    if (!currentUser) {
      res.status(401).json({
        success: false,
        message: 'Not authenticated',
      });
      return;
    }
    
    try {
      // Get full user details
      const memory = await MemoryFactory.getLongTermMemory(USER_NAMESPACE);
      const user = await memory.get<User>(currentUser.username);
      
      if (!user) {
        throw new Error(`User not found: ${currentUser.username}`);
      }
      
      // Return user profile (without password hash)
      logger.debug(`Profile retrieved for user: ${user.username}`);
      res.status(200).json({
        success: true,
        user: {
          id: user.id,
          username: user.username,
          email: user.email,
          roles: user.roles,
          createdAt: user.createdAt,
          updatedAt: user.updatedAt,
        },
      });
    } catch (error) {
      logger.error(`Get profile error: ${error}`);
      res.status(500).json({
        success: false,
        message: 'Failed to retrieve profile',
        error: (error as Error).message,
      });
    }
  }
} 