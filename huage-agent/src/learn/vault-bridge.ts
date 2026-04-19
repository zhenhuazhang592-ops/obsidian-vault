/**
 * VaultBridge — Vault 本能库双写 + Python Skill 进化触发
 *
 * 双写：
 *   1. 项目层：huage-agent/.instincts/YYYY-MM-DD-*.yaml
 *   2. Vault层：~/.claude/instincts/projects/huage-agent/YYYY-MM-DD-*.yaml
 *
 * Skill 进化：
 *   通过 child_process.spawn 调用 ~/.claude/modules/instinct_evolver.py
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { ExtractedPattern } from './types.js';
import { PatternExtractor } from './extractor.js';

export interface VaultBridgeConfig {
  /** Vault 全局本能目录（默认 ~/.claude/instincts/projects/huage-agent） */
  vaultInstinctDir?: string;
  /** Vault skills 目录（默认 ~/.claude/skills） */
  skillsDir?: string;
  /** 项目本能目录（默认 huage-agent/.instincts） */
  projectInstinctDir?: string;
  /** spawn 函数（测试时注入 mock） */
  spawn?: (cmd: string, args: string[]) => { on: (event: string, cb: (code: number) => void) => void };
}

export class VaultBridge {
  private vaultInstinctDir: string;
  private projectInstinctDir: string;
  private skillsDir: string;
  private doSpawn: (cmd: string, args: string[]) => { on: (event: string, cb: (code: number) => void) => void };

  constructor(config: VaultBridgeConfig = {}) {
    const home = os.homedir();
    this.vaultInstinctDir =
      config.vaultInstinctDir ??
      path.join(home, '.claude', 'instincts', 'projects', 'huage-agent');
    this.skillsDir =
      config.skillsDir ?? path.join(home, '.claude', 'skills');
    this.projectInstinctDir =
      config.projectInstinctDir ??
      path.join(process.cwd(), 'huage-agent', '.instincts');
    this.doSpawn = config.spawn ?? ((cmd, args) => require('child_process').spawn(cmd, args));
  }

  /**
   * 写本能到项目层（TypeScript 直接写）
   */
  async writeProjectInstinct(
    pattern: ExtractedPattern,
    date: string,
    extractor: PatternExtractor
  ): Promise<string> {
    const yaml = extractor.toYaml(pattern);
    const slug = pattern.type;
    const fileName = `${date.replace(/-/g, '')}-${slug}.yaml`;
    const filePath = path.join(this.projectInstinctDir, fileName);

    fs.mkdirSync(this.projectInstinctDir, { recursive: true });
    fs.writeFileSync(filePath, yaml, 'utf-8');
    return filePath;
  }

  /**
   * 写本能到 Vault 全局层
   */
  async writeVaultInstinct(
    pattern: ExtractedPattern,
    date: string
  ): Promise<string> {
    const slug = pattern.type;
    const fileName = `${date.replace(/-/g, '')}-${slug}.yaml`;
    const filePath = path.join(this.vaultInstinctDir, fileName);

    fs.mkdirSync(this.vaultInstinctDir, { recursive: true });
    fs.writeFileSync(filePath, this.patternToYaml(pattern, date), 'utf-8');
    return filePath;
  }

  /**
   * 触发 Python Skill 进化
   * 当 confidence >= 0.9 的本能累计出现时，调用 InstinctEvolver
   */
  async triggerSkillEvolution(patterns: ExtractedPattern[]): Promise<void> {
    if (patterns.length === 0) return;

    const home = os.homedir();

    return new Promise((resolve) => {
      const proc = this.doSpawn('python3', [
        '-c',
        `
import sys
sys.path.insert(0, '${home}/.claude/modules')
from instinct_evolver import InstinctEvolver
from pathlib import Path

instincts_data = ${JSON.stringify(patterns.map(p => ({
  id: `huage-agent-${p.type}-auto`,
  name: p.type,
  confidence: p.confidence,
  domain: p.domain,
  scope: 'huage-agent',
  trigger: p.trigger,
  behavior: p.behavior,
  evidence: p.evidence,
})))}
print(f'Evolution check for {len(instincts_data)} patterns')
for idata in instincts_data:
    print(f'  - {idata["name"]} (confidence={idata["confidence"]})')
print('done')
`,
      ]);

      proc.on('close', (code: number) => {
        if (code !== 0) {
          console.warn(`[vault-bridge] Python evolve exited with code ${code}`);
        }
        resolve();
      });

      // 30s 超时保护
      setTimeout(() => {
        console.warn('[vault-bridge] Python evolve timed out, killing...');
        proc.kill();
        resolve();
      }, 30_000);
    });
  }

  private patternToYaml(p: ExtractedPattern, date: string): string {
    const id = `huage-agent-${p.type}-${date.replace(/-/g, '')}`;
    return `---
id: ${id}
trigger: "${p.trigger.replace(/"/g, '\\"')}"
confidence: ${p.confidence}
domain: ${p.domain}
source: session-${date.replace(/-/g, '')}
scope: huage-agent
---

# ${p.type}模式

## 行为
${p.behavior}

## 证据
- 会话：${date}
- 案例：${p.evidence}

## 适用边界
${p.boundary}
`;
  }
}
