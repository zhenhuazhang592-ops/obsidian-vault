# NanoPhoto.AI 视频反推提示词 深度研究报告

> 调研时间：2026-03-25
> 调研目标：https://nanophoto.ai/zh/video-reverse-prompt
> 核心技术：Gemini 3 Flash/Pro + Sora 2 / Veo 3.1
> 研究方法：浏览器 CDP 抓取 + JS Chunk 分析 + RSC Payload 解析

---

## 一、平台架构总览

### 1.1 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | Next.js (App Router) + React + Radix UI + Tailwind CSS |
| CDN/部署 | Cloudflare |
| AI 模型 | Gemini 3 Flash（免费）、Gemini 3 Pro（付费） |
| 生成模型 | Sora 2 / Sora 2 Pro / Veo 3.1 / Nano Banana Pro |
| Prompt 存储 | **服务端**（Next.js SSR RSC Payload），前端 JS Chunk 无业务逻辑 |

### 1.2 产品定位

NanoPhoto.AI = **AI 视频/图片生成 + 反推工具矩阵**：

| 功能 | 路径 | 核心模型 |
|------|------|---------|
| 视频反推提示词 | `/zh/video-reverse-prompt` | Gemini 3 Pro |
| Sora 2 文生视频 | `/zh/sora-2` | Sora 2 |
| Sora 2 分镜 | `/zh/sora-storyboard` | Sora 2 |
| Sora 2 Prompt 生成器 | `/zh/sora-2-prompt-generator` | Gemini 3 Pro |
| 图片生成 | `/zh/nano-banana-pro` | Nano Banana Pro |

### 1.3 定价体系

| 套餐 | 价格 | 积分/月 | 积分单价 | 视频反推 |
|------|------|---------|---------|---------|
| 基础版 | ¥52.5/月 | 150 | ¥0.35/积分 | 无限 |
| 专业版 | ¥136.5/月 | 800 | ¥0.17/积分 | 无限 |
| 旗舰版 | ¥280/月 | 2000 | ¥0.14/积分 | 无限 |
| 至尊版 | ¥3100/月 | 25000 | ¥0.124/积分 | 无限 |

> 免费用户有体验额度（Gemini 3 Pro 免费分析）

---

## 二、核心 API 体系

### 2.1 视频反推 API

**Endpoint**: `POST /api/sora-2/reverse-prompt`

**Request**:
```json
{
  "videoSource": "youtube" | "url" | "file",
  "locale": "en" | "zh" | "ja" | "es" ...,
  "videoUrl": "string",         // YouTube URL 或直链 .mp4
  "videoFile": "string",        // Base64 编码（videoSource="file" 时）
  "videoFileName": "string"
}
```

**响应**: Streaming SSE，输出 Markdown table 格式

**Credits**: 1 credit/次（网页界面免费）

**文件限制**: 最大 30MB（Base64 前）

**错误码体系**:
| errorCode | 说明 |
|-----------|------|
| `LOGIN_REQUIRED` | 需要认证 |
| `API_KEY_RATE_LIMIT_EXCEEDED` | 速率超限（100 req/h） |
| `INSUFFICIENT_CREDITS` | 积分不足 |
| `INVALID_YOUTUBE_URL` | YouTube URL 无效 |
| `VIDEO_DOWNLOAD_FAILED` | 视频下载失败 |
| `VIDEO_PROCESSING_FAILED` | 视频处理失败 |
| `AI_SERVICE_ERROR` | AI 服务错误 |

### 2.2 Sora 2 Prompt 生成 API

**Endpoint**: `POST /api/sora-2/generate-prompt`

**Request**:
```json
{
  "topic": "string",           // 主题描述（必填）
  "mode": "textToVideo" | "imageToVideo",
  "technique": "montage" | "long take" | "time-lapse" | "slow-motion" |
               "tracking-shot" | "aerial-view" | "pov" | "split-screen" |
               "match-cut" | "fade-transition",
  "duration": 10 | 15,
  "model": "sora2" | "sora2-pro-standard" | "sora2-pro-high",
  "locale": "en" | "zh" | "ja" ...,
  "imageUrls": ["string"]      // imageToVideo 时必填
}
```

**响应**: Streaming SSE，输出 Markdown 结构化 Prompt

