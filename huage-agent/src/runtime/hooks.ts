/**
 * Hook 系统
 * 参考：claw-code rust/crates/runtime/src/hooks.rs
 *
 * 退出码语义：
 * - 0 = 允许执行
 * - 2 = 拒绝执行（阻断）
 * - 其他 = 警告（允许但记录）
 *
 * Fixes (plan-eng-review):
 * - Issue 1: stdin 写入 payload JSON
 * - Issue 2/8: 移除 config 循环依赖，直接读环境变量或 registry.json
 * - Issue 9: runHooks 加 try-catch 防御性处理
 */

import * as fs from 'fs';
import * as path from 'path';

export interface HookPayload {
  hook_event_name: 'PreToolUse' | 'PostToolUse';
  tool_name: string;
  tool_input: Record<string, unknown>;
  tool_input_json: string;
  tool_output: string | null;
  tool_result_is_error: boolean;
}

export interface HookResult {
  denied: boolean;
  messages: string[];
}

export class HookRunner {
  private preScripts: string[] = [];
  private postScripts: string[] = [];

  constructor() {
    this.loadHooks();
  }

  private loadHooks(): void {
    // 读取 vault 的 hook registry（不依赖 config 避免循环）
    const vaultPath = process.env.OBSIDIAN_VAULT_PATH
      ?? path.join(process.env.HOME ?? '', 'Obsidian Vault');
    const registryPath = path.join(vaultPath, '.claude/hooks/registry.json');

    if (fs.existsSync(registryPath)) {
      try {
        const registry = JSON.parse(fs.readFileSync(registryPath, 'utf-8'));
        this.preScripts = registry.pre_tool_use ?? [];
        this.postScripts = registry.post_tool_use ?? [];
      } catch {
        // registry 解析失败，忽略
      }
    }
  }

  async runPreToolUse(
    toolName: string,
    toolInput: Record<string, unknown>
  ): Promise<HookResult> {
    const payload: HookPayload = {
      hook_event_name: 'PreToolUse',
      tool_name: toolName,
      tool_input: toolInput,
      tool_input_json: JSON.stringify(toolInput),
      tool_output: null,
      tool_result_is_error: false,
    };
    return this.runHooks(this.preScripts, payload);
  }

  async runPostToolUse(
    toolName: string,
    toolInput: Record<string, unknown>,
    toolOutput: string | null,
    isError: boolean
  ): Promise<HookResult> {
    const payload: HookPayload = {
      hook_event_name: 'PostToolUse',
      tool_name: toolName,
      tool_input: toolInput,
      tool_input_json: JSON.stringify(toolInput),
      tool_output: toolOutput,
      tool_result_is_error: isError,
    };
    return this.runHooks(this.postScripts, payload);
  }

  private async runHooks(scripts: string[], payload: HookPayload): Promise<HookResult> {
    const messages: string[] = [];

    for (const script of scripts) {
      if (!fs.existsSync(script)) continue;

      let child: ReturnType<typeof import('child_process')['spawn']> | null = null;
      try {
        const { spawn } = await import('child_process');

        child = spawn('sh', ['-c', script], {
          stdio: ['pipe', 'pipe', 'pipe'],
        });

        // Fix Issue 1: stdin 写入 payload JSON
        const payloadJson = JSON.stringify(payload);
        child.stdin?.write(payloadJson);
        child.stdin?.end();

        let stdout = '';
        let stderr = '';
        child.stdout?.on('data', (d) => (stdout += d.toString()));
        child.stderr?.on('data', (d) => (stderr += d.toString()));

        const result = await new Promise<{ code: number | null; stdout: string; stderr: string }>(
          (resolve) => {
            child!.on('close', (code) => resolve({ code, stdout, stderr }));
          }
        );

        const exitCode = result.code ?? 1;
        const msg = (result.stdout.trim() || result.stderr.trim());

        if (exitCode === 0) {
          // 允许
        } else if (exitCode === 2) {
          // 拒绝
          return { denied: true, messages: [msg || `Hook denied: ${payload.tool_name}`] };
        } else {
          // 警告
          if (msg) messages.push(msg);
        }
      } catch (e) {
        // Fix Issue 9: 防御性处理
        messages.push(`Hook error: ${e}`);
      } finally {
        // 确保子进程已关闭
        if (child && !child.killed) {
          child.kill();
        }
      }
    }

    return { denied: false, messages };
  }
}
