# TapNow 短剧制作全流程架构深度研究报告

> 研究日期：2026-03-25
> 研究对象：app.tapnow.ai Canvas 完整功能体系
> 研究范围：短剧/视频制作的完整流程、架构、Prompt模板

---

## 一、整体架构总览

### 1.1 产品定位

```
TapNow = AI视觉创作引擎
├── Canvas（无限画布）
│   ├── 节点系统（Node Graph）
│   ├── Agent对话系统
│   └── 资产管理
├── 视频生成（多模型）
│   ├── 图片生成（文生图/图生图）
│   ├── 视频生成（首帧/首尾帧）
│   └── 音频生成（配音/BGM/SFX）
└── 社区（TapTV）
```

### 1.2 核心模块关系图

```
┌─────────────────────────────────────────────────────────────────┐
│                         TapNow Canvas                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌─────────┐     ┌──────────┐     ┌────────────┐               │
│   │  灵感   │────▶│  分镜   │────▶│   视频    │               │
│   │  探索   │     │  策划   │     │   生成    │               │
│   └─────────┘     └──────────┘     └────────────┘               │
│       │               │                   │                     │
│       ▼               ▼                   ▼                     │
│   ┌─────────┐     ┌──────────┐     ┌────────────┐             │
│   │  情绪板 │     │  镜头表  │     │  剪辑合成  │             │
│   │  收集   │     │  输出    │     │            │             │
│   └─────────┘     └──────────┘     └────────────┘             │
│                                                                   │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │                    Agent 对话系统                         │    │
│   │  ├── 创作对话（灵感发散）                               │    │
│   │  ├── 分镜策划（镜头生成）                               │    │
│   │  └── 资产引用（@素材）                                  │    │
│   └─────────────────────────────────────────────────────────┘    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、创作流程详解（6大阶段）

### 2.1 流程图

```
阶段1          阶段2          阶段3          阶段4          阶段5          阶段6
灵感探索 ────▶ 分镜策划 ────▶ 视觉生成 ────▶ 视频合成 ────▶ 后期处理 ────▶ 导出发布
  │              │              │              │              │              │
  ▼              ▼              ▼              ▼              ▼              ▼
情绪板        镜头脚本       参考图         片段生成       剪辑合成       格式导出
素材收集      分镜表         风格图         分镜视频       音频配乐       分享发布
参考图        Keyframes      角色图         运镜图册       调色输出       社区投稿
```

### 2.2 各阶段核心功能

| 阶段 | 入口功能 | 核心产出 |
|------|---------|---------|
| **阶段1：灵感探索** | Agent对话 / 情绪板 | 参考图集 / 风格方向 |
| **阶段2：分镜策划** | 分镜策划节点 | 分镜表 / Keyframes |
| **阶段3：视觉生成** | 图片生成节点 | 参考图 / 角色图 / 风格图 |
| **阶段4：视频合成** | 视频生成节点 | 分镜视频片段 |
| **阶段5：后期处理** | 视频编辑节点 | 完整视频 |
| **阶段6：导出发布** | 导出功能 | 成品视频 |

---

## 三、节点系统（Node Graph）

### 3.1 节点类型总览

```
节点类型
├── 文本节点
│   ├── 对话（Agent）
│   ├── 脚本（广告词/文案）
│   └── 表格
│
├── 图片节点
│   ├── 文生图
│   ├── 图生图
│   └── 角色库
│
├── 视频节点
│   ├── 首帧生视频
│   ├── 首尾帧生视频
│   └── 视频编辑
│
├── 音频节点
│   └── 音乐/配音/音效
│
├── 分镜节点
│   ├── 分镜策划
│   └── 分镜头解析（拉片）
│
└── 快捷功能
    ├── 多机位九宫格
    ├── 电影级光影
    ├── 角色三视图
    ├── 画面推演+3s
    └── 画面推演-5s
