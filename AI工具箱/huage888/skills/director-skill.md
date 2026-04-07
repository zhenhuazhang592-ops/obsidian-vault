# skills/director-skill.md — 导演讲戏规范

> huage888 系统 | 导演 Agent 使用
> 输出：outputs/01-director-analysis.md

---

## 一、核心职责

将剧本转化为**讲戏本**，包含：
- 人物清单（含资产状态 **+ 说话风格锚点**）
- 场景清单（含光影设置）
- 道具清单（含分级）
- 分段讲戏（五维融合）
- 视觉圣经对照

**不做的事**：不写生图 prompt，不调模型，不生成视频。

---

## 二、讲戏本格式

### 文件头

```markdown
# outputs/01-director-analysis.md — 导演讲戏本

> 项目：[剧名] | 集数：S01E01 | 目标时长：[X] 分钟
> 视觉风格：[来自 visual-bible.md]
> 情感基调：[如：压抑→爆发]

---

## 全集统计

| 统计项 | 数值 |
|-------|------|
| 总段落数 | X |
| 预估镜头数 | X |
| 新建角色 | X |
| 复用角色 | X |
| 新建场景 | X |
| 复用场景 | X |
| 一级道具 | X |
```

### 人物清单

```markdown
## 人物清单

### [角色名] | C[N] | 首次出现：S01E01

| 字段 | 内容 |
|------|------|
| 年龄/性别/身份 | [描述] |
| 核心外貌词 | [3-5个最具辨识性的词] |
| 标志性特征 | [疤痕/配饰/习惯动作，无则填"无"] |
| 本集服装 | [颜色+款式+质感] |
| 资产状态 | 新建 / 复用(C00X) |
| Visual Bible 对照 | ✅ 符合 / ⚠️ 偏离（原因：[描述]） |
| **说话风格锚点** | |
| 口癖/口头禅 | [3-5个角色专属词汇] |
| 语气词 | [高频语气助词，如"也罢""嗯..."] |
| 句长偏好 | 短促 ≤10字 / 诗意留白 / 说明解释型 |
| 情绪温度 | 冷 / 暖 / 痞 / 中性 |
| 禁止词汇 | [此角色绝对不说的词，无则填"无"] |
| 语气标签 | [从枚举选1-2：书生腔/古典冷艳/阳光痞帅/威严霸气/诗意留白] |

### [角色名] | C[N+1] | 首次出现：S01E01
[同上格式]
```

### 场景清单

```markdown
## 场景清单

### [场景名] | S[N] | 首次出现：S01E01

| 字段 | 内容 |
|------|------|
| 空间类型 | [室内/室外] |
| 时段 | [如：深夜、凌晨、黄昏] |
| 主光源 | [如：荧光灯顶光、窗外自然光] |
| 色调氛围 | [3-4个氛围词] |
| 核心陈设 | [关键道具/家具] |
| 资产状态 | 新建 / 复用(S00X) |
| Visual Bible 对照 | ✅ 符合 / ⚠️ 偏离 |
```

### 道具清单

```markdown
## 道具清单

### [道具名] | P[N] | 等级：一级（核心道具）

| 字段 | 内容 |
|------|------|
| 外观描述 | [形态+材质+颜色+标志性细节] |
| 叙事功能 | [在剧情中的作用] |
| 出现段落 | [第X段] |
| 出现次数 | X次 |
| 是否需要特写 | 是 / 否 |
| 状态变化 | [如：完整→撕碎→烧毁] |
| 资产状态 | 新建 / 复用(P00X) |

### [道具名] | P[N+1] | 等级：三级（背景道具）
[三级道具纳入场景描述，不单独出资产]
```

### 分段讲戏

```markdown
## 分段讲戏

### 第 1 段：[段落标题]（约 X 秒）

**情绪锚点**：
- 情绪目标：[描述]
- 情绪转折点：[如有]
- 信息植入点：[关键道具/信息出现]

**道具出现记录**：
- P001 [道具名]：[首次/再次出现]，[状态描述]，[是否特写：是/否]

**讲戏内容**：

[用自然段落叙述，五个维度完整融合：

一、画面（景别+空间关系）：
[描述]

二、动作链（物理动作，时序清晰）：
[描述]

三、台词/声音（如有）：
[角色]：[台词]（情绪：[克制/爆发/平静]）
或：画外音：[描述]

四、镜头运动（方向+速度）：
[描述]

五、光影氛围（方向+色温+强度）：
[描述，与 visual-bible.md 光影基准对照]

]

**Visual Bible 对照**：
- 角色外貌：✅ C001 [角色名] 符合锚点
- 场景光影：✅ S001 符合 visual-bible.md [时段] 基调
- 色调：✅ 符合整体 [色调] 基调
- 道具：✅ P001 符合外观锚点
- 偏离标注：无 / ⚠️ [偏离描述 + 剧情原因]

**分镜预估**：约 X 个镜头
- 镜头1：全景建立，X秒
- 镜头2：[景别]，[动作]，X秒
- 镜头3：特写，[道具名/P001状态变化]，X秒
```

---

## 四、结构化段落输出 Schema（Toonflow episodeSchema 对照）

> 参考 Toonflow outlineScript/index.ts 的 `EpisodeData` 接口
> 讲戏本输出 Markdown 后，须附上等效 JSON，供 qwen-max 格式校验

### 4.1 段落结构规范

每个段落对应 `segments[N]`，必须包含：

