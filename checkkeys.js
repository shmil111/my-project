/**
 * Simple script to check API keys and write results to a file
 */
const fs = require('fs');
const path = require('path');

const CREDENTIALS_DIR = 'C:/Documents/credentials/myproject';
const OUTPUT_FILE = './key_test_results.txt';

// Buffer for log messages
let logMessages = [];

function log(message) {
  logMessages.push(message);
}

// Check if directory exists
log(`Credentials directory (${CREDENTIALS_DIR}) exists: ${fs.existsSync(CREDENTIALS_DIR)}`);

if (fs.existsSync(CREDENTIALS_DIR)) {
  try {
    // List directory contents
    const files = fs.readdirSync(CREDENTIALS_DIR);
    log(`Files in directory: ${files.join(', ')}`);
    
    // Check each credential file
    const credentialFiles = ['API_KEY', 'DB_PASSWORD', 'SECRET_TOKEN'];
    
    credentialFiles.forEach(filename => {
      const filePath = path.join(CREDENTIALS_DIR, filename);
      if (fs.existsSync(filePath)) {
        try {
          const content = fs.readFileSync(filePath, 'utf8').trim();
          log(`${filename}: Found and contains ${content.length} characters`);
          log(`${filename} content starts with: ${content.substring(0, 3)}...`);
        } catch (err) {
          log(`Error reading ${filename}: ${err.message}`);
        }
      } else {
        log(`${filename}: File not found`);
      }
    });
  } catch (err) {
    log(`Error accessing directory: ${err.message}`);
  }
} else {
  log('Credentials directory not found');
}

// Write results to file
fs.writeFileSync(OUTPUT_FILE, logMessages.join('\n'), 'utf8');
console.log(`Results written to ${OUTPUT_FILE}`); 