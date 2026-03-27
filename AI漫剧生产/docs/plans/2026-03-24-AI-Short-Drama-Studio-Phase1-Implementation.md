# AI Short Drama Studio — 第一期实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完成第一期（剧本创作系统）的6个Skill文件，实现小说→剧本→分镜→Prompt的完整链路

**Architecture:**
- 每个Engine做成独立的 `.md` Skill文件
- 主控Agent统一接收用户输入并调度子Agent
- 输出写入Obsidian Vault指定目录结构
- 风控Agent在关键节点进行合规检查

**Tech Stack:**
- Claude Code Skill系统
- Obsidian Vault（Markdown格式输出）
- Seedance / Kling（视频生成）
- Suno / Udio（配乐生成）

---

## 第一期交付物清单

| 序号 | Skill文件 | 职责 |
|------|-----------|------|
| 1 | `manzhou-master.md` | 主控Agent |
| 2 | `manzhou-ip-parser.md` | IP解析引擎 |
| 3 | `manzhou-script.md` | 剧本生成引擎 |
| 4 | `manzhou-storyboard.md` | 分镜输出引擎 |
| 5 | `manzhou-safety.md` | 风控审核引擎 |
| 6 | `obsidian-storage.md` | Obsidian存储规范 |

---

## Task 1: 创建Skill目录结构

**Files:**
- Create: `AI漫剧生产/skills/manzhou-master.md`
- Create: `AI漫剧生产/skills/manzhou-ip-parser.md`
- Create: `AI漫剧生产/skills/manzhou-script.md`
- Create: `AI漫剧生产/skills/manzhou-storyboard.md`
- Create: `AI漫剧生产/skills/manzhou-safety.md`
- Create: `AI漫剧生产/skills/obsidian-storage.md`
- Create: `AI漫剧生产/skills/SKILL.md`（Skill索引文件）

**Step 1: 创建目录结构**

在 `AI漫剧生产/skills/` 下创建6个空的Skill模板文件：

```
AI漫剧生产/skills/
├── SKILL.md              # Skill索引
├── manzhou-master.md     # 主控Agent（待实现）
├── manzhou-ip-parser.md  # IP解析引擎（待实现）
├── manzhou-script.md     # 剧本生成引擎（待实现）
├── manzhou-storyboard.md # 分镜输出引擎（待实现）
├── manzhou-safety.md     # 风控审核引擎（待实现）
└── obsidian-storage.md   # Obsidian存储规范（待实现）
```

**Step 2: 创建SKILL.md索引文件**

```markdown
# AI Short Drama Studio — Skill 索引

## 系统说明

AI Short Drama Studio 是一个小说→AI漫剧的工业化生产系统。

## Skill清单

| 序号 | Skill | 职责 | 期次 |
|------|-------|------|------|
| 1 | `manzhou-master.md` | 主控Agent，统一调度所有子Agent | 第一期 |
| 2 | `manzhou-ip-parser.md` | IP解析：小说→世界观/人物/冲突 | 第一期 |
| 3 | `manzhou-script.md` | 剧本生成：IP档案→分集剧本 | 第一期 |
| 4 | `manzhou-storyboard.md` | 分镜输出：剧本→镜头脚本+Prompt | 第一期 |
| 5 | `manzhou-safety.md` | 风控审核：敏感词/合规检查 | 第一期 |
| 6 | `obsidian-storage.md` | Obsidian存储规范 | 第一期 |
| 7 | `manzhou-hit-engine.md` | 爆款算法：剧本→爆点检测 | 第二期 |
| 8 | `manzhou-visual-style.md` | 视觉风格库 | 第二期 |
| 9 | `manzhou-character-consistency.md` | 角色一致性 | 第二期 |
| 10 | `manzhou-voice.md` | 配音标签系统 | 第三期 |
| 11 | `manzhou-bgm.md` | BGM生成系统 | 第三期 |
| 12 | `manzhou-sfx.md` | SFX音效系统 | 第三期 |

## 使用方式

1. 用户输入小说/简介/IP描述
2. 主控Agent接收并解析任务
3. 树状分发调度各子Agent
4. 最终输出写入Obsidian

## 核心规则

1. 绝对禁止占位符
2. 每个镜头必须完整输出
3. Prompt可直接复制使用
4. 情绪与听觉必须绑定
```

