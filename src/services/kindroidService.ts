import axios, { AxiosError } from 'axios';
import { createLogger } from '../utils/logger';
import { config } from '../utils/env';
import fs from 'fs';
import path from 'path';

const logger = createLogger('KindroidService');

/**
 * Response from Kindroid AI API
 */
export interface KindroidResponse {
  message: string;
  status: number;
  success: boolean;
  data?: any;
  error?: string;
}

/**
 * Conversation message format for Discord bot endpoint
 */
interface KindroidConversationMessage {
  username: string;
  text: string;
  timestamp: string;
}

/**
 * Memory item for Kindroid AI
 */
interface KindroidMemoryItem {
  key: string;
  value: string;
  timestamp: number;
  priority: number;
  tags?: string[];
}

/**
 * Memory query options for retrieving memories
 */
interface MemoryQueryOptions {
  limit?: number;
  tags?: string[];
  afterTimestamp?: number;
  beforeTimestamp?: number;
  minPriority?: number;
}

/**
 * Service for Kindroid AI API integration
 */
export class KindroidService {
  private apiKey: string;
  private baseUrl: string;
  private aiId: string;
  private memoryCache: Map<string, KindroidMemoryItem>;
  private memoryPersistPath: string;
  private useLocalCache: boolean;

  constructor() {
    this.apiKey = config.kindroid?.apiKey || '';
    this.baseUrl = 'https://api.kindroid.ai/v1';
    this.aiId = config.kindroid?.aiId || '';
    this.memoryCache = new Map();
    this.memoryPersistPath = path.join(process.cwd(), 'data', 'kindroid-memory.json');
    this.useLocalCache = true; // Set to false to disable local caching

    if (!this.apiKey) {
      logger.warn('Kindroid API key not configured. Kindroid functionality will be limited.');
    }

    if (!this.aiId) {
      logger.warn('Kindroid AI ID not configured. Kindroid functionality will be limited.');
    }

    // Ensure data directory exists
    if (this.useLocalCache) {
      const dataDir = path.dirname(this.memoryPersistPath);
      if (!fs.existsSync(dataDir)) {
        try {
          fs.mkdirSync(dataDir, { recursive: true });
        } catch (error) {
          logger.error(`Failed to create data directory: ${error}`);
        }
      }
      
      // Load cached memories
      this.loadMemoryCache();
    }
  }

