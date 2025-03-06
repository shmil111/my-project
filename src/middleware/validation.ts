/**
 * Validation Middleware
 * 
 * This middleware provides validation functions for request data using express-validator.
 */

import { Request, Response, NextFunction } from 'express';
import { body, param, query, validationResult, ValidationChain } from 'express-validator';
import { ApiError } from './errorHandler';
import { createLogger } from '../utils/logger';

// Initialize logger
const logger = createLogger('Validation');

/**
 * Middleware to validate request against provided rules
 */
export const validate = (validations: ValidationChain[]) => {
  return async (req: Request, res: Response, next: NextFunction) => {
    // Execute all validations
    await Promise.all(validations.map(validation => validation.run(req)));
    
    // Check if there are validation errors
    const errors = validationResult(req);
    if (errors.isEmpty()) {
      return next();
    }
    
    // Log validation errors
    logger.debug(`Validation errors: ${JSON.stringify(errors.array())}`);
    
    // Get the array of errors and create a simple message
    const errorArray = errors.array();
    const errorMessages = errorArray.map(err => `${err.msg}`);
    
    // Return a 400 Bad Request with the validation error
    throw ApiError.badRequest(`Validation error: ${errorMessages.join(', ')}`);
  };
};

/**
 * Common validators for reuse across routes
 */
export const validators = {
  // Auth validators
  auth: {
    register: [
      body('username')
        .exists().withMessage('is required')
        .isString().withMessage('must be a string')
        .trim()
        .isLength({ min: 3, max: 20 }).withMessage('must be between 3 and 20 characters')
        .matches(/^[a-zA-Z0-9_]+$/).withMessage('must contain only letters, numbers, and underscores'),
      body('email')
        .exists().withMessage('is required')
        .isEmail().withMessage('must be a valid email address')
        .normalizeEmail(),
      body('password')
        .exists().withMessage('is required')
        .isString().withMessage('must be a string')
        .isLength({ min: 8 }).withMessage('must be at least 8 characters')
        .matches(/[a-z]/).withMessage('must contain at least one lowercase letter')
        .matches(/[A-Z]/).withMessage('must contain at least one uppercase letter')
        .matches(/[0-9]/).withMessage('must contain at least one number')
    ],
    login: [
      body('username')
        .exists().withMessage('is required')
        .isString().withMessage('must be a string')
        .trim()
        .notEmpty().withMessage('cannot be empty'),
      body('password')
        .exists().withMessage('is required')
        .isString().withMessage('must be a string')
        .notEmpty().withMessage('cannot be empty')
    ],
    validate: [
      body('token')
        .exists().withMessage('is required')
        .isString().withMessage('must be a string')
        .notEmpty().withMessage('cannot be empty')
    ]
  },
  
  // Data validators
  data: {
    create: [
      body('name')
        .exists().withMessage('is required')
        .isString().withMessage('must be a string')
        .trim()
        .notEmpty().withMessage('cannot be empty'),
      body('description')
        .optional()
        .isString().withMessage('must be a string')
        .trim()
    ],
    update: [
      param('id')
        .exists().withMessage('is required')
        .notEmpty().withMessage('cannot be empty'),
      body('name')
        .optional()
        .isString().withMessage('must be a string')
        .trim()
        .notEmpty().withMessage('cannot be empty'),
      body('description')
        .optional()
        .isString().withMessage('must be a string')
        .trim()
    ],
    getById: [
      param('id')
        .exists().withMessage('is required')
        .notEmpty().withMessage('cannot be empty')
    ],
    getAll: [
      query('limit')
        .optional()
        .isInt({ min: 1 }).withMessage('must be a positive integer'),
      query('offset')
        .optional()
        .isInt({ min: 0 }).withMessage('must be a non-negative integer'),
      query('sortBy')
        .optional()
        .isString().withMessage('must be a string'),
      query('sortDirection')
        .optional()
        .isIn(['asc', 'desc']).withMessage('must be either "asc" or "desc"')
    ]
  },
  
  // Text processing validators
  text: {
    sentiment: [
      body('text')
        .exists().withMessage('is required')
        .isString().withMessage('must be a string')
        .trim()
        .notEmpty().withMessage('cannot be empty')
    ],
    translate: [
      body('text')
        .exists().withMessage('is required')
        .isString().withMessage('must be a string')
        .trim()
        .notEmpty().withMessage('cannot be empty'),
      body('sourceLang')
        .exists().withMessage('is required')
        .isString().withMessage('must be a string')
        .trim()
        .notEmpty().withMessage('cannot be empty'),
      body('targetLang')
        .exists().withMessage('is required')
        .isString().withMessage('must be a string')
        .trim()
        .notEmpty().withMessage('cannot be empty')
    ],
    summarize: [
      body('text')
        .exists().withMessage('is required')
        .isString().withMessage('must be a string')
        .trim()
        .notEmpty().withMessage('cannot be empty'),
      body('maxLength')
        .optional()
        .isInt({ min: 1 }).withMessage('must be a positive integer')
    ]
  },
  
  // Memory validators
  memory: {
    getItem: [
      param('namespace')
        .exists().withMessage('is required')
        .isString().withMessage('must be a string')
        .trim()
        .notEmpty().withMessage('cannot be empty'),
      param('key')
        .exists().withMessage('is required')
        .isString().withMessage('must be a string')
        .trim()
        .notEmpty().withMessage('cannot be empty'),
      query('type')
        .optional()
        .isIn(['short-term', 'long-term']).withMessage('must be either "short-term" or "long-term"')
    ],
    setItem: [
      param('namespace')
        .exists().withMessage('is required')
        .isString().withMessage('must be a string')
        .trim()
        .notEmpty().withMessage('cannot be empty'),
      body('key')
        .exists().withMessage('is required')
        .isString().withMessage('must be a string')
        .trim()
        .notEmpty().withMessage('cannot be empty'),
      body('value')
        .exists().withMessage('is required'),
      body('ttl')
        .optional()
        .isInt({ min: 1 }).withMessage('must be a positive integer'),
      body('type')
        .optional()
        .isIn(['short-term', 'long-term']).withMessage('must be either "short-term" or "long-term"')
    ],
    listItems: [
      param('namespace')
        .exists().withMessage('is required')
        .isString().withMessage('must be a string')
        .trim()
        .notEmpty().withMessage('cannot be empty'),
      query('type')
        .optional()
        .isIn(['short-term', 'long-term']).withMessage('must be either "short-term" or "long-term"')
    ],
    clearNamespace: [
      param('namespace')
        .exists().withMessage('is required')
        .isString().withMessage('must be a string')
        .trim()
        .notEmpty().withMessage('cannot be empty'),
      body('type')
        .optional()
        .isIn(['short-term', 'long-term']).withMessage('must be either "short-term" or "long-term"')
    ]
  }
}; 