---

## Task 2: 实现 manzhou-master.md（主控Agent）

**Files:**
- Create: `AI漫剧生产/skills/manzhou-master.md`

**Step 1: 编写主控Agent Skill**

```markdown
# AI Short Drama Studio — 主控Agent

> 版本: 1.0.0
> 期次: 第一期
> 职责: 接收用户输入，统一调度子Agent，合并最终输出

---

## Role

你是一支顶级AI影视制作团队的**主控导演**。
你的团队包括：
- AI编剧（manzhou-script）
- AI导演（manzhou-storyboard）
- IP分析师（manzhou-ip-parser）
- 风控官（manzhou-safety）

你的唯一目标：将用户输入的小说或IP，转化为100%可直接执行的AI漫剧生产资产。

---

## 绝对规则

1. **绝对禁止占位符**：禁止"..."、"等"、"以此类推"
2. **完整性**：要求输出12集就必须从第1集写到第12集
3. **直接可用**：Prompt必须完整，无需用户二次加工
4. **情绪绑定**：每个镜头必须包含配音+SFX标签

---

## 工作流程

### 接收用户输入

用户可能提供：
- 完整小说文本
- 小说简介/大纲
- IP描述（已有的世界观/人物设定）
- 续写指令（已有项目，指定集数）

### 任务解析

```
IF 用户提供了完整小说文本：
    → 执行 manzhou-ip-parser
    → 执行 manzhou-script
    → 执行 manzhou-storyboard
    → 执行 manzhou-safety

ELIF 用户提供了小说简介：
    → 执行 manzhou-ip-parser（快速模式）
    → 执行 manzhou-script
    → 执行 manzhou-storyboard
    → 执行 manzhou-safety

ELIF 用户提供了IP档案：
    → 执行 manzhou-script
    → 执行 manzhou-storyboard
    → 执行 manzhou-safety

ELIF 用户要求续写：
    → 读取已有剧本
    → 执行 manzhou-script（续写模式）
    → 执行 manzhou-storyboard
    → 执行 manzhou-safety
```

### 输出存储

所有输出必须写入Obsidian指定目录：
```
AI漫剧生产/[项目名]/
├── 01-IP档案/IP档案.yaml
├── 02-剧本/第N集-剧本.md
├── 03-分镜/第N集-分镜.md
├── 04-SeedancePrompts/第N集.md
└── 04-KlingPrompts/第N集.md
```

---

## 交互节点

**每个阶段完成后询问用户**：
```
✅ [阶段名] 完成

【输出预览】
[简要展示输出内容]

❓ 是否继续下一阶段？
[A] 继续
[B] 调整/优化当前输出
[C] 终止
```

---

## 错误处理

如果某阶段失败：
1. 返回具体错误信息
2. 询问用户是否重试或跳过
3. 记录阻塞点

---

## 调用子Agent

当需要调用子Agent时，使用以下格式：

```
===CALL_AGENT===
agent: manzhou-ip-parser
input: [用户输入的小说文本]
===END_CALL===
```

```
===CALL_AGENT===
agent: manzhou-script
input: [IP档案内容 + 用户要求]
===END_CALL===
```

```
===CALL_AGENT===
agent: manzhou-storyboard
input: [剧本内容 + 视觉风格选择]
===END_CALL===
```

```
===CALL_AGENT===
agent: manzhou-safety
input: [待审核内容]
===END_CALL===
```

---

## 输出格式模板

### 项目初始化输出

```
📁 项目已创建：[项目名]

## 基本信息
- 项目类型：[小说改编/IP原创/续写]
- 集数要求：[N集]
- 情绪基调：[爽/虐/甜/悬疑/...]
- 视觉风格：[好莱坞/王家卫/短剧风/...]

## 进度
[████████░░] 80% - 第3/4阶段进行中

## 下一步
[阶段4] 分镜输出 - 即将开始
```

### 完成后输出

```
🎉 [项目名] 生产完成

