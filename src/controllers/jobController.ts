/**
 * Job Controller
 * 
 * Manages background jobs and provides an API for job monitoring.
 */

import { Request, Response } from 'express';
import { Queue, JobStatus, Job } from '../jobs/Queue';
import { createLogger } from '../utils/logger';

// Initialize logger
const logger = createLogger('JobController');

// Create a global queue instance
export const jobQueue = new Queue({
  concurrency: 3,
  retries: 2,
  retryDelay: 5000,
});

/**
 * Job controller for handling job-related requests
 */
export class JobController {
  constructor() {
    // Bind methods to this instance
    this.getAllJobs = this.getAllJobs.bind(this);
    this.getJobById = this.getJobById.bind(this);
    this.getJobsByStatus = this.getJobsByStatus.bind(this);
    this.clearCompletedJobs = this.clearCompletedJobs.bind(this);
    this.createBatchProcessingJob = this.createBatchProcessingJob.bind(this);
    
    // Register job handlers
    this.registerJobHandlers();
    
    logger.info('Job controller initialized');
  }
  
  /**
   * Register job handlers
   */
  private registerJobHandlers(): void {
    // Register data processing job handler
    jobQueue.register('data-processing', async (job: Job) => {
      logger.info(`Processing data job ${job.id}`);
      
      // Simulate processing time
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Process data (example)
      const { items } = job.data;
      const results = items.map((item: any) => ({
        id: item.id,
        processed: true,
        timestamp: new Date(),
      }));
      
      logger.info(`Completed data processing job ${job.id} with ${results.length} items`);
      return { processed: results.length, results };
    });
    
    // Register export job handler
    jobQueue.register('export', async (job: Job) => {
      logger.info(`Processing export job ${job.id}`);
      
      // Simulate export time
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Export data (example)
      const { format, items } = job.data;
      const exportedData = {
        format,
        timestamp: new Date(),
        count: items.length,
        data: items,
      };
      
      logger.info(`Completed export job ${job.id} in ${format} format`);
      return exportedData;
    });
    
    // Register notification job handler
    jobQueue.register('notification', async (job: Job) => {
      logger.info(`Processing notification job ${job.id}`);
      
      // Simulate notification sending
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Send notification (example)
      const { to, subject, message } = job.data;
      const notificationResult = {
        sent: true,
        to,
        subject,
        timestamp: new Date(),
      };
      
      logger.info(`Sent notification to ${to}`);
      return notificationResult;
    });
  }
  
  /**
   * Get all jobs
   * @param req Request
   * @param res Response
   */
  public getAllJobs(req: Request, res: Response): void {
    const jobs = jobQueue.getAllJobs();
    
    // Filter out sensitive data
    const safeJobs = jobs.map(this.sanitizeJob);
    
    res.status(200).json({
      success: true,
      count: safeJobs.length,
      jobs: safeJobs,
    });
  }
  
  /**
   * Get a job by ID
   * @param req Request
   * @param res Response
   */
  public getJobById(req: Request, res: Response): void {
    const { id } = req.params;
    const job = jobQueue.getJob(id);
    
    if (!job) {
      res.status(404).json({
        success: false,
        message: `Job not found: ${id}`,
      });
      return;
    }
    
    res.status(200).json({
      success: true,
      job: this.sanitizeJob(job),
    });
  }
  
  /**
   * Get jobs by status
   * @param req Request
   * @param res Response
   */
  public getJobsByStatus(req: Request, res: Response): void {
    const { status } = req.params;
    
    // Validate status
    if (!Object.values(JobStatus).includes(status as JobStatus)) {
      res.status(400).json({
        success: false,
        message: `Invalid status: ${status}`,
      });
      return;
    }
    
    const jobs = jobQueue.getJobsByStatus(status as JobStatus);
    
    // Filter out sensitive data
    const safeJobs = jobs.map(this.sanitizeJob);
    
    res.status(200).json({
      success: true,
      count: safeJobs.length,
      jobs: safeJobs,
    });
  }
  
  /**
   * Clear completed jobs
   * @param req Request
   * @param res Response
   */
  public clearCompletedJobs(req: Request, res: Response): void {
    const count = jobQueue.clearCompletedJobs();
    
    res.status(200).json({
      success: true,
      message: `Cleared ${count} completed jobs`,
      count,
    });
  }
  
  /**
   * Create a batch processing job
   * @param req Request
   * @param res Response
   */
  public async createBatchProcessingJob(req: Request, res: Response): Promise<void> {
    const { items } = req.body;
    
    try {
      // Create a new job
      const jobId = await jobQueue.createJob('data-processing', { items });
      
      res.status(201).json({
        success: true,
        message: 'Batch processing job created',
        jobId,
      });
    } catch (error) {
      logger.error(`Error creating job: ${error}`);
      
      res.status(500).json({
        success: false,
        message: 'Failed to create job',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Create an export job
   * @param req Request
   * @param res Response
   */
  public async createExportJob(req: Request, res: Response): Promise<void> {
    const { format, items } = req.body;
    
    try {
      // Create a new job
      const jobId = await jobQueue.createJob('export', { format, items });
      
      res.status(201).json({
        success: true,
        message: 'Export job created',
        jobId,
      });
    } catch (error) {
      logger.error(`Error creating export job: ${error}`);
      
      res.status(500).json({
        success: false,
        message: 'Failed to create export job',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Create a notification job
   * @param req Request
   * @param res Response
   */
  public async createNotificationJob(req: Request, res: Response): Promise<void> {
    const { to, subject, message } = req.body;
    
    try {
      // Create a new job
      const jobId = await jobQueue.createJob('notification', { to, subject, message });
      
      res.status(201).json({
        success: true,
        message: 'Notification job created',
        jobId,
      });
    } catch (error) {
      logger.error(`Error creating notification job: ${error}`);
      
      res.status(500).json({
        success: false,
        message: 'Failed to create notification job',
        error: (error as Error).message,
      });
    }
  }
  
  /**
   * Sanitize job for API response (remove sensitive data)
   * @param job Job to sanitize
   * @returns Sanitized job
   */
  private sanitizeJob(job: Job): Partial<Job> {
    const { id, type, status, createdAt, startedAt, completedAt, result, retryCount } = job;
    
    // Only include error message, not the full error object
    const errorMessage = job.error ? job.error.message : undefined;
    
    return {
      id,
      type,
      status,
      createdAt,
      startedAt,
      completedAt,
      result,
      error: job.error,  // Return the full error object as defined in the Job interface
      retryCount,
    };
  }
} 