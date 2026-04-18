/**
 * MEMORY.md 状态管理
 * 参考：claw-code memory.ts
 */

import * as fs from 'fs';
import * as path from 'path';
import { AgentSession } from './types';

// 默认路径（不依赖 config，避免循环）
const DEFAULT_MEMORY_PATH = path.join(
  process.env.HOME ?? '',
  'Obsidian Vault',
  '.claude/projects/-Users-huage-Obsidian-Vault/memory/MEMORY.md'
);

export class Memory {
  private memoryPath: string;

  constructor(memoryPath?: string) {
    this.memoryPath = memoryPath ?? DEFAULT_MEMORY_PATH;
  }

  async load(): Promise<AgentSession | null> {
    if (!fs.existsSync(this.memoryPath)) {
      return null;
    }
    try {
      const content = fs.readFileSync(this.memoryPath, 'utf-8');
      // 简单解析当前项目字段
      const match = content.match(/\*\*当前项目\*\*[^\n]*\n[^\w]*([^\n]+)/);
      if (match) {
        return {
          sessionId: 'restored',
          topic: match[1].trim(),
          outputDir: '',
          phase: 'idle',
          currentStage: 'pending',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
      }
    } catch {
      // ignore
    }
    return null;
  }

  async save(session: AgentSession): Promise<void> {
    if (!fs.existsSync(this.memoryPath)) return;
    try {
      const content = fs.readFileSync(this.memoryPath, 'utf-8');
      const updated = content.replace(
        /(\*\*当前项目\*\*[^\n]*\n[^\w]*)[^\n]+/,
        `$1${session.topic}`
      );
      fs.writeFileSync(this.memoryPath, updated, 'utf-8');
    } catch {
      // ignore
    }
  }

  async appendLog(entry: string): Promise<void> {
    const vaultPath = process.env.OBSIDIAN_VAULT_PATH
      ?? path.join(process.env.HOME ?? '', 'Obsidian Vault');
    const logPath = path.join(vaultPath, 'wiki', 'log.md');
    const header = `# Wiki Log\n\n`;
    if (!fs.existsSync(logPath)) {
      fs.writeFileSync(logPath, `${header}## ${entry}\n`, 'utf-8');
    } else {
      const content = fs.readFileSync(logPath, 'utf-8');
      fs.writeFileSync(logPath, `${content}\n## ${entry}\n`, 'utf-8');
    }
  }
}
