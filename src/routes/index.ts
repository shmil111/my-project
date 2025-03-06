import { Express } from 'express';
import kindroidRoutes from './kindroidRoutes';
import { createLogger } from '../utils/logger';

const logger = createLogger('Routes');

/**
 * Configure all API routes
 * @param app: Express application
 */
export function configureRoutes(app: Express): void {
  // Register API routes
  app.use('/api/kindroid', kindroidRoutes);
  
  // Log registered routes
  logger.info('Routes configured successfully');
} 