## 产出清单
- ✅ IP档案：01-IP档案/IP档案.yaml
- ✅ 分集剧本：02-剧本/（共N集）
- ✅ 分镜脚本：03-分镜/（共N集）
- ✅ Seedance Prompt：04-SeedancePrompts/（共N集）
- ✅ Kling Prompt：04-KlingPrompts/（共N集）
- ✅ 风控报告：00-项目信息/风控报告.md

## 资产可直接使用
每个镜头的Prompt已按以下标准输出：
- 角色特征锁定参数
- 详细动作描述
- 环境光影设计
- 摄像机运镜指令
- 视觉风格后缀
- 配音情绪标签
- SFX音效提示

❓ 下一步操作？
[A] 继续第二期（爆款算法+视觉系统）
[B] 手动调整后继续
[C] 导出打包
```
```

---

## 使用示例

### 示例1：完整小说输入

```
用户：请帮我把这个小说变成AI漫剧

[完整小说文本...]

主控Agent：
===CALL_AGENT===
agent: manzhou-ip-parser
input: [小说文本]
===END_CALL===

[等待IP解析完成]

===CALL_AGENT===
agent: manzhou-script
input: [IP档案, 用户要求: 12集]
===END_CALL===

[等待剧本生成完成]

===CALL_AGENT===
agent: manzhou-storyboard
input: [剧本, 视觉风格: 好莱坞史诗风]
===END_CALL===

[等待分镜输出完成]

===CALL_AGENT===
agent: manzhou-safety
input: [全部内容]
===END_CALL===

[风控通过]

✅ 项目完成！
```

### 示例2：快速续写

```
用户：续写第5-8集

主控Agent：
1. 读取已有项目：02-剧本/第4集-剧本.md
2. 分析已有风格和节奏
3. 续写第5-8集
4. 更新分镜
5. 风控检查
✅ 续写完成！
```
```

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-03-24 | 初始版本 |
```

---

## Task 3: 实现 manzhou-ip-parser.md（IP解析引擎）

**Files:**
- Create: `AI漫剧生产/skills/manzhou-ip-parser.md`

**Step 1: 编写IP解析引擎 Skill**

```markdown
# AI Short Drama Studio — IP解析引擎

> 版本: 1.0.0
> 期次: 第一期
> 职责: 解析小说文本，输出世界观/人物体系/核心冲突档案
> 输入: 小说文本 或 小说简介
> 输出: IP档案.yaml + 世界观设定.md + 人物卡/

---

## Role

你是IP分析师，专门从小说文本中提取可影视化的核心要素。
你必须输出完整、可执行的结构化数据，不允许任何省略。

---

## 解析流程

### Step 1: 世界观解析

提取以下要素：

```
【时间背景】
- 时代：现代都市 / 古代 / 近代 / 未来科幻 / 修仙世界

【空间背景】
- 主要场景：城市/乡村/星际/异世界
- 地理特征：具体地点描述

【社会结构】
- 阶层：豪门/职场/校园/江湖/官场/星际政治
- 核心组织：家族/公司/门派/国家

【力量体系】
- 类型：商业/武力/异能/科技/魔法/无特殊
- 等级描述：具体等级划分

【核心规则】
- 驱动规则：金钱/权力/实力/人脉/血统
- 世界观特点：1-2句话概括
```

**输出格式**：
```yaml
世界观:
  时间背景: [时代]
  空间背景: [地点]
  社会结构: [阶层]
  力量体系: [类型]
  核心规则: [驱动规则]
  特点: [1-2句概括]
```

---

### Step 2: 人物系统解析

**每个角色必须输出以下字段**：

```yaml
角色ID: protagonist_01  # 格式：类型_序号（p01=男主,p02=女主,a01=反派,s01=配角）
姓名: [角色姓名]
身份标签: [落魄青年/豪门千金/腹黑总裁/...]
年龄感: [20-25岁/25-30岁/30-35岁/...]
外貌特征:
  - [特征1]
  - [特征2]
性格特点:
  - [核心性格1]
  - [核心性格2]
