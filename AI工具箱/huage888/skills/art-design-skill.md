# skills/art-design-skill.md — 资产规范 v3

> huage888 系统 | 阶段二 | 角色/场景资产管理
>
> **设计原则：huage888 先想清楚（规划层），再交给 Skill 执行（执行层）**
>
> **两阶段流程**：Phase1 锚点图 → Phase2 多角度一致性图
> **生图模型**：nanobanana（固定，不可替换）

---

## 核心职责

将导演的人物清单和场景清单，转化为 **LibTV 结构化 JSON spec**，供制片人生成 LibTV 操作指南，用户手动在 LibTV 执行两阶段资产创建。

**不做的事**：不直接生成图片，不调 LibTV Skill。
**做的事**：输出结构化 JSON，为制片人提供精确的 LibTV 执行素材。

---

## 两阶段资产创建流水线

```
Phase 1 ──────────────────────────────────────────────────────────
Step 1: character_front_view  →  角色正面白底图  →  拿到 element_id
Step 2: scene_establishing    →  场景全景图      →  拿到 element_id
        ↓
Phase 2 ──────────────────────────────────────────────────────────
Step 3: character_sheet        →  多角度一致性图   →  角色 Character Sheet
Step 4: scene_sheet           →  多角度一致性图   →  场景 Scene Sheet
        ↓
分镜 ─────────────────────────────────────────────────────────────
Step 5: storyboard_image_batch  →  分镜批量出图
Step 6: storyboard_video_batch   →  分镜批量视频
```

**必须按顺序执行**：Phase 2 依赖 Phase 1 返回的 element_id。

---

## 一、角色 Character Sheet 规范

### 输出文件

- **Phase 1**：`assets/character-front-view.json`
- **Phase 2**：`assets/character-sheet.json`

### JSON 格式（直接复制使用）

每个角色输出一个 JSON code block，放在 markdown 文件中：

````markdown
```json
{
  "task_type": "character_front_view",
  "project": {"name": "漠玫传 S01E01《断桥奇遇》"},
  "characters": [
    {
      "id": "C001",
      "name": "漠玫",
      "description": "完整角色描述，用于生成正面锚点图",
      "notes": "金色瞳孔为全片核心记忆点"
    }
  ]
}
```
````

### Phase 1 角色正面图字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| task_type | ✅ | 固定值：`character_front_view` |
| project.name | ✅ | 项目名称 |
| characters[].id | ✅ | 角色编号，如 C001 |
| characters[].name | ✅ | 角色名称 |
| characters[].description | ✅ | 完整角色描述（中文，详细），用于 nanobanana 生图 |
| characters[].notes | 否 | 核心记忆点标注 |

### Phase 2 Character Sheet 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| task_type | ✅ | 固定值：`character_sheet` |
| project.name | ✅ | 项目名称 |
| characters[].id | ✅ | 角色编号 |
| characters[].name | ✅ | 角色名称 |
| characters[].element_id | ✅ | **Phase1 返回的 element_id**（待制片人填入） |
| characters[].appearance_tags | ✅ | 人物核心外貌标签列表（固定不变） |
| characters[].outfit_tags | ✅ | 服装装备标签列表（固定不变） |
| characters[].views | ✅ | 多角度视图列表 |
| views[].view_id | ✅ | 视图唯一ID，如 `正-3/4侧` |
| views[].label | ✅ | 视图中文标签，如 `3/4侧脸无表情` |
| views[].view_angle | ✅ | nanobanana 视角：`front view` / `side view` / `back view` / `3/4 view` |
| views[].shot_type | ✅ | 景别：`full body` / `waist up` / `close-up face` |
| views[].expression | ✅ | 表情：`neutral expression` / `calm` / `shocked` / `nervous` |
| views[].pose | ✅ | 姿态：`standing upright` / `sitting` / `walking` |
| views[].background | 否 | 背景，默认 `simple white background` |

### appearance_tags 拆解规则

每个角色必须拆出 4-6 个独立的 appearance_tags，覆盖：

```
发型（hair）
脸型（face）
眉毛（eyebrows）
眼睛（eyes）— 含瞳色和特殊效果
鼻子（nose，可省略）
肤色（skin）
气质（aura）
头饰（accessory）— 核心符号必须标注
```

### outfit_tags 拆解规则

每个角色必须拆出服装标签，覆盖：

```
上装（外衣）
下装/裙装
鞋子
配饰（可选）
```

---

## 二、场景 Scene Sheet 规范

### 输出文件

- **Phase 1**：`assets/scene-establishing.json`
- **Phase 2**：`assets/scene-sheet.json`

### Phase 1 场景全景图字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| task_type | ✅ | 固定值：`scene_establishing` |
| project.name | ✅ | 项目名称 |
| scenes[].id | ✅ | 场景编号，如 S001 |
| scenes[].name | ✅ | 场景名称 |
| scenes[].description | ✅ | 场景描述（中文，详细） |
| scenes[].lighting | ✅ | 主光源描述 |
| scenes[].notes | 否 | 特殊注意事项 |

