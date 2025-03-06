import { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  await knex.schema.createTable('categories', (table) => {
    table.increments('id').primary();
    table.string('name').notNullable();
    table.string('slug').notNullable().unique();
    table.text('description');
    table.integer('parentId').unsigned();
    table.integer('postCount').unsigned().notNullable().defaultTo(0);
    table.integer('level').unsigned().notNullable().defaultTo(0);
    table.integer('order').unsigned().notNullable().defaultTo(0);
    table.boolean('isActive').notNullable().defaultTo(true);
    table.timestamp('createdAt').notNullable().defaultTo(knex.fn.now());
    table.timestamp('updatedAt').notNullable().defaultTo(knex.fn.now());
    
    // Add self-referential foreign key for parent category
    table.foreign('parentId')
      .references('id')
      .inTable('categories')
      .onDelete('SET NULL');
    
    // Add indexes
    table.index('name');
    table.index('slug');
    table.index('parentId');
    table.index('level');
    table.index('order');
    table.index('isActive');
  });

  // Add categoryId to posts table
  await knex.schema.alterTable('posts', (table) => {
    table.integer('categoryId').unsigned();
    table.foreign('categoryId')
      .references('id')
      .inTable('categories')
      .onDelete('SET NULL');
    table.index('categoryId');
  });
}

export async function down(knex: Knex): Promise<void> {
  // Remove categoryId from posts table
  await knex.schema.alterTable('posts', (table) => {
    table.dropForeign(['categoryId']);
    table.dropColumn('categoryId');
  });
  
  // Drop categories table
  await knex.schema.dropTable('categories');
} 