import { Request, Response } from 'express';
import { GistController } from '../../controllers/gistController';
import { GistService } from '../../services/GistService';
import { 
  createMockRequest, 
  createMockResponse, 
  assertHelpers 
} from '../../../testHelpers';

// Mock the GistService
jest.mock('../../services/GistService');

// Mock the logger to avoid console output during tests
jest.mock('../../utils/logger', () => ({
  createLogger: jest.fn().mockReturnValue({
    info: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
    warn: jest.fn(),
  }),
}));

describe('GistController', () => {
  let gistController: GistController;
  let mockRequest: Request;
  let mockResponse: Response & { statusCode: number; body: any; headers: Record<string, string> };
  
  const sampleGists = [
    {
      id: '1',
      description: 'Test Gist',
      files: {
        'file1.txt': {
          filename: 'file1.txt',
          content: 'Test content'
        }
      },
      public: true,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-02T00:00:00Z'
    }
  ];
  
  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Set up test environment
    mockRequest = createMockRequest();
    mockResponse = createMockResponse();
    
    // Create a new instance of GistController for each test
    gistController = new GistController();
  });
  
  describe('getGists', () => {
    it('should return all gists with status 200', async () => {
      // Mock GistService getGists method
      (GistService.prototype.getGists as jest.Mock).mockResolvedValue(sampleGists);
      
      // Set up request query
      mockRequest.query = { page: '1', perPage: '10' };
      
      // Call the controller method
      await gistController.getGists(mockRequest, mockResponse);
      
      // Check that the correct response was sent
      expect(mockResponse.statusCode).toBe(200);
      expect(mockResponse.body).toEqual({
        success: true,
        count: 1,
        gists: sampleGists,
      });
    });
    
    it('should handle errors and return status 500', async () => {
      // Mock GistService getGists method to throw an error
      const errorMessage = 'Failed to get gists';
      (GistService.prototype.getGists as jest.Mock).mockRejectedValue(new Error(errorMessage));
      
      // Call the controller method
      await gistController.getGists(mockRequest, mockResponse);
      
      // Check that the error response was sent
      expect(mockResponse.statusCode).toBe(500);
      expect(mockResponse.body).toEqual({
        success: false,
        message: 'Failed to get gists',
        error: errorMessage,
      });
    });
  });
  
  describe('getUserGists', () => {
    it('should return user gists with status 200', async () => {
      // Mock GistService getUserGists method
      (GistService.prototype.getUserGists as jest.Mock).mockResolvedValue(sampleGists);
      
      // Set up request params and query
      mockRequest.params = { username: 'shmil111' };
      mockRequest.query = { page: '1', perPage: '10' };
      
      // Call the controller method
      await gistController.getUserGists(mockRequest, mockResponse);
      
      // Check that the correct response was sent
      expect(mockResponse.statusCode).toBe(200);
      expect(mockResponse.body).toEqual({
        success: true,
        count: 1,
        gists: sampleGists,
      });
    });
    
    it('should handle errors and return status 500', async () => {
      // Mock GistService getUserGists method to throw an error
      const errorMessage = 'Failed to get user gists';
      (GistService.prototype.getUserGists as jest.Mock).mockRejectedValue(new Error(errorMessage));
      
      // Set up request params
      mockRequest.params = { username: 'shmil111' };
      
      // Call the controller method
      await gistController.getUserGists(mockRequest, mockResponse);
      
      // Check that the correct error response was sent
      expect(mockResponse.statusCode).toBe(500);
      expect(mockResponse.body).toEqual({
        success: false,
        message: 'Failed to get user gists',
        error: errorMessage,
      });
    });
  });
  
  describe('getGist', () => {
    it('should return a specific gist with status 200', async () => {
      // Mock GistService getGist method
      (GistService.prototype.getGist as jest.Mock).mockResolvedValue(sampleGists[0]);
      
      // Set up request params
      mockRequest.params = { id: '1' };
      
      // Call the controller method
      await gistController.getGist(mockRequest, mockResponse);
      
      // Check that the correct response was sent
      expect(mockResponse.statusCode).toBe(200);
      expect(mockResponse.body).toEqual({
        success: true,
        gist: sampleGists[0],
      });
    });
    
    it('should handle 404 errors and return status 404', async () => {
      // Mock GistService getGist method to throw a 404 error
      const errorMessage = 'Not found - 404';
      (GistService.prototype.getGist as jest.Mock).mockRejectedValue(new Error(errorMessage));
      
      // Set up request params
      mockRequest.params = { id: 'nonexistent' };
      
      // Call the controller method
      await gistController.getGist(mockRequest, mockResponse);
      
      // Check that the correct error response was sent
      expect(mockResponse.statusCode).toBe(404);
      expect(mockResponse.body).toEqual({
        success: false,
        message: 'Gist not found with ID: nonexistent',
      });
    });
    
    it('should handle other errors and return status 500', async () => {
      // Mock GistService getGist method to throw a generic error
      const errorMessage = 'Server error';
      (GistService.prototype.getGist as jest.Mock).mockRejectedValue(new Error(errorMessage));
      
      // Set up request params
      mockRequest.params = { id: '1' };
      
      // Call the controller method
      await gistController.getGist(mockRequest, mockResponse);
      
      // Check that the correct error response was sent
      expect(mockResponse.statusCode).toBe(500);
      expect(mockResponse.body).toEqual({
        success: false,
        message: 'Failed to get gist',
        error: errorMessage,
      });
    });
  });
  
  describe('createGist', () => {
    it('should create a gist and return status 201', async () => {
      // Mock GistService createGist method
      (GistService.prototype.createGist as jest.Mock).mockResolvedValue(sampleGists[0]);
      
      // Set up request body
      mockRequest.body = {
        description: 'Test Gist',
        public: true,
        files: {
          'file1.txt': {
            content: 'Test content'
          }
        },
      };
      
      // Call the controller method
      await gistController.createGist(mockRequest, mockResponse);
      
      // Check that the correct response was sent
      expect(mockResponse.statusCode).toBe(201);
      expect(mockResponse.body).toEqual({
        success: true,
        message: 'Gist created successfully',
        gist: sampleGists[0],
      });
    });
    
    it('should handle errors and return status 500', async () => {
      // Mock GistService createGist method to throw an error
      const errorMessage = 'Failed to create gist';
      (GistService.prototype.createGist as jest.Mock).mockRejectedValue(new Error(errorMessage));
      
      // Set up request body
      mockRequest.body = {
        description: 'Test Gist',
        public: true,
        files: {
          'file1.txt': {
            content: 'Test content'
          }
        },
      };
      
      // Call the controller method
      await gistController.createGist(mockRequest, mockResponse);
      
      // Check that the correct error response was sent
      expect(mockResponse.statusCode).toBe(500);
      expect(mockResponse.body).toEqual({
        success: false,
        message: 'Failed to create gist',
        error: errorMessage,
      });
    });
  });
  
  // Additional tests for other controller methods would follow the same pattern
}); 