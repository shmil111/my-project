const apiConfig = require('../config/api-config');
const journalStore = require('./journal-store');

class ApiService {
    constructor() {
        this.baseUrl = apiConfig.baseUrl;
        this.headers = {
            ...apiConfig.headers,
            ...(apiConfig.apiKey && { 'Authorization': `Bearer ${apiConfig.apiKey}` })
        };
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const requestOptions = {
            ...options,
            headers: {
                ...this.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, requestOptions);
            
            if (!response.ok) {
                throw new Error(`API request failed: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    }

    // Journal endpoints
    async getJournals() {
        return journalStore.getAllJournals();
    }

    async getJournal(filename) {
        const journal = journalStore.getJournal(filename);
        if (!journal) {
            throw new Error('Journal not found');
        }
        return journal;
    }

    async createJournal(data) {
        return journalStore.createJournal(data);
    }

    async deleteJournal(filename) {
        const success = journalStore.deleteJournal(filename);
        if (!success) {
            throw new Error('Journal not found');
        }
    }

    // Message endpoints
    async getMessages() {
        return this.request(apiConfig.endpoints.messages);
    }

    async sendMessage(data) {
        return this.request(apiConfig.endpoints.messages, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Kindroid endpoints
    async processText(data) {
        return this.request(apiConfig.endpoints.kindroid.process, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async sendKindroidMessage(data) {
        return this.request(apiConfig.endpoints.kindroid.sendMessage, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Profile endpoint
    async getProfile() {
        return this.request(apiConfig.endpoints.profile);
    }

    // Health check
    async checkHealth() {
        return {
            status: 'healthy',
            timestamp: new Date().toISOString()
        };
    }
}

module.exports = new ApiService(); 