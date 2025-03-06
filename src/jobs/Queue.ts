/**
 * Job Queue System
 * 
 * A simple job queue system for running background tasks.
 */

import { EventEmitter } from 'events';
import { createLogger } from '../utils/logger';

// Initialize logger
const logger = createLogger('Queue');

/**
 * Job status enum
 */
export enum JobStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

/**
 * Job interface
 */
export interface Job {
  id: string;
  type: string;
  data: any;
  status: JobStatus;
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  error?: Error;
  result?: any;
  retryCount?: number;
}

/**
 * Job handler function type
 */
export type JobHandler = (job: Job) => Promise<any>;

/**
 * Job queue options
 */
export interface QueueOptions {
  concurrency?: number;
  retries?: number;
  retryDelay?: number;
}

/**
 * Simple in-memory job queue
 */
export class Queue extends EventEmitter {
  private jobs: Map<string, Job> = new Map();
  private handlers: Map<string, JobHandler> = new Map();
  private queue: string[] = [];
  private running: Set<string> = new Set();
  private options: QueueOptions;
  
  /**
   * Create a new job queue
   * @param options Queue options
   */
  constructor(options: QueueOptions = {}) {
    super();
    this.options = {
      concurrency: options.concurrency || 1,
      retries: options.retries || 0,
      retryDelay: options.retryDelay || 1000,
    };
    
    logger.debug(`Queue initialized with concurrency=${this.options.concurrency}, retries=${this.options.retries}`);
  }
  
  /**
   * Register a job handler
   * @param jobType Job type
   * @param handler Handler function
   */
  public register(jobType: string, handler: JobHandler): void {
    this.handlers.set(jobType, handler);
    logger.debug(`Registered handler for job type: ${jobType}`);
  }
  
  /**
   * Create a new job
   * @param jobType Job type
   * @param data Job data
   * @returns Job ID
   */
  public async createJob(jobType: string, data: any): Promise<string> {
    // Check if handler exists
    if (!this.handlers.has(jobType)) {
      throw new Error(`No handler registered for job type: ${jobType}`);
    }
    
    // Create a job ID
    const id = `${jobType}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    // Create the job
    const job: Job = {
      id,
      type: jobType,
      data,
      status: JobStatus.PENDING,
      createdAt: new Date(),
      retryCount: 0,
    };
    
    // Store the job
    this.jobs.set(id, job);
    
    // Add to queue
    this.queue.push(id);
    
    logger.debug(`Created job ${id} of type ${jobType}`);
    this.emit('job:created', job);
    
    // Start processing if not already
    setImmediate(() => this.processQueue());
    
    return id;
  }
  
  /**
   * Get a job by ID
   * @param id Job ID
   * @returns Job or undefined if not found
   */
  public getJob(id: string): Job | undefined {
    return this.jobs.get(id);
  }
  
  /**
   * Process the queue
   */
  private async processQueue(): Promise<void> {
    // Check if we can process more jobs
    if (this.running.size >= this.options.concurrency!) {
      return;
    }
    
    // Get next job
    const id = this.queue.shift();
    if (!id) {
      return;
    }
    
    // Get the job
    const job = this.jobs.get(id);
    if (!job) {
      logger.warn(`Job ${id} not found in queue`);
      return;
    }
    
    // Mark as running
    job.status = JobStatus.RUNNING;
    job.startedAt = new Date();
    this.running.add(id);
    
    logger.debug(`Starting job ${id} of type ${job.type}`);
    this.emit('job:started', job);
    
    try {
      // Get the handler
      const handler = this.handlers.get(job.type);
      if (!handler) {
        throw new Error(`No handler for job type: ${job.type}`);
      }
      
      // Run the handler
      const result = await handler(job);
      
      // Update job
      job.status = JobStatus.COMPLETED;
      job.completedAt = new Date();
      job.result = result;
      
      logger.debug(`Completed job ${id} of type ${job.type}`);
      this.emit('job:completed', job);
    } catch (error) {
      // Handle error
      job.status = JobStatus.FAILED;
      job.error = error as Error;
      
      logger.error(`Job ${id} failed: ${error}`);
      this.emit('job:failed', job, error);
      
      // Initialize retry count if needed
      if (job.retryCount === undefined) {
        job.retryCount = 0;
      }
      
      // Retry if configured
      if (job.retryCount < this.options.retries!) {
        job.retryCount++;
        job.status = JobStatus.PENDING;
        
        logger.debug(`Retrying job ${id} (${job.retryCount}/${this.options.retries})`);
        
        // Add back to queue after delay
        setTimeout(() => {
          this.queue.push(id);
          this.emit('job:retrying', job);
          this.processQueue();
        }, this.options.retryDelay!);
      }
    } finally {
      // Remove from running
      this.running.delete(id);
      
      // Process more jobs
      setImmediate(() => this.processQueue());
    }
  }
  
  /**
   * Get all jobs
   * @returns Array of all jobs
   */
  public getAllJobs(): Job[] {
    return Array.from(this.jobs.values());
  }
  
  /**
   * Get jobs by status
   * @param status Job status
   * @returns Array of jobs with the given status
   */
  public getJobsByStatus(status: JobStatus): Job[] {
    return Array.from(this.jobs.values()).filter(job => job.status === status);
  }
  
  /**
   * Get jobs by type
   * @param type Job type
   * @returns Array of jobs with the given type
   */
  public getJobsByType(type: string): Job[] {
    return Array.from(this.jobs.values()).filter(job => job.type === type);
  }
  
  /**
   * Clear completed and failed jobs
   * @returns Number of jobs cleared
   */
  public clearCompletedJobs(): number {
    let count = 0;
    
    for (const [id, job] of this.jobs.entries()) {
      if (job.status === JobStatus.COMPLETED || job.status === JobStatus.FAILED) {
        this.jobs.delete(id);
        count++;
      }
    }
    
    logger.debug(`Cleared ${count} completed/failed jobs`);
    return count;
  }
}