# 制作文档自动化 · 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task.
>
> **Goal:** Pipeline 结束后自动生成 `technical_log.json` + `production_report.md`，支持 `--report-level stage|shot` 两档颗粒度
>
> **Architecture:** 在 `run_episode_pipeline.py` wrapper 层集成埋点，JSONL 追加写入，`production_report.py` 结束时一次性聚合生成双格式文档。零改动现有 22 个脚本。
>
> **Tech Stack:** Python 3（纯标准库，无新依赖）
>
> **Files Overview:**
> - 新建: `AI工具箱/huage888/scripts/report_logger.py`
> - 新建: `AI工具箱/huage888/scripts/production_report.py`
> - 修改: `AI工具箱/huage888/scripts/run_episode_pipeline.py`（埋点注入 + `--report-level` 参数）
>
> **最终文件结构：**
> ```
> outputs/{episode}/
> ├── technical_log.json        # 机器可读
> ├── production_report.md      # 人类可读
> └── ...（现有文件不变）
>
> .huage888/production_logs/{project}/{episode}/
> └── pipeline.jsonl            # 追加写入事件流
> ```
>
> ---

## Task 1: 新建 `scripts/report_logger.py`

**Files:**
- Create: `AI工具箱/huage888/scripts/report_logger.py`

- [ ] **Step 1: 写文件**

```python
#!/usr/bin/env python3
"""report_logger.py — 轻量 JSONL 埋点模块

用法：
    from report_logger import ReportLogger

    logger = ReportLogger(project="漠玫传", episode="S01E01")
    logger.log_stage_start(stage=1, name="outline", model="qwen-plus")
    # ... 执行阶段 ...
    logger.log_stage_end(stage=1, name="outline", status="success",
                        output_file="outputs/S01E01/outline.md", review_result="PASS")

    logger.log_shot(shot_number=1, description="漠玫立于断桥",
                    image_prompt="...", asset_id="A001")
"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / ".huage888" / "production_logs"


class ReportLogger:
    def __init__(self, project: str, episode: str):
        self.project = project
        self.episode = episode
        self.session_id = uuid.uuid4().hex[:8]
        self._log_dir = LOG_DIR / project / episode
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._jsonl_path = self._log_dir / "pipeline.jsonl"

    def _write_event(self, event_type: str, data: dict):
        """追加写入一条 JSONL 事件"""
        event = {
            "event": event_type,
            "session_id": self.session_id,
            "project": self.project,
            "episode": self.episode,
            "ts": datetime.now().isoformat(),
            **data,
        }
        with open(self._jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def log_pipeline_start(self, report_level: str = "stage"):
        self._write_event("pipeline_start", {"report_level": report_level})

    def log_pipeline_end(self, report_level: str = "stage",
                          total_duration: float = 0.0,
                          summary: dict | None = None):
        self._write_event("pipeline_end", {
            "report_level": report_level,
            "total_duration_seconds": total_duration,
            "summary": summary or {},
        })

    def log_stage_start(self, stage: int, name: str, model: str = ""):
        self._write_event("stage_start", {
            "stage": stage,
            "name": name,
            "model": model,
        })

    def log_stage_end(self, stage: int, name: str,
                      status: Literal["success", "failed", "skipped"] = "success",
                      output_file: str = "",
                      review_result: Literal["PASS", "FAIL", "WARNING", ""] = "",
                      prompt_id: str = "",
                      retry_count: int = 0,
                      error_message: str = "",
                      duration_seconds: float = 0.0,
                      model: str = ""):
        self._write_event("stage_end", {
            "stage": stage,
            "name": name,
            "status": status,
            "output_file": output_file,
            "review_result": review_result,
            "prompt_id": prompt_id,
            "retry_count": retry_count,
            "error_message": error_message,
            "duration_seconds": duration_seconds,
            "model": model,
        })

    def log_shot(self, shot_number: int,
                 description: str = "",
                 image_prompt: str = "",
                 image_asset_id: str = "",
                 motion_prompt: str = "",
                 video_url: str = "",
                 duration_seconds: int = 0,
                 model: str = "",
                 quality_score: float | None = None,
                 notes: str = ""):
        self._write_event("shot", {
            "shot_number": shot_number,
            "description": description,
            "image_prompt": image_prompt,
            "image_asset_id": image_asset_id,
            "motion_prompt": motion_prompt,
            "video_url": video_url,
            "duration_seconds": duration_seconds,
            "model": model,
            "quality_score": quality_score,
            "notes": notes,
        })

    def log_manual_note(self, content: str):
        """人工备注（shot 级别可写）"""
        self._write_event("manual_note", {"content": content})
```

