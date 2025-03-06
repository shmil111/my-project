/**
 * Security Middleware
 * 
 * Implements various security measures for the application including:
 * - Content Security Policy
 * - XSS Protection
 * - Prevention of clickjacking
 * - Secure headers
 */

import { Express, Request, Response, NextFunction } from 'express';
import helmet from 'helmet';
import { createLogger } from '../utils/logger';
import { config } from '../config';

// Initialize logger
const logger = createLogger('Security');

/**
 * Configure security middleware for the Express application
 * @param app Express application
 */
export function configureSecurityMiddleware(app: Express): void {
  // Apply Helmet middleware for security headers
  app.use(helmet());
  
  // Content Security Policy (CSP)
  app.use(helmet.contentSecurityPolicy({
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net"], // Allow scripts from CDN for Swagger UI
      styleSrc: ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net"], // Allow styles from CDN for Swagger UI
      imgSrc: ["'self'", "data:"],
      connectSrc: ["'self'"],
      fontSrc: ["'self'"],
      objectSrc: ["'none'"],
      mediaSrc: ["'none'"],
      frameSrc: ["'none'"],
      upgradeInsecureRequests: [],
    },
  }));
  
  // Prevent XSS attacks
  app.use(helmet.xssFilter());
  
  // Prevent clickjacking
  app.use(helmet.frameguard({ action: 'deny' }));
  
  // Disable X-Powered-By header
  app.use(helmet.hidePoweredBy());
  
  // Enable Strict Transport Security
  app.use(helmet.hsts({
    maxAge: 15552000, // 180 days in seconds
    includeSubDomains: true,
    preload: true,
  }));
  
  // Prevent MIME type sniffing
  app.use(helmet.noSniff());
  
  // Add custom security check middleware
  app.use(securityCheckMiddleware);
  
  logger.info('Security middleware configured');
}

/**
 * Custom security check middleware
 * Logs potential security issues and takes appropriate action
 */
function securityCheckMiddleware(req: Request, res: Response, next: NextFunction): void {
  // Check for suspicious query parameters
  const suspiciousParams = ['<script>', 'javascript:', 'eval(', 'onerror=', 'document.cookie'];
  const queryParams = req.query;
  
  for (const param in queryParams) {
    const value = String(queryParams[param]);
    for (const suspicious of suspiciousParams) {
      if (value.toLowerCase().includes(suspicious.toLowerCase())) {
        logger.warn(`Potential XSS attempt detected from IP ${req.ip} with parameter: ${param}=${value}`);
        // Don't send detailed error info to the client to avoid information leakage
        res.status(403).json({ status: 'error', message: 'Request contains disallowed content' });
        return; // Return after sending response
      }
    }
  }
  
  // Check request body for suspicious content if it's JSON
  if (req.body && typeof req.body === 'object') {
    const bodyStr = JSON.stringify(req.body);
    for (const suspicious of suspiciousParams) {
      if (bodyStr.toLowerCase().includes(suspicious.toLowerCase())) {
        logger.warn(`Potential XSS attempt detected from IP ${req.ip} in request body: ${bodyStr.substring(0, 100)}...`);
        // Don't send detailed error info to the client to avoid information leakage
        res.status(403).json({ status: 'error', message: 'Request contains disallowed content' });
        return; // Return after sending response
      }
    }
  }
  
  next();
} 