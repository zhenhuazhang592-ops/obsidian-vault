# AI Short Drama Studio — 第二阶段优化方案

> 日期：2026-03-25
> 基准：竞品研究成果（联易方舟/TapNow/NanoPhoto）+ 当前13个Skill
> 目标：从"能用"升级到"专业级漫剧工作室"

---

## 一、优化背景：当前系统 vs 竞品差距

### 1.1 当前13个Skill完成度

| Skill | 版本 | 状态 | 与竞品差距 |
|-------|------|------|----------|
| manzhou-master | 1.5.0 | ✅ 完成 | 缺少@引用变量机制 |
| manzhou-ip-parser | ? | ✅ 完成 | 缺少别名aliases系统 |
| manzhou-script | 1.3.0 | ✅ 完成 | **缺少创意/大纲二级结构** |
| manzhou-storyboard | 2.1.0 | ✅ 完成 | 缺少固定时长/ID引用/多Shot |
| manzhou-hit-engine | ? | ✅ 完成 | OK |
| manzhou-visual-style | 1.0.0 | ✅ 完成 | **缺少11种预设完整描述** |
| manzhou-character-consistency | 1.2.0 | ✅ 完成 | 缺少别名aliases系统 |
| manzhou-voice | ? | ✅ 完成 | OK |
| manzhou-bgm | ? | ✅ 完成 | 缺少BPM精确参数 |
| manzhou-sfx | ? | ✅ 完成 | 缺少精确时间戳(0.1s) |
| manzhou-audio | ? | ✅ 完成 | OK |
| manzhou-safety | ? | ✅ 完成 | OK |
| obsidian-storage | ? | ✅ 完成 | **缺少CDP JSON Schema** |

### 1.2 竞品对比差距矩阵

| 能力项 | 漫舟现状 | 联易方舟 | TapNow | NanoPhoto | 差距级别 |
|--------|---------|---------|--------|---------|---------|
| 剧本二级结构 | 直接到剧本 | 创意→大纲→正文 | - | - | 🔴缺失 |
| CDP JSON Schema | 分散式输出 | **完整Schema** | - | - | 🔴缺失 |
| 角色ID引用 | 文本名 | ID引用(c_c1) | - | - | 🟡需升级 |
| 场景ID引用 | 文本名 | ID引用(l_l1) | - | - | 🟡需升级 |
| 道具系统 | **完全缺失** | 30道具完整档案 | - | - | 🔴缺失 |
| 增量追加机制 | **无** | 增量追加+版本历史 | - | - | 🔴缺失 |
| @引用变量机制 | **无** | @前5集/@大纲/@本集 | - | - | 🔴缺失 |
| 镜头时长固定秒数 | 范围(5-10s) | **固定15s** | - | - | 🟡需升级 |
| 视频多Shot格式 | 单段video_prompt | **多Shot分段** | - | - | 🟡需升级 |
| 11种风格预设 | 5种，描述不足 | **11种完整描述** | - | - | 🟡需升级 |
| 角色别名aliases | **无** | aliases[]数组 | - | - | 🟡需升级 |
| 润色工具库 | **无** | 19个润色模板 | - | - | 🟡需升级 |
| SFX精确时间戳 | 粗粒度 | - | - | **0.05s精度** | 🟡需升级 |
| 5灯灯光系统 | 隐含在光影 | - | **Hollywood 5灯** | **5灯分离** | 🟢可选 |
| 多机位九宫格 | 3x3固定 | 3x3固定 | **5步法** | - | 🟢可选 |
| 场景推演(3秒) | **无** | - | **前后推演** | - | 🟢可选 |
| 流式输出SSE | **无** | - | - | **SSE流式** | 🟢可选 |

---

## 二、优化方案：六大模块

### 模块A：剧本二级结构（新增2个Skill）

#### A1：新增 manzhou-concept（剧本创意）
**来源**：联易方舟 G1剧本创意（`cmj716f38...`）
**综合评分**：3.8

