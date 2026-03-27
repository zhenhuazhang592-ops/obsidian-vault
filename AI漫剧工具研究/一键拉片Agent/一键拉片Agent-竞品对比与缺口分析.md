# 一键拉片 Agent — 竞品对比与缺口分析

> 日期：2026-03-25
> 对比对象：TapNow vs NanoPhoto.AI

---

## 一、核心定位对比

| 维度 | TapNow | NanoPhoto |
|------|--------|-----------|
| **产品定位** | AI漫剧制作平台（视频→分镜→生成） | AI视频提示词工具（视频→结构化Prompt） |
| **输入** | 视频上传（内部存储） | YouTube / URL / 本地文件（≤30MB） |
| **输出** | 14列结构化分镜表（含关键帧图） | 10+维结构化Prompt（非表格） |
| **目标用户** | 短剧创作者 | AI视频创作者（Sora/Veo用户） |
| **AI模型** | 未知（后端私有） | Gemini 3 Flash/Pro（服务端） |
| **关键帧图** | ✅ AI生成关键帧图 | ❌ 无关键帧图 |
| **API公开性** | 需认证，可调用部分API | 开放API（有错误码文档） |

---

## 二、输出结构详细对比

### 2.1 分镜描述维度

| 维度 | TapNow（14列） | NanoPhoto（10+维度） |
|------|--------------|-------------------|
| 镜号 | ✅ 镜号（数字） | ✅ Shot N（数字） |
| 时间 | ✅ 开始时间+结束时间+时长 | ✅ Duration per shot |
| 分镜描述 | ✅ 分镜描述 + 画面描述 | ✅ Subject/Scene Settings（含FG/MG/BG分层） |
| 景别 | ✅ 景别（近/中/特写） | ✅ Camera: WS/MS/CU/ECU（更精细） |
| 角度 | ✅ 相机角度（平/俯/仰/过肩） | ✅ Camera: profile/high/low/Dutch angle |
| 运镜 | ✅ 运镜方式（固定镜头） | ✅ Camera movement: Gimbal/Tracking/Dolly/Aerial |
| 构图 | ❌ 无 | ✅ Composition: rule-of-thirds/center/left-third |
| 灯光 | ✅ 光影风格（3种） | ✅ **5灯分离**（key/rim/fill/kicker/neg） |
| 调色 | ❌ 无独立字段 | ✅ **Grade: S-curve/bloom/vignette/grain/CA** |
| 景深 | ✅ 浅景深/深景深 | ✅ Lens: bokeh level / rack focus |
| 焦段 | ❌ 无 | ✅ Focal length feel（35mm→90mm） |
| 角色一致性 | ❌ 无 | ✅ Persist（same subject/核心特征） |
| 机位覆盖 | ❌ 无 | ✅ Coverage: master+inserts/match-on-action |
| 方向一致性 | ❌ 无 | ✅ L→R / R→L 方向标注 |
| 台词 | ✅ 台词列 | ✅ Dialogue: [时间区间] "VO: 台词" |
| 音效 | ✅ 音效列 | ✅ SFX Cues（精确到0.05s） |
| BGM | ✅ 背景音乐 | ✅ BGM: 风格+BPM+crossfades |
| 混音指令 | ❌ 无 | ✅ Mix notes（特定时刻降3dB等） |
| 转场 | ❌ 无 | ✅ CUT / FADE TO BLACK / TEXT OVERLAY |
| 尾帧 | ❌ 无 | ✅ End Card: Font+Color+Animation |
| 视频结构 | ❌ 无 | ✅ Structure mode（montage/long-take等10种） |
| 节奏因子 | ❌ 无 | ✅ tempo_factor |
| 关键帧图 | ✅ AI生成关键帧图 | ❌ 无 |
| 风格/情绪 | ⚠️ 光影风格（3种） | ✅ Visual Taste + Narrative tone |
| 主体特征 | ⚠️ 分镜描述中含 | ✅ 独立字段：Species/Coat/Color/Temperament |

**结论**：NanoPhoto 的分镜维度**远超 TapNow**，尤其在灯光5灯系统、专业调色、精确音频Cue方面。

---

## 三、技术管线对比

### 3.1 帧提取策略

| 维度 | TapNow | NanoPhoto |
|------|--------|-----------|
| 提取工具 | 未知（FFmpeg/WebAV？后端） | 未知（后端） |
| 提取数量 | 30帧/134秒（约每4秒1帧） | 未知 |
| 关键帧选取 | AI自动选择（后端私有） | 无关键帧图 |
| 帧上传 | 上传到 files.tapnow.ai | 内部处理 |

### 3.2 AI分析管线

