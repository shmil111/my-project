const env = require('../utils/env');

const apiConfig = {
    baseUrl: process.env.API_BASE_URL || 'http://localhost:8080',
    apiKey: process.env.API_KEY,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    },
    endpoints: {
        health: '/api/health',
        journals: '/api/journals',
        messages: '/api/messages',
        profile: '/api/profile',
        kindroid: {
            process: '/api/kindroid/process',
            sendMessage: '/api/kindroid/message'
        }
    }
};

module.exports = apiConfig; 