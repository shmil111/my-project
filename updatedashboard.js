/**
 * Script to automatically update the API status dashboard by checking
 * the availability and validity of API credentials
 */
const fs = require('fs');
const path = require('path');
const config = require('./config');
const security = require('./security');

// Constants
const DASHBOARD_FILE = path.join(__dirname, 'api_status_dashboard.md');
const CREDENTIALS_DIR = 'C:/Documents/credentials/myproject';

// Service definitions with their required credentials
const SERVICES = [
  {
    name: 'Core Authentication API',
    credentialFile: 'API_KEY',
    validateFn: security.verifyApiKey,
    credentialKey: 'apiKey'
  },
  {
    name: 'Database Connection Service',
    credentialFile: 'DB_PASSWORD',
    validateFn: security.verifyDbPassword,
    credentialKey: 'dbPassword'
  },
  {
    name: 'Cryptographic Service',
    credentialFile: 'SECRET_TOKEN',
    validateFn: (token) => token && token.length >= 16,
    credentialKey: 'secretToken'
  },
  {
    name: 'Mail Service',
    credentialFile: 'MAIL_API_KEY',
    validateFn: (key) => key && key.length >= 8,
    credentialKey: null
  },
  {
    name: 'Logging Service',
    credentialFile: 'LOGGING_API_KEY',
    validateFn: (key) => key && key.length >= 8,
    credentialKey: null
  },
  {
    name: 'Analytics API',
    credentialFile: 'ANALYTICS_API_KEY',
    validateFn: (key) => key && key.length >= 8,
    credentialKey: null
  },
  {
    name: 'Payment Gateway',
    credentialFile: 'PAYMENT_API_KEY',
    validateFn: (key) => key && key.length >= 8,
    credentialKey: null
  },
  {
    name: 'External Movie Database API',
    credentialFile: 'MOVIE_DB_API_KEY',
    validateFn: (key) => key && key.length >= 8,
    credentialKey: null
  },
  {
    name: 'User Management Service',
    credentialFile: 'USER_MGMT_API_KEY',
    validateFn: (key) => key && key.length >= 8,
    credentialKey: null
  },
  {
    name: 'Content Delivery Network',
    credentialFile: 'CDN_API_KEY',
    validateFn: (key) => key && key.length >= 8,
    credentialKey: null
  }
];

/**
 * Check if a credential file exists and is valid
 * @param {Object} service - Service to check
 * @returns {Object} Status information
 */
function checkServiceStatus(service) {
  // Default status is RED
  let status = {
    color: '🔴 RED',
    description: 'No codebase embedding created yet',
    details: 'Pending implementation',
    hasFile: false,
    isValid: false
  };
  
  // Check if credential file exists
  const filePath = path.join(CREDENTIALS_DIR, service.credentialFile);
  try {
    if (fs.existsSync(filePath)) {
      status.hasFile = true;
      status.description = `API key found in ${CREDENTIALS_DIR}`;
      
      // For services integrated in config, check if loaded properly
      if (service.credentialKey && config[service.credentialKey]) {
        const isValid = service.validateFn(config[service.credentialKey]);
        if (isValid) {
          status.color = '🟢 GREEN';
          status.details = 'Successfully integrated with security module';
          status.isValid = true;
        } else {
          status.color = '🟡 ORANGE';
          status.details = 'API key format validation failed';
        }
      } else if (service.credentialKey) {
        // Credential should be in config but isn't
        status.color = '🟡 ORANGE';
        status.details = 'API configured but credentials not properly loaded';
      } else {
        // Check if file content is valid by reading directly
        const credential = fs.readFileSync(filePath, 'utf8').trim();
        const isValid = service.validateFn(credential);
        if (isValid) {
          status.color = '🟡 ORANGE';
          status.details = 'Credential file exists but not integrated with security module';
        } else {
          status.color = '🟡 ORANGE';
          status.details = 'Credential file exists but has invalid format';
        }
      }
    }
  } catch (err) {
    console.error(`Error checking status for ${service.name}:`, err.message);
  }
  
  return status;
}

/**
 * Update the API status dashboard markdown file
 */
function updateDashboard() {
  try {
    // Read the current dashboard file
    const dashboardContent = fs.readFileSync(DASHBOARD_FILE, 'utf8');
    
    // Update the timestamp
    const now = new Date().toISOString();
    let updatedContent = dashboardContent.replace(
      /\*Last Updated: <!-- AUTO_UPDATE_TIMESTAMP -->\*/,
      `*Last Updated: ${now}*`
    );
    
    // Check service statuses
    const serviceStatuses = SERVICES.map(service => {
      const status = checkServiceStatus(service);
      return {
        service,
        status
      };
    });
    
    // Update the table in the dashboard
    let tableRows = '';
    serviceStatuses.forEach(({ service, status }) => {
      tableRows += `| ${service.name} | ${status.color} | ${status.description} | ${status.details} |\n`;
    });
    
    // Replace the table in the dashboard content
    updatedContent = updatedContent.replace(
      /\| Service \| Status \| Description \| Integration Details \|\n\|---------|--------|-------------|---------------------\|\n([\s\S]*?)(?=\n## Green Light Services Documentation)/,
      `| Service | Status | Description | Integration Details |\n|---------|--------|-------------|---------------------|\n${tableRows}\n`
    );
    
    // Write the updated dashboard back to file
    fs.writeFileSync(DASHBOARD_FILE, updatedContent, 'utf8');
    console.log('API status dashboard updated successfully!');
  } catch (err) {
    console.error('Error updating API status dashboard:', err.message);
  }
}

// Run the update when script is executed directly
if (require.main === module) {
  updateDashboard();
}

module.exports = { updateDashboard, checkServiceStatus }; 