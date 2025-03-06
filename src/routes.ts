import { Express, Request, Response } from 'express';
import { DataController } from './controllers/dataController';
import { TextProcessingController } from './controllers/textProcessingController';
import { MemoryController } from './controllers/memoryController';
import { AuthController } from './controllers/authController';
import { validate, validators } from './middleware/validation';
import { authenticate, authorize } from './middleware/auth';
import { JobController, jobQueue } from './controllers/jobController';
import { jobValidators } from './middleware/jobValidation';
import { GistController } from './controllers/gistController';
import { gistValidators } from './middleware/gistValidation';
import { gistWebhook } from './webhooks/GistWebhook';
import { config } from './utils/env';
import { createLogger } from './utils/logger';
import { MemoryFactory } from './services/MemoryFactory';
import { authLimiter, heavyOperationLimiter, webhookLimiter } from './middleware/rateLimiter';

// Import controllers
const dataController = new DataController();
const textProcessingController = new TextProcessingController();
const memoryController = new MemoryController();
const authController = new AuthController();
const jobController = new JobController();
const gistController = new GistController();

// Initialize logger
const logger = createLogger('Routes');

// Configure all application routes
export function configureRoutes(app: Express): void {
  /**
   * @swagger
   * /:
   *   get:
   *     summary: Welcome message
   *     description: Returns a welcome message for the API
   *     responses:
   *       200:
   *         description: Successfully returns a welcome message
   *         content:
   *           text/plain:
   *             schema:
   *               type: string
   *               example: Welcome to my project!
   */
  // Home route
  app.get('/', (req: Request, res: Response) => {
    res.send('Welcome to my project!');
  });

  /**
   * @swagger
   * /api:
   *   get:
   *     summary: API information
   *     description: Returns information about available API endpoints
   *     responses:
   *       200:
   *         description: Successfully returns API information
   *         content:
   *           application/json:
   *             schema:
   *               type: object
   */
  // API summary route
  app.get('/api', (req: Request, res: Response) => {
    res.json({
      name: 'My Project API',
      version: '1.0.0',
      endpoints: {
        auth: {
          base: '/auth',
          methods: {
            'POST /auth/login': 'Authenticate a user',
            'POST /auth/register': 'Register a new user',
            'POST /auth/validate': 'Validate a token',
            'GET /auth/profile': 'Get current user profile (requires authentication)'
          }
        },
        data: {
          base: '/data',
          methods: {
            'GET /data': 'Get all data items',
            'POST /data': 'Create a new data item',
            'GET /data/:id': 'Get a specific data item by ID',
            'PUT /data/:id': 'Update a specific data item',
            'DELETE /data/:id': 'Delete a specific data item'
          }
        },
        text: {
          base: '/text',
          methods: {
            'POST /text/sentiment': 'Analyze sentiment of provided text',
            'POST /text/translate': 'Translate text between languages',
            'POST /text/summarize': 'Generate a summary of provided text'
          }
        },
        memory: {
          base: '/memory',
          methods: {
            'GET /memory/:namespace/items': 'List all items in a namespace',
            'GET /memory/:namespace/items/:key': 'Get a specific item',
            'POST /memory/:namespace/items': 'Store an item',
            'DELETE /memory/:namespace/items/:key': 'Delete a specific item',
            'DELETE /memory/:namespace': 'Clear a namespace'
          }
        }
      }
    });
  });

  /**
   * @swagger
   * /auth/register:
   *   post:
   *     summary: Register a new user
   *     description: Create a new user account
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             required:
   *               - username
   *               - email
   *               - password
   *             properties:
   *               username:
   *                 type: string
   *                 description: User's unique username
   *               email:
   *                 type: string
   *                 format: email
   *                 description: User's email address
   *               password:
   *                 type: string
   *                 format: password
   *                 description: User's password
   *     responses:
   *       201:
   *         description: Successfully registered
   *       409:
   *         description: Username already exists
   *       400:
   *         description: Invalid input
   */
  app.post('/auth/register', authLimiter, validate(validators.auth.register), authController.register);
  
  /**
   * @swagger
   * /auth/login:
   *   post:
   *     summary: Login
   *     description: Authenticate a user
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             required:
   *               - username
   *               - password
   *             properties:
   *               username:
   *                 type: string
   *                 description: User's username
   *               password:
   *                 type: string
   *                 format: password
   *                 description: User's password
   *     responses:
   *       200:
   *         description: Successfully authenticated
   *       401:
   *         description: Invalid credentials
   */
  app.post('/auth/login', authLimiter, validate(validators.auth.login), authController.login);
  
  /**
   * @swagger
   * /auth/validate:
   *   post:
   *     summary: Validate token
   *     description: Validate a JWT token
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             required:
   *               - token
   *             properties:
   *               token:
   *                 type: string
   *                 description: JWT token to validate
   *     responses:
   *       200:
   *         description: Token is valid
   *       401:
   *         description: Invalid or expired token
   */
  app.post('/auth/validate', validate(validators.auth.validate), authController.validateToken);
  
  /**
   * @swagger
   * /auth/profile:
   *   get:
   *     summary: Get user profile
   *     description: Get current user profile (requires authentication)
   *     security:
   *       - bearerAuth: []
   *     responses:
   *       200:
   *         description: User profile
   *       401:
   *         description: Not authenticated
   */
  app.get('/auth/profile', authenticate, authController.getProfile);

  /**
   * @swagger
   * /data:
   *   post:
   *     summary: Create a new data item
   *     description: Create a new data item with the provided data
   *     security:
   *       - bearerAuth: []
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             required:
   *               - name
   *             properties:
   *               name:
   *                 type: string
   *                 description: Name of the item
   *               description:
   *                 type: string
   *                 description: Description of the item
   *     responses:
   *       201:
   *         description: Successfully created data item
   *       400:
   *         description: Invalid input
   *       401:
   *         description: Not authenticated
   */
  // Data routes (now with authentication)
  app.post('/data', authenticate, validate(validators.data.create), dataController.createItem);
  app.get('/data', validate(validators.data.getAll), dataController.getAllItems);
  
  /**
   * @swagger
   * /data/{id}:
   *   get:
   *     summary: Get a data item by ID
   *     description: Retrieve a single data item by its ID
   *     parameters:
   *       - in: path
   *         name: id
   *         required: true
   *         schema:
   *           type: string
   *         description: ID of the data item
   *     responses:
   *       200:
   *         description: A single data item
   *       404:
   *         description: Data item not found
   *   put:
   *     summary: Update a data item
   *     description: Update an existing data item by its ID
   *     security:
   *       - bearerAuth: []
   *     parameters:
   *       - in: path
   *         name: id
   *         required: true
   *         schema:
   *           type: string
   *         description: ID of the data item
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             properties:
   *               name:
   *                 type: string
   *                 description: Updated name
   *               description:
   *                 type: string
   *                 description: Updated description
   *     responses:
   *       200:
   *         description: Successfully updated data item
   *       404:
   *         description: Data item not found
   *       401:
   *         description: Not authenticated
   *   delete:
   *     summary: Delete a data item
   *     description: Delete a data item by its ID
   *     security:
   *       - bearerAuth: []
   *     parameters:
   *       - in: path
   *         name: id
   *         required: true
   *         schema:
   *           type: string
   *         description: ID of the data item
   *     responses:
   *       204:
   *         description: Successfully deleted data item
   *       404:
   *         description: Data item not found
   *       401:
   *         description: Not authenticated
   */
  app.get('/data/:id', validate(validators.data.getById), dataController.getItemById);
  app.put('/data/:id', authenticate, validate(validators.data.update), dataController.updateItem);
  app.delete('/data/:id', authenticate, validate(validators.data.getById), dataController.deleteItem);

  /**
   * @swagger
   * /text/sentiment:
   *   post:
   *     summary: Analyze sentiment
   *     description: Analyze the sentiment of the provided text
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             required:
   *               - text
   *             properties:
   *               text:
   *                 type: string
   *                 description: The text to analyze
   *     responses:
   *       200:
   *         description: Sentiment analysis result
   *       400:
   *         description: Invalid input
   */
  // Text processing routes
  app.post('/text/sentiment', heavyOperationLimiter, validate(validators.text.sentiment), textProcessingController.analyzeSentiment);
  
  /**
   * @swagger
   * /text/translate:
   *   post:
   *     summary: Translate text
   *     description: Translate text from one language to another
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             required:
   *               - text
   *               - sourceLang
   *               - targetLang
   *             properties:
   *               text:
   *                 type: string
   *                 description: The text to translate
   *               sourceLang:
   *                 type: string
   *                 description: Source language code
   *               targetLang:
   *                 type: string
   *                 description: Target language code
   *     responses:
   *       200:
   *         description: Translation result
   *       400:
   *         description: Invalid input
   */
  app.post('/text/translate', heavyOperationLimiter, validate(validators.text.translate), textProcessingController.translateText);
  
  /**
   * @swagger
   * /text/summarize:
   *   post:
   *     summary: Summarize text
   *     description: Generate a summary of the provided text
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             required:
   *               - text
   *             properties:
   *               text:
   *                 type: string
   *                 description: The text to summarize
   *               maxLength:
   *                 type: integer
   *                 description: Maximum number of sentences in the summary
   *     responses:
   *       200:
   *         description: Summary result
   *       400:
   *         description: Invalid input
   */
  app.post('/text/summarize', heavyOperationLimiter, validate(validators.text.summarize), textProcessingController.summarizeText);

  /**
   * @swagger
   * /memory/{namespace}/items:
   *   get:
   *     summary: List memory items
   *     description: List all keys in a namespace
   *     security:
   *       - bearerAuth: []
   *     parameters:
   *       - in: path
   *         name: namespace
   *         required: true
   *         schema:
   *           type: string
   *         description: Memory namespace
   *       - in: query
   *         name: type
   *         schema:
   *           type: string
   *           enum: [short-term, long-term]
   *         description: Memory type
   *     responses:
   *       200:
   *         description: Successfully retrieved memory items
   *       400:
   *         description: Invalid input
   *       401:
   *         description: Not authenticated
   */
  // Memory routes with authentication for write operations
  app.get('/memory/:namespace/items', authenticate, validate(validators.memory.listItems), memoryController.listItems);
  
  /**
   * @swagger
   * /memory/{namespace}/items/{key}:
   *   get:
   *     summary: Get memory item
   *     description: Get a specific item from memory
   *     security:
   *       - bearerAuth: []
   *     parameters:
   *       - in: path
   *         name: namespace
   *         required: true
   *         schema:
   *           type: string
   *         description: Memory namespace
   *       - in: path
   *         name: key
   *         required: true
   *         schema:
   *           type: string
   *         description: Item key
   *       - in: query
   *         name: type
   *         schema:
   *           type: string
   *           enum: [short-term, long-term]
   *         description: Memory type
   *     responses:
   *       200:
   *         description: Successfully retrieved memory item
   *       404:
   *         description: Item not found
   *       400:
   *         description: Invalid input
   *       401:
   *         description: Not authenticated
   */
  app.get('/memory/:namespace/items/:key', authenticate, validate(validators.memory.getItem), memoryController.getItem);
  
  /**
   * @swagger
   * /memory/{namespace}/items/{key}:
   *   delete:
   *     summary: Delete memory item
   *     description: Delete a specific item from memory
   *     security:
   *       - bearerAuth: []
   *     parameters:
   *       - in: path
   *         name: namespace
   *         required: true
   *         schema:
   *           type: string
   *         description: Memory namespace
   *       - in: path
   *         name: key
   *         required: true
   *         schema:
   *           type: string
   *         description: Item key
   *       - in: query
   *         name: type
   *         schema:
   *           type: string
   *           enum: [short-term, long-term]
   *         description: Memory type
   *     responses:
   *       204:
   *         description: Successfully deleted memory item
   *       404:
   *         description: Item not found
   *       400:
   *         description: Invalid input
   *       401:
   *         description: Not authenticated
   */
  app.delete('/memory/:namespace/items/:key', authenticate, validate(validators.memory.getItem), memoryController.deleteItem);
  
  /**
   * @swagger
   * /memory/{namespace}/items:
   *   post:
   *     summary: Set memory item
   *     description: Store an item in memory
   *     security:
   *       - bearerAuth: []
   *     parameters:
   *       - in: path
   *         name: namespace
   *         required: true
   *         schema:
   *           type: string
   *         description: Memory namespace
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             required:
   *               - key
   *               - value
   *             properties:
   *               key:
   *                 type: string
   *                 description: Item key
   *               value:
   *                 type: object
   *                 description: Item value
   *               ttl:
   *                 type: integer
   *                 description: Time to live in seconds
   *               type:
   *                 type: string
   *                 enum: [short-term, long-term]
   *                 description: Memory type
   *     responses:
   *       201:
   *         description: Successfully stored memory item
   *       400:
   *         description: Invalid input
   *       401:
   *         description: Not authenticated
   */
  app.post('/memory/:namespace/items', authenticate, validate(validators.memory.setItem), memoryController.setItem);
  
  /**
   * @swagger
   * /memory/{namespace}:
   *   delete:
   *     summary: Clear memory namespace
   *     description: Delete all items in a namespace
   *     security:
   *       - bearerAuth: []
   *     parameters:
   *       - in: path
   *         name: namespace
   *         required: true
   *         schema:
   *           type: string
   *         description: Memory namespace
   *     requestBody:
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             properties:
   *               type:
   *                 type: string
   *                 enum: [short-term, long-term]
   *                 description: Memory type
   *     responses:
   *       204:
   *         description: Successfully cleared memory namespace
   *       400:
   *         description: Invalid input
   *       401:
   *         description: Not authenticated
   */
  app.delete('/memory/:namespace', authenticate, validate(validators.memory.clearNamespace), memoryController.clearNamespace);

  /**
   * @swagger
   * /jobs:
   *   get:
   *     summary: Get all jobs
   *     tags: [Jobs]
   *     responses:
   *       200:
   *         description: List of all jobs
   *         content:
   *           application/json:
   *             schema:
   *               type: object
   *               properties:
   *                 success:
   *                   type: boolean
   *                 count:
   *                   type: integer
   *                 jobs:
   *                   type: array
   *                   items:
   *                     $ref: '#/components/schemas/Job'
   */
  app.get('/jobs', jobController.getAllJobs);
  
  /**
   * @swagger
   * /jobs/{id}:
   *   get:
   *     summary: Get job by ID
   *     tags: [Jobs]
   *     parameters:
   *       - in: path
   *         name: id
   *         required: true
   *         schema:
   *           type: string
   *     responses:
   *       200:
   *         description: Job details
   *         content:
   *           application/json:
   *             schema:
   *               type: object
   *               properties:
   *                 success:
   *                   type: boolean
   *                 job:
   *                   $ref: '#/components/schemas/Job'
   *       404:
   *         description: Job not found
   */
  app.get('/jobs/:id', validate(jobValidators.getJobById), jobController.getJobById);
  
  /**
   * @swagger
   * /jobs/status/{status}:
   *   get:
   *     summary: Get jobs by status
   *     tags: [Jobs]
   *     parameters:
   *       - in: path
   *         name: status
   *         required: true
   *         schema:
   *           type: string
   *           enum: [PENDING, RUNNING, COMPLETED, FAILED]
   *     responses:
   *       200:
   *         description: List of jobs with the specified status
   *         content:
   *           application/json:
   *             schema:
   *               type: object
   *               properties:
   *                 success:
   *                   type: boolean
   *                 count:
   *                   type: integer
   *                 jobs:
   *                   type: array
   *                   items:
   *                     $ref: '#/components/schemas/Job'
   *       400:
   *         description: Invalid status
   */
  app.get('/jobs/status/:status', validate(jobValidators.getJobsByStatus), jobController.getJobsByStatus);
  
  /**
   * @swagger
   * /jobs/completed:
   *   delete:
   *     summary: Clear completed jobs
   *     tags: [Jobs]
   *     responses:
   *       200:
   *         description: Completed jobs cleared
   *         content:
   *           application/json:
   *             schema:
   *               type: object
   *               properties:
   *                 success:
   *                   type: boolean
   *                 message:
   *                   type: string
   *                 count:
   *                   type: integer
   */
  app.delete('/jobs/completed', validate(jobValidators.clearCompletedJobs), jobController.clearCompletedJobs);
  
  /**
   * @swagger
   * /jobs/batch:
   *   post:
   *     summary: Create a batch processing job
   *     tags: [Jobs]
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             properties:
   *               items:
   *                 type: array
   *                 items:
   *                   type: object
   *             required:
   *               - items
   *     responses:
   *       201:
   *         description: Batch processing job created
   *         content:
   *           application/json:
   *             schema:
   *               type: object
   *               properties:
   *                 success:
   *                   type: boolean
   *                 message:
   *                   type: string
   *                 jobId:
   *                   type: string
   *       400:
   *         description: Invalid request
   *       500:
   *         description: Server error
   */
  app.post('/jobs/batch', validate(jobValidators.createBatchProcessingJob), jobController.createBatchProcessingJob);
  
  /**
   * @swagger
   * /jobs/export:
   *   post:
   *     summary: Create an export job
   *     tags: [Jobs]
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             properties:
   *               format:
   *                 type: string
   *                 enum: [json, csv, xml, txt]
   *               items:
   *                 type: array
   *                 items:
   *                   type: object
   *             required:
   *               - format
   *               - items
   *     responses:
   *       201:
   *         description: Export job created
   *         content:
   *           application/json:
   *             schema:
   *               type: object
   *               properties:
   *                 success:
   *                   type: boolean
   *                 message:
   *                   type: string
   *                 jobId:
   *                   type: string
   *       400:
   *         description: Invalid request
   *       500:
   *         description: Server error
   */
  app.post('/jobs/export', validate(jobValidators.createExportJob), jobController.createExportJob);
  
  /**
   * @swagger
   * /jobs/notification:
   *   post:
   *     summary: Create a notification job
   *     tags: [Jobs]
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             properties:
   *               to:
   *                 type: string
   *                 format: email
   *               subject:
   *                 type: string
   *                 maxLength: 100
   *               message:
   *                 type: string
   *             required:
   *               - to
   *               - subject
   *               - message
   *     responses:
   *       201:
   *         description: Notification job created
   *         content:
   *           application/json:
   *             schema:
   *               type: object
   *               properties:
   *                 success:
   *                   type: boolean
   *                 message:
   *                   type: string
   *                 jobId:
   *                   type: string
   *       400:
   *         description: Invalid request
   *       500:
   *         description: Server error
   */
  app.post('/jobs/notification', validate(jobValidators.createNotificationJob), jobController.createNotificationJob);

  // Gist API routes
  /**
   * @swagger
   * /gists:
   *   get:
   *     summary: Get all gists for authenticated user
   *     tags: [Gists]
   *     security:
   *       - bearerAuth: []
   *     parameters:
   *       - in: query
   *         name: page
   *         schema:
   *           type: integer
   *         description: Page number
   *       - in: query
   *         name: perPage
   *         schema:
   *           type: integer
   *         description: Number of gists per page
   *     responses:
   *       200:
   *         description: List of gists
   *       401:
   *         description: Unauthorized
   *       500:
   *         description: Server error
   */
  app.get('/gists', authenticate, validate(gistValidators.getGists), gistController.getGists);
  
  /**
   * @swagger
   * /gists/user/{username}:
   *   get:
   *     summary: Get all public gists for a specific user
   *     tags: [Gists]
   *     parameters:
   *       - in: path
   *         name: username
   *         required: true
   *         schema:
   *           type: string
   *       - in: query
   *         name: page
   *         schema:
   *           type: integer
   *         description: Page number
   *       - in: query
   *         name: perPage
   *         schema:
   *           type: integer
   *         description: Number of gists per page
   *     responses:
   *       200:
   *         description: List of gists
   *       500:
   *         description: Server error
   */
  app.get('/gists/user/:username', validate(gistValidators.getUserGists), gistController.getUserGists);
  
  /**
   * @swagger
   * /gists/{id}:
   *   get:
   *     summary: Get a specific gist by ID
   *     tags: [Gists]
   *     parameters:
   *       - in: path
   *         name: id
   *         required: true
   *         schema:
   *           type: string
   *     responses:
   *       200:
   *         description: Gist details
   *       404:
   *         description: Gist not found
   *       500:
   *         description: Server error
   */
  app.get('/gists/:id', validate(gistValidators.getGist), gistController.getGist);
  
  /**
   * @swagger
   * /gists:
   *   post:
   *     summary: Create a new gist
   *     tags: [Gists]
   *     security:
   *       - bearerAuth: []
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             properties:
   *               description:
   *                 type: string
   *               public:
   *                 type: boolean
   *               files:
   *                 type: object
   *                 additionalProperties:
   *                   type: object
   *                   properties:
   *                     content:
   *                       type: string
   *             required:
   *               - files
   *     responses:
   *       201:
   *         description: Gist created
   *       400:
   *         description: Invalid request
   *       401:
   *         description: Unauthorized
   *       500:
   *         description: Server error
   */
  app.post('/gists', authenticate, validate(gistValidators.createGist), gistController.createGist);
  
  /**
   * @swagger
   * /gists/{id}:
   *   patch:
   *     summary: Update an existing gist
   *     tags: [Gists]
   *     security:
   *       - bearerAuth: []
   *     parameters:
   *       - in: path
   *         name: id
   *         required: true
   *         schema:
   *           type: string
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             properties:
   *               description:
   *                 type: string
   *               files:
   *                 type: object
   *                 additionalProperties:
   *                   oneOf:
   *                     - type: object
   *                       properties:
   *                         content:
   *                           type: string
   *                     - type: 'null'
   *     responses:
   *       200:
   *         description: Gist updated
   *       400:
   *         description: Invalid request
   *       401:
   *         description: Unauthorized
   *       404:
   *         description: Gist not found
   *       500:
   *         description: Server error
   */
  app.patch('/gists/:id', authenticate, validate(gistValidators.updateGist), gistController.updateGist);
  
  /**
   * @swagger
   * /gists/{id}:
   *   delete:
   *     summary: Delete a gist
   *     tags: [Gists]
   *     security:
   *       - bearerAuth: []
   *     parameters:
   *       - in: path
   *         name: id
   *         required: true
   *         schema:
   *           type: string
   *     responses:
   *       200:
   *         description: Gist deleted
   *       401:
   *         description: Unauthorized
   *       404:
   *         description: Gist not found
   *       500:
   *         description: Server error
   */
  app.delete('/gists/:id', authenticate, validate(gistValidators.deleteGist), gistController.deleteGist);
  
  /**
   * @swagger
   * /gists/{id}/star:
   *   put:
   *     summary: Star a gist
   *     tags: [Gists]
   *     security:
   *       - bearerAuth: []
   *     parameters:
   *       - in: path
   *         name: id
   *         required: true
   *         schema:
   *           type: string
   *     responses:
   *       200:
   *         description: Gist starred
   *       401:
   *         description: Unauthorized
   *       404:
   *         description: Gist not found
   *       500:
   *         description: Server error
   */
  app.put('/gists/:id/star', authenticate, validate(gistValidators.starGist), gistController.starGist);
  
  /**
   * @swagger
   * /gists/{id}/star:
   *   delete:
   *     summary: Unstar a gist
   *     tags: [Gists]
   *     security:
   *       - bearerAuth: []
   *     parameters:
   *       - in: path
   *         name: id
   *         required: true
   *         schema:
   *           type: string
   *     responses:
   *       200:
   *         description: Gist unstarred
   *       401:
   *         description: Unauthorized
   *       404:
   *         description: Gist not found
   *       500:
   *         description: Server error
   */
  app.delete('/gists/:id/star', authenticate, validate(gistValidators.starGist), gistController.unstarGist);
  
  /**
   * @swagger
   * /gists/{id}/starred:
   *   get:
   *     summary: Check if a gist is starred
   *     tags: [Gists]
   *     security:
   *       - bearerAuth: []
   *     parameters:
   *       - in: path
   *         name: id
   *         required: true
   *         schema:
   *           type: string
   *     responses:
   *       200:
   *         description: Starred status
   *         content:
   *           application/json:
   *             schema:
   *               type: object
   *               properties:
   *                 success:
   *                   type: boolean
   *                 isStarred:
   *                   type: boolean
   *       401:
   *         description: Unauthorized
   *       404:
   *         description: Gist not found
   *       500:
   *         description: Server error
   */
  app.get('/gists/:id/starred', authenticate, validate(gistValidators.starGist), gistController.checkIsStarred);
  
  /**
   * @swagger
   * /gists/{id}/fork:
   *   post:
   *     summary: Fork a gist
   *     tags: [Gists]
   *     security:
   *       - bearerAuth: []
   *     parameters:
   *       - in: path
   *         name: id
   *         required: true
   *         schema:
   *           type: string
   *     responses:
   *       201:
   *         description: Gist forked
   *       401:
   *         description: Unauthorized
   *       404:
   *         description: Gist not found
   *       500:
   *         description: Server error
   */
  app.post('/gists/:id/fork', authenticate, validate(gistValidators.forkGist), gistController.forkGist);

  /**
   * @swagger
   * /webhooks/github/gist:
   *   post:
   *     summary: GitHub Gist webhook endpoint
   *     tags: [Webhooks]
   *     description: >
   *       Endpoint for GitHub webhook events related to Gists.
   *       This endpoint is used to receive notifications when Gists are created, updated, or deleted.
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *     responses:
   *       200:
   *         description: Webhook processed successfully
   *       403:
   *         description: Invalid webhook signature
   *       500:
   *         description: Server error
   */
  if (config.webhooks.enabled) {
    app.post('/webhooks/github/gist', webhookLimiter, gistWebhook.handleWebhook);
    
    // Example webhook event handlers
    gistWebhook.onGistCreated((payload) => {
      console.log(`Webhook: Gist created - ${payload.gist.id} by ${payload.sender.login}`);
    });
    
    gistWebhook.onGistUpdated((payload) => {
      console.log(`Webhook: Gist updated - ${payload.gist.id} by ${payload.sender.login}`);
    });
    
    gistWebhook.onGistDeleted((payload) => {
      console.log(`Webhook: Gist deleted - ${payload.gist.id} by ${payload.sender.login}`);
    });
  }

  /**
   * @swagger
   * /health:
   *   get:
   *     summary: Health check endpoint
   *     description: Returns the health status of the application and its dependencies
   *     tags: [System]
   *     responses:
   *       200:
   *         description: Application is healthy
   *         content:
   *           application/json:
   *             schema:
   *               type: object
   *               properties:
   *                 status:
   *                   type: string
   *                   example: "ok"
   *                 version:
   *                   type: string
   *                   example: "1.0.0"
   *                 uptime:
   *                   type: number
   *                   example: 3600
   *                 dependencies:
   *                   type: object
   *                   properties:
   *                     redis:
   *                       type: string
   *                       example: "connected"
   *                     database:
   *                       type: string
   *                       example: "connected"
   *       503:
   *         description: Application is unhealthy
   *         content:
   *           application/json:
   *             schema:
   *               type: object
   *               properties:
   *                 status:
   *                   type: string
   *                   example: "error"
   *                 message:
   *                   type: string
   *                   example: "One or more dependencies unavailable"
   *                 dependencies:
   *                   type: object
   *                   properties:
   *                     redis:
   *                       type: string
   *                       example: "disconnected"
   */
  app.get('/health', async (req: Request, res: Response) => {
    try {
      // Check Redis connection if configured
      let redisStatus = 'not_configured';
      if (config.redis && config.redis.host) {
        try {
          const longTermMemory = await MemoryFactory.getLongTermMemory('health-check');
          await longTermMemory.ping();
          redisStatus = 'connected';
        } catch (error) {
          logger.error(`Health check - Redis error: ${error}`);
          redisStatus = 'disconnected';
        }
      }

      // Get application uptime
      const uptime = process.uptime();
      
      // Get package version
      const version = process.env.npm_package_version || '1.0.0';
      
      // Check if any critical dependency is down
      const isHealthy = redisStatus !== 'disconnected';
      
      // Prepare response
      const healthStatus = {
        status: isHealthy ? 'ok' : 'error',
        version,
        uptime,
        environment: config.env,
        dependencies: {
          redis: redisStatus
        }
      };
      
      res.status(isHealthy ? 200 : 503).json(healthStatus);
    } catch (error) {
      logger.error(`Health check failed: ${error}`);
      res.status(503).json({
        status: 'error',
        message: 'Health check failed',
        error: (error as Error).message
      });
    }
  });
} 