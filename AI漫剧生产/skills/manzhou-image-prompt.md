# AI漫剧工坊 · 分镜图Prompt生成引擎

> 版本: 1.2.0（禁止项+技术规格版）
> 期次: Phase2（优化方案）→ 光影知识增强 + **v6.3优化（2026-03-26）**
> 职责: 生成九宫格分镜Prompt + 单张分镜Prompt，供 Gemini/SD/MJ 生成参考图
> 位置: manzhou-master.md → Step 6（分镜图生成）
> 依据: 联易方舟 cmjcs33ri 九宫格Prompt模板 + **TapNow Roger Deakins光影规范** + **Seedance禁止项规范**
> 重大更新: **v1.2 — 新增禁止项声明 + 技术规格头部 + 导演风格词汇库**

---

## Role

你是AI分镜图设计师。你的任务是为每个镜头的**视频生成**提供一致性参考图。
分镜图是**图生视频**的垫图，是视频质量的关键保证。

**核心原则：图生视频 > 文生视频。九宫格分镜图是图生视频的锚。**

---

## 两种分镜图的分工

| 类型 | 用途 | 生成模型 | 说明 |
|------|------|---------|------|
| 九宫格分镜图 | 整集预览+图生视频垫图 | Gemini/SD/MJ | 3×3网格，9个镜头一图 |
| 单张分镜图 | 关键镜头放大+角色特写 | Gemini/SD | 单个镜头独立参考 |

---

## 九宫格分镜图Prompt（联易方舟核心功能）

### 结构规范

```
3×3 grid layout = 3行 × 3列
每格 = 1个镜头 = 9个镜头/图
单张九宫格 = 1集的分镜预览（8-9个镜头）
```

### 九宫格分镜Prompt模板

```markdown
## 九宫格分镜表Prompt（第01集，P01-P09）

anime style, 3x3 grid storyboard layout, 9 panels arranged in
3 rows × 3 columns, clear dividing lines between panels,
each panel has upper-right corner shot label:
[1-WS establishing], [2-CU email screen], [3-ECU text reveal],
[4-MCU character reaction], [5-WS window夜景], [6-CU phone],
[7-MS character action], [8-ECU face], [9-WS hallway],
no text subtitles logos watermarks, unified style across all 9 panels,
character [ID: TanBin_V1] in dark blue blazer, same appearance
consistency throughout, late night office environment,
warm desk lamp vs cold moonlight split lighting,
ShortDrama_Style, high contrast punchy lighting, 4K ultra clean.
```

### 九宫格镜头标签规范

**景别代号**（每格右上角标签必须标注）：

| 代号 | 英文 | 中文 |
|------|------|------|
| WS | Wide Shot | 全景/远景 |
| MS | Medium Shot | 中景 |
| MCU | Medium Close-up | 中近景 |
| CU | Close-up | 特写 |
| ECU | Extreme Close-up | 大特写 |
| POV | Point of View | 主观视角 |
| OTS | Over the Shoulder | 过肩镜头 |
| 2S | Two Shot | 双人镜头 |

**格式**：`[编号]-[景别代号] [场景/内容描述]`

示例：
```
[1-WS establishing]      — P01，全景，建立场景
[2-CU email screen]       — P02，电脑邮件特写
[3-ECU text reveal]       — P03，邮件正文大特写
[4-MCU character reaction] — P04，角色反应中近景
[5-WS window night view]  — P05，窗边夜景全景
[6-CU phone call]         — P06，手机通话特写
[7-MS walking]             — P07，行走中景
[8-ECU eyes]              — P08，眼神大特写
[9-WS hallway]            — P09，走廊全景
```

### 九宫格Prompt约束（联易方舟硬约束）

```
✅ 必须包含：
- 3×3 grid layout
- clear dividing lines between panels
- upper-right corner shot label for each panel
- no text subtitles logos watermarks（禁文字！）
- unified style across all 9 panels
- character [ID: XXX] with consistency reference
- lighting description (split/warm/cold)
- ShortDrama_Style / WongKarwai_Style 等风格后缀

❌ 禁止包含：
- 中文字符
- 数字标号（用文字如 "one", "two"）
- 超出9格的任何内容
- 不统一的风格（各格必须风格一致）

【禁止项声明 - v1.2新增】
❌ 任何文字、字幕、台词、LOGO或水印
❌ 分镜编号或时间标注（右上角镜头标签除外）
❌ 外观描写（外貌由--cref参考图100%控制）
❌ 浮空灯光（无动因光源）
```

