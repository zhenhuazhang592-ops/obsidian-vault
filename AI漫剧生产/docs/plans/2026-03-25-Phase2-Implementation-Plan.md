# AI Short Drama Studio — 第二阶段优化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将13个Skill升级为21个Skill，引入CDP JSON Schema、ID化引用、道具系统、增量机制，在第02集生产前完成全部P0优化

**Architecture:** 以 Skill 文件为核心交付物，每个优化项作为一个独立任务单元；Schema规范作为共享契约文件；所有Skill遵循统一的CDP数据结构

**Tech Stack:** Markdown(Skill文件) + YAML(Schema规范) + Obsidian Vault

---

## 一、文件结构总览

### 新增文件（8个Skill + 1个Schema）

```
AI漫剧生产/skills/
+ manzhou-cdp-schema.md        # CDP JSON Schema 规范文件（共享契约）
+ manzhou-concept.md            # A1 剧本创意Skill
+ manzhou-outline.md            # A2 剧本大纲Skill
+ manzhou-item-generator.md     # B3 道具生成Skill
+ manzhou-incremental.md        # E1 增量追加Skill
+ manzhou-polish.md             # E2 润色工具Skill
+ manzhou-cost-estimator.md     # E3 成本估算Skill

AI漫剧生产/docs/plans/
+ 2026-03-25-Phase2-Optimization-Plan.md  # 优化方案（已创建）
```

### 改造文件（10个现有Skill升级版本）

```
AI漫剧生产/skills/
  manzhou-master.md              # 2.0.0 - 增加@引用/CDP Schema
  manzhou-ip-parser.md           # 2.0.0 - 增加aliases别名系统
  manzhou-script.md              # 2.0.0 - @引用机制/台词规范
  manzhou-storyboard.md          # 3.0.0 - 固定时长/ID引用/多Shot
  manzhou-visual-style.md         # 2.0.0 - 11种预设完整描述
  manzhou-character-consistency.md # 2.0.0 - aliases别名系统
  manzhou-bgm.md                 # 2.0.0 - BPM参数
  manzhou-sfx.md                 # 2.0.0 - 精确时间戳
  manzhou-audio.md               # 2.0.0 - 适配新Schema
  manzhou-safety.md              # 2.0.0 - 适配新Schema
```

---

## 二、任务分解（共5个阶段）

---

### 阶段一：Schema契约层（P0前置，必须先完成）

---

#### 任务 1：制定 CDP JSON Schema 规范文件

**Files:**
- Create: `AI漫剧生产/skills/manzhou-cdp-schema.md`

- [ ] **Step 1: 创建 manzhou-cdp-schema.md**

```markdown
# Manzhou CDP JSON Schema v1.0

> 版本: 1.0.0
> 日期: 2026-03-25
> 来源: 联易方舟 CDP JSON Schema（逆向工程）
> 用途: 所有Skill输出的统一数据契约

---

## 一、顶层结构

```yaml
manzhouCDP:
  version: "1.0"
  format: "manzhou_comic_drama_package"
  meta: {}           # 项目元信息
  settings: {}       # 全局设置
  characters: []     # 角色库
  locations: []      # 场景库
  items: []          # 道具库（新增）
  episodes: []       # 分集数组
```

## 二、各模块Schema

### meta（项目元信息）

```yaml
meta:
  projectId: string      # UUID
  title: string         # 项目名
  totalEpisodes: number # 总集数
  currentEpisode: number # 当前处理集数
  createdAt: string      # ISO时间戳
  updatedAt: string      # ISO时间戳
  append: boolean       # 增量追加标志
```

### settings（全局设置）

```yaml
settings:
  targetPlatform: string   # douyin/kuaishou/bilibili
  aspectRatio: string       # 16:9 / 9:16 / 1:1
  stylePresetId: string    # anime / cn_anime / cn_3d / ink / cyber / us_comics / real / horror / pixar / shinkai / miyazaki
  shotDurationSec: number # 单镜头固定秒数（10/15/25）
  episodeDurationMin: number # 每集目标时长（分钟）
  textModel: string       # AI模型
  imageModel: string      # 生图模型
  videoModel: string      # 生视频模型
```

### characters（角色库）

```yaml
characters:
  - id: string           # char_01, char_02...（ID化引用）
    name: string         # 角色中文名
    aliases: []         # 别名数组（新增！）
    gender: string       # male/female/other
    ageRange: string     # "25-30" / "40左右"
    appearance: string   # 外貌描述（用于生图Prompt）
    clothing: string     # 服饰描述
    persona: string      # 人设/性格
    dnaAnchors:          # DNA锚点（manzhou-character-consistency输出）
      - type: string     # 配饰/外貌/服装
        description: string
    referenceImage: string # 参考图路径
```

### locations（场景库）

```yaml
locations:
  - id: string           # loc_01, loc_02...
    name: string         # 场景名
    description: string   # 氛围描述
    props: []            # 场景道具列表
    moodBoard: string    # Mood Board路径（可选）
```

### items（道具库）

```yaml
items:
  - id: string           # item_01, item_02...
    name: string         # 道具名
    description: string   # 功能描述
    appearance: string    # 外观描述（用于生图）
    referenceImage: string # 参考图路径（可选）
```

### episodes（分集）

```yaml
episodes:
  - episodeNumber: number
    title: string
    hook: string         # 本集钩子
    twist: string        # 本集反转
    endingHook: string   # 结尾钩子
    shots: []           # 镜头数组
