import { MongoClient } from 'mongodb';
import dotenv from 'dotenv';

dotenv.config();

const uri = process.env.MONGO_URI; // Get MongoDB connection string from .env

if (!uri) {
    throw new Error("MONGO_URI environment variable is not set.");
}

const client = new MongoClient(uri);
let db: MongoClient;

async function connectDB() {
    try {
        await client.connect();
        console.log('Connected to MongoDB');
        db = client; // Store the connected client
        return client.db(); // Return the default database
    } catch (error) {
        console.error('Error connecting to MongoDB:', error);
        throw error;
    }
}
const getDb = () => db;

export { connectDB, getDb, db }; 