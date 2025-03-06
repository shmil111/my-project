import express from 'express';
import mysqlRoutes from './routes/mysqlRoutes';
import dotenv from 'dotenv';
import { connectDB } from './db';
import { DatabaseFactory } from './services/DatabaseFactory';
import { getDatabaseConfig } from './config/database';
import { createLogger } from './utils/logger';

const logger = createLogger('index');

dotenv.config();
const app = express();
const port = process.env.PORT || 8080;

// Connect to MongoDB (using your existing db.ts)
connectDB();

// Middleware to parse JSON requests
app.use(express.json());

// Mount the MySQL routes
app.use('/mysql', mysqlRoutes); // Use /mysql as a base path for these routes

// ... your other routes and middleware ...

// Graceful shutdown
process.on('SIGINT', async () => {
    logger.info('Shutting down gracefully...');
    const dbConfig = getDatabaseConfig();
    if(dbConfig.implementation === 'mysql') {
        const mySqlService = DatabaseFactory.createDatabaseService('mytable', dbConfig); // Use the correct table name
        await mySqlService.close(); // Close the database connection
    }

    process.exit(0);
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
}); 