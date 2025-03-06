import { Request, Response } from 'express';
import { body, validationResult } from 'express-validator';
import { pythonService } from '../services/pythonService';
import { ApiError } from '../middleware/errorHandler';
import { createLogger } from '../utils/logger';

const logger = createLogger('TextController');

/**
 * Text processing controller
 * Handles API endpoints for text processing features
 */
export class TextController {
  /**
   * Validate request
   */
  static validate(method: string) {
    switch (method) {
      case 'processText':
        return [
          body('text').isString().notEmpty().withMessage('Text is required'),
          body('action').isString().notEmpty().withMessage('Action is required')
            .isIn(['clean', 'analyze', 'summarize', 'translate', 'entities'])
            .withMessage('Invalid action')
        ];
      case 'translateText':
        return [
          body('text').isString().notEmpty().withMessage('Text is required'),
          body('targetLanguage').isString().optional().withMessage('Target language must be a string'),
          body('sourceLanguage').isString().optional().withMessage('Source language must be a string')
        ];
      default:
        return [];
    }
  }

  /**
   * Process text based on action
   */
  static async processText(req: Request, res: Response) {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { text, action, options } = req.body;

    try {
      let result;

      switch (action) {
        case 'clean':
          result = await pythonService.cleanText(text, options);
          break;
        case 'analyze':
          result = await pythonService.analyzeSentiment(text);
          break;
        case 'summarize':
          const reductionTarget = options?.reductionTarget || 0.3;
          result = await pythonService.summarizeText(text, reductionTarget);
          break;
        case 'translate':
          const sourceLang = options?.sourceLanguage || 'en';
          const targetLang = options?.targetLanguage || 'es';
          result = await pythonService.translateText(text, sourceLang, targetLang);
          break;
        case 'entities':
          result = await pythonService.extractEntities(text);
          break;
        default:
          throw new ApiError(400, `Unsupported action: ${action}`);
      }

      if (!result.success) {
        throw new ApiError(500, result.error || 'Python script execution failed');
      }

      res.json({
        success: true,
        data: result.data
      });
    } catch (error) {
      logger.error(`Error processing text with action '${action}':`, error);
      
      if (error instanceof ApiError) {
        throw error;
      }
      
      throw new ApiError(500, `Error processing text: ${error.message}`);
    }
  }

  /**
   * Clean text
   */
  static async cleanText(req: Request, res: Response) {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { text, options } = req.body;

    try {
      const result = await pythonService.cleanText(text, options);

      if (!result.success) {
        throw new ApiError(500, result.error || 'Text cleaning failed');
      }

      res.json({
        success: true,
        data: result.data
      });
    } catch (error) {
      logger.error('Error cleaning text:', error);
      
      if (error instanceof ApiError) {
        throw error;
      }
      
      throw new ApiError(500, `Error cleaning text: ${error.message}`);
    }
  }

  /**
   * Analyze sentiment
   */
  static async analyzeSentiment(req: Request, res: Response) {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { text } = req.body;

    try {
      const result = await pythonService.analyzeSentiment(text);

      if (!result.success) {
        throw new ApiError(500, result.error || 'Sentiment analysis failed');
      }

      res.json({
        success: true,
        data: result.data
      });
    } catch (error) {
      logger.error('Error analyzing sentiment:', error);
      
      if (error instanceof ApiError) {
        throw error;
      }
      
      throw new ApiError(500, `Error analyzing sentiment: ${error.message}`);
    }
  }

  /**
   * Summarize text
   */
  static async summarizeText(req: Request, res: Response) {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { text, reductionTarget } = req.body;

    try {
      const result = await pythonService.summarizeText(text, reductionTarget || 0.3);

      if (!result.success) {
        throw new ApiError(500, result.error || 'Text summarization failed');
      }

      res.json({
        success: true,
        data: result.data
      });
    } catch (error) {
      logger.error('Error summarizing text:', error);
      
      if (error instanceof ApiError) {
        throw error;
      }
      
      throw new ApiError(500, `Error summarizing text: ${error.message}`);
    }
  }

  /**
   * Translate text
   */
  static async translateText(req: Request, res: Response) {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { text, sourceLanguage, targetLanguage } = req.body;

    try {
      const result = await pythonService.translateText(
        text,
        sourceLanguage || 'en',
        targetLanguage || 'es'
      );

      if (!result.success) {
        throw new ApiError(500, result.error || 'Text translation failed');
      }

      res.json({
        success: true,
        data: result.data
      });
    } catch (error) {
      logger.error('Error translating text:', error);
      
      if (error instanceof ApiError) {
        throw error;
      }
      
      throw new ApiError(500, `Error translating text: ${error.message}`);
    }
  }

  /**
   * Extract entities
   */
  static async extractEntities(req: Request, res: Response) {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { text } = req.body;

    try {
      const result = await pythonService.extractEntities(text);

      if (!result.success) {
        throw new ApiError(500, result.error || 'Entity extraction failed');
      }

      res.json({
        success: true,
        data: result.data
      });
    } catch (error) {
      logger.error('Error extracting entities:', error);
      
      if (error instanceof ApiError) {
        throw error;
      }
      
      throw new ApiError(500, `Error extracting entities: ${error.message}`);
    }
  }
} 