```

### shots（镜头）

```yaml
shots:
  - id: string           # ep01_sh01, ep01_sh02...
    shotNumber: number   # 镜头序号（1, 2, 3...）
    durationSec: number # 固定秒数（10/15）
    locationId: string  # ID引用（升级！）
    characterIds: []    # ID引用数组（升级！）
    itemIds: []         # 道具ID数组（新增！）
    script: string      # 镜头描述
    dialogue: []        # 对话数组
        - speakerId: string  # ID引用（升级！）
          text: string
    imagePrompt: string # 生图Prompt
    videoPrompt: string # 视频Prompt（支持多Shot格式）
    objective: string    # 镜头目的
    action: string      # 时序动作（0-5s/5-10s...）
    vo: string          # 配音文本
    bgm: string         # BGM描述
    sfx: string         # 音效描述
    emotionCurve: string # 情绪标注
    status: string       # pending / generating / completed
```

---

## 三、Skill输出规范

每个Skill必须遵循：

1. **输出文件命名**：`第N集-{Skill名}.md`
2. **字段引用**：角色/场景/道具必须使用ID引用，禁止文本名
3. **增量模式**：第02集开始时，读取第01集CDP，复用已有ID
4. **版本追踪**：每次更新记录 `updatedAt` 时间戳

---

## 四、ID命名规范

```
角色: char_01, char_02...      （共8个）
场景: loc_01, loc_02...         （共8个）
道具: item_01, item_02...       （共30个）
镜头: ep{集号}_sh{序号}         （如 ep01_sh01）
```

---

## 五、增量追加规则

```yaml
# 第N集开始时：
1. 读取 manzhou-cdp-{项目名}.yaml
2. 如有同名角色/场景/道具 → 复用已有ID
3. 如有新角色/场景/道具 → 分配新ID
4. shotNumber 从1开始，系统自动偏移
5. 设置 meta.append = true
```
```

- [ ] **Step 2: 在 `manzhou-master.md` 顶部添加CDP Schema引用说明**

在 Role 段落后增加：
```markdown
## CDP JSON Schema

所有Skill输出遵循 `manzhou-cdp-schema.md` 规范。
角色/场景/道具必须使用ID引用，禁止文本名。
```

- [ ] **Step 3: 提交**

```bash
git add AI漫剧生产/skills/manzhou-cdp-schema.md AI漫剧生产/skills/manzhou-master.md
git commit -m "feat(phase2): add manzhou-cdp-schema as shared contract"
```

---

### 任务 2：升级 manzhou-character-consistency（别名aliases）

**Files:**
- Modify: `AI漫剧生产/skills/manzhou-character-consistency.md`

- [ ] **Step 1: 在角色DNA手册模板的"基本信息"部分新增 aliases 字段**

找到 `## 基本信息` 部分，在 `name` 字段后新增：

```yaml
## 基本信息
角色英文名: LinFeng
角色中文名: 林峰
角色ID: char_01              # 新增！
aliases: ["Cherie", "林总", "峰哥"]  # 新增！角色别名数组
```

- [ ] **Step 2: 在 CDP Schema 对应部分说明 aliases 用途**

在文件末尾版本历史前添加：
```markdown
## aliases 别名系统（v1.3.0 新增）

### 功能
同一角色在小说中可能有多个称呼（如"谭斌"/"Cherie"/"谭女士"/"糖饼"），
aliases 用于记录所有别名，确保剧本生成时归一化处理。

### 执行规则
- IP解析阶段：提取所有别名 → 填入 aliases 数组
- 剧本生成阶段：所有别名统一替换为正式角色名
- 视频生成阶段：使用正式角色名 + aliases 作为补充描述

### 示例
```
aliases: ["Cherie", "谭女士", "糖饼"]
→ 剧本中对白统一使用"谭斌"
→ aliases 可用于Voice Prompt中的角色识别
```
```

- [ ] **Step 3: 更新版本历史**

```markdown
| 1.3.0 | 2026-03-25 | 新增aliases别名系统，对标联易方舟CDP JSON |
```

- [ ] **Step 4: 提交**

```bash
git add AI漫剧生产/skills/manzhou-character-consistency.md
git commit -m "feat(phase2): add aliases system to character DNA"
```

---

### 任务 3：升级 manzhou-ip-parser（适配CDP Schema + 别名提取）

**Files:**
- Modify: `AI漫剧生产/skills/manzhou-ip-parser.md`

- [ ] **Step 1: 在IP档案YAML模板中增加CDP Schema必填字段**

找到 YAML 输出模板部分，在 `projectId` 后增加：

```yaml
# IP档案.yaml（CDP Schema兼容格式）
projectId: "${uuid}"          # 必填！CDP Schema要求
title: "${项目名}"
totalEpisodes: 12             # 默认12集
currentEpisode: 1

characters:                   # 角色库（ID化）
  - id: "char_01"            # ID引用
    name: "谭斌"
    aliases: ["Cherie", "谭女士", "糖饼"]  # 新增！别名提取
    gender: "female"
    ageRange: "30-35"
    appearance: "..."
    clothing: "..."
    persona: "..."

locations:                    # 场景库（ID化）
  - id: "loc_01"
    name: "MPL公司写字楼"
    description: "..."
    props: ["电脑", "会议桌"]

items: []                     # 道具库（新增！CDP Schema要求）
```

- [ ] **Step 2: 在"角色识别"部分增加别名提取规则**

找到角色识别相关段落，新增：

```markdown
### 别名提取规则（新增）

识别并提取角色的所有别名/昵称/代号：

```
谭斌 → Cherie / 谭女士 / 糖饼 / 斌姐
程睿敏 → Ray / 程帅 / Ray总
余永麟 → Tony / 老余
```

输出格式：每个角色的 `aliases: []` 数组填入所有识别到的别名。
```

- [ ] **Step 3: 更新版本历史并提交**

