---
name: huage888
description: huage888 短剧预生产编排层。触发词：做短剧、生成视频、创建项目、查看进度、执行 pipeline、管理集数。当用户提到 huage888、short drama production、或需要短剧制作流水线时使用。
---

# huage888 短剧预生产编排层

## 系统定位

```
huage888（Claude Code 编排层）  →  qwen-max（内容生成）  →  LibTV（用户手动执行）
```

- **huage888** 只做编排：读取 agent prompt → 拼 system+user → 调用 qwen_pipeline → 解析输出
- **qwen-max** 负责所有文字内容生成（讲戏本/提示词/分镜脚本）
- **LibTV** 由用户在 huage888 生成操作指南后手动操作

## 项目入口

```bash
cd /Users/huage/Obsidian\ Vault/AI工具箱/huage888
```

## 核心脚本索引

| 脚本 | 作用 |
|------|------|
| `scripts/project_manager.py` | 项目/集数管理、Pipeline 编排 |
| `scripts/run_episode_pipeline.py` | 7 阶段 Pipeline 执行 |
| `scripts/outline_agent.py` | 大纲/故事线 Agent |
| `scripts/novel_manager.py` | 小说原文管理器 |
| `scripts/script_generator.py` | 大纲 → 剧本生成器 |
| `scripts/task_db.py` | TaskDB SQLite（项目/任务/资产/对话全量） |
| `scripts/conversation_context.py` | 多 Agent 会话上下文管理器 |
| `config/qwen_pipeline.py` | qwen-max 调用封装 |
| `config/video_model_registry.py` | 视频模型能力矩阵 + 自动选型 |
| `scripts/adapters/` | 多厂商视频适配器（Doubao/Kling/Wan/Vidu/Gemini） |

## Pipeline 8 阶段

```
storyline → outline → asset_imgs → script → storyboard → P1 → P2 → video
```

各阶段对应命令：

```bash
# 完整流水线
python3 scripts/run_episode_pipeline.py \
  --storyline --run-asset-images --run-script \
  --episode S01E01 --project 漠玫传 \
  --script docs/剧本.md

# 分步执行
python3 scripts/run_episode_pipeline.py \
  --episode S01E01 --project 漠玫传 \
  --run-outline           # 仅大纲
  --run-asset-images      # 仅资产图片
  --run-script            # 仅剧本
  --run-storyboard        # 仅分镜脚本
  --run-p1                # 仅 P1 分镜图
  --run-p2                # 仅 P2 宫格分镜
  --run-video             # 仅视频（默认）

# dry-run（不调 API）
python3 scripts/run_episode_pipeline.py \
  --episode S01E01 --project 漠玫传 \
  --dry-run
```

## 项目管理命令

```bash
# 列出所有项目
python3 scripts/project_manager.py list

# 新建项目
python3 scripts/project_manager.py new-project \
  --name 漠玫传 --type 漫剧 --art-style "赛博墨韵" --video-ratio 16:9

# 新建集数
python3 scripts/project_manager.py new-episode \
  --project 漠玫传 --episode S01E02

# 制作状态仪表盘
python3 scripts/project_manager.py dashboard

# 单集各 Stage 状态
python3 scripts/project_manager.py stage-status \
  --project 漠玫传 --episode S01E01

# 执行 Pipeline
python3 scripts/project_manager.py run \
  --project 漠玫传 --episode S01E01 \
  --stages outline,storyboard,P1,P2 \
  --dry-run
```

## 数据库操作

```bash
# 查看项目
python3 scripts/task_db.py projects

# 查看集数大纲
python3 scripts/task_db.py outlines --project-id 1

# 查看对话历史
python3 scripts/task_db.py chat --project-id 1 --agent outline

# 清空对话历史
python3 scripts/task_db.py chat --project-id 1 --clear

# 导出依赖 DAG
python3 scripts/task_db.py dag --project-id 1

# AI 模型配置
python3 scripts/task_db.py aimodels --list
python3 scripts/task_db.py aimodels --get outlineScriptAgent
```

## 新项目启动流程

```
1. huage888 新建项目
   python3 scripts/project_manager.py new-project \
     --name 断桥奇遇 --project 漠玫传 --episode S01E01

2. 用户将剧本放入 projects/断桥奇遇/docs/剧本.md

3. huage888 加载 libtv-skill 生成操作指南
   → 用户在 LibTV 上传角色/场景资产，获取 element_id

4. huage888 生成完整流水线
   → 分镜脚本 → P1 图片 → P2 宫格 → 视频

5. 用户在 LibTV 按分镜指南生成视频 → 手动剪辑合成
```

## Agent 调用（qwen_pipeline）

```bash
# 使用已注册 Agent（自动拼接 agents/<name>.md + skills/<name>/SKILL.md）
python3 config/qwen_pipeline.py \
  --agent director \
  --user "请分析以下剧本：..." \
  --output outputs/01-director-analysis.md

# 指定 skill
python3 config/qwen_pipeline.py \
  --agent storyboard-artist \
  --skill custom-skill \
  --user "..."

# 带会话历史
python3 config/qwen_pipeline.py \
  --agent outline \
  --user "..." \
  --session-id S01E01 \
  --max-history 10
```

## 视频模型自动选型

```bash
# 列出所有模型
python3 config/video_model_registry.py list

# 推荐场景选型
python3 config/video_model_registry.py recommend \
  --has-audio --duration 5 --aspect-ratio 16:9 --mode I2V

# API 测试
python3 config/qwen_pipeline.py --test
```

## 会话上下文（M3-3）

```bash
# 开启 episode 会话
python3 scripts/conversation_context.py begin \
  --project 漠玫传 --episode S01E01

# 追加对话
python3 scripts/conversation_context.py append \
  --agent outline --role assistant --content "..."

# 构建注入上下文
python3 scripts/conversation_context.py context \
  --agent storyboard --agents outline,storyboard --max 20

# 查看 Session 调用链
python3 scripts/conversation_context.py chain \
  --agent storyboard --project 漠玫传 --episode S01E01
```

## 资产一致性校验

```bash
# 校验分镜脚本资产 ID 一致性（失败则阻断）
python3 scripts/check_asset_consistency.py \
  outputs/S01E01/S01E01-shots.md \
  outputs/S01E01/S01E01-outline.md

# 校验大纲格式
python3 scripts/validate_outline.py outputs/S01E01/S01E01-outline.md
```

## 质量审核（Pipeline 内置）

```
Stage 1   → [script-review]      PASS → 继续，FAIL → 重试（×3）
Stage 2   → [storyboard-review]  PASS → 继续，FAIL → 重试（×3）
Stage 1.5 → check_asset_consistency()  FAIL → 重试（×3）
```

## Visual Bible（全局视觉圣经）

位置：`config/visual-bible.md`

每集启动前必须确认，覆盖：
- 角色六层身份锚点（C001/C002 等）
- 场景光影基准
- 道具视觉锚点
- 风格禁止变体
- 角色说话风格锚点（第7层）

## 阻塞点记录规范

遇到阻塞时，记录到 `MEMORY.md` 仪表盘：

```
| **阻塞点** | [具体描述] |
| **下一步** | [需要华哥确认的内容] |
```

禁止：模糊的"待定"、超过 3 个阻塞点同时存在。