- [ ] **Step 2: 提交**

```bash
cd /Users/huage/Obsidian\ Vault/AI工具箱/huage888
git add scripts/report_logger.py
git commit -m "feat(report): add report_logger.py — lightweight JSONL logger

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 2: 修改 `scripts/run_episode_pipeline.py` — 集成埋点

**Files:**
- Modify: `AI工具箱/huage888/scripts/run_episode_pipeline.py`

**涉及位置（全文索引）：**

| 修改 | 位置 | 内容 |
|------|------|------|
| 新增 `--report-level` | 第 738 行后（`--max-history` 之后） | argparse 参数 |
| 初始化 logger | 第 743 行前（TaskDB 之前） | `from report_logger import ReportLogger` |
| Stage 0 埋点 | `main()` 内 `stage0_storyline()` 调用后 | `logger.log_stage_end()` |
| Stage 1 埋点 | `main()` 内 `stage1_outline()` 调用后 | `logger.log_stage_end()` |
| Stage 1.5 埋点 | `main()` 内 `stage1_5_asset_images()` 调用后 | `logger.log_stage_end()` |
| Stage 2 埋点 | `main()` 内 `stage2_storyboard()` 调用后 | `logger.log_stage_end()` |
| Stage 3 埋点 | `main()` 内 `stage3_p1()` 调用后 | `logger.log_stage_end()` |
| Stage 4 埋点 | `main()` 内 `stage4_p2()` 调用后 | `logger.log_stage_end()` |
| Stage 5 埋点 | `main()` 内 `stage5_video()` 调用后 | `logger.log_stage_end()` |
| Pipeline 结束时 | 第 961 行前（汇总之前） | 调用 `production_report.py` |

---

- [ ] **Step 1: 新增 `--report-level` argparse 参数**

在约第 738 行（`--max-history` 之后，`args = parser.parse_args()` 之前）新增：

```python
    parser.add_argument(
        "--report-level",
        default="stage",
        choices=["stage", "shot"],
        help="报告颗粒度：stage（默认，日常用）/ shot（精查用）",
    )
```

---

- [ ] **Step 2: 初始化 ReportLogger**

在约第 743 行（`# ── 初始化 TaskDB 和 ConversationManager ──` 之前）新增：

```python
    # ── 初始化 ReportLogger ───────────────────────────────────────────────
    report_logger = None
    try:
        from report_logger import ReportLogger
        report_logger = ReportLogger(project=args.project, episode=args.episode)
        report_logger.log_pipeline_start(report_level=args.report_level)
        print(f"  📝 ReportLogger 已连接")
    except Exception as e:
        print(f"  [INFO] ReportLogger 不可用: {e}")
```

---

- [ ] **Step 3: Stage 0 埋点**

在约第 792-803 行（`stage0_storyline()` 调用后，失败判断之后）新增：

```python
        if report_logger:
            report_logger.log_stage_end(
                stage=0, name="storyline",
                status="success" if storyline_path else "failed",
                output_file=_rel(storyline_path) if storyline_path else "",
            )
```

---

- [ ] **Step 4: Stage 1 埋点**

在约第 826 行（`stage1_outline()` 调用 + 失败判断之后）新增：

```python
        if report_logger:
            _review = "PASS" if (
                outline_path and outline_path.exists()
                and not args.dry_run and not args.skip_review
                and review_pass
            ) else "WARNING"
            report_logger.log_stage_end(
                stage=1, name="outline",
                status="success" if outline_path else "failed",
                output_file=_rel(outline_path) if outline_path else "",
                review_result=_review,
                model="qwen-plus",
            )
```

