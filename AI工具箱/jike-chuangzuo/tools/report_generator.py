#!/usr/bin/env python3
"""制作报告生成器"""
import json, pathlib, sqlite3
from datetime import datetime

DB_PATH = pathlib.Path(__file__).parent.parent / "db" / "jike.db"


def generate_report(project_id: int, output_dir: pathlib.Path) -> pathlib.Path:
    """从 SQLite 读取项目状态，生成 Markdown 制作报告"""
    conn = sqlite3.connect(DB_PATH)

    project = conn.execute(
        "SELECT name, type, art_style, create_time FROM t_project WHERE id = ?",
        (project_id,),
    ).fetchone()

    outlines = conn.execute(
        "SELECT episode_index, title, data, state FROM t_outline WHERE project_id = ? ORDER BY episode_index",
        (project_id,),
    ).fetchall()

    assets = conn.execute(
        "SELECT name, type, intro, state FROM t_asset WHERE project_id = ?",
        (project_id,),
    ).fetchall()

    storyline = conn.execute(
        "SELECT content FROM t_storyline WHERE project_id = ? ORDER BY create_time DESC LIMIT 1",
        (project_id,),
    ).fetchone()

    shots = conn.execute(
        "SELECT COUNT(*) FROM t_shot s JOIN t_segment seg ON s.segment_id = seg.id WHERE seg.storyboard_id = ?",
        (project_id,),
    ).fetchone()

    conn.close()

    if not project:
        raise ValueError(f"Project {project_id} not found")

    project_name = project[0]
    lines = [
        f"# 制作报告 · {project_name}",
        "",
        f"**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**项目类型:** {project[1]}",
        f"**视觉风格:** {project[2]}",
        f"**创建时间:** {project[3]}",
        "",
        "## 生产阶段",
        "",
        "- [ ] 故事线",
        "- [ ] 大纲",
        "- [ ] 资产提取",
        "- [ ] 资产图生成",
        "- [ ] 分镜脚本",
        "- [ ] 分镜图生成",
        "- [ ] 视频生成",
        "- [ ] 合成输出",
        "",
        "## 故事线",
        "",
    ]

    if storyline and storyline[0]:
        try:
            sl = json.loads(storyline[0])
            lines.append(f"**故事主线:** {sl.get('story_arc', '?')}")
            lines.append("")
            for evt in sl.get("key_events", []):
                lines.append(f"- {evt}")
            lines.append("")
            lines.append(f"**主要角色:** {', '.join(sl.get('characters', []))}")
            lines.append(f"\n**场景:** {', '.join(sl.get('scenes', []))}")
        except (json.JSONDecodeError, TypeError):
            lines.append(storyline[0][:500])
    else:
        lines.append("（未生成）")

    lines.append("\n## 剧集大纲")
    for ep in outlines:
        data = {}
        try:
            data = json.loads(ep[2]) if ep[2] else {}
        except json.JSONDecodeError:
            pass
        lines.append(f"\n### 第{ep[0]}集: {ep[1] or '未命名'}  [{ep[3]}]")
        lines.append(f"- **核心矛盾:** {data.get('coreConflict', '?')}")
        lines.append(f"- **情绪曲线:** {data.get('emotionalCurve', '?')}")
        lines.append(f"- **视觉高光:** {', '.join(data.get('visualHighlights', []))}")
        lines.append(f"- **金句:** {', '.join(data.get('classicQuotes', []))}")

    lines.append("\n## 资产清单")
    lines.append(f"| 名称 | 类型 | 简介 | 状态 |")
    lines.append(f"|------|------|------|------|")
    for a in assets:
        lines.append(f"| {a[0]} | {a[1]} | {a[2] or ''} | {a[3]} |")

    lines.append(f"\n**资产总计:** {len(assets)} 个")

    report_path = output_dir / "production_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