```

### 3.2 节点数据结构

```javascript
// 节点基础结构
{
  id: "node_uuid",
  type: "image_node",           // 节点类型
  position: { x: 100, y: 200 }, // 画布位置
  data: {
    prompt: "生成描述",
    model: "model_name",
    params: { ... },
    src: "asset_url"            // 输出资源
  }
}

// 连接结构
{
  id: "edge_uuid",
  source: "node_a",
  target: "node_b",
  sourceHandle: "output",
  targetHandle: "input"
}
```

---

## 四、Prompt模板体系（核心发现）

### 4.1 分镜策划Prompt（5步分镜法）

```markdown
<goal>
The output will be used to create multi-angle AI video variations.
</goal>

<step 1 – scene breakdown>
Output (with subheadings):

* **Subjects:** Identify all visible subjects in the reference image;
  describe appearance, pose, facing direction, spatial position.
* **Environment & Lighting:** Describe the environment layout,
  background elements, materials, light direction/quality,
  time-of-day, and atmosphere.
* **Visual Anchors:** List 3–6 visual traits that must remain
  unchanged across all frames (color tone, key props, light
  direction, environmental markers, etc.).
</step 1 – scene breakdown>

<step 2 – theme>
Output a single sentence describing the mood/theme conveyed by
the original image (for stylistic coherence; does not change content).
</step 2 – theme>

<step 3 – cinematic approach>
Describe:

* **Shot strategy:** 9 frames covering a full range of perspectives
  and shot sizes (ELS, LS, MLS, MS, MCU, CU, ECU, high-angle,
  low-angle).
* **Camera approach:** fixed moment; only camera relocates
  (left/right, front/back, high/low, close/far).
* **Lens & DoF:** recommended focal lengths for each shot size
  and depth-of-field behavior.
* **Light & color:** must strictly match the reference image.
</step 3 – cinematic approach>

<step 4 – keyframes for AI video>
Output **9 keyframes**, using the format:

**[KF# | duration (sec) | shot type]**

* **Composition:** describe subject placement, perspective shift,
  foreground/mid/background.
* **Perspective:** describe camera position (e.g., left side,
  low-angle upshot, overhead, telephoto compression).
* **Camera:** height, angle, static or minimal motion.
* **Lens/DoF:** focal length, focus point, DoF depth.
* **Lighting/Grade:** identical to the reference image.

**Hard rules:**

* All 9 frames must preserve the same moment with zero
  pose/action changes.
* Includes mandatory shots:

  * 1 extreme wide
  * 1 wide
  * 1 medium-wide
  * 1 medium
  * 1 medium-close
  * 1 close-up
  * 1 extreme close-up
  * 1 high-angle view
  * 1 low-angle view
* **NO text, NO labels, NO graphics inside the images.**
</step 4 – keyframes for AI video>

<step 5 – contact sheet output>
You must output **ONE single master image**: a 3×3 cinematic
contact sheet containing all 9 keyframes.

Requirements:

1. 3×3 layout only.
2. Each frame = one unique camera angle/shot size.
3. No visual text labels inside any frame (strict).
4. Perfect continuity across all 9 frames.
5. After the master contact sheet, output the full KF text
   descriptions for rerendering any frame.
</step 5 – contact sheet output>

<final output format>
A) Scene Breakdown
B) Theme
C) Cinematic Approach
D) Keyframes
E) ONE 3×3 Master Contact Sheet Image
</final output format>
```

### 4.2 电影级光影Prompt（Roger Deakins级）

```markdown
(MASTER_CINEMATOGRAPHY_MODE: ON), act as a Roger Deakins-level
Director of Photography and Chief Lighting Technician.

**STRICT RULE:** You are NOT allowed to modify, alter, remove,
add, reshape, beautify, redesign, or change ANY original elements
of the image (characters, props, shapes, costume, makeup, environment,
framing, pose, anatomy, composition). You may ONLY adjust lighting,
exposure, shading, color temperature, volumetrics, and optical
characteristics. ALL structural, narrative, and visual content
MUST remain untouched.**

## [KNOWLEDGE BASE: LIGHTING PHYSICS & AESTHETICS]