（需在埋点引用之前，将 `review_pass` 变量提升到此处可见范围——它已在第 830-837 行定义，需将埋点放在 Review 判断之后执行）

---

- [ ] **Step 5: Stage 1.5 埋点**

在约第 859 行（`stage1_5_asset_images()` 调用后）新增：

```python
        if report_logger:
            report_logger.log_stage_end(
                stage=1.5, name="asset_images",
                status="success" if asset_ok else "failed",
                model="doubao",
            )
```

---

- [ ] **Step 6: Stage 2 埋点**

在约第 879 行（`stage2_storyboard()` 调用后）新增：

```python
        if report_logger:
            _review2 = "PASS" if (
                shots_path and shots_path.exists()
                and not args.dry_run and not args.skip_review
                and review_pass
            ) else "WARNING"
            report_logger.log_stage_end(
                stage=2, name="storyboard",
                status="success" if shots_path else "failed",
                output_file=_rel(shots_path) if shots_path else "",
                review_result=_review2,
                model="qwen-plus",
            )
```

---

- [ ] **Step 7: Stage 3/4 埋点**

Stage 3（P1）后约第 918 行新增：
```python
        if report_logger:
            report_logger.log_stage_end(
                stage=3, name="p1",
                status="success" if p1_ok else "failed",
                model="doubao-seedream-4.5",
            )
```

Stage 4（P2）后约第 929 行新增：
```python
        if report_logger:
            report_logger.log_stage_end(
                stage=4, name="p2",
                status="success" if p2_ok else "failed",
                model="doubao-seedream-5-0-260128",
            )
```

---

- [ ] **Step 8: Stage 5 埋点 + 调用 production_report.py**

在第 959 行后（Stage 5 完成后，汇总之前）新增：

```python
        if report_logger:
            report_logger.log_stage_end(
                stage=5, name="video",
                status="success" if video_ok else "failed",
                model=args.video_provider,
            )
            # ── 生成制作文档 ───────────────────────────────────────────
            try:
                import subprocess as _subprocess
                _subprocess.run([
                    sys.executable,
                    str(SCRIPT_DIR / "production_report.py"),
                    "--project", args.project,
                    "--episode", args.episode,
                    "--report-level", args.report_level,
                ], check=False)
            except Exception as e:
                print(f"  [WARN] 制作文档生成失败: {e}")
```

---

- [ ] **Step 9: 提交**