### 2.3 分镜重写 API

**Endpoint**: `POST /api/sora-2/rewrite-storyboard`

```json
{
  "originalNote": "string",    // 原始分镜内容
  "modification": "string",    // 修改指令
  "style": "string",
  "duration": 5-60,            // 秒数（验证：5-60）
  "locale": "string",
  "model": "string"
}
```

### 2.4 视频生成 API

**Endpoint**: `POST /api/sora-2/generate`

```json
{
  "prompt": "string",
  "mode": "textToVideo" | "imageToVideo",
  "modelTier": "sora2" | "sora2-pro-standard" | "sora2-pro-high",
  "aspectRatio": "portrait" | "landscape",
  "videoDuration": "10" | "15",
  "imageUrls": ["string"]       // imageToVideo 时
}
```

**Credits 消耗**:
| 模型 | 720P 10s | 720P 15s | 1080P 10s | 1080P 15s |
|------|---------|---------|---------|---------|
| Sora 2 | 2 | 4 | - | - |
| Sora 2 Pro 标准版 | 30 | 60 | - | - |
| Sora 2 Pro 高清版 | 60 | 100 | 100 | 150 |

---

## 三、Prompt 模板体系（完整版）

### 3.1 视频反推输出结构（10+ 维度）

从示例截图 "Neural Mane" 提取的完整 Prompt 框架：

```
# Neural Mane

## 1. Subject / Scene Settings（主体/场景）
- Audience: locale="JP"; Narrative tone: charged, majestic
- Subject type: animal
- Key features: [主体特征描述]; Scale: WS↔ECU; Motion: [动作列表]
- Species: [物种]; Coat/Skin: [材质描述]
- Color: [主色调]; Temperament: [性格/气质]
- Environment: [环境]; Time: [时间]; Weather/Light: [天气/光线]
- FG/MG/BG: [前景] / [中景] / [背景]

## 2. Lighting（灯光）
- key light（主光）: [位置/色温/强度]
- rim light（轮廓光）: [位置/颜色]
- fill light（填充光）: [柔光/补光]
- kicker / gobo / haze / volumetric 等专业参数

## 3. Grade（调色）
- Palette: [主色调]
- Curve: S-curve / flat / crushed 等
- bloom / halation / vignette / grain / CA 等风格参数

## 4. Visual Taste（视觉风格）
- premium techno-organic realism / cinematic documentary 等

## 5. Camera（镜头/相机）
- 景别: WS( wide shot) / MS(medium shot) / CU(close-up) / ECU(extreme close-up)
- 角度: profile / high angle / low angle / Dutch angle
- 运动: Gimbal Push / Tracking / Dolly / Aerial 等
- 构图: left-third / center / rule-of-thirds

## 6. Lens/Focus（镜头技术）
- 焦段感: 35mm→90mm
- 背景虚化: creamy bokeh / sharp
- 焦点切换: rack focus / fixed

## 7. Coverage（机位覆盖）
- master + inserts
- match-on-action
- L→R / R→L 方向一致性
- fixed eyelines

## 8. Persist（一致性维持）
- same [主体]; [核心特征] constant
- 右向凝视等固定属性

## 9. Dialogue（对白/配音）
- [0–2s] "VO: [配音内容]"
- [2–4s] "VO: [配音内容]"
格式: [时间区间] "说话人: 台词内容"

## 10. Audio（BGM + SFX + Cues）

### BGM:
- 风格描述: ambient-cinematic pulse / dramatic orchestral 等
- BPM: [数值范围]
- crossfades: [过渡方式]

### SFX:
- 音效列表: 微光闪烁/呼吸声/机械声等具体音效

### Cues（音效时间轴）:
- 0.05: [音效名]
- 2.0: [音效名]
- 4.0: [音效名]
- 6.0: [音效名]
- 7.5: [音效名]
- 8.5: [音效名]

### Mix Note:
- BGM 在特定时刻降低 3dB 等混音指令

## 11. Structure（整体结构）

### 元数据:
- total duration: [总时长]
- mode: montage / long-take / time-lapse / slow-motion 等
- tempo_factor: [节奏因子]

### 分段结构:
- [时间区间]: [镜头描述]
- CUT at [时间点]: [切换描述]
- FADE TO BLACK: [转场]
- TEXT OVERLAY: [文字内容]
  - Font: [字体]
  - Color: [颜色/渐变]
  - Position: [位置]
  - Size: [大小]
  - Animation: [动画]
- Background: [背景]
- Audio: [音频变化]
```

