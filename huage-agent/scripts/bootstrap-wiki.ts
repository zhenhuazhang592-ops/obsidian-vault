/**
 * Day-0 Wiki Bootstrap
 *
 * 目标：在第一篇文章创作前，将现有的 raw/ 内容批量摄入 wiki
 * 参考：llm-wiki-agent tools/ingest.py + wiki-schema.md
 *
 * 流程：
 * 1. 扫描 raw/ 目录下的所有 .md 文件
 * 2. 对每个文件调用 LLM 生成来源页
 * 3. 提取实体和概念
 * 4. 创建实体页和概念页
 * 5. 更新 wiki/index.md
 * 6. 追加 wiki/log.md 日志
 */

import * as fs from 'fs';
import * as path from 'path';
import { z } from 'zod';
import { config } from '../src/config.js';
import { PromptEngine } from '../src/prompts/shared.js';
import { WIKI_REFLUX_PROMPT } from '../src/prompts/wiki-reflux.js';

// ==================== Schema ====================

const EntitySchema = z.object({
  name: z.string(),
  type: z.enum(['person', 'company', 'product', 'place']),
  content: z.string(),
});

const ConceptSchema = z.object({
  name: z.string(),
  content: z.string(),
});

const NewConnectionSchema = z.object({
  from: z.string(),
  to: z.string(),
  reason: z.string(),
});

const WikiRefluxOutputSchema = z.object({
  sourcePage: z.object({ content: z.string() }),
  entities: z.array(EntitySchema),
  concepts: z.array(ConceptSchema),
  newConnections: z.array(NewConnectionSchema).optional(),
});

type WikiRefluxOutput = z.infer<typeof WikiRefluxOutputSchema>;

// ==================== Helpers ====================

function walkDir(dir: string): string[] {
  const files: string[] = [];
  if (!fs.existsSync(dir)) return files;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...walkDir(full));
    } else if (entry.name.endsWith('.md') && entry.name !== '.DS_Store') {
      files.push(full);
    }
  }
  return files;
}

function toSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

function parseJsonResponse(text: string): WikiRefluxOutput | null {
  // Try to extract JSON from markdown code fences first
  const jsonMatch = text.match(/```json\s*([\s\S]*?)\s*```/);
  if (jsonMatch) {
    try {
      return WikiRefluxOutputSchema.parse(JSON.parse(jsonMatch[1]));
    } catch {
      // fall through
    }
  }
  // Try direct JSON parse
  try {
    return WikiRefluxOutputSchema.parse(JSON.parse(text.trim()));
  } catch {
    return null;
  }
}

