# 漠玫视觉 MoMei Visual Agent · 实施计划 V1.0

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Claude Code 内实现漠玫视觉 Agent，上传生鲜实拍图后一键产出全平台电商规格的视觉资产（主图/详情页/海报）。

**Architecture:** 5 步流水线——品类分析 → 场景合成（Doubao-Seedream-4.5）→ 智能裁切（Fabric.js）→ 海报合成 → 详情页文案+HTML。推理层用 Qwen3-Max，生成层用 Doubao-Seedream-4.5。

**Tech Stack:** Claude Code Skill / TypeScript（Fabric.js） / Doubao-Seedream-4.5（baoyu-image-gen）/ Qwen3-Max / baoyu-markdown-to-html

**Reference:** `docs/plans/2026-04-02-mo-mei-visual-design.md`

---

## Phase 1 · MVP（单 SKU 完整流程跑通）

### Task 1: 创建 Skill 目录结构

**Files:**
- Create: `.claude/skills/mo-mei-visual/SKILL.md`
- Create: `.claude/skills/mo-mei-visual/prompts/` (空目录)
- Create: `.claude/skills/mo-mei-visual/scripts/` (空目录)
- Create: `.claude/skills/mo-mei-visual/references/` (空目录)

- [ ] **Step 1: 创建目录**

```bash
mkdir -p .claude/skills/mo-mei-visual/{prompts,scripts,references}
```

- [ ] **Step 2: 提交**

```bash
git add .claude/skills/mo-mei-visual/
git commit -m "feat(mo-mei-visual): create skill directory structure

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 2: 编写 SKILL.md 入口文件

**Files:**
- Create: `.claude/skills/mo-mei-visual/SKILL.md`

- [ ] **Step 1: 写入 SKILL.md**

```markdown
---
name: mo-mei-visual
description: 漠玫视觉 · 生鲜电商视觉资产生产 Agent。用户上传实拍图，一键产出全平台主图、详情页、海报。触发词：做主图、生成电商图、漠玫视觉。
---

# 漠玫视觉 MoMei Visual Agent

## 快速开始

### 输入格式

**方式一：自然语言**
```
上传实拍图 + 产品信息：
- 品名：墨西哥哈斯牛油果
- 品类：牛油果
- 产地：墨西哥米却肯州
- 核心卖点：奶油般绵密口感，油脂含量高达20%
- 规格：1kg / 2kg
- 价格：68-128元
```

**方式二：JSON**
```json
{
  "品名": "墨西哥哈斯牛油果",
  "品类": "avocado",
  "产地": "墨西哥米却肯州",
  "核心卖点": "奶油般绵密口感，油脂含量高达20%",
  "规格": "1kg / 2kg",
  "价格": "68-128元"
}
```

### 执行流程

```
Step 1: 品类分析
  · 读取 prompts/product-analysis.md
  · 调用 Qwen3-Max 分析品类和风格推荐
  · 输出：品类标签 + 场景关键词

Step 2: 场景合成
  · 读取对应场景 prompt（prompts/scene-*.md）
  · 调用 baoyu-image-gen（--provider doubao --ref <实拍图>）
  · 4 种场景各生成 1 张

Step 3: 智能裁切
  · 调用 scripts/smart-crop.ts
  · 基础图 → 全平台尺寸

Step 4: 海报合成
  · 调用 scripts/poster-compose.ts
  · 输出：横版 + 竖版

Step 5: 详情页文案 + HTML
  · 读取 prompts/detail-copy.md
  · 调用 Qwen3-Max 生成详情页内容
  · 调用 baoyu-markdown-to-html 输出 HTML
```

### 输出目录

```
output/<slug>/
├── main-taobao-1:1.png      # 淘宝 800×800
├── main-taobao-3:4.png      # 淘宝 800×1066
├── main-jd-1:1.png          # 京东 800×800
├── main-pdd-1:1.png         # 拼多多 800×800
├── main-douyin-9:16.png    # 抖音 1080×1920
├── poster-h.png             # 横版海报 1920×800
├── poster-v.png             # 竖版海报 1080×1920
└── index.html               # 详情页
```

## Prompt 文件

| 文件 | 用途 |
|------|------|
| `prompts/scene-minimal.md` | 极简净色场景 |
| `prompts/scene-origin.md` | 原产地场景 |
| `prompts/scene-lifestyle.md` | 生活场景代入 |
| `prompts/scene-道具.md` | 极简+精致道具场景 |
| `prompts/product-analysis.md` | 品类分析与风格推荐 |
| `prompts/detail-copy.md` | 详情页文案生成 |
| `prompts/poster-overlay.md` | 海报合成 prompt |

## 脚本

| 脚本 | 用途 |
|------|------|
| `scripts/smart-crop.ts` | 智能裁切（Fabric.js） |
| `scripts/poster-compose.ts` | 海报合成（Fabric.js） |

## 参考文档

