/**
 * GitHub Gist Service
 * 
 * Provides methods for interacting with the GitHub Gist API.
 */

import axios, { AxiosInstance } from 'axios';
import { createLogger } from '../utils/logger';
import { gistCache } from './CacheService';

// Initialize logger
const logger = createLogger('GistService');

// Gist API base URL
const GIST_API_BASE_URL = 'https://api.github.com/gists';

// Gist interface
export interface Gist {
  id: string;
  description: string;
  public: boolean;
  files: Record<string, GistFile>;
  html_url: string;
  created_at: string;
  updated_at: string;
}

// Gist file interface
export interface GistFile {
  filename: string;
  content: string;
  type?: string;
  language?: string;
  raw_url?: string;
  size?: number;
}

// Gist creation options
export interface CreateGistOptions {
  description: string;
  public: boolean;
  files: Record<string, { content: string }>;
}

// Gist update options
export interface UpdateGistOptions {
  description?: string;
  files?: Record<string, { content: string } | null>;
}

/**
 * GitHub Gist Service
 */
export class GistService {
  private client: AxiosInstance;
  private username: string;
  private useCache: boolean;
  
  /**
   * Create a new GistService
   * @param token GitHub personal access token
   * @param username GitHub username
   * @param useCache Whether to use caching (default: true)
   */
  constructor(token: string, username: string, useCache: boolean = true) {
    if (!token) {
      throw new Error('GitHub token is required');
    }
    
    this.username = username;
    this.useCache = useCache;
    
    // Create Axios client with authentication
    this.client = axios.create({
      baseURL: GIST_API_BASE_URL,
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': `token ${token}`,
        'User-Agent': 'my-project-gist-client'
      }
    });
    
