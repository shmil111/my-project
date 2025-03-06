/**
 * GitHub Gist Webhook Handler
 * 
 * Processes incoming GitHub webhook events related to Gists
 */

import { Request, Response } from 'express';
import crypto from 'crypto';
import { createLogger } from '../utils/logger';
import { config } from '../config';
import { gistCache } from '../services/CacheService';
import { EventEmitter } from 'events';

// Initialize logger
const logger = createLogger('GistWebhook');

/**
 * GitHub webhook event types related to Gists
 */
export enum GistWebhookEvent {
  CREATED = 'gist.created',
  UPDATED = 'gist.updated',
  DELETED = 'gist.deleted',
}

/**
 * GitHub webhook payload for Gist events
 */
export interface GistWebhookPayload {
  action: string;
  gist: {
    id: string;
    description: string;
    public: boolean;
    owner: {
      login: string;
    };
    html_url: string;
    created_at: string;
    updated_at: string;
  };
  sender: {
    login: string;
  };
}

/**
 * GitHub Gist Webhook Handler
 * Processes incoming GitHub webhook events for Gists
 */
export class GistWebhook extends EventEmitter {
  private webhookSecret: string;
  
  /**
   * Create a new GistWebhook
   * @param webhookSecret Secret for validating GitHub webhooks
   */
  constructor(webhookSecret: string = config.webhooks?.githubSecret || '') {
    super();
    
    this.webhookSecret = webhookSecret;
    this.handleWebhook = this.handleWebhook.bind(this);
    
    logger.info('GistWebhook initialized');
    
    if (!this.webhookSecret) {
      logger.warn('No webhook secret configured. Webhook signature verification will be skipped.');
    }
  }
  
  /**
   * Validate the GitHub webhook signature
   * @param payload Raw request body
   * @param signature GitHub signature header value
   * @returns True if signature is valid or no secret is configured
   */
  private validateSignature(payload: string, signature: string): boolean {
    if (!this.webhookSecret) {
      // If no secret is configured, skip validation
      logger.debug('Skipping webhook signature validation (no secret configured)');
      return true;
    }
    
    if (!signature) {
      logger.warn('Webhook request missing signature header');
      return false;
    }
    
    const signatureParts = signature.split('=');
    if (signatureParts.length !== 2) {
      logger.warn(`Invalid webhook signature format: ${signature}`);
      return false;
    }
    
    const [algorithm, providedHash] = signatureParts;
    
    try {
      const hmac = crypto.createHmac(algorithm, this.webhookSecret);
      const calculatedHash = hmac.update(payload).digest('hex');
      
      const valid = crypto.timingSafeEqual(
        Buffer.from(providedHash),
        Buffer.from(calculatedHash)
      );
      
      if (!valid) {
        logger.warn('Invalid webhook signature');
      }
      
      return valid;
    } catch (error) {
      logger.error(`Error validating webhook signature: ${error}`);
      return false;
    }
  }
  
  /**
   * Handle incoming GitHub webhook requests
   * @param req Express request
   * @param res Express response
   */
  public async handleWebhook(req: Request, res: Response): Promise<void> {
    try {
      // Get raw request body and signature
      const rawBody = JSON.stringify(req.body);
      const signature = req.header('X-Hub-Signature-256') || '';
      const event = req.header('X-GitHub-Event') || '';
      
      // Validate signature
      if (!this.validateSignature(rawBody, signature)) {
        res.status(403).json({
          success: false,
          message: 'Invalid webhook signature',
        });
        return;
      }
      
      // Check if this is a Gist event
      if (event !== 'gist') {
        logger.debug(`Ignoring non-Gist webhook event: ${event}`);
        res.status(200).json({
          success: true,
          message: 'Event acknowledged but not processed (not a Gist event)',
        });
        return;
      }
      
      // Process the Gist event
      const payload = req.body as GistWebhookPayload;
      const { action, gist } = payload;
      
      logger.info(`Received Gist webhook event: ${action} for ${gist.id} by ${payload.sender.login}`);
      
      // Invalidate cache for this gist
      gistCache.delete(`gist-${gist.id}`);
      
      // Invalidate user gists cache
      const cacheKeyPrefix = `user-gists-${gist.owner.login}`;
      for (let i = 1; i <= 10; i++) {
        for (let j = 10; j <= 100; j += 10) {
          gistCache.delete(`${cacheKeyPrefix}-${i}-${j}`);
        }
      }
      
      // Map to event type
      let eventType: GistWebhookEvent | null = null;
      
      switch (action) {
        case 'created':
          eventType = GistWebhookEvent.CREATED;
          break;
        case 'updated':
          eventType = GistWebhookEvent.UPDATED;
          break;
        case 'deleted':
          eventType = GistWebhookEvent.DELETED;
          break;
        default:
          logger.debug(`Unhandled Gist action: ${action}`);
          break;
      }
      
      // Emit event if we have a valid event type
      if (eventType) {
        this.emit(eventType, payload);
      }
      
      res.status(200).json({
        success: true,
        message: `Webhook processed: ${action}`,
        gistId: gist.id,
      });
    } catch (error) {
      logger.error(`Error processing webhook: ${error}`);
      res.status(500).json({
        success: false,
        message: 'Error processing webhook',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Register an event handler for Gist created events
   * @param handler Event handler function
   */
  public onGistCreated(handler: (payload: GistWebhookPayload) => void): void {
    this.on(GistWebhookEvent.CREATED, handler);
  }
  
  /**
   * Register an event handler for Gist updated events
   * @param handler Event handler function
   */
  public onGistUpdated(handler: (payload: GistWebhookPayload) => void): void {
    this.on(GistWebhookEvent.UPDATED, handler);
  }
  
  /**
   * Register an event handler for Gist deleted events
   * @param handler Event handler function
   */
  public onGistDeleted(handler: (payload: GistWebhookPayload) => void): void {
    this.on(GistWebhookEvent.DELETED, handler);
  }
}

// Export a singleton instance
export const gistWebhook = new GistWebhook(); 