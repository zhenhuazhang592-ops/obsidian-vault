# huage888 vs Toonflow 差距分析报告

> 对标：`/Users/huage/Downloads/Toonflow-app-master`
> 生成：2026-04-07
> 参考：Toonflow v1.0.7，AGPL-3.0

---

## P0 — 阻断性问题（立即修复）

### P0-1: [CRITICAL] 视频 API URL 错误

**文件**：`config/doubao_pipeline.py:210`

```python
# ❌ 错误（404）
url = f"{base_url}/content_generation/tasks"

# ✅ 正确（用户 curl 验证通过）
url = f"{base_url}/contents/generations/tasks"
```

**影响**：所有视频生成（Stage 3/4/5）全部失败，HTTP 404。
**状态**：🚨 阻断

### P0-2: [HIGH] 图片 size 参数大小写错误

**文件**：`config/doubao_pipeline.py:371`

```python
# ❌ 错误（HTTP 400）
response = client.images.generate(..., size="2K", ...)

# ✅ 正确（API 要求小写）
response = client.images.generate(..., size="2k", ...)

# ✅ 修正后（config/doubao_pipeline.py:424-427）
size_map = {"16:9": "2k", "9:16": "2k", "1:1": "2k"}
```

**影响**：所有图片生成（Stage 1.5/3/4）参数校验失败。
**状态**：⚠️ 部分修复（`create_and_wait_image` line 371 仍为 `"2K"`，`create_and_wait_image_with_ref` 已修正为 `"2k"`）

---

## P1 — 核心能力缺失（影响 production）

### P1-1: Multi-Agent 委托链未实现

| 维度 | Toonflow | huage888 | 差距 |
|------|---------|---------|------|
| 架构 | 主 Agent + Sub Agent 真实嵌套调用 | Pipeline 脚本串联（顺序执行） | 架构级别差距 |
| Agent 间通信 | `transfer` 事件切换子 Agent，WebSocket 推送 | 纯文本传递，无事件驱动 | 功能缺失 |
| Sub-Agent 委托 | `segmentAgent` / `shotAgent` / `AI1`/`AI2`/`director` 真实并行生成 | 单次 qwen-max 调用产出所有结果 | 质量差距 |
| 工具调用 | Vercel AI SDK `tool()` 真实执行 | 工具调用为假（Fake），实际不执行 | 机制缺失 |

**根本原因**：
- Toonflow 用 Vercel AI SDK 的 `tool` 参数 + ModelMessage 架构实现真实 Agent 间调用
- huage888 用 `qwen_pipeline.py` 纯文本调用，无法实现工具嵌套

**改进方向**：
1. 短期：将 storyboard 分段由单 Agent 改为 segment + shot 两个独立 Agent 串联
2. 中期：引入 `agno` 或 `smolagents` 框架实现真实工具调用
3. 长期：对标 Toonflow，基于 Vercel AI SDK 重构 Agent 系统

**对应文件**：
- Toonflow: `src/agents/outlineScript/index.ts`（主+3子），`src/agents/storyboard/index.ts`（主+2子）
- huage888: `config/qwen_pipeline.py`（纯文本），`agents/storyboard-artist.md`（无工具调用）

### P1-2: 资产一致性强制规则缺失

| 维度 | Toonflow | huage888 |
|------|---------|---------|
| 强制机制 | `getAssets` 工具返回时强制附带警告，禁止近义词/缩写/捏造 | agent-md 中有文字规则，但无强制手段 |
| 资产引用 | `buildResourcesMapPrompts()` 自动拼接 "漠玫=图片1, 大圣=图片2" | `asset_library.py` 仅做路径解析，prompt 中不注入资产映射 |
| 宫格参考图 | `filterRelevantAssets()` + `buildResourcesMapPrompts()` 生成参考图底图 | `batch_image_pipeline.py` 合并参考图但无 AI 过滤 |

**改进**：
- 在 `storyboard-artist.md` 中强化 "⚠️ 禁止近义词" 规则（已有文字版，需确保 qwen-max 遵守）
- `generate_shot_images.py` 和 `batch_image_pipeline.py` 应注入资产映射前缀

### P1-3: 视频生成缺少 prompt 增强

Toonflow 在生成视频前对 prompt 做增强：
```
"请完全参照以下内容生成视频：
 ${prompt}
 重要强调：
 风格高度保持 ${artStyle} 风格，保证人物一致性
 ..."
```

huage888 的 `doubao_pipeline.py` 直接传原始 prompt，无增强处理。

