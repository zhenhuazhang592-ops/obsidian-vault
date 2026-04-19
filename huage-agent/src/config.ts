/**
 * 配置文件
 * 从 .env 读取环境变量
 */

import { config as dotenvConfig } from 'dotenv';
import * as path from 'path';
import { z } from 'zod';

dotenvConfig();

const EnvSchema = z.object({
  ANTHROPIC_API_KEY: z.string().optional(),
  ANTHROPIC_BASE_URL: z.string().optional(), // MiniMax 兼容: https://api.minimaxi.com/anthropic
  TAVILY_API_KEY: z.string().optional(),
  YOUTUBE_API_KEY: z.string().optional(),
  YOUTUBE_CLIENT_SECRET: z.string().optional(),
  ARK_API_KEY: z.string().optional(),
  OBSIDIAN_VAULT_PATH: z.string().optional(),
});

export const env = EnvSchema.parse(process.env);

const vaultPath = env.OBSIDIAN_VAULT_PATH ?? '/Users/huage/Obsidian Vault';

export const config = {
  // API Keys
  anthropicApiKey: env.ANTHROPIC_API_KEY ?? '',
  anthropicBaseUrl: env.ANTHROPIC_BASE_URL ?? '', // MiniMax 兼容模式
  tavilyApiKey: env.TAVILY_API_KEY ?? '',
  youtubeApiKey: env.YOUTUBE_API_KEY ?? '',
  youtubeClientSecret: env.YOUTUBE_CLIENT_SECRET ?? '',
  arkApiKey: env.ARK_API_KEY ?? '',

  // 路径
  vaultPath,
  wikiPath: path.join(vaultPath, 'wiki'),
  outputPath: path.join(vaultPath, '写作知识库'),
  memoryPath: path.join(vaultPath, '.claude/projects/-Users-huage-Obsidian-Vault/memory/MEMORY.md'),
  referencesPath: path.join(vaultPath, 'AI工具箱/huage-agent/skills/writing/five-stage-longform/references'),

  // 模型
  claudeModel: 'claude-opus-4-6',
  writingModel: 'qwen3-max', // 正文写作用 Qwen3-Max
};
