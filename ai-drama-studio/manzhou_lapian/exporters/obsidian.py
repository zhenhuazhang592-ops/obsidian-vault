"""漫舟拉片智能体 - Obsidian 笔记导出器"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..types import LapianResult, ShotAnalysis

logger = logging.getLogger(__name__)


def _fmt_time(seconds: float) -> str:
    """秒 → MM:SS 格式"""
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:04.1f}"


def _fmt_range(start: float, end: float) -> str:
    return f"{_fmt_time(start)}–{_fmt_time(end)}"


def _build_frontmatter(result: LapianResult) -> str:
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    # 从文件名推断 series/episode（如有）
    name = Path(result.video_filename).stem
    return f"""---
uid: lapian-{result.video_id}
title: {name} 拉片分析
created: {date}
video: {result.video_filename}
video_duration: {result.video_duration:.1f}s
video_shots: {result.total_shots}
analysis_model: {result.analysis_model}
scene_threshold: {result.scene_threshold}
tags: [拉片分析]
---

"""


def _build_overview_table(shots: list[ShotAnalysis]) -> str:
    header = "| 镜 | 时间 | 时长 | 景别 | 角度 | 运镜 | 光影 | 景深 | 分镜描述 | 台词 |"
    sep = "|------|------|------|------|------|------|------|------|---------|------|"
    rows = []
    for s in shots:
        desc_short = s.description[:30] + ("..." if len(s.description) > 30 else "")
        rows.append(
            f"| {s.shot_number:02d} | {_fmt_range(s.start_time, s.end_time)} | "
            f"{s.duration:.1f}s | {s.shot_size} | {s.camera_angle} | "
            f"{s.camera_movement} | {s.lighting_style} | {s.depth_of_field} | "
            f"{desc_short} | {s.dialogue[:20] if s.dialogue != '无' else '无'} |"
        )
    return "\n".join([header, sep] + rows)


def _build_stats(shots: list[ShotAnalysis]) -> str:
    total = len(shots)
    fixed = sum(1 for s in shots if s.camera_movement == "固定")
    moving = total - fixed
    has_dialogue = sum(1 for s in shots if s.dialogue != "无")
    no_dialogue = total - has_dialogue
    avg_dur = sum(s.duration for s in shots) / total if total else 0
    return f"""> [!TIP] 场景统计
> - 全剧共 **{total}** 镜头
> - 固定镜头 **{fixed}** 个 / 运动镜头 **{moving}** 个
> - 有台词镜头 **{has_dialogue}** 个 / 无台词镜头 **{no_dialogue}** 个
> - 平均镜头时长：**{avg_dur:.1f}s**

"""


def _build_shot_detail(s: ShotAnalysis, video_id: str) -> str:
    """生成单个镜头的详细分析区块"""
    yaw_pitch = f"| **Yaw/Pitch**：{s.yaw}° / {s.pitch}°" if s.yaw or s.pitch else ""
    dolly_str = f"**Dolly**：{s.dolly}" if s.dolly != "z" else ""
    viseme_str = f"**【Viseme】** {s.viseme}\n" if s.viseme != "无" else ""

    # 关键帧嵌入（Obsidian wikilink）
    frames_md = ""
    for fp in s.extracted_frames[:3]:
        fname = Path(fp).name
        frames_md += f"![[./.assets/{video_id}/{fname}]]\n"

    audio_md = s.audio_layer.to_markdown() if s.audio_layer else "无"

    return f"""## 镜 {s.shot_number:02d} | {_fmt_range(s.start_time, s.end_time)} | {s.duration:.1f}s

**景别**：{s.shot_size} | **角度**：{s.camera_angle} | **运镜**：{s.camera_movement} {dolly_str} {yaw_pitch}
**光影**：{s.lighting_style} | **色温**：{s.color_temperature}K | **景深**：{s.depth_of_field}

**【画面描述】**
{s.visual_description or "（无画面描述）"}

**【分镜描述】**
{s.description}

**【台词】** {s.dialogue}

{viseme_str}**【Audio Layer】**
```
{audio_md}
```

**【叙事功能】**：{s.narrative_function or '—'} | **【视觉钩子】**：{s.visual_hook or '—'} | **【道具】**：{s.props}

**【关键帧】**
{frames_md}

**【imagePrompt】**
> {s.imagePrompt}

**【videoPrompt】**
```
{s.videoPrompt}
```

**【转场】** → {s.transition}

---

"""


class ObsidianExporter:
    """生成 Obsidian Markdown 笔记"""

    def __init__(self, series: str = "", episode: str = ""):
        self.series = series
        self.episode = episode

    def export(self, result: LapianResult) -> Path:
        output_dir = Path(result.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 笔记文件名
        stem = Path(result.video_filename).stem
        output_path = output_dir / f"{stem} 拉片分析.md"

        # 组装内容
        content_parts = []

        # Frontmatter
        content_parts.append(_build_frontmatter(result))

        # 标题
        content_parts.append(f"# {stem} 拉片分析\n")

        # 统计信息
        content_parts.append(f"> **分析时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        content_parts.append(f"> **视频时长**：{result.video_duration:.1f}s | **镜头数**：{result.total_shots} | **AI模型**：{result.analysis_model}\n")
        content_parts.append(f"> **场景阈值**：{result.scene_threshold}\n\n")

        # 分镜总览表格
        if result.shots:
            content_parts.append("## 分镜总览\n\n")
            content_parts.append(_build_overview_table(result.shots) + "\n\n")
            content_parts.append(_build_stats(result.shots))

        # 各镜头详情
        for shot in result.shots:
            content_parts.append(_build_shot_detail(shot, result.video_id))

        # 写入文件
        content = "".join(content_parts)
        output_path.write_text(content, encoding="utf-8")
        logger.info(f"笔记已生成: {output_path}")

        return output_path
