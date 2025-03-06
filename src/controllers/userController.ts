import { MongoClient, Db } from 'mongodb';
import asyncHandler from 'express-async-handler';

// Assuming you have a database connection established elsewhere, e.g., in src/db.ts
// and you're exporting the 'db' object.  Import it here.
import { db } from '../db'; // Import your database connection

// ... other controller code ...

export const getUsersOver30 = asyncHandler(async (req, res) => {
  if (!db) {
    res.status(500).json({ message: 'Database connection not established' });
    return;
  }

  try {
    const users = await db.collection('users').find({ age: { $gt: 30 } }).toArray();
    res.status(200).json(users);
  } catch (error) {
    console.error("Error fetching users:", error);
    res.status(500).json({ message: 'Error fetching users', error: error.message });
  }
});

// ... other controller code ... 