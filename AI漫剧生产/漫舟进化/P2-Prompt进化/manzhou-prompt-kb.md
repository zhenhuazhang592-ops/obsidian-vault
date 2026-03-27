# 漫舟 Prompt 知识库规范

> **版本**: 1.0.0
> **文件名**: `manzhou-prompt-kb.md`
> **角色**: 建立可积累、可检索、可复用的 Prompt 资产库
> **维护者**: 漫舟 Agent

---

## 1. 知识库目录结构

```
P2-Prompt进化/prompt库/
├── 成功/
│   ├── 景别Prompt/
│   │   ├── ELS远景Prompt.json
│   │   ├── LS全景Prompt.json
│   │   ├── MS中景Prompt.json
│   │   ├── MCU中近景Prompt.json
│   │   └── CU特写Prompt.json
│   ├── 情绪Prompt/
│   │   ├── 紧张悬疑Prompt.json
│   │   ├── 甜蜜暧昧Prompt.json
│   │   ├── 愤怒爆发Prompt.json
│   │   └── 悲伤低沉Prompt.json
│   ├── 光影Prompt/
│   │   ├── 自然日光Prompt.json
│   │   ├── 冷白荧光Prompt.json
│   │   └── 暖黄台灯Prompt.json
│   └── 运镜Prompt/
│       ├── 推镜头Prompt.json
│       ├── 拉镜头Prompt.json
│       └── 摇镜头Prompt.json
└── 失败/
    └── [失败Prompt记录]
```

---

## 2. Prompt 元数据格式

```json
{
  "id": "prompt_001",
  "category": "景别Prompt/情绪Prompt/光影Prompt/运镜Prompt",
  "subcategory": "MS中景",
  "effect_score_avg": 0.75,
  "usage_count": 12,
  "success_rate": 0.83,
  "tags": ["都市职场", "室内光", "对话场景"],
  "created_from": "格子间女人-P01",
  "evolved_from": null,
  "parent_prompt_id": null,
  "created_at": "2026-03-25",
  "last_verified": "2026-03-25",
  "verification_count": 3,
  "text": "完整Prompt原文"
}
```

---

## 3. 入库规则

### 成功Prompt入库

**触发条件**: `effect_score ≥ 0.80` 的镜头

**入库流程**:
```
Step 1: 提取 shot_id → 找到原始 imagePrompt / videoPrompt
Step 2: 按 category 分类（景别/情绪/光影/运镜）
Step 3: 提取 tags（场景类型 + 视觉特征 + 情绪）
Step 4: 计算 success_rate（基于历史使用记录）
Step 5: 生成元数据，存入对应目录
Step 6: verification_count = 1（入库验证）
```

### 验证机制

**触发条件**: 同一 Prompt 被复用 ≥ 2 次

```
复用记录 +1 → verification_count++
     ↓
如果第二次验证效果仍好 → success_rate 更新
     ↓
verification_count ≥ 3 → 标记为"已验证"（高可信度）
```

---

## 4. 知识库检索逻辑

**触发时机**: 新镜头生成前

```
输入: 新镜头特征 (location_id, character_ids, emotion, shot_type)
     ↓
Step 1: 提取关键词 tags
        - 角色人设标签（如"职场女强人"）
        - 场景类型标签（如"办公室内景"）
        - 情绪标签（如"压抑"）
        - 景别标签（如"MS中景"）
     ↓
Step 2: 检索相似成功Prompt
        - 匹配 tags 交集 > 50%
        - 按 effect_score_avg 降序排列
     ↓
  ├─ 找到高置信度Prompt（verification_count ≥ 3）
  │   → 优先复用，微调后使用
  ├─ 找到普通成功Prompt
  │   → 复用，补充验证数据
  └─ 未找到匹配
      → 使用默认模板，生成后入库
```

---

## 5. Prompt 进化追踪

```
prompt_001 (初始Prompt)
    ↓ 微调后用于新场景
prompt_001_v2 (evolved_from: prompt_001)
    ↓ 再次进化
prompt_001_v3 (evolved_from: prompt_001_v2)
```

每个Prompt记录 `parent_prompt_id`，形成Prompt进化链，便于追溯最原始的成功模式。

---

## 6. 标签体系

**场景标签**:
```
都市职场 | 古风国潮 | 校园青春 | 家庭伦理 | 悬疑探案 | 科幻未来
```

**视觉标签**:
```
室内光 | 室外光 | 夜景 | 日景 | 冷色调 | 暖色调
```

**情绪标签**:
```
紧张 | 悬疑 | 甜蜜 | 暧昧 | 愤怒 | 悲伤 | 压抑 | 爆发 | 平静
```

**景别标签**:
```
ELS远景 | LS全景 | WS全景 | MS中景 | MCU中近景 | CU特写 | ECU极特写
```