| 文件 | 内容 |
|------|------|
| `references/brand-colors.md` | 品牌色彩规范 |
| `references/platform-specs.md` | 全平台尺寸规格 |
| `references/style-guide.md` | 场景风格详细说明 |
```

- [ ] **Step 2: 提交**

```bash
git add .claude/skills/mo-mei-visual/SKILL.md
git commit -m "feat(mo-mei-visual): add SKILL.md entry point

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 3: 编写品牌约束参考文档

**Files:**
- Create: `.claude/skills/mo-mei-visual/references/brand-colors.md`
- Create: `.claude/skills/mo-mei-visual/references/platform-specs.md`
- Create: `.claude/skills/mo-mei-visual/references/style-guide.md`

- [ ] **Step 1: brand-colors.md**

```markdown
# 漠玫品牌色彩体系

> 来源：`docs/plans/2026-03-29-momo-healthy-food-ecommerce-design.md`

## 主色

| 角色 | 色名 | Hex | 用途 |
|------|------|-----|------|
| 主色 | 漠玫绿 | `#2E7D32` | 品牌标识、CTA 按钮、主要链接 |
| 辅色 | 牛油果绿 | `#8BC34A` | 分类标签、hover 状态、装饰元素 |
| 背景 | 米白 | `#FDFBF7` | 全站背景，替代纯白 |
| 强调 | 暖金 | `#D4A853` | 特价标签、重要提示、VIP 高亮 |
| 正文 | 墨色 | `#1A1A1A` | 正文标题，深黑非纯黑 |
| 次要文字 | 灰调 | `#6B6B6B` | 副标题、说明文字 |

## 禁止色

- 荧光绿
- 薄荷绿（微商感）
- 纯黑 `#000000`（正文用墨色 `#1A1A1A`）

## 字体规范

- 标题：思源宋体（Noto Serif SC）Bold
- 正文：思源黑体（Noto Sans SC）Regular
- 禁止：华文行楷、方正粗宋、圆润儿童字体

## 摄影规范

- Apple 产品摄影感，自然光，浅景深
- 主体占画面 60-70%，留白 30%+
- 食材本身是主角，禁止过度 PS
- 禁止：emoji 堆砌、过度锐化、微商感滤镜
```

- [ ] **Step 2: platform-specs.md**

```markdown
# 全平台电商尺寸规格

## 主图

| 平台 | 图片类型 | 尺寸(px) | 比例 | 文件名规范 |
|------|---------|----------|------|-----------|
| 淘宝/天猫 | 主图 | 800×800 | 1:1 | `main-taobao-1:1.png` |
| 淘宝/天猫 | 长图 | 800×1066 | 3:4 | `main-taobao-3:4.png` |
| 京东 | 白底主图 | 800×800 | 1:1 | `main-jd-1:1.png` |
| 京东 | 副图 | 480×480 | 1:1 | `main-jd-sub.png` |
| 拼多多 | 主图 | 800×800 | 1:1 | `main-pdd-1:1.png` |
| 拼多多 | 长图 | 800×1200 | 2:3 | `main-pdd-3:4.png` |
| 抖音小店 | 主图 | 800×1066 | 3:4 | `main-douyin-3:4.png` |
| 抖音小店 | 竖版主图 | 1080×1920 | 9:16 | `main-douyin-9:16.png` |

## 海报

| 类型 | 尺寸(px) | 比例 | 用途 |
|------|----------|------|------|
| 横版海报 | 1920×800 | 2.4:1 | 公众号、官网 |
| 竖版海报 | 1080×1920 | 9:16 | 朋友圈、抖音 |

## 裁切规则

1. 主体水果必须在安全区内（边距 ≥ 10%）
2. 主体中心点落在画面中心 ± 15%
3. 优先保留上方空间（文字/标签常在顶部）
```

- [ ] **Step 3: style-guide.md**

```markdown
# 场景风格详细说明

## 场景 A：极简净色（minimal）

**适用：** 京东白底图、淘宝主图

**画面描述：**
- 背景：浅米白色 `#FDFBF7` 或浅灰色
- 光线：自然侧光，柔和阴影
- 主体：水果居中，占画面 60-70%
- 留白：30%+，无任何道具
- 质感：Apple 产品摄影感，干净利落

**禁止：** 任何装饰道具、文字水印、过度锐化

---

## 场景 B：原产地场景（origin）

**适用：** 淘宝详情页 Banner、产地故事图

**画面描述：**
- 背景：果园/农场/远山轮廓，浅景深虚化
- 光线：清晨薄雾感，自然光
- 主体：水果在前景，占画面 50-60%
- 氛围：强调"源头直采"故事感
- 季节：对应产地的典型季节氛围

**品类适配：**
- 牛油果：墨西哥米却肯州果园、棕榈树背景
- 榴莲：泰国/越南榴莲园、芭蕉叶
- 蓝莓：智利/云南蓝莓灌木丛

---

