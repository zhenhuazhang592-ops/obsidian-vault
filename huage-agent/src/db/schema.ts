/**
 * SQLite/drizzle schema
 * 参考：dankoe-writer stage_history 表设计
 */

import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const stageHistory = sqliteTable('stage_history', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  projectId: text('project_id').notNull(),
  stage: text('stage').notNull(), // 'research' | 'stage1' | 'stage2' | 'stage3' | 'stage4' | 'stage5'
  version: integer('version').notNull().default(1),
  input: text('input').notNull(),   // JSON string
  output: text('output').notNull(), // JSON string
  model: text('model').notNull(),
  temperature: integer('temperature').notNull(),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

export const projectTable = sqliteTable('project', {
  id: text('id').primaryKey(),
  title: text('title').notNull(),
  subtitle: text('subtitle'),
  targetReader: text('target_reader'),
  painPoint: text('pain_point'),
  status: text('status').notNull().default('active'), // 'active' | 'archived'
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

export type StageHistory = typeof stageHistory.$inferSelect;
export type NewStageHistory = typeof stageHistory.$inferInsert;
export type Project = typeof projectTable.$inferSelect;
export type NewProject = typeof projectTable.$inferInsert;