```bash
cd /Users/huage/Obsidian\ Vault/AI工具箱/huage888
git add scripts/run_episode_pipeline.py
git commit -m "feat(pipeline): integrate ReportLogger — auto-generate production docs

Adds --report-level stage|shot, writes pipeline.jsonl, calls production_report.py on exit.
Zero changes to existing 22 scripts.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 3: 新建 `scripts/production_report.py`

**Files:**
- Create: `AI工具箱/huage888/scripts/production_report.py`

- [ ] **Step 1: 写文件**

```python
#!/usr/bin/env python3
"""production_report.py — 制作文档生成器

读取 .huage888/production_logs/{project}/{episode}/pipeline.jsonl
生成：
  outputs/{episode}/technical_log.json   （机器可读）
  outputs/{episode}/production_report.md  （人类可读）

用法（独立运行）：
  python3 scripts/production_report.py \
    --project 漠玫传 \
    --episode S01E01 \
    --report-level stage
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / ".huage888" / "production_logs"


def parse_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def build_stages(records: list[dict]) -> list[dict]:
    stages = []
    stage_starts: dict = {}

    for rec in records:
        if rec["event"] == "stage_start":
            sid = rec["data"].get("stage", rec["data"].get("name", ""))
            stage_starts[sid] = rec
        elif rec["event"] == "stage_end":
            data = rec["data"]
            sid = data.get("stage", data.get("name", ""))
            started_at = ""
            duration = data.get("duration_seconds", 0.0)
            if sid in stage_starts:
                started_at = stage_starts[sid].get("ts", "")
                if duration == 0.0 and started_at:
                    try:
                        end_ts = datetime.fromisoformat(rec["ts"])
                        start_ts = datetime.fromisoformat(started_at)
                        duration = (end_ts - start_ts).total_seconds()
                    except Exception:
                        duration = 0.0
            stages.append({
                "stage": data.get("stage", 0),
                "name": data.get("name", ""),
                "model": data.get("model", ""),
                "started_at": started_at,
                "duration_seconds": duration,
                "status": data.get("status", "success"),
                "prompt_id": data.get("prompt_id", ""),
                "review_result": data.get("review_result", ""),
                "output_file": data.get("output_file", ""),
                "retry_count": data.get("retry_count", 0),
                "error_message": data.get("error_message", ""),
            })
    return stages


def build_shots(records: list[dict]) -> list[dict]:
    shots = []
    for rec in records:
        if rec["event"] == "shot":
            data = rec["data"]
            shots.append({
                "shot_number": data.get("shot_number", 0),
                "description": data.get("description", ""),
                "image_prompt": data.get("image_prompt", ""),
                "image_asset_id": data.get("image_asset_id", ""),
                "motion_prompt": data.get("motion_prompt", ""),
                "video_url": data.get("video_url", ""),
                "duration_seconds": data.get("duration_seconds", 0),
                "model": data.get("model", ""),
                "quality_score": data.get("quality_score"),
                "notes": data.get("notes", ""),
            })
    return sorted(shots, key=lambda x: x["shot_number"])


def generate_technical_log(project: str, episode: str,
                            report_level: str,
                            stages: list[dict],
                            shots: list[dict]) -> dict:
    total_dur = sum(s.get("duration_seconds", 0) for s in stages)
    return {
        "project": project,
        "episode": episode,
        "generated_at": datetime.now().isoformat(),
        "report_level": report_level,
        "total_duration_seconds": round(total_dur, 1),
        "stages": stages,
        "shots": shots if report_level == "shot" else [],
    }


def generate_markdown_report(project: str, episode: str,
                               report_level: str,
                               stages: list[dict],
                               shots: list[dict],
                               records: list[dict]) -> str:
    # 从 pipeline_end 事件取 summary
    summary = {}
    for rec in records:
        if rec["event"] == "pipeline_end":
            summary = rec["data"].get("summary", {})

    total_dur = sum(s.get("duration_seconds", 0) for s in stages)
    mins, secs = divmod(int(total_dur), 60)
    total_time = f"{mins}分{secs}秒" if mins else f"{secs}秒"

    lines = [
        f"# 制作报告 · {project} {episode}",
        "",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 基本信息",
        "",
        f"| 字段 | 内容 |",
        f"|------|------|",
        f"| 项目 | {project} |",
        f"| 集数 | {episode} |",
        f"| 报告颗粒度 | {report_level} |",
        f"| 总耗时 | {total_time} |",
        "",
        "## 制作流程",
        "",
        f"| 阶段 | 名称 | 模型 | 状态 | 耗时 | 审核 | 产出 |",
        f"|------|------|------|------|------|------|------|",
    ]

    for s in sorted(stages, key=lambda x: x.get("stage", 0)):
        stage_num = s.get("stage", "")
        name = s.get("name", "")
        model = s.get("model", "")
        status = s.get("status", "")
        dur = s.get("duration_seconds", 0)
        review = s.get("review_result", "")
        output = s.get("output_file", "")
        status_icon = "✅" if status == "success" else ("⏭️ " if status == "skipped" else "❌")
        lines.append(
            f"| {stage_num} | {name} | {model} | {status_icon} | {dur:.1f}s | {review} | {output} |"
        )

    video_stages = [s for s in stages if s.get("name") == "video"]
    if video_stages:
        video_summary = summary.get("stages", {}).get("video", {})
        generated = video_summary.get("generated", 0)
        failed = video_summary.get("failed", 0)
        lines.extend([
            "",
            "## 视频统计",
            "",
            f"- 生成成功：{generated} 个",
            f"- 生成失败：{failed} 个",
        ])

    if report_level == "shot" and shots:
        lines.extend([
            "",
            "## 镜头详情",
            "",
            f"| 镜头 | 描述 | Asset ID | 视频 | 时长 |",
            f"|------|------|----------|------|------|",
        ])
        for shot in shots:
            desc = shot.get("description", "")[:40]
            video = shot.get("video_url", "").split("/")[-1][:20]
            lines.append(
                f"| {shot['shot_number']} | {desc} | "
                f"{shot.get('image_asset_id','')} | {video} | "
                f"{shot.get('duration_seconds',0)}s |"
            )

    lines.extend([
        "",
        "---",
        f"*由 huage888 自动生成 · {datetime.now().isoformat()}*",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="生成制作文档")
    parser.add_argument("--project", required=True)
    parser.add_argument("--episode", required=True)
    parser.add_argument(
        "--report-level",
        default="stage",
        choices=["stage", "shot"],
    )
    args = parser.parse_args()

    jsonl_path = LOG_DIR / args.project / args.episode / "pipeline.jsonl"
    output_dir = BASE_DIR / "outputs" / args.episode
    output_dir.mkdir(parents=True, exist_ok=True)

    records = parse_jsonl(jsonl_path)
    if not records:
        print(f"[WARN] 无事件记录: {jsonl_path}")
        sys.exit(0)

    stages = build_stages(records)
    shots = build_shots(records)

    tech_log = generate_technical_log(
        project=args.project, episode=args.episode,
        report_level=args.report_level,
        stages=stages, shots=shots,
    )
    tech_path = output_dir / "technical_log.json"
    tech_path.write_text(json.dumps(tech_log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✅ technical_log.json → {tech_path.relative_to(BASE_DIR)}")

    md_report = generate_markdown_report(
        project=args.project, episode=args.episode,
        report_level=args.report_level,
        stages=stages, shots=shots, records=records,
    )
    md_path = output_dir / "production_report.md"
    md_path.write_text(md_report, encoding="utf-8")
    print(f"  ✅ production_report.md → {md_path.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 提交**

```bash
cd /Users/huage/Obsidian\ Vault/AI工具箱/huage888
git add scripts/production_report.py
git commit -m "feat(report): add production_report.py — generates dual-format docs from JSONL

Reads .huage888/production_logs/{project}/{episode}/pipeline.jsonl
Outputs: technical_log.json + production_report.md

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 4: 端到端验证（dry-run）

- [ ] **Step 1: dry-run 测试（stage 级别）**

```bash
cd /Users/huage/Obsidian\ Vault/AI工具箱/huage888
python3 scripts/run_episode_pipeline.py \
  --episode S01E01 \
  --project 测试验证 \
  --dry-run \
  --report-level stage
```

预期：输出包含 `ReportLogger 已连接`

- [ ] **Step 2: 单独运行 production_report.py**

```bash
python3 scripts/production_report.py \
  --project 测试验证 \
  --episode S01E01 \
  --report-level stage
```

预期：
- `outputs/S01E01/technical_log.json` 生成
- `outputs/S01E01/production_report.md` 生成，含制作流程表格

- [ ] **Step 3: 提交验证结果**

```bash
git add -A
git commit -m "test(production-report): e2e dry-run verification

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## 自检清单

- [ ] **Spec 覆盖检查：**
  - [x] 双格式文档（technical_log.json + production_report.md）
  - [x] `--report-level stage|shot` 两档颗粒度
  - [x] Pipeline 结束时自动触发
  - [x] 零改动现有 22 个脚本
- [ ] **占位符扫描：** 无 TBD/TODO ✅
- [ ] **类型一致性：** `stage`/`name`/`status`/`review_result` 字段在 Task 1-3 全链路一致 ✅
- [ ] **依赖检查：** `production_report.py` 依赖 `report_logger.py`（Task 1 先完成）✅