```bash
git add AI漫剧生产/skills/manzhou-ip-parser.md
git commit -m "feat(phase2): adapt ip-parser to CDP Schema with aliases"
```

---

## 阶段二：剧本二级结构（新增2个Skill）

---

### 任务 4：创建 manzhou-concept（剧本创意）

**Files:**
- Create: `AI漫剧生产/skills/manzhou-concept.md`

- [ ] **Step 1: 创建 manzhou-concept.md**

```markdown
# AI Short Drama Studio — 剧本创意引擎

> 版本: 1.0.0
> 期次: 第二阶段新增
> 职责: 根据题材/剧情类型/情绪/角色设定，生成N条差异化创意
> 来源: 联易方舟剧本创意模板（cmj716f38...）
> 输入: 题材/情绪/时代/角色设定
> 输出: N条差异化创意JSON

---

## Role

你是顶尖的中国短剧剧本策划专家。
擅长竖屏短剧：节奏极快、冲突密集、反转不断、爽点拉满、人设标签化、结尾强钩子。

---

## 输入参数

```yaml
题材: 都市日常 / 悬疑推理 / 现代言情 / 家庭伦理 / 古风言情 / 玄幻仙侠
剧情类型: 逆袭 / 马甲 / 亲情 / 穿越 / 重生 / 战神归来 / 豪婚逆袭 / 异能 / 无敌神医
情绪基调: 甜宠 / 虐恋 / 轻松 / 紧张 / 温馨 / 感动 / 惊悚 / 搞笑 / 热血
时代背景: 现代 / 近代 / 古代 / 架空
角色设定: 神豪 / 小人物 / 强者回归 / 总裁 / 大女主 / 萌宝
创意数量: N（默认5条）
```

---

## Prompt（直接使用）

你是一位顶尖的中国短剧剧本策划专家，擅长竖屏短剧：节奏极快、冲突密集、反转不断、爽点拉满、人设标签化、结尾强钩子。

请根据系统给出的题材/剧情/情绪/时代/角色设定/补充信息，生成创意列表。创意数量等于系统设置的创意数量N。创意之间必须明显差异化（主角身份标签/人物关系/核心冲突/反转机制至少一项与其他任意条不同）。

【输出要求 必须严格遵守】
1 只输出一个JSON数组 禁止任何解释 前后缀 Markdown 代码块
2 输出必须为单行 首字符为[ 末字符为] 末尾不允许任何多余字符
3 必须可被JSON.parse直接解析 所有key与字符串值使用双引号 不允许尾逗号
4 数组长度必须等于N
5 每个元素仅包含且必须包含字段 id title description 不得出现其他字段
6 id必须依次为c1 c2 … cN
7 title为8到18字 噱头强 暗示核心冲突或爽点
8 description为80到150字 一段话无换行 精炼说明核心设定+主冲突+爽点情绪点+关键反转或结尾钩子 且最后一句必须是钩子
9 title与description的文字内容禁止出现 单引号 双引号 书名号《》 以及任何换行符
10 输出前自检 JSON闭合正确 字段正确 数量正确 长度正确 禁用字符为零 差异化满足后再输出

---

## 输出格式

```json
[{"id":"c1","title":"霸总隐藏身份被助理揭穿","description":"..."},{"id":"c2","title":"..."}]
```

---

## 创意差异化规则

创意之间至少有一项明显不同：
- **主角身份标签**：隐藏身份 vs 公开身份
- **人物关系**：主仆/敌对/暧昧/亲情
- **核心冲突**：职场/家族/商战/情感
- **反转机制**：身份翻转/证据反杀/误会反转

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-03-25 | 新建：剧本创意Skill，来源联易方舟 |
```

- [ ] **Step 2: 提交**

```bash
git add AI漫剧生产/skills/manzhou-concept.md
git commit -m "feat(phase2): add manzhou-concept skill from 联易方舟"
```

---

### 任务 5：创建 manzhou-outline（剧本大纲）

**Files:**
- Create: `AI漫剧生产/skills/manzhou-outline.md`

- [ ] **Step 1: 创建 manzhou-outline.md**

```markdown
# AI Short Drama Studio — 剧本大纲引擎

> 版本: 1.0.0
> 期次: 第二阶段新增
> 职责: 根据选中的创意，生成总大纲 + 人物小传 + 分集规划
> 来源: 联易方舟剧本大纲模板（cmj716f3h...）
> 输入: 选中的创意（来自manzhou-concept）
> 输出: 总大纲JSON

---

## Role

你是AI短剧大纲策划师，负责将创意细化为可执行的分集大纲。

---

## Prompt（直接使用）

请根据选中的创意，生成短剧大纲。

【核心约束】
- title：不超过200字
- characters：2-4人，每集hook/twist/endingHook均不超过30字
- beats：每集3-5条，每条不超过20字
- 第1集必须立刻抛出主冲突与目标
- 每5集一个小高潮，每10集一个大反转
- 反转机制要多样化（身份翻转/立场背刺/证据反杀/误会反转至少两种）

【JSON输出schema】
{
  "title": string,
  "overview": string,          // 不超过200字
  "characters": [{"name": string, "arc": string}],
  "episodeCount": number,
  "episodes": [{
    "episode": number,
    "title": string,
    "hook": string,            // ≤30字，本集开头钩子
    "beats": string[],         // 每集3-5条，每条≤20字
    "twist": string,           // ≤30字，本集反转
    "endingHook": string       // ≤30字，结尾悬念
  }]
}

---

## @引用机制（新增）

生成大纲时，可引用以下上下文：

- @选中创意 → 保持与创意一致
- @前项目大纲（如果有） → 保持系列一致性

---

## 分集规划规则

| 集数区间 | 任务 |
|---------|------|
| 第1-2集 | 建立世界观 + 主冲突抛出 |
| 第3-5集 | 第一波冲突升级 + 首次高潮 |
| 第6-8集 | 身份/关系反转 + 情感升温 |
| 第9-10集 | 第二波高潮 + 核心秘密揭示 |
| 第11-12集 | 终局对决 + 完美收尾钩子 |

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-03-25 | 新建：剧本大纲Skill，来源联易方舟 |
```