| 维度 | TapNow | NanoPhoto |
|------|--------|-----------|
| AI模型 | 未知（私有） | Gemini 3 Flash/Pro（已知） |
| Prompt存储 | 后端私有 | 后端RSC Payload（无法提取） |
| 输出格式 | 结构化JSON（14列） | Streaming Markdown（10+维度） |
| 响应方式 | 轮询/未知 | **SSE流式输出**（实时渲染） |
| 生成关键帧图 | ✅（调用图像生成AI） | ❌ |

### 3.3 API开放程度

| 维度 | TapNow | NanoPhoto |
|------|--------|-----------|
| 端点 | `POST /api/workflow/v1/film/scene_breakdown` | `POST /api/sora-2/reverse-prompt` |
| 认证 | Bearer Token（私有） | API Key（公开文档） |
| 文档 | 无公开文档 | ✅ 完整错误码体系 |
| 限流 | 未知 | 100 req/h |
| 计费 | Tapies（内部积分） | Credits（1 credit/次） |

---

## 四、缺口分析：做完整一键拉片Agent还缺什么

### 4.1 P0 — 无法绕过的缺失

#### A. AI分镜分析Prompt（两个平台都拿不到）

| 平台 | Prompt存储位置 | 能否获取 |
|------|-------------|---------|
| TapNow | 后端私有 | ❌ |
| NanoPhoto | 服务端RSC Payload | ❌ |

**缺口**：只能从输出结果逆向推断Prompt结构，无法直接获取完整Prompt。

#### B. 帧提取策略（两个平台都后端处理）

**缺口**：
- 提取多少帧？（TapNow实测30帧/134秒，但未知算法）
- 按什么间隔？（固定间隔？关键帧检测？）
- 如何上传处理？

#### C. 镜头边界检测逻辑

**缺口**：如何判断画面主体/场景变化 = 新镜头？两平台均无公开。

---

### 4.2 P1 — 核心能力缺块

#### D. 关键帧图生成能力

| 平台 | 关键帧图 |
|------|---------|
| TapNow | ✅ 有（后端AI生成） |
| NanoPhoto | ❌ 无 |

**缺口**：如果要生成关键帧图，需要图像生成AI（Midjourney/Flux/Seedance等）。

#### E. 分镜Prompt设计（自研）

需要自行设计分镜分析Prompt，包含：

```
必含维度：
1. 镜头边界检测（时间点+时长）
2. 分镜描述（中文，主体+动作+表情）
3. 景别（ELS/LS/MS/MCU/CU/ECU）
4. 相机角度（平/俯/仰/过肩/Dutch）
5. 运镜方式（固定/推进/拉远/跟踪/摇镜）
6. 构图（主体位置）
7. 光影风格（5灯系统：key/rim/fill/kicker/neg）
8. 调色（Grade: S-curve/bloom/vignette/grain）
9. 景深（浅/深）
10. 焦段感（35mm/50mm/85mm）
11. 角色一致性标注（Persist）
12. 台词（带时间戳）
13. 音效Cue（精确到0.1s）
14. BGM（风格+BPM）
15. 转场（CUT/FADE）
16. 视频结构（montage/long-take等10种）
```

#### F. 流式输出架构（SSE）

NanoPhoto 使用 SSE 流式输出，前端实时渲染Markdown。
**缺口**：需要实现流式API + 前端Markdown实时渲染。

---

### 4.3 P2 — 工程实现缺块

#### G. 视频处理管线

```
视频 → 格式检测 → 帧提取（FFmpeg） → 帧筛选 → 图片存储（OSS）
```

**缺口**：FFmpeg集成 + OSS存储 + 帧质量筛选。

#### H. 分镜表存储与渲染

**缺口**：
- 数据库设计（14列分镜表Schema）
- 前端表格组件（可编辑/可导出）
- 导出格式（PDF/Excel/JSON/Markdown）

#### I. 与视频生成平台集成

最终目标：分镜 → AI视频生成
**缺口**：
- 视频生成API对接（Sora 2 / Veo 3 / Seedance 2）
- 分镜Prompt格式转换（分镜格式 → 目标平台Prompt格式）

---

## 五、缺口优先级矩阵

```
          技术难度
          低 ▲ 高
        ┌─────────┐
业务关键 │  EPrompt │ G存储/H前端
        │   D图像  │ I视频集成
        ├─────────┤
        │ F流式架构 │ C边界检测
        │         │
        └─────────┘
          ▲
        P0: A Prompt + B 帧提取
```

### P0（阻断级）

