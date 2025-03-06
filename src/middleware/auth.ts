/**
 * Authentication Middleware
 * 
 * Provides JWT-based authentication for securing API endpoints.
 */

import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { ApiError } from './errorHandler';
import { createLogger } from '../utils/logger';
import { config } from '../config';

// Initialize logger
const logger = createLogger('Auth');

// JWT secret key - should be in environment variables in production
const JWT_SECRET = config.jwtSecret || 'your-secret-key';

export interface AuthUser {
  id: string;
  username: string;
  roles: string[];
}

// Extend Express Request type to include user
declare global {
  namespace Express {
    interface Request {
      user?: AuthUser;
    }
  }
}

/**
 * Authenticate using JWT token from Authorization header
 */
export const authenticate = (req: Request, res: Response, next: NextFunction): void => {
  // Get the token from the Authorization header
  const authHeader = req.headers.authorization;
  const token = authHeader && authHeader.split(' ')[1]; // "Bearer TOKEN"
  
  if (!token) {
    logger.debug('No token provided');
    throw ApiError.unauthorized('Authentication token is required');
  }
  
  try {
    // Verify the token
    const decoded = jwt.verify(token, JWT_SECRET) as AuthUser;
    
    // Attach the user to the request
    req.user = decoded;
    logger.debug(`Authenticated user: ${decoded.username}`);
    
    next();
  } catch (error) {
    logger.error(`Authentication error: ${error}`);
    throw ApiError.unauthorized('Invalid or expired token');
  }
};

/**
 * Check if user has required role
 * @param roles Allowed roles for the endpoint
 */
export const authorize = (roles: string[] = []) => {
  return (req: Request, res: Response, next: NextFunction): void => {
    // Check if user is authenticated
    if (!req.user) {
      logger.error('Authorization attempted without authentication');
      throw ApiError.unauthorized('User is not authenticated');
    }
    
    // If no roles are required, allow access
    if (!roles.length) {
      return next();
    }
    
    // Check if user has any of the required roles
    const hasRole = req.user.roles.some(role => roles.includes(role));
    
    if (!hasRole) {
      logger.warn(`User ${req.user.username} does not have required roles: ${roles.join(', ')}`);
      throw ApiError.forbidden('Insufficient permissions');
    }
    
    logger.debug(`User ${req.user.username} authorized with roles: ${req.user.roles.join(', ')}`);
    next();
  };
};

/**
 * Generate a JWT token for a user
 * @param user User data to encode in the token
 * @param expiresIn Token expiration time (default: 1 day)
 * @returns JWT token
 */
export const generateToken = (user: AuthUser, expiresIn: string = '1d'): string => {
  return jwt.sign(user, JWT_SECRET, { expiresIn });
};

/**
 * Verify and decode a JWT token
 * @param token JWT token to verify
 * @returns Decoded user data or null if invalid
 */
export const verifyToken = (token: string): AuthUser | null => {
  try {
    return jwt.verify(token, JWT_SECRET) as AuthUser;
  } catch (error) {
    logger.error(`Token verification error: ${error}`);
    return null;
  }
}; 