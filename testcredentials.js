/**
 * Test script to verify credential loading.
 */
console.error("Starting test script...");

try {
  const config = require('./config');
  console.error("Successfully imported config module");
  
  // Log config object directly to stderr
  console.error("Config module contains:", config);
  
  const fs = require('fs');
  const path = require('path');
  
  function main() {
    console.error("Starting main function...");
    
    try {
      console.error("Testing credential loading from C:\\Documents\\credentials\\myproject\\");
      console.error("-".repeat(60));
      
      // Check direct file access to ensure files exist
      const CREDENTIALS_DIR = 'C:/Documents/credentials/myproject';
      console.error(`Checking if credentials directory exists: ${fs.existsSync(CREDENTIALS_DIR)}`);
      
      if (fs.existsSync(CREDENTIALS_DIR)) {
        // List all files in the directory
        try {
          const files = fs.readdirSync(CREDENTIALS_DIR);
          console.error("Files in credentials directory:", files);
        } catch (err) {
          console.error(`Error listing files: ${err.message}`);
        }
        
        // API_KEY
        const apiKeyPath = path.join(CREDENTIALS_DIR, 'API_KEY');
        if (fs.existsSync(apiKeyPath)) {
          try {
            const apiKey = fs.readFileSync(apiKeyPath, 'utf8').trim();
            console.error(`Found API_KEY file with content: ${apiKey.substring(0, 3)}...`);
          } catch (err) {
            console.error(`Error reading API_KEY file: ${err.message}`);
          }
        } else {
          console.error("API_KEY file not found");
        }
        
        // DB_PASSWORD
        const dbPasswordPath = path.join(CREDENTIALS_DIR, 'DB_PASSWORD');
        if (fs.existsSync(dbPasswordPath)) {
          try {
            const dbPassword = fs.readFileSync(dbPasswordPath, 'utf8').trim();
            console.error(`Found DB_PASSWORD file with content: ${dbPassword.substring(0, 3)}...`);
          } catch (err) {
            console.error(`Error reading DB_PASSWORD file: ${err.message}`);
          }
        } else {
          console.error("DB_PASSWORD file not found");
        }
        
        // SECRET_TOKEN
        const secretTokenPath = path.join(CREDENTIALS_DIR, 'SECRET_TOKEN');
        if (fs.existsSync(secretTokenPath)) {
          try {
            const secretToken = fs.readFileSync(secretTokenPath, 'utf8').trim();
            console.error(`Found SECRET_TOKEN file with content: ${secretToken.substring(0, 3)}...`);
          } catch (err) {
            console.error(`Error reading SECRET_TOKEN file: ${err.message}`);
          }
        } else {
          console.error("SECRET_TOKEN file not found");
        }
      } else {
        console.error(`Credentials directory ${CREDENTIALS_DIR} not found`);
      }
    } catch (err) {
      console.error(`Unexpected error in test: ${err.message}`);
      console.error(err.stack);
    }
  }
  
  // Run the test
  main();
} catch (err) {
  console.error(`Critical error loading modules: ${err.message}`);
  console.error(err.stack);
} 