- [ ] **Step 2: 提交**

```bash
git add AI漫剧生产/skills/manzhou-outline.md
git commit -m "feat(phase2): add manzhou-outline skill from 联易方舟"
```

---

### 任务 6：升级 manzhou-script（@引用机制 + 台词规范）

**Files:**
- Modify: `AI漫剧生产/skills/manzhou-script.md`

- [ ] **Step 1: 在"剧本正文"部分增加@引用机制**

在 Step 3 时长估算前添加：

```markdown
### @引用变量机制（v2.0.0 新增）

剧本生成时支持以下@引用，实现上下文追踪：

| 引用变量 | 用途 | 示例 |
|---------|------|------|
| @选中创意 | 保持与立项创意一致 | 参考manzhou-concept输出 |
| @剧本大纲 | 保持总纲一致性 | 参考manzhou-outline输出 |
| @前5集剧本正文 | 保持剧情连贯 | 衔接已有剧情 |
| @本集剧情目标 | 聚焦本集任务 | 聚焦本集hook/twist |
| @角色档案 | 保持人设一致 | 参考IP档案aliases |

**使用格式**：
```
===REFERENCE===
@剧本大纲: {manzhou-outline输出摘要}
@前5集剧本正文: {前5集关键剧情节点}
@本集剧情目标: hook={本集hook}, twist={本集twist}, endingHook={本集endingHook}
@角色档案: {IP档案角色摘要}
===END_REFERENCE===

[开始生成剧本正文]
```

### 台词规范强化（v2.0.0 新增）

联易方舟台词规则（直接采用）：
- 台词必须口语化、短句
- 单句台词 ≤15字
- 禁止文学化描写替代对白
- 禁止无角色标注的台词
```

- [ ] **Step 2: 在分集剧本模板中适配CDP Schema**

更新 `## 分集剧本输出规范`，将镜头输出改为ID引用格式：

```markdown
## 分集剧本输出规范（CDP Schema兼容）

### 镜头输出格式（ID引用，v2.0.0升级）

[场次/镜号] | [时长] | [locationId] | [characterIds] | [Visual] | [Audio/dialogue] | [SFX & Emotion]

01/01 | 5s | loc_01 | char_01 | [ECU酒杯特写...] | 【【char_01】】/冷峻：... | [SFX]... [Emotion]...
```

- [ ] **Step 3: 更新版本历史并提交**

```bash
git add AI漫剧生产/skills/manzhou-script.md
git commit -m "feat(phase2): add @reference mechanism and dialogue rules to script"
```

---

## 阶段三：分镜系统升级（P0核心）

---

### 任务 7：升级 manzhou-storyboard（固定时长 + ID引用 + 多Shot）

**Files:**
- Modify: `AI漫剧生产/skills/manzhou-storyboard.md`

- [ ] **Step 1: 在"核心规格"部分修改时长定义**

将：
```markdown
| 单镜时长 | 5-10秒 |
```

改为：
```markdown
| 单镜时长 | 固定秒数（由CDP Schema settings.shotDurationSec决定，默认10s） |
```

- [ ] **Step 2: 新增多Shot videoPrompt格式**

在 `## Prompt 七要素结构` 的要素6后新增：

```markdown
### 要素7：videoPrompt多Shot格式（v3.0.0新增）

当镜头时长 > 5秒时，建议使用多Shot格式：

```
Global Context: no text, no subtitles, no music, no logo
Shot 1 / Duration: 5 sec / Scene: [景别+角色动作描述]
Shot 2 / Duration: 5 sec / Scene: [景别+角色动作描述]
（各Shot Duration之和 ≈ durationSec，允许±1秒容差）
```

**触发条件**：durationSec >= 10s 时自动启用多Shot格式
```

- [ ] **Step 3: 在Prompt模板中将角色/场景改为ID引用**

找到所有Seedance/Kling示例，将文本名替换为ID：

```markdown
# 改前：
Medium Shot, [ID: TanBin_V1], facing camera directly,

# 改后：
Medium Shot, [ID: char_01_V1], facing camera directly,
# 引用manzhou-cdp-schema.md：char_01 = 谭斌
```

- [ ] **Step 4: 更新镜头时长表格式（CDP Schema兼容）**

更新 `## 分镜输出模板` 的时长总表：

```markdown
## 本集镜头时长总表（CDP Schema兼容）

| 镜号 | ID | 时长 | 累计 | 景别 | locationId | characterIds | VO | BGM | SFX |
|------|----|------|------|------|-----------|-------------|-----|-----|-----|
| 01/01 | ep01_sh01 | 10s | 0:10 | WS | loc_01 | - | 无 | 钢琴单音 | 城市夜声 |
| 01/02 | ep01_sh02 | 10s | 0:20 | MS | loc_01 | char_01 | "..." | 规律节奏 | 键盘声 |
```

- [ ] **Step 5: 在"禁止事项"中新增CDP Schema强制规则**

