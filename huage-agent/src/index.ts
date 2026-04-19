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
  .argument('[topic]', '文章主题（不填则交互式输入）')
  .action(async (topic: string | undefined) => {
    try {
      // 如果没给主题，交互式输入
      if (!topic) {
        const readline = await import('readline');
        const rl = readline.createInterface({
          input: process.stdin,
          output: process.stdout,
        });
        topic = await new Promise<string>((resolve) => {
          rl.question('📝 请输入文章主题: ', (answer) => {
            rl.close();
            resolve(answer.trim());
          });
        });
        if (!topic) {
          logger.error('主题不能为空');
          process.exit(1);
        }
      }

      logger.info(`🚀 开始创作: "${topic}"`);
      const engine = await createSession(topic, await createReadlineLoop());
      await engine.run();
    } catch (error) {
      logger.error(`启动失败: ${error}`);
      process.exit(1);
    }
  });

// ==================== prompt 命令（交互式） ====================

program
  .command('prompt')
  .description('交互式对话模式')
  .action(async () => {
    const readline = await import('readline');
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    });

    console.log('🔵 huage-agent 交互模式，输入主题开始创作，输入 q 退出\n');

    let topic = await new Promise<string>((resolve) => {
      rl.question('📝 请输入文章主题: ', (answer) => resolve(answer.trim()));
    });

    if (!topic || topic.toLowerCase() === 'q') {
      console.log('👋 再见！');
      rl.close();
      return;
    }

    try {
      console.log(`🚀 开始创作: "${topic}"`);
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