**功能**：
- 输入：题材/剧情类型/情绪/时代/角色设定
- 输出：N条差异化创意JSON

**Prompt核心约束（照搬联易方舟）**：
```
- 只输出一个JSON数组，禁止任何解释/前后缀/Markdown
- 输出必须为单行，首字符为[，末字符为]
- 必须可被JSON.parse直接解析
- 创意之间必须明显差异化（主角身份/人物关系/核心冲突/反转至少一项不同）
- title：8-18字，噱头强，暗示核心冲突或爽点
- description：80-150字，最后一句必须是钩子
```

**输出Schema**：
```json
[{
  "id": "c1",
  "title": "霸总隐藏身份被揭穿",
  "description": "..." // 包含钩子结尾
}]
```

#### A2：新增 manzhou-outline（剧本大纲）
**来源**：联易方舟 G2剧本大纲（`cmj716f3h...`）
**综合评分**：3.8

**功能**：
- 输入：选中的创意
- 输出：总大纲 + 人物小传 + 分集规划

**Prompt核心约束（照搬联易方舟）**：
```
- overview ≤ 200字
- characters：2-4人，每集hook/twist/endingHook ≤ 30字
- beats：每集3-5条，每条 ≤ 20字
- 第1集：立刻抛出主冲突与目标
- 每5集一个小高潮，每10集一个大反转
- 反转机制多样化（身份翻转/立场背刺/证据反杀/误会反转）
```

**输出Schema**：
```json
{
  "title": "...",
  "overview": "...",
  "characters": [{"name": "...", "arc": "..."}],
  "episodeCount": 12,
  "episodes": [{
    "episode": 1,
    "title": "...",
    "hook": "...",
    "beats": ["...", "..."],
    "twist": "...",
    "endingHook": "..."
  }]
}
```

---

### 模块B：资产包Schema统一（核心改造）

#### B1：制定 Manzhou CDP JSON Schema（新增规范文件）
**来源**：联易方舟 CDP JSON Schema（D1）
**综合评分**：4.4 | **最高优先级**

**意义**：统一所有Skill输出格式，实现：
1. 角色/场景/道具ID化（告别文本名）
2. 多集增量追加（复用已有资产）
3. 版本历史追踪
4. 与联易方舟数据互通

**Manzhou CDP Schema v1.0**：
```yaml
# manzhou-cdp-schema.yaml

version: "1.0"
format: "manzhou_comic_drama_package"

meta:
  projectId: string          # 项目唯一ID
  title: string             # 项目名
  totalEpisodes: number     # 总集数
  currentEpisode: number    # 当前集数
  style: string             # 风格预设
  aspectRatio: string       # 画幅 16:9/9:16/1:1
  shotDurationSec: number   # 单镜头固定秒数（默认10s）
  createdAt: string
  updatedAt: string

characters:  # 角色库（ID化）
  - id: "char_01"           # 角色ID
    name: "谭斌"              # 角色名
    aliases: ["Cherie", "谭女士", "糖饼"]  # 别名（新增！）
    gender: "female"
    ageRange: "30-35"
    appearance: "..."        # 外貌描述
    clothing: "..."          # 服饰描述
    persona: "..."           # 性格/人设
    referenceImage: "path"   # 参考图路径
    dnaAnchors:              # DNA锚点
      - type: "配饰"
        description: "左耳银色十字架耳钉"
      - type: "外貌"
        features: ["(sharp jawline:1.3)", "..."]

locations:  # 场景库（ID化）
  - id: "loc_01"
    name: "MPL公司写字楼"
    description: "现代写字楼，格子间分布"
    props: ["电脑", "会议桌", "电子门卡"]

items:  # 道具库（新增！漫舟目前缺失）
  - id: "item_01"
    name: "邮件通知"
    description: "指出程睿敏离职的电子邮件"
    appearance: "电脑屏幕浮动窗口，简洁英文内容"

episodes:
  - episodeNumber: 1
    shots:  # 镜头数组
      - id: "ep01_sh01"
        shotNumber: 1
        durationSec: 10        # 固定秒数（升级！）
        locationId: "loc_01"  # ID引用（升级！）
        characterIds: ["char_01"]
        itemIds: ["item_01"]
        script: "..."          # 镜头描述
        dialogue: [
          {"speakerId": "char_01", "text": "..."}
        ]
        imagePrompt: "..."      # 生图Prompt
        videoPrompt: "..."      # 视频Prompt（支持多Shot格式）
        objective: "..."        # 镜头目的
        action: "0-5s: ...; 5-10s: ..."  # 动作时间轴
        vo: "..."               # 配音文本
        bgm: "..."              # BGM描述
        sfx: "..."              # 音效
        emotionCurve: "紧张↑"  # 情绪标注
        status: "pending"        # pending/generating/completed
```

