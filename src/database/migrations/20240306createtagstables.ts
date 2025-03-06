import { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  // Create tags table
  await knex.schema.createTable('tags', (table) => {
    table.increments('id').primary();
    table.string('name').notNullable().unique();
    table.string('slug').notNullable().unique();
    table.text('description');
    table.integer('postCount').unsigned().notNullable().defaultTo(0);
    table.timestamp('createdAt').notNullable().defaultTo(knex.fn.now());
    table.timestamp('updatedAt').notNullable().defaultTo(knex.fn.now());
    
    // Add indexes
    table.index('name');
    table.index('slug');
  });

  // Create post_tags junction table
  await knex.schema.createTable('post_tags', (table) => {
    table.increments('id').primary();
    table.integer('postId').unsigned().notNullable();
    table.integer('tagId').unsigned().notNullable();
    table.timestamp('createdAt').notNullable().defaultTo(knex.fn.now());
    
    // Add foreign key constraints
    table.foreign('postId')
      .references('id')
      .inTable('posts')
      .onDelete('CASCADE');
    
    table.foreign('tagId')
      .references('id')
      .inTable('tags')
      .onDelete('CASCADE');
    
    // Add unique constraint to prevent duplicate tag assignments
    table.unique(['postId', 'tagId']);
    
    // Add indexes
    table.index('postId');
    table.index('tagId');
  });
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTable('post_tags');
  await knex.schema.dropTable('tags');
} 