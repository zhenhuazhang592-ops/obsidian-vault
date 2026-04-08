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
            sid = rec.get("stage", rec.get("name", ""))
            stage_starts[sid] = rec
        elif rec["event"] == "stage_end":
            started_at = ""
            duration = rec.get("duration_seconds", 0.0)
            sid = rec.get("stage", rec.get("name", ""))
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
                "stage": rec.get("stage", 0),
                "name": rec.get("name", ""),
                "model": rec.get("model", ""),
                "started_at": started_at,
                "duration_seconds": duration,
                "status": rec.get("status", "success"),
                "prompt_id": rec.get("prompt_id", ""),
                "review_result": rec.get("review_result", ""),
                "output_file": rec.get("output_file", ""),
                "retry_count": rec.get("retry_count", 0),
                "error_message": rec.get("error_message", ""),
            })
    return stages


def build_shots(records: list[dict]) -> list[dict]:
    shots = []
    for rec in records:
        if rec["event"] == "shot":
            shots.append({
                "shot_number": rec.get("shot_number", 0),
                "description": rec.get("description", ""),
                "image_prompt": rec.get("image_prompt", ""),
                "image_asset_id": rec.get("image_asset_id", ""),
                "motion_prompt": rec.get("motion_prompt", ""),
                "video_url": rec.get("video_url", ""),
                "duration_seconds": rec.get("duration_seconds", 0),
                "model": rec.get("model", ""),
                "quality_score": rec.get("quality_score"),
                "notes": rec.get("notes", ""),
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
    summary = {}
    for rec in records:
        if rec["event"] == "pipeline_end":
            summary = rec.get("summary", {})

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
        status_icon = "✅" if s.get("status") == "success" else ("⏭️ " if s.get("status") == "skipped" else "❌")
        lines.append(
            f"| {s.get('stage','')} | {s.get('name','')} | {s.get('model','')} | "
            f"{status_icon} | {s.get('duration_seconds',0):.1f}s | "
            f"{s.get('review_result','')} | {s.get('output_file','')} |"
        )

    video_stages = [s for s in stages if s.get("name") == "video"]
    if video_stages:
        vs = summary.get("stages", {}).get("video", {})
        lines.extend([
            "",
            "## 视频统计",
            "",
            f"- 生成成功：{vs.get('generated', 0)} 个",
            f"- 生成失败：{vs.get('failed', 0)} 个",
        ])

    if report_level == "shot" and shots:
        lines.extend(["", "## 镜头详情", "", f"| 镜头 | 描述 | Asset ID | 视频 | 时长 |", f"|------|------|----------|------|------|"])
        for shot in shots:
            desc = shot.get("description", "")[:40]
            video = shot.get("video_url", "").split("/")[-1][:20]
            lines.append(
                f"| {shot['shot_number']} | {desc} | "
                f"{shot.get('image_asset_id','')} | {video} | "
                f"{shot.get('duration_seconds',0)}s |"
            )

    lines.extend(["", "---", f"*由 huage888 自动生成 · {datetime.now().isoformat()}*"])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="生成制作文档")
    parser.add_argument("--project", required=True)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--report-level", default="stage", choices=["stage", "shot"])
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

    tech_log = generate_technical_log(args.project, args.episode, args.report_level, stages, shots)
    tech_path = output_dir / "technical_log.json"
    tech_path.write_text(json.dumps(tech_log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✅ technical_log.json → {tech_path.relative_to(BASE_DIR)}")

    md_report = generate_markdown_report(args.project, args.episode, args.report_level, stages, shots, records)
    md_path = output_dir / "production_report.md"
    md_path.write_text(md_report, encoding="utf-8")
    print(f"  ✅ production_report.md → {md_path.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
