/**
 * Job API Validation Rules
 * 
 * Provides validation rules for job-related API endpoints
 */

import { body, param, ValidationChain } from 'express-validator';
import { JobStatus } from '../jobs/Queue';

/**
 * Validators for job-related API endpoints
 */
export const jobValidators = {
  /**
   * Validation rules for getting a job by ID
   */
  getJobById: [
    param('id')
      .notEmpty()
      .withMessage('Job ID is required')
      .isString()
      .withMessage('Job ID must be a string'),
  ],
  
  /**
   * Validation rules for getting jobs by status
   */
  getJobsByStatus: [
    param('status')
      .notEmpty()
      .withMessage('Status is required')
      .isString()
      .withMessage('Status must be a string')
      .isIn(Object.values(JobStatus))
      .withMessage(`Invalid job status. Must be one of: ${Object.values(JobStatus).join(', ')}`),
  ],
  
  /**
   * Validation rules for clearing completed jobs
   */
  clearCompletedJobs: [],
  
  /**
   * Validation rules for creating a batch processing job
   */
  createBatchProcessingJob: [
    body('items')
      .notEmpty()
      .withMessage('Items are required')
      .isArray()
      .withMessage('Items must be an array')
      .custom((items) => {
        if (!items || !Array.isArray(items) || items.length === 0) {
          throw new Error('At least one item is required');
        }
        return true;
      }),
  ],
  
  /**
   * Validation rules for creating an export job
   */
  createExportJob: [
    body('format')
      .notEmpty()
      .withMessage('Format is required')
      .isString()
      .withMessage('Format must be a string')
      .isIn(['json', 'csv', 'xml', 'txt'])
      .withMessage('Invalid export format. Must be one of: json, csv, xml, txt'),
    
    body('items')
      .notEmpty()
      .withMessage('Items are required')
      .isArray()
      .withMessage('Items must be an array')
      .custom((items) => {
        if (!items || !Array.isArray(items) || items.length === 0) {
          throw new Error('At least one item is required');
        }
        return true;
      }),
  ],
  
  /**
   * Validation rules for creating a notification job
   */
  createNotificationJob: [
    body('to')
      .notEmpty()
      .withMessage('Recipient is required')
      .isString()
      .withMessage('Recipient must be a string')
      .isEmail()
      .withMessage('Recipient must be a valid email address'),
    
    body('subject')
      .notEmpty()
      .withMessage('Subject is required')
      .isString()
      .withMessage('Subject must be a string')
      .isLength({ max: 100 })
      .withMessage('Subject must be at most 100 characters'),
    
    body('message')
      .notEmpty()
      .withMessage('Message is required')
      .isString()
      .withMessage('Message must be a string'),
  ],
}; 