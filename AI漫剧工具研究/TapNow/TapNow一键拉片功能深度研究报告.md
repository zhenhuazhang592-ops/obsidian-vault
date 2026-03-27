# TapNow 一键拉片功能深度研究报告

> 研究日期：2026-03-25
> 研究对象：app.tapnow.ai Canvas 功能模块
> 研究范围：一键拉片（Shot Breakdown / Film Analysis）功能

---

## 一、产品定位与功能概述

### 1.1 功能入口

| 入口位置 | 描述 |
|---------|------|
| 底部工具栏 | 左下角红色圆形图标按钮 |
| 视频标签页 | 视频播放器下方 |
| Canvas节点 | 通过"分镜头解析"节点 |

### 1.2 功能名称（多语言）

| 语言 | 功能名称 |
|------|---------|
| 中文 | 一键拉片 / 分镜头解析 |
| 英文 | Shot Breakdown / Film Analysis |
| 日文 | ショット分解 / 映画分析 |
| 韩文 | 샷 분석 / 영화 분석 |

### 1.3 定价模式

```
分镜头解析（每30秒75Tapies）
```

- 计费单位：每30秒视频 = 75 Tapies
- 预计耗时：5-10分钟

---

## 二、底层架构分析

### 2.1 技术架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    TapNow Canvas 前端                        │
├─────────────────────────────────────────────────────────────┤
│  视频输入 → 分镜节点 → AI解析引擎 → 分镜表输出               │
│     ↓           ↓            ↓           ↓                  │
│  视频文件    Video Node   Backend API   Shot Table          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Backend API 服务                          │
├─────────────────────────────────────────────────────────────┤
│  POST /api/canvas/v1/asset-reviews                        │
│  - 视频帧提取                                              │
│  - AI场景分析                                              │
│  - 分镜输出                                                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心API端点

```
https://app.tapnow.ai/api/canvas/v1/asset-reviews
```

### 2.3 资源文件结构

```
https://fe-assets.tapnow.top/
├── assets/
│   ├── index-DEsqSklO.js          # 主应用JS (~896KB)
│   ├── vendor-pkg-canvas-Bo6fvKxS.js  # Canvas模块JS (~1.5MB)
│   ├── vendor-dexie-DKLp6sVo.js    # 本地数据库
│   ├── vendor-webav-BOhtjtmb.js     # WebAV音视频处理
│   ├── vendor-echarts-gwfkJyXx.js  # 图表库
│   └── ...
```

---

## 三、Prompt模板体系（核心发现）

### 3.1 多角度九宫格生成（Multi-Angle Grid）

**功能定位**：基于单张参考图，生成9种运镜角度的参考图

**完整Prompt模板**：

