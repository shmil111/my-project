import { getKnexInstance } from '../database/mysql';
import { Knex } from 'knex';

interface MyTableRecord {
  id?: number; // Assuming an auto-incrementing ID
  name: string;
  age: number;
}
const knex: Knex = getKnexInstance();
const tableName = 'mytable'; // Define the table name

//We don't need any functions here anymore, as they are handled by SQLDatabaseService 