---
id: cookbook-evaluator-optimizer
name: cookbook-evaluator-optimizer
description: Cookbook Evaluator-Optimizer 评估循环：生成内容 → 按 Instinct 置信度打分 → 迭代优化 → 达标输出
tags: [cookbook, evaluator, quality, iteration]
confidence: 0.8
domain: Claude Code 配置
source: claude-cookbooks/patterns/agents/evaluator_optimizer.ipynb
scope: global
created: 2026-04-02
---

# Cookbook · 评估-优化循环（漫剧版）

> 来源：`claude-cookbooks/patterns/agents/evaluator_optimizer.ipynb`
> 核心思想：Claude 生成内容后，自己评估质量，不达标就迭代优化

## 原型流程

```
生成内容
    ↓
评估器（Evaluator）→ 质量是否达标？
    ↓                    ↓
  达标                不达标
    ↓                    ↓
  输出            优化器（Optimizer）处理反馈
                        ↓
                    重新生成 → 再次评估
```

## 漫剧剧本质量评估器（基于 Instinct 置信度）

### 评估维度（来自格子间女人本能库）

| 维度 | Instinct 规则 | 置信度 |
|------|--------------|--------|
| 角色弧线 | 觉醒点放 50-60% 处 | 0.8 |
| 对话节奏 | 每句 ≤ 15 字 | 0.7 |
| 视觉叙事 | 情绪切换 ≥ 3 个镜头 | 0.7 |
| 潜台词原则 | 不直接说，让观众猜到 | 0.7 |
| 沉默留白 | 关键场景 ≥ 2 秒 | 0.6 |

### 评估算法

```
总分 = Σ(维度置信度 × 达标分数) / Σ维度置信度

达标标准：
  - 总分 ≥ 0.75 → 合格，输出
  - 总分 < 0.75 → 不合格，给出具体改进意见
  - 迭代次数 > 3 → 停止，输出草稿 + 阻塞点
```

### 评估输出格式

```yaml
评估报告:
  总分: 0.68
  达标: false
  维度:
    角色弧线: [pass, "觉醒点放在 55% 处，符合"]
    对话节奏: [fail, "第 3 场有 3 句超过 20 字"]
    视觉叙事: [pass, "情绪切换用了 4 个镜头"]
  改进建议:
    - "第 3 场对白压缩到 15 字以内"
    - "EP02 增加一个视觉叙事留白"
  迭代次数: 1/3
```

## 在 Vault 中的触发方式

### 手动触发（当前阶段）

```
用户: "帮我评估 EP01 剧本质量"
Claude: 运行 `/evolve` 分析本能置信度 → 输出评估报告
```

### 自动化目标（未来）

```
.pre-commit/
  └──剧本质量评估.py
      # 每次 commit 自动运行评估器
      # 不达标 → commit 被 hook 拒绝
```

## 与 Instinct Confidence 演化的关系

| Cookbook 阶段 | Vault 对应 |
|-------------|----------|
| 初始生成 | Claude 首次写剧本 |
| 评估 | Instinct 规则打分 |
| 反馈 | 改进建议写入本能文件 |
| 优化重写 | 置信度不变或微升 |
| 达标输出 | Confidence × 1.2 → 新基准 |

**Confidence 演化规则（来自 `rules/continuous-learning.md`）：**
- 模式被反复观察到 + 用户未纠正 → 升置信度
- 用户明确纠正 → 降置信度