1. **Motivated Lighting (Diegetic Only)**
   Every light must come from a logical in-scene source
   (window, lamp, moon, fire).
   **No artificial floating studio lights allowed.**

2. **Short Lighting Rule (Far-Side Key)**
   Key should illuminate the face *away* from camera,
   leaving camera-side in shadow.
   Avoid broad/flat lighting.

3. **Inverse Square Law**
   Light falloff must follow physics:
   Foreground brighter → midground → background unless
   intentional silhouette.

4. **Color Temperature Logic**
   * Fire/Candle/Tungsten: **1800–3200K** (warm amber)
   * Daylight/Moon: **5600–8000K** (cool cyan/teal)
   * Apply **warm key vs cool shadow** separation if
     contextually motivated.

5. **Material Physics (PBR Accuracy)**
   * **Skin**: Add SSS (subsurface scattering) &
     micro-red scatter at shadow edges
   * **Metals**: Add realistic specular anisotropy +
     Fresnel reflections

## [DIAGNOSTIC & REPAIR — LIGHTING ONLY]

### **STEP 1 — FIX LIGHT DIRECTION (MOLDING)**
* Detect the in-scene (diegetic) motivating source.
* Realign Key Light to match its direction.
* Add Negative Fill to deepen shadows and raise contrast
  to cinematic ratios (8:1–16:1).
* Remove flat frontal lighting.

### **STEP 2 — FIX COLOR GRADING (LIGHTING ONLY)**
* Warm up highlights if source is warm (fire/lamp).
* Cool shadows subtly for chromatic separation.
* Keep blacks clean.

### **STEP 3 — FIX TEXTURE & OPTICAL EFFECTS**
Apply ONLY lighting-related optical effects:
* Anamorphic lens glow, oval bokeh, barrel distortion
* Halation on bright light sources
* Film-grain lighting roll-off
* Restore pore texture via lighting micro-contrast

### **STEP 4 — VOLUMETRICS & AIR**
* Add haze, Tyndall scattering, god rays ONLY if motivated
  by the existing light.

## [EXECUTION PARAMETERS — LIGHTING ONLY]
Photorealistic, 8K, Arri Alexa 65, Panavision Primo 70,
Kodak Vision3 500T halation, path-traced global illumination
and reflections.
```

### 4.3 角色三视图Prompt

```markdown
<system_instruction>
  <role>
    You are a Lead Character Concept Artist for a AAA film studio.
  </role>
  <input_context>
    The user has provided a raw reference image. Your goal is to
    "standardize" this character into a production-ready asset.
  </input_context>
  <task>
    1. Analyze the character in the image strictly: Ethnicity, Age,
       Hairstyle, Facial Features, and Exact Outfit Details
       (materials, cuts, colors).
    2. DISCARD the original background, lighting, and pose.
    3. Write a text-to-image prompt to generate a
       "Character Turnaround Sheet".
  </task>
</system_instruction>
```

### 4.4 画面推演Prompt（3秒后）

```markdown
<system_instruction>
  <role>
    You are an Action Director and Physics Simulator.
  </role>
  <input_context>
    Treat the provided image as the "Start Frame" (Time = 0s)
    of a video clip.
  </input_context>
  <task>
    1. Analyze the implied motion vectors (e.g., Is the car moving?
       Is the person running? Is the gun firing?).
    2. Predict the physics state at Time = 3s (End Frame).
    3. Write a prompt for this "End Frame".
  </task>
  <logic_constraints>
    - STRICTLY KEEP: Character identity, clothes, environment
      style, lighting.
    - ONLY CHANGE: Pose, Position, and Effect (blur, smoke, debris).
    - Example: If Start Frame is "holding cup", End Frame might
      be "sipping from cup".
  </logic_constraints>
  <output_rules>
    - The prompt should start with:
      "A cinematic screenshot, 3 seconds later..."
    - Include keywords like: "Motion blur, dynamic action,
      aftermath, physics interaction."
    - RETURN ONLY THE PROMPT STRING.
  </output_rules>
