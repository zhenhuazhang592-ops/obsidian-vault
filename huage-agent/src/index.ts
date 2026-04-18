#!/usr/bin/env node

import { Command } from 'commander';
import { WritingEngine, createSession, createReadlineLoop } from './engine';
import { WikiManager } from './wiki/manager';
import { logger } from './logger';

const program = new Command();

program
  .name('huage-agent')
  .description('华哥创作智能体 — 专注文章创作的 Writing Workflow Engine')
  .version('0.1.0');

// ==================== write 命令 ====================

program
  .command('write')
  .description('开始一篇文章创作')
  .argument('<topic>', '文章主题')
  .action(async (topic: string) => {
    try {
      logger.info('启动 Writing Workflow Engine...');
      const engine = await createSession(topic, await createReadlineLoop());
      await engine.run();
    } catch (error) {
      logger.error(`启动失败: ${error}`);
      process.exit(1);
    }
  });

// ==================== wiki 命令组 ====================

const wiki = program.command('wiki').description('Wiki 管理命令');

wiki
  .command('query')
  .description('查询 wiki 知识')
  .argument('<keyword>', '搜索关键词')
  .action(async (keyword: string) => {
    try {
      const manager = new WikiManager();
      const result = await manager.search(keyword);
      console.log(`找到 ${result.pages.length} 个相关页面:`);
      result.pages.forEach((page) => {
        console.log(`- [[${page.title}]]: ${page.content.slice(0, 100)}...`);
      });
    } catch (error) {
      logger.error(`查询失败: ${error}`);
    }
  });

wiki
  .command('ingest')
  .description('摄入源文件到 wiki')
  .argument('<file>', '文件路径')
  .action(async (file: string) => {
    try {
      const manager = new WikiManager();
      await manager.ingestSource(file);
      logger.success('摄入完成');
    } catch (error) {
      logger.error(`摄入失败: ${error}`);
    }
  });

wiki
  .command('lint')
  .description('检查 wiki 健康状态')
  .action(async () => {
    try {
      const manager = new WikiManager();
      const result = await manager.lint();
      if (result.passed) {
        logger.success('Wiki 健康检查通过');
      } else {
        logger.warn(`发现 ${result.issues.length} 个问题:`);
        result.issues.forEach((issue) => console.log(`  - [${issue.type}] ${issue.file}: ${issue.detail}`));
      }
    } catch (error) {
      logger.error(`检查失败: ${error}`);
    }
  });

wiki
  .command('graph')
  .description('构建 wiki 知识图谱')
  .action(async () => {
    try {
      const manager = new WikiManager();
      const graph = await manager.buildGraph();
      logger.success(`图谱构建完成: ${graph.nodes.length} 个节点, ${graph.edges.length} 条边`);
    } catch (error) {
      logger.error(`图谱构建失败: ${error}`);
    }
  });

// ==================== 启动 ====================

program.parse();
