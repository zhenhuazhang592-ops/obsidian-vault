#!/usr/bin/env node

import { Command } from 'commander';
import * as fs from 'fs';
import * as path from 'path';
import { config } from './config.js';
import { logger } from './logger.js';
import { FiveStageOrchestrator } from './stages/index.js';
import { Phase0Research } from './stages/phase0-research.js';
import { WikiManager } from './wiki/manager.js';
import { SessionMetaBuilder } from './learn/session-meta.js';
import { PatternExtractor } from './learn/extractor.js';
import { LocalEvolve } from './learn/evolve.js';
import { VaultBridge } from './learn/vault-bridge.js';

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
  .option('-i, --interactive', '交互模式：选题时由用户选择（默认自动选第1个）')
  .action(async (topic: string | undefined, opts: { interactive?: boolean }) => {
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

      console.log(`\n🚀 开始创作: "${topic}"\n`);
      console.log('━'.repeat(50));

      // Wiki 知识查询（先查，用于研究阶段注入）
      let wikiKnowledge = '';
      try {
        const wiki = new WikiManager();
        const result = await wiki.search(topic);
        if (result.pages.length > 0) {
          wikiKnowledge = result.pages.map((p) => `[[${p.title}]]: ${p.content.slice(0, 200)}`).join('\n');
          console.log(`📚 Wiki 知识: ${result.pages.length} 条相关页面\n`);
        }
      } catch (e) {
        // wiki 查询失败不影响主流程
      }

      // 生成输出目录
      const dateStr = new Date().toISOString().split('T')[0];
      const safeTopic = topic.replace(/[<>:"/\\|?*]/g, '-');
      const outputDir = path.join(config.outputPath, dateStr, safeTopic);
      fs.mkdirSync(outputDir, { recursive: true });
      console.log(`\n📁 输出目录: ${outputDir}\n`);

      // Phase 0: 深度研究（Tavily + YouTube）
      let researchSummary = '';
      try {
        console.log('\n📡 Phase 0: 深度研究中...\n');
        const researcher = new Phase0Research(outputDir);
        await researcher.execute({ topic, wikiKnowledge });
        const saved = await researcher.load();
        researchSummary = saved.summary;
        console.log('\n✅ Phase 0 研究完成\n');
      } catch (e) {
        console.log('⚠️  Phase 0 研究失败，继续后续阶段:', (e as Error).message, '\n');
      }

      console.log('━'.repeat(50));

      // 五阶段执行
      const orchestrator = new FiveStageOrchestrator(outputDir);
      if (opts.interactive) {
        await orchestrator.runInteractive({ topic, researchSummary, wikiKnowledge });
      } else {
        await orchestrator.runFull({ topic, researchSummary, wikiKnowledge });
      }

      console.log('\n✅ 文章创作完成！');
      console.log(`📂 查看: ${outputDir}\n`);

      // Stage 5 完成后 — 自动触发 /learn
      try {
        console.log('\n' + '━'.repeat(50));
        console.log('📚 开始学习本次创作模式...\n');

        // 1. 构建 session-meta.json
        const sessionMeta = new SessionMetaBuilder(outputDir);
        await sessionMeta.build();
        await sessionMeta.save();

        // 2. 提取模式
        const extractor = new PatternExtractor(sessionMeta.getMeta());
        const patterns = extractor.extract();
        if (patterns.length === 0) {
          console.log('未提取到任何模式，跳过学习。\n');
        } else {
          extractor.printSummary(patterns);

          // 3. 用户确认
          console.log('确认要保存以上模式吗？(y/n，默认 y)');
          const rl = await import('readline');
          const rli = rl.createInterface({ input: process.stdin, output: process.stdout });
          const answer = await new Promise<string>(resolve => {
            rli.question('> ', (a: string) => { rli.close(); resolve(a.trim()); });
          });

          if (answer.toLowerCase() !== 'n' && answer !== 'no') {
            // 4. 双写
            const vaultBridge = new VaultBridge();
            const dateStr2 = new Date().toISOString().split('T')[0];

            for (const pattern of patterns) {
              await vaultBridge.writeProjectInstinct(pattern, dateStr2, extractor);
              await vaultBridge.writeVaultInstinct(pattern, dateStr2);
            }
            console.log(`已保存 ${patterns.length} 个创作模式。`);

            // 5. 自动进化检查
            const evolve = new LocalEvolve();
            const suggestions = evolve.check(patterns);
            if (suggestions.highConfidence.length > 0 || suggestions.clusters.length > 0) {
              console.log('\n✨ 检测到可进化的模式：');
              suggestions.highConfidence.forEach(p => {
                console.log(`  - ${p.type}（confidence: ${p.confidence}）`);
              });
              suggestions.clusters.forEach(group => {
                console.log(`  - 聚类：${group[0].domain}（${group.length} 个）`);
              });
              await vaultBridge.triggerSkillEvolution(suggestions.highConfidence);
            }
          } else {
            console.log('已取消保存模式。');
          }
        }
      } catch (e) {
        console.warn('⚠️ 学习模块执行失败，不影响主流程:', (e as Error).message);
      }
    } catch (error) {
      logger.error(`创作失败: ${error}`);
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
