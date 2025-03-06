import request from 'supertest';

// Mock the env module before importing app
jest.mock('./utils/env', () => {
  // Mock the config object
  const mockConfig = {
    PORT: 3000,
    NODE_ENV: 'test',
    LOG_LEVEL: 'info',
    CORS_ORIGIN: '*',
    PYTHON_PATH: 'python',
    kindroid: {
      apiKey: 'kn_test',
      aiId: 'test-ai-id',
    },
    redis: {
      host: '',
      port: 6379,
      password: '',
      db: 0,
    },
    jwt: {
      secret: 'test-jwt-secret-that-is-at-least-32-characters',
      expiresIn: '1d'
    },
    github: {
      token: 'test-github-token',
    },
    webhooks: {
      enabled: false,
      secret: 'test-webhook-secret',
    }
  };
  
  return {
    config: mockConfig,
    // Mock the validateEnv function to do nothing
    validateEnv: jest.fn()
  };
});

// Now import app after the mock is set up
import app from './app';

describe('Express App', () => {
  beforeEach(() => {
    // Reset all mocks
    jest.resetAllMocks();
  });

  describe('GET /', () => {
    it('should return welcome message', async () => {
      const response = await request(app).get('/');
      expect(response.status).toBe(200);
      expect(response.text).toBe('Welcome to my project!');
    });
  });

  describe('Invalid Routes', () => {
    it('should return 404 for non-existent route', async () => {
      const response = await request(app).get('/nonexistent-route');
      
      expect(response.status).toBe(404);
      expect(response.body).toHaveProperty('error');
    });
  });
  
  describe('API Documentation', () => {
    it('should serve API documentation', async () => {
      const response = await request(app).get('/api-docs');
      
      // Either redirects to the docs UI or serves the docs directly
      expect([200, 301, 302, 307, 308]).toContain(response.status);
    });
  });
  
  describe('Health Check', () => {
    it('should return health status', async () => {
      const response = await request(app).get('/health');
      
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('status', 'ok');
    });
  });
});