#### B2：升级 manzhou-script（增强@引用机制）
**来源**：联易方舟 G3剧本正文 + D5 @引用变量
**综合评分**：4.2

**新增功能**：
1. @引用变量机制（上下文追踪）
2. 台词规范（≤15字，口语化）
3. 开场5秒抓人规则强化

**Prompt增强**：
```
剧本正文生成时，支持以下@引用：
- @前5集剧本正文 → 保持剧情连贯
- @剧本大纲 → 保持总纲一致
- @本集剧情目标 → 聚焦本集任务
- @角色档案 → 保持人设一致
```

#### B3：新增 manzhou-item-generator（道具生成）
**来源**：联易方舟 A5道具物品图（`cmjdxpc1s...`）
**综合评分**：4.2

**功能**：为道具库中的每个道具生成参考图

**Prompt模板（照搬联易方舟）**：
```
请生成"道具/物品参考图"单张图片：主体清晰、材质细节明确、
背景干净、无文字/无水印。

物品名：${name}
物品描述：${description}
外观：${appearance}
```

---

### 模块C：分镜系统升级

#### C1：升级 manzhou-storyboard（固定时长+多Shot）
**来源**：联易方舟 C1 CDP分镜脚本 + S1九宫格
**综合评分**：4.4 + 4.6

**升级项**：
1. 镜头时长从"范围"升级为"固定秒数"
2. 角色/场景引用从"文本名"升级为"ID引用"
3. videoPrompt升级为多Shot格式

**videoPrompt多Shot格式（新增）**：
```
Global Context: no text, no subtitles, no music, no logo
Shot 1 / Duration: 5 sec / Scene: [描述]
Shot 2 / Duration: 5 sec / Scene: [描述]
各Shot Duration之和 ≈ durationSec（±1秒）
```

#### C2：升级 manzhou-visual-style（11种预设完整描述）
**来源**：联易方舟 11种风格预设
**综合评分**：4.0

**当前**：漫舟只有5种风格，描述不足
**升级**：补全11种风格预设的完整描述文本

| ID | 名称 | 状态 |
|----|------|------|
| anime | 日漫 | 已有，需完善 |
| cn_anime | 国风动漫 | **需新增** |
| cn_3d | 国风3D | **需新增** |
| ink | 水墨国风 | **需新增** |
| cyber | 赛博朋克 | **需新增** |
| us_comics | 美漫 | **需新增** |
| real | 写实 | **需新增** |
| horror | 恐怖惊悚 | **需新增** |
| pixar | 皮克斯 | **需新增** |
| shinkai | 新海诚 | **需新增** |
| miyazaki | 宫崎骏 | **需新增** |

**每种预设完整描述格式（照搬联易方舟）**：
```
cn_anime（国风动漫）:
国风美术与动画质感结合，色彩典雅，
融合中国传统美学元素与现代动画技术，
人物形象符合中国审美，服饰细节考究，
背景呈现中式建筑/山水/室内场景。
```

#### C3：升级 manzhou-character-consistency（别名aliases）
**来源**：联易方舟 D6角色别名
**综合评分**：3.6

**新增字段**：角色aliases[]数组
```
aliases: ["Cherie", "谭女士", "糖饼"]
```
用于剧本中同一角色的多称呼归一。

---

