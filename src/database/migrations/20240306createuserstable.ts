import { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  await knex.schema.createTable('users', (table) => {
    table.increments('id').primary();
    table.string('username').notNullable().unique();
    table.string('email').notNullable().unique();
    table.string('password').notNullable();
    table.string('firstName');
    table.string('lastName');
    table.enum('role', ['admin', 'user', 'guest']).notNullable().defaultTo('user');
    table.boolean('isActive').notNullable().defaultTo(true);
    table.timestamp('lastLogin');
    table.timestamp('createdAt').notNullable().defaultTo(knex.fn.now());
    table.timestamp('updatedAt').notNullable().defaultTo(knex.fn.now());
    
    // Add indexes for frequently queried columns
    table.index('email');
    table.index('username');
    table.index('role');
    table.index('isActive');
  });
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTable('users');
} 