```markdown
## 禁止事项（v3.0.0新增）

- ❌ 角色使用文本名：必须使用ID引用（char_01, char_02...）
- ❌ 场景使用文本名：必须使用ID引用（loc_01, loc_02...）
- ❌ 道具未标注itemIds：如有道具必须引用（item_01...）
- ❌ 镜头时长使用范围：必须使用CDP Schema指定的固定秒数
```

- [ ] **Step 6: 更新版本历史并提交**

```bash
git add AI漫剧生产/skills/manzhou-storyboard.md
git commit -m "feat(phase2): upgrade storyboard with fixed duration + ID refs + multi-shot"
```

---

### 任务 8：创建 manzhou-item-generator（道具系统）

**Files:**
- Create: `AI漫剧生产/skills/manzhou-item-generator.md`

- [ ] **Step 1: 创建 manzhou-item-generator.md**

```markdown
# AI Short Drama Studio — 道具生成引擎

> 版本: 1.0.0
> 期次: 第二阶段新增
> 职责: 为道具库中的每个道具生成参考图
> 来源: 联易方舟道具物品图模板（cmjdxpc1s...）
> 输入: manzhou-ip-parser输出的items[]数组
> 输出: 道具参考图 + 参考图路径更新到CDP

---

## Role

你是道具概念设计师，负责为每个道具生成清晰、可复用的参考图。

---

## Prompt模板（直接使用）

请生成"道具/物品参考图"单张图片。

**要求**：
- 主体清晰、材质细节明确
- 背景干净、无文字/无水印
- 可用于视频生成参考

**输入字段**：
- 物品名：${name}
- 物品描述：${description}
- 外观：${appearance}

---

## 执行流程

```
1. 读取 manzhou-cdp-schema.md 的items[]数组
2. 对每个item生成参考图Prompt
3. 调用图像生成AI（Seedance/Flux/Midjourney）
4. 更新CDP中每个item的referenceImage字段
5. 输出：更新后的items[]数组
```

---

## 道具分类

| 类型 | 示例 | 优先级 |
|------|------|--------|
| 关键道具 | 邮件通知/车钥匙/红酒杯 | 高（影响剧情） |
| 场景道具 | 电脑/会议桌/电子门卡 | 中（环境统一） |
| 装饰道具 | 花瓶/书本/装饰画 | 低（可选） |

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-03-25 | 新建：道具生成Skill，来源联易方舟 |
```

- [ ] **Step 2: 提交**

```bash
git add AI漫剧生产/skills/manzhou-item-generator.md
git commit -m "feat(phase2): add manzhou-item-generator skill"
```

---

## 阶段四：工作流增强（增量 + 润色 + 成本）

---

### 任务 9：创建 manzhou-incremental（增量追加机制）

**Files:**
- Create: `AI漫剧生产/skills/manzhou-incremental.md`

- [ ] **Step 1: 创建 manzhou-incremental.md**

```markdown
# AI Short Drama Studio — 增量追加引擎

> 版本: 1.0.0
> 期次: 第二阶段新增
> 职责: 支持多集制作时复用已有资产（角色/场景/道具）
> 来源: 联易方舟增量追加机制
> 输入: 已有CDP JSON + 新集剧本
> 输出: 合并后的CDP JSON

---

## Role

你是增量制作管理器，确保第02集复用第01集资产，实现数据一致性。

---

## 核心机制

### 增量追加规则

```
第N集开始时：
1. 读取已有 manzhou-cdp-{项目名}.yaml
2. 比对新集角色/场景/道具：
   - 同名 → 复用已有ID（禁止新建）
   - 新增 → 自动分配新ID
3. shotNumber从1开始，系统自动偏移到全局序号
4. 设置 meta.append = true
5. 更新 updatedAt 时间戳
```

### ID复用检测

```python
# 伪代码
for each new_character in new_script.characters:
    for each existing_character in cdp.characters:
        if new_character.name in existing_character.aliases:
            # 别名匹配 → 复用已有ID
            new_character.id = existing_character.id
        else:
            # 新角色 → 分配新ID
            new_character.id = f"char_{len(cdp.characters) + 1}"
```

### 场景/道具复用

```
场景复用条件：location.name 完全匹配
道具复用条件：item.name 完全匹配
```

---

## 执行流程

```
[第01集完成]
    ↓
生成 manzhou-cdp-{项目名}.yaml（含char_01~08, loc_01~08, item_01~30）
    ↓
[第02集开始]
    ↓
manzhou-incremental 加载已有CDP
    ↓
新集剧本解析 → 识别角色/场景/道具
    ↓
复用已有ID + 分配新ID
    ↓
合并到CDP → 输出更新后的CDP
    ↓
[第02集继续后续流程]
```

---

## CDP更新操作

| 操作 | 字段变化 |
|------|---------|
| 复用角色 | characters[] 不变，episodes[] 新增 |
| 新增角色 | characters[] 追加，ID自动递增 |
| 复用场景 | locations[] 不变 |
| 新增场景 | locations[] 追加 |
| 复用道具 | items[] 不变 |
| 新增道具 | items[] 追加 |

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-03-25 | 新建：增量追加Skill，来源联易方舟 |
```

- [ ] **Step 2: 提交**

```bash
git add AI漫剧生产/skills/manzhou-incremental.md
git commit -m "feat(phase2): add manzhou-incremental for multi-episode production"
```

---

### 任务 10：创建 manzhou-polish（润色工具）

**Files:**
- Create: `AI漫剧生产/skills/manzhou-polish.md`

- [ ] **Step 1: 创建 manzhou-polish.md（19个润色方向）**