  /**
   * Send a message to the Kindroid AI and get a response
   * @param message The message to send to the AI
   * @param includeMemories Whether to include relevant memories in the request
   * @returns The AI's response
   */
  async sendMessage(message: string, includeMemories: boolean = true): Promise<KindroidResponse> {
    try {
      if (!this.apiKey || !this.aiId) {
        return {
          message: 'Kindroid API key or AI ID not configured',
          status: 400,
          success: false,
          error: 'Configuration missing'
        };
      }

      // Prepare request data
      const requestData: any = {
        ai_id: this.aiId,
        message
      };

      // Include relevant memories if enabled
      if (includeMemories) {
        const relevantMemories = this.getRelevantMemories(message);
        if (relevantMemories.length > 0) {
          // Format memories for the API (adjust this based on actual API requirements)
          requestData.context = {
            memories: relevantMemories.map(m => ({ 
              content: m.value,
              importance: m.priority
            }))
          };
        }
      }

      const response = await axios.post(
        `${this.baseUrl}/send-message`,
        requestData,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      // Extract potential knowledge to store in memory
      this.extractAndStoreMemories(message, response.data);

      return {
        message: 'Message sent successfully',
        status: response.status,
        success: true,
        data: response.data
      };
    } catch (error) {
      const axiosError = error as AxiosError;
      logger.error(`Error sending message to Kindroid: ${axiosError.message}`);
      
      return {
        message: `Error sending message to Kindroid: ${axiosError.message}`,
        status: axiosError.response?.status || 500,
        success: false,
        error: axiosError.message
      };
    }
  }

  /**
   * Reset the conversation with a chat break and new greeting
   * @param greeting The greeting message to start the new conversation
   * @returns Status of the chat break operation
   */
  async resetConversation(greeting: string): Promise<KindroidResponse> {
    try {
      if (!this.apiKey || !this.aiId) {
        return {
          message: 'Kindroid API key or AI ID not configured',
          status: 400,
          success: false,
          error: 'Configuration missing'
        };
      }

      const response = await axios.post(
        `${this.baseUrl}/chat-break`,
        {
          ai_id: this.aiId,
          greeting
        },
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      return {
        message: 'Chat break successful',
        status: response.status,
        success: true,
        data: response.data
      };
    } catch (error) {
      const axiosError = error as AxiosError;
      logger.error(`Error performing chat break: ${axiosError.message}`);
      
      return {
        message: `Error performing chat break: ${axiosError.message}`,
        status: axiosError.response?.status || 500,
        success: false,
        error: axiosError.message
      };
    }
  }

  /**
   * Process text with combined Kindroid AI and local processing
   * @param text Text to process
   * @param processingType Type of processing to perform
   * @param useMemory Whether to include and update memory during processing
   * @returns Promise with processed result
   */
  async processTextWithAI(
    text: string, 
    processingType: 'analyze' | 'enhance' | 'summarize' | 'question',
    useMemory: boolean = true
  ): Promise<KindroidResponse> {
    try {
      // Formulate prompt based on processing type
      let prompt = '';
      const memoryTags = [`process:${processingType}`];
      
      switch (processingType) {
        case 'analyze':
          prompt = `Please analyze this text and provide insights: "${text}"`;
          memoryTags.push('analysis');
          break;
        case 'enhance':
          prompt = `Please improve this text while maintaining its meaning: "${text}"`;
          memoryTags.push('enhancement');
          break;
        case 'summarize':
          prompt = `Please summarize this text concisely: "${text}"`;
          memoryTags.push('summary');
          break;
        case 'question':
          prompt = text; // Direct question to AI
          memoryTags.push('question');
          break;
        default:
          return {
            success: false,
            error: `Unsupported processing type: ${processingType}`,
            message: `Unsupported processing type: ${processingType}`,
            status: 400
          };
      }
      
      // Include relevant memories if enabled
      if (useMemory) {
        const relevantMemories = this.getRelevantMemories(text, { tags: memoryTags });
        if (relevantMemories.length > 0) {
          const memoryContext = relevantMemories.map(m => m.value).join("\n");
          prompt = `Considering this relevant information:\n${memoryContext}\n\n${prompt}`;
        }
      }

      const result = await this.sendMessage(prompt, false); // Don't double-include memories
      
      // Store the result in memory if successful
      if (result.success && result.data) {
        const aiResponse = typeof result.data === 'string' ? result.data : result.data.response || result.data.message || '';
        
        if (aiResponse) {
          this.storeMemory({
            key: `${processingType}:${Date.now()}`,
            value: `${text}\n---\n${aiResponse}`,
            timestamp: Date.now(),
            priority: 3,
            tags: memoryTags
          });
        }
      }

      return result;
    } catch (error) {
      const axiosError = error as AxiosError;
      logger.error(`Error processing text with Kindroid (${processingType}): ${axiosError.message}`);
      
      return {
        message: `Error processing text with Kindroid: ${axiosError.message}`,
        status: 500,
        success: false,
        error: axiosError.message
      };
    }
  }

  /**
   * Send a conversation to the Kindroid Discord bot endpoint
   * @param conversation Array of conversation messages
   * @param options Additional options
   * @returns Promise with AI response
   */
  async sendDiscordConversation(
    conversation: KindroidConversationMessage[],
    options: {shareCode: string, enableFilter?: boolean} = {shareCode: '', enableFilter: true}
  ): Promise<KindroidResponse> {
    try {
      if (!this.apiKey) {
        return {
          message: 'Kindroid API key not configured',
          status: 400,
          success: false,
          error: 'Configuration missing'
        };
      }

      // Create a unique identifier for the requester
      const lastUsername = conversation[conversation.length - 1]?.username || '';
      const requesterHash = this.hashUsername(lastUsername);

      const headers: Record<string, string> = {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      };

      if (requesterHash) {
        headers['X-Kindroid-Requester'] = requesterHash;
      }

      const response = await axios.post(
        `${this.baseUrl}/discord-bot`,
        {
          share_code: options.shareCode,
          enable_filter: options.enableFilter !== false,
          conversation
        },
        { headers }
      );

      // Store the conversation in memory
      this.storeConversationInMemory(conversation, response.data);

      return {
        message: 'Discord bot request successful',
        status: response.status,
        success: true,
        data: response.data
      };
    } catch (error) {
      const axiosError = error as AxiosError;
      logger.error(`Error sending Discord bot request: ${axiosError.message}`);
      
      return {
        message: `Error sending Discord bot request: ${axiosError.message}`,
        status: axiosError.response?.status || 500,
        success: false,
        error: axiosError.message
      };
    }
  }

  /**
   * Store a memory item
   * @param memory The memory item to store
   */
  async storeMemory(memory: KindroidMemoryItem): Promise<void> {
    // Store in local cache
    this.memoryCache.set(memory.key, memory);
    
    // Persist to disk if local caching is enabled
    if (this.useLocalCache) {
      this.saveMemoryCache();
    }

    // Attempt to sync with Kindroid memory servers if implemented
    try {
      this.syncMemoryWithKindroid(memory);
    } catch (error) {
      logger.error(`Failed to sync memory with Kindroid: ${error}`);
    }
  }

  /**
   * Get relevant memories based on query text and options
   * @param queryText The text to find relevant memories for
   * @param options Query options to filter memories
   * @returns Array of relevant memories
   */
  getRelevantMemories(queryText: string, options: MemoryQueryOptions = {}): KindroidMemoryItem[] {
    // Simple relevance filtering for now - could be enhanced with embeddings or more sophisticated matching
    const memories = Array.from(this.memoryCache.values());
    
    // Apply filters
    let filtered = memories;
    
    if (options.tags && options.tags.length > 0) {
      filtered = filtered.filter(m => 
        m.tags && options.tags?.some(tag => m.tags?.includes(tag))
      );
    }
    
    if (options.afterTimestamp) {
      filtered = filtered.filter(m => m.timestamp >= (options.afterTimestamp || 0));
    }
    
    if (options.beforeTimestamp) {
      filtered = filtered.filter(m => m.timestamp <= (options.beforeTimestamp || Date.now()));
    }
    
    if (options.minPriority !== undefined) {
      filtered = filtered.filter(m => m.priority >= (options.minPriority || 0));
    }
    
    // Simple relevance scoring - count word overlap
    const queryWords = new Set(queryText.toLowerCase().split(/\s+/).filter(w => w.length > 3));
    
    const scoredMemories = filtered.map(memory => {
      const memoryWords = new Set(memory.value.toLowerCase().split(/\s+/).filter(w => w.length > 3));
      let overlap = 0;
      
      queryWords.forEach(word => {
        if (memoryWords.has(word)) overlap++;
      });
      
      return {
        memory,
        score: overlap * memory.priority // Weigh by priority
      };
    });
    
    // Sort by score and limit results
    scoredMemories.sort((a, b) => b.score - a.score);
    const relevant = scoredMemories
      .filter(item => item.score > 0) // Only include actually relevant items
      .slice(0, options.limit || 5) // Limit the number of items
      .map(item => item.memory);
      
    return relevant;
  }

  /**
   * Extract potential knowledge from messages and responses and store in memory
   * @param userMessage The user's message
   * @param aiResponse The AI's response
   */
  private extractAndStoreMemories(userMessage: string, aiResponse: any): void {
    // Skip short messages that likely don't contain useful information
    if (userMessage.length < 20) return;
    
    // Extract the AI response text
    const responseText = typeof aiResponse === 'string' 
      ? aiResponse 
      : aiResponse?.response || aiResponse?.message || '';
    
    if (!responseText) return;
    
    // Store user message with moderate priority
    this.storeMemory({
      key: `user:${Date.now()}`,
      value: userMessage,
      timestamp: Date.now(),
      priority: 2,
      tags: ['user-message']
    });
    
    // Store AI response with moderate priority
    this.storeMemory({
      key: `ai:${Date.now()}`,
      value: responseText,
      timestamp: Date.now(),
      priority: 2,
      tags: ['ai-response']
    });
    
    // Extract facts or statements that might be important (very basic implementation)
    const potentialFacts = userMessage.split('.').filter(s => {
      const trimmed = s.trim();
      return trimmed.length > 30 && // Long enough to be meaningful
             !trimmed.includes('?') && // Not a question
             (
               trimmed.includes(' is ') || // Likely a statement of fact
               trimmed.includes(' are ') ||
               trimmed.includes(' was ') ||
               trimmed.includes(' were ')
             );
    });
    
    // Store each potential fact with higher priority
    potentialFacts.forEach((fact, index) => {
      this.storeMemory({
        key: `fact:${Date.now()}-${index}`,
        value: fact.trim(),
        timestamp: Date.now(),
        priority: 4, // Higher priority for potential facts
        tags: ['extracted-fact']
      });
    });
  }

  /**
   * Store conversation messages in memory
   * @param conversation The conversation messages
   * @param response The API response
   */
  private storeConversationInMemory(conversation: KindroidConversationMessage[], response: any): void {
    if (!conversation || conversation.length === 0) return;
    
    // Store the most recent user message with context
    const lastMsg = conversation[conversation.length - 1];
    if (!lastMsg) return;
    
    // Create a condensed version of the conversation for context
    const contextMessages = conversation
      .slice(Math.max(0, conversation.length - 5)) // Last 5 messages for context
      .map(msg => `${msg.username}: ${msg.text}`).join('\n');
    
    // Store with conversation tag and username
    this.storeMemory({
      key: `conv:${Date.now()}`,
      value: contextMessages,
      timestamp: Date.now(),
      priority: 3,
      tags: ['conversation', `user:${lastMsg.username}`]
    });
    
    // If there's an AI response, store it too
    if (response) {
      const responseText = typeof response === 'string' ? response : response.response || response.message || '';
      
      if (responseText) {
        this.storeMemory({
          key: `conv-response:${Date.now()}`,
          value: `${contextMessages}\n\nAI: ${responseText}`,
          timestamp: Date.now(),
          priority: 3,
          tags: ['conversation', 'ai-response']
        });
      }
    }
  }

  /**
   * Sync a memory item with Kindroid memory servers
   * @param memory The memory item to sync
   */
  private async syncMemoryWithKindroid(memory: KindroidMemoryItem): Promise<void> {
    // This is a placeholder for actual Kindroid memory server integration
    // If Kindroid provides an API for memory management, implement it here
    
    // Example implementation if an API exists:
    /*
    try {
      await axios.post(
        `${this.baseUrl}/memory`,
        {
          ai_id: this.aiId,
          memory: {
            content: memory.value,
            importance: memory.priority,
            tags: memory.tags || []
          }
        },
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );
    } catch (error) {
      logger.error(`Failed to sync memory with Kindroid: ${error}`);
    }
    */
  }

  /**
   * Save memory cache to persistent storage
   */
  private saveMemoryCache(): void {
    try {
      const data = JSON.stringify(Array.from(this.memoryCache.entries()));
      fs.writeFileSync(this.memoryPersistPath, data);
    } catch (error) {
      logger.error(`Failed to save memory cache: ${error}`);
    }
  }

  /**
   * Load memory cache from persistent storage
   */
  private loadMemoryCache(): void {
    try {
      if (fs.existsSync(this.memoryPersistPath)) {
        const data = fs.readFileSync(this.memoryPersistPath, 'utf-8');
        const entries = JSON.parse(data) as [string, KindroidMemoryItem][];
        this.memoryCache = new Map(entries);
      }
    } catch (error) {
      logger.error(`Failed to load memory cache: ${error}`);
      // Create a new empty cache if loading fails
      this.memoryCache = new Map();
    }
  }

  /**
   * Clean up old or low-priority memories
   * @param maxItems Maximum number of items to keep
   * @param maxAgeMs Maximum age of memories in milliseconds
   */
  async cleanupMemories(maxItems: number = 1000, maxAgeMs: number = 30 * 24 * 60 * 60 * 1000): Promise<number> {
    let initialCount = this.memoryCache.size;
    
    // Remove old memories
    const cutoffTime = Date.now() - maxAgeMs;
    for (const [key, memory] of this.memoryCache.entries()) {
      if (memory.timestamp < cutoffTime) {
        this.memoryCache.delete(key);
      }
    }
    
    // If still over limit, remove lowest priority items
    if (this.memoryCache.size > maxItems) {
      const memories = Array.from(this.memoryCache.entries());
      // Sort by priority (ascending) and then by timestamp (oldest first)
      memories.sort((a, b) => {
        if (a[1].priority !== b[1].priority) {
          return a[1].priority - b[1].priority;
        }
        return a[1].timestamp - b[1].timestamp;
      });
      
      // Remove excess items
      const toRemove = memories.slice(0, memories.length - maxItems);
      toRemove.forEach(item => {
        this.memoryCache.delete(item[0]);
      });
    }
    
    // Save updated cache
    if (this.useLocalCache && initialCount !== this.memoryCache.size) {
      this.saveMemoryCache();
    }
    
    return initialCount - this.memoryCache.size;
  }

  /**
   * Generate a hashed username for the X-Kindroid-Requester header
   * @param username The username to hash
   * @returns A base64 encoded hash of the username
   */
  hashUsername(username: string): string {
    const encodedUsername = encodeURIComponent(username);
    const base64Username = Buffer.from(encodedUsername).toString('base64');
    return base64Username.replace(/[^a-zA-Z0-9]/g, '').slice(0, 32);
  }

  /**
   * Check if the Kindroid API is properly configured
   * @returns Boolean indicating if the API is configured
   */
  isConfigured(): boolean {
    return Boolean(this.apiKey) && Boolean(this.aiId);
  }
  
  /**
   * Get memory statistics
   * @returns Object with memory statistics
   */
  getMemoryStats(): { total: number, byTag: Record<string, number>, byPriority: Record<number, number> } {
    const stats = {
      total: this.memoryCache.size,
      byTag: {} as Record<string, number>,
      byPriority: {} as Record<number, number>
    };
    
    // Count memories by tag and priority
    for (const memory of this.memoryCache.values()) {
      // Count by priority
      stats.byPriority[memory.priority] = (stats.byPriority[memory.priority] || 0) + 1;
      
      // Count by tag
      if (memory.tags) {
        for (const tag of memory.tags) {
          stats.byTag[tag] = (stats.byTag[tag] || 0) + 1;
        }
      }
    }
    
    return stats;
  }
}

// Export singleton instance
export const kindroidService = new KindroidService(); 