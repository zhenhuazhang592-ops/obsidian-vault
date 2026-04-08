---
date: 2026-04-08
tags: [huage888, 设计, production-report]
---

# 制作文档自动化 · 设计方案

> 目标：huage888 每次执行 Pipeline 后，自动生成技术日志 + 可读报告，实现复盘可追溯、优化有依据

## 核心设计

### 1. 双层文档架构

| 文件 | 定位 | 读者 |
|------|------|------|
| `outputs/{episode}/technical_log.json` | 机器可读技术日志 | AI / 自动化工具 / 后续脚本 |
| `outputs/{episode}/production_report.md` | 人类可读制作报告 | 创作者 / 团队 / 客户 |

### 2. 颗粒度分级

**`--report-level stage`（默认，日常用）**
每大阶段记录：阶段号、名称、模型、耗时、状态、prompt ID、审核结果、产出路径、重试次数。

**`--report-level shot`（精查用）**
在 stage 基础上，追加每个镜头详情：编号、描述、图 prompt、motion prompt、asset ID、视频路径、质量评分、人工备注。

### 3. 输出位置

```
outputs/S01E01/
├── technical_log.json      # 新增
├── production_report.md    # 新增
└── ...（现有文件保留）
```

## 文件清单

| 文件 | 作用 | 依赖 |
|------|------|------|
| `scripts/report_logger.py` | 轻量埋点模块，Pipeline 各阶段 import，append 到 JSONL | event_emitter.py |
| `scripts/production_report.py` | 报告生成器，读取 JSONL → 输出双格式文档 | report_logger.py |
| `run_episode_pipeline.py` | 每阶段结束时调用 `report_logger`，全部结束后调用 `production_report.py` | report_logger, production_report |

## 数据模型（technical_log.json）

```json
{
  "project": "断桥奇遇",
  "episode": "S01E01",
  "generated_at": "ISO8601",
  "report_level": "stage|shot",
  "total_duration_seconds": 0,
  "stages": [
    {
      "stage": 1,
      "name": "outline",
      "model": "qwen-plus",
      "started_at": "ISO8601",
      "duration_seconds": 12.3,
      "status": "success|failed",
      "prompt_id": "outline_v2",
      "review_result": "PASS|WARNING|FAIL",
      "output_file": "outputs/01-outline.md",
      "retry_count": 0,
      "error_message": null
    }
  ],
  "shots": []  // 仅 shot 级别
}
```

## 集成点（run_episode_pipeline.py）

```python
# 每阶段结束时
from report_logger import log_stage_end
log_stage_end(stage=1, name="outline", model="qwen-plus", ...)

# Pipeline 全部结束后
import subprocess
subprocess.run([
    "python3", "scripts/production_report.py",
    "--project", project,
    "--episode", episode,
    "--report-level", report_level,
    "--output-dir", output_dir
])
```

## 实现顺序

1. `report_logger.py` — 纯函数，JSONL append，无副作用
2. `run_episode_pipeline.py` — 在各 stage 节点插入 log 调用
3. `production_report.py` — 读取 JSONL，生成双格式文档
4. `--report-level` 参数挂到 `run_episode_pipeline.py`

## 约束

- 不改动现有 22 个脚本核心逻辑，只在 wrapper 层（`run_episode_pipeline.py`）集成
- JSONL 是追加写入，支持 Pipeline 中途断点续传后追加新记录
- `production_report.py` 可单独运行，复查历史项目时无需重跑 Pipeline
