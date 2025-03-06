/**
 * Text Processing Controller
 * 
 * This controller handles text processing operations like sentiment analysis and translation.
 */

import { Request, Response } from 'express';
import { createLogger } from '../utils/logger';
import { ApiError, asyncHandler } from '../middleware/errorHandler';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import { config } from '../utils/env';

// Promisify exec
const execPromise = promisify(exec);

// Create logger
const logger = createLogger('TextProcessingController');

export class TextProcessingController {
  private pythonPath: string;
  
  constructor() {
    this.pythonPath = config.PYTHON_PATH;
    
    // Bind methods to ensure 'this' context
    this.analyzeSentiment = this.analyzeSentiment.bind(this);
    this.translateText = this.translateText.bind(this);
    this.summarizeText = this.summarizeText.bind(this);
  }
  
  /**
   * Execute a Python script with arguments
   */
  private async executePythonScript(scriptName: string, args: Record<string, any>): Promise<any> {
    try {
      // Convert arguments to JSON string
      const argsJson = JSON.stringify(args);
      
      // Construct the command
      const scriptPath = path.join(__dirname, '..', '..', scriptName);
      const command = `${this.pythonPath} "${scriptPath}" '${argsJson}'`;
      
      logger.debug(`Executing Python script: ${command}`);
      
      // Execute the command
      const { stdout, stderr } = await execPromise(command);
      
      if (stderr) {
        logger.warn(`Python script warning: ${stderr}`);
      }
      
      // Parse the JSON output
      return JSON.parse(stdout);
    } catch (error: any) {
      logger.error(`Error executing Python script: ${error.message}`, error);
      throw new ApiError(500, `Error processing text: ${error.message}`);
    }
  }
  
  /**
   * Analyze sentiment of text
   */
  public analyzeSentiment = asyncHandler(async (req: Request, res: Response) => {
    await this._analyzeSentiment(req, res);
  });
  
  /**
   * Implementation of sentiment analysis for testing
   */
  public async _analyzeSentiment(req: Request, res: Response): Promise<void> {
    const { text } = req.body;
    
    // Validate input
    if (!text || typeof text !== 'string') {
      throw ApiError.badRequest('Text is required and must be a string');
    }
    
    // Analyze sentiment
    logger.info('Analyzing sentiment for text');
    const result = await this.executePythonScript('sentiment.py', { text });
    
    res.json(result);
  }
  
  /**
   * Translate text
   */
  public translateText = asyncHandler(async (req: Request, res: Response) => {
    await this._translateText(req, res);
  });
  
  /**
   * Implementation of text translation for testing
   */
  public async _translateText(req: Request, res: Response): Promise<void> {
    const { text, sourceLang, targetLang } = req.body;
    
    // Validate input
    if (!text || typeof text !== 'string') {
      throw ApiError.badRequest('Text is required and must be a string');
    }
    
    if (!sourceLang || typeof sourceLang !== 'string') {
      throw ApiError.badRequest('Source language is required and must be a string');
    }
    
    if (!targetLang || typeof targetLang !== 'string') {
      throw ApiError.badRequest('Target language is required and must be a string');
    }
    
    // Translate text
    logger.info(`Translating text from ${sourceLang} to ${targetLang}`);
    const result = await this.executePythonScript('translator_module.py', { 
      text, 
      sourceLang, 
      targetLang 
    });
    
    res.json(result);
  }
  
  /**
   * Summarize text
   */
  public summarizeText = asyncHandler(async (req: Request, res: Response) => {
    await this._summarizeText(req, res);
  });
  
  /**
   * Implementation of text summarization for testing
   */
  public async _summarizeText(req: Request, res: Response): Promise<void> {
    const { text, maxLength } = req.body;
    
    // Validate input
    if (!text || typeof text !== 'string') {
      throw ApiError.badRequest('Text is required and must be a string');
    }
    
    // Validate maxLength if provided
    if (maxLength !== undefined && (typeof maxLength !== 'number' || maxLength <= 0)) {
      throw ApiError.badRequest('maxLength must be a positive number if provided');
    }
    
    // Summarize text
    logger.info('Summarizing text');
    const result = await this.executePythonScript('summarizer.py', { 
      text, 
      maxLength: maxLength || 3 // Default to 3 sentences if not specified
    });
    
    res.json(result);
  }
} 