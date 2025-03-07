/**
 * Security module for API key verification and credential usage tracking
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const config = require('./config');

// Store for tracking credential usage
const usageLog = [];
const MAX_LOG_SIZE = 1000; // Maximum number of entries to keep in memory

/**
 * Generate a unique request identifier
 * @returns {string} Unique request ID
 */
function generateRequestId() {
  return crypto.randomUUID();
}

/**
 * Mask a credential for secure logging
 * @param {string} credential - The credential to mask
 * @returns {string} Masked credential
 */
function maskCredential(credential) {
  if (!credential) return 'undefined';
  if (credential.length <= 6) return '******';
  
  return `${credential.substring(0, 3)}...${credential.substring(credential.length - 3)}`;
}

/**
 * Log credential usage with security tracking information
 * @param {string} credentialType - Type of credential (API_KEY, DB_PASSWORD, etc.)
 * @param {string} component - Component using the credential
 * @param {string} operation - Operation being performed
 * @param {object} options - Additional options
 * @returns {string} Request ID for this operation
 */
function logCredentialUsage(credentialType, component, operation, options = {}) {
  const requestId = options.requestId || generateRequestId();
  const timestamp = new Date().toISOString();
  const clientIp = options.clientIp || 'internal';
  
  // Create usage record
  const usageRecord = {
    requestId,
    timestamp,
    credentialType,
    component,
    operation,
    clientIp,
    success: options.success !== false,
    userId: options.userId || 'system'
  };
  
  // Add to in-memory log with size limit
  usageLog.unshift(usageRecord);
  if (usageLog.length > MAX_LOG_SIZE) {
    usageLog.pop();
  }
  
  // Log to console (in production, you'd use a proper logging system)
  console.log(`[${timestamp}] [${requestId}] Credential usage: ${credentialType} by ${component} for ${operation} from ${clientIp}`);
  
  // In a real system, you might also write to a secure log file or database
  
  return requestId;
}

/**
 * Verify API key format and validity
 * @param {string} apiKey - The API key to verify
 * @param {object} options - Verification options
 * @returns {boolean} True if valid, false otherwise
 */
function verifyApiKey(apiKey, options = {}) {
  // Check API key format
  if (!apiKey || typeof apiKey !== 'string' || apiKey.length < 10) {
    logCredentialUsage('API_KEY', options.component || 'unknown', 'verify', { 
      success: false,
      requestId: options.requestId,
      clientIp: options.clientIp,
      userId: options.userId
    });
    return false;
  }
  
  // In a real system, you might validate against a whitelist or check a hash
  // This is a simple example that just checks if it matches our stored API key
  const isValid = apiKey === config.apiKey;
  
  logCredentialUsage('API_KEY', options.component || 'unknown', 'verify', {
    success: isValid,
    requestId: options.requestId,
    clientIp: options.clientIp,
    userId: options.userId
  });
  
  return isValid;
}

/**
 * Verify database password
 * @param {string} password - The password to verify
 * @param {object} options - Verification options
 * @returns {boolean} True if valid, false otherwise
 */
function verifyDbPassword(password, options = {}) {
  // Basic validation
  if (!password || typeof password !== 'string' || password.length < 8) {
    logCredentialUsage('DB_PASSWORD', options.component || 'unknown', 'verify', { 
      success: false,
      requestId: options.requestId,
      clientIp: options.clientIp,
      userId: options.userId 
    });
    return false;
  }
  
  // Simple verification
  const isValid = password === config.dbPassword;
  
  logCredentialUsage('DB_PASSWORD', options.component || 'unknown', 'verify', {
    success: isValid,
    requestId: options.requestId,
    clientIp: options.clientIp,
    userId: options.userId
  });
  
  return isValid;
}

/**
 * Verify mail API key format and validity
 * @param {string} mailApiKey - The mail API key to verify
 * @param {object} options - Verification options
 * @returns {boolean} True if valid, false otherwise
 */