### 模块D：音频系统增强

#### D1：升级 manzhou-sfx（精确时间戳）
**来源**：NanoPhoto N1 SFX Cue精确到0.05s
**综合评分**：3.6

**当前**：粗粒度音效标注
**升级**：精确到0.1s（NanoPhoto做到0.05s）

**新格式**：
```
SFX时间戳格式：
[00:00.0] 咖啡杯轻碰
[00:03.2] 键盘打字开始
[00:07.8] 键盘打字停止
```

#### D2：升级 manzhou-bgm（BPM参数）
**来源**：NanoPhoto N1 BGM BPM/crossfades
**综合评分**：3.4

**新增字段**：
```
BGM参数：
- 风格：悬疑/温情/燃向
- BPM：60/80/120
- 时长：30s/60s
- Crossfade点：[00:15]渐入，[00:45]渐出
```

---

### 模块E：工作流增强

#### E1：新增 manzhou-incremental（增量追加机制）
**来源**：联易方舟 D2 增量追加机制
**综合评分**：4.4

**功能**：支持多集/多章节制作时复用已有资产

**机制**：
```
增量追加规则：
1. 读取已有CDP JSON（包含characters/locations/items）
2. 新集生成时：
   - 同名角色 → 复用已有ID
   - 同名场景 → 复用已有ID
   - 新角色/场景 → 自动分配新ID
3. shotNumber从1开始，系统自动偏移到全局序号
4. 支持"设为基准"重置增量起点
```

#### E2：新增 manzhou-polish（润色工具）
**来源**：联易方舟 G5 润色工具（19个模板）
**综合评分**：4.2 | **高优先级**

**功能**：去除AI生成痕迹，提升文稿质量

**19个润色方向**：
```
- 去AI味
- 提升文采
- 口语化
- 情绪强化
- 节奏加快
- 细节丰富
- 对话自然化
- 心理描写内敛
- 动作描写具体化
- 场景描写生动
- 台词简短化
- 钩子强化
- 过渡自然
- 人设强化
- 爽点放大
- 虐点深化
- 甜度提升
- 悬念增强
- 反转自然化
```

#### E3：新增 manzhou-cost-estimator（成本估算）
**来源**：联易方舟 D4 灵石定价体系
**综合评分**：3.6

**功能**：为每个项目估算生成成本

**成本表（基于联易方舟灵石体系）**：
| 操作 | 成本 | 备注 |
|------|------|------|
| 角色卡生成 | ¥0.02-0.10 | 取决于模型 |
| 场景基底图 | ¥0.02-0.10 | 同上 |
| 九宫格分镜图 | ¥0.02-0.07 | Nano Banana最快 |
| 镜头视频(10s) | ¥0.14 | Sora2最优性价比 |
| 镜头视频(15s) | ¥0.14 | Sora2 |
| TTS配音 | ¥0.006/200字 | tts-1基础 |
| TTS高清配音 | ¥0.012/200字 | tts-1-hd |

---

### 模块F：视觉系统可选增强

#### F1：新增 manzhou-cinematic-lighting（5灯灯光系统）
**来源**：TapNow T2 + NanoPhoto N1
**综合评分**：4.0

**5灯系统**：
```
key light    — 主光（塑造主体形态）
rim light    — 轮廓光（主体与背景分离）
fill light  — 补光（减少阴影）
kicker light — 强化轮廓（通常在key对面）
negative fill — 负补光（加深阴影，增加戏剧感）
```

#### F2：新增 manzhou-scene-predictor（场景推演）
**来源**：TapNow T4 Scene Prediction +3s / T5 Reconstruction -5s
**综合评分**：4.0

**功能**：基于当前镜头，自动推演3秒后/5秒前的画面

**Prompt模板（TapNow照搬）**：
```
画面推演3秒后：
- STRICTLY KEEP: Character identity, clothes, environment, lighting
- ONLY CHANGE: Pose, Position, Effect
- 适用于：动作连续性、自然过渡

画面推演5秒前：
- 预测当前动作的前因
- 保持物体完整性（如：碎玻璃→完整玻璃）
- 适用于：因果逻辑验证
```