</system_instruction>
```

### 4.5 画面推演Prompt（5秒前）

```markdown
<system_instruction>
  <role>
    You are an Action Director and Reverse-Physics Simulator.
  </role>

  <input_context>
    Treat the provided image as the "End Frame" (Time = 0s) of a
    video clip. Your goal is to imagine the "Start Frame"
    (Time = -3s).
  </input_context>

  <task>
    1. Analyze the current motion vectors and impact states
       (e.g., Is the glass broken? Is the car crashed?
       Is the runner mid-air?).
    2. Reconstruct the physics state at Time = -3s
       (Cause/Preparation).
    3. Write a prompt for this "Start Frame".
  </task>

  <logic_constraints>
    - STRICTLY KEEP: Character identity, clothes, environment
      style, lighting.
    - ONLY CHANGE: Pose, Position, and Object Integrity
      (restore broken objects, holster weapons, previous location).
    - Example: If End Frame is "sipping from cup", Start Frame
      might be "lifting cup from table".
  </logic_constraints>

  <output_rules>
    - The prompt should start with:
      "A cinematic screenshot, 3 seconds earlier..."
    - Include keywords like: "preparation, calm before action,
      anticipation, object integrity."
    - RETURN ONLY THE PROMPT STRING.
  </output_rules>
</system_instruction>
```

---

## 五、Agent对话系统

### 5.1 创作对话Prompt模板

```markdown
// 创作发散阶段（无素材时）
{
  "0": "先找个感觉",
  "0_prompt": "我现在还不太确定具体想做什么，你可以先帮我找一些整体氛围比较统一的参考吗？比如同一类风格或情绪的电影/画面，让我先找找感觉。",
  "1": "看看夜里",
  "1_prompt": "我想看看「夜晚」大概能拍出什么感觉，你可以帮我找一些夜景氛围很好的电影或画面参考吗？",
  "2": "雨天会怎样",
  "2_prompt": "如果是下雨天，这个世界/画面会变成什么样？你可以帮我找一些雨天氛围的参考让我看看吗？",
  // ... 更多发散选项
}

// 已有素材时的对话
{
  "0": "这场怎么拍",
  "0_prompt": "这场戏现在意思有了，但画面还没对，帮我找些接近的电影参考。",
  "1": "看看像哪部",
  "1_prompt": "你帮我找几部气质比较接近的片子，我想看看我现在这版更像哪一路。",
  "2": "先把气氛找准",
  "2_prompt": "这一段的气氛我还拿不准，帮我找些情绪和光线都接近的画面参考。",
  "3": "这段有点平",
  "3_prompt": "我感觉这一段画面有点太平了，帮我找些更有张力的参考让我看看。",
  "4": "人物怎么站",
  "4_prompt": "我想看看人物关系能怎么靠站位和景别拍出来，帮我找些这类画面。",
  "5": "室内怎么弄",
  "5_prompt": "这段多半要落在室内，帮我找些室内戏处理得很好的电影参考。",
  "6": "光还不太对",
  "6_prompt": "这段的光我还没想明白，帮我找些光影处理接近的画面参考。",
  "7": "还可以更压一点",
  "7_prompt": "这一段我想再压一点，帮我找些空间和氛围更有压迫感的参考。",
  "8": "也许该松一点",
  "8_prompt": "这儿也可能不用那么满，帮我找些更有留白和呼吸感的画面参考。",
  "9": "讲讲现在这版",
  "9_prompt": "你先帮我讲讲现在这版已经成立的东西是什么，重点到底落在哪。",
  "10": "接下来补哪里",
  "10_prompt": "如果顺着现在这条线走，下一步最该补哪一块，你直接告诉我。",
  "11": "先顺一顺",
  "11_prompt": "现在这些内容有点散，你先帮我顺一下，看怎么摆会更清楚。"
}
```

### 5.2 分镜策划Prompt

```markdown
storyboardPlaceholder: "说说你的创意，我来翻译成看得见的线稿镜头和画面节奏"