```markdown
# AI Short Drama Studio — 润色工具引擎

> 版本: 1.0.0
> 期次: 第二阶段新增
> 职责: 去除AI生成痕迹，提升文稿质量
> 来源: 联易方舟润色工具（19个模板）
> 输入: 剧本正文/台词/场景描述
> 输出: 润色后的文本

---

## Role

你是文稿润色师，专注于去除AI生成痕迹，让文字读起来像人写的。

---

## 19个润色方向

### 1. 去AI味
**目标**：消除过度规整、缺乏情感温度的文字
**Prompt**：请将以下文本改写得更自然、口语化，去除明显的AI生成痕迹（如过度对仗、过于完美的逻辑衔接）

### 2. 提升文采
**目标**：增加文学性和表现力
**Prompt**：请用更生动、更有画面感的语言重写以下内容

### 3. 口语化
**目标**：让台词更贴近真实对话
**Prompt**：请将以下台词改写为更口语化、更自然的对话

### 4. 情绪强化
**目标**：放大情绪感染力
**Prompt**：请强化以下文本的情绪表达，让读者更有代入感

### 5. 节奏加快
**目标**：提升叙事紧凑度
**Prompt**：请精简以下文本，去除冗余描述，加快叙事节奏

### 6. 细节丰富
**目标**：增加场景/动作的具体性
**Prompt**：请为以下描述补充更多感官细节（视觉/听觉/触觉）

### 7. 对话自然化
**目标**：消除"书面语"对话感
**Prompt**：请将以下对白改得更像真实人物的说话方式

### 8. 心理描写内敛
**目标**：减少直白心理描写，用动作/表情暗示
**Prompt**：请将以下直白心理描写转化为暗示性的动作/表情描写

### 9. 动作描写具体化
**目标**：从抽象动作到具体行为
**Prompt**：请将以下模糊的动作描写具体化

### 10. 场景描写生动
**目标**：增加场景的氛围感
**Prompt**：请为以下场景增加氛围感和代入感

### 11. 台词简短化
**目标**：每句台词控制在15字内
**Prompt**：请精简以下台词，每句不超过15字

### 12. 钩子强化
**目标**：让结尾更有悬念感
**Prompt**：请强化以下结尾的悬念感，制造更强的钩子效果

### 13. 过渡自然
**目标**：让场景切换更流畅
**Prompt**：请优化以下场景过渡，让转场更自然

### 14. 人设强化
**目标**：让人物性格更鲜明
**Prompt**：请强化以下内容中的人物性格特征

### 15. 爽点放大
**目标**：放大逆袭/打脸的情绪爽感
**Prompt**：请放大以下内容的"爽感"，让读者更解气

### 16. 虐点深化
**目标**：加深虐心情节的情绪张力
**Prompt**：请深化以下内容的情感冲突，让读者更心痛

### 17. 甜度提升
**目标**：增加暧昧/甜蜜情节的甜度
**Prompt**：请提升以下内容的甜蜜感和心动感

### 18. 悬念增强
**目标**：让叙事更有悬念
**Prompt**：请在以下内容中增加悬念和期待感

### 19. 反转自然化
**目标**：让剧情反转更合乎逻辑
**Prompt**：请优化以下反转情节，让其更合理、更令人惊讶

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-03-25 | 新建：润色工具Skill，来源联易方舟 |
```

- [ ] **Step 2: 提交**

```bash
git add AI漫剧生产/skills/manzhou-polish.md
git commit -m "feat(phase2): add manzhou-polish with 19 refinement directions"
```

---

### 任务 11：创建 manzhou-cost-estimator（成本估算）

**Files:**
- Create: `AI漫剧生产/skills/manzhou-cost-estimator.md`

- [ ] **Step 1: 创建 manzhou-cost-estimator.md**

```markdown
# AI Short Drama Studio — 成本估算引擎

> 版本: 1.0.0
> 期次: 第二阶段新增
> 职责: 估算每个项目的AI生成成本
> 来源: 联易方舟灵石定价体系
> 输入: 项目配置（集数/镜头数/角色数/每集时长）
> 输出: 成本明细表

---

## 定价表（基于联易方舟灵石体系，换算人民币）

### 图片生成

| 模型 | 分辨率 | 灵石 | 人民币 | 适用 |
|------|--------|------|--------|------|
| channelA:sora-image | 1K | 800 | ¥0.02 | 资产预览 |
| gemini-3.1-flash-image | 1K | 2000 | ¥0.10 | 角色卡 |
| gemini-3-pro-image-preview | 1K | 3000 | ¥0.33 | 高清角色 |
| nano-banana-fast | 1K | 1000 | ¥0.02 | 九宫格分镜 |
| nano-banana | 1K | 2000 | ¥0.07 | 场景基底图 |

### 视频生成

| 模型 | 时长 | 灵石 | 人民币 | 性价比 |
|------|------|------|--------|--------|
| sora-2-all | 10/15s | 3000 | ¥0.14 | ⭐最高 |
| official:veo_3_1-fast-4K | 8s | 4000 | ¥0.15 | 高 |
| grok-video-3-10s | 10s | 6000 | ¥0.28 | 中 |
| official:veo_3_1-4K | 8s | 8000 | ¥0.43 | 低 |
| official:veo3.1-pro-4k | 8s | 40000 | ¥1.75 | 低 |

### 配音生成

| 模型 | 单位 | 灵石 | 人民币 |
|------|------|------|--------|
| tts-1 | 200字 | 120 | ¥0.006 |
| tts-1-hd | 200字 | 240 | ¥0.012 |

---

## 估算公式

```
每集图片成本 = 角色数 × 角色卡单价 + 场景数 × 场景图单价 + 道具数 × 道具图单价
每集视频成本 = 镜头数 × (镜头时长/10s) × sora-2-all单价
每集配音成本 = 总字数/200 × tts-1单价
每集BGM成本 = 固定2首 × 估算单价