function ensureDir(dir: string): void {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

// ==================== Core ====================

async function ingestFile(filePath: string): Promise<WikiRefluxOutput | null> {
  const content = fs.readFileSync(filePath, 'utf-8');
  const rawSlug = path.basename(filePath, path.extname(filePath));
  const slug = toSlug(rawSlug);
  const sourcesJson = JSON.stringify([{ title: slug, url: filePath }]);

  console.log(`  [LLM] 调用 wiki-reflux prompt...`);

  let rawText: string;
  try {
    rawText = await PromptEngine.callLLM({
      template: WIKI_REFLUX_PROMPT,
      vars: {
        title: slug,
        content: content.slice(0, 8000), // truncate to avoid token overflow
        sources: sourcesJson,
      },
      model: 'claude-sonnet',
      temperature: 0.5,
      thinking: { type: 'disabled' },
      maxTokens: 32000,
    }) as string;
  } catch (err) {
    console.log(`  [错误] LLM 调用失败: ${err instanceof Error ? err.message : String(err)}`);
    return null;
  }

  if (!rawText || rawText.trim().length === 0) {
    console.log(`  [错误] LLM 返回为空`);
    return null;
  }

  console.log(`  [LLM] 返回 ${rawText.length} 字符`);
  return parseJsonResponse(rawText);
}

async function main() {
  console.log('========================================');
  console.log('  Day-0 Wiki Bootstrap');
  console.log('  raw/ → wiki/ 批量摄入');
  console.log('========================================\n');

  const rawDir = path.join(config.vaultPath, 'raw');
  const wikiDir = config.wikiPath;

  // Ensure wiki subdirs exist
  ensureDir(path.join(wikiDir, 'sources'));
  ensureDir(path.join(wikiDir, 'entities'));
  ensureDir(path.join(wikiDir, 'concepts'));

  // Step 1: Scan raw/
  const files = walkDir(rawDir);
  console.log(`[扫描] raw/ 共找到 ${files.length} 个 .md 文件\n`);

  if (files.length === 0) {
    console.log('[完成] raw/ 为空，无需摄入。');
    return;
  }

  const date = new Date().toISOString().split('T')[0];
  let totalEntities = 0;
  let totalConcepts = 0;
  const ingestedSources: string[] = [];

  // Step 2: Ingest each file
  for (const file of files) {
    const relPath = path.relative(config.vaultPath, file);
    console.log(`[摄入] ${relPath}`);

    try {
      const result = await ingestFile(file);

      if (!result) {
        console.log(`  [警告] 无法解析 LLM 返回，跳过`);
        continue;
      }

      // Step 3: Write source page
      const slug = toSlug(path.basename(file, path.extname(file)));
      const sourceFilename = `${date}-${slug}.md`;
      const sourcePath = path.join(wikiDir, 'sources', sourceFilename);
      fs.writeFileSync(sourcePath, result.sourcePage.content, 'utf-8');
      ingestedSources.push(`sources/${sourceFilename}`);
      console.log(`  [创建] sources/${sourceFilename}`);

      // Step 4: Write entity pages
      for (const entity of result.entities ?? []) {
        const entityFilename = `${toSlug(entity.name)}.md`;
        const entityPath = path.join(wikiDir, 'entities', entityFilename);
        fs.writeFileSync(entityPath, entity.content, 'utf-8');
        totalEntities++;
        console.log(`  [创建] entities/${entityFilename}`);
      }

      // Step 5: Write concept pages
      for (const concept of result.concepts ?? []) {
        const conceptFilename = `${toSlug(concept.name)}.md`;
        const conceptPath = path.join(wikiDir, 'concepts', conceptFilename);
        fs.writeFileSync(conceptPath, concept.content, 'utf-8');
        totalConcepts++;
        console.log(`  [创建] concepts/${conceptFilename}`);
      }
    } catch (err) {
      console.log(`  [错误] ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  // Step 6: Update wiki/index.md
  if (ingestedSources.length > 0) {
    const indexPath = path.join(wikiDir, 'index.md');
    const indexEntry = `\n\n## ${date} Bootstrap\n\n- ${ingestedSources.length} 个来源页已从 raw/ 批量摄入\n`;
    if (fs.existsSync(indexPath)) {
      fs.appendFileSync(indexPath, indexEntry, 'utf-8');
    } else {
      fs.writeFileSync(indexPath, `# Wiki Index\n${indexEntry}`, 'utf-8');
    }
    console.log(`\n[更新] wiki/index.md`);
  }

  // Step 7: Append wiki/log.md
  const logPath = path.join(wikiDir, 'log.md');
  const logEntry = `\n## [${date}] bootstrap | Day-0 Wiki Bootstrap\n- 来源：raw/ 目录\n- 摄入：${ingestedSources.length} 个来源页\n- 实体：${totalEntities} 个\n- 概念：${totalConcepts} 个\n`;
  if (fs.existsSync(logPath)) {
    fs.appendFileSync(logPath, logEntry, 'utf-8');
  } else {
    fs.writeFileSync(logPath, `# Wiki Log\n${logEntry}`, 'utf-8');
  }
  console.log(`[更新] wiki/log.md`);

  console.log('\n========================================');
  console.log('  Bootstrap 完成！');
  console.log(`  来源：${ingestedSources.length} | 实体：${totalEntities} | 概念：${totalConcepts}`);
  console.log('========================================');
}

main().catch(console.error);