## 场景 C：生活场景代入（lifestyle）

**适用：** 抖音、小红书、朋友圈

**画面描述：**
- 背景：现代厨房/餐桌/阳台场景
- 光线：自然窗光，温暖氛围
- 主体：水果在画面中央偏下
- 道具：餐盘、刀叉、亚麻布桌布、咖啡杯
- 代入感：让消费者想象"我买了之后的生活"

**禁止：** 过于凌乱、过于精致失真

---

## 场景 D：极简+精致道具（道具）

**适用：** 品牌官网、公众号、高端宣传

**画面描述：**
- 背景：净色或极简纹理（白色大理石、木纹）
- 光线：专业布光，质感强烈
- 主体：水果 + 1-2 个精致道具
- 道具类型：
  - 牛油果：原木砧板、刀叉餐具、牛油果切面
  - 榴莲：热带水果刀、芭蕉叶
  - 蓝莓：白色瓷盘、玻璃杯、酸奶
- 整体调性：克制、高级、有呼吸感

**禁止：** 过于热闹的道具组合、颜色过于丰富
```

- [ ] **Step 4: 提交**

```bash
git add .claude/skills/mo-mei-visual/references/
git commit -m "feat(mo-mei-visual): add brand colors, platform specs, style guide references

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 4: 编写四种场景 Prompt

**Files:**
- Create: `.claude/skills/mo-mei-visual/prompts/scene-minimal.md`
- Create: `.claude/skills/mo-mei-visual/prompts/scene-origin.md`
- Create: `.claude/skills/mo-mei-visual/prompts/scene-lifestyle.md`
- Create: `.claude/skills/mo-mei-visual/prompts/scene-daoju.md`

- [ ] **Step 1: scene-minimal.md**

```markdown
# 极简净色场景 Prompt

## 模板

```
将实拍图中的[品类]作为主体，
合成到浅米白色背景中（#FDFBF7），
Apple产品摄影风格，
自然侧光，柔和阴影，
主体居中，占画面60-70%，
留白30%以上，
无任何装饰道具。

品牌调性：克制·精致·有呼吸感。

禁止：emoji、文字水印、过度锐化、微商感滤镜、荧光色、卡通风格。
```

## 品类占位符填充规则

| 品类 | 填入 |
|------|------|
| avocado | 牛油果 |
| durian | 榴莲 |
| blueberry | 蓝莓 |
| other | [从实拍图识别的具体品类] |

## 示例输出（牛油果）

```
将实拍图中的牛油果作为主体，
合成到浅米白色背景中（#FDFBF7），
Apple产品摄影风格，
自然侧光，柔和阴影，
主体居中，占画面60-70%，
留白30%以上，
无任何装饰道具。

品牌调性：克制·精致·有呼吸感。

禁止：emoji、文字水印、过度锐化、微商感滤镜、荧光色、卡通风格。
```
```

- [ ] **Step 2: scene-origin.md**

```markdown
# 原产地场景 Prompt

## 模板

```
将实拍图中的[品类]作为主体，
合成到[产地名]的农场/果园氛围中，
自然光，清晨薄雾感，浅景深，
背景为远山或果树轮廓，地面有浅景深虚化，
主体在前景，占画面50-60%。

漠玫品牌调性：克制·精致·有呼吸感，
强调"源头直采"故事感。

禁止：emoji、文字水印、过度锐化、微商感滤镜、荧光色。
```

## 品类产地适配表

| 品类 | 产地 | 背景描述 |
|------|------|---------|
| 牛油果 | 墨西哥米却肯州 | 墨西哥高原果园、棕榈树、牛油果树 |
| 牛油果 | 秘鲁 | 安第斯山脉脚下的绿色丘陵 |
| 榴莲 | 泰国尖竹汶府 | 热带榴莲园、芭蕉叶、金枕榴莲树 |
| 榴莲 | 越南林同省 | 高山榴莲园、晨雾、热带植被 |
| 蓝莓 | 智利 | 南美高原蓝莓灌木丛、蓝天背景 |
| 蓝莓 | 云南 | 云南高原蓝莓大棚、山脉背景 |

## 示例输出（榴莲-泰国）

```
将实拍图中的榴莲作为主体，
合成到泰国尖竹汶府的热带榴莲园氛围中，
自然光，清晨薄雾感，浅景深，
背景为热带果树轮廓，地面有浅景深虚化，
主体在前景，占画面50-60%。

漠玫品牌调性：克制·精致·有呼吸感，
强调"源头直采"故事感。

禁止：emoji、文字水印、过度锐化、微商感滤镜、荧光色。
```
```

- [ ] **Step 3: scene-lifestyle.md**

```markdown
# 生活场景代入 Prompt

## 模板

```
将实拍图中的[品类]作为主体，
合成到现代简约风格的厨房/餐桌场景中，
自然窗光，温暖氛围，
[品类]放置在画面中央偏下，
配套道具：[品类对应道具]，
整体氛围：让人想象"购买后的美好生活"。

