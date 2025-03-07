/**
 * Script to test adding a credential file to see status change
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Credentials directory
const CREDENTIALS_DIR = 'C:/Documents/credentials/myproject';

// Make sure the credentials directory exists
if (!fs.existsSync(CREDENTIALS_DIR)) {
  console.log(`Creating credentials directory: ${CREDENTIALS_DIR}`);
  try {
    fs.mkdirSync(CREDENTIALS_DIR, { recursive: true });
  } catch (err) {
    console.error(`Error creating directory: ${err.message}`);
    process.exit(1);
  }
}

// Choose a service to add a credential for
const service = 'Mail Service';
const credentialFile = 'MAIL_API_KEY';
const credentialValue = 'test_mail_api_key_123456789';

// Create the credential file
const filePath = path.join(CREDENTIALS_DIR, credentialFile);
try {
  fs.writeFileSync(filePath, credentialValue);
  console.log(`Created credential file: ${filePath}`);
} catch (err) {
  console.error(`Error creating credential file: ${err.message}`);
  process.exit(1);
}

// Run the dashboard update to see the change
console.log('Running dashboard update...');
try {
  const output = execSync('node update_dashboard.js', { encoding: 'utf8' });
  console.log(output);
} catch (err) {
  console.error(`Error running update: ${err.message}`);
}

console.log(`\nService ${service} should now show as ORANGE in the dashboard.`);
console.log(`You can check the dashboard at: ${path.resolve('api_status_dashboard.md')}`);

// Offer to remove the test credential
const readline = require('readline').createInterface({
  input: process.stdin,
  output: process.stdout
});

readline.question('Do you want to remove the test credential? (y/n) ', answer => {
  if (answer.toLowerCase() === 'y' || answer.toLowerCase() === 'yes') {
    try {
      fs.unlinkSync(filePath);
      console.log(`Removed credential file: ${filePath}`);
      
      // Update dashboard again
      console.log('Running dashboard update...');
      try {
        const output = execSync('node update_dashboard.js', { encoding: 'utf8' });
        console.log(output);
      } catch (err) {
        console.error(`Error running update: ${err.message}`);
      }
    } catch (err) {
      console.error(`Error removing credential file: ${err.message}`);
    }
  }
  
  readline.close();
}); 