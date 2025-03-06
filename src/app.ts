import express, { Request, Response, NextFunction, Express } from 'express';
import cors from 'cors';
import swaggerUi from 'swagger-ui-express';
import { configureRoutes } from './routes';
import { config } from './utils/env';
import { createLogger } from './utils/logger';
import { errorHandler, notFoundHandler, ApiError } from './middleware/errorHandler';
import swaggerDocs from './utils/swagger';
import { generateSwaggerSpec } from './utils/swagger';
import { configureSecurityMiddleware } from './middleware/security';
import { standardLimiter } from './middleware/rateLimiter';
import path from 'path';

// Initialize logger
const logger = createLogger('App');

// Initialize the express application
const app: Express = express();
const PORT = config.PORT;

// Configure CORS
app.use(cors({
  origin: config.CORS_ORIGIN,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Apply rate limiting
app.use(standardLimiter);

// Configure middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Configure security middleware
configureSecurityMiddleware(app);

// Serve static files from the public directory
app.use(express.static(path.join(__dirname, '..', '..', 'public')));

// Set up Swagger
const swaggerSpec = generateSwaggerSpec();
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));
logger.info('Swagger documentation available at /api-docs');

// Add request logging
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.path}`);
  next();
});

// Configure API routes
configureRoutes(app);

// Serve the HTML interface for all non-API routes
app.get('*', (req: Request, res: Response, next: NextFunction) => {
  // Only serve index.html for non-API routes that aren't static files
  if (!req.path.startsWith('/api') && !req.path.includes('.')) {
    res.sendFile(path.join(__dirname, '..', '..', 'public', 'index.html'));
  } else {
    next();
  }
});

// Add 404 handler
app.use((req: Request, res: Response, next: NextFunction) => {
  next(ApiError.notFound(`Route not found: ${req.method} ${req.path}`));
});

// Add global error handler
app.use(errorHandler);

// Start the server if this file is being run directly
if (require.main === module) {
  app.listen(PORT, () => {
    logger.info(`Server is running on http://localhost:${PORT}`);
  });
}

export default app;