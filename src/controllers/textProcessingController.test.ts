import { Request, Response } from 'express';
import { TextProcessingController } from './textProcessingController';
import { ApiError } from '../middleware/errorHandler';

// Mock the child_process module
jest.mock('child_process', () => ({
  exec: jest.fn()
}));

// Mock the util module to return our mocked exec
jest.mock('util', () => ({
  promisify: jest.fn((fn: Function) => {
    return async (...args: any[]) => {
      return new Promise((resolve, reject) => {
        const callback = (error: Error | null, stdout: string, stderr: string) => {
          if (error) {
            reject(error);
          } else {
            resolve({ stdout, stderr });
          }
        };
        fn(...args, callback);
      });
    };
  })
}));

// Mock the logger
jest.mock('../utils/logger', () => ({
  createLogger: jest.fn(() => ({
    error: jest.fn(),
    warn: jest.fn(),
    info: jest.fn(),
    debug: jest.fn()
  }))
}));

// Mock the config
jest.mock('../utils/env', () => ({
  config: {
    PYTHON_PATH: 'python'
  }
}));

describe('TextProcessingController', () => {
  let controller: TextProcessingController;
  let req: Partial<Request>;
  let res: Partial<Response>;
  let next: jest.Mock;
  
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Setup request and response objects
    req = {
      body: {}
    };
    
    res = {
      json: jest.fn(),
      status: jest.fn().mockReturnThis()
    };
    
    next = jest.fn();
    
    // Mock the exec function for successful responses
    const { exec } = require('child_process');
    exec.mockImplementation((cmd: string, callback: (error: Error | null, stdout: string, stderr: string) => void) => {
      // Different mock responses based on the command
      if (cmd.includes('sentiment.py')) {
        callback(null, JSON.stringify({
          label: 'positive',
          score: 0.8
        }), '');
      } else if (cmd.includes('translator_module.py')) {
        callback(null, JSON.stringify({
          translated: 'Hola mundo',
          sourceLang: 'en',
          targetLang: 'es'
        }), '');
      } else if (cmd.includes('summarizer.py')) {
        callback(null, JSON.stringify({
          summary: 'This is a summary.',
          originalLength: 100,
          summaryLength: 20
        }), '');
      } else {
        callback(new Error('Unknown command'), '', 'Error executing command');
      }
    });
    
    // Setup controller after mocks
    controller = new TextProcessingController();
  });
  
  describe('analyzeSentiment', () => {
    it('should analyze sentiment successfully', async () => {
      // Setup request
      req.body = { text: 'This is a positive text!' };
      
      // Call the implementation method directly
      await controller._analyzeSentiment(req as Request, res as Response);
      
      // Verify response
      expect(res.json).toHaveBeenCalledWith({
        label: 'positive',
        score: 0.8
      });
      expect(next).not.toHaveBeenCalled();
    });
    
    it('should handle missing text parameter', async () => {
      // Setup request with missing text
      req.body = {};
      
      // Call the implementation method directly
      try {
        await controller._analyzeSentiment(req as Request, res as Response);
        fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        expect((error as ApiError).statusCode).toBe(400);
      }
    });
  });
  
  describe('translateText', () => {
    it('should translate text successfully', async () => {
      // Setup request
      req.body = { 
        text: 'Hello world', 
        sourceLang: 'en', 
        targetLang: 'es' 
      };
      
      // Call the implementation method directly
      await controller._translateText(req as Request, res as Response);
      
      // Verify response
      expect(res.json).toHaveBeenCalledWith({
        translated: 'Hola mundo',
        sourceLang: 'en',
        targetLang: 'es'
      });
      expect(next).not.toHaveBeenCalled();
    });
    
    it('should handle missing parameters', async () => {
      // Setup request with missing parameters
      req.body = { text: 'Hello world' };
      
      // Call the implementation method directly
      try {
        await controller._translateText(req as Request, res as Response);
        fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        expect((error as ApiError).statusCode).toBe(400);
      }
    });
  });
  
  describe('summarizeText', () => {
    it('should summarize text successfully', async () => {
      // Setup request
      req.body = { 
        text: 'This is a long text that needs to be summarized. It contains multiple sentences with various information. The summarization should pick the most important parts.',
        maxLength: 2
      };
      
      // Call the implementation method directly
      await controller._summarizeText(req as Request, res as Response);
      
      // Verify response
      expect(res.json).toHaveBeenCalledWith({
        summary: 'This is a summary.',
        originalLength: 100,
        summaryLength: 20
      });
      expect(next).not.toHaveBeenCalled();
    });
    
    it('should handle missing text parameter', async () => {
      // Setup request with missing text
      req.body = { maxLength: 2 };
      
      // Call the implementation method directly
      try {
        await controller._summarizeText(req as Request, res as Response);
        fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        expect((error as ApiError).statusCode).toBe(400);
      }
    });
    
    it('should handle invalid maxLength parameter', async () => {
      // Setup request with invalid maxLength
      req.body = { 
        text: 'This is some text',
        maxLength: -1
      };
      
      // Call the implementation method directly
      try {
        await controller._summarizeText(req as Request, res as Response);
        fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        expect((error as ApiError).statusCode).toBe(400);
      }
    });
  });
}); 