---

## 四、分镜输出格式（截图实测）

从页面示例 "Neural Mane" 截图提取的分镜卡片结构：

```
┌─────────────────────────────────────────────────────┐
│ Shot 1    Duration: 0.1–0.5s                        │
│ --------------------------------------------------------│
│ 📷 WS/ECU · Camera: Gimbal Push                       │
│ 🎨 Lighting: soft wrap back-left                      │
│                                                         │
│ 🔍 [详细视觉描述]                                       │
│ A lion with luminous filaments glowing...              │
│                                                         │
│ 🎵 Audio                                               │
│ BGM: ambient-cinematic pulse                          │
│ SFX: sparks radiate, filament ignition                │
│ VO: "Awaken—the pride runs on light."                 │
└─────────────────────────────────────────────────────┘
```

### 景别术语体系

| 缩写 | 全称 | 中文 |
|------|------|------|
| ELS | Extreme Long Shot | 超远景 |
| LS | Long Shot | 远景 |
| MLS | Medium Long Shot | 中远景 |
| MS | Medium Shot | 中景 |
| MCU | Medium Close-Up | 中近景 |
| CU | Close-Up | 特写 |
| ECU | Extreme Close-Up | 大特写 |

### 相机运动术语

| 类型 | 说明 |
|------|------|
| Gimbal Push | 稳定器推进 |
| Tracking | 跟踪拍摄 |
| Dolly | 轨道推进 |
| Aerial | 航拍 |
| Tilt | 上下摇镜 |
| Pan | 水平扫镜 |
| Zoom | 变焦 |

---

## 五、底层 Prompt 分析（推测重建）

### 5.1 视频反推系统 Prompt（推测）

基于输出结构和 API 参数，推测 Gemini 3 Pro 使用的系统 Prompt 框架：

```
You are a professional film analysis AI.
Analyze the provided video and generate a detailed, structured prompt
for AI video generation.

## Output Format

Generate a structured analysis following these sections:

### Subject / Scene Settings
- Subject type, key features, scale (WS↔ECU), motion
- Environment (FG/MG/BG layers)
- Color palette, temperament

### Lighting
- Key, rim, fill, kicker positions and qualities
- Atmospheric effects (haze, volumetric, gobo)

### Camera
- Framing (WS/MS/CU/ECU)
- Camera movement type
- Angle and composition

### Lens/Focus
- Focal length feel
- Depth of field characteristics

### Coverage
- Shot types used
- Match-on-action moments
- Directional continuity (L→R)

### Audio
- BGM: style, BPM, mood
- SFX: listed with timestamps (Cues)
- VO: dialogue with time ranges

### Structure
- Total duration
- Editing mode (montage/long-take/etc)
- tempo_factor
-分段描述

## Requirements
- Use professional filmmaking terminology
- Be specific about camera movements and lens choices
- Include precise timestamps for audio cues
- Maintain consistency in character/scene descriptions
```

### 5.2 示例主题→Prompt 生成流程

```
输入: "a majestic lion made of luminous filaments in black studio"
↓
Gemini 3 Pro 分析 + 结构化
↓
输出: Neural Mane (完整10+维结构化Prompt)
↓
输入 Sora 2 → 生成视频
```

---

## 六、与漫舟系统的对比

### 6.1 功能对照

| 功能维度 | NanoPhoto.AI | 漫舟系统 |
|---------|-------------|---------|
| **输入** | 视频（YouTube/URL/文件） | 小说/剧本/IP |
| **输出** | 分镜 Prompt | 剧本 + 分镜 + 音频 |
| **角色一致性** | Persist 字段（简单） | DNA 三层锁（九宫格） |
| **景别体系** | 10+ 术语 | 7 要素 Prompt |
| **灯光系统** | 专业5灯（key/rim/fill/kicker/neg） | 视觉风格包 |
| **调色系统** | Grade + S-curve/bloom/vignette | 情绪调色 |
| **音频要素** | BGM + SFX + Cues + Mix notes | VO + BGM + SFX |
| **镜头时长** | Duration per shot | 总时长 + 镜头数 |
| **转场** | CUT / FADE / TEXT OVERLAY | 简短提及 |
| **结构分段** | Montage / tempo_factor | 蒙太奇类型 |
| **End Card** | TEXT OVERLAY + Font + Animation | 无 |