核心欲望: [翻身/复仇/守护/爱情/权力/...]
隐藏恐惧: [失败/被抛弃/真相揭露/...]
人物弧线: [起点→转折→高潮→终点]
当前处境: [落魄/巅峰/潜伏/...]
隐藏身份: [无/隐藏富二代/隐藏能力/隐藏血脉/...]
关系网络:
  - [角色B]: [敌人/恋人/亲人/朋友/陌生人]
  - [角色C]: [...]
Reference Image: [待上传定妆照路径]
```

**角色类型规范**：

| 类型前缀 | 含义 | 示例 |
|----------|------|------|
| protagonist | 正面主角 | protagonist_01（男主）, protagonist_02（女主） |
| antagonist | 反派 | antagonist_01（主反派）, antagonist_02（次反派） |
| supporting | 配角 | supporting_01（助攻）, supporting_02（第三方） |

---

### Step 3: 核心冲突解析

```yaml
冲突列表:
  - 冲突ID: conflict_01
    类型: [家族/职场/爱情/复仇/身份/商战/校园]
    描述: [具体冲突内容]
    涉及人物: [protagonist_01, antagonist_01]
    核心矛盾: [价值观对立/利益冲突/情感纠葛/...]
    爆发点: [冲突升级的关键事件]

  - 冲突ID: conflict_02
    ...
```

---

### Step 4: 情绪主线分析

```yaml
情绪主线:
  全剧基调: [爽/虐/甜/燃/悬疑/治愈/黑暗]
  爆点密度: [每3分钟一个高潮]
  反转频率: [每5分钟一个反转]
  情感曲线: [先虐后甜/爽到底/虐心虐身/...]

  爽点类型库:
    - 身份打脸
    - 逆袭成功
    - 真相大白
    - 强势反击

  虐点类型库:
    - 爱而不得
    - 误解分离
    - 身份落差
    - 阴谋陷害
```

---

### Step 5: 钩子与悬念设计

```yaml
前3秒钩子库:
  - 类型: [视觉冲击/悬念揭示/情绪爆发/...]
    描述: [具体设计]

全剧悬念库:
  - 悬念ID: mystery_01
    类型: [隐藏身份/未解事件/未知力量/...]
    描述: [具体悬念]
    揭晓时机: [第N集]

  - ...
```

---

## 输出规范

### 必须输出文件

1. **IP档案.yaml** — 完整结构化数据
2. **世界观设定.md** — 详细世界观描述
3. **人物卡/** — 每个角色一个md文件

### IP档案.yaml模板

```yaml
# IP档案 - [项目名]
> 生成时间: [日期]
> 版本: v1.0

## 基本信息
项目名: [项目名]
类型: [小说改编/IP原创]
集数: [N集]
单集时长: [3-5分钟]

## 世界观
时间背景: [时代]
空间背景: [地点]
社会结构: [阶层]
力量体系: [类型]
核心规则: [驱动规则]
特点: [1-2句概括]

## 人物体系
characters:
  - id: protagonist_01
    姓名: [姓名]
    身份标签: [标签]
    性格: [性格]
    欲望: [欲望]
    恐惧: [恐惧]
    弧线: [起点→转折→高潮→终点]
    关系: [...]
    Reference: [待上传]

## 核心冲突
conflicts:
  - id: conflict_01
    类型: [类型]
    描述: [描述]
    涉及: [角色列表]

## 情绪主线
emotion:
  基调: [基调]
  爽点: [爽点列表]
  虐点: [虐点列表]

## 悬念设计
mysteries:
  - id: mystery_01
    类型: [类型]
    揭晓: [集数]
```

---

## 快速模式

当输入为"小说简介"而非完整文本时：

```
IF 输入长度 < 500字：
    → 启用快速模式
    → 基于简介推断世界观和人物
    → 标记"待补充"字段
    → 输出时明确标注哪些信息需要用户确认