function verifyMailApiKey(mailApiKey, options = {}) {
  // Check API key format
  if (!mailApiKey || typeof mailApiKey !== 'string' || mailApiKey.length < 8) {
    logCredentialUsage('MAIL_API_KEY', options.component || 'unknown', 'verify', { 
      success: false,
      requestId: options.requestId,
      clientIp: options.clientIp,
      userId: options.userId
    });
    return false;
  }
  
  // In a real system, you'd validate this properly
  const isValid = mailApiKey === config.mailApiKey;
  
  logCredentialUsage('MAIL_API_KEY', options.component || 'unknown', 'verify', {
    success: isValid,
    requestId: options.requestId,
    clientIp: options.clientIp,
    userId: options.userId
  });
  
  return isValid;
}

/**
 * Verify logging service API key format and validity
 * @param {string} loggingApiKey - The logging API key to verify
 * @param {object} options - Verification options
 * @returns {boolean} True if valid, false otherwise
 */
function verifyLoggingApiKey(loggingApiKey, options = {}) {
  // Check API key format
  if (!loggingApiKey || typeof loggingApiKey !== 'string' || loggingApiKey.length < 8) {
    logCredentialUsage('LOGGING_API_KEY', options.component || 'unknown', 'verify', { 
      success: false,
      requestId: options.requestId,
      clientIp: options.clientIp,
      userId: options.userId
    });
    return false;
  }
  
  // In a real system, you'd validate this properly
  const isValid = loggingApiKey === config.loggingApiKey;
  
  logCredentialUsage('LOGGING_API_KEY', options.component || 'unknown', 'verify', {
    success: isValid,
    requestId: options.requestId,
    clientIp: options.clientIp,
    userId: options.userId
  });
  
  return isValid;
}

/**
 * Get recent credential usage logs
 * @param {number} limit - Maximum number of records to return
 * @returns {Array} Usage records
 */
function getRecentUsage(limit = 100) {
  return usageLog.slice(0, limit);
}

/**
 * Analyze credential usage for suspicious patterns
 * @returns {Array} List of suspicious activities
 */
function analyzeForSuspiciousActivity() {
  // In a real implementation, this would contain logic to detect:
  // - Unusual access patterns
  // - Access from unexpected IPs
  // - Credential usage at unusual times
  // - Multiple failed verification attempts
  
  // This is a placeholder that simply looks for failed verifications
  const suspiciousActivities = usageLog
    .filter(record => !record.success)
    .map(record => ({
      level: 'warning',
      message: `Failed credential verification: ${record.credentialType}`,
      timestamp: record.timestamp,
      requestId: record.requestId,
      clientIp: record.clientIp,
      component: record.component
    }));
  
  return suspiciousActivities;
}

/**
 * Create a middleware for Express that adds request ID and logs API key usage
 * @returns {Function} Express middleware function
 */
function createSecurityMiddleware() {
  return function(req, res, next) {
    // Add request ID to request object
    req.requestId = generateRequestId();
    
    // Add to response headers
    res.setHeader('X-Request-ID', req.requestId);
    
    // Capture IP address
    const clientIp = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
    
    // Check for API key in Authorization header
    const authHeader = req.headers.authorization;
    if (authHeader && authHeader.startsWith('Bearer ')) {
      const apiKey = authHeader.substring(7);
      
      const isValid = verifyApiKey(apiKey, {
        component: 'api-middleware',
        operation: req.method + ' ' + req.path,
        requestId: req.requestId,
        clientIp: clientIp
      });
      
      // Attach validation result to request for use in route handlers
      req.apiKeyValid = isValid;
    }
    
    next();
  };
}

module.exports = {
  generateRequestId,
  maskCredential,
  logCredentialUsage,
  verifyApiKey,
  verifyDbPassword,
  verifyMailApiKey,
  verifyLoggingApiKey,
  getRecentUsage,
  analyzeForSuspiciousActivity,
  createSecurityMiddleware
}; 