### Phase 2 Scene Sheet 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| task_type | ✅ | 固定值：`scene_sheet` |
| project.name | ✅ | 项目名称 |
| scenes[].id | ✅ | 场景编号 |
| scenes[].name | ✅ | 场景名称 |
| scenes[].element_id | ✅ | **Phase1 返回的 element_id**（待制片人填入） |
| scenes[].description | ✅ | 场景整体描述 |
| scenes[].lighting | ✅ | 主光源描述 |
| scenes[].scene_type_tags | ✅ | 场景类型标签列表（固定不变） |
| scenes[].props_tags | ✅ | 道具陈设标签列表（固定不变） |
| scenes[].views | ✅ | 多角度视图列表 |
| views[].view_id | ✅ | 视图唯一ID |
| views[].label | ✅ | 视图中文标签 |
| views[].shot_type | ✅ | 景别：`wide establishing shot` / `medium shot` / `close-up detail shot` |
| views[].camera_angle | ✅ | 角度：`eye-level` / `high angle` / `low angle` / `overhead` |
| views[].focus_subject | ✅ | 聚焦主体 |
| views[].lighting | ✅ | 该镜头具体光线 |
| views[].time_of_day | ✅ | 时段 |
| views[].atmosphere | 否 | 氛围效果 |
| views[].character_handling | 否 | 人物处理，默认 `no characters` |

### scene_type_tags 拆解规则

每个场景必须拆出场景类型标签：

```
场景大类（如：ancient Chinese bridge）
色调关键词
时代/风格关键词
consistent environment, same scene（固定标注）
```

### props_tags 拆解规则

每个场景列出 3-5 个标志性道具/陈设：

```
主体建筑/自然元素
核心陈设物品
光源相关道具
背景元素
same props, same furniture arrangement（固定标注）
```

---

## 三、大圣角色变体处理

大圣有 3 个变体，每个变体是独立的 character 对象：

```
C002a — 大圣·狼狈状态    （00:00–00:32）
C002b — 大圣·金光爆发状态 （00:33–00:40）
C002c — 大圣·意气风发状态 （00:41–00:52）
```

每个变体：
- 独立生成 Phase1 正面图 → 独立 element_id
- Phase2 按变体分别生成 Character Sheet
- 共享部分外观描述（如：发型、五官结构），只在 expression/pose/clothing 上区分

---

## 四、质量检查清单

### Phase 1 输出前
- [ ] 每个角色完整填写 `description`（中文，详细）
- [ ] 核心记忆点标注在 `notes` 中
- [ ] 场景完整填写 `description` 和 `lighting`

### Phase 2 输出前
- [ ] `element_id` 已从 Phase 1 结果填入
- [ ] `appearance_tags` 已拆分完整（4-6 个独立标签）
- [ ] `outfit_tags` 已拆分完整
- [ ] `views` 列表包含：正面 + 3/4侧 + 侧面 + 背面（至少4个视图）
- [ ] 核心记忆点（如金色瞳孔/金色紧箍）标注在备注中

### 禁止项
- ❌ `appearance_tags` 留空或合并成一条长描述
- ❌ Phase 2 未填 `element_id` 就执行
- ❌ 同一角色的不同变体共享同一个 element_id

---

## 五、输出文件命名规范

```
assets/
├── character-front-view.json   # Phase1：角色正面图 spec
├── character-sheet.json        # Phase2：角色多角度 spec
├── scene-establishing.json     # Phase1：场景全景图 spec
└── scene-sheet.json            # Phase2：场景多角度 spec
```

**制片人执行（LibTV 手动模式）**：

```
huage888 执行：
  1. 读取 art-design-skill.md（完整规范）
  2. 读取 outputs/01-director-analysis.md（讲戏本）
  3. 生成「角色正面图操作指南」→ 用户在 LibTV 操作 → 拿到 element_id
  4. 填入 assets/character-front-view.json → assets/character-sheet.json
  5. 生成「角色多角度图操作指南」→ 用户在 LibTV 操作 → 完成 Phase 2

  6. 生成「场景全景图操作指南」→ 用户在 LibTV 操作 → 拿到 element_id
  7. 填入 assets/scene-establishing.json → assets/scene-sheet.json
  8. 生成「场景多角度图操作指南」→ 用户在 LibTV 操作 → 完成 Phase 2

用户执行：
  按操作指南，在 LibTV 控制台手动输入对应的 nanobanana prompt，下载结果图。
  将返回的 element_id 填入对应 JSON 的 element_id 字段。
```

**操作指南由 huage888 调用 qwen-max 生成，详见 `.claude/skills/libtv-skill/SKILL.md`。**