---

## 三、优化优先级与工作量估算

### 优先级矩阵

| 优先级 | 模块 | 优化项 | 工作量 | ROI | 来源 |
|--------|------|--------|--------|-----|------|
| 🔴 P0 | 模块B | CDP JSON Schema统一 | 中 | 极高 | 联易方舟 |
| 🔴 P0 | 模块B | 角色/场景ID化引用 | 中 | 极高 | 联易方舟 |
| 🔴 P0 | 模块B | 道具系统(manzhou-item) | 高 | 高 | 联易方舟 |
| 🔴 P0 | 模块C | 镜头时长固定秒数 | 低 | 高 | 联易方舟 |
| 🔴 P0 | 模块A | manzhou-concept新增 | 中 | 高 | 联易方舟 |
| 🔴 P0 | 模块A | manzhou-outline新增 | 中 | 高 | 联易方舟 |
| 🔴 P0 | 模块E | manzhou-incremental增量机制 | 高 | 极高 | 联易方舟 |
| 🟡 P1 | 模块B | manzhou-script增强@引用 | 低 | 高 | 联易方舟 |
| 🟡 P1 | 模块C | manzhou-visual-style 11种预设 | 中 | 中 | 联易方舟 |
| 🟡 P1 | 模块C | manzhou-character aliases别名 | 低 | 中 | 联易方舟 |
| 🟡 P1 | 模块D | manzhou-sfx精确时间戳 | 低 | 中 | NanoPhoto |
| 🟡 P1 | 模块E | manzhou-polish润色工具 | 中 | 高 | 联易方舟 |
| 🟢 P2 | 模块D | manzhou-bgm BPM参数 | 低 | 中 | NanoPhoto |
| 🟢 P2 | 模块C | videoPrompt多Shot格式 | 低 | 中 | 联易方舟 |
| 🟢 P2 | 模块E | manzhou-cost-estimator成本估算 | 低 | 低 | 联易方舟 |
| 🟡 P3 | 模块F | manzhou-cinematic-lighting | 高 | 中 | TapNow |
| 🟡 P3 | 模块F | manzhou-scene-predictor | 高 | 中 | TapNow |

### 实施顺序建议

```
第一阶段（第02集生产前必须完成）：
  [B1] CDP JSON Schema 制定
  [B2] 角色/场景ID化引用
  [B3] 道具系统
  [C1] 镜头时长固定秒数
  [A1] manzhou-concept
  [A2] manzhou-outline
  [E1] manzhou-incremental

第二阶段（第02集生产中迭代）：
  [B1增强] manzhou-script @引用机制
  [C2] manzhou-visual-style 11种预设
  [C3] manzhou-character aliases
  [E2] manzhou-polish润色工具

第三阶段（系统完善后）：
  [D1] manzhou-sfx精确时间戳
  [D2] manzhou-bgm BPM参数
  [C2增强] videoPrompt多Shot格式
  [E3] manzhou-cost-estimator

第四阶段（可选，差异化）：
  [F1] manzhou-cinematic-lighting
  [F2] manzhou-scene-predictor
```

---

## 四、优化后系统架构

### 4.1 升级后的Skill清单

