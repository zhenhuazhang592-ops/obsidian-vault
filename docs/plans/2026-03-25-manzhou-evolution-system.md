# 漫舟进化系统 · 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为漫舟智能体新增三大进化能力——资产沉淀(P0)、效果追踪(P1)、Prompt进化(P2)，构成数据驱动闭环飞轮。

**Architecture:** 三个子系统共享同一CDP资产包基础设施，P1产生评分数据喂给P2，P2优化结果沉淀进P0资产库，形成正向循环。

---

## 系统联动架构

```
┌─────────────────────────────────────────────────────────┐
│                   漫舟进化飞轮                            │
│                                                         │
│  P0: 资产沉淀    P1: 效果追踪    P2: Prompt进化         │
│   ↓                  ↓                  ↓               │
│  CDP资产库   →   Prompt版本记录   →  爆款Prompt库       │
│   ↓                  ↓                  ↓               │
│  ID引用复用       效果评分          成功/失败模式提取     │
│   ↓                  ↓                  ↓               │
│  风格一致性    ←  数据闭环      ←   自动优化            │
└─────────────────────────────────────────────────────────┘
```

**数据流向:**
1. P0资产库 → 为P1/P2提供可复用的标准资产
2. P1效果追踪 → 产出"哪个Prompt好/坏"的数据
3. P2进化引擎 → 用P1数据优化Prompt，优秀结果反哺P0

---

## 交付物结构

```
AI漫剧生产/漫舟进化/
├── P0-资产库/
│   ├── cdp-global.json              # 全局资产包（跨项目复用）
│   ├── cdp-global-schema.json       # Schema定义
│   ├── manzhou-asset-library.md     # 资产库使用规范
│   └── [角色资产/] [场景资产/] [道具资产/]
├── P1-效果追踪/
│   ├── manzhou-shot-tracker.md      # 镜头级效果埋点规范
│   ├── manzhou-effect-scorer.md     # 效果评分引擎
│   └── 效果数据/[项目名]-效果日志.json
└── P2-Prompt进化/
    ├── manzhou-prompt-kb.md          # Prompt知识库规范
    ├── manzhou-failure-log.md       # 失败Prompt追踪规范
    └── prompt库/成功/[类型]/  失败/[类型]/
```

---

## Phase 0: 基础设施

### Task 0.1: 创建CDP全局资产包Schema

**文件:** 创建 `AI漫剧生产/漫舟进化/P0-资产库/cdp-global-schema.json`

**内容:**
```json
{
  "version": "1.0.0",
  "meta": {
    "created": "{{date}}",
    "project": "{{project_name}}",
    "type": "global_asset_library",
    "append": false
  },
  "characters": [
    {
      "id": "char_01",
      "name": "{{中文名}}",
      "aliases": ["{{别名}}"],
      "role": "protagonist|antagonist|supporting",
      "dna": {
        "identity": "{{身份背景}}",
        "appearance": "{{外貌特征}}",
        "clothing": "{{服装风格}}",
        "expression": "{{表情习惯}}",
        "gesture": "{{动作习惯}}",
        "perspective": "{{视角偏好}}"
      },
      "visual_anchors": ["{{必须保持的视觉特征}}"],
      "reference_images": [],
      "usage_count": 0,
      "last_used": null,
      "projects": []
    }
  ],
  "locations": [
    {
      "id": "loc_01",
      "name": "{{场景名}}",
      "aliases": ["{{别名}}"],
      "category": "interior|exterior|virtual",
      "lighting": "{{光影规格}}",
      "props": [],
      "reference_images": [],
      "usage_count": 0,
      "last_used": null,
      "projects": []
    }
  ],
  "items": [
    {
      "id": "item_01",
      "name": "{{道具名}}",
      "category": "key|supporting|ambient",
      "narrative_weight": "high|medium|low",
      "appearance": "{{外观描述}}",
      "reference_images": [],
      "usage_count": 0,
      "last_used": null,
      "projects": []
    }
  ]
}
```

**验证:** JSON语法正确性检查

---

## Phase 1: P0 资产复用ID体系

### Task 1.1: 升级manzhou-cdp-schema.md

**目标:** 强化ID引用机制，支持跨项目复用

