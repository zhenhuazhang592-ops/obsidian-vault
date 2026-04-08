---
name: libtv-skill
description: LibTV 手动执行指南 - 将 huage888 的资产 JSON Spec 转换为用户可照做的操作指南，在 LibTV 手动完成角色/场景/分镜资产的生成。覆盖场景与原 libtv-skill 完全一致：角色正面图、角色多角度、场景全景图、场景多角度、分镜批量出图、分镜批量视频、图生视频。当用户提到 liblib、libtv、或任何生图/生视频需求时触发。
---

# LibTV 手动执行指南

LibTV 是 LiblibAI 推出的 AI 视频创作平台。本技能**不调用 API**，只生成操作指南，你照做即可。

**平台核心能力：**
- **生成**：文生图、文生视频、图生视频、视频续写
- **编辑**：局部修改、元素替换、镜头调整、风格迁移
- **模型**：Seedance 2.0、Kling 3.0/O3、Wan 2.6、NanoBanana、Seedream 5.0 等

---

## 一、如何使用本技能

当你有生图/生视频需求时，告诉我：

1. **你想做什么**（如：生成角色正面图、分镜出图、做视频）
2. **提供相关 JSON Spec 文件路径**（如 `assets/character-front-view.json`）

我会：
- 读取 JSON Spec
- 生成一份**完整的操作指南**（含分步骤说明 + 具体 Prompt）
- 你照着指南在 LibTV 操作即可

---

## 二、两阶段资产创建流程

### ▌阶段一：生成锚点图（建立 element_id）

**目的**：为每个角色/场景生成一张正面/全景图，作为后续多角度的基准。

| 步骤 | 操作 | 输入文件 |
|------|------|---------|
| Step 1 | 角色正面图（锚点） | `assets/character-front-view.json` |
| Step 2 | 场景全景图（锚点） | `assets/scene-establishing.json` |

**完成后**：LibTV 会返回图片 URL，你需要把图片的 element_id 填入阶段二的 JSON 文件。

---

### ▌阶段二：生成多角度一致性图

**前提**：阶段一已完成，element_id 已填入对应 JSON。

| 步骤 | 操作 | 输入文件 |
|------|------|---------|
| Step 3 | 角色多角度图（Character Sheet） | `assets/character-sheet.json` |
| Step 4 | 场景多角度图（Scene Sheet） | `assets/scene-sheet.json` |

---

### ▌分镜阶段：分镜批量视频

**前提**：阶段一+二已完成，资产注册表已更新。

| 步骤 | 操作 |
|------|------|
| Step 5 | 分镜批量出图（可选） |
| Step 6 | 分镜批量视频（Kling O1） |

---

## 三、每种任务的操作指南模板

### 3.1 角色正面图（Phase 1）

当你提供 `assets/character-front-view.json` 后，输出如下指南：

---

**【角色正面图 · 操作指南】**

**目标**：为以下角色各生成一张正面全身无表情白底图，作为后续多角度的基准。

**在 LibTV 中操作：**

