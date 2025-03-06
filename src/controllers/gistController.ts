/**
 * Gist Controller
 * 
 * Manages GitHub Gist operations via API endpoints.
 */

import { Request, Response } from 'express';
import { GistService, CreateGistOptions, UpdateGistOptions } from '../services/GistService';
import { createLogger } from '../utils/logger';
import { config } from '../config';

// Initialize logger
const logger = createLogger('GistController');

// Default GitHub username
const DEFAULT_GITHUB_USERNAME = 'shmil111';

/**
 * Controller for handling GitHub Gist operations
 */
export class GistController {
  private gistService: GistService;
  
  /**
   * Create a new GistController
   */
  constructor() {
    // Get GitHub token from config or environment
    const githubToken = config.github.token;
    const githubUsername = config.github.username;
    
    if (!githubToken) {
      logger.warn('No GitHub token found. Gist operations will fail.');
    }
    
    // Initialize Gist service
    this.gistService = new GistService(githubToken, githubUsername);
    
    // Bind methods to this instance
    this.getGists = this.getGists.bind(this);
    this.getUserGists = this.getUserGists.bind(this);
    this.getGist = this.getGist.bind(this);
    this.createGist = this.createGist.bind(this);
    this.updateGist = this.updateGist.bind(this);
    this.deleteGist = this.deleteGist.bind(this);
    this.starGist = this.starGist.bind(this);
    this.unstarGist = this.unstarGist.bind(this);
    this.checkIsStarred = this.checkIsStarred.bind(this);
    this.forkGist = this.forkGist.bind(this);
    
    logger.info('Gist controller initialized');
  }
  