漠玫品牌调性：克制·精致·有呼吸感，
自然光，浅景深，主体突出。

禁止：场景过于凌乱、emoji、文字水印、过度锐化、微商感滤镜。
```

## 品类道具适配表

| 品类 | 推荐道具 |
|------|---------|
| 牛油果 | 白色瓷盘、原木砧板、银色刀叉、亚麻布桌布、咖啡杯 |
| 榴莲 | 木质砧板、热带水果刀、芭蕉叶、白色餐盘 |
| 蓝莓 | 白色瓷碗、透明玻璃杯、酸奶、白色亚麻布、浆果勺 |
| 其他 | 白色餐盘、简洁餐具、亚麻布桌布 |

## 示例输出（蓝莓）

```
将实拍图中的蓝莓作为主体，
合成到现代简约风格的白色厨房场景中，
自然窗光，温暖氛围，
蓝莓放置在白色瓷碗中，画面中央偏下，
配套道具：透明玻璃杯、原味酸奶、白色亚麻布桌布，
整体氛围：让人想象"购买后的美好健康生活"。

漠玫品牌调性：克制·精致·有呼吸感，
自然光，浅景深，主体突出。

禁止：场景过于凌乱、emoji、文字水印、过度锐化、微商感滤镜。
```
```

- [ ] **Step 4: scene-daoju.md**

```markdown
# 极简+精致道具场景 Prompt

## 模板

```
将实拍图中的[品类]作为主体，
放置在[背景材质]上，
Apple产品摄影风格，
专业布光，质感强烈，
[品类] + [精致道具1-2个]，
整体构图克制、高端、有呼吸感。

漠玫品牌调性：克制·精致·有呼吸感。

禁止：道具过多超过3个、emoji、文字水印、过度锐化、微商感滤镜、荧光色。
```

## 背景材质 & 道具适配表

| 品类 | 背景材质 | 精致道具 |
|------|---------|---------|
| 牛油果 | 白色大理石 / 原木 | 原木砧板 + 银色刀叉；或牛油果切面特写 |
| 榴莲 | 深色木质 / 黑石板 | 热带水果刀 + 芭蕉叶；或榴莲金黄果肉切面 |
| 蓝莓 | 白色大理石 / 浅木 | 白色瓷盘 + 银色浆果勺；或蓝莓切面特写 |
| 其他 | 白色大理石 | 白色瓷盘 + 简洁餐具 |

## 示例输出（牛油果）

```
将实拍图中的牛油果作为主体，
放置在白色大理石台面上，
Apple产品摄影风格，
专业布光，质感强烈，
牛油果 + 原木砧板 + 银色刀叉，
整体构图克制、高端、有呼吸感。

漠玫品牌调性：克制·精致·有呼吸感。

禁止：道具过多超过3个、emoji、文字水印、过度锐化、微商感滤镜、荧光色。
```
```

- [ ] **Step 5: 提交**

```bash
git add .claude/skills/mo-mei-visual/prompts/scene-*.md
git commit -m "feat(mo-mei-visual): add 4 scene prompts (minimal/origin/lifestyle/daoju)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 5: 编写品类分析与详情页文案 Prompt

**Files:**
- Create: `.claude/skills/mo-mei-visual/prompts/product-analysis.md`
- Create: `.claude/skills/mo-mei-visual/prompts/detail-copy.md`
- Create: `.claude/skills/mo-mei-visual/prompts/poster-overlay.md`

- [ ] **Step 1: product-analysis.md**

```markdown
# 品类分析与风格推荐 Prompt

## 输入

用户提供的：
- 实拍图路径
- 产品信息（品名/品类/产地/卖点/规格/价格）

## Prompt 模板

```
你是一个专注于生鲜电商的专业视觉顾问。

## 产品信息
- 品名：[品名]
- 品类：[品类]
- 产地：[产地]
- 核心卖点：[卖点]
- 规格：[规格]
- 价格：[价格区间]

## 任务

1. **品类识别**：确认品类是否正确，补充品类特征关键词
2. **风格推荐**：根据产品特性和目标平台，从以下4种场景中选择最合适的2-3种：
   - minimal（极简净色）：适合京东白底图、淘宝主图
   - origin（原产地场景）：适合产地故事、详情页Banner
   - lifestyle（生活场景）：适合抖音、小红书、朋友圈
   - daoju（精致道具）：适合品牌官网、高端宣传
3. **产地关键词**：提取适合AI绘图使用的产地氛围描述词
4. **专属道具**：推荐最适合该品类的拍摄道具
5. **色彩建议**：从品牌色彩体系中选择最匹配的辅助色

## 输出格式

```json
{
  "品类确认": "avocado/durian/blueberry/other",
  "推荐场景": ["minimal", "lifestyle"],
  "产地关键词": "描述词1, 描述词2, 描述词3",
  "专属道具": "道具1, 道具2",
  "色彩建议": "#主色  #辅助色"
}
```
```