项目总成本 = 每集图片 × 集数 + 每集视频 × 集数 + 每集配音 × 集数 + BGM
```

---

## 估算示例

```
项目配置：12集 × 20镜头 × 10s/镜 × 角色8人 × 场景8个

每集估算：
- 图片：8角色×¥0.10 + 8场景×¥0.07 + 30道具×¥0.02 = ¥1.46
- 视频：20镜头×¥0.14 = ¥2.80
- 配音：1000字/集÷200×¥0.006 = ¥0.03
- BGM：2首×¥0.50 = ¥1.00

每集合计：¥5.29
项目总计（12集）：¥63.48
```

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-03-25 | 新建：成本估算Skill，来源联易方舟灵石体系 |
```

- [ ] **Step 2: 提交**

```bash
git add AI漫剧生产/skills/manzhou-cost-estimator.md
git commit -m "feat(phase2): add manzhou-cost-estimator with pricing table"
```

---

## 阶段五：收尾改造（P1级）

---

### 任务 12：升级 manzhou-visual-style（11种预设完整描述）

**Files:**
- Modify: `AI漫剧生产/skills/manzhou-visual-style.md`

- [ ] **Step 1: 在风格参数包前新增11种预设完整描述**

在 `## 风格参数包` 前新增：

```markdown
## 11种风格预设（v2.0.0 扩充，来源联易方舟）

> 联易方舟实测11种预设，漫舟原有5种扩充至此

| ID | 名称 | 说明 |
|----|------|------|
| anime | 日漫 | 清晰线稿、赛璐璐上色、表情夸张可爱 |
| cn_anime | 国风动漫 | 国风美术与动画质感结合，色彩典雅 |
| cn_3d | 国风3D | 国风符号+3D质感，史诗氛围 |
| ink | 水墨国风 | 水墨写意、留白、宣纸纹理 |
| cyber | 赛博朋克 | 霓虹光效，未来都市 |
| us_comics | 美漫 | 强轮廓线、高对比上色 |
| real | 写实 | 真实摄影质感 |
| horror | 恐怖惊悚 | 低照度、高反差 |
| pixar | 皮克斯 | 美式3D动画感（去品牌化） |
| shinkai | 新海诚 | 通透光影动画感（去作者名） |
| miyazaki | 宫崎骏 | 治愈手绘动画风（去作者名） |

### cn_anime（国风动漫）完整描述

```
国风美术与动画质感结合，色彩典雅，融合中国传统美学元素与现代动画技术，
人物形象符合中国审美，服饰细节考究，背景呈现中式建筑/山水/室内场景。
动漫风格，精致线稿，赛璐璐上色，柔和光影，传统色彩体系。
```

### cn_3d（国风3D）完整描述

```
国风符号+3D质感，史诗氛围，融合中国古典元素与现代3D动画技术，
人物建模精致，场景宏大壮观，光影效果华丽，
适合表现家族对决、商战博弈等大场面。
```

### ink（水墨国风）完整描述

```
水墨写意、留白、宣纸纹理，融合中国传统水墨画技法与现代动画，
墨色浓淡变化，笔触灵动飘逸，意境深远，
适合表现情感内敛、古典美的场景。
```

### cyber（赛博朋克）完整描述

```
赛博朋克风格，霓虹光效，未来都市设定，
高对比色调（霓虹粉/青/紫），暗色调背景，
光污染效果，数据流/全息投影元素，
适合科幻设定和异能题材。
```

### us_comics（美漫）完整描述

```
美式漫画风格，强轮廓线、高对比上色、平板着色，
风格参考漫威/DC插画，色彩饱和，
人物造型夸张有力，动态感强。
```

### real（写实）完整描述

```
写实摄影风格，真实摄影质感，自然光效，
皮肤纹理清晰，环境真实感强，
适合现实题材和纪录片风格。
```

### horror（恐怖惊悚）完整描述

```
恐怖惊悚风格，低照度、高反差、阴影浓重，
冷色调为主，诡异光效，
适合惊悚悬疑题材。
```

### pixar（皮克斯）完整描述

```
皮克斯动画风格，美式3D动画感，圆润角色建模，
温馨色调，柔和光影，家庭友好氛围，
适合温情/家庭/成长题材。
```

### shinkai（新海诚）完整描述

```
新海诚动画风格，通透光影动画感，云彩/天空/水面细节丰富，
真实场景与幻想元素结合，色彩通透，光影唯美，
适合浪漫/离别/重逢等情感细腻场景。
```

### miyazaki（宫崎骏）完整描述

```
宫崎骏动画风格，治愈手绘动画风，自然主题，
手绘质感，温暖色调，魔法元素，
适合奇幻/冒险/成长题材。
```

### Style Preset ID 映射（新增）

```yaml
# CDP Schema stylePresetId 映射
stylePresetId: "cn_anime"  # ← 用这个ID引用
```

### 风格选择决策树更新（v2.0.0）

```markdown
## 风格选择决策树（v2.0.0）

1. 古装/仙侠/历史题材？
   → cn_anime 或 ink

2. 科幻/末世/废土/异能题材？
   → cyber 或 cn_3d

3. 温情/家庭/成长题材？
   → pixar

4. 浪漫/离别/都市情感？
   → shinkai 或 anime

5. 复仇/对决/商战大场面？
   → cn_3d 或 Villeneuve_Style

6. 恐怖/惊悚/悬疑？
   → horror

7. 美式英雄/超级英雄？
   → us_comics

8. 写实/纪录/现实题材？
   → real

9. 默认/爽感短剧？
   → anime 或 ShortDrama_Style
```
```

- [ ] **Step 2: 更新版本历史并提交**