    logger.info(`GistService initialized for user: ${username} (caching: ${useCache ? 'enabled' : 'disabled'})`);
  }
  
  /**
   * Get all gists for the authenticated user
   * @param page Page number (1-based)
   * @param perPage Results per page
   * @returns Array of gists
   */
  public async getGists(page: number = 1, perPage: number = 30): Promise<Gist[]> {
    try {
      // Check cache first if caching is enabled
      const cacheKey = `user-gists-${this.username}-${page}-${perPage}`;
      let gists: Gist[] | undefined;
      
      if (this.useCache) {
        gists = gistCache.get<Gist[]>(cacheKey);
        if (gists) {
          logger.debug(`Using cached gists for user ${this.username}, page ${page}, perPage ${perPage}`);
          return gists;
        }
      }
      
      logger.debug(`Fetching gists for user ${this.username}, page ${page}, perPage ${perPage}`);
      
      const response = await this.client.get('', {
        params: {
          page,
          per_page: perPage
        }
      });
      
      logger.debug(`Fetched ${response.data.length} gists`);
      
      // Cache the result if caching is enabled
      if (this.useCache) {
        gistCache.set(cacheKey, response.data);
      }
      
      return response.data;
    } catch (error) {
      logger.error(`Error fetching gists: ${error}`);
      throw new Error(`Failed to fetch gists: ${(error as Error).message}`);
    }
  }
  
  /**
   * Get gists for a specific user
   * @param username GitHub username
   * @param page Page number (1-based)
   * @param perPage Results per page
   * @returns Array of gists
   */
  public async getUserGists(username: string, page: number = 1, perPage: number = 30): Promise<Gist[]> {
    try {
      // Check cache first if caching is enabled
      const cacheKey = `user-gists-${username}-${page}-${perPage}`;
      let gists: Gist[] | undefined;
      
      if (this.useCache) {
        gists = gistCache.get<Gist[]>(cacheKey);
        if (gists) {
          logger.debug(`Using cached gists for user ${username}, page ${page}, perPage ${perPage}`);
          return gists;
        }
      }
      
      logger.debug(`Fetching gists for user ${username}, page ${page}, perPage ${perPage}`);
      
      const response = await this.client.get(`/users/${username}/gists`, {
        params: {
          page,
          per_page: perPage
        }
      });
      
      logger.debug(`Fetched ${response.data.length} gists for user ${username}`);
      
      // Cache the result if caching is enabled
      if (this.useCache) {
        gistCache.set(cacheKey, response.data);
      }
      
      return response.data;
    } catch (error) {
      logger.error(`Error fetching gists for user ${username}: ${error}`);
      throw new Error(`Failed to fetch gists for user ${username}: ${(error as Error).message}`);
    }
  }
  
  /**
   * Get a specific gist by ID
   * @param id Gist ID
   * @returns Gist object
   */
  public async getGist(id: string): Promise<Gist> {
    try {
      // Check cache first if caching is enabled
      const cacheKey = `gist-${id}`;
      let gist: Gist | undefined;
      
      if (this.useCache) {
        gist = gistCache.get<Gist>(cacheKey);
        if (gist) {
          logger.debug(`Using cached gist with ID: ${id}`);
          return gist;
        }
      }
      
      logger.debug(`Fetching gist with ID: ${id}`);
      
      const response = await this.client.get(`/${id}`);
      
      logger.debug(`Fetched gist: ${response.data.description}`);
      
      // Cache the result if caching is enabled
      if (this.useCache) {
        gistCache.set(cacheKey, response.data);
      }
      
      return response.data;
    } catch (error) {
      logger.error(`Error fetching gist ${id}: ${error}`);
      throw new Error(`Failed to fetch gist ${id}: ${(error as Error).message}`);
    }
  }
  
  /**
   * Create a new gist
   * @param options Gist creation options
   * @returns Created gist
   */
  public async createGist(options: CreateGistOptions): Promise<Gist> {
    try {
      logger.debug(`Creating gist: ${options.description}`);
      
      const response = await this.client.post('', options);
      
      logger.info(`Created gist with ID: ${response.data.id}`);
      
      // Cache the new gist if caching is enabled
      if (this.useCache) {
        const gist = response.data;
        gistCache.set(`gist-${gist.id}`, gist);
        
        // Invalidate user gists cache since we've added a new gist
        this.invalidateUserGistsCache();
      }
      
      return response.data;
    } catch (error) {
      logger.error(`Error creating gist: ${error}`);
      throw new Error(`Failed to create gist: ${(error as Error).message}`);
    }
  }
  
  /**
   * Update an existing gist
   * @param id Gist ID
   * @param options Gist update options
   * @returns Updated gist
   */
  public async updateGist(id: string, options: UpdateGistOptions): Promise<Gist> {
    try {
      logger.debug(`Updating gist with ID: ${id}`);
      
      const response = await this.client.patch(`/${id}`, options);
      
      logger.info(`Updated gist with ID: ${response.data.id}`);
      
      // Update cache if caching is enabled
      if (this.useCache) {
        gistCache.set(`gist-${id}`, response.data);
        
        // Invalidate user gists cache since we've modified a gist
        this.invalidateUserGistsCache();
      }
      
      return response.data;
    } catch (error) {
      logger.error(`Error updating gist ${id}: ${error}`);
      throw new Error(`Failed to update gist ${id}: ${(error as Error).message}`);
    }
  }
  
  /**
   * Delete a gist
   * @param id Gist ID
   * @returns True if successful
   */
  public async deleteGist(id: string): Promise<boolean> {
    try {
      if (!id) {
        throw new Error('Gist ID is required');
      }
      
      logger.debug(`Deleting gist with ID: ${id}`);
      
      await this.client.delete(`/${id}`);
      
      logger.info(`Deleted gist with ID: ${id}`);
      
      // Remove from cache if caching is enabled
      if (this.useCache) {
        gistCache.delete(`gist-${id}`);
        
        // Invalidate user gists cache since we've deleted a gist
        this.invalidateUserGistsCache();
      }
      
      return true;
    } catch (error) {
      logger.error(`Error deleting gist ${id}: ${error}`);
      throw new Error(`Failed to delete gist ${id}: ${(error as Error).message}`);
    }
  }
  
  /**
   * Star a gist
   * @param id Gist ID
   * @returns True if successful
   */
  public async starGist(id: string): Promise<boolean> {
    try {
      if (!id) {
        throw new Error('Gist ID is required');
      }
      
      logger.debug(`Starring gist with ID: ${id}`);
      
      await this.client.put(`/${id}/star`);
      
      logger.info(`Starred gist with ID: ${id}`);
      
      // Update starred status in cache if caching is enabled
      if (this.useCache) {
        gistCache.set(`gist-starred-${id}`, true);
      }
      
      return true;
    } catch (error) {
      logger.error(`Error starring gist ${id}: ${error}`);
      throw new Error(`Failed to star gist ${id}: ${(error as Error).message}`);
    }
  }
  
  /**
   * Unstar a gist
   * @param id Gist ID
   * @returns True if successful
   */
  public async unstarGist(id: string): Promise<boolean> {
    try {
      if (!id) {
        throw new Error('Gist ID is required');
      }
      
      logger.debug(`Unstarring gist with ID: ${id}`);
      
      await this.client.delete(`/${id}/star`);
      
      logger.info(`Unstarred gist with ID: ${id}`);
      
      // Update starred status in cache if caching is enabled
      if (this.useCache) {
        gistCache.set(`gist-starred-${id}`, false);
      }
      
      return true;
    } catch (error) {
      logger.error(`Error unstarring gist ${id}: ${error}`);
      throw new Error(`Failed to unstar gist ${id}: ${(error as Error).message}`);
    }
  }
  
  /**
   * Check if a gist is starred
   * @param id Gist ID
   * @returns True if starred
   */
  public async isGistStarred(id: string): Promise<boolean> {
    try {
      if (!id) {
        throw new Error('Gist ID is required');
      }
      
      // Check cache first if caching is enabled
      const cacheKey = `gist-starred-${id}`;
      let isStarred: boolean | undefined;
      
      if (this.useCache) {
        isStarred = gistCache.get<boolean>(cacheKey);
        if (isStarred !== undefined) {
          logger.debug(`Using cached starred status for gist ${id}: ${isStarred}`);
          return isStarred;
        }
      }
      
      logger.debug(`Checking if gist ${id} is starred`);
      
      const response = await this.client.get(`/${id}/star`);
      isStarred = response.status === 204;
      
      // Cache the result if caching is enabled
      if (this.useCache) {
        gistCache.set(cacheKey, isStarred);
      }
      
      return isStarred;
    } catch (error) {
      // 404 means not starred
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        // Cache the result if caching is enabled
        if (this.useCache) {
          gistCache.set(`gist-starred-${id}`, false);
        }
        return false;
      }
      
      logger.error(`Error checking if gist ${id} is starred: ${error}`);
      throw new Error(`Failed to check if gist ${id} is starred: ${(error as Error).message}`);
    }
  }
  
  /**
   * Fork a gist
   * @param id Gist ID
   * @returns Forked gist
   */
  public async forkGist(id: string): Promise<Gist> {
    try {
      logger.debug(`Forking gist with ID: ${id}`);
      
      const response = await this.client.post(`/${id}/forks`);
      
      logger.info(`Forked gist with ID: ${response.data.id}`);
      
      // Cache the forked gist if caching is enabled
      if (this.useCache) {
        const gist = response.data;
        gistCache.set(`gist-${gist.id}`, gist);
        
        // Invalidate user gists cache since we've added a new gist
        this.invalidateUserGistsCache();
      }
      
      return response.data;
    } catch (error) {
      logger.error(`Error forking gist ${id}: ${error}`);
      throw new Error(`Failed to fork gist ${id}: ${(error as Error).message}`);
    }
  }
  
  /**
   * Invalidate all cached user gists for the current user
   * This is called whenever we create, update, or delete a gist
   */
  private invalidateUserGistsCache(): void {
    if (!this.useCache) return;
    
    // Clear all cached gists for this user from the cache
    const cacheKeyPrefix = `user-gists-${this.username}`;
    
    // Get all keys in the cache
    for (let i = 1; i <= 10; i++) {  // Assume we don't cache more than 10 pages
      for (let j = 10; j <= 100; j += 10) {  // Common per_page values
        gistCache.delete(`${cacheKeyPrefix}-${i}-${j}`);
      }
    }
    
    logger.debug(`Invalidated user gists cache for ${this.username}`);
  }
} 