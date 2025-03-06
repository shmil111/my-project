/**
 * Environment Configuration
 * 
 * Loads and validates environment variables for the application.
 */

import dotenv from 'dotenv';
import { createLogger } from './logger';

// Load environment variables from .env file
dotenv.config();

// Initialize logger
const logger = createLogger('Env');

/**
 * Environment variable configuration
 */
interface EnvConfig {
  // Variable name
  name: string;
  // Whether the variable is required
  required: boolean;
  // Default value if not provided
  default?: string;
  // Validation function
  validate?: (value: string) => boolean;
  // Error message if validation fails
  errorMessage?: string;
}

/**
 * Common validation patterns
 */
const validators = {
  // Validate numeric values
  isNumber: (value: string) => !isNaN(Number(value)),
  
  // Validate boolean values
  isBoolean: (value: string) => ['true', 'false', '0', '1'].includes(value.toLowerCase()),
  
  // Validate URL pattern
  isUrl: (value: string) => {
    try {
      new URL(value);
      return true;
    } catch (e) {
      return false;
    }
  },
  
  // Validate port number (0-65535)
  isPort: (value: string) => {
    const port = parseInt(value, 10);
    return !isNaN(port) && port >= 0 && port <= 65535;
  },
  
  // Validate JWT secret minimum length
  isStrongSecret: (value: string) => value.length >= 32,
  
  // Validate Redis URI
  isRedisUri: (value: string) => {
    return value.startsWith('redis://') || value.startsWith('rediss://');
  }
};

/**
 * Common env configurations
 */
const commonEnvConfigs: EnvConfig[] = [
  {
    name: 'NODE_ENV',
    required: true,
    default: 'development',
    validate: (value) => ['development', 'production', 'test'].includes(value),
    errorMessage: 'must be one of: development, production, test'
  },
  {
    name: 'PORT',
    required: true,
    default: '3000',
    validate: validators.isPort,
    errorMessage: 'must be a valid port number (0-65535)'
  },
  {
    name: 'LOG_LEVEL',
    required: false,
    default: 'info',
    validate: (value) => ['error', 'warn', 'info', 'debug'].includes(value),
    errorMessage: 'must be one of: error, warn, info, debug'
  },
  {
    name: 'JWT_SECRET',
    required: true,
    validate: validators.isStrongSecret,
    errorMessage: 'must be at least 32 characters long for security'
  }
];

/**
 * Validate environment variables
 * @param configs Array of environment variable configurations
 */
function validateEnv(configs: EnvConfig[]): void {
  let hasError = false;
  const missingVars: string[] = [];
  const invalidVars: string[] = [];
  
  configs.forEach(config => {
    const value = process.env[config.name];
    
    // Check if required variable is missing
    if (config.required && !value && !config.default) {
      missingVars.push(config.name);
      hasError = true;
      return;
    }
    
    // If value exists and there's a validation function, check it
    if (value && config.validate && !config.validate(value)) {
      invalidVars.push(`${config.name}${config.errorMessage ? ': ' + config.errorMessage : ''}`);
      hasError = true;
    }
    
    // Set default value if not provided
    if (!value && config.default) {
      process.env[config.name] = config.default;
    }
  });
  
  // Log missing and invalid variables
  if (missingVars.length > 0) {
    logger.error(`Missing required environment variables: ${missingVars.join(', ')}`);
  }
  
  if (invalidVars.length > 0) {
    logger.error(`Invalid environment variables: ${invalidVars.join(', ')}`);
  }
  
  // Exit process if any errors occurred
  if (hasError) {
    logger.error('Application startup failed due to environment configuration issues');
    process.exit(1);
  }
  
  logger.info('Environment variables validated successfully');
}

// Validate environment variables
validateEnv([
  ...commonEnvConfigs,
  {
    name: 'CORS_ORIGIN',
    required: false,
    default: '*',
    validate: (value: string) => true // Any value is acceptable for CORS_ORIGIN
  },
  {
    name: 'REDIS_HOST',
    required: false,
    default: '',
  },
  {
    name: 'REDIS_PORT',
    required: false,
    default: '6379',
    validate: validators.isPort,
    errorMessage: 'must be a valid port number (0-65535)'
  },
  {
    name: 'REDIS_PASSWORD',
    required: false,
  },
  {
    name: 'REDIS_DB',
    required: false,
    default: '0',
    validate: validators.isNumber,
    errorMessage: 'must be a number'
  },
  {
    name: 'GITHUB_TOKEN',
    required: false,
    validate: (value: string) => value.length > 30,
    errorMessage: 'should be at least 30 characters long'
  },
  {
    name: 'WEBHOOK_SECRET',
    required: false,
    validate: (value: string) => value.length >= 16,
    errorMessage: 'should be at least 16 characters long for security'
  },
  {
    name: 'PYTHON_PATH',
    required: false,
    default: 'python',
    validate: (value: string) => true, // Assuming any value is acceptable
    errorMessage: 'should be a valid Python path'
  },
  {
    name: 'KINDROID_API_KEY',
    required: false,
    validate: (value: string) => value.startsWith('kn_'),
    errorMessage: 'should start with "kn_"'
  },
  {
    name: 'KINDROID_AI_ID',
    required: false,
    validate: (value: string) => value.length > 0,
    errorMessage: 'should be a valid Kindroid AI ID'
  }
]);

// Configuration object
export const config = {
  // Server configuration
  PORT: parseInt(process.env.PORT || '3000', 10),
  NODE_ENV: process.env.NODE_ENV || 'development',
  LOG_LEVEL: process.env.LOG_LEVEL || 'info',
  CORS_ORIGIN: process.env.CORS_ORIGIN || '*',
  PYTHON_PATH: process.env.PYTHON_PATH || 'python',
  
  // Kindroid configuration
  kindroid: {
    apiKey: process.env.KINDROID_API_KEY || '',
    aiId: process.env.KINDROID_AI_ID || '',
  },
  
  // Redis configuration
  redis: {
    host: process.env.REDIS_HOST || '',
    port: parseInt(process.env.REDIS_PORT || '6379', 10),
    password: process.env.REDIS_PASSWORD,
    db: parseInt(process.env.REDIS_DB || '0', 10),
  },
  
  // JWT configuration
  jwt: {
    secret: process.env.JWT_SECRET || '',
    expiresIn: process.env.JWT_EXPIRES_IN || '1d'
  },
  
  // GitHub configuration 
  github: {
    token: process.env.GITHUB_TOKEN || '',
  },
  
  // Webhook configuration
  webhooks: {
    enabled: process.env.WEBHOOKS_ENABLED === 'true',
    secret: process.env.WEBHOOK_SECRET || '',
  },
  
  // Environment helper functions
  env: process.env.NODE_ENV || 'development',
  isProd: () => process.env.NODE_ENV === 'production',
  isDev: () => process.env.NODE_ENV === 'development',
  isTest: () => process.env.NODE_ENV === 'test',
};

logger.debug('Environment configuration loaded');

export default config; 