| 缺口 | 说明 | 解决方案 |
|------|------|---------|
| **A. 分镜Prompt** | 两平台Prompt均在后端，无法获取 | **自研Prompt**（基于Schema逆向） |
| **B. 帧提取策略** | 后端处理，策略未知 | **自研**（FFmpeg固定间隔+关键帧检测） |
| **C. 镜头边界检测** | 核心算法，两平台均未公开 | **自研**（LLM多帧推理 + 阈值检测） |

### P1（核心能力）

| 缺口 | 说明 | 解决方案 |
|------|------|---------|
| **D. 关键帧图** | 需要图像生成AI | 集成Midjourney/Flux/Seedance API |
| **E. 分镜Prompt设计** | 10+维度结构化输出 | 参考NanoPhoto 10维 + TapNow 14列 |
| **F. SSE流式输出** | NanoPhoto核心体验 | 实现SSE + Markdown实时渲染 |

### P2（工程实现）

| 缺口 | 说明 | 解决方案 |
|------|------|---------|
| **G. 视频处理管线** | FFmpeg + OSS | 自研或用现成库 |
| **H. 存储与渲染** | 数据库 + UI | PostgreSQL + React表格 |
| **I. 视频生成集成** | 分镜→视频生成 | 对接Sora/Veo/Seedance API |

---

## 六、最小可行产品路径

```
Phase 1（最快落地）：
视频 → FFmpeg提取帧 → 自研分镜Prompt → 14列表格输出
                        ↓
              参考NanoPhoto 10维设计Prompt
              参考TapNow 14列定义输出Schema

Phase 2（增强体验）：
+ 流式SSE输出（NanoPhoto体验）
+ 关键帧图生成（TapNow体验）

Phase 3（完整闭环）：
+ 视频生成集成（分镜→Sora 2/Veo 3）
```

---

## 七、可直接复用的成果

### 7.1 从TapNow复用

| 成果 | 可用性 | 用途 |
|------|--------|------|
| 14列分镜表Schema | ✅ 完全可用 | 数据模型设计 |
| 镜头类型体系（景别+角度+运镜） | ✅ 完全可用 | Prompt输出枚举 |
| API端点格式（参考） | ✅ 完全可用 | 自研API设计 |
| 字段映射逻辑 | ✅ 完全可用 | 前端渲染逻辑 |

### 7.2 从NanoPhoto复用

| 成果 | 可用性 | 用途 |
|------|--------|------|
| 10+维度分镜Prompt结构 | ✅ 可参考 | Prompt设计框架 |
| 5灯灯光体系 | ✅ 可参考 | 光影Prompt设计 |
| SFX Cue精确时间戳格式 | ✅ 可参考 | 音效时间轴设计 |
| BGM参数（BPM/crossfades） | ✅ 可参考 | BGM Prompt设计 |
| Structure mode（10种视频技术） | ✅ 可参考 | 分镜类型枚举 |
| tempo_factor 节奏因子 | ✅ 可参考 | 剪辑节奏控制 |
| Grade调色参数 | ✅ 可参考 | 调色Prompt设计 |
| Persist 角色一致性格式 | ✅ 可参考 | 角色一致性Prompt |
| End Card 模板 | ✅ 可参考 | 尾帧生成 |
| SSE流式输出架构 | ✅ 可参考 | 实时渲染管线 |

---

## 八、最终结论

### 做完整一键拉片Agent的缺口清单

| 优先级 | 缺口 | 来源 | 可绕过？ |
|--------|------|------|---------|
| P0 | AI分镜分析Prompt | 两平台均在后端 | ❌ 只能自研 |
| P0 | 帧提取策略（数量/间隔） | 后端私有 | ❌ 只能自研 |
| P0 | 镜头边界检测算法 | 后端私有 | ❌ 只能自研 |
| P1 | 关键帧图生成 | TapNow后端 | ⚠️ 可选（非必须） |
| P1 | 分镜Prompt设计（10+维） | 两平台均在后端 | ⚠️ 可自研（参考两平台） |
| P1 | SSE流式输出 | NanoPhoto架构 | ⚠️ 可自研 |
| P2 | 视频处理管线 | 工程实现 | ✅ 可自研（FFmpeg） |
| P2 | 分镜表存储+渲染 | 工程实现 | ✅ 可自研 |
| P2 | 视频生成集成 | 工程实现 | ✅ 可选（Phase 3） |

### 核心结论

**可以做出的一键拉片Agent**：
- 核心功能（分镜分析）✅ 可实现，但Prompt需自研
- Schema体系 ✅ 完全可复用（14列 + 10维）
- 关键帧图 ⚠️ 需要图像生成AI集成
- 流式体验 ⚠️ 需要SSE架构

**真正无法复制的**：后端AI模型本身（TapNow私有模型、NanoPhoto的Gemini微调版本）
