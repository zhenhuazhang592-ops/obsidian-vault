---
id: cookbook-agent-patterns
name: cookbook-agent-patterns
description: Cookbook 5 种 Agent 工作流模式：Chaining / Routing / Parallel / Orchestrator-Workers / Evaluator-Optimizer，映射到漫剧创作场景
tags: [cookbook, agent-patterns, workflow, orchestration]
confidence: 0.8
domain: Claude Code 配置
source: claude-cookbooks/patterns/agents/
scope: global
created: 2026-04-02
---

# Cookbook · Agent 工作流模式映射

> 来源：`claude-cookbooks/patterns/agents/`
> 参考：[Building Effective Agents](https://anthropic.com/research/building-effective-agents)

## 5 种核心模式

### 模式 1：Prompt Chaining（链式）

```
A → B → C → D
```
每个步骤依赖上一个输出。

**漫剧适用场景：**
```
主题调研 → 大纲生成 → 分集展开 → 正文写作 → 自审
```

### 模式 2：Routing（路由）

```
输入 → 分类器 → 专家 Agent
```
模型判断输入类型，路由到不同技能。

**漫剧适用场景：**
```
用户请求 → 识别类型（剧本/配图/分镜/发布）
  → manju-skill（剧本）
  → baoyu-image-gen（配图）
  → remotion（动画）
```

### 模式 3：Parallel LLM（并行）

```
     → Agent A（EP01 剧本）
输入 → Agent B（EP02 剧本）  同时运行
     → Agent C（分镜资产）
```
互不依赖的任务并行执行。

**漫剧适用场景：**
```
格子间女人 EP01/EP02/EP03 剧本并行开发
worktree 隔离执行（见 rules/worktree-isolation.md）
```

### 模式 4：Orchestrator-Workers（主控+工人）

```
主控 Agent
  → Worker 1（调研）
  → Worker 2（写作）
  → Worker 3（配图）
  → 主控聚合结果
```
主控动态分配任务，结果统一整合。

**漫剧适用场景：**
```
主控：漫剧质量评估
  → 调研 Worker：核查原著版权状态
  → 写作 Worker：生成剧本初稿
  → 配图 Worker：生成分镜参考图
  → 主控：汇总各 Worker 输出，形成完整改编方案
```

### 模式 5：Evaluator-Optimizer（评估-优化循环）

```
生成内容 → 评估器 → 不合格 → 优化 → 再评估
                 ↓ 合格
              输出
```

**漫剧适用场景：**
```
初稿剧本 → Instinct 置信度评估（角色弧线/对话节奏/视觉叙事）
  → 不达标 → 反馈优化
  → 达标 → 定稿
```

## Cookbook 实现代码（Evaluator-Optimizer）

```python
# patterns/agents/evaluator_optimizer.ipynb 原型
class EvaluatorOptimizer:
    def run(self, content):
        for _ in range(max_iterations):
            evaluation = self.evaluator(content)
            if evaluation.passes():
                return content
            content = self.optimizer(content, evaluation.feedback)
        return content
```

## 与 Vault 任务图的映射

| Agent 模式 | Vault 实现 |
|-----------|----------|
| Parallel LLM | `git worktree` 并行多集 |
| Orchestrator-Workers | Agent 工具编排子代理 |
| Evaluator-Optimizer | Instinct 置信度 × `/evolve` |
| Routing | Skill 按需加载（Layer 1/2）|
| Prompt Chaining | `.tasks/` DAG 任务链 |

## 在 Vault 中的触发方式

- **Parallel LLM**：`/enter-worktree` 创建多集并行 worktree
- **Evaluator-Optimizer**：运行 `/evolve` 分析本能库 Confidence
- **Orchestrator-Workers**：Agent 工具编排（遵守 `rules/subagent.md`）