- [ ] **Step 2: detail-copy.md**

```markdown
# 详情页文案生成 Prompt

## 输入

- 品类信息
- 产地信息
- 核心卖点

## Prompt 模板

```
你是一个专注于高端生鲜电商的专业内容编辑，擅长撰写既专业又有温度的产品详情页文案。

## 产品信息
- 品名：[品名]
- 品类：[品类]
- 产地：[产地]
- 核心卖点：[卖点]
- 规格：[规格]
- 价格：[价格区间]

## 任务

为该产品生成详情页的所有文案模块，每个模块100-200字：

1. **产地溯源**：产地故事，强调"源头直采"的专业感和品质保障
2. **核心卖点**：3-5条，每条一句话，带emoji图标
3. **规格选择说明**：不同规格的适用场景推荐
4. **营养成分**：根据品类输出常见营养数据（如有具体数据最好，无则基于常识输出代表性数据并注明"以实测为准"）
5. **选购指南**：如何判断成熟度、如何挑选优质产品
6. **储存方法**：最佳储存温度、储存时长建议
7. **食用建议**：推荐食用方式、食谱搭配

## 风格约束

- 语气：专业但亲切，像朋友分享，不是广告
- 禁止：极限词（最好/第一/全网最低）、无来源的"研究表明"
- SEO：在H2、小标题中自然融入品类关键词
- CTA：引导关注公众号，不直接强推购买
- 品牌植入：在结尾自然推荐漠玫，不超过2处

## 输出格式

Markdown格式，含H2标题和正文。
```

- [ ] **Step 3: poster-overlay.md**

```markdown
# 海报合成 Prompt

## 横版海报 Prompt（公众号/官网）

```
设计一张横版品牌海报，尺寸1920×800px。

结构：
- 背景：虚化的生鲜产品摄影图（模糊度20%），作为氛围底图
- 底部色块：漠玫绿 #2E7D32，高度200px，透明度85%
- 品名：居中，白色，72px
- 副标题：居中，米白色 #FDFBF7，36px
- 右下角：品牌Logo + ©漠玫

风格：克制·精致·有呼吸感，Apple产品摄影质感。
```

## 竖版海报 Prompt（朋友圈/抖音）

```
设计一张竖版品牌海报，尺寸1080×1920px。

结构：
- 背景：全出血的生鲜产品摄影图
- 顶部渐变遮罩：黑色→透明，透明度40%
- 品名：居中偏上，白色，80px
- 核心卖点：居中，米白色 #FDFBF7，36px
- 底部色块：漠玫绿 #2E7D32，高度160px
- 价格：底部色块上，暖金色 #D4A853，48px
- 底部：品牌Logo

风格：克制·精致·有呼吸感，Apple产品摄影质感。
```
```

- [ ] **Step 4: 提交**

```bash
git add .claude/skills/mo-mei-visual/prompts/product-analysis.md .claude/skills/mo-mei-visual/prompts/detail-copy.md .claude/skills/mo-mei-visual/prompts/poster-overlay.md
git commit -m "feat(mo-mei-visual): add product analysis, detail copy, poster prompts

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 6: 编写智能裁切脚本（Fabric.js）

**Files:**
- Create: `.claude/skills/mo-mei-visual/scripts/smart-crop.ts`
- Modify: `.claude/skills/mo-mei-visual/SKILL.md`（补充脚本调用说明）

**Prerequisite:** `npm install --save-dev fabric` 或 `bun add -d fabric`（在 vault 根目录或 skill 目录执行）

- [ ] **Step 1: 安装依赖**

```bash
cd /Users/huage/Obsidian Vault
bun add -d fabric 2>/dev/null || npm install --save-dev fabric
```

- [ ] **Step 2: 编写 smart-crop.ts**

