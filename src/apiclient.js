class EveApiClient {
    constructor(config = {}) {
        this.baseUrl = config.baseUrl || 'https://www.woodenghost.org/api';
        this.apiKey = config.apiKey;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` }),
            ...options.headers
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

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
        return this.request('/journals');
    }

    async getJournal(filename) {
        return this.request(`/journals/${filename}`);
    }

    async createJournal(data) {
        return this.request('/journals', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async deleteJournal(filename) {
        return this.request(`/journals/${filename}`, {
            method: 'DELETE'
        });
    }

    // Message endpoints
    async getMessages() {
        return this.request('/messages');
    }

    async sendMessage(data) {
        return this.request('/messages', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Kindroid endpoints
    async processText(data) {
        return this.request('/kindroid/process', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async sendKindroidMessage(data) {
        return this.request('/kindroid/send-message', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Profile endpoint
    async getProfile() {
        return this.request('/auth/profile');
    }

    // Health check
    async checkHealth() {
        return this.request('/health');
    }
}

// Export for both browser and Node.js environments
if (typeof window !== 'undefined') {
    window.EveApiClient = EveApiClient;
} else if (typeof module !== 'undefined' && module.exports) {
    module.exports = EveApiClient;
} 