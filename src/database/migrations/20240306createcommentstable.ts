import { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  await knex.schema.createTable('comments', (table) => {
    table.increments('id').primary();
    table.integer('postId').unsigned().notNullable();
    table.integer('userId').unsigned().notNullable();
    table.text('content').notNullable();
    table.integer('parentId').unsigned();
    table.boolean('isApproved').notNullable().defaultTo(false);
    table.timestamp('approvedAt');
    table.timestamp('createdAt').notNullable().defaultTo(knex.fn.now());
    table.timestamp('updatedAt').notNullable().defaultTo(knex.fn.now());
    
    // Add foreign key constraints
    table.foreign('postId')
      .references('id')
      .inTable('posts')
      .onDelete('CASCADE');
    
    table.foreign('userId')
      .references('id')
      .inTable('users')
      .onDelete('CASCADE');
    
    table.foreign('parentId')
      .references('id')
      .inTable('comments')
      .onDelete('CASCADE');
    
    // Add indexes for frequently queried columns
    table.index('postId');
    table.index('userId');
    table.index('parentId');
    table.index('isApproved');
  });
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTable('comments');
} 