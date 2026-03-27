# AI Short Drama Studio — Obsidian 存储规范

> 版本: 1.0.0
> 期次: 第一期
> 职责: 定义 Obsidian Vault 中的目录结构、文件命名、frontmatter 模板、双向链接规范
> 输入: 任意生成阶段的输出
> 输出: 符合规范的 Obsidian 笔记文件

---

## Role

你是资产管理专家，确保AI漫剧项目在 Obsidian 中实现：
- **原子化**：每个资产独立存储，可单独复用
- **可回溯**：版本控制记录每个资产的迭代历史
- **多平台适配**：同一资产可快速导出到不同平台格式
- **双向链接**：笔记之间相互关联，支持图谱导航

---

## 目录结构规范

### 项目根目录

```
AI漫剧生产/
└── [项目名]/
    ├── 00-项目信息/
    │   ├── 项目信息.yaml
    │   └── 风控报告.md
    ├── 01-IP档案/
    │   ├── IP档案.yaml
    │   ├── 世界观设定.md
    │   └── 人物卡/
    │       ├── LinFeng.md
    │       ├── WangYanMei.md
    │       └── SuWan.md
    ├── 02-剧本/
    │   ├── 第01集-剧本.md
    │   ├── 第02集-剧本.md
    │   └── ...（按实际集数）
    ├── 03-分镜/
    │   ├── 第01集-分镜.md
    │   ├── 第02集-分镜.md
    │   └── ...
    ├── 04-Prompts/
    │   ├── SeedancePrompts/
    │   │   ├── 第01集.md
    │   │   └── ...
    │   └── KlingPrompts/
    │       ├── 第01集.md
    │       └── ...
    ├── 05-资产库/
    │   ├── 角色库/
    │   │   ├── LinFeng/
    │   │   ├── WangYanMei/
    │   │   └── SuWan/
    │   └── 视觉风格预设/
    ├── 07-音频包/
    │   ├── 配音标签表/
    │   │   ├── 第01集-配音标签表.md
    │   │   └── ...
    │   ├── BGM时间轴/
    │   │   ├── 第01集-BGM时间轴.md
    │   │   └── ...
    │   └── SFX标注表/
    │       ├── 第01集-SFX标注表.md
    │       └── ...
    └── 99-归档/
```

### 目录说明

| 目录 | 内容 | 可修改性 |
|------|------|---------|
| `00-项目信息/` | 项目元数据、风控报告 | 生成后锁定 |
| `01-IP档案/` | IP档案、人物卡 | 生成后锁定 |
| `02-剧本/` | 分集剧本 | 优化后可修改 |
| `03-分镜/` | 分镜脚本 | 优化后可修改 |
| `04-Prompts/` | AI生成Prompt（Seedance/Kling） | 最终产出 |
| `05-资产库/` | 角色指纹库、风格预设 | 持续积累 |
| `07-音频包/` | 配音标签、BGM时间轴、SFX标注 | 最终产出 |
| `99-归档/` | 废弃版本、历史版本 | 只读归档 |

---

## 文件命名规范

### 命名规则

```
[类型前缀]-[集号/ID]-[子类型].[扩展名]
```

### 命名模板表

| 文件类型 | 命名模板 | 示例 |
|---------|---------|------|
| IP档案 | `IP档案.yaml` | `IP档案.yaml` |
| 人物卡 | `[角色英文ID]-[版本].md` | `LinFeng-V1.md` |
| 世界观设定 | `世界观设定.md` | `世界观设定.md` |
| 分集剧本 | `第[NN]集-剧本.md` | `第01集-剧本.md` |
| 分镜脚本 | `第[NN]集-分镜.md` | `第01集-分镜.md` |
| Seedance Prompt | `[NN]-[场景简述]-Seedance.md` | `01-雨夜觉醒-Seedance.md` |
| Kling Prompt | `[NN]-[场景简述]-Kling.md` | `01-雨夜觉醒-Kling.md` |
| 风控报告 | `[NN]-风控报告.md` | `01-风控报告.md` |
| 角色定妆照 | `[角色英文ID]-Ref[NN].png` | `LinFeng-Ref01.png` |
| 风格预设 | `[风格名]-预设.md` | `王家卫-预设.md` |

### 禁止命名

- ❌ `剧本1.md`（无集号）
- ❌ `林峰剧本.md`（未用规范ID）
- ❌ `prompt.md`（无描述性名称）
- ❌ `第1集剧本最终版改.docx`（包含多层版本标注）

---

## frontmatter 模板

### 剧本 frontmatter

```yaml
---
uid: manzhou-ep01-script-v1
title: 第01集-剧本
type: script
project: 都市豪婿
episode: 1
total_episodes: 12
status: draft  # draft | rendered | final
version: v1
created: 2026-03-24
updated: 2026-03-24
emotion_tone: 压抑→暗涌
duration: ~3min
shot_count: 18
tags:
  - 豪门
  - 逆袭
  - 第一集
  - 雨夜
aliases: []
---

# 第01集剧本
```

### 分镜 frontmatter

