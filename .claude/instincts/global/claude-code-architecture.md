---
id: claude-code-architecture
trigger: "需要深度理解 Claude Code 内部机制，或设计类似的 CLI/Agent 系统时"
confidence: 0.8
domain: 工程架构
source: session-2026-04-02-source-analysis
scope: global
---

# Claude Code 2.1.88 源码架构 · 深度参考

> 来源：Source Map 还原源码，`/Users/huage/Downloads/claude_code_src-master/`
> 版本：@anthropic-ai/claude-code@2.1.88（2026-03-31）
> 规模：1,884 TS/TSX 文件，约 51.2 万行

---

## 顶层目录结构

```
src/
├── entrypoints/     # CLI 入口（cli.tsx, init.ts, mcp.ts）
├── commands/        # 命令系统（101个子目录）
├── components/      # React+Ink UI（146个子目录）
├── tools/           # 工具系统（45个子目录）
├── services/        # 核心业务（mcp/compact/api/analytics/...）
├── hooks/           # React 状态管理（87个子目录）
├── ink/             # 终端渲染基础设施
├── utils/           # 工具函数（331个子目录）
├── state/           # 应用状态（AppState + React Context）
├── skills/          # Skill 系统（bundled/22个内置Skill）
├── plugins/        # 插件系统
├── memdir/          # 记忆目录
├── bridge/          # Bridge 远程控制
├── server/          # 服务器实现
├── migrations/      # 数据库迁移
├── query.ts         # 查询引擎（~68KB，核心通信）
├── QueryEngine.ts   # 查询引擎类（~46KB）
└── vendor/          # 原生扩展源码（audio/image/NAPI）
```

---

## 核心技术发现

### 1. React + Ink 终端 UI

Ink 是 React 在终端的渲染引擎（类似 React DOM）：

```typescript
// src/ink/render.ts — 渲染管线核心
// src/ink/screen.ts — 屏幕管理
// src/ink/layout/ — Flexbox 布局
// src/ink/keybindings/ — 键盘事件
```

**对漫舟的价值**：如果要构建终端工具（Vite CLI / Obsidian 插件），可用 Ink + React 构建交互式界面。

### 2. Feature Flags 条件编译

```typescript
// 编译时裁剪，支撑多版本
feature('KAIROS')        // 主动模式
feature('AGENT_TRIGGERS') // Cron/定时触发
feature('VOICE')          // 语音模式
feature('REACTIVE_COMPACT') // 响应式压缩

// ANT 内部版专有
process.env.USER_TYPE === 'ant'
```

**对漫舟的价值**：设计 Feature Flag 系统，支持多环境/多角色配置。

### 3. 工具原子化注册

`src/tools/tools.ts` 是唯一的工具注册入口：

```typescript
// 条件导入确保 tree-shaking
if (feature('WORKTREE')) {
  import { EnterWorktreeTool, ExitWorktreeTool } from './worktree.ts'
}
// 所有工具统一注册到 tools.ts
```

### 4. MCP 深度集成

`src/services/mcp/` 是完整的 MCP 实现：

```typescript
// 核心文件
MCPConnectionManager.tsx  // 连接管理
SdkControlTransport.ts    // SDK Transport
InProcessTransport.ts     // 进程内传输
officialRegistry.ts        // 官方服务器注册表
oauthPort.ts               // OAuth 端口
```

### 5. Task 抽象系统

支持多种任务类型（前缀标识）：

| 前缀 | 类型 | 文件 |
|------|------|------|
| `b=` | Bash | `LocalShellTask.ts` |
| `a=` | Agent | `LocalAgentTask.ts` |
| `r=` | Remote | `RemoteAgentTask.ts` |
| `t=` | Teammate | `InProcessTeammateTask.ts` |
| `w=` | Workflow | — |
| `m=` | Monitor | — |
| `d=` | Dream | `DreamTask.ts` |

### 6. 上下文压缩

`src/services/compact/` 防止 token 溢出：
- 自动清理思维块和工具结果
- 结合 `query.ts` 的 token 预算追踪
- 支持 `REACTIVE_COMPACT` / `CONTEXT_COLLAPSE` 等实验性特性

### 7. Bridge 远程控制

`src/bridge/` 支持多种远程控制方式：
- SSH 传输
- WebSocket
- 信任设备管理

---

## 设计模式参考（可直接迁移到漫舟工程）

### 模式 A：条件导入 + Feature Flag

```typescript
// 原子工具，各自独立
// src/tools/ 下的每个工具文件职责单一
// 条件导入确保 bundle 干净
import { feature } from '@/utils/betas.ts'

if (feature('WORKTREE')) {
  // 仅在启用时加载
}
```

### 模式 B：两层注册（命令 + 工具）

```typescript
// 命令注册
src/commands/xxx/
// ↓ 导出到
src/commands/index.ts
// ↓ 注册到 CLI
src/entrypoints/cli.tsx

// 工具注册
src/tools/xxx/
// ↓ 导出到
src/tools/tools.ts
// ↓ 注册到 QueryEngine
```

### 模式 C：Hook 状态管理模式

```typescript
// 87 个 hooks，各管各的领域
useCanUseTool.tsx       // 权限
useMergedTools.ts       // 工具合并
useTaskListWatcher.ts   // 任务监听
useSettings.ts          // 设置
// 订阅 AppStateStore 统一状态
```

### 模式 D：迁移系统

```typescript
// src/migrations/ 每版本一个迁移文件
migrateFennecToOpus.ts
migrateSonnet1mToSonnet45.ts
migrateOpusToOpus1m.ts
migrateAutoUpdatesToSettings.ts
```

---

## 内置 Skill 实现参考

`src/skills/bundled/` 的 22 个内置 Skill：

| Skill | 用途 |
|-------|------|
| `batch` | 批量处理 |
| `claudeApi` | API 调用 |
| `debug` | 调试 |
| `keybindings` | 快捷键 |
| `loop` | 循环执行 |
| `remember` | 记忆 |
| `scheduleRemoteAgents` | 定时 Agent |
| `simplify` | 简化 |
| `skillify` | Skill 化 |
| `stuck` | 卡住处理 |
| `updateConfig` | 配置更新 |
| `verify` | 验证 |

**Skill 格式**：每个 Skill 是一个目录，包含 `SKILL.md` + `prompts/` 等子文件，通过 `bundledSkills.ts` 统一注册。

---

## 快速查阅路径

| 想了解 | 查这个文件/目录 |
|--------|----------------|
| CLI 入口 | `src/entrypoints/cli.tsx` |
| 工具注册 | `src/tools/tools.ts` |
| 查询引擎 | `src/query.ts` |
| 状态管理 | `src/state/AppStateStore.ts` |
| Skill 系统 | `src/skills/bundledSkills.ts` |
| MCP 实现 | `src/services/mcp/MCPConnectionManager.tsx` |
| Worktree | `src/utils/worktree.ts` |
| 上下文压缩 | `src/services/compact/` |
| 终端渲染 | `src/ink/render.ts` |
| Hooks | `src/hooks/useMergedTools.ts` |
| 命令系统 | `src/commands/` |
