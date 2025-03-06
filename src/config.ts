/**
 * Application Configuration
 * 
 * Centralizes application configuration and environment variables
 */

// Import environment variables
const env = process.env;

interface RedisConfig {
  host: string;
  port: number;
  password?: string;
  db: number;
}

interface GithubConfig {
  token: string;
  username: string;
}

interface WebhooksConfig {
  githubSecret: string;
  enabled: boolean;
}

interface AppConfig {
  env: string;
  port: number;
  apiPrefix: string;
  logLevel: string;
  pythonPath: string;
  corsOrigin: string | string[];
  redis: RedisConfig;
  jwtSecret: string;
  jwtExpiresIn: string;
  github: GithubConfig;
  webhooks: WebhooksConfig;
}

/**
 * Application configuration
 */
export const config: AppConfig = {
  // Server configuration
  env: env.NODE_ENV || 'development',
  port: parseInt(env.PORT || '3000', 10),
  apiPrefix: env.API_PREFIX || '',
  logLevel: env.LOG_LEVEL || 'info',
  pythonPath: env.PYTHON_PATH || 'python',
  
  // CORS configuration
  corsOrigin: env.CORS_ORIGIN ? env.CORS_ORIGIN.split(',') : '*',
  
  // Redis configuration (for long-term memory)
  redis: {
    host: env.REDIS_HOST || 'localhost',
    port: parseInt(env.REDIS_PORT || '6379', 10),
    password: env.REDIS_PASSWORD,
    db: parseInt(env.REDIS_DB || '0', 10),
  },
  
  // JWT configuration
  jwtSecret: env.JWT_SECRET || 'my-project-secret-key-change-in-production',
  jwtExpiresIn: env.JWT_EXPIRES_IN || '1d',
  
  // GitHub configuration
  github: {
    token: env.GITHUB_TOKEN || '',
    username: env.GITHUB_USERNAME || 'shmil111',
  },
  
  // Webhooks configuration
  webhooks: {
    githubSecret: env.GITHUB_WEBHOOK_SECRET || '',
    enabled: env.ENABLE_WEBHOOKS === 'true',
  },
};

/**
 * Check if the environment is production
 */
export const isProd = (): boolean => config.env === 'production';

/**
 * Check if the environment is development
 */
export const isDev = (): boolean => config.env === 'development';

/**
 * Check if the environment is test
 */
export const isTest = (): boolean => config.env === 'test'; 