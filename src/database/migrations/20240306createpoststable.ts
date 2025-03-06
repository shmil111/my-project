import { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  await knex.schema.createTable('posts', (table) => {
    table.increments('id').primary();
    table.integer('userId').unsigned().notNullable();
    table.string('title').notNullable();
    table.text('content').notNullable();
    table.string('slug').notNullable().unique();
    table.boolean('isPublished').notNullable().defaultTo(false);
    table.timestamp('publishedAt');
    table.integer('viewCount').unsigned().notNullable().defaultTo(0);
    table.timestamp('createdAt').notNullable().defaultTo(knex.fn.now());
    table.timestamp('updatedAt').notNullable().defaultTo(knex.fn.now());
    
    // Add foreign key constraint
    table.foreign('userId')
      .references('id')
      .inTable('users')
      .onDelete('CASCADE');
    
    // Add indexes for frequently queried columns
    table.index('userId');
    table.index('slug');
    table.index('isPublished');
    table.index('publishedAt');
  });
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTable('posts');
} 