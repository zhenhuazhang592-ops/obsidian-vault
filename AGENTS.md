# 漫舟工作室 · 智能体导航

> 本文件是仓库顶层地图（Map, Not Manual）。按 Harness Engineering 原则：不超过 60 行。

## 仓库地图

```
Obsidian Vault/
├── CLAUDE.md              ← 全局驭缰配置（六原则）
├── AGENTS.md              ← 本文件，顶层地图
├── MEMORY.md              ← 当前任务仪表盘（唯一真实来源）
├── .claude/
│   ├── rules/             ← 机械化执行规则（lint 守护）
│   ├── hooks/             ← 生命周期钩子（自动化检查）
│   ├── agents/            ← 子智能体定义
│   └── skills/            ← 渐进式专业知识包
├── 格子间女人/漫剧改编/    ← 当前创作项目
│   ├── chapter_index.md   ← 30集分集目录
│   └── atom.md            ← 剧情原子清单
└── 01-输出内容/
    ├── 公众号/             ← 公众号内容输出
    └── 工具研究/           ← 工具调研归档
```

## 六原则入口

| 原则 | 入口 |
|------|------|
| 仓库即记录系统 | MEMORY.md |
| 地图而非手册 | 本文件 |
| 机械化执行 | `.claude/rules/` |
| 熵管理 | `doc-gardening.md` agent |
| 人类掌舵 | CLAUDE.md 第一性原理 |
| Back-Pressure | 每次任务完成的验证清单 |

## 当前活跃项目

**格子间女人漫剧改编**（见 MEMORY.md 仪表盘）

## 写作/创作规范

- Obsidian Vault 使用中文
- 文件命名：`YYYY-MM-DD-文件名.md`
- frontmatter 必须含：`created`/`tags`/`status`
- AI味检查：调用 `ai-taste` rule
- 所有决策必须写入仓库，不在脑子/聊天记录里

## 子目录地图

每个子目录可有自己的 `AGENTS.md`，指向更深的文档。
