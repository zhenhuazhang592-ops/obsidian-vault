---
tags: [huage888, 漫剧, 预生产, pipeline]
date: 2026-04-07
---

# huage888 · AI 漫剧预生产系统

> 一键端到端：剧本 → 故事线 → 大纲 → 分镜 → 资产图 → 批量视频

## 快速开始

### 前置依赖

```bash
# 1. 配置环境变量
export QWEN_API_KEY="your-api-key"
export ARK_API_KEY="your-volc-engine-api-key"   # Doubao 视频生成

# 2. 验证连接
python3 config/qwen_pipeline.py --test
```

### 完整流水线

```bash
python3 scripts/run_episode_pipeline.py \
  --storyline \
  --run-asset-images \
  --run-p1 \
  --run-p2 \
  --episode S01E01 \
  --project 漠玫传 \
  --script docs/剧本.md
```

### 分阶段流水线

| 阶段 | 命令 | 输出 |
|------|------|------|
| Stage 0 故事线 | `--storyline` | `.huage888/storylines/{project}/{episode}/storyline.json` |
| Stage 1 大纲 | `--skip-outline=False`（默认） | `outputs/{episode}/{episode}-outline.md` |
| Stage 1.5 资产图 | `--run-asset-images` | `assets/{episode}/*.png` |
| Stage 2 分镜 | `--skip-storyboard=False`（默认） | `outputs/{episode}/{episode}-shots.md` |
| Stage 3 P1 图 | `--run-p1` | `outputs/{episode}/shots/images/shot_01.png...` |
| Stage 4 P2 宫格 | `--run-p2` | `outputs/{episode}/shots/grid_01.png...` |
| Stage 5 视频 | 默认开启，可用 `--skip-video` | `outputs/{episode}/videos/shot_01.mp4...` |

### 跳过特定阶段

```bash
# 使用已有大纲，跳过 Stage 0+1
python3 scripts/run_episode_pipeline.py \
  --skip-outline \
  --episode S01E01 \
  --project 漠玫传 \
  --run-p1 --run-p2

# 跳过视频生成（仅预生产）
python3 scripts/run_episode_pipeline.py \
  --skip-video \
  --episode S01E01 \
  --project 漠玫传 \
  --run-p1 --run-p2
```

---

## 流水线架构

```
剧本（.md/.txt）
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ run_episode_pipeline.py                                 │
│                                                         │
│  Stage 0: storyline     → storyline.json                 │
│  Stage 1: outline      → outline.md（Stage 0 输出优先）  │
│  Stage 1.5: asset_imgs → assets/*.png                   │
│  Stage 2: storyboard   → shots.md                       │
│  Stage 3: P1 图        → shots/images/shot_XX.png       │
│  Stage 4: P2 宫格      → shots/grid/grid_XX.png         │
│  Stage 5: video        → shots/videos/shot_XX.mp4       │
└─────────────────────────────────────────────────────────┘
```

### 决策层（决策层 Agent）

每个阶段内置 review gate，FAIL 直接阻断执行：

```
Stage 1 审核 → validate_outline.py → FAIL → sys.exit(1)
Stage 2 审核 → check_asset_consistency.py → FAIL → sys.exit(1)
```

### 数据流

- Stage 0 故事线 → **Stage 1 大纲**（自动传递 storyline.json）
- Stage 2 分镜 → **Stage 3 P1**（分镜脚本中的镜头映射）
- Stage 3 P1 图片 → **Stage 5 视频**（自动作为首帧参考图 img1）

---

## 核心脚本

| 脚本 | 用途 |
|------|------|
| `run_episode_pipeline.py` | 主编排脚本，一键执行全流水线 |
| `qwen_pipeline.py` | Qwen-Max API 调用封装（内容生成） |
| `video_pipeline.py` | 视频生成批量编排（Doubao/Kling） |
| `asset_image_pipeline.py` | 资产图 API 生成 |
| `storyline_pipeline.py` | 故事线生成 |
| `generate_shot_images.py` | 分镜逐镜头图生图（P1） |
| `batch_image_pipeline.py` | 宫格图批量合成（P2） |
| `asset_library.py` | 资产库管理器（注册/查询/DB 同步） |
| `task_db.py` | SQLite 任务状态数据库（10 张表） |
| `event_emitter.py` | 实时事件总线（Console + JSONL + WebSocket） |

---

## 资产一致性规则

所有 Agent 必须遵守以下规则：

- ✅ 主体列使用大纲 JSON 中的精确 ID（如 `C001`）
- ✅ 场景列使用大纲 JSON 中的精确 ID（如 `S001`）
- ❌ 禁止近义词替换（如"漠玫"不可写成"道姑"）
- ❌ 禁止捏造未声明的角色/场景/道具

---

## 配置参考

| 文件 | 作用 |
|------|------|
| `config/visual-bible.md` | 全局视觉锚点（角色/场景/道具规范） |
| `config/video-model-registry.md` | 视频模型能力矩阵 |
| `config/prompts-registry.md` | Agent 参数配置（temperature/top_p/max_tokens） |
| `config/art_styles.py` | 艺术风格库（7 类 200+ 风格） |
| `config/prompts_templates.py` | 提示词模板库（9 个模板） |
| `config/qwen_pipeline.py` | Qwen-Max API 调用封装 |
| `.env` | 环境变量（API Keys） |

---

## 目录结构

```
huage888/
├── agents/               # Agent 定义（qwen-max system prompt 来源）
├── skills/               # 技能定义（详细格式规范）
├── config/               # 配置文件 + API 封装
├── scripts/              # 流水线脚本
├── assets/library/       # 资产库（characters/scenes/props）
├── .huage888/           # 运行时缓存（tasks/events/sessions）
│   ├── storylines/       # Stage 0 故事线输出
│   ├── tasks/            # 任务队列
│   └── queue_events.jsonl # 事件日志
└── outputs/             # 最终输出（按 episode 分目录）
```