---

## 六、资产一致性强制规则（Toonflow getAssets 对照）

> 参考 Toonflow `getAssets` 工具的禁止规则，以下为硬性约束，违反 = 审核 FAIL

```
⚠️ 资产使用强制规则：
1. 所有输出必须原封不动引用 outputs/01-director-analysis.md 中的角色编号和名称
   - 角色：只能写 C001、C002、C002a、C002b 等，禁止近义词/缩写/变体
   - 场景：只能写 S001、S002 等，禁止用描述替代编号
   - 道具：只能写 P001、P002 等，禁止用描述替代编号
2. 禁止在资产名称前后添加修饰词（如「优雅的C001」「阴郁的S002」）
3. 禁止在 appearance_tags / outfit_tags / scene_type_tags 中引入 director analysis 中没有的描述
4. Phase 2 element_id 必须来自 Phase 1 结果，禁止跨角色借用
5. 同一角色的不同变体（C002a/b/c）必须各自独立 element_id
```

---

## 七、输出 JSON Schema（CharacterSchema + SceneSchema）

> 为 art-designer 生成的结构化输出规范，供 qwen-max 格式校验

### 7.1 CharacterSchema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CharacterAsset",
  "type": "object",
  "required": ["id", "name", "description", "appearanceTags", "outfitTags", "views"],
  "properties": {
    "id":           { "type": "string", "pattern": "^C[0-9]{3}(-[a-z])?$" },
    "name":         { "type": "string" },
    "description":  { "type": "string", "minLength": 20 },
    "notes":        { "type": "string" },
    "elementId":    { "type": "string" },
    "appearanceTags": {
      "type": "array",
      "minItems": 4,
      "items": { "type": "string" }
    },
    "outfitTags": {
      "type": "array",
      "minItems": 3,
      "items": { "type": "string" }
    },
    "views": {
      "type": "array",
      "minItems": 4,
      "items": {
        "type": "object",
        "required": ["viewId", "label", "viewAngle", "shotType", "expression", "pose"],
        "properties": {
          "viewId":    { "type": "string" },
          "label":     { "type": "string" },
          "viewAngle": { "type": "string", "enum": ["front view","side view","back view","3/4 view"] },
          "shotType":  { "type": "string", "enum": ["full body","waist up","close-up face"] },
          "expression":{ "type": "string" },
          "pose":      { "type": "string" }
        }
      }
    }
  }
}
```

### 7.2 SceneSchema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SceneAsset",
  "type": "object",
  "required": ["id", "name", "description", "lighting", "sceneTypeTags", "propsTags", "views"],
  "properties": {
    "id":           { "type": "string", "pattern": "^S[0-9]{3}$" },
    "name":         { "type": "string" },
    "description":  { "type": "string", "minLength": 20 },
    "lighting":     { "type": "string" },
    "notes":        { "type": "string" },
    "elementId":    { "type": "string" },
    "sceneTypeTags": {
      "type": "array",
      "minItems": 3,
      "items": { "type": "string" }
    },
    "propsTags": {
      "type": "array",
      "minItems": 3,
      "items": { "type": "string" }
    },
    "views": {
      "type": "array",
      "minItems": 3,
      "items": {
        "type": "object",
        "required": ["viewId", "label", "shotType", "cameraAngle"],
        "properties": {
          "viewId":      { "type": "string" },
          "label":       { "type": "string" },
          "shotType":    { "type": "string" },
          "cameraAngle": { "type": "string", "enum": ["eye-level","high angle","low angle","overhead"] },
          "focusSubject":{ "type": "string" },
          "lighting":    { "type": "string" },
          "atmosphere":  { "type": "string" }
        }
      }
    }
  }
}
```

---

## 八、质量检查清单（更新版）

### Phase 1 输出前
- [ ] 每个角色完整填写 `description`（中文，详细，≥20字）
- [ ] 核心记忆点标注在 `notes` 中
- [ ] 场景完整填写 `description` 和 `lighting`
- [ ] 角色编号/场景编号与 director analysis 完全一致

### Phase 2 输出前
- [ ] `element_id` 已从 Phase 1 结果填入
- [ ] `appearance_tags` 已拆分完整（≥4 个独立标签）
- [ ] `outfit_tags` 已拆分完整（≥3 个标签）
- [ ] `views` 列表包含：正面 + 3/4侧 + 侧面 + 背面（≥4 个视图）
- [ ] 核心记忆点标注在备注中
- [ ] 同一角色不同变体各自独立 element_id

### 禁止项
- ❌ `appearance_tags` 留空或合并成一条长描述
- ❌ Phase 2 未填 `element_id` 就执行
- ❌ 同一角色的不同变体共享同一个 element_id
- ❌ 引入 director analysis 中不存在的角色/场景描述
- ❌ 在标签中添加资产编号的修饰词（如「优雅的C001」）