// 分镜推荐示例
storyboardRecommendations:
  - "为日式City Pop风格的夏日遗憾主题MV，需要一组怀旧胶片感镜头，包含海边奔跑、自动售货机、失焦的烟花等元素。"
  - "帮我为产品TapNow咖啡机创建30秒YouTube广告分镜。核心卖点是'3秒速热'..."
  - "20个镜头。这是修仙者与上古凶兽的决战。帮我设计'万剑归一'的特效分镜..."
```

---

## 六、景别体系（运镜标准）

### 6.1 9种标准景别

```
┌─────────────────────────────────────────────────────────────────┐
│                      景别体系（Shot Sizes）                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ELS (Extreme Wide Shot) ──── 极远景/交代镜头                   │
│         │                                                         │
│         ▼                                                         │
│   LS (Wide Shot) ──────── 远景/环境镜头                         │
│         │                                                         │
│         ▼                                                         │
│   MLS (Medium Wide Shot) ─ 中远景/全身镜头                       │
│         │                                                         │
│         ▼                                                         │
│   MS (Medium Shot) ────── 中景/膝上镜头                          │
│         │                                                         │
│         ▼                                                         │
│   MCU (Medium Close-Up) ─ 中近景/胸口以上                       │
│         │                                                         │
│         ▼                                                         │
│   CU (Close-Up) ──────── 近景/肩部以上                           │
│         │                                                         │
│         ▼                                                         │
│   ECU (Extreme Close-Up) 极特写/局部细节                        │
│                                                                   │
│   ─────────────────────────────────────────────────────────────  │
│                                                                   │
│   高角俯拍 (High-Angle) ──────── 俯视镜头                        │
│   低角仰拍 (Low-Angle) ──────── 仰视镜头                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 运镜描述规范

```javascript
// 运镜参数
{
  camera: {
    // 相机位置
    position: {
      azimuth: "left/right/front/back",
      elevation: "high/middle/low",
      distance: "close/far"
    },
    // 相机运动
    movement: "static/tracking/dolly/pan/tilt/crane",
    // 镜头参数
    lens: {
      focal_length: "wide/standard/telephoto",
      depth_of_field: "shallow/deep"
    }
  },
  // 光照要求
  lighting: {
    key_light: "方向",
    color_temperature: "warm/cool",
    quality: "hard/soft"
  }
}
```

---

## 七、分镜表数据结构

### 7.1 分镜表Schema

```json
{
  "storyboard": {
    "id": "storyboard_uuid",
    "title": "分镜标题",
    "duration": "总时长",
    "shots": [
      {
        "shot_number": 1,
        "start_time": "00:00:00",
        "duration": "2.8s",
        "description": "一名身穿花衬衫的男子站在便利店内，伸手整理头发，神情略显困惑。",
        "shot_type": "近景",
        "camera_angle": "平视镜头",
        "camera_movement": "固定镜头",
        "scene_label": "场景 1",
        "visual_prompt": "生成该镜头的参考图描述",
        "keyframes": [
          {
            "kf_number": 1,
            "shot_type": "Extreme Wide",
            "composition": "主体位置",
            "perspective": "相机位置"
          }
        ]
      }
    ]
  }
}
```

### 7.2 分镜表示例

```
┌────┬────────┬─────────────────────────────────────────────┬────────────┬────────────┬────────────┐
│ 镜 │  时长  │              分镜描述                        │  景别    │  相机角度  │  运镜    │
├────┼────────┼─────────────────────────────────────────────┼──────────┼──────────┼──────────┤
│  1 │  2.8s  │ 一名身穿花衬衫的男子站在便利店内，           │   近景    │  平视镜头   │ 固定镜头  │
│    │        │ 伸手整理头发，神情略显困惑。                   │           │            │          │
├────┼────────┼─────────────────────────────────────────────┼──────────┼──────────┼──────────┤
│  2 │  1.4s  │ 戴眼镜的店主坐在柜台后，看向顾客回答。        │  中近景   │  平视镜头   │ 固定镜头  │
├────┼────────┼─────────────────────────────────────────────┼──────────┼──────────┼──────────┤
│  3 │  0.9s  │ 货架上摆放整齐的几瓶草莓罐头。               │   特写     │  俯拍镜头   │ 固定镜头  │
└────┴────────┴─────────────────────────────────────────────┴──────────┴──────────┴──────────┘
```