```bash
git add AI漫剧生产/skills/manzhou-visual-style.md
git commit -m "feat(phase2): expand visual-style to 11 presets with full descriptions"
```

---

### 任务 13：升级 manzhou-bgm 和 manzhou-sfx（音频增强）

**Files:**
- Modify: `AI漫剧生产/skills/manzhou-bgm.md`
- Modify: `AI漫剧生产/skills/manzhou-sfx.md`

- [ ] **Step 1: manzhou-bgm 新增BPM参数**

在BGM Prompt模板部分新增：

```markdown
## BPM参数规范（v2.0.0新增，来源NanoPhoto）

BGM Prompt可包含以下参数：

| 参数 | 格式 | 示例 |
|------|------|------|
| BPM | 数字 | 60 / 80 / 120 |
| 情绪 | 文字 | 悬疑 / 温情 / 燃向 |
| Crossfade | 时间戳 | [00:15]渐入，[00:45]渐出 |
| 风格描述 | 文字 | 弦乐 / 电子 / 钢琴 |

### 增强BGM Prompt格式

```
[BGM: 悬疑/低沉弦乐, 60BPM, [00:00]渐入,[00:45]渐出]
```

**BPM参考表**：
- 紧张/悬疑：60-70 BPM
- 日常/温馨：80-90 BPM
- 动作/燃向：120-140 BPM
- 浪漫/甜宠：70-80 BPM
```

- [ ] **Step 2: manzhou-sfx 新增精确时间戳**

在SFX参数部分新增：

```markdown
## 精确时间戳规范（v2.0.0新增，来源NanoPhoto）

SFX标注格式升级为精确时间戳：

```
SFX时间戳格式：
[00:00.0] 咖啡杯轻碰
[00:03.2] 键盘打字开始
[00:07.8] 键盘打字停止
```

**精度标准**：小数点后1位（0.1s），NanoPhoto达到0.05s，漫舟目标0.1s

**时间轴生成规则**：
1. 根据镜头时长分配音效位置
2. 关键动作点必须标注精确时间
3. 转场点标注转场音效
```

- [ ] **Step 3: 提交**

```bash
git add AI漫剧生产/skills/manzhou-bgm.md AI漫剧生产/skills/manzhou-sfx.md
git commit -m "feat(phase2): enhance audio skills with BPM and timestamp precision"
```

---

## 三、验证与总结

---

### 任务 14：全量验证

**验证清单：**

- [ ] manzhou-cdp-schema.md — Schema规范文件创建完成
- [ ] manzhou-master.md — 引用CDP Schema
- [ ] manzhou-ip-parser.md — aliases提取 + CDP格式
- [ ] manzhou-character-consistency.md — aliases字段
- [ ] manzhou-concept.md — 新增
- [ ] manzhou-outline.md — 新增
- [ ] manzhou-script.md — @引用机制
- [ ] manzhou-storyboard.md — 固定时长 + ID引用 + 多Shot
- [ ] manzhou-item-generator.md — 新增
- [ ] manzhou-incremental.md — 新增
- [ ] manzhou-polish.md — 新增
- [ ] manzhou-cost-estimator.md — 新增
- [ ] manzhou-visual-style.md — 11种预设
- [ ] manzhou-bgm.md — BPM参数
- [ ] manzhou-sfx.md — 精确时间戳

- [ ] **执行验证：运行 manzhou-master 对第02集进行完整流程测试**

```bash
# 读取 manzhou-master.md
# 选择一个新项目运行 manzhou-concept
# 验证@引用机制是否生效
# 验证ID引用格式是否正确
```

- [ ] **提交最终优化版本**

```bash
git add AI漫剧生产/skills/
git commit -m "feat(phase2): complete P0+P1 optimizations - 21 skills total"
```

---

## 四、任务依赖关系

```
[Schema契约层]
    Task1(CDP Schema) ──────────────────────────────────────┐
          │                                                   │
[角色系统]                                                    │
    Task2(char aliases) ──→ Task3(ip-parser aliases) ───────┤
                                                              │
[剧本二级结构]                                                 │
    Task4(concept) ────────────→ Task5(outline) ─────────────┤
              │                                                   │
[剧本增强]                                                      │
    Task6(script @引用) ─────────────────────────────────────┤
                                                              │
[分镜系统]                                                        │
    Task7(storyboard 固定时长+ID+多Shot) ─→ Task8(item-generator) ─┤
                                                                 │
[工作流增强]                                                       │
    Task9(incremental) ─→ Task10(polish) ─→ Task11(cost-estimator) ┤
                                                                 │
[收尾]                                                             │
    Task12(visual-style 11预设) ─→ Task13(bgm/sfx增强) ──→ Task14(验证) ┘
```

---

## 五、Git提交历史规划

```
feat(phase2): add manzhou-cdp-schema as shared contract
feat(phase2): add aliases system to character DNA
feat(phase2): adapt ip-parser to CDP Schema with aliases
feat(phase2): add manzhou-concept skill
feat(phase2): add manzhou-outline skill
feat(phase2): add @reference mechanism to script
feat(phase2): upgrade storyboard with fixed duration + ID refs + multi-shot
feat(phase2): add manzhou-item-generator skill
feat(phase2): add manzhou-incremental for multi-episode production
feat(phase2): add manzhou-polish with 19 refinement directions
feat(phase2): add manzhou-cost-estimator with pricing table
feat(phase2): expand visual-style to 11 presets with full descriptions
feat(phase2): enhance audio skills with BPM and timestamp precision
feat(phase2): complete P0+P1 optimizations - 21 skills total
```

---

*计划完成 — 2026-03-25*
