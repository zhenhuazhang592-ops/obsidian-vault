# Vault Hook 系统

> 来源：Claw Code `rust/crates/plugins/src/hooks.rs` + `rust/crates/plugins/src/lib.rs`
> 用途：在工具执行前/后注入检查管道，实现自动化质量门禁

---

## 核心概念

```
工具调用流程
    │
    ▼
┌─────────────────┐
│  PreToolUse Hook  │  ← 工具执行前运行，可阻断（exit 2）
│  (Bash 脚本/CLI)   │
└────────┬────────┘
         │ 允许 → 继续
         │ 阻断 → 返回错误消息，工具不执行
         ▼
┌─────────────────┐
│   工具执行       │
└────────┬────────┘
         ▼
┌─────────────────┐
│ PostToolUse Hook │  ← 工具执行后运行，通知/日志
└─────────────────┘
```

---

## 触发时机

| 钩子 | 触发条件 | 退出码含义 |
|------|---------|-----------|
| `PreToolUse` | 工具执行前 | 0=允许, 2=拒绝, 其他=警告 |
| `PostToolUse` | 工具执行后 | 任何退出码=警告，不阻断 |

---

## 环境变量（Hook 脚本可读取）

```bash
# 事件元数据
HOOK_EVENT=PreToolUse          # PreToolUse | PostToolUse
HOOK_TOOL_NAME=Write           # 工具名
HOOK_TOOL_IS_ERROR=0           # 0 | 1（仅 PostToolUse）
HOOK_TOOL_INPUT='{"file_path":"..."}'   # 工具输入（JSON）
HOOK_TOOL_OUTPUT='...'          # 工具输出（仅 PostToolUse）

# 管道：stdin 传入完整 JSON
{
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": { "file_path": "...", "content": "..." },
  "tool_input_json": '{"file_path":"..."}',
  "tool_output": null,
  "tool_result_is_error": false
}
```

---

## Vault 内置 Hook 集

位置：`.claude/hooks/`

### 1. frontmatter-check.sh（PreToolUse）

```bash
#!/bin/sh
# 触发条件：Write / Edit 文件是 .md
# 行为：检查 frontmatter 是否含 tags + date
# 阻断：无 frontmatter 的新文件（退出 2）
INPUT=$(cat)
FILE=$(echo "$INPUT" | node -e "const d=require('fs').readFileSync(0,'utf8');const j=JSON.parse(d);console.log(j.tool_input?.file_path||'')")
EXT=$(echo "$FILE" | sed 's/.*\.//')

if [ "$EXT" = "md" ]; then
  if ! echo "$INPUT" | node -e "
    const d=require('fs').readFileSync(0,'utf8');
    const j=JSON.parse(d);
    const content=j.tool_input?.content||'';
    const hasFront=content.startsWith('---');
    const hasTags=hasFront && /\ntags:/.test(content);
    const hasDate=hasFront && /\ndate:/.test(content);
    process.exit(hasTags&&hasDate?0:2);
  "; then
    echo "frontmatter-check: .md file missing tags or date in frontmatter"
    exit 2
  fi
fi
exit 0
```

### 2. filename-sanitize.sh（PreToolUse）

```bash
#!/bin/sh
# 触发条件：Write / Edit
# 行为：文件名不得含空格、中文（建议转为 kebab-case）
# 警告：含空格（退出 1，不阻断）
FILE=$(echo "$INPUT" | node -e "const d=require('fs').readFileSync(0,'utf8');const j=JSON.parse(d);console.log(j.tool_input?.file_path||'')")
if echo "$FILE" | grep -q ' '; then
  echo "filename-sanitize: spaces in path — consider kebab-case"
  exit 1
fi
exit 0
```

### 3. git-lint.sh（PreToolUse）

```bash
#!/bin/sh
# 触发条件：Bash 命令含 git add / git commit / git push
# 行为：git push 默认警告（危险操作）
CMD=$(echo "$INPUT" | node -e "const d=require('fs').readFileSync(0,'utf8');const j=JSON.parse(d);console.log(j.tool_input?.command||'')")
if echo "$CMD" | grep -qE 'git\s+(push|reset\s+--hard|clean\s+-fd)'; then
  echo "git-lint: dangerous git operation detected: $CMD"
  exit 1
fi
exit 0
```

### 4. token-budget-watch.sh（PostToolUse）

```bash
#!/bin/sh
# 触发条件：所有工具
# 行为：记录操作到 .claude/hooks/events.logl（JSONL）
INPUT=$(cat)
TS=$(date +%s%3N)
EVT=$(echo "$INPUT" | node -e "const d=require('fs').readFileSync(0,'utf8');const j=JSON.parse(d);console.log(JSON.stringify({event:j.hook_event_name,tool:j.tool_name,ts:$TS}))")
mkdir -p .claude/hooks
echo "$EVT" >> .claude/hooks/events.logl
exit 0
```

---

## Hook 注册表（JSON 格式）

位置：`.claude/hooks/registry.json`

```json
{
  "pre_tool_use": [
    "./.claude/hooks/frontmatter-check.sh",
    "./.claude/hooks/filename-sanitize.sh",
    "./.claude/hooks/git-lint.sh"
  ],
  "post_tool_use": [
    "./.claude/hooks/token-budget-watch.sh"
  ]
}
```