1. 打开 [LibTV](https://www.liblib.tv/)，新建一个 Project（命名为本项目名）
2. 在 Project 中新建一个 Session
3. 选择**生图模型**：**nanobanana**（固定，不可换）
4. 向 AI 发送以下消息（复制粘贴全部内容）：

```
【任务类型】角色正面图 · 主体锚点建立
【项目名称】（从 JSON 中读取项目名）
【生图模型】nanobanana（固定）

（然后逐角色列出，格式如下：）

【角色】（角色ID）（角色名）
nanobanana style, anime illustration, flat shading, clean lineart,
（角色的 description 字段内容），
front view, full body, neutral expression, standing upright,
simple white background,
masterpiece, best quality, highly detailed, sharp focus

⚠️ 必出：正面全身无表情图，作为后续多角度 Character Sheet 的主体锚点
⚠️ 重要：此图人物为后续所有变体的唯一基准，禁止改变脸型/发型/服装
```

5. 等待生成完成，下载图片
6. **把图片 URL 转为 element_id**（LibTV 画布中右键图片 → 复制 element_id 或截图保存路径）
7. 将 element_id 填入 `assets/character-sheet.json` 的对应角色字段

---

### 3.2 场景全景图（Phase 1）

当你提供 `assets/scene-establishing.json` 后，输出如下指南：

---

**【场景全景图 · 操作指南】**

**目标**：为以下场景各生成一张全景图，作为后续多角度的基准。

**在 LibTV 中操作：**

1. 在 LibTV Project 中新建 Session
2. 选择**生图模型**：**nanobanana**（固定）
3. 向 AI 发送以下消息：

```
【任务类型】场景全景图 · 主体锚点建立
【项目名称】（项目名）
【生图模型】nanobanana（固定）

（逐场景列出：）

【场景】（场景ID）（场景名）
nanobanana style, anime illustration,
（场景的 description 字段），
wide establishing shot, eye-level,
（lighting 字段），
no characters,
masterpiece, best quality, highly detailed, sharp focus

⚠️ 必出：全景图，作为后续多角度 Scene Sheet 的场景锚点
⚠️ 重要：此图为后续所有子图的唯一基准，禁止改变场景布局/色调/道具陈设
```

4. 等待生成完成，下载图片
5. 将 element_id 填入 `assets/scene-sheet.json` 的对应场景字段

---

### 3.3 角色多角度图（Phase 2）

当你提供 `assets/character-sheet.json` 后，输出如下指南：

---

**【角色多角度图 · Character Sheet 操作指南】**

**前提**：Phase 1 已完成，element_id 已填入 JSON。

**在 LibTV 中操作：**

1. 在 LibTV Project 中新建 Session
2. 选择**生图模型**：**nanobanana**（固定）
3. 向 AI 发送以下消息：

```
【任务类型】角色多角度一致性图 · Character Sheet
【项目名称】（项目名）
【生图模型】nanobanana（固定）
【核心原则】②③部分固定不变，只改④变量；所有子图必须与正面锚点人物完全一致
【锚点使用】使用角色正面锚点图（element_id: 见各角色标注）保持脸型/发型/服装一致

── 角色 （角色ID） （角色名） ──
【锚点 element_id】（填入的值）

① 风格锚点（固定）：
nanobanana style, anime illustration, flat shading, clean lineart,

② 人物核心外貌（固定不变）：
（逐条列出 appearance_tags）
  （如：乌黑长发盘成现代感道姑髻，）
  （如：鹅蛋脸，清冷古典感，）
  same face, consistent character design,

③ 服装装备（固定不变）：
（逐条列出 outfit_tags）
  （如：宽松黑色科技丝绒长袍，）
  same outfit,

④ 镜头变量（每个子图只改这里）：
（以下按 views 数组逐条列出）

  ── （view_id）: （label） ──
    view_angle: （view_angle 字段）
    shot_type: （shot_type 字段）
    expression: （expression 字段）
    pose: （pose 字段）
    background: （background 字段）
    合成完整提示词：
      nanobanana style, anime illustration, flat shading, clean lineart,
      （appearance_tags 逐条）
      （outfit_tags 逐条）
      same face, same outfit,
      （view_angle）, （shot_type）, （expression）, （pose）,
      （background）,
      masterpiece, best quality, highly detailed, sharp focus

⚠️ 重要：所有子图必须保持人物脸型、服装、发型完全一致
```

---

### 3.4 场景多角度图（Phase 2）

当你提供 `assets/scene-sheet.json` 后，输出如下指南：

---

**【场景多角度图 · Scene Sheet 操作指南】**

**前提**：Phase 1 已完成，element_id 已填入 JSON。

**在 LibTV 中操作：**

1. 在 LibTV Project 中新建 Session
2. 选择**生图模型**：**nanobanana**（固定）
3. 向 AI 发送以下消息：

```
【任务类型】场景多角度一致性图 · Scene Sheet
【项目名称】（项目名）
【生图模型】nanobanana（固定）
【核心原则】②③部分固定不变，只改④⑤变量；所有子图必须与全景锚点场景完全一致
【锚点使用】使用场景全景锚点图（element_id: 见各场景标注）保持布局/色调/道具一致

── 场景 （场景ID） （场景名） ──
【锚点 element_id】（填入的值）

① 风格锚点（固定）：
nanobanana style, cinematic illustration, detailed interior, atmospheric lighting,

② 场景类型定义（固定不变）：
（逐条列出 scene_type_tags）
  consistent environment, same room, same layout,

③ 固定道具与陈设（固定不变）：
（逐条列出 props_tags）
  same props, same furniture arrangement,

④ 镜头变量（每个子图只改这里）：
（以下按 views 数组逐条列出）

  ── （view_id）: （label） ──
    shot_type: （shot_type 字段）
    camera_angle: （camera_angle 字段）
    focus_subject: （focus_subject 字段）
    lighting: （lighting 字段）
    time_of_day: （time_of_day 字段）
    atmosphere: （atmosphere 字段）
    character_handling: （character_handling 字段）
    合成完整提示词：
      nanobanana style, cinematic illustration, detailed interior, atmospheric lighting,
      （scene_type_tags 逐条）
      （props_tags 逐条）
      same props, same furniture arrangement,
      （shot_type）, （camera_angle）, focusing on （focus_subject）,
      （lighting）, （time_of_day）, （atmosphere）,
      （character_handling）,
      masterpiece, best quality, highly detailed, sharp focus, rich textures

⚠️ 重要：所有子图必须保持场景布局、道具陈设、光线色调完全一致
```

---

### 3.5 分镜批量视频

当你提供分镜脚本或 `02-storyboard-script.md` 路径后，输出如下指南：

---

**【分镜批量视频 · 操作指南】**

**前提**：阶段一+二已完成，角色和场景的 element_id 均已填入资产注册表。

**在 LibTV 中操作：**

1. 在 LibTV Project 中新建 Session
2. 选择**视频模型**：**Kling O1**（推荐）或 **Wan 2.6**
3. 向 AI 发送以下消息：

```
【任务类型】分镜批量视频生成
【项目名称】（项目名）
【总时长】约（总秒数）秒
【视频模型】Kling O1（或 Wan 2.6）
【画面比例】（16:9 或 9:16）
【单镜头时长】（3-5）秒

【角色主体库】
（从资产注册表读取，逐角色列出）
  C001 （角色名） | element_id: （element_id）
  C002a/b/c（变体）| element_id: （各变体 element_id）

【场景参考库】
  S001 （场景名） | element_id: （element_id）
  S002 ...

【分镜脚本（逐镜头视频生成）】

（逐镜头列出，格式如下：）

镜头01（00:00-00:05）
| 全景 | 固定镜头 | 时长：5s
  画面：（分镜描述）
  台词：（如有）
  音效：（如有）

镜头02（00:05-00:10）
| 中景 | 推镜头 | 时长：5s
  画面：（分镜描述）
  主体：C001
  场景：S001
  ...

【转场说明】
（如有转场，列出）
```

**注意**：
- 每个镜头单独生成，完成后手动剪辑合成
- 生成顺序：先角色近景 → 再场景全景 → 最后大全景
- 遇到镜头与预期不符 → 在 LibTV 中用「局部重绘」调整，不要重新生成整个镜头

---

## 四、JSON Spec 文件说明

LibTV 的 JSON Spec 是**结构化任务描述**，由 huage888 系统自动生成。

### 4.1 核心字段

| 字段 | 说明 |
|------|------|
| `task_type` | 任务类型（见下表） |
| `project.name` | 项目名称 |
| `characters[]` | 角色列表 |
| `scenes[]` | 场景列表 |
| `characters[].element_id` | **Phase 1 完成后必须填入** |
| `scenes[].element_id` | **Phase 1 完成后必须填入** |

### 4.2 task_type 总览

| task_type | 说明 | 阶段 |
|-----------|------|------|
| `character_front_view` | 角色正面图（锚点） | Phase 1 |
| `character_sheet` | 角色多角度图 | Phase 2 |
| `scene_establishing` | 场景全景图（锚点） | Phase 1 |
| `scene_sheet` | 场景多角度图 | Phase 2 |
| `storyboard_image_batch` | 分镜批量出图 | 分镜 |
| `storyboard_video_batch` | 分镜批量视频 | 分镜 |
| `image_to_video` | 图生视频 | 分镜 |

### 4.3 Phase 1 → Phase 2 流水线

```
Step 1: character_front_view → 返回 element_id → 填入 character_sheet
Step 2: character_sheet（引用 element_id）→ 多角度参考图

Step 3: scene_establishing → 返回 element_id → 填入 scene_sheet
Step 4: scene_sheet（引用 element_id）→ 多角度参考图
```

**element_id 填入规则**：
- Phase 1 返回的图片 element_id 填入 Phase 2 JSON 的对应字段
- 每个角色/场景独立 element_id，不可共享
- 大圣多变体（C002a/b/c）各自独立 element_id

---

## 五、操作检查清单

每次执行前，对照检查：

```
□ 已在 LibTV 新建 Project（命名为本项目名）
□ 生图任务选择了 nanobanana 模型
□ 视频任务选择了 Kling O1 或 Wan 2.6 模型
□ Phase 1 → element_id 已填入 Phase 2 JSON
□ 所有角色/场景的 element_id 均已填入资产注册表
□ 分镜脚本已与资产注册表对照，无遗漏角色/场景
□ 画面比例正确（9:16竖屏 或 16:9横屏）
□ 每个镜头单独生成，不要一次发多个镜头
□ 生成完成 → 下载到本地 → 更新资产注册表
```

---

## 六、常见问题

**Q：element_id 是什么？**
A：LibTV 中图片的唯一标识符。在画布中选中图片，右侧属性面板可看到 element_id。Phase 2 的多角度生成依赖它来保持一致性。

**Q：可以一次生成所有角色吗？**
A：可以，但建议逐角色生成以便检查质量。多个角色放在同一个 Session 里生成即可。

**Q：生成结果与预期不符怎么办？**
A：用 LibTV 的「局部重绘」或「元素替换」功能调整，不要重新生成整个图片。完全失败才重新生成。

**Q：nanobanana 模型找不到？**
A：在 LibTV 模型列表中搜索 "nanobanana" 或 "nano"。如果该模型不可用，联系项目负责人确认替代模型。