| # | Skill名 | 版本 | 变化 | 来源 |
|---|---------|------|------|------|
| 1 | manzhou-master | 2.0.0 | 增加@引用/CDP Schema | 联易方舟 |
| 2 | manzhou-ip-parser | 2.0.0 | 增加aliases别名系统 | 联易方舟 |
| 3 | **manzhou-concept** | 1.0.0 | **🆕新增** | 联易方舟G1 |
| 4 | **manzhou-outline** | 1.0.0 | **🆕新增** | 联易方舟G2 |
| 5 | manzhou-script | 2.0.0 | @引用机制/台词规范 | 联易方舟G3 |
| 6 | manzhou-hit-engine | 2.0.0 | OK | - |
| 7 | manzhou-visual-style | 2.0.0 | 11种预设完整描述 | 联易方舟 |
| 8 | manzhou-character-consistency | 2.0.0 | aliases别名 | 联易方舟 |
| 9 | **manzhou-item-generator** | 1.0.0 | **🆕新增** | 联易方舟A5 |
| 10 | manzhou-storyboard | 3.0.0 | 固定时长/ID引用/多Shot | 联易方舟 |
| 11 | manzhou-voice | 2.0.0 | OK | - |
| 12 | manzhou-bgm | 2.0.0 | BPM参数 | NanoPhoto |
| 13 | manzhou-sfx | 2.0.0 | 精确时间戳 | NanoPhoto |
| 14 | manzhou-audio | 2.0.0 | OK | - |
| 15 | manzhou-safety | 2.0.0 | OK | - |
| 16 | **manzhou-incremental** | 1.0.0 | **🆕新增** | 联易方舟 |
| 17 | **manzhou-polish** | 1.0.0 | **🆕新增** | 联易方舟G5 |
| 18 | **manzhou-cost-estimator** | 1.0.0 | **🆕新增** | 联易方舟 |
| 19 | **manzhou-cinematic-lighting** | 1.0.0 | **🆕可选** | TapNow |
| 20 | **manzhou-scene-predictor** | 1.0.0 | **🆕可选** | TapNow |
| 21 | **manzhou-cdp-schema** | 1.0.0 | **🆕规范文件** | 联易方舟 |

**总计**：13个现有Skill → 21个Skill文件
**新增**：8个Skill + 1个Schema规范
**改造**：10个现有Skill版本升级

### 4.2 升级后的工作流

```
用户输入（小说/IP/大纲）
        ↓
[1] manzhou-ip-parser → IP档案（含aliases）
        ↓
【🆕新增】[2] manzhou-concept → N条差异化创意
        ↓
【🆕新增】[3] manzhou-outline → 总大纲 + 分集hook/twist
        ↓
[4] manzhou-script → 分集剧本（含@引用）
        ↓
[5] manzhou-hit-engine → 爆款检测
        ↓
[6] manzhou-visual-style → 视觉风格（含11种预设）
        ↓
[7] manzhou-character-consistency → DNA手册 + 九宫格（含aliases）
        ↓
【🆕新增】[8] manzhou-item-generator → 道具参考图
        ↓
[9] manzhou-storyboard → 分镜Prompt（固定时长/ID引用/多Shot）
        ↓
[10] manzhou-voice → 配音标签
        ↓
[11] manzhou-bgm → BGM时间轴（含BPM）
        ↓
[12] manzhou-sfx → SFX标注（精确时间戳）
        ↓
[13] manzhou-audio → 三轨整合
        ↓
[14] manzhou-safety → 风控报告
        ↓
【🆕新增】[15] manzhou-polish → 润色（如需要）
        ↓
【🆕新增】[16] manzhou-incremental → 增量追加（第02集复用）
```

---

## 五、与第02集生产的衔接

### 5.1 优化与生产的节奏

```
方案：优化和生产并行

第02集生产前：
  → 完成P0全部（Schema/ID引用/道具/固定时长/concept/outline/incremental）
  → 这6项优化直接影响第02集质量

第02集生产中：
  → 用第02集验证新Schema
  → 发现问题及时迭代优化

第02集生产后：
  → 完成P1优化
  → 收集第02集反馈，更新优化方案
```

### 5.2 优化对第02集的价值

| 优化项 | 对第02集的价值 |
|--------|--------------|
| CDP JSON Schema | 多集数据统一管理 |
| ID化引用 | 第02集复用第01集角色/场景 |
| 道具系统 | 第02集新场景有道具支持 |
| 固定时长 | 分镜更精确 |
| manzhou-concept | 更优质的第02集立项 |
| manzhou-outline | 更清晰的分集规划 |
| manzhou-incremental | **最关键**：第02集复用第01集资产 |
| manzhou-polish | 提升第02集文稿质量 |

---

*方案完成 — 2026-03-25*
