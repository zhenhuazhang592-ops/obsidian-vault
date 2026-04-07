# skills/prop-design-skill.md — 道具设计规范

> huage888 系统 | 道具师 Agent 使用
> 输出：assets/prop-prompts.md

---

## 一、道具分级

| 等级 | 定义 | 处理方式 | 是否出资产 |
|------|------|---------|---------|
| 一级（核心道具） | 剧情核心道具，多次出现，有状态变化 | 单独建立资产描述 | ✅ |
| 二级（重要道具） | 多次出现，无状态变化 | 纳入场景描述或角色资产 | ⚠️ 按需 |
| 三级（背景道具） | 场景内摆设，一次性出现 | 纳入场景描述 | ❌ |

---

## 二、道具描述词格式

```markdown
## [道具名] | P[N] | 等级：一级 | 首次出现：S01E01

### 基本信息

| 字段 | 内容 |
|------|------|
| 外观描述 | [形态+材质+颜色+标志性细节] |
| 叙事功能 | [在剧情中的作用] |
| 出现段落 | 第 [X] 段 |
| 出现次数 | X次 |
| 是否需要特写 | 是 / 否 |
| 状态变化 | [如：完整→被撕碎→烧毁，三种状态] |
| 资产状态 | 新建 / 复用(P00X) |

### Visual Bible 对照

✅ / ⚠️ [偏离描述]

### 外观详细描述

```
形态：[形状+大小+比例]
材质：[材质质感关键词，如：金属/皮质/塑料/布料]
颜色：[具体颜色+色号]
标志性细节：[如：底部有磨损痕迹/左侧有一道划痕/盖子边缘掉漆]
```

### 状态变化记录

| 状态 | 出现段落 | 画面描述 |
|------|---------|---------|
| 完整 | 第1段 | [道具完整状态的画面描述] |
| 损坏 | 第3段 | [道具损坏后的画面描述] |
| 消失 | 第5段 | [道具消失（被丢弃/销毁）] |

### LibTV 道具主体创建消息（如需独立出资产）

```markdown
创建道具主体：[道具名]，
主体描述：
```
[道具名]，
外观：[形态+材质+颜色+标志性细节]
状态（本次）：[完整/损坏/消失]
出现场景：[场景名]
叙事功能：[描述]
```
主体类型：商品/物品
参考图数量：2-3张（正面+侧面+细节特写）
```

### 文字锚点（分镜兜底）

```markdown
**文字锚点**：
- 道具名：[道具名]
- 核心外观词：[3个最关键的外观词]
- 标志性细节：[如：底部磨损痕迹/左侧划痕]
- 当前状态：[完整/损坏/消失]
- 禁止词：[矛盾描述]
```
```

---

## 四、质量检查清单

- [ ] 一级道具均输出完整描述词
- [ ] 所有道具外观描述包含形态+材质+颜色+标志性细节
- [ ] 状态变化记录完整（所有出现段落均有记录）
- [ ] 与 visual-bible.md 道具锚点对照标注
- [ ] 道具描述词与角色/场景风格一致
- [ ] 资产库索引已更新（P[N] 编号分配）
- [ ] 道具编号与 outputs/01-director-analysis.md 完全一致
- [ ] 禁止用描述性词汇替代 P[N] 编号

---

## 五、资产一致性强制规则（Toonflow getAssets 对照）

> 参考 Toonflow `getAssets` 工具的禁止规则，以下为硬性约束，违反 = 审核 FAIL

```
⚠️ 资产使用强制规则：
1. 所有输出必须原封不动引用 outputs/01-director-analysis.md 中的道具编号和名称
   - 道具：只能写 P001、P002 等，禁止近义词/缩写/变体
2. 禁止在道具名称前后添加修饰词（如「破碎的P001」「精致的P002」）
3. 外观描述中的关键词必须与 visual-bible.md 道具锚点一致
4. 状态变化记录必须与 director analysis 的道具清单一致
5. 禁止捏造 director analysis 中不存在的道具
```

---

## 六、输出 JSON Schema（PropSchema）

> 为 prop-designer 生成的结构化输出规范，供 qwen-max 格式校验

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PropAsset",
  "description": "道具资产生成输出",
  "type": "object",
  "required": ["id", "name", "level", "description", "narrativeFunction", "appearances", "appearanceDetails", "states"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^P[0-9]{3}$",
      "description": "道具编号，必须与 director analysis 一致"
    },
    "name": { "type": "string" },
    "level": {
      "type": "string",
      "enum": ["一级","二级","三级"],
      "description": "一级=核心道具，二级=重要道具，三级=背景道具"
    },
    "assetStatus": {
      "type": "string",
      "enum": ["新建","复用"],
      "description": "新建=需建立资产，复用=使用已有 P[N] 编号"
    },
    "description": {
      "type": "string",
      "minLength": 20,
      "description": "外观描述：形态+材质+颜色+标志性细节"
    },
    "narrativeFunction": { "type": "string" },
    "appearances": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "integer" },
      "description": "出现段落编号数组，如 [1, 3, 5]"
    },
    "appearanceDetails": {
      "type": "object",
      "required": ["shape", "material", "color", "signatureDetail"],
      "properties": {
        "shape":           { "type": "string", "description": "形状+大小+比例" },
        "material":        { "type": "string", "description": "材质质感关键词" },
        "color":           { "type": "string", "description": "具体颜色+色号" },
        "signatureDetail": { "type": "string", "description": "标志性细节，如磨损痕迹/划痕/掉漆" }
      }
    },
    "states": {
      "type": "array",
      "description": "状态变化记录，每个出现段落一条",
      "items": {
        "type": "object",
        "required": ["state", "segment", "description"],
        "properties": {
          "state":       { "type": "string", "description": "状态名称，如：完整/损坏/消失" },
          "segment":     { "type": "integer", "description": "出现段落编号" },
          "description": { "type": "string", "description": "该状态下的画面描述" }
        }
      }
    },
    "needCloseup": {
      "type": "boolean",
      "description": "是否需要特写"
    },
    "textAnchors": {
      "type": "object",
      "properties": {
        "coreAppearanceWords": {
          "type": "array",
          "items": { "type": "string" },
          "description": "3个最关键的外观词"
        },
        "signatureDetail": { "type": "string" },
        "currentState":     { "type": "string" },
        "forbiddenWords":   { "type": "array", "items": { "type": "string" } }
      }
    }
  }
}
```
