/**
 * Error Handling Middleware
 * 
 * This module provides middleware for consistent error handling throughout the application.
 */

import { Request, Response, NextFunction } from 'express';
import { createLogger } from '../utils/logger';

const logger = createLogger('ErrorHandler');

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  statusCode: number;
  code?: string;
  
  constructor(statusCode: number, message: string, code?: string) {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.name = 'ApiError';
  }
  
  static badRequest(message: string, code?: string): ApiError {
    return new ApiError(400, message, code);
  }
  
  static unauthorized(message: string = 'Unauthorized', code?: string): ApiError {
    return new ApiError(401, message, code);
  }
  
  static forbidden(message: string = 'Forbidden', code?: string): ApiError {
    return new ApiError(403, message, code);
  }
  
  static notFound(message: string = 'Resource not found', code?: string): ApiError {
    return new ApiError(404, message, code);
  }
  
  static internalServer(message: string = 'Internal server error', code?: string): ApiError {
    return new ApiError(500, message, code);
  }
}

/**
 * Catch-all for 404 errors
 */
export function notFoundHandler(req: Request, res: Response, next: NextFunction): void {
  const error = ApiError.notFound(`Cannot ${req.method} ${req.path}`);
  next(error);
}

/**
 * Global error handler middleware
 */
export function errorHandler(err: any, req: Request, res: Response, next: NextFunction): void {
  const statusCode = err.statusCode || 500;
  const message = err.message || 'Something went wrong';
  const code = err.code || 'INTERNAL_ERROR';
  
  // Only log 5xx errors as errors, log 4xx as warnings
  if (statusCode >= 500) {
    logger.error(`Error ${code}: ${message}`, err);
  } else {
    logger.warn(`Client error ${code}: ${message} [${statusCode}]`);
  }
  
  // Include stack trace in development but not in production
  const isDevelopment = process.env.NODE_ENV !== 'production';
  
  res.status(statusCode).json({
    success: false,
    error: {
      message,
      code,
      ...(isDevelopment && err.stack ? { stack: err.stack.split('\n') } : {})
    }
  });
}

/**
 * Async route handler wrapper to catch promise rejections
 */
export function asyncHandler(fn: (req: Request, res: Response, next: NextFunction) => Promise<any>) {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
} 