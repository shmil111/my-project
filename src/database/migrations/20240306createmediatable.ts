import { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  // Create media table
  await knex.schema.createTable('media', (table) => {
    table.increments('id').primary();
    table.integer('userId').unsigned().notNullable();
    table.string('filename').notNullable();
    table.string('originalName').notNullable();
    table.string('mimeType').notNullable();
    table.integer('size').unsigned().notNullable();
    table.string('path').notNullable();
    table.string('url').notNullable();
    table.string('alt').nullable();
    table.string('caption').nullable();
    table.json('metadata').nullable();
    table.integer('width').unsigned().nullable();
    table.integer('height').unsigned().nullable();
    table.integer('duration').unsigned().nullable();
    table.boolean('isPublic').notNullable().defaultTo(false);
    table.timestamp('createdAt').notNullable().defaultTo(knex.fn.now());
    table.timestamp('updatedAt').notNullable().defaultTo(knex.fn.now());
    
    // Add foreign key constraint
    table.foreign('userId')
      .references('id')
      .inTable('users')
      .onDelete('CASCADE');
    
    // Add indexes
    table.index('userId');
    table.index('mimeType');
    table.index('isPublic');
  });

  // Create post_media junction table
  await knex.schema.createTable('post_media', (table) => {
    table.increments('id').primary();
    table.integer('postId').unsigned().notNullable();
    table.integer('mediaId').unsigned().notNullable();
    table.string('type').notNullable().defaultTo('attachment'); // attachment, featured, gallery
    table.integer('order').unsigned().notNullable().defaultTo(0);
    table.timestamp('createdAt').notNullable().defaultTo(knex.fn.now());
    
    // Add foreign key constraints
    table.foreign('postId')
      .references('id')
      .inTable('posts')
      .onDelete('CASCADE');
    
    table.foreign('mediaId')
      .references('id')
      .inTable('media')
      .onDelete('CASCADE');
    
    // Add unique constraint to prevent duplicate attachments
    table.unique(['postId', 'mediaId']);
    
    // Add indexes
    table.index('postId');
    table.index('mediaId');
    table.index('type');
    table.index('order');
  });
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTable('post_media');
  await knex.schema.dropTable('media');
} 