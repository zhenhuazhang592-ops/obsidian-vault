---
id: cookbook-context-engineering
name: cookbook-context-engineering
description: Cookbook 上下文工程：自动清理长会话中的思维块和工具结果，防止 token 膨胀
tags: [cookbook, context, compression, token]
confidence: 0.8
domain: Claude Code 配置
source: claude-cookbooks/tool_use/context_engineering_tools.ipynb
scope: global
created: 2026-04-02
---

# Cookbook · 上下文自动压缩工程

> 来源：`claude-cookbooks/tool_use/context_engineering_tools.ipynb`
> 问题：长会话 token 膨胀，重要信息被挤出上下文窗口

## 两种清理策略

### 1. 工具结果清理 `clear_tool_uses_20250919`

触发条件：输入 token 超过阈值时，自动清除老的工具调用结果。

```python
context_management = {
    "edits": [{
        "type": "clear_tool_uses_20250919",
        "trigger": {"type": "input_tokens", "value": 35000},
        "keep": {"type": "tool_uses", "value": 5},  # 保留最近 5 个
        "clear_at_least": {"type": "input_tokens", "value": 8000}
    }]
}
```

### 2. 思维块清理 `clear_thinking_20251015`

触发条件：扩展思维累积时，自动清除历史思维块。

```python
context_management = {
    "edits": [{
        "type": "clear_thinking_20251015",
        "keep": {"type": "thinking_turns", "value": 1}  # 只保留最后 1 轮
    }]
}
```

**注意：必须放在 edits 数组第一位**

## 对应 Vault 的做法

### MEMORY.md 自动压缩规则

当前 MEMORY.md **331 行，已超 200 行限制**。

触发压缩的条件：
- 文件 > 200 行
- 存在可以迁移到独立 topic 文件的内容

压缩操作：
1. 将历史记录、技能列表、Cookbook 知识 → 迁移到独立 `.md` 文件
2. MEMORY.md 只保留「仪表盘 + 指针」

### 压缩后的理想结构

```
MEMORY.md                          # ≤200 行，仪表盘
.instincts/                        # 历史本能（已从 MEMORY 迁出）
  global/
    cookbook-memory-cross-session.md  # Cookbook 跨会话模式
    cookbook-context-engineering.md  # Cookbook 上下文工程 ← 本文件
    cookbook-agent-patterns.md        # Cookbook Agent 模式
    cookbook-evaluator-optimizer.md  # Cookbook 评估器
  格子间女人/
    ...existing instincts...
```

## Cookbook 中的实测数据

- **触发阈值**：5,000 input tokens（小演示）/ 35,000 tokens（生产）
- **Token 节省**：单次清理节省 166~265 tokens
- **记忆持久化**：清理后本能文件完好，跨会话知识不受影响