**文件:** 修改 `AI漫剧生产/skills/manzhou-cdp-schema.md`

**新增字段:**
- `usage_count`: 累计使用次数
- `last_used`: 最后使用时间
- `projects[]`: 使用过的项目列表
- `meta.append`: 增量追加标志

**核心规则:**
1. 所有Skill输出必须使用ID引用（`char_01`而非"谭斌"）
2. 新项目自动查询`cdp-global.json`，复用已有资产
3. 新增资产时`usage_count++`

### Task 1.2: 创建manzhou-asset-library.md

**目标:** 资产库使用规范文档

**文件:** 创建 `AI漫剧生产/漫舟进化/P0-资产库/manzhou-asset-library.md`

**内容结构:**
```
## 资产库工作流

### 新项目启动
1. 检查cdp-global.json是否已有相关角色/场景/道具
2. 如有 → 复用，usage_count++
3. 如无 → 生成新ID，追加到cdp-global.json

### ID引用规范
- 角色: char_01, char_02...
- 场景: loc_01, loc_02...
- 道具: item_01, item_02...

### 复用条件
- 角色: 相同人设 + 相同视觉风格 → 可复用
- 场景: 相同类型 + 相似光影 → 可复用
- 道具: 相同叙事功能 → 可复用
```

### Task 1.3: 将《格子间女人》资产迁移到全局库

**目标:** 用现有项目验证资产库机制

**文件:** 创建 `AI漫剧生产/漫舟进化/P0-资产库/全球间女人-cdp-migration.json`

**操作:**
1. 读取现有`格子间女人/01-IP档案/IP档案.yaml`
2. 按新Schema格式重组
3. 补充usage_count=1, projects=["格子间女人"]

---

## Phase 2: P1 效果追踪闭环

### Task 2.1: 创建manzhou-shot-tracker.md

**目标:** 定义镜头级效果埋点规范

**文件:** 创建 `AI漫剧生产/漫舟进化/P1-效果追踪/manzhou-shot-tracker.md`

**埋点数据结构:**
```json
{
  "shot_id": "P01",
  "project": "{{项目名}}",
  "episode": 1,
  "timestamp": "{{ISO时间}}",
  "image_prompt": "{{原始imagePrompt}}",
  "video_prompt": "{{原始videoPrompt}}",
  "generated_video_url": "{{视频URL}}",
  "platform_metrics": {
    "play_count": 0,
    "completion_rate": 0.0,
    "like_count": 0,
    "comment_count": 0,
    "share_count": 0
  },
  "manual_rating": null,
  "ai_rating": null,
  "effect_score": 0.0,
  "tags": ["{{爆款标签}}"]
}
```

**埋点时机:**
- 生成时: 记录原始Prompt + 视频URL
- 发布后: 接入平台API或手动填入数据
- 完成后: 计算effect_score

### Task 2.2: 创建manzhou-effect-scorer.md

**目标:** 效果评分引擎，将多维指标聚合成单一评分

**文件:** 创建 `AI漫剧生产/漫舟进化/P1-效果追踪/manzhou-effect-scorer.md`

**评分公式:**
```
effect_score = w1×完播率 + w2×点赞率 + w3×评论率 + w4×分享率

权重建议:
- 完播率(w1): 0.4 — 最核心指标
- 点赞率(w2): 0.25
- 评论率(w3): 0.20
- 分享率(w4): 0.15
```

**评分分级:**
- 🔥 爆款: score ≥ 0.8
- ✅ 合格: 0.6 ≤ score < 0.8
- ⚠️ 待优化: 0.4 ≤ score < 0.6
- ❌ 失败: score < 0.4

**与爆款引擎联动:**
- 每个shot关联到SRL模型的位置（Pressure/Release/Vacuum）
- 统计哪类触发器得分最高 → 反哺剧本规则

### Task 2.3: 创建效果日志模板

**目标:** 提供可填写的效果追踪表格

**文件:** 创建 `AI漫剧生产/漫舟进化/P1-效果追踪/效果数据/效果日志-template.json`

---

## Phase 3: P2 Prompt进化引擎

### Task 3.1: 创建manzhou-prompt-kb.md

**目标:** Prompt知识库规范，建立可积累/检索/复用的Prompt资产

