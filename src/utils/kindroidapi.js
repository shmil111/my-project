/**
 * Shared Kindroid API Client
 * 
 * This module provides a common interface for interacting with the Kindroid API
 * Used by both memory-enhancer.js and journal-memory.js to prevent code duplication.
 */

require('dotenv').config();
const axios = require('axios');

const KINDROID_API_BASE_URL = 'https://api.kindroid.ai/v1';

class KindroidAPI {
  constructor(apiKey, aiId) {
    this.apiKey = apiKey;
    this.aiId = aiId;
    this.headers = {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json'
    };
  }
  
  async sendMessage(message) {
    try {
      console.log(`Sending message to Kindroid API for AI ${this.aiId}...`);
      
      const response = await axios.post(
        `${KINDROID_API_BASE_URL}/send-message`,
        {
          ai_id: this.aiId,
          message
        },
        { headers: this.headers }
      );
      
      if (response.status !== 200) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      console.log('Message sent successfully');
      return response.data;
    } catch (error) {
      console.error('Error sending message to Kindroid API:', error.message);
      throw error;
    }
  }
  
  async chatBreak(greeting = "Hello Eve, let's start a new session.") {
    try {
      console.log('Creating a chat break...');
      
      const response = await axios.post(
        `${KINDROID_API_BASE_URL}/chat-break`,
        {
          ai_id: this.aiId,
          greeting
        },
        { headers: this.headers }
      );
      
      if (response.status !== 200) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      console.log('Chat break created successfully');
      return response.data;
    } catch (error) {
      console.error('Error creating chat break:', error.message);
      throw error;
    }
  }
}

module.exports = {
  KindroidAPI,
  KINDROID_API_BASE_URL
}; 