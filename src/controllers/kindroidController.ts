import { Request, Response } from 'express';
import { body, validationResult } from 'express-validator';
import { kindroidService } from '../services/kindroidService';
import { ApiError } from '../middleware/errorHandler';
import { createLogger } from '../utils/logger';

const logger = createLogger('KindroidController');

/**
 * Controller for Kindroid AI API integration
 */
export class KindroidController {
  /**
   * Validate request based on method
   */
  static validate(method: string) {
    switch (method) {
      case 'sendMessage':
        return [
          body('message').isString().notEmpty().withMessage('Message is required')
        ];
      case 'resetConversation':
        return [
          body('greeting').isString().optional().withMessage('Greeting should be a string')
        ];
      case 'processTextWithAI':
        return [
          body('text').isString().notEmpty().withMessage('Text is required'),
          body('processingType').isString().notEmpty().withMessage('Processing type is required')
            .isIn(['analyze', 'enhance', 'summarize', 'question'])
            .withMessage('Invalid processing type')
        ];
      case 'sendDiscordConversation':
        return [
          body('conversation').isArray().notEmpty().withMessage('Conversation is required'),
          body('conversation.*.username').isString().notEmpty().withMessage('Username is required for each message'),
          body('conversation.*.text').isString().notEmpty().withMessage('Text is required for each message'),
          body('conversation.*.timestamp').isString().notEmpty().withMessage('Timestamp is required for each message'),
          body('options.shareCode').isString().optional().withMessage('Share code should be a string'),
          body('options.enableFilter').isBoolean().optional().withMessage('Enable filter should be a boolean')
        ];
      case 'getMemoryStats':
        return [];
      case 'cleanupMemories':
        return [
          body('maxItems').isInt({ min: 0 }).optional().withMessage('maxItems must be a non-negative integer'),
          body('maxAgeMs').isInt({ min: 0 }).optional().withMessage('maxAgeMs must be a non-negative integer'),
        ];
      default:
        return [];
    }
  }

  /**
   * Send a message to Kindroid AI
   */
  static async sendMessage(req: Request, res: Response) {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      throw new ApiError(400, 'Validation error', errors.array());
    }

    const { message } = req.body;

    try {
      const result = await kindroidService.sendMessage(message);

      if (!result.success) {
        throw new ApiError(500, result.error || 'Failed to send message to Kindroid AI');
      }

      res.json({
        success: true,
        data: result.data
      });
    } catch (error) {
      throw error;
    }
  }

  /**
   * Reset conversation with Kindroid AI
   */
  static async resetConversation(req: Request, res: Response) {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      throw new ApiError(400, 'Validation error', errors.array());
    }

    const { greeting = '' } = req.body;

    try {
      const result = await kindroidService.resetConversation(greeting);

      if (!result.success) {
        throw new ApiError(500, result.error || 'Failed to reset conversation with Kindroid AI');
      }

      res.json({
        success: true,
        data: result.data
      });
    } catch (error) {
      throw error;
    }
  }

  /**
   * Process text with Kindroid AI
   */
  static async processTextWithAI(req: Request, res: Response) {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      throw new ApiError(400, 'Validation error', errors.array());
    }

    const { text, processingType, useMemory = true } = req.body;

    try {
      const result = await kindroidService.processTextWithAI(
        text,
        processingType as 'analyze' | 'enhance' | 'summarize' | 'question',
        useMemory
      );

      if (!result.success) {
        throw new ApiError(500, result.error || 'Failed to process text with Kindroid AI');
      }

      res.json({
        success: true,
        data: result.data
      });
    } catch (error) {
      throw error;
    }
  }

  /**
   * Send a conversation to the Kindroid Discord bot endpoint
   */
  static async sendDiscordConversation(req: Request, res: Response) {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      throw new ApiError(400, 'Validation error', errors.array());
    }

    const { conversation, options = {} } = req.body;

    try {
      const result = await kindroidService.sendDiscordConversation(conversation, options);

      if (!result.success) {
        throw new ApiError(500, result.error || 'Failed to communicate with Kindroid Discord endpoint');
      }

      res.json({
        success: true,
        data: result.data
      });
    } catch (error) {
      throw error;
    }
  }

  /**
   * Get memory statistics for Kindroid AI.
   */
  static async getMemoryStats(req: Request, res: Response): Promise<void> {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      throw new ApiError(400, 'Validation error', errors.array());
    }

    try {
      const stats = await kindroidService.getMemoryStats();
      res.json({ success: true, data: stats });
    } catch (error) {
      throw error;
    }
  }

  /**
   * Clean up old or low-priority memories.
   */
  static async cleanupMemories(req: Request, res: Response): Promise<void> {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      throw new ApiError(400, 'Validation error', errors.array());
    }

    const { maxItems, maxAgeMs } = req.body;

    try {
      const result = await kindroidService.cleanupMemories(maxItems, maxAgeMs);
      res.json({ success: true, data: result });
    } catch (error) {
      throw error;
    }
  }
} 