```typescript
#!/usr/bin/env bun
/**
 * smart-crop.ts
 * 智能裁切脚本：将基础合成图裁切为全平台尺寸
 *
 * 用法：
 *   bun scripts/smart-crop.ts <input-image> <output-dir>
 *   bun scripts/smart-crop.ts avocado-main.png output/avocado/
 *
 * 输出：
 *   main-taobao-1:1.png    (800x800)
 *   main-taobao-3:4.png   (800x1066)
 *   main-jd-1:1.png       (800x800)
 *   main-pdd-1:1.png      (800x800)
 *   main-pdd-3:4.png      (800x1200)
 *   main-douyin-3:4.png   (800x1066)
 *   main-douyin-9:16.png  (1080x1920)
 */

import { Canvas, FabricImage, loadSVGFromString } from 'fabric';
import { readFileSync, mkdirSync, existsSync } from 'fs';
import { join, basename, extname } from 'path';

interface CropSpec {
  name: string;
  width: number;
  height: number;
  mode: 'center' | 'top' | 'bottom';
}

const PLATFORM_SPECS: CropSpec[] = [
  { name: 'main-taobao-1:1',  width: 800,  height: 800,  mode: 'center' },
  { name: 'main-taobao-3:4',  width: 800,  height: 1066, mode: 'center' },
  { name: 'main-jd-1:1',     width: 800,  height: 800,  mode: 'center' },
  { name: 'main-pdd-1:1',    width: 800,  height: 800,  mode: 'center' },
  { name: 'main-pdd-3:4',    width: 800,  height: 1200, mode: 'center' },
  { name: 'main-douyin-3:4', width: 800,  height: 1066, mode: 'top' },
  { name: 'main-douyin-9:16',width: 1080, height: 1920, mode: 'top' },
];

async function smartCrop(inputPath: string, outputDir: string): Promise<void> {
  if (!existsSync(inputPath)) {
    throw new Error(`输入图片不存在: ${inputPath}`);
  }

  mkdirSync(outputDir, { recursive: true });
  console.log(`📥 读取图片: ${inputPath}`);

  // 加载输入图片
  const img = await Canvas.fromURL(`file://${resolve(inputPath)}`);

  // 加载为 FabricImage
  const fabricImg = await FabricImage.fromURL(`file://${resolve(inputPath)}`);
  const inputWidth = fabricImg.width || 1024;
  const inputHeight = fabricImg.height || 1024;
  console.log(`📐 原图尺寸: ${inputWidth}×${inputHeight}`);

  // 计算主体中心（假设主体在画面中心，这是默认假设）
  const centerX = inputWidth / 2;
  const centerY = inputHeight / 2;

  for (const spec of PLATFORM_SPECS) {
    const { name, width, height, mode } = spec;
    const canvas = new Canvas(`${name}`, { width, height });

    // 计算裁切区域
    let cropX: number;
    let cropY: number;

    if (mode === 'center') {
      // 中心裁切：优先保证主体完整
      cropX = Math.max(0, centerX - width / 2);
      cropY = Math.max(0, centerY - height / 2);
    } else if (mode === 'top') {
      // 顶部对齐：保留上方空间（文字/标签常在顶部）
      cropX = Math.max(0, centerX - width / 2);
      cropY = 0;
    } else {
      cropY = Math.max(0, inputHeight - height);
      cropX = Math.max(0, centerX - width / 2);
    }

    // 计算缩放比例，保证填满目标尺寸
    const scaleX = width / Math.min(width, inputWidth);
    const scaleY = height / Math.min(height, inputHeight);
    const scale = Math.max(scaleX, scaleY);

    // 创建裁切后的图片
    const croppedImg = await FabricImage.fromURL(`file://${resolve(inputPath)}`);
    croppedImg.scale(scale);
    croppedImg.set({
      left: -cropX * scale,
      top: -cropY * scale,
    });

    canvas.add(cropedImg);
    canvas.renderAll();

    const outputPath = join(outputDir, `${name}.png`);
    const dataUrl = canvas.toDataURL({ format: 'png', quality: 1 });
    // 将 dataUrl 保存为文件
    const base64 = dataUrl.replace(/^data:image\/png;base64,/, '');
    writeFileSync(outputPath, Buffer.from(base64, 'base64'));
    console.log(`✅ 已生成: ${name}.png (${width}×${height})`);
  }
}

// 简单路径解析（避免 import { resolve } from 'path' 的问题）
function resolve(p: string): string {
  if (p.startsWith('/')) return p;
  return join(process.cwd(), p);
}

const inputPath = process.argv[2];
const outputDir = process.argv[3];

if (!inputPath || !outputDir) {
  console.error('用法: bun scripts/smart-crop.ts <input-image> <output-dir>');
  process.exit(1);
}

smartCrop(inputPath, outputDir)
  .then(() => console.log('🎉 全部完成!'))
  .catch(err => { console.error('❌ 错误:', err.message); process.exit(1); });
```

- [ ] **Step 3: 验证脚本语法**

```bash
cd /Users/huage/Obsidian Vault
npx tsc --noEmit .claude/skills/mo-mei-visual/scripts/smart-crop.ts 2>&1 | head -20
```

> 如果有类型错误，手动修正 TS 语法（Fabric.js 的 TS 类型有时不完整，可加 `// @ts-ignore`）

- [ ] **Step 4: 提交**

