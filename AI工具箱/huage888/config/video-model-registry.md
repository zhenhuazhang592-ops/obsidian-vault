# config/video-model-registry.md — 视频模型能力矩阵

> huage888 系统 | 资产执行层 | LibTV 模型选型依据
> 版本：v1.0 | 用途：为每个视频模型定义量化参数，指导 LibTV 自动化选型
> 来源：Toonflow modelList.ts + LibTV 官方文档（2026-04）

---

## 一、模型选型决策树

```
输入：镜头类型 + 需求时长 + 画面比例 + 是否需要音频
         │
         ▼
┌─────────────────────────────────┐
│ 是否需要音频？                   │
├────────────────┬────────────────┤
│     是          │      否        │
│     ▼           │      ▼        │
│ Doubao 1.5-pro  │  参考下方矩阵  │
│ Wan 2.6-t2v    │               │
│ Gemini Veo 3   │               │
└────────────────┴────────────────┘
```

**默认推荐**：Kling O1（综合质量最高）
**快速出图**：Doubao 1.0-lite-t2v / Wan 2.6-t2v-flash
**写实人物特写**：Gemini Veo 3 / Veo 3.1
**竖屏短剧**：优先 9:16 支持的模型

---

## 二、模型参数矩阵

### 2.1 火山引擎 / 豆包系列

| 字段 | Doubao Seedance 1.5-pro | Doubao Seedance 1.0-pro | Doubao 1.0-lite-i2v | Doubao 1.0-lite-t2v |
|------|------------------------|------------------------|--------------------|---------------------|
| **model_id** | `doubao-seedance-1-5-pro-251215` | `doubao-seedance-1-0-pro-250528` | `doubao-seedance-1-0-lite-i2v-250428` | `doubao-seedance-1-0-lite-t2v-250428` |
| **manufacturer** | volcengine | volcengine | volcengine | volcengine |
| **mode** | T2V + I2V | T2V + I2V | I2V only | T2V only |
| **audio** | ✅ 有声 | ❌ 无声 | ❌ 无声 | ❌ 无声 |
| **duration(s)** | 4/5/6/7/8/9/10/11/12 | 2/3/4/5/6/7/8/9/10/11/12 | 2-12 | 2-12 |
| **resolution** | 480p / 720p / 1080p | 480p / 720p / 1080p | 480p / 720p / 1080p | 480p / 720p / 1080p |
| **aspect_ratio** | 16:9 · 4:3 · 1:1 · 3:4 · 9:16 · 21:9 | 同上 | —（继承参考图） | 16:9 · 4:3 · 1:1 · 3:4 · 9:16 · 21:9 |
| **generation_type** | `text` / `endFrameOptional` | `text` / `endFrameOptional` | `endFrameOptional` / `reference` | `text` |
| **recommend_for** | 高质量有声短剧，推荐首选 | 标准短剧，T2V 主力 | 写实人物图生视频 | 快速 T2V 预览 |
| **caveat** | — | 质量略低于 1.5-pro | 仅支持图生视频 | 质量偏低，调试用 |

---

### 2.2 可灵系列（Kling）

| 字段 | Kling O1（STD 5s）| Kling O1（STD 10s）| Kling O1（PRO 5s）| Kling O1（PRO 10s）| Kling v2.6-turbo（PRO）|
|------|------------------|-------------------|-----------------|-------------------|----------------------|
| **model_id** | `kling-v1(STD)` | `kling-v1(STD)` | `kling-v1(PRO)` | `kling-v1(PRO)` | `kling-v2-6(PRO)` |
| **manufacturer** | kling | kling | kling | kling | kling |
| **mode** | T2V | T2V | T2V | T2V | T2V |
| **audio** | ❌ | ❌ | ❌ | ❌ | ❌ |
| **duration(s)** | 5 | 10 | 5 | 10 | 5 / 10 |
| **resolution** | 720p | 720p | 1080p | 1080p | 1080p |
| **aspect_ratio** | 16:9 · 1:1 · 9:16 | 同左 | 16:9 · 1:1 · 9:16 | 同左 | 16:9 · 1:1 · 9:16 |
| **generation_type** | `text` | `text` | `text` | `text` | `text` |
| **i2v_type** | `startEndRequired` | `startEndRequired` | `startEndRequired` | `startEndRequired` | `startEndRequired` |
| **recommend_for** | 竖屏短剧日常镜头 | 竖屏短剧长镜头 | 高质量竖屏精品 | 高质量竖屏长镜头 | v2 最新款，质量最优 |
| **caveat** | — | — | — | — | 成本最高 |

---

### 2.3 万象系列（Wan）

| 字段 | Wan 2.6-t2v | Wan 2.6-i2v-flash | Wan 2.6-i2v | Wan 2.5-t2v-preview |
|------|------------|------------------|------------|---------------------|
| **model_id** | `wan2.6-t2v` | `wan2.6-i2v-flash` | `wan2.6-i2v` | `wan2.5-t2v-preview` |
| **manufacturer** | wan | wan | wan | wan |
| **mode** | T2V | I2V | I2V | T2V |
| **audio** | ✅ 有声 | ✅ 有声 | ✅ 有声 | ✅ 有声 |
| **duration(s)** | 2/3/4/5/6/7/8/9/10/11/12/13/14/15 | 2-15 | 2-15 | 5 / 10 |
| **resolution** | 720p / 1080p | 720p / 1080p | 720p / 1080p | 480p / 720p / 1080p |
| **aspect_ratio** | 16:9 · 9:16 · 1:1 · 4:3 · 3:4 | —（继承参考图）| —（继承参考图）| 16:9 · 9:16 · 1:1 · 4:3 · 3:4 |
| **generation_type** | `text` | `singleImage` | `singleImage` | `text` |
| **recommend_for** | 有声短剧首选 | 快速图生视频 | 高质量图生视频 | 有声预览 |
| **caveat** | — | 质量偏低 | — | 较 2.6 旧 |