### 6.2 可借鉴点

| 借鉴维度 | NanoPhoto 优势 | 漫舟引入建议 |
|---------|--------------|------------|
| **灯光体系** | 5灯分离（key/rim/fill/kicker/neg） | 新增 `lighting.schema.yaml` |
| **调色参数** | Grade (S-curve/bloom/vignette/grain/CA) | 新增调色 Prompt 模板 |
| **音频 Cue** | 精确到小数位（0.05s / 2.0s / 4.0s） | 强化 manzhou-sfx 时间轴精度 |
| **BGM 参数** | BPM + crossfades 量化 | manzhou-bgm 新增 BPM 字段 |
| **Persist** | 角色一致性维持指令 | 可强化 DNA 三层锁的 Prompt 表达 |
| **tempo_factor** | 剪辑节奏因子 | 可新增剪辑节奏参数 |
| **End Card** | TEXT OVERLAY 模板 | 可新增尾帧模板 |
| **Structure mode** | 10 种视频技术 | manzhou-storyboard 新增 technique 参数 |

---

## 七、关键技术发现

### 7.1 Prompt 存储位置

NanoPhoto 的 AI Prompt 模板**不存储在前端 JS**：
- 所有业务 Prompt 存储在**服务端 RSC Payload**
- 前端 JS 全部为框架代码（Next.js/Radix UI）
- Demo 示例通过 SSR 直接嵌入 HTML

### 7.2 流式输出架构

```
用户输入视频
    ↓
POST /api/sora-2/reverse-prompt
    ↓
Gemini 3 Pro 视频理解（服务端）
    ↓
Streaming SSE → 前端实时渲染 Markdown
    ↓
分镜卡片（每帧一个 Shot 卡片）
```

### 7.3 技术 technique 体系

NanoPhoto 支持 10 种视频技术作为 Prompt 约束：

| Technique | 漫舟对应 |
|-----------|---------|
| `montage` | 快速切换蒙太奇 |
| `long-take` | 长镜头 |
| `time-lapse` | 延时摄影 |
| `slow-motion` | 慢动作 |
| `tracking-shot` | 跟踪拍摄 |
| `aerial-view` | 航拍视角 |
| `pov` | 第一人称视角 |
| `split-screen` | 分屏 |
| `match-cut` | 匹配剪辑 |
| `fade-transition` | 淡入淡出 |

---

## 八、研究结论

### 8.1 NanoPhoto 核心价值

1. **视频逆向工程**：将任意视频拆解为可复现的 AI Prompt
2. **专业分镜输出**：10+ 维度结构化分镜（远超行业平均）
3. **音频要素时间轴**：SFX Cue 精确到小数位
4. **调色/灯光体系**：引入专业影视参数（Grade/S-curve/5灯系统）

### 8.2 对漫舟的启发

1. **灯光系统扩展**：在视觉风格包中新增 `lighting:` 参数（key/rim/fill/kicker/neg）
2. **调色参数扩展**：新增 `grade:` 参数（S-curve/bloom/vignette/grain/CA）
3. **End Card 模板**：新增尾帧生成 Prompt 模板
4. **tempo_factor**：在分镜结构中新增剪辑节奏因子
5. **Persist 强化**：将 DNA 三层锁的表达进一步强化为 Prompt 友好格式

### 8.3 研究限制

- Prompt 模板存储于服务端 RSC，无法直接提取完整系统 Prompt
- Gemini 3 Pro 的视频理解 Prompt 属于商业机密，未直接暴露
- Demo 示例 "Neural Mane" 是 Sora 2 Prompt 生成器的输出，非视频反推的直接输出格式
- 视频反推的实际 Shot-level 输出格式基于截图实测，推测可能略有差异

---

*研究方法：CDP 浏览器抓取 + JS Chunk 分析 + RSC Payload 解析 + 截图实测*