```bash
git add .claude/skills/mo-mei-visual/scripts/smart-crop.ts
git commit -m "feat(mo-mei-visual): add smart-crop.ts with Fabric.js

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 7: Phase 1 端到端验证

**Files:**
- Test: 用一张真实的牛油果/榴莲/蓝莓实拍图跑完整流程
- Verify: 确认输出目录生成所有规格图片

- [ ] **Step 1: 准备测试素材**

```bash
# 创建一个测试用的模拟输入（实际测试时替换为真实图片）
mkdir -p .claude/skills/mo-mei-visual/test-fixtures
# 注：实际测试需要用户提供一张真实水果实拍图
```

- [ ] **Step 2: 手动跑通全流程（模拟）**

按照 SKILL.md 的执行流程，用 Qwen3-Max + baoyu-image-gen 手动跑一遍：

```
1. 调用 Qwen3-Max → 产品分析 prompt → 输出推荐场景
2. 调用 baoyu-image-gen → 4场景各生成1张
3. 调用 smart-crop.ts → 裁切为全平台尺寸
4. 检查输出目录 → 确认文件完整
```

- [ ] **Step 3: 更新 SKILL.md 执行流程为实际可用的完整版本**

- [ ] **Step 4: 提交 Phase 1 完成**

```bash
git add -A
git commit -m "feat(mo-mei-visual): Phase 1 MVP complete - full pipeline verified

- SKILL.md entry point
- 4 scene prompts (minimal/origin/lifestyle/daoju)
- Product analysis, detail copy, poster prompts
- Smart crop script (Fabric.js)
- References (brand colors, platform specs, style guide)
- End-to-end pipeline verified

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Phase 2 · 完整资产产出

### Task 8: 海报合成脚本（Fabric.js）

**Files:**
- Create: `.claude/skills/mo-mei-visual/scripts/poster-compose.ts`

- [ ] **Step 1: 编写 poster-compose.ts**

```typescript
#!/usr/bin/env bun
/**
 * poster-compose.ts
 * 海报合成脚本：基础图 + 品牌文字 + 色块 = 品牌海报
 *
 * 用法：
 *   bun scripts/poster-compose.ts <base-image> <product-name> <tagline> <output-dir>
 *
 * 示例：
 *   bun scripts/poster-compose.ts avocado-main.png "墨西哥哈斯牛油果" "奶油般绵密口感" output/
 */

interface PosterSpec {
  name: string;
  width: number;
  height: number;
  layout: 'landscape' | 'portrait';
}

const POSTER_SPECS: PosterSpec[] = [
  { name: 'poster-h', width: 1920, height: 800, layout: 'landscape' },
  { name: 'poster-v', width: 1080, height: 1920, layout: 'portrait' },
];

async function composePoster(
  baseImagePath: string,
  productName: string,
  tagline: string,
  outputDir: string
): Promise<void> {
  const { Canvas, FabricImage, Rect, IText, Gradient } = await import('fabric');

  for (const spec of POSTER_SPECS) {
    const canvas = new Canvas(spec.name, {
      width: spec.width,
      height: spec.height,
    });

    // 1. 添加背景图（填满，虚化效果通过覆盖半透明色实现）
    const bg = await FabricImage.fromURL(`file://${baseImagePath}`);
    bg.scale(Math.max(spec.width / bg.width!, spec.height / bg.height!));
    bg.set({
      left: (spec.width - bg.width! * bg.scaleX!) / 2,
      top: (spec.height - bg.height! * bg.scaleY!) / 2,
    });
    canvas.add(bg);

    // 2. 添加半透明叠加（虚化感 + 品牌色）
    const overlay = new Rect({
      left: 0, top: 0,
      width: spec.width,
      height: spec.height,
      fill: new Gradient({
        type: 'linear',
        gradientUnits: 'pixels',
        coords: spec.layout === 'landscape'
          ? { x1: 0, y1: 0, x2: 0, y2: spec.height }
          : { x1: 0, y1: 0, x2: 0, y2: spec.height },
        colorStops: [
          { offset: 0, color: 'rgba(0,0,0,0)' },
          { offset: spec.layout === 'landscape' ? 0.6 : 0.85, color: 'rgba(0,0,0,0.3)' },
          { offset: 1, color: '#2E7D32' },
        ],
      }),
    });
    canvas.add(overlay);

    // 3. 添加品名
    const nameText = new IText(productName, {
      left: spec.width / 2,
      top: spec.layout === 'landscape' ? spec.height - 280 : spec.height * 0.35,
      fontSize: spec.layout === 'landscape' ? 72 : 80,
      fontFamily: 'Noto Serif SC',
      fontWeight: 'bold',
      fill: '#FFFFFF',
      originX: 'center',
      originY: 'center',
      textAlign: 'center',
    });
    canvas.add(nameText);

    // 4. 添加副标题
    const taglineText = new IText(tagline, {
      left: spec.width / 2,
      top: spec.layout === 'landscape' ? spec.height - 200 : spec.height * 0.45,
      fontSize: spec.layout === 'landscape' ? 36 : 36,
      fontFamily: 'Noto Sans SC',
      fill: '#FDFBF7',
      originX: 'center',
      originY: 'center',
      textAlign: 'center',
    });
    canvas.add(taglineText);

    // 5. 添加品牌水印
    const brandText = new IText('© 漠玫 Mo Mei', {
      left: spec.width - 20,
      top: spec.height - 30,
      fontSize: 16,
      fontFamily: 'Noto Sans SC',
      fill: 'rgba(255,255,255,0.7)',
      originX: 'right',
      originY: 'bottom',
      textAlign: 'right',
    });
    canvas.add(brandText);

    canvas.renderAll();

    const outputPath = `${outputDir}/${spec.name}.png`;
    const dataUrl = canvas.toDataURL({ format: 'png', quality: 1 });
    const base64 = dataUrl.replace(/^data:image\/png;base64,/, '');
    writeFileSync(outputPath, Buffer.from(base64, 'base64'));
    console.log(`✅ 已生成: ${spec.name}.png`);
  }
}