---

## Hook Runner（TypeScript 实现）

> 工具调用前后的 Hook 执行器
> 位置：`.claude/scripts/hook-runner.ts`

```typescript
import { spawn } from "child_process";
import * as fs from "fs";

export interface HookPayload {
  hook_event_name: string;
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

type ExitCode = 0 | 1 | 2;

const HOOK_OUTCOMES: Record<number, "allow" | "deny" | "warn"> = {
  0: "allow",
  2: "deny",
};

async function runHookScript(
  scriptPath: string,
  payload: HookPayload,
): Promise<{ outcome: "allow" | "deny" | "warn"; message: string | null }> {
  return new Promise((resolve) => {
    const child = spawn("sh", ["-c", scriptPath], {
      stdio: ["pipe", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    child.stdout?.on("data", (d) => (stdout += d.toString()));
    child.stderr?.on("data", (d) => (stderr += d.toString()));

    child.on("close", (code) => {
      const exitCode = code ?? 1;
      const message = stdout.trim() || (stderr.trim() ? stderr.trim() : null);

      if (exitCode === 0) {
        resolve({ outcome: "allow", message });
      } else if (exitCode === 2) {
        resolve({
          outcome: "deny",
          message: message ?? `${payload.hook_event_name} hook denied`,
        });
      } else {
        resolve({
          outcome: "warn",
          message:
            message ??
            `Hook exited with ${exitCode}; allowing tool execution`,
        });
      }
    });

    child.on("error", (err) => {
      resolve({
        outcome: "warn",
        message: `${payload.hook_event_name} hook failed to start: ${err.message}`,
      });
    });

    child.stdin?.write(JSON.stringify(payload));
    child.stdin?.end();
  });
}

/**
 * 运行 PreToolUse 或 PostToolUse 钩子管道
 */
export async function runHooks(
  eventName: "PreToolUse" | "PostToolUse",
  toolName: string,
  toolInput: Record<string, unknown>,
  toolOutput: string | null = null,
  isError: boolean = false,
): Promise<HookResult> {
  const registryPath = ".claude/hooks/registry.json";

  if (!fs.existsSync(registryPath)) {
    return { denied: false, messages: [] };
  }

  const registry = JSON.parse(fs.readFileSync(registryPath, "utf-8"));
  const scripts: string[] = eventName === "PreToolUse"
    ? registry.pre_tool_use ?? []
    : registry.post_tool_use ?? [];

  if (scripts.length === 0) {
    return { denied: false, messages: [] };
  }

  const payload: HookPayload = {
    hook_event_name: eventName,
    tool_name: toolName,
    tool_input: toolInput,
    tool_input_json: JSON.stringify(toolInput),
    tool_output: toolOutput,
    tool_result_is_error: isError,
  };

  const messages: string[] = [];

  for (const script of scripts) {
    if (!fs.existsSync(script)) {
      messages.push(`Hook script not found: ${script}`);
      continue;
    }

    const result = await runHookScript(script, payload);
    messages.push(...(result.message ? [result.message] : []));

    if (result.outcome === "deny") {
      return { denied: true, messages };
    }
  }

  return { denied: false, messages };
}

// ─── 使用示例 ──────────────────────────────────────────────────────

async function example() {
  // PreToolUse
  const pre = await runHooks(
    "PreToolUse",
    "Write",
    { file_path: "docs/test.md", content: "---\ntags: []\ndate: 2026-04-03\n\n# Test" },
  );
  if (pre.denied) {
    console.error("Hook blocked Write:", pre.messages);
    process.exit(1);
  }

  // PostToolUse
  const post = await runHooks(
    "PostToolUse",
    "Write",
    { file_path: "docs/test.md", content: "..." },
    "OK",
    false,
  );
  console.log("PostToolUse messages:", post.messages);
}

if (require.main === module) {
  example().catch(console.error);
}
```

---

## 规则引用

- `rules/atomic-tools.md` — Hook Runner 本身是原子工具的组合
- `rules/persistence.md` — Hook events.logl 是持久化事件流
- `rules/subagent.md` — 探索性任务中 Hook 可被禁用

---

## 与 Claw Code 的差异

| 维度 | Claw Code | Vault Hook |
|------|-----------|-----------|
| 运行环境 | Rust subprocess | Node.js spawn / Bash |
| 注册方式 | `plugin.json` 内嵌 | 独立 `registry.json` |
| 工具透传 | 环境变量 + stdin JSON | 同 |
| 权限模型 | `read-only` / `workspace-write` / `danger-full-access` | Vault 不分级，均为 `workspace-write` |
| 生命周期 | init / shutdown hooks | Vault 不实现（会话粒度） |

---

## 快速启用

```bash
# 1. 写好 hook 脚本（记得 chmod +x）
chmod +x .claude/hooks/frontmatter-check.sh

# 2. 注册到 registry.json
# （已在上面提供完整 registry.json 示例）

# 3. 验证钩子可运行
echo '{"hook_event_name":"PreToolUse","tool_name":"Write","tool_input":{"file_path":"test.md","content":"no frontmatter"},"tool_input_json":"{}","tool_output":null,"tool_result_is_error":false}' \
  | sh .claude/hooks/frontmatter-check.sh
# 期望：退出码 2，输出阻断原因
```