```markdown
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

### 3.2 电影级光影校正（Cinematic Lighting）

**功能定位**：修正物理光照与色温逻辑，呈现专业电影质感

**完整Prompt模板**：

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

Apply the following "Hollywood Lighting Physics & Aesthetics
Knowledge Base" to analyze and correct ONLY THE LIGHTING
of the image:

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
     Apply **warm key vs cool shadow** separation if
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

### 3.3 角色三视图生成（Character Turnaround）

**功能定位**：一键生成角色三视图（正面/侧面/背面）

**Prompt模板**：

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

### 3.4 画面推演 - 3秒后（Scene Prediction）

**功能定位**：基于物理逻辑，生成3秒后的动作结果

**Prompt模板**：

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

### 3.5 画面推演 - 5秒前（Scene Reconstruction）

**功能定位**：基于物理逻辑，反推5秒前的动作起因

**Prompt模板**：

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

## 四、快捷指令体系

### 4.1 全部快捷指令

| ID | 英文名称 | 中文名称 | Prompt变量 |
|----|---------|---------|-----------|
| multi_angle_grid | Multi-Angle Grid | 多机位九宫格 | `Ra.multi_angle_grid` |
| cinematic_lighting | Cinematic Lighting | 电影级光影校正 | `Ra.cinematic_lighting` |
| character_turnaround | Character Turnaround | 角色三视图生成 | `Ra.character_turnaround` |
| scene_prediction | Scene Prediction +3s | 画面推演 - 3秒后 | `Ra.scene_prediction` |
| scene_reconstruction | Scene Reconstruction | 画面推演 - 5秒前 | `Ra.scene_reconstruction` |

### 4.2 快捷指令数据结构

```javascript
Hr = [
  {
    id: "multi_angle_grid",
    icon: t.jsx(mo, {className: "w-5 h-5"}),
    titleKey: "nodes.slashCommands.multiAngleGrid.title",
    descriptionKey: "nodes.slashCommands.multiAngleGrid.description",
    prompt: Ra.multi_angle_grid
  },
  // ... 其他指令
]
```

---

## 五、分镜表数据结构

### 5.1 分镜表字段

| 字段 | 描述 | 示例 |
|------|------|------|
| shot_number | 镜头编号 | 1, 2, 3... |
| duration | 时长（秒） | 2.8s, 1.4s |
| description | 分镜描述 | "一名身穿花衬衫的男子站在便利店内，伸手整理头发，神情略显困惑。" |
| shot_type | 镜头类型 | 近景、中近景、特写 |
| camera_angle | 相机角度 | 平视镜头、俯拍镜头、仰拍镜头 |
| camera_movement | 运镜方式 | 固定镜头 |
| scene_label | 场景标签 | 场景 1, 场景 2 |

### 5.2 分镜表示例

```
┌────┬────────┬─────────────────────────────────────────────┬────────────┬────────────┐
│ 镜 │  时长  │              分镜描述                       │  镜头类型  │  相机角度  │
├────┼────────┼─────────────────────────────────────────────┼────────────┼────────────┤
│  1 │  2.8s  │ 一名身穿花衬衫的男子站在便利店内，             │   近景     │  平视镜头   │
│    │        │ 伸手整理头发，神情略显困惑。                   │            │            │
├────┼────────┼─────────────────────────────────────────────┼────────────┼────────────┤
│  2 │  1.4s  │ 戴眼镜的店主坐在柜台后，看向顾客回答。        │  中近景    │  平视镜头   │
├────┼────────┼─────────────────────────────────────────────┼────────────┼────────────┤
│  3 │  0.9s  │ 货架上摆放整齐的几瓶草莓罐头。               │   特写     │  俯拍镜头   │
└────┴────────┴─────────────────────────────────────────────┴────────────┴────────────┘
```

---

## 六、与漫舟（Manzhou）对比分析

### 6.1 功能对比

| 功能 | TapNow | Manzhou |
|------|--------|---------|
| 视频分镜解析 | ✅ 一键拉片 | ❌ 需手动输入剧本 |
| 镜头类型 | ✅ 自动识别 | ✅ 模板选择 |
| 相机角度 | ✅ 自动推断 | ✅ 模板选择 |
| 运镜方式 | ✅ 自动推断 | ✅ Prompt注入 |
| 多机位生成 | ✅ 九宫格 | ❌ 需多次生成 |
| 光影校正 | ✅ 电影级光影 | ❌ 依赖视觉风格 |

### 6.2 Prompt架构对比

| 维度 | TapNow | Manzhou |
|------|--------|---------|
| 分镜粒度 | 镜头级（Shot） | 镜头级（Shot） |
| 运镜控制 | 通过Prompt描述 | 通过相机参数Yaw/Pitch |
| 角色一致性 | 依赖Visual Anchors | DNA三层锁机制 |
| 音频注入 | ❌ | ✅ VO/BGM/SFX三要素 |

### 6.3 可借鉴点

1. **Scene Prediction/Reconstruction**：视频推演逻辑可用于漫舟的"场景推演"模块
2. **Multi-Angle Grid**：多机位九宫格可用于漫舟的分镜增强
3. **电影级光影知识库**：Hollywood Lighting Physics可用于漫舟的视觉风格库

---

## 七、技术实现细节

### 7.1 视频处理管线

```
视频上传 → 帧提取 → 关键帧选择 → AI分析 → 分镜输出
    ↓          ↓            ↓          ↓         ↓
  视频文件   WebAV库    时间点采样   LLM推理   分镜表
```

### 7.2 关键依赖

| 库名 | 用途 |
|------|------|
| `vendor-webav` | WebAV音视频处理 |
| `vendor-dexie` | IndexedDB本地存储 |
| `vendor-echarts` | 数据可视化 |

### 7.3 定价体系

```
分镜头解析 = 视频时长(秒) / 30 × 75 Tapies
```

示例：2分14秒视频 = 134秒 ≈ 5×30秒 = 5×75 = 375 Tapies

---

## 八、研究结论与建议

### 8.1 核心发现

1. **Prompt工程化**：TapNow将分镜Prompt分解为5个步骤，结构清晰
2. **电影知识库**：内置Hollywood级光影知识库
3. **物理推演**：支持时间维度的画面推演（3秒后/5秒前）
4. **多机位生成**：一键生成9种运镜角度

### 8.2 漫舟可借鉴点

1. **引入画面推演**：增加"3秒后/5秒前"的分镜增强功能
2. **光影知识库**：丰富视觉风格库，增加电影级光影预设
3. **多机位生成**：支持一键生成多机位参考图

### 8.3 研究局限

1. 未能捕获实际API调用（需要认证）
2. 未能获取完整的后端Prompt处理逻辑
3. 未能验证多语言Prompt的差异

---

## 九、附录

### 9.1 资源链接

- 官网：https://app.tapnow.ai
- Canvas页面：https://app.tapnow.ai/canvas/{id}
- 资源CDN：https://fe-assets.tapnow.top

### 9.2 截图存档

- `TapNow/canvas-storieshot-*.png` - Canvas页面截图

### 9.3 JS Bundle

- 主应用：`index-DEsqSklO.js` (~896KB)
- Canvas模块：`vendor-pkg-canvas-Bo6fvKxS.js` (~1.5MB)

---

*研究报告完成*