---

### 2.4 Vidu / Gemini Veo / Sora 系列

| 字段 | Vidu Q3-pro | Vidu 2.0 | Gemini Veo 3.1 | Gemini Veo 3 | Sora 2 Pro |
|------|------------|---------|---------------|-------------|-----------|
| **model_id** | `viduq3-pro` | `vidu2.0` | `veo-3.1-generate-preview` | `veo-3.0-generate-preview` | `sora-2-pro` |
| **manufacturer** | vidu | vidu | gemini | gemini | runninghub |
| **mode** | I2V | I2V | T2V+I2V | T2V+I2V | T2V+I2V |
| **audio** | ✅ | ❌ | ✅ | ✅ | ❌ |
| **duration(s)** | 1-16 | 4(360p/720p/1080p) / 8(720p) | 4 / 6 / 8 | 4 / 6 / 8 | 15 / 25 |
| **resolution** | 540p / 720p / 1080p | 360p / 720p / 1080p | 720p / 1080p | 720p / 1080p | — |
| **aspect_ratio** | — | — | 16:9 · 9:16 | 16:9 · 9:16 | 16:9 · 9:16 |
| **generation_type** | `singleImage` | `singleImage` / `reference` | `text` / `singleImage` / `startEndRequired` / `endFrameOptional` / `reference` | `text` / `singleImage` | `singleImage` / `text` |
| **recommend_for** | 长时长图生视频 | 多分辨率兼容 | 写实人物，多类型生成 | 写实人物高质量 | 超长镜头 |
| **caveat** | 仅图生 | — | Preview 阶段 | 质量最高 | 需 RunningHub |

---

## 三、LibTV 脚本节点格式对照

LibTV 的视频生成节点（Script Node）参数与本矩阵的映射关系：

```
LibTV Script Node 参数
│
├── model         → model_id（本文件第一列）
├── prompt        → 来自分镜脚本的画面描述（storyboard-skill 输出）
├── duration      → duration(s)（本文件）
├── resolution    → resolution（本文件，优先选 1080p）
├── aspect_ratio  → aspect_ratio（本文件，注意竖屏短剧选 9:16）
├── image_ref     → 来自 assets/03-asset-registry.md 的 image_url（I2V 模式）
└── audio         → audio 字段：true=生成音频轨道，false=无声
```

---

## 四、选型速查表

### 按需求场景

| 场景 | 推荐模型 | 理由 |
|------|---------|------|
| **竖屏短剧（有声）** | Doubao 1.5-pro 或 Wan 2.6-t2v | 9:16 + 有声，竖屏首选 |
| **竖屏短剧（无声，高质量）** | Kling O1 PRO 10s | 1080p，竖屏质量最优 |
| **竖屏短剧（无声，标准）** | Kling v2.6-turbo | v2 最新款，性价比高 |
| **人物特写（写实）** | Gemini Veo 3.1 或 Veo 3 | 写实人脸表现最佳 |
| **产品特写（牛油果等）** | Doubao 1.5-pro 或 Wan 2.6-i2v | 图生视频保真度高 |
| **快速预览/草稿** | Doubao 1.0-lite-t2v / Wan 2.6-i2v-flash | 出图快，成本低 |
| **超长镜头（>10s）** | Wan 2.6-t2v / Vidu Q3-pro / Sora 2 Pro | 支持最长 15-25s |
| **横屏短剧（B站）** | Kling O1 PRO 或 Gemini Veo 3 | 16:9 表现最佳 |

### 按时长推荐

| 时长 | 首选 | 备选 |
|------|------|------|
| 2-4s | Wan 2.6-i2v-flash / Doubao 1.0-lite | Kling 最短 5s |
| 5s | Kling O1 STD/PRO | Wan 2.6-t2v |
| 8-10s | Kling O1 PRO 10s | Gemini Veo 3.1（8s）|
| 12-15s | Wan 2.6-t2v / Vidu Q3-pro | — |
| 15-25s | Sora 2 Pro | Vidu Q3-pro |

---

## 五、Prompt 撰写规范（给分镜师）

> 视频生成 Prompt 与分镜脚本的分工边界

```
分镜脚本（storyboard-skill 输出）：
  → 叙事语言，描述「发生了什么」，含主体/场景/运镜/光影
  → 不含模型指令（如 camera angle、render engine）

LibTV Script Node 优化层（用户手动）：
  → 参考分镜脚本，翻译为模型指令
  → 追加镜头运动词、风格词、氛围词

分镜师只写叙事，分镜脚本「LibTV 生成提示」栏提供简化的画面描述词
```

---

## 六、版本记录

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.0 | 2026-04-05 | 初始建立，基于 Toonflow modelList.ts + LibTV 文档 |
