import { Request, Response, NextFunction } from 'express';

/**
 * Wrapper for async route handlers to catch errors
 * @param fn Route handler function
 * @returns Wrapped route handler
 */
export const asyncHandler = (fn: Function) => (
  req: Request, 
  res: Response, 
  next: NextFunction
) => {
  Promise.resolve(fn(req, res, next)).catch(next);
}; 