const args = process.argv.slice(2);
if (args.length < 4) {
  console.error('用法: bun scripts/poster-compose.ts <base-image> <product-name> <tagline> <output-dir>');
  process.exit(1);
}

composePoster(args[0], args[1], args[2], args[3])
  .then(() => console.log('🎉 海报合成完成!'))
  .catch(err => { console.error('❌ 错误:', err.message); process.exit(1); });
```

- [ ] **Step 2: 提交**

```bash
git add .claude/skills/mo-mei-visual/scripts/poster-compose.ts
git commit -m "feat(mo-mei-visual): add poster-compose.ts with brand overlay

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 9: 全平台尺寸覆盖 + Phase 2 端到端验证

**Files:**
- Modify: `.claude/skills/mo-mei-visual/scripts/smart-crop.ts`（补充 480×480 和 2:3 比例）
- Modify: `.claude/skills/mo-mei-visual/SKILL.md`（补充 Phase 2 执行说明）

- [ ] **Step 1: 更新 smart-crop.ts 的尺寸表**

在 `PLATFORM_SPECS` 数组中添加：
```typescript
{ name: 'main-jd-sub',  width: 480,  height: 480,  mode: 'center' },  // 京东副图
{ name: 'main-pdd-3:4', width: 800,  height: 1200, mode: 'center' },  // 拼多多长图
```

- [ ] **Step 2: 更新 SKILL.md 添加 Phase 2 说明**

- [ ] **Step 3: 端到端验证**

用真实图片跑 Phase 2 完整流程（主图 + 海报 + 详情页文案）

- [ ] **Step 4: 提交 Phase 2**

```bash
git add -A
git commit -m "feat(mo-mei-visual): Phase 2 complete - poster synthesis + full platform coverage

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Phase 3 · 规模化能力

### Task 10: 批量处理模式

**Files:**
- Create: `.claude/skills/mo-mei-visual/scripts/batch-process.ts`
- Modify: `.claude/skills/mo-mei-visual/SKILL.md`

- [ ] **Step 1: 编写 batch-process.ts**

```typescript
#!/usr/bin/env bun
/**
 * batch-process.ts
 * 批量处理多个 SKU
 *
 * 用法：
 *   bun scripts/batch-process.ts <manifest.json> <input-images-dir> <output-dir>
 *
 * manifest.json 格式：
 * [
 *   { "slug": "avocado-hass", "name": "墨西哥哈斯牛油果", "image": "avocado.jpg", ... },
 *   { "slug": "durian-monthong", "name": "泰国金枕榴莲", "image": "durian.jpg", ... }
 * ]
 */
```

- [ ] **Step 2: 提交**

---

### Task 11: 增量追加模式 + 素材库

**Files:**
- Create: `.claude/skills/mo-mei-visual/scripts/incremental-add.ts`
- Create: `.claude/skills/mo-mei-visual/assets/`（品牌元素目录）

- [ ] **Step 1: 创建品牌素材目录结构**

```bash
mkdir -p .claude/skills/mo-mei-visual/assets/{fonts,logos,watermarks}
```

- [ ] **Step 2: 提交**

---

## 实施顺序建议

```
Phase 1（MVP，最快跑通）：
  Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7

Phase 2（完整产出）：
  Task 8 → Task 9

Phase 3（规模化）：
  Task 10 → Task 11
```

---

## 验收标准

### Phase 1 验收

- [ ] `SKILL.md` 可被 Claude Code 识别并加载
- [ ] 4 种场景 prompt 可被 baoyu-image-gen 正确调用
- [ ] `smart-crop.ts` 可将 1024×1024 图裁切为 7 种尺寸
- [ ] 用真实水果图片跑通 Step 1-3 全流程
- [ ] 输出目录包含：7 种主图尺寸文件

### Phase 2 验收

- [ ] `poster-compose.ts` 生成横版 + 竖版海报
- [ ] 详情页文案生成质量可读
- [ ] HTML 排版在浏览器中正常显示
- [ ] 全流程（主图 + 海报 + 详情页）可一键完成

### Phase 3 验收

- [ ] `--batch` 支持批量处理 3+ SKU
- [ ] `--add-poster-style` 支持追加指定风格
- [ ] 品牌 Logo/水印素材库已建立
```

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-02-mo-mei-visual-implementation.md`.**

Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