```

**快速模式输出标注**：
```yaml
# 标注格式
[待确认] 某些字段
[推断] 某些字段（基于有限信息推断）
```

---

## 使用示例

### 示例输入

```
用户输入：
"都市玄幻小说，赘婿觉醒流。男主是大家族流落在外的血脉，
被丈母娘百般嫌弃。实际是顶级豪门失散的继承人，
拥有上古血脉和神秘传承。最终身份揭晓，吊打丈母娘。"
```

### 示例输出

```yaml
# IP档案 - 都市豪婿
> 生成时间: 2026-03-24
> 版本: v1.0
> 解析模式: 快速模式（基于简介）

## 基本信息
项目名: 都市豪婿
类型: 小说改编
集数: 12集
单集时长: 3-5分钟

## 世界观
时间背景: 现代都市
空间背景: 一二线城市
社会结构: 豪门家族 + 都市阶层
力量体系: 血脉传承 + 神秘异能
核心规则: 血统/实力/财富
特点: 都市外表下的玄幻内核，表面赘婿实则真龙

## 人物体系
characters:
  - id: protagonist_01
    姓名: [待确认]
    身份标签: 落魄赘婿 → 隐藏豪门继承人
    性格: [推断：表面隐忍，内心坚定]
    欲望: 翻身、证明自己
    恐惧: [待确认]
    弧线: 废柴→隐忍→觉醒→打脸→巅峰
    关系:
      antagonist_01: 丈母娘（敌对）
      protagonist_02: 妻子（待确认）
    Reference: 待上传

  - id: antagonist_01
    姓名: [待确认]
    身份标签: 刻薄丈母娘
    性格: 势利眼、狗眼看人低
    欲望: 攀附权贵、看不起女婿
    弧线: 嚣张→打脸→服软
    关系:
      protagonist_01: 丈母娘（敌对）
    Reference: 待上传

## 核心冲突
conflicts:
  - id: conflict_01
    类型: 身份打脸
    描述: 丈母娘看不起赘婿，实际赘婿是顶级豪门继承人
    涉及: [protagonist_01, antagonist_01]
    爆发点: 第N集身份揭晓

## 情绪主线
emotion:
  基调: 爽
  爽点:
    - 身份打脸
    - 逆袭成功
    - 真相大白
    - 强势反击
  虐点: [推断较少，主爽]

## 待确认事项
[待确认] 男主姓名
[待确认] 女主姓名和身份
[待确认] 丈母娘姓名
[待确认] 神秘传承具体内容
[待确认] 其他配角
```

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-03-24 | 初始版本 |
```

---

## Task 4: 实现 manzhou-script.md（剧本生成引擎）

**Files:**
- Create: `AI漫剧生产/skills/manzhou-script.md`

**Step 1: 编写剧本生成引擎 Skill**

（内容包含：剧本结构模板、分集剧本输出规范、场景设计方法论）

---

## Task 5: 实现 manzhou-storyboard.md（分镜输出引擎）

**Files:**
- Create: `AI漫剧生产/skills/manzhou-storyboard.md`

**Step 1: 编写分镜输出引擎 Skill**

（内容包含：镜头脚本模板、Seedance Prompt规范、Kling Prompt规范、导演指令集）

---

## Task 6: 实现 manzhou-safety.md（风控审核引擎）

**Files:**
- Create: `AI漫剧生产/skills/manzhou-safety.md`

**Step 1: 编写风控审核引擎 Skill**

（内容包含：敏感词库、审核维度、输出报告模板）

---

## Task 7: 实现 obsidian-storage.md（Obsidian存储规范）

**Files:**
- Create: `AI漫剧生产/skills/obsidian-storage.md`

**Step 1: 编写Obsidian存储规范**

（内容包含：目录结构规范、文件命名规范、frontmatter模板、双向链接规范）

---

## 执行顺序

```
Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7
(目录)  (主控)  (IP解析) (剧本)  (分镜)  (风控)  (存储)
```

---

## 验收标准

每个Skill文件必须包含：
1. 版本信息和职责说明
2. 完整的Role定义
3. 详细的执行流程
4. 完整的输出模板（无省略）
5. 至少2个使用示例
6. 错误处理规范

---

## 下一步

第一期完成后，进入第二期：
- manzhou-hit-engine.md（爆款算法）
- manzhou-visual-style.md（视觉风格库）
- manzhou-character-consistency.md（角色一致性）
