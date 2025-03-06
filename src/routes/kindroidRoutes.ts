import { Router } from 'express';
import { KindroidController } from '../controllers/kindroidController';
import { asyncHandler } from '../middleware/asyncHandler';

const router = Router();

/**
 * @swagger
 * tags:
 *   name: Kindroid
 *   description: Kindroid AI API integration
 */

/**
 * @swagger
 * /api/kindroid/send-message:
 *   post:
 *     summary: Send a message to Kindroid AI
 *     tags: [Kindroid]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - message
 *             properties:
 *               message:
 *                 type: string
 *                 description: Message to send to the AI
 *     responses:
 *       200:
 *         description: Message sent successfully
 *       400:
 *         description: Invalid request
 *       500:
 *         description: Server error
 */
router.post(
  '/send-message',
  KindroidController.validate('sendMessage'),
  asyncHandler(KindroidController.sendMessage)
);

/**
 * @swagger
 * /api/kindroid/reset:
 *   post:
 *     summary: Reset conversation with Kindroid AI
 *     tags: [Kindroid]
 *     requestBody:
 *       required: false
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               greeting:
 *                 type: string
 *                 description: Initial greeting to start new conversation
 *     responses:
 *       200:
 *         description: Conversation reset successfully
 *       500:
 *         description: Server error
 */
router.post(
  '/reset',
  KindroidController.validate('resetConversation'),
  asyncHandler(KindroidController.resetConversation)
);

/**
 * @swagger
 * /api/kindroid/process:
 *   post:
 *     summary: Process text with Kindroid AI
 *     tags: [Kindroid]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - text
 *               - processingType
 *             properties:
 *               text:
 *                 type: string
 *                 description: Text to process
 *               processingType:
 *                 type: string
 *                 enum: [analyze, enhance, summarize, question]
 *                 description: Type of processing to apply
 *               useMemory:
 *                 type: boolean
 *                 description: Whether to include and update memory during processing
 *                 default: true
 *     responses:
 *       200:
 *         description: Text processed successfully
 *       400:
 *         description: Invalid request
 *       500:
 *         description: Server error
 */
router.post(
  '/process',
  KindroidController.validate('processTextWithAI'),
  asyncHandler(KindroidController.processTextWithAI)
);

/**
 * @swagger
 * /api/kindroid/discord:
 *   post:
 *     summary: Send conversation to Kindroid Discord bot
 *     tags: [Kindroid]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - conversation
 *             properties:
 *               conversation:
 *                 type: array
 *                 items:
 *                   type: object
 *                   required:
 *                     - username
 *                     - text
 *                     - timestamp
 *                   properties:
 *                     username:
 *                       type: string
 *                     text:
 *                       type: string
 *                     timestamp:
 *                       type: string
 *               options:
 *                 type: object
 *                 properties:
 *                   shareCode:
 *                     type: string
 *                   enableFilter:
 *                     type: boolean
 *     responses:
 *       200:
 *         description: Discord conversation processed successfully
 *       400:
 *         description: Invalid request
 *       500:
 *         description: Server error
 */
router.post(
  '/discord',
  KindroidController.validate('sendDiscordConversation'),
  asyncHandler(KindroidController.sendDiscordConversation)
);

/**
 * @swagger
 * /api/kindroid/memory/stats:
 *   get:
 *     summary: Get memory statistics for Kindroid AI
 *     tags: [Kindroid, Memory]
 *     responses:
 *       200:
 *         description: Memory statistics retrieved successfully
 *       500:
 *         description: Server error
 */
router.get(
  '/memory/stats',
  asyncHandler(KindroidController.getMemoryStats)
);

/**
 * @swagger
 * /api/kindroid/memory/cleanup:
 *   post:
 *     summary: Clean up old or low-priority memories
 *     tags: [Kindroid, Memory]
 *     requestBody:
 *       required: false
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               maxItems:
 *                 type: integer
 *                 description: Maximum number of memories to keep
 *                 default: 1000
 *               maxAgeMs:
 *                 type: integer
 *                 description: Maximum age of memories in milliseconds
 *                 default: 2592000000 (30 days)
 *     responses:
 *       200:
 *         description: Memories cleaned up successfully
 *       400:
 *         description: Invalid request
 *       500:
 *         description: Server error
 */
router.post(
  '/memory/cleanup',
  asyncHandler(KindroidController.cleanupMemories)
);

export default router; 