**改进**：在 `video_pipeline.py` 的 `stage5_video()` 中加入 `build_video_prompt()` 函数，注入风格锚定词。

### P1-4: P1/P2 分镜图生成缺少 Shot imagePrompt 解析

**问题**：
- `generate_shot_images.py` 的 Pydantic 模型 `IMAGE_MODEL = "doubao-seedream-4.5"`（旧版，应为 `doubao-seedream-5-0-260128`）
- `batch_image_pipeline.py` 调用 `grid_split.py`，但 `grid_split.py` 是否使用 Sharp 未知

**改进**：
1. 统一 P1/P2 模型为 `doubao-seedream-5-0-260128`
2. 验证 `grid_split.py` 使用 Pillow 或 Sharp 切割宫格

---

## P2 — 工程完整性

### P2-1: EventEmitter 未集成 WebSocket

| 维度 | Toonflow | huage888 |
|------|---------|---------|
| 事件总线 | EventEmitter → WebSocketSink → 前端实时展示 | `event_emitter.py` 有 ConsoleSink + JSONLSink，无 WebSocketSink |
| 实时进度 | 前端可看到 token 逐字输出、工具调用、分镜图生成进度 | 仅控制台输出，无前端 |

**影响**：用户体验差，无法实时看到生成进度。

**改进**：`scripts/event_emitter.py` 实现 `WebSocketSink`，支持 `ws://` URL 推送事件。

### P2-2: 35张数据库表 vs Markdown

Toonflow 有 35 张 SQLite 表，huage888 的 `task_db.py` 仅实现了 projects/tasks/dependencies/conversations 4 张表。

**缺失表**：
- `t_assets`：资产状态管理（type/shots/segmentId）
- `t_image`：图片生成记录（filePath/state）
- `t_video`：视频记录（resolution/model/errorReason/state）
- `t_videoConfig`：视频配置（startFrame/endFrame/audio）
- `t_artStyle`：艺术风格库（200+风格）
- `t_prompts`：提示词模板（defaultValue/customValue 双轨）

**改进**：按 Toonflow Schema 补全 `task_db.py` 的表结构。

### P2-3: 9家视频厂商 vs 仅 Doubao

Toonflow 支持 9 家视频厂商（volcengine/kling/vidu/wan/gemini/runninghub/sora 等），huage888 的 `video_pipeline.py` 有 adapter 架构但实际仅配置了 Doubao。

**改进**：接入 Kling 即梦 API（`KLING_API_KEY`），验证 adapter 架构是否完整可用。

### P2-4: 数据库 Schema 不完整

Toonflow 的 `t_video.state` 使用整数状态码（0=进行中/1=成功/-1=失败），huage888 的 `task_db.py` 混用了 `TaskState` 枚举。

**改进**：统一状态码定义，参考 Toonflow 整数码。

---

## P3 — 质量与体验优化

### P3-1: 缺少流式输出

Toonflow 的 qwen-max 输出通过 WebSocket 逐 token 推送，huage888 的 `qwen_pipeline.py` 是 `stream=False`，无流式。

**影响**：用户等待时间长，无中间反馈。

**改进**：`qwen_pipeline.py` 支持 `stream=True` + SSE（Server-Sent Events）输出。

### P3-2: 视频生成 prompt 未注入 style

Toonflow `generateVideo.ts`：
```typescript
"请完全参照以下内容生成视频：${prompt}\n重要强调：风格高度保持 ${artStyle} 风格"
```

huage888 直接用 `libtvPrompt` 作为视频 prompt，无风格增强。

**改进**：在 `video_pipeline.py` 的 `stage5_video()` 中加 `build_video_prompt()`。

### P3-3: 提示词管理硬编码 vs 可运行时编辑

Toonflow 的 `t_prompts` 表支持 `defaultValue`/`customValue` 双轨，制片人可在 UI 中修改提示词模板。

huage888 的 prompts 硬编码在 `agents/*.md` 和 `skills/*/SKILL.md` 中。

**改进**：将关键 prompts 抽取为 `config/prompts_templates.py`，支持 `customValue` 覆盖。

### P3-4: 缺少 `t_artStyle` 艺术风格库

Toonflow 有 200+ 艺术风格，`src/data/artStyle.ts` 包含中英文关键词。

huage888 有 `config/art_styles.py`，但仅含赛博墨韵锚定词，缺少 Toonflow 的完整风格体系。