```json
{
  "segments": [
    {
      "index": 1,
      "title": "段落标题",
      "keyEvent": "起",
      "description": "剧情主干摘要，50-100字",
      "emotion": 2,
      "emotionLabel": "压抑",
      "shotCount": 3,
      "duration": 8,
      "characters": ["C001", "C002"],
      "scene": "S001",
      "props": ["P001"],
      "visualHighlights": ["标志性镜头1", "标志性镜头2"],
      "conflict": "核心矛盾一句话"
    }
  ]
}
```

**情绪量化规范（emotion → emotionLabel）**：

| emotion | emotionLabel | 适用场景 |
|---------|-------------|---------|
| 1-2 | 压抑 | 困境初始，角色处于低谷 |
| 3-4 | 积累 | 矛盾酝酿，压抑中暗流涌动 |
| 5-6 | 对抗 | 正面冲突，意志碰撞 |
| 7-8 | 爆发 | 高潮，情绪顶点 |
| 9-10 | 释放 | 转折，余波，悬念 |

**keyEvents 分配规则**：
- 第 1 段 → 起（建立困境）
- 第 2 段 → 承（矛盾积累）
- 第 3 段 → 转（高潮爆发）
- 第 4+ 段 → 合（收束悬念）

### 4.2 完整 JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DirectorAnalysis",
  "description": "导演讲戏本结构化输出",
  "type": "object",
  "required": ["meta", "segments", "characters", "scenes", "props"],
  "properties": {
    "meta": {
      "type": "object",
      "required": ["projectName", "episode", "totalDuration", "emotionalArc"],
      "properties": {
        "projectName":   { "type": "string" },
        "episode":       { "type": "string" },
        "totalDuration": { "type": "number", "description": "总时长（秒）" },
        "emotionalArc":  { "type": "string",  "description": "情绪弧线，如：2(压抑)→5(对抗)→9(爆发)→3(余波)" }
      }
    },
    "segments": {
      "type": "array",
      "minItems": 1,
      "description": "段落列表，严格按叙事顺序排列",
      "items": {
        "type": "object",
        "required": ["index", "title", "keyEvent", "description", "emotion", "emotionLabel", "shotCount", "duration", "characters", "scene"],
        "properties": {
          "index":           { "type": "integer", "minimum": 1 },
          "title":           { "type": "string" },
          "keyEvent":        { "type": "string", "enum": ["起","承","转","合"] },
          "description":     { "type": "string", "minLength": 50, "maxLength": 200 },
          "emotion":         { "type": "integer", "minimum": 1, "maximum": 10 },
          "emotionLabel":    { "type": "string" },
          "shotCount":       { "type": "integer", "minimum": 1 },
          "duration":        { "type": "number", "minimum": 1 },
          "characters":      { "type": "array", "items": { "type": "string", "pattern": "^C[0-9]{3}(-[a-z])?$" } },
          "scene":           { "type": "string", "pattern": "^S[0-9]{3}$" },
          "props":           { "type": "array", "items": { "type": "string", "pattern": "^P[0-9]{3}$" } },
          "visualHighlights":{ "type": "array", "items": { "type": "string" } },
          "conflict":        { "type": "string" }
        }
      }
    },
    "characters": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name", "assetStatus"],
        "properties": {
          "id":          { "type": "string", "pattern": "^C[0-9]{3}(-[a-z])?$" },
          "name":        { "type": "string" },
          "assetStatus": { "type": "string", "enum": ["新建","复用"] }
        }
      }
    },
    "scenes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name", "assetStatus"],
        "properties": {
          "id":          { "type": "string", "pattern": "^S[0-9]{3}$" },
          "name":        { "type": "string" },
          "assetStatus": { "type": "string", "enum": ["新建","复用"] }
        }
      }
    },
    "props": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name", "level", "assetStatus"],
        "properties": {
          "id":          { "type": "string", "pattern": "^P[0-9]{3}$" },
          "name":        { "type": "string" },
          "level":       { "type": "string", "enum": ["一级","二级","三级"] },
          "assetStatus": { "type": "string", "enum": ["新建","复用"] }
        }
      }
    }
  }
}
```

### 4.3 情绪弧线填写规范

讲戏本文件头须包含 `emotionalArc` 字段，格式为：

```
emotion(起) → emotion(承) → emotion(转) → emotion(合)
如：2(压抑) → 5(对抗) → 9(爆发) → 3(余波)
```

四段情绪差值（转折 - 初始）应 ≥ 3，否则节奏感不足。

---

## 五、质量检查清单

- [ ] 所有角色均有核心外貌词（3-5个）
- [ ] 所有新建角色均标注 Visual Bible 对照
- [ ] 所有场景均含光影设置（光源方向+色温）
- [ ] 一级道具均有状态变化记录
- [ ] 每段落讲戏含五维（画面+动作+台词+运镜+光影）
- [ ] 所有段落标注 Visual Bible 对照
- [ ] 有意偏离均已标注原因
- [ ] 分镜预估镜头数与目标时长匹配（约2.5秒/镜头）
- [ ] 文件头含 emotionalArc（如：`2(压抑)→5(对抗)→9(爆发)→3(余波)`）
- [ ] 每段落含 keyEvent（起/承/转/合四选一）
- [ ] 每段落含 emotion 数值（1-10）
- [ ] 情绪弧线转折差值 ≥ 3
- [ ] Markdown 输出后附等效 JSON（如条件允许）