  /**
   * Get all gists for the authenticated user
   * @param req Request
   * @param res Response
   */
  public async getGists(req: Request, res: Response): Promise<void> {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const perPage = parseInt(req.query.perPage as string) || 30;
      
      logger.debug(`Getting gists: page=${page}, perPage=${perPage}`);
      
      const gists = await this.gistService.getGists(page, perPage);
      
      res.status(200).json({
        success: true,
        count: gists.length,
        gists,
      });
    } catch (error) {
      logger.error(`Error getting gists: ${error}`);
      
      res.status(500).json({
        success: false,
        message: 'Failed to get gists',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Get gists for a specific user
   * @param req Request
   * @param res Response
   */
  public async getUserGists(req: Request, res: Response): Promise<void> {
    try {
      const { username } = req.params;
      const page = parseInt(req.query.page as string) || 1;
      const perPage = parseInt(req.query.perPage as string) || 30;
      
      logger.debug(`Getting gists for user ${username}: page=${page}, perPage=${perPage}`);
      
      const gists = await this.gistService.getUserGists(username, page, perPage);
      
      res.status(200).json({
        success: true,
        count: gists.length,
        gists,
      });
    } catch (error) {
      logger.error(`Error getting user gists: ${error}`);
      
      res.status(500).json({
        success: false,
        message: 'Failed to get user gists',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Get a specific gist by ID
   * @param req Request
   * @param res Response
   */
  public async getGist(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      
      logger.debug(`Getting gist with ID: ${id}`);
      
      const gist = await this.gistService.getGist(id);
      
      res.status(200).json({
        success: true,
        gist,
      });
    } catch (error) {
      logger.error(`Error getting gist: ${error}`);
      
      // Handle 404 error specifically
      if ((error as any)?.message?.includes('404')) {
        res.status(404).json({
          success: false,
          message: `Gist not found with ID: ${req.params.id}`,
        });
        return;
      }
      
      res.status(500).json({
        success: false,
        message: 'Failed to get gist',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Create a new gist
   * @param req Request
   * @param res Response
   */
  public async createGist(req: Request, res: Response): Promise<void> {
    try {
      const { description, public: isPublic, files } = req.body;
      
      logger.debug(`Creating gist: ${description}`);
      
      const options: CreateGistOptions = {
        description,
        public: isPublic === undefined ? true : isPublic,
        files,
      };
      
      const gist = await this.gistService.createGist(options);
      
      res.status(201).json({
        success: true,
        message: 'Gist created successfully',
        gist,
      });
    } catch (error) {
      logger.error(`Error creating gist: ${error}`);
      
      res.status(500).json({
        success: false,
        message: 'Failed to create gist',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Update an existing gist
   * @param req Request
   * @param res Response
   */
  public async updateGist(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { description, files } = req.body;
      
      logger.debug(`Updating gist with ID: ${id}`);
      
      const options: UpdateGistOptions = {};
      
      if (description !== undefined) {
        options.description = description;
      }
      
      if (files !== undefined) {
        options.files = files;
      }
      
      const gist = await this.gistService.updateGist(id, options);
      
      res.status(200).json({
        success: true,
        message: 'Gist updated successfully',
        gist,
      });
    } catch (error) {
      logger.error(`Error updating gist: ${error}`);
      
      // Handle 404 error specifically
      if ((error as any)?.message?.includes('404')) {
        res.status(404).json({
          success: false,
          message: `Gist not found with ID: ${req.params.id}`,
        });
        return;
      }
      
      res.status(500).json({
        success: false,
        message: 'Failed to update gist',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Delete a gist
   * @param req Request
   * @param res Response
   */
  public async deleteGist(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      
      logger.debug(`Deleting gist with ID: ${id}`);
      
      await this.gistService.deleteGist(id);
      
      res.status(200).json({
        success: true,
        message: 'Gist deleted successfully',
      });
    } catch (error) {
      logger.error(`Error deleting gist: ${error}`);
      
      // Handle 404 error specifically
      if ((error as any)?.message?.includes('404')) {
        res.status(404).json({
          success: false,
          message: `Gist not found with ID: ${req.params.id}`,
        });
        return;
      }
      
      res.status(500).json({
        success: false,
        message: 'Failed to delete gist',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Star a gist
   * @param req Request
   * @param res Response
   */
  public async starGist(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      
      logger.debug(`Starring gist with ID: ${id}`);
      
      await this.gistService.starGist(id);
      
      res.status(200).json({
        success: true,
        message: 'Gist starred successfully',
      });
    } catch (error) {
      logger.error(`Error starring gist: ${error}`);
      
      // Handle 404 error specifically
      if ((error as any)?.message?.includes('404')) {
        res.status(404).json({
          success: false,
          message: `Gist not found with ID: ${req.params.id}`,
        });
        return;
      }
      
      res.status(500).json({
        success: false,
        message: 'Failed to star gist',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Unstar a gist
   * @param req Request
   * @param res Response
   */
  public async unstarGist(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      
      logger.debug(`Unstarring gist with ID: ${id}`);
      
      await this.gistService.unstarGist(id);
      
      res.status(200).json({
        success: true,
        message: 'Gist unstarred successfully',
      });
    } catch (error) {
      logger.error(`Error unstarring gist: ${error}`);
      
      // Handle 404 error specifically
      if ((error as any)?.message?.includes('404')) {
        res.status(404).json({
          success: false,
          message: `Gist not found with ID: ${req.params.id}`,
        });
        return;
      }
      
      res.status(500).json({
        success: false,
        message: 'Failed to unstar gist',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Check if a gist is starred
   * @param req Request
   * @param res Response
   */
  public async checkIsStarred(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      
      logger.debug(`Checking if gist ${id} is starred`);
      
      const isStarred = await this.gistService.isGistStarred(id);
      
      res.status(200).json({
        success: true,
        isStarred,
      });
    } catch (error) {
      logger.error(`Error checking if gist is starred: ${error}`);
      
      // Handle 404 error specifically
      if ((error as any)?.message?.includes('404')) {
        res.status(404).json({
          success: false,
          message: `Gist not found with ID: ${req.params.id}`,
        });
        return;
      }
      
      res.status(500).json({
        success: false,
        message: 'Failed to check if gist is starred',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Fork a gist
   * @param req Request
   * @param res Response
   */
  public async forkGist(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      
      logger.debug(`Forking gist with ID: ${id}`);
      
      const gist = await this.gistService.forkGist(id);
      
      res.status(201).json({
        success: true,
        message: 'Gist forked successfully',
        gist,
      });
    } catch (error) {
      logger.error(`Error forking gist: ${error}`);
      
      // Handle 404 error specifically
      if ((error as any)?.message?.includes('404')) {
        res.status(404).json({
          success: false,
          message: `Gist not found with ID: ${req.params.id}`,
        });
        return;
      }
      
      res.status(500).json({
        success: false,
        message: 'Failed to fork gist',
        error: (error as Error).message,
      });
    }
  }
} 