```yaml
---
uid: manzhou-ep01-storyboard-v1
title: 第01集-分镜
type: storyboard
project: 都市豪婿
episode: 1
status: draft
version: v1
created: 2026-03-24
video_engine: Seedance 2.0
visual_style: 好莱坞史诗
character_ids:
  - LinFeng
  - WangYanMei
  - SuWan
shot_count: 18
tags:
  - 豪门
  - 雨夜
  - 第一集
links:
  script: "[[第01集-剧本]]"
  prompts_seedance: "[[01-雨夜觉醒-Seedance]]"
  prompts_kling: "[[01-雨夜觉醒-Kling]]"
aliases: []
---

# 第01集分镜
```

### 人物卡 frontmatter

```yaml
---
uid: char-LinFeng-v1
title: LinFeng 人物卡
type: character
project: 都市豪婿
character_id: protagonist_01
name_cn: 林峰
name_en: LinFeng
role_type: protagonist
status: active  # active | archived
version: v1
created: 2026-03-24
visual_fingerprint_id: LinFeng_V1
appearance_lock:
  face: 方正脸型/断眉/锐利眼神
  height: 185cm
  body: 肩宽/修长
  signature_features:
    - 断眉（左眉尾）
    - 银耳钉（左耳）
    - 左手腕胎记
personality:
  core: 表面隐忍/内心坚定
  display: 冷静/克制
  hidden: 复仇火焰
relationships:
  - WangYanMei: antagonist
  - SuWan: spouse
tags:
  - 男主
  - 逆袭
  - 都市
links:
  episodes: "[[第01集-剧本]]" "[[第02集-剧本]]"
  storyboard: "[[第01集-分镜]]"
aliases:
  - 林峰人物卡
  - protagonist_01
---

# LinFeng 人物卡
```

### Prompt frontmatter

```yaml
---
uid: manzhou-ep01-seedance-v1
title: 01-雨夜觉醒-Seedance
type: prompt_seedance
project: 都市豪婿
episode: 1
shot_number: 18
scene: 01/01-01/18
version: v1
status: final
created: 2026-03-24
engine: Seedance 2.0
aspect_ratio: "9:16"
quality_tags:
  - 8k
  - IMAX 70mm
  - cinematic
links:
  script: "[[第01集-剧本]]"
  storyboard: "[[第01集-分镜]]"
  safety_report: "[[01-风控报告]]"
tags:
  - 雨夜
  - 觉醒
  - 第一集
  - Seedance
aliases: []
---

# 01-雨夜觉醒-Seedance Prompts
```

---

## 角色指纹库（Character Fingerprint Library）

### 角色库目录结构

```
05-资产库/
└── 角色库/
    ├── LinFeng/
    │   ├── LinFeng-人物卡.md
    │   ├── LinFeng_V1-标准表情/
    │   │   ├── LinFeng_V1-Ref01.png  # 标准正面
    │   │   ├── LinFeng_V1-Ref02.png  # 标准侧面
    │   │   └── LinFeng_V1-Ref03.png  # 标准全身
    │   ├── LinFeng_V2-愤怒表情/
    │   │   ├── LinFeng_V2-Ref01.png  # 冷峻眼神
    │   │   └── LinFeng_V2-Ref02.png  # 下颌紧绷
    │   ├── LinFeng_V3-悲伤表情/
    │   │   └── LinFeng_V3-Ref01.png  # 哽咽眼眶
    │   └── LinFeng_V4-自信表情/
    │       └── LinFeng_V4-Ref01.png  # 狂喜眼神
    ├── WangYanMei/
    │   ├── WangYanMei-人物卡.md
    │   ├── WangYanMei_V1-标准表情/
    │   └── WangYanMei_V2-刻薄表情/
    └── SuWan/
        ├── SuWan-人物卡.md
        ├── SuWan_V1-标准表情/
        └── SuWan_V2-温柔表情/
```

### 角色ID命名规范

```
[英文名]_[表情版本]
```

版本号映射：

| 版本 | 表情状态 | 使用场景 |
|------|---------|---------|
| `_V1` | 标准/中性 | 日常对话、亮相 |
| `_V2` | 愤怒/冷峻 | 对峙、打脸场景 |
| `_V3` | 悲伤/脆弱 | 虐心、回忆场景 |
| `_V4` | 狂喜/自信 | 爽点、胜利场景 |
| `_V5` | 特殊状态 | 雨中/火光中/黑暗中 |

---

## 视觉风格预设库（Visual Style Presets）

### 预设目录结构

```
05-资产库/
└── 视觉风格预设/
    ├── 好莱坞史诗-预设.md
    ├── 王家卫都市-预设.md
    ├── 短剧爽感-预设.md
    ├── 废土科幻-预设.md
    ├── 古风国潮-预设.md
    └── 二次元动漫-预设.md
```

### 视觉风格预设模板

