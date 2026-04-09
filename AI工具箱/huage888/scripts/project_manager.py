#!/usr/bin/env python3
"""
project_manager.py — huage888 项目管理器（Claude Code 编排层）

对标 Toonflow t_projectList + t_episodeList，为多集多项目提供：
- 项目/集数的 CRUD（TaskDB + 文件系统）
- Pipeline 任务创建与状态追踪（DAG 依赖）
- 制作状态仪表盘（跨项目资产/分镜/视频完成率）
- 与 run_episode_pipeline.py 集成（stage 粒度任务创建）

用法（CLI）：
  python3 scripts/project_manager.py list
  python3 scripts/project_manager.py status --project 漠玫传
  python3 scripts/project_manager.py dashboard
  python3 scripts/project_manager.py new-episode --project 漠玫传 --episode S01E02
  python3 scripts/project_manager.py run --project 漠玫传 --episode S01E01 --stages outline,storyboard

用法（代码）：
  from project_manager import ProjectManager
  mgr = ProjectManager()
  mgr.create_project("漠玫传", art_style="赛博墨韵", video_ratio="16:9")
  mgr.create_episode("漠玫传", "S01E01")
  mgr.run_pipeline("漠玫传", "S01E01", stages=["outline", "storyboard", "P1", "P2"])
  status = mgr.get_dashboard()
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from task_db import TaskDB, TaskState


# ─────────────────────────────────────────────────────────────────────────────
# 阶段定义
# ─────────────────────────────────────────────────────────────────────────────

PIPELINE_STAGES = [
    ("storyline",  "故事线",        "stage0_storyline"),
    ("outline",    "大纲",          "stage1_outline"),
    ("asset_imgs", "资产图片",      "stage1_5_asset_imgs"),
    ("script",     "剧本",          "stage1_8_script"),
    ("storyboard", "分镜脚本",       "stage2_storyboard"),
    ("P1",         "分镜图片",       "stage3_P1"),
    ("P2",         "宫格分镜",       "stage4_P2"),
    ("video",      "视频生成",       "stage5_video"),
]

# Pipeline 阶段依赖顺序
STAGE_ORDER = [s[0] for s in PIPELINE_STAGES]

# 依赖映射：stage -> 需要先完成的 stage
STAGE_DEPS = {
    "outline":    ["storyline"],
    "asset_imgs": ["outline"],
    "script":     ["outline"],
    "storyboard": ["script"],
    "P1":         ["storyboard"],
    "P2":         ["P1"],
    "video":      ["P2"],
}


# ─────────────────────────────────────────────────────────────────────────────
# ProjectManager
# ─────────────────────────────────────────────────────────────────────────────

class ProjectManager:
    """
    huage888 项目管理器

    对外接口：
      create_project(name, **kwargs) -> project_id
      create_episode(project_name, episode, script_path=None) -> episode_id
      run_pipeline(project_name, episode, stages=None, dry_run=False)
      get_project(name_or_id) -> dict
      list_projects() -> list[dict]
      get_episodes(project_name) -> list[dict]
      get_dashboard(project_name=None) -> dict
      get_episode_status(project_name, episode) -> dict
    """

    def __init__(self, db: Optional[TaskDB] = None):
        self._db = db or TaskDB()

    # ─── 项目 CRUD ───────────────────────────────────────────────────────────

    def create_project(
        self,
        name: str,
        type: str = "漫剧",
        art_style: str = "",
        video_ratio: str = "16:9",
    ) -> int:
        """创建项目（upsert），返回 project_id"""
        pid = self._db.upsert_project(
            name=name,
            type=type,
            art_style=art_style,
            video_ratio=video_ratio,
        )
        return pid

    def get_project(self, name_or_id: str | int) -> dict | None:
        """按 name 或 id 查询项目"""
        return self._db.get_project(name_or_id)

    def list_projects(self) -> list[dict]:
        """列出所有项目"""
        return [
            {
                "id": p.id,
                "name": p.name,
                "type": p.type,
                "art_style": p.art_style,
                "video_ratio": p.video_ratio,
                "created_at": p.created_at,
            }
            for p in self._db.list_projects()
        ]

    # ─── 集数 CRUD ────────────────────────────────────────────────────────────

    def create_episode(
        self,
        project_name: str,
        episode: str,
        script_path: str | Path | None = None,
    ) -> dict:
        """
        创建集数记录，在 TaskDB projects 中查找 project_id，
        并在 TaskDB tasks 中创建该集数的 pipeline 任务条目。

        返回 dict，含 project_id 和 episode_info。
        """
        project = self._db.get_project(project_name)
        if not project:
            raise ValueError(f"项目不存在：{project_name}")
        project_id = project.id

        # 解析集号（S01E01 -> 1）
        ep_num = self._parse_episode_number(episode)

        # 在 TaskDB tasks 中创建该集数的初始任务
        task_id = self._db.create(
            task_type="episode",
            name=f"{project_name} {episode}",
            params={"episode": episode, "project": project_name},
            project_id=project_id,
            episode=episode,
            stage="init",
        )

        # 若提供了剧本路径，读取字数等元信息
        meta = {}
        if script_path:
            p = Path(script_path)
            if p.exists():
                meta["script_path"] = str(p)
                meta["script_chars"] = len(p.read_text(encoding="utf-8"))

        return {
            "project_id": project_id,
            "project_name": project_name,
            "episode": episode,
            "episode_number": ep_num,
            "task_id": task_id,
            "meta": meta,
        }

    def get_episodes(self, project_name: str) -> list[dict]:
        """获取项目所有集数的 pipeline 状态"""
        project = self._db.get_project(project_name)
        if not project:
            return []

        project_id = project.id

        # 获取该项目的所有任务，按 episode 分组
        tasks = self._db.list_by_project(project_id)

        # 按 episode 分组
        episodes: dict[str, dict] = {}
        for t in tasks:
            ep = t.episode or "unknown"
            if ep not in episodes:
                episodes[ep] = {
                    "episode": ep,
                    "project_id": project_id,
                    "tasks": [],
                    "state": "unknown",
                }
            episodes[ep]["tasks"].append({
                "id": t.id,
                "name": t.name,
                "stage": t.stage,
                "state": int(t.state),
                "state_name": TaskState(t.state).name,
            })

        # 汇总每集状态
        result = []
        for ep, data in sorted(episodes.items()):
            task_count = len(data["tasks"])
            success_count = sum(1 for t in data["tasks"] if t["state"] == int(TaskState.SUCCESS))
            failed_count = sum(1 for t in data["tasks"] if t["state"] == int(TaskState.FAILED))

            if failed_count > 0:
                state = "failed"
            elif success_count == task_count and task_count > 0:
                state = "completed"
            elif success_count > 0:
                state = "in_progress"
            else:
                state = "pending"

            result.append({
                "episode": ep,
                "project_id": project_id,
                "state": state,
                "total_tasks": task_count,
                "completed_tasks": success_count,
                "tasks": data["tasks"],
            })

        return result

    def get_episode_status(self, project_name: str, episode: str) -> dict:
        """获取单集 pipeline 状态（各 stage 完成情况）"""
        project = self._db.get_project(project_name)
        if not project:
            return {}

        tasks = self._db.list_by_episode(episode)

        # 按 stage 汇总
        stage_status: dict[str, dict] = {}
        for stage_key, stage_label, _ in PIPELINE_STAGES:
            stage_status[stage_key] = {
                "stage": stage_key,
                "label": stage_label,
                "state": "not_started",
                "task_id": None,
            }

        for t in tasks:
            stage = t.stage or ""
            if stage in stage_status:
                state = TaskState(t.state)
                if state == TaskState.SUCCESS:
                    stage_status[stage]["state"] = "completed"
                elif state == TaskState.RUNNING:
                    stage_status[stage]["state"] = "running"
                elif state == TaskState.FAILED:
                    stage_status[stage]["state"] = "failed"
                elif state == TaskState.PENDING:
                    stage_status[stage]["state"] = "pending"
                stage_status[stage]["task_id"] = t.id

        return {
            "project": project_name,
            "episode": episode,
            "stages": list(stage_status.values()),
        }

    # ─── Pipeline 运行 ────────────────────────────────────────────────────────

    def run_pipeline(
        self,
        project_name: str,
        episode: str,
        stages: list[str] | None = None,
        dry_run: bool = False,
        **pipeline_kwargs,
    ) -> dict:
        """
        在 TaskDB 中创建 pipeline 任务，然后调用 run_episode_pipeline.py。

        stages: 要执行的 stage 列表（默认全部）
        dry_run: 不实际调用 API，仅打印执行计划

        返回执行结果摘要。
        """
        project = self._db.get_project(project_name)
        if not project:
            raise ValueError(f"项目不存在：{project_name}")
        project_id = project.id

        target_stages = stages or [s[0] for s in PIPELINE_STAGES]

        # 检查依赖
        dep_warnings = []
        for stage in target_stages:
            deps = STAGE_DEPS.get(stage, [])
            for dep in deps:
                if dep not in target_stages and dep not in [
                    s["stage"] for s in self.get_episode_status(project_name, episode)["stages"]
                    if s["state"] == "completed"
                ]:
                    dep_warnings.append(f"  ⚠️  {stage} 依赖 {dep}（未执行或未完成）")

        # 创建任务记录
        task_ids = []
        for stage in target_stages:
            stage_info = next((s for s in PIPELINE_STAGES if s[0] == stage), None)
            if not stage_info:
                continue
            _, stage_label, _ = stage_info

            task_id = self._db.create(
                task_type="pipeline",
                name=f"{project_name} {episode} {stage_label}",
                params={
                    "episode": episode,
                    "project": project_name,
                    "stage": stage,
                },
                project_id=project_id,
                episode=episode,
                stage=stage,
            )
            task_ids.append((stage, task_id))

        # 构造 CLI 命令
        SCRIPT_DIR = Path(__file__).parent
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "run_episode_pipeline.py"),
            "--episode", episode,
            "--project", project_name,
        ]

        # stage 参数映射
        if "storyline" in target_stages:
            cmd.append("--storyline")
        if "outline" in target_stages:
            cmd.append("--run-outline")
        if "asset_imgs" in target_stages:
            cmd.append("--run-asset-images")
        if "script" in target_stages:
            cmd.append("--run-script")
        if "storyboard" in target_stages:
            cmd.append("--run-storyboard")
        if "P1" in target_stages:
            cmd.append("--run-p1")
        if "P2" in target_stages:
            cmd.append("--run-p2")
        if "video" in target_stages:
            cmd.append("--run-video")

        if dry_run:
            cmd.append("--dry-run")

        for k, v in pipeline_kwargs.items():
            if v is not None:
                cmd.extend([f"--{k}", str(v)])

        result = {
            "project_name": project_name,
            "episode": episode,
            "stages": target_stages,
            "task_ids": dict(task_ids),
            "dry_run": dry_run,
            "command": " ".join(cmd),
            "dep_warnings": dep_warnings,
        }

        if dry_run:
            result["executed"] = False
            return result

        # 实际执行
        try:
            self._db.update(
                task_ids[0][1] if task_ids else "",
                TaskState.RUNNING,
            )
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
            )
            stdout = proc.stdout[-2000:] if proc.stdout else ""
            stderr = proc.stderr[-500:] if proc.stderr else ""

            if proc.returncode == 0:
                for stage, tid in task_ids:
                    self._db.update(tid, TaskState.SUCCESS, result={"stdout": stdout})
                result["executed"] = True
                result["returncode"] = 0
                result["stdout"] = stdout
            else:
                for stage, tid in task_ids:
                    self._db.update(tid, TaskState.FAILED, error=stderr[:500])
                result["executed"] = False
                result["returncode"] = proc.returncode
                result["stderr"] = stderr

        except subprocess.TimeoutExpired:
            result["executed"] = False
            result["error"] = "Pipeline 执行超时（10分钟）"
        except Exception as e:
            result["executed"] = False
            result["error"] = str(e)

        return result

    # ─── 仪表盘 ─────────────────────────────────────────────────────────────

    def get_dashboard(self, project_name: str | None = None) -> dict:
        """
        制作状态仪表盘。

        返回：
        {
          "projects": [...],
          "total_episodes": N,
          "completed_episodes": N,
          "total_assets": N,
          "total_videos": N,
          "overall_progress": 0.0-1.0,
        }
        """
        projects = self.list_projects()

        if project_name:
            projects = [p for p in projects if p["name"] == project_name]

        project_summaries = []
        total_episodes = 0
        completed_episodes = 0
        total_assets = 0
        total_videos = 0
        total_images = 0

        for p in projects:
            episodes = self.get_episodes(p["name"])
            total_episodes += len(episodes)
            completed_episodes += sum(1 for e in episodes if e["state"] == "completed")

            # 资产统计
            assets = self._db.get_assets(project_id=p["id"])
            images = self._db.list_images(project_id=p["id"])
            videos = self._db.list_videos(project_id=p["id"])
            total_assets += len(assets)
            total_images += len(images)
            total_videos += len(videos)

            # 计算进度
            if episodes:
                progress = sum(
                    e["completed_tasks"] / max(e["total_tasks"], 1)
                    for e in episodes
                ) / len(episodes)
            else:
                progress = 0.0

            project_summaries.append({
                "name": p["name"],
                "type": p["type"],
                "art_style": p["art_style"],
                "episodes": episodes,
                "episode_count": len(episodes),
                "completed_episodes": sum(1 for e in episodes if e["state"] == "completed"),
                "assets_count": len(assets),
                "images_count": len(images),
                "videos_count": len(videos),
                "progress": round(progress, 3),
            })

        # 全局进度
        all_tasks = self._db.list(limit=10000)
        if all_tasks:
            completed = sum(1 for t in all_tasks if TaskState(t.state) == TaskState.SUCCESS)
            overall = completed / len(all_tasks)
        else:
            overall = 0.0

        return {
            "projects": project_summaries,
            "total_episodes": total_episodes,
            "completed_episodes": completed_episodes,
            "total_assets": total_assets,
            "total_images": total_images,
            "total_videos": total_videos,
            "overall_progress": round(overall, 3),
            "generated_at": datetime.now().isoformat(),
        }

    # ─── 工具 ────────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_episode_number(episode: str) -> int:
        """解析集号：S01E01 -> 1"""
        import re
        m = re.search(r"E(\d+)", episode, re.IGNORECASE)
        return int(m.group(1)) if m else 1


# ─────────────────────────────────────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────────────────────────────────────

def _build_cli():
    import argparse

    parser = argparse.ArgumentParser(description="huage888 项目管理器")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # list
    sub.add_parser("list", help="列出所有项目")

    # status
    p_status = sub.add_parser("status", help="查看集数 pipeline 状态")
    p_status.add_argument("--project", required=True)
    p_status.add_argument("--episode", help="指定集数（默认全部）")

    # dashboard
    sub.add_parser("dashboard", help="制作状态仪表盘")

    # new-project
    p_np = sub.add_parser("new-project", help="新建项目")
    p_np.add_argument("--name", required=True)
    p_np.add_argument("--type", default="漫剧")
    p_np.add_argument("--art-style", default="")
    p_np.add_argument("--video-ratio", default="16:9")

    # new-episode
    p_ne = sub.add_parser("new-episode", help="新建集数")
    p_ne.add_argument("--project", required=True)
    p_ne.add_argument("--episode", required=True)
    p_ne.add_argument("--script", help="剧本路径")

    # run
    p_run = sub.add_parser("run", help="执行 pipeline")
    p_run.add_argument("--project", required=True)
    p_run.add_argument("--episode", required=True)
    p_run.add_argument("--stages", help="逗号分隔的 stage 列表")
    p_run.add_argument("--dry-run", action="store_true")

    # stage-status
    p_ss = sub.add_parser("stage-status", help="查看单集各 stage 状态")
    p_ss.add_argument("--project", required=True)
    p_ss.add_argument("--episode", required=True)

    return parser


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    """简单表格打印"""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    sep = "  "
    header_line = sep.join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(header_line)
    print("-" * len(header_line))
    for row in rows:
        print(sep.join(str(c).ljust(w) for c, w in zip(row, col_widths)))


def main():
    parser = _build_cli()
    args = parser.parse_args()

    mgr = ProjectManager()

    if args.cmd == "list":
        projects = mgr.list_projects()
        if not projects:
            print("尚无项目")
            return
        rows = [[p["name"], p["type"], p["art_style"], p["video_ratio"], p["created_at"] or ""]
                for p in projects]
        _print_table(["项目名", "类型", "风格", "比例", "创建时间"], rows)

    elif args.cmd == "status":
        episodes = mgr.get_episodes(args.project)
        if not episodes:
            print(f"项目「{args.project}」尚无集数记录")
            return
        if args.episode:
            episodes = [e for e in episodes if e["episode"] == args.episode]
        rows = [[e["episode"], e["state"], str(e["completed_tasks"]), str(e["total_tasks"])]
                for e in episodes]
        _print_table(["集数", "状态", "完成/总数", ""], rows)

    elif args.cmd == "dashboard":
        dash = mgr.get_dashboard()
        print(f"\n=== huage888 制作仪表盘 ===")
        print(f"总项目：{len(dash['projects'])}")
        print(f"总集数：{dash['total_episodes']}（已完成 {dash['completed_episodes']}）")
        print(f"总资产：{dash['total_assets']} | 图片：{dash['total_images']} | 视频：{dash['total_videos']}")
        print(f"全局进度：{dash['overall_progress']:.1%}")
        print()
        for p in dash["projects"]:
            print(f"  【{p['name']}】{p['type']} | {p['art_style']} | "
                  f"进度 {p['progress']:.0%} | "
                  f"集数 {p['completed_episodes']}/{p['episode_count']}")

    elif args.cmd == "new-project":
        pid = mgr.create_project(
            name=args.name,
            type=args.type,
            art_style=args.art_style,
            video_ratio=args.video_ratio,
        )
        print(f"✅ 项目已创建/更新 (id={pid}): {args.name}")
        print(f"   类型={args.type} | 风格={args.art_style} | 比例={args.video_ratio}")

    elif args.cmd == "new-episode":
        try:
            info = mgr.create_episode(
                project_name=args.project,
                episode=args.episode,
                script_path=args.script,
            )
            print(f"✅ 集数已创建: {info['episode']}")
            print(f"   project_id={info['project_id']} | task_id={info['task_id']}")
            if info["meta"]:
                print(f"   剧本字数：{info['meta'].get('script_chars', '?')} 字")
        except ValueError as e:
            print(f"❌ {e}")
            sys.exit(1)

    elif args.cmd == "run":
        stages = args.stages.split(",") if args.stages else None
        result = mgr.run_pipeline(
            project_name=args.project,
            episode=args.episode,
            stages=stages,
            dry_run=args.dry_run,
        )
        if result.get("dep_warnings"):
            for w in result["dep_warnings"]:
                print(w)
        if args.dry_run:
            print(f"[DRY RUN] 命令：{result['command']}")
        else:
            if result.get("error"):
                print(f"❌ 执行失败：{result['error']}")
            else:
                print(f"✅ Pipeline 完成 (returncode={result.get('returncode', 0)})")

    elif args.cmd == "stage-status":
        status = mgr.get_episode_status(args.project, args.episode)
        if not status:
            print(f"未找到 {args.project} {args.episode} 的状态")
            return
        print(f"\n{status['project']} · {status['episode']} 各 Stage 状态：\n")
        state_icons = {
            "completed": "✅",
            "running":   "⏳",
            "failed":    "❌",
            "pending":   "⏸️",
            "not_started": "⬜",
        }
        for s in status["stages"]:
            icon = state_icons.get(s["state"], "？")
            print(f"  {icon} {s['stage']:12s} {s['label']:12s} [{s['state']}]")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
