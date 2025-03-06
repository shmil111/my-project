# SQL Database Implementation

This document describes how to use the SQL database features in the Eve project.

## Overview

The project now supports multiple SQL database backends in addition to the in-memory database. The supported databases are:

- **SQLite** - A file-based SQL database, perfect for development and small deployments
- **PostgreSQL** - A powerful, production-ready relational database
- **MySQL** - Another production-ready relational database option

## Configuration

### Environment Variables

Database configuration is controlled through environment variables in the `.env` file:

```
# Database Configuration
DB_IMPLEMENTATION=memory  # memory, sqlite, postgres, mysql
DB_NAME=eve_db
DB_PATH=./data/sqlite  # For SQLite
DB_HOST=localhost  # For PostgreSQL/MySQL
DB_PORT=5432  # For PostgreSQL/MySQL (use 3306 for MySQL)
DB_USER=postgres  # For PostgreSQL/MySQL
DB_PASSWORD=password  # For PostgreSQL/MySQL
```

### Choosing a Database Implementation

Set the `DB_IMPLEMENTATION` environment variable to one of:

- `memory` - Uses the in-memory database (default)
- `sqlite` - Uses SQLite file-based database
- `postgres` - Uses PostgreSQL
- `mysql` - Uses MySQL

### Implementation-Specific Configuration

#### SQLite

- `DB_NAME` - The name of the database file (without extension)
- `DB_PATH` - The directory where the SQLite file will be stored

#### PostgreSQL and MySQL

- `DB_HOST` - The host where the database server is running
- `DB_PORT` - The port number (5432 for PostgreSQL, 3306 for MySQL)
- `DB_USER` - The database user
- `DB_PASSWORD` - The database password
- `DB_NAME` - The name of the database

## Usage

### Using the Database Factory

The recommended way to create database services is through the `DatabaseFactory`:

```typescript
import { DatabaseFactory } from '../services/DatabaseFactory';
import { getDatabaseConfig } from '../config/database';
import { DatabaseRecord } from '../services/DatabaseService';

// Define your data interface
interface MyData extends DatabaseRecord {
  id: number | string;
  // Add your custom fields here
  name: string;
  value: number;
}

// Get configuration from environment
const dbConfig = getDatabaseConfig();

// Create the service
const myDataService = DatabaseFactory.createDatabaseService<MyData>('my_collection', dbConfig);

// Initialize the database
await myDataService.initialize();

// Use the service
const item = await myDataService.create({ name: 'Test', value: 42 });
console.log(`Created item with ID: ${item.id}`);
```

### Direct Usage of SQL Database Service

You can also use the `SQLDatabaseService` directly:

```typescript
import { SQLDatabaseService } from '../services/SQLDatabaseService';

// Configure for SQLite
const sqliteConfig = {
  client: 'sqlite3',
  connection: {
    filename: './data/mydb.sqlite',
    database: 'mydb'
  },
  useNullAsDefault: true
};

// Create the service
const sqlService = new SQLDatabaseService<MyData>('my_collection', sqliteConfig);

// Initialize and use
await sqlService.initialize();
```

## Database Operations

All database implementations support the same operations:

### Initialization

```typescript
await myDataService.initialize();
```

### Creating Records

```typescript
const newItem = await myDataService.create({
  name: 'Test Item',
  value: 42,
  tags: ['test', 'example']
});
```

### Retrieving Records

```typescript
// Get by ID
const item = await myDataService.getById(123);

// Get all records
const allItems = await myDataService.getAll();

// Get with options
const filteredItems = await myDataService.getAll({
  filter: { name: 'Test Item' },
  sortBy: 'value',
  sortDirection: 'desc',
  limit: 10,
  offset: 0
});
```

### Updating Records

```typescript
const updated = await myDataService.update(123, {
  value: 100,
  tags: ['updated']
});
```

### Deleting Records

```typescript
const deleted = await myDataService.delete(123);
```

### Checking if a Record Exists

```typescript
const exists = await myDataService.exists(123);
```

### Counting Records

```typescript
// Count all records
const total = await myDataService.count();

// Count with filter
const filtered = await myDataService.count({ name: 'Test Item' });
```

## Dynamic Schema

The SQL implementation supports dynamic schema, which means it will automatically add columns to the table when you add new fields to your records.

For example, if you create a record with a new field:

```typescript
await myDataService.create({
  name: 'Test',
  value: 42,
  newField: 'This is a new field'
});
```

The implementation will automatically add the `newField` column to the table if it doesn't exist yet.

## Closing Connections

Always close database connections when they are no longer needed:

```typescript
await myDataService.close();
```

## Advanced Usage: Raw SQL Queries

For advanced use cases, you can access the underlying Knex instance:

```typescript
// Get the Knex instance
const knex = sqlService.getKnexInstance();

// Run raw SQL queries
const results = await knex.raw('SELECT * FROM my_collection WHERE name LIKE ?', ['%test%']);
```

## Example

See `examples/sql-database-example.ts` for a complete usage example. 