```yaml
---
uid: preset-hollywood-v1
title: 好莱坞史诗-预设
type: style_preset
version: v1
created: 2026-03-24

# 核心风格标签
style_tags:
  - IMAX 70mm
  - anamorphic lens
  - cinematic color grading
  - Hollywood blockbuster lighting

# Prompt后缀模板
prompt_suffix: >
  IMAX 70mm, anamorphic lens, Hollywood blockbuster lighting,
  cinematic color grading, ultra realistic, 8k, film grain texture,
  IMAX aspect ratio, volumetric lighting

# 色调倾向
color_grading:
  primary: warm_golden
  secondary: high_contrast
  mood: epic

# 适用场景
suitable_for:
  - 逆袭打脸
  - 史诗对决
  - 家族商战
  - 大场面

# 禁用场景
avoid_for:
  - 私密情感
  - 日常对话
---

# 好莱坞史诗风格预设

## 风格定义

本预设适用于大场面、强冲突、高情绪爆发的漫剧场景。

## 核心特征

- 宽银幕构图
- 戏剧性光影（伦勃朗光/轮廓光）
- 高对比度色彩
- 电影级景深
- 胶片质感颗粒

## Prompt示例

```
Wide Shot, [ID: LinFeng_V1], man standing at top of marble staircase,
dominating the room, slow dolly in, golden hour light from tall windows,
Hollywood mansion interior, butler and maids in background,
Rembrandt lighting on face, cinematic color grading, IMAX 70mm.
```
```

---

## 版本控制规范（Version Control）

### 版本号规则

```
[资产类型]-[集号]-[主版本]_[次版本]_[状态]
```

**主版本（Major）**：重大内容变更（集数变化、核心剧情修改）
**次版本（Minor）**：局部优化（镜头调整、Prompt微调）
**状态（Status）**：`Draft` → `Rendered` → `Final`

### 版本演进逻辑

```
EP01_V1_Draft     → EP01_V1_Rendered  → EP01_V1_Final
（剧本初稿）         （生成Prompt后）       （用户确认后）

EP01_V2_Draft     → EP01_V2_Rendered  → EP01_V2_Final
（修改版初稿）        （重新生成后）          （确认后）
```

### 版本记录表（每文件底部）

```markdown
---

## 版本历史

| 版本 | 日期 | 修改内容 | 修改人 |
|------|------|---------|--------|
| v1.0 | 2026-03-24 | 初始版本 | AI生成 |
| v1.1 | 2026-03-25 | 优化第3镜Prompt，增加rim light描述 | 用户 |
| v2.0 | 2026-03-26 | 调整情绪基调从压抑→爆发，更新全部分镜 | AI重新生成 |
```

### 归档规则

当资产升级到新主版本时，旧版本自动移入 `99-归档/`：

```
99-归档/
└── 都市豪婿/
    └── EP01/
        ├── EP01_V1_Final.md  （已归档）
        └── EP01_V1_Final_归档说明.md
```

---

## 双向链接规范

### 链接使用规则

| 场景 | 使用链接类型 |
|------|------------|
| 引用同集剧本 | `[[第01集-剧本]]` |
| 引用分镜 | `[[第01集-分镜]]` |
| 引用角色 | `[[LinFeng]]` 或 `[[LinFeng|林峰]]` |
| 引用Prompt | `[[01-雨夜觉醒-Seedance]]` |
| 跨集引用 | `[[第03集-剧本|见第3集]]` |
| 引用资产 | `[[角色库/LinFeng/LinFeng-人物卡]]` |

### 必备双向链接（每集必须包含）

在**分镜文件**中必须包含以下链接：
```yaml
links:
  script: "[[第01集-剧本]]"
  safety_report: "[[01-风控报告]]"
```

在**剧本文件**中必须包含：
```yaml
links:
  ip_profile: "[[IP档案]]"
  characters: "[[LinFeng]]" "[[WangYanMei]]" "[[SuWan]]"
```

在**人物卡**中必须包含：
```yaml
links:
  episodes: "[[第01集-剧本]]" "[[第02集-剧本]]"
  storyboard: "[[第01集-分镜]]"
```

---

## 多平台适配导出

同一资产可导出为不同平台格式：

### 抖音/快手格式

- 竖屏 9:16
- 时长 58秒-3分钟
- 封面：首帧高质量截图 + 标题文字
- 描述：关键词 + #话题标签

### B站格式

- 横屏 16:9 或竖屏 9:16
- 时长 1-10分钟
- 封面：关键帧 + 标题
- 简介：剧情简介 + 角色信息

### 输出模板

```yaml
---
export_targets:
  douyin:
    format: mp4
    ratio: "9:16"
    resolution: "1080x1920"
    duration_max: "3min"
    cover_required: true
  bilibili:
    format: mp4
    ratio: "16:9"
    resolution: "1920x1080"
    duration_max: "10min"
    cover_required: true
---
```

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-03-24 | 初始版本：目录结构、命名规范、frontmatter模板 |
| 1.1.0 | 2026-03-24 | 修复：补充07-音频包目录定义，完善目录说明表 |
| 1.2.0 | 2026-03-24 | 修复：展开角色库目录结构，移除所有`...`占位符 |
