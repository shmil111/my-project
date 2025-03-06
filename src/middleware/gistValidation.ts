/**
 * Gist API Validation Rules
 * 
 * Provides validation rules for GitHub Gist API endpoints
 */

import { body, param, query, ValidationChain } from 'express-validator';

/**
 * Validators for Gist-related API endpoints
 */
export const gistValidators = {
  /**
   * Validation rules for getting all gists
   */
  getGists: [
    query('page')
      .optional()
      .isInt({ min: 1 })
      .withMessage('Page must be a positive integer'),
    
    query('perPage')
      .optional()
      .isInt({ min: 1, max: 100 })
      .withMessage('Per page must be between 1 and 100'),
  ],
  
  /**
   * Validation rules for getting user gists
   */
  getUserGists: [
    param('username')
      .notEmpty()
      .withMessage('Username is required')
      .isString()
      .withMessage('Username must be a string'),
    
    query('page')
      .optional()
      .isInt({ min: 1 })
      .withMessage('Page must be a positive integer'),
    
    query('perPage')
      .optional()
      .isInt({ min: 1, max: 100 })
      .withMessage('Per page must be between 1 and 100'),
  ],
  
  /**
   * Validation rules for getting a gist by ID
   */
  getGist: [
    param('id')
      .notEmpty()
      .withMessage('Gist ID is required')
      .isString()
      .withMessage('Gist ID must be a string'),
  ],
  
  /**
   * Validation rules for creating a gist
   */
  createGist: [
    body('description')
      .optional()
      .isString()
      .withMessage('Description must be a string'),
    
    body('public')
      .optional()
      .isBoolean()
      .withMessage('Public field must be a boolean'),
    
    body('files')
      .notEmpty()
      .withMessage('Files are required')
      .isObject()
      .withMessage('Files must be an object')
      .custom((files: Record<string, any>) => {
        if (!files || typeof files !== 'object' || Object.keys(files).length === 0) {
          throw new Error('At least one file is required');
        }
        
        // Check that each file has content
        for (const [filename, file] of Object.entries(files)) {
          if (!filename || filename.trim() === '') {
            throw new Error('Filename cannot be empty');
          }
          
          if (!file || typeof file !== 'object') {
            throw new Error(`File "${filename}" must be an object`);
          }
          
          if (!file.content || typeof file.content !== 'string') {
            throw new Error(`File "${filename}" must have content`);
          }
        }
        
        return true;
      }),
  ],
  
  /**
   * Validation rules for updating a gist
   */
  updateGist: [
    param('id')
      .notEmpty()
      .withMessage('Gist ID is required')
      .isString()
      .withMessage('Gist ID must be a string'),
    
    body('description')
      .optional()
      .isString()
      .withMessage('Description must be a string'),
    
    body('files')
      .optional()
      .isObject()
      .withMessage('Files must be an object')
      .custom((files: Record<string, any>) => {
        if (!files || typeof files !== 'object') {
          return true; // No files to update
        }
        
        // Check that each file has content or is null (for deletion)
        for (const [filename, file] of Object.entries(files)) {
          if (!filename || filename.trim() === '') {
            throw new Error('Filename cannot be empty');
          }
          
          if (file === null) {
            continue; // Null means delete the file
          }
          
          if (typeof file !== 'object') {
            throw new Error(`File "${filename}" must be an object or null`);
          }
          
          if (file.content && typeof file.content !== 'string') {
            throw new Error(`File "${filename}" content must be a string`);
          }
        }
        
        return true;
      }),
  ],
  
  /**
   * Validation rules for deleting a gist
   */
  deleteGist: [
    param('id')
      .notEmpty()
      .withMessage('Gist ID is required')
      .isString()
      .withMessage('Gist ID must be a string'),
  ],
  
  /**
   * Validation rules for starring/unstarring a gist
   */
  starGist: [
    param('id')
      .notEmpty()
      .withMessage('Gist ID is required')
      .isString()
      .withMessage('Gist ID must be a string'),
  ],
  
  /**
   * Validation rules for forking a gist
   */
  forkGist: [
    param('id')
      .notEmpty()
      .withMessage('Gist ID is required')
      .isString()
      .withMessage('Gist ID must be a string'),
  ],
}; 