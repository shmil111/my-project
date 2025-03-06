require('dotenv').config();

const env = {
    nodeEnv: process.env.NODE_ENV || 'development',
    port: parseInt(process.env.PORT || '8080', 10),
    httpsPort: parseInt(process.env.HTTPS_PORT || '443', 10),
    host: process.env.HOST || 'localhost',
    domain: process.env.DOMAIN || 'api.woodenghost.org',
    corsOrigin: process.env.CORS_ORIGIN || 'https://www.woodenghost.org',
    
    // Google configuration
    googleEmail: process.env.GOOGLE_EMAIL,
    googleAppPassword: process.env.GOOGLE_APP_PASSWORD,
    googleApiKey: process.env.GOOGLE_API_KEY,
    
    // Database configuration
    db: {
        implementation: process.env.DB_IMPLEMENTATION || 'memory',
        name: process.env.DB_NAME || 'eve_db',
        path: process.env.DB_PATH || './data/sqlite',
        host: process.env.DB_HOST || 'localhost',
        port: parseInt(process.env.DB_PORT || '5432', 10),
        user: process.env.DB_USER,
        password: process.env.DB_PASSWORD,
    },
    
    // Memory configuration
    memory: {
        capacity: parseInt(process.env.MEMORY_CAPACITY || '100', 10),
        limit: parseInt(process.env.MEMORY_LIMIT || '10000', 10),
    },
    
    // Socket configuration
    socketCorsOrigin: process.env.SOCKET_CORS_ORIGIN || 'https://www.woodenghost.org',
    
    // Validate required environment variables
    validate() {
        const required = [
            'GOOGLE_EMAIL',
            'GOOGLE_APP_PASSWORD',
            'GOOGLE_API_KEY',
        ];
        
        const missing = required.filter(key => !process.env[key]);
        
        if (missing.length > 0) {
            throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
        }
    }
};

// Validate on import
env.validate();

module.exports = env; 