---

## 八、快捷指令体系

### 8.1 5大快捷指令

```javascript
const shortcuts = [
  {
    id: "multi_angle_grid",
    title: "多机位九宫格",
    description: "基于关键帧参考图，从同一画面生成 9 种运镜角度参考。",
    icon: "mo",
    prompt: Ra.multi_angle_grid
  },
  {
    id: "cinematic_lighting",
    title: "电影级光影校正",
    description: "修正物理光照与色温逻辑，呈现专业电影质感。",
    icon: "Ob",
    prompt: Ra.cinematic_lighting
  },
  {
    id: "character_turnaround",
    title: "角色三视图生成",
    description: "一键生成角色三视图（正面/侧面/背面）。",
    icon: "zb",
    prompt: Ra.character_turnaround
  },
  {
    id: "scene_prediction",
    title: "画面推演 - 3秒后",
    description: "基于物理逻辑，生成3秒后的动作结果。",
    icon: "Ub",
    prompt: Ra.scene_prediction
  },
  {
    id: "scene_reconstruction",
    title: "画面推演 - 5秒前",
    description: "基于物理逻辑，反推5秒前的动作起因。",
    icon: "Vb",
    prompt: Ra.scene_reconstruction
  }
];
```

---

## 九、资产管理系统

### 9.1 角色库属性

```javascript
const characterAttributes = {
  // 基础属性
  imgFullBody: "角色立绘",
  imgCloseup: "肖像特写",
  imgExpression: "表情九宫格",
  imgThreeView: "三视图",

  // 分类属性
  attrEra: "大类",
  attrCulturalRegion: "文化区域",
  attrGenre: "题材",
  attrTimePeriod: "时代",
  attrScene: "场景",
  attrGender: "性别",
  attrAgeGroup: "年龄段",
  attrSpecies: "物种",

  // 外观属性
  attrPhysique: "体格",
  attrHeightLevel: "身高",
  attrSkinColor: "肤色",
  attrHairLength: "发长",
  attrHairColor: "发色",
  attrTemperament: "气质",

  // 描述区块
  sectionFeatures: "辨识特征",
  sectionOutfit: "着装描述",
  sectionAnchors: "视觉锚点"
};
```

### 9.2 角色合规验证

```javascript
const authenticityCheck = {
  // 允许
  accepted: [
    "原创角色",
    "AI 生成角色（含写实风格）"
  ],
  // 禁止
  prohibited: [
    "真人照片",
    "明星/公众人物肖像",
    "受版权保护的 IP 形象"
  ]
};
```

---

## 十、图片处理节点

### 10.1 图片生成参数

```javascript
const imageGenerationParams = {
  // 分辨率
  resolution: {
    "1K": "1024x1024",
    "2K": "2048x2048",
    "4K": "4096x4096"
  },
  // 宽高比
  aspectRatio: [
    "1:1", "4:3", "3:2", "16:9",
    "9:16", "3:4", "4:5", "2:3"
  ],
  // 生成次数
  generationTimes: [1, 2, 3, 4]
};
```

### 10.2 图片编辑功能

```javascript
const imageEditFunctions = {
  // 局部重绘
  localRedraw: {
    prompt: "局部重绘描述",
    mask: "用户绘制的蒙版"
  },
  // 扩图
  outpainting: {
    direction: "left/right/top/bottom",
    extendRatio: "扩展比例"
  },
  // 抠图
  matting: {
    type: "人像/物体/通用"
  },
  // 高清放大
  hdUpscale: {
    provider: "Topazlabs/Magnific",
    scaleFactor: "2x/4x/8x",
    style: "通用/低分辨率/3D动画/高保真/文字优化"
  },
  // 多角度生成
  multiAngle: {
    rotation: "水平旋转",
    tilt: "垂直倾斜",
    scale: "缩放",
    wideAngleLens: "广角镜头"
  },
  // 打光
  relight: {
    brightness: "亮度",
    colorTemp: "色温",
    mainLight: "主光源方向",
    rimLight: "轮廓光预设"
  }
};
```

