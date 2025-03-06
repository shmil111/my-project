/**
 * Rate Limiting Middleware
 * 
 * This middleware implements rate limiting for API endpoints to prevent abuse.
 * Different rate limits are applied to different types of routes.
 */

import rateLimit from 'express-rate-limit';
import { createLogger } from '../utils/logger';
import { Request, Response } from 'express';
import { config } from '../config';

// Initialize logger
const logger = createLogger('RateLimiter');

// Skip rate limiting in test environment
const skipInTest = () => config.env === 'test';

// Helper to get IP address from request
const getIpFromRequest = (req: Request): string => {
  // Get IP from proxy headers if behind a proxy
  const xForwardedFor = req.headers['x-forwarded-for'];
  if (xForwardedFor) {
    const ips = Array.isArray(xForwardedFor) 
      ? xForwardedFor[0] 
      : xForwardedFor.split(',')[0].trim();
    return ips;
  }
  
  return req.ip || 'unknown';
};

// Handler for when rate limit is exceeded
const handleRateLimitExceeded = (req: Request, res: Response): void => {
  const ip = getIpFromRequest(req);
  logger.warn(`Rate limit exceeded for IP: ${ip}, path: ${req.path}`);
};

/**
 * Standard API rate limiter
 * Allows 100 requests per minute
 */
export const standardLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 100, // limit each IP to 100 requests per windowMs
  standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
  legacyHeaders: false, // Disable the `X-RateLimit-*` headers
  message: { 
    status: 'error',
    message: 'Too many requests, please try again later.'
  },
  skip: skipInTest,
  keyGenerator: getIpFromRequest,
  handler: (req, res) => {
    handleRateLimitExceeded(req, res);
    res.status(429).json({ 
      status: 'error',
      message: 'Too many requests, please try again later.' 
    });
  }
});

/**
 * Stricter rate limiter for authentication routes
 * Allows 20 requests per minute
 */
export const authLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 20, // limit each IP to 20 requests per windowMs
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    status: 'error',
    message: 'Too many authentication attempts, please try again later.'
  },
  skip: skipInTest,
  keyGenerator: getIpFromRequest,
  handler: (req, res) => {
    handleRateLimitExceeded(req, res);
    res.status(429).json({ 
      status: 'error',
      message: 'Too many authentication attempts, please try again later.' 
    });
  }
});

/**
 * Webhook rate limiter
 * Allows 60 requests per minute for webhooks
 */
export const webhookLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 60, // limit each IP to 60 requests per windowMs
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    status: 'error',
    message: 'Too many webhook requests, please try again later.'
  },
  skip: skipInTest,
  keyGenerator: getIpFromRequest,
  handler: (req, res) => {
    handleRateLimitExceeded(req, res);
    res.status(429).json({ 
      status: 'error',
      message: 'Too many webhook requests, please try again later.' 
    });
  }
});

/**
 * Heavy operation rate limiter
 * Allows 10 requests per minute for resource-intensive operations
 */
export const heavyOperationLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 10, // limit each IP to 10 requests per windowMs
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    status: 'error',
    message: 'Too many requests for this operation, please try again later.'
  },
  skip: skipInTest,
  keyGenerator: getIpFromRequest,
  handler: (req, res) => {
    handleRateLimitExceeded(req, res);
    res.status(429).json({ 
      status: 'error',
      message: 'Too many requests for this operation, please try again later.' 
    });
  }
}); 