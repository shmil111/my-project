require('dotenv').config({ path: 'C:/Documents/credentials/myproject/.env' });

const config = {
  apiKey: process.env.API_KEY,
  dbPassword: process.env.DB_PASSWORD,
  secretToken: process.env.SECRET_TOKEN
};

module.exports = config; 