---

## 十一、视频生成节点

### 11.1 视频生成模式

```javascript
const videoGenerationModes = {
  // 首帧生视频
  firstFrameToVideo: {
    description: "基于首帧图片生成视频",
    input: "首帧图片 + 运动描述"
  },
  // 首尾帧生视频
  firstLastFrameToVideo: {
    description: "基于首尾帧生成过渡视频",
    input: "首帧 + 尾帧 + 运动描述"
  }
};
```

### 11.2 视频编辑功能

```javascript
const videoEditFunctions = {
  trim: "裁剪片段",
  speed: "速度调整",
  reverse: "倒放",
  loop: "循环",
  transition: "转场",
  overlay: "叠加"
};
```

---

## 十二、架构特点总结

### 12.1 核心设计理念

| 理念 | 实现方式 | 价值 |
|------|---------|------|
| **节点化** | 所有功能抽象为节点 | 灵活组合/复用 |
| **对话驱动** | Agent理解自然语言 | 降低创作门槛 |
| **参考锚定** | Visual Anchors | 保持一致性 |
| **专业深度** | Hollywood知识库 | 输出专业品质 |

### 12.2 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | React | 组件化开发 |
| 状态管理 | Zustand/Context | 画布状态 |
| 图形引擎 | Fabric.js | Canvas渲染 |
| 音视频 | WebAV | 视频处理 |
| AI服务 | Gemini等多模型 | 生成能力 |
| 存储 | IndexedDB | 本地缓存 |
| CDN | 自建+云服务 | 资源分发 |

### 12.3 数据流

```
用户输入 → Agent解析 → 意图识别 → 节点生成 → AI推理 → 结果渲染
    │                                              │
    ▼                                              ▼
上下文关联                                    资产存储
    │                                              │
    └────────────────→ 画布状态 ←───────────────┘
```

---

## 十三、与漫舟对比

### 13.1 功能矩阵

| 功能 | TapNow | Manzhou |
|------|--------|---------|
| 视频上传 | ✅ | ❌ (剧本输入) |
| 一键拉片 | ✅ | ❌ |
| 分镜生成 | ✅ (Prompt驱动) | ✅ (模板) |
| 角色库 | ✅ (带属性) | ✅ (DNA锁) |
| 多机位 | ✅ (九宫格) | ❌ |
| 光影校正 | ✅ (专业级) | ❌ |
| 画面推演 | ✅ (+3s/-5s) | ❌ |
| 配音 | ✅ | ✅ |
| BGM | ✅ | ✅ |
| SFX | ✅ | ✅ |
| 视频合成 | ✅ | ❌ |
| 导出 | ✅ | ❌ |

### 13.2 Prompt体系对比

| 维度 | TapNow | Manzhou |
|------|--------|---------|
| 分镜Prompt | 5步结构化 | 7要素模板 |
| 景别体系 | 9种标准 | 自定义 |
| 光影知识 | Hollywood级 | 基础 |
| 运镜控制 | Prompt描述 | 参数控制 |
| 角色一致性 | Visual Anchors | DNA三层锁 |

---

## 十四、关键借鉴点

### 14.1 可直接复用

1. **景别体系** → 漫舟相机参数标准化
2. **九宫格Prompt** → 漫舟多机位功能
3. **Hollywood光影知识库** → 漫舟视觉风格库
4. **画面推演逻辑** → 漫舟闪回/预判镜头

### 14.2 需要改造

1. **视频拉片** → 改为剧本输入拉片
2. **对话驱动** → 改为模板驱动
3. **无限画布** → 保留线性流程

### 14.3 新增能力

1. **多机位九宫格** → 生成9种运镜参考图
2. **画面时间推演** → +3s/-5s物理预测
3. **专业光影预设** → 电影级调色

---

*研究报告完成*