**文件:** 创建 `AI漫剧生产/漫舟进化/P2-Prompt进化/manzhou-prompt-kb.md`

**知识库分类:**
```
prompt库/
├── 成功/
│   ├── 景别Prompt/         # ELS/LS/MS/CU等标准景别
│   ├── 情绪Prompt/          # 紧张/甜蜜/悬疑等情绪场景
│   ├── 光影Prompt/          # Roger Deakins级光影
│   └── 运镜Prompt/          # 推/拉/摇/移/跟
└── 失败/
    └── [记录失败原因]
```

**Prompt元数据:**
```json
{
  "id": "prompt_001",
  "category": "景别Prompt/情绪Prompt/光影Prompt/运镜Prompt",
  "effect_score_avg": 0.75,
  "usage_count": 12,
  "success_rate": 0.83,
  "tags": ["都市职场", "室内光", "对话场景"],
  "created_from": "格子间女人-P01",
  "evolved_from": null,
  "parent_prompt_id": null
}
```

**知识库检索逻辑:**
1. 新镜头生成时 → 查询知识库是否有相似tag的成功Prompt
2. 找到 → 优先复用并微调
3. 找不到 → 使用默认模板，生成后入库

### Task 3.2: 创建manzhou-failure-log.md

**目标:** 失败Prompt追踪，积累"什么不该做"

**文件:** 创建 `AI漫剧生产/漫舟进化/P2-Prompt进化/manzhou-failure-log.md`

**失败分类:**
```
失败类型:
- 生成失败: 模型无法生成（如提示词冲突）
- 质量低分: effect_score < 0.4
- 角色崩坏: 与DNA手册不一致
- 场景穿帮: 逻辑不合理
- 风格漂移: 与整体不一致
```

**失败记录格式:**
```json
{
  "id": "fail_001",
  "shot_id": "P07",
  "failure_type": "角色崩坏",
  "original_prompt": "{{原始Prompt}}",
  "failure_reason": "{{失败原因分析}}",
  "corrected_prompt": "{{修正后Prompt}}",
  "correction_effect": "{{修正效果}}",
  "date": "{{date}}"
}
```

**防重复机制:**
- 失败记录入库时 → 检查是否有相似失败模式
- 命中 → 提取共性规则 → 写入manzhou-safety.md黑名单

### Task 3.3: 创建Prompt进化规则

**目标:** 定义Prompt如何从数据中学习

**文件:** 创建 `AI漫剧生产/漫舟进化/P2-Prompt进化/Prompt进化规则.md`

**进化机制:**
```
触发条件: 同一场景类型累计≥5个shot有评分数据

进化算法:
1. 聚类分析: 将相似镜头的Prompt聚类
2. 词频提取: 提取高评分Prompt的共有关键词
3. 权重提升: 高评分关键词权重++
4. 模板生成: 生成新的标准Prompt模板
5. 入库验证: 新模板入库需≥3次成功验证
```

---

## 实施顺序与依赖

```
Phase 0 (Task 0.1)
    ↓
Phase 1 (Task 1.1 → 1.2 → 1.3)    ← P0优先，是P1/P2底座
    ↓
Phase 2 (Task 2.1 → 2.2 → 2.3)    ← P1依赖P0的ID体系
    ↓
Phase 3 (Task 3.1 → 3.2 → 3.3)    ← P2依赖P1的效果数据
```

---

## 实施检查点

| 检查点 | 完成标准 |
|--------|---------|
| CDP Schema | 现有项目的IP档案可转换为新Schema |
| 资产库 | 《格子间女人》角色/场景/道具成功迁移 |
| 效果追踪 | 跑完第01集18个shot的埋点记录 |
| Prompt库 | 有≥10个成功Prompt入库 |
| 失败追踪 | 有≥3个失败Prompt记录及修正 |
| 进化验证 | 用历史数据测试进化算法，验证效果 |

---

## 版本规划

| 版本 | 日期 | 内容 |
|------|------|------|
| v1.0.0 | 2026-03-25 | 基础框架搭建（本文档） |
| v1.1.0 | 待定 | P0资产库上线 |
| v1.2.0 | 待定 | P1效果追踪上线 |
| v1.3.0 | 待定 | P2进化引擎上线 |
| v2.0.0 | 待定 | 三系统联动验证 |
