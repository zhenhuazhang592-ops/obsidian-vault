---
name: instinct-create
description: 手动创建一个新本能（不依赖会话观察）
---

# /instinct-create — 手动创建本能

## 使用场景

- 发现了明确模式，但不在当前会话中发生
- 从外部知识（书本/教程/复盘）提取规律
- 回溯已有的创作经验

## 交互流程

### 1. 确认本能信息

向用户收集：
- **Trigger**：什么时候触发？（"当设计角色成长时"）
- **Action**：具体做什么行为？（"觉醒点放在 50-60% 处"）
- **Domain**：属于哪个领域？
  - 剧本结构
  - 角色弧线
  - 对话节奏
  - 视觉叙事
  - 观众情感
  - 技术实现
- **Scope**：`global` 还是项目名？
- **Confidence**：初始置信度（建议 0.3-0.5，因为是手动创建）

### 2. 确认文件路径

```
.global/本能/<domain>/<id>.yaml        # global
.<项目名>/本能/<domain>/<id>.yaml   # 项目级
```

### 3. 生成文件

```yaml
---
id: <id>
trigger: "<trigger>"
confidence: <0.3-0.5>
domain: <domain>
source: manual-creation
scope: <global|项目名>
created: YYYY-MM-DD
---

# <标题>

## 行为
<action>

## 证据
- 创建时间：YYYY-MM-DD
- 创建方式：手动创建
- 来源：[用户的经验/书籍/教程/复盘]

## 适用边界
- 适用于：
- 不适用于：
```

### 4. 更新注册表

更新 `.claude/instincts/registry.json`：

```json
{
  "<id>": {
    "file": "<path>",
    "domain": "<domain>",
    "confidence": <n>,
    "source": "manual-creation",
    "created": "YYYY-MM-DD"
  }
}
```

### 5. 询问是否运行 /evolve

```
本能已创建：<id>
路径：.claude/instincts/<path>

是否运行 /evolve 检查是否需要合并入现有 skill？
```