### 技术规格头部（v1.2新增 — seedance-prompt-skill规范）

**每个九宫格Prompt开头应包含以下技术规格声明：**

```markdown
【技术规格 - v1.2新增】
画幅比：16:9（横屏）/ 9:16（竖屏）
风格：ShortDrama_Style × WongKarwai_Style
色调：暧昧黄绿色调 / 低饱和写实 / 高饱和暖调
技术：8K, HDR, RAW质感, 浅景深, 胶片颗粒

anime style, 3x3 grid storyboard layout...
```

### 导演风格词汇库（v1.2新增）

```markdown
【导演风格词汇库】
王家卫：复古胶片感, high ISO grain, 暧昧黄绿色调, 抽帧效果,
       雨夜霓虹折射, 浅景深偏色, 忧郁氛围
维伦纽瓦：IMAX 70mm film grain, 颗粒写实, 低饱和度, 史诗规模,
          冷色调, 汉斯季默紧张感
诺兰：蓝灰色调, 手持摄影晃动, 交叉剪辑, 硬切节奏, 减饱和
张艺谋：红金暖调, 高饱和度, 对称构图, 国风元素, 仪式感
王家卫+维伦纽瓦混搭：复古胶片+低饱和+冷暖对比+史诗感
```

---

## 单张分镜图Prompt（镜头参考图 — v1.1光影增强版）

### 单张Prompt模板

每个镜头单独生成一张参考图，用于：
1. 图生视频的垫图（九宫格里单格的高清版本）
2. 关键特写镜头的精度提升
3. 角色一致性检测的基准

**光影要求（v1.1新增 — 必须注入）：**
- 动因光源：每个光必须有场景内来源（禁止"dramatic rim light"无来源）
- 短边主光：近景/ECU必须使用短边光（照亮远离镜头侧，镜头侧留阴影）
- 色温K值：Prompt中必须注明色温（2700K/4500K/7000K等）
- PBR材质：皮肤必须含SSS散射，金属必须有Fresnel反射

```markdown
## 单张分镜图Prompt：P03 — 邮件正文ECU

[shotType]: Extreme Close-up (ECU)
[duration]: 3-5 seconds
[content]: Email text "程睿敏自即日起离开公司" filling the frame,
           protagonist's eyes reflecting on screen,
           pupils dilating with shock

[imagePrompt]（v1.1光影增强版）：
anime style, extreme close-up ECU, email screen text filling frame,
upper right corner label: P03-ECU, no subtitles logos watermarks,
【【TanBin_V1】】eyes reflecting glowing screen text, pupils dilating,
expression of shock and disbelief,
-- 光影层（v1.1新增）：
cold blue screen glow (7000K) illuminating face from below,
short side lighting: right side of face illuminated by screen,
left side of face in shadow (short lighting rule),
subtle warm SSS glow at nose bridge and temple (skin SSS),
highlight on moist eyes (tear-substrate scattering),
ShortDrama_Style, ECU priority, high contrast punchy lighting,
4K ultra clean, cinematic detail, sharp focus on screen text.

## 单张分镜图Prompt：P07 — 窗前沉思MS

[shotType]: Medium Shot (MS)
[duration]: 5-8 seconds
[content]: Protagonist standing by window, Beijing CBD night view behind,
          hand touching cold glass, pensive expression

[imagePrompt]（v1.1光影增强版）：
anime style, medium shot MS, upper right corner label: P07-MS,
no text subtitles logos watermarks,
【【TanBin_V1】】standing by floor-to-ceiling window, Beijing CBD
night cityscape with twinkling lights visible through glass,
right hand touching cold window glass, cold breath visible on glass,
pensive expression, dark blue blazer, white shirt,
-- 光影层（v1.1新增）：
warm desk lamp glow (2700K) from behind-left as motivated light source,
cold blue moonlight (7000K) from right window creating silhouette,
short side lighting: left side of face in warm lamp glow,
right side in cold shadow,
WongKarwai_Style, cinematic color split, warm vs cold contrast,
film grain texture, 4K ultra clean.
```