**改进**：扩充 `config/art_styles.py`，对标 Toonflow 200+ 风格。

### P3-5: API 测试缺少完整诊断

Toonflow `src/service/other/testAI.ts`：
```typescript
{ code: "InvalidParameter", message: "model not found" }
```

huage888 的 `doubao_pipeline.py --test` 仅测连接，不测具体模型可用性。

**改进**：加 `--test-model doubao-seedream-5-0-260128` 测试具体模型是否开通。

---

## P4 — 流程完整性

### P4-1: 视频配置界面缺失

Toonflow 有 `t_videoConfig` 表存储视频配置（首尾帧/多图模式/startFrame/endFrame/audio）。

huage888 的 `video_pipeline.py` 直接调 API，无视频配置管理。

**改进**：`task_db.py` 实现 `video_configs` 表。

### P4-2: 资产注册表追踪缺失

Toonflow 的 `t_assets` 追踪每张资产的 `type/episode/segmentId/shotIndex`。

huage888 的 `assets/03-asset-registry.md` 是 Markdown，无版本控制。

**改进**：用 `task_db.py` 的 `assets` 表替代 Markdown 追踪。

### P4-3: 对话历史未跨 session 续接

Toonflow 的 `t_chatHistory` 持久化对话，WebSocket close 时保存。

huage888 的 `conversation_manager.py` 有基本实现，但未在 `run_episode_pipeline.py` 全流程中启用。

**改进**：在 `run_episode_pipeline.py` 中对所有 `--agent` 调用启用 `--session-id`。

---

## 差距矩阵汇总

| 优先级 | 差距项 | Toonflow | huage888 | 状态 |
|--------|--------|---------|---------|------|
| P0 | 视频 API URL 错误 | ✅ | ❌ | 🚨 阻断 |
| P0 | 图片 size 大小写 | ✅ | ⚠️ 部分修复 | 🚨 阻断 |
| P1 | Multi-Agent 真实委托链 | ✅ | ❌ | 架构差距 |
| P1 | 资产一致性强制规则 | ✅ | ⚠️ 文字版有 | 需强化 |
| P1 | 视频 prompt 风格增强 | ✅ | ❌ | 功能缺失 |
| P1 | P1/P2 模型版本统一 | ✅ | ⚠️ | 需修 IMAGE_MODEL |
| P2 | EventEmitter + WebSocket | ✅ | ❌ | 无 WS Sink |
| P2 | 35张数据库表 | ✅ | ❌ 4张 | Schema 缺失 |
| P2 | 9家视频厂商 | ✅ | ❌ 仅 Doubao | 适配器未填 |
| P2 | 视频配置管理 | ✅ | ❌ | 表缺失 |
| P3 | 流式输出 | ✅ | ❌ | 无 SSE |
| P3 | 提示词运行时编辑 | ✅ | ❌ | 硬编码 |
| P3 | 200+艺术风格库 | ✅ | ⚠️ | 需扩充 |
| P3 | 模型可用性测试 | ✅ | ❌ | 诊断缺失 |
| P4 | 资产注册表 DB 化 | ✅ | ❌ Markdown | 需迁移 |
| P4 | 对话历史跨 session | ✅ | ⚠️ | 未启用 |

---

## 修复计划

### 立即（5 分钟）

- [ ] `config/doubao_pipeline.py:210` URL `content_generation` → `contents/generations`
- [ ] `config/doubao_pipeline.py:371` size `"2K"` → `"2k"`
- [ ] `scripts/generate_shot_images.py:34` IMAGE_MODEL 更新为 `doubao-seedream-5-0-260128`

### 短期（1-2 小时）

- [ ] `video_pipeline.py` 加入 `build_video_prompt()` 风格增强
- [ ] `storyboard-artist.md` 强化 ⚠️ 资产一致性警告
- [ ] `doubao_pipeline.py --test` 增加具体模型可用性测试
- [ ] 验证 `grid_split.py` 使用 Pillow/Sharp 切割宫格

### 中期（半天）

- [ ] `event_emitter.py` 实现 `WebSocketSink`
- [ ] `task_db.py` 补全 assets/video/videoConfig 表
- [ ] `config/art_styles.py` 扩充到 Toonflow 级别
- [ ] 接入 Kling API，验证 adapter 架构

### 长期（1-2 天）

- [ ] Sub-Agent 架构：segment + shot 分离为独立 Agent
- [ ] 对话历史全流程启用 `--session-id`
- [ ] `t_prompts` 表实现，提示词支持运行时编辑
