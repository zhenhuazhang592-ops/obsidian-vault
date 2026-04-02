---
id: cookbook-memory-cross-session
name: cookbook-memory-cross-session
description: Cookbook 跨会话记忆：Claude 用 Memory Tool 把学到的模式存文件，下次对话直接调取
tags: [cookbook, memory, persistence, cross-session]
confidence: 0.8
domain: Claude Code 配置
source: claude-cookbooks/tool_use/memory_cookbook.ipynb
scope: global
created: 2026-04-02
---

# Cookbook · 跨会话记忆模式

> 来源：`claude-cookbooks/tool_use/memory_cookbook.ipynb`
> 目标：将 Claude 解决问题的原子模式持久化，下次同类任务自动触发

## 核心机制

```
Session 1: 发现 bug 或模式 → 存入 /memories/*.md
Session 2: 新对话 → 先查 memory → 直接应用已学模式
```

**文件结构（Cookbook 原型）：**
```
memory_demo/memory_storage/
└── memories/
    ├── review.md          # 代码审查模式
    └── patterns/          # 原子模式子目录
        ├── concurrency.md
        └── sql-injection.md
```

## 与 Vault Instinct 系统的对应关系

| Cookbook 概念 | Vault Instinct 对应 |
|--------------|-------------------|
| `/memories/` 目录 | `.claude/instincts/{scope}/` |
| `review.md` 模式文件 | `格子间女人/角色弧线/xxx.yaml` |
| 跨会话调取 | `/learn` 提取 → 下次触发 |
| 模式置信度 | Confidence 0.3/0.7/0.9 |

## 实际应用方式

当 Claude 在会话中识别到一个值得复用的原子模式时：

1. **触发 `/learn`** — 从当前会话提取该模式
2. **存入本能库** — 写入 `.claude/instincts/{scope}/xxx.yaml`
3. **下次任务自动激活** — 模型读到 frontmatter 中的 `trigger`

## 验证 Demo（Cookbook 原生代码）

```python
# 关键 API 参数（Cookbook 原型）
client.beta.messages.create(
    model="claude-sonnet-4-6",
    messages=messages,
    tools=[{"type": "memory_20250818", "name": "memory"}],
    betas=["context-management-2025-06-27"],
)
```

**工具命令：**
| 命令 | 作用 |
|------|------|
| `view` | 查看文件/目录 |
| `create` | 创建文件 |
| `str_replace` | 编辑文件内容（追加/更新模式） |

## 安全注意

- **禁止** 存入密码、API Key、PII
- **禁止** 无限制增长，定期清理
- **必须** 防止 memory poisoning（注入攻击）