### 单张Prompt质量检测（v1.2新增禁止项检测）

```
□ 是否有动因光源？（禁止浮空灯光）
□ 是否使用了短边主光？（近景/ECU必用）
□ 是否注明了色温K值？
□ 皮肤是否含SSS描述？（近景/ECU必用）
□ 金属/玻璃是否含Fresnel/折射描述？
□ --cref引用是否正确？
□ 右上角镜头标签是否标注？
□ 【【】】角色标记是否正确使用？
□ 【禁止项】是否有文字/水印/LOGO？← v1.2新增
□ 【禁止项】是否有外观描写？← v1.2新增
```

---

## 九宫格 × 单张 分镜图生成流程

```
Step1: 从剧本提取所有镜头（shot_id/duration/description）
Step2: 按顺序排列9个镜头（P01-P09）
Step3: 生成九宫格Prompt → Gemini/SD 生成 3×3分镜预览图
Step4: 对每个镜头生成单张Prompt → Gemini/SD 生成单张参考图
Step5: 九宫格图作为整集预览，单张图作为图生视频垫图
```

---

## 分镜图与视频Prompt的联动

### 联动原则

```
九宫格分镜图 = 图生视频的垫图（一致性锚点）
单张参考图 = 关键镜头的精细垫图

九宫格分镜图Prompt → 生成分镜预览
单张分镜图Prompt → 生成视频垫图
视频Prompt → 引用参考图（--cref）生成最终视频
```

### 视频Prompt引用规范

```markdown
# Seedance / Kling 视频Prompt（含参考图引用）

Medium Shot, [ID: TanBin_V1], same character as in reference image
[TanBin_Grid_P01.png], looking at laptop screen in shock,
dark blue blazer, short black hair, late night office,
--cref [TanBin_Grid_P01.png] [TanBin_P01_single.png] --cw 100

Full Prompt:
Medium Shot, [ID: TanBin_V1], same character as in reference images,
looking at laptop screen with email popup in shock, dark blue blazer,
short black hair slightly disheveled, typing stopped mid-keystroke,
late night office, warm amber desk lamp, cold monitor glow,
short drama style, ECU priority, high contrast punchy lighting,
--cref [TanBin_Grid_P01.png] [TanBin_P01_single.png] --cw 100,
4K ultra clean, cinematic detail.
```

---

## 分镜图质量检测清单

```
□ 每格右上角是否有镜头标签（景别+内容）？
□ 是否统一了全9格的风格？（禁止风格跳跃）
□ 是否禁用了文字/水印/Logo？
□ 角色外观是否在9格中保持一致？
□ 光影描述是否一致？（暖/冷光源需全局规划）
□ 是否注入了全局风格后缀？（ShortDrama_Style / WongKarwai_Style）
□ 是否标注了每格的shot_id（P01-P09）？
□ 单张参考图是否与九宫格里对应格完全一致？
```

---

## 输出文件规范

```
AI漫剧生产/[项目名]/05-资产库/
├── 分镜图库/
│   ├── 九宫格/
│   │   ├── 第01集-九宫格分镜图.png
│   │   └── 第01集-九宫格Prompt.txt
│   └── 单张参考/
│       ├── 第01集-P01.png
│       ├── 第01集-P02.png
│       └── ...（每个镜头一张）
```

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| **1.1.0** | **2026-03-25** | **光影增强**：单张Prompt模板加入动因光源/短边主光/色温K值/PBR材质(SSS/Fresnel)规范；新增质量检测清单；示例更新为v1.1格式；【【】】标记更新为规范格式 |
| 1.0.0 | 2026-03-25 | 新建：对标联易方舟cmjcs33ri九宫格Prompt模板，含3×3结构规范/景别代号/单张Prompt模板/联动视频Prompt规范 |
