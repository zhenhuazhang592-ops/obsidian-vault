#!/usr/bin/env python3
"""
task_db.py — huage888 SQLite 任务状态数据库

对标 Toonflow t_video.state 模式，替代 JSON 文件方案：
- 支持任务依赖图（blockedBy DAG）
- 支持按 project/episode/stage 查询
- 对外接口与 task_state.TaskManager 兼容

Schema：
  projects           — 项目信息
  tasks              — 任务记录
  task_dependencies  — 任务依赖关系
  conversations      — 对话历史（与 conversation_manager.py 共用）

迁移：
  python3 scripts/task_db.py migrate
    → 将 .huage888/tasks/*.json 迁移到 SQLite
    → JSON 归档到 .huage888/tasks/archived/

用法：
  from task_db import TaskDB, TaskState

  db = TaskDB()

  # 与 TaskManager 兼容的接口
  task_id = db.create("qwen", "stage0_storyline_S01E01", params={"episode": "S01E01"})
  db.update(task_id, TaskState.RUNNING)
  db.update(task_id, TaskState.SUCCESS, result={"path": "/path/to/storyline.json"})

  task = db.get(task_id)
  print(task.state, task.result)

  # 新增接口
  db.add_dependency(task_id, depends_on_id=parent_id)
  blocked = db.get_blocked_tasks(task_id)
  tasks = db.list_by_project(project_id=1)
  dag = db.build_dependency_graph(project_id=1)
"""

import json
import os
import re
import shutil
import sqlite3
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Optional, Any


# ─────────────────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
DEFAULT_DB = BASE_DIR / ".huage888" / "huage888.db"
TASKS_DIR = BASE_DIR / ".huage888" / "tasks"
ARCHIVED_DIR = TASKS_DIR / "archived"


# ─────────────────────────────────────────────────────────────────────────────
# 状态枚举（与 task_state.TaskState 保持一致）
# ─────────────────────────────────────────────────────────────────────────────

class TaskState(IntEnum):
    PENDING = 0
    RUNNING = 1
    SUCCESS = 2
    FAILED = -1
    RETRYING = 3


# ─────────────────────────────────────────────────────────────────────────────
# 数据模型
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TaskRecord:
    """任务记录（对应 tasks 表）"""
    id: str
    type: str
    name: str
    state: TaskState
    project_id: Optional[int] = None
    episode: Optional[str] = None
    stage: Optional[str] = None
    params_json: Optional[str] = None
    result_json: Optional[str] = None
    error: Optional[str] = None
    external_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    def params(self) -> dict:
        if not self.params_json:
            return {}
        return json.loads(self.params_json)

    def result(self) -> dict:
        if not self.result_json:
            return {}
        return json.loads(self.result_json)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["state"] = int(d["state"])
        return d

    @classmethod
    def from_row(cls, row: tuple) -> "TaskRecord":
        return cls(
            id=row[0], type=row[1], name=row[2], state=TaskState(row[3]),
            project_id=row[4], episode=row[5], stage=row[6],
            params_json=row[7], result_json=row[8], error=row[9],
            external_id=row[10], retry_count=row[11], max_retries=row[12],
            created_at=row[13], started_at=row[14], finished_at=row[15],
        )


@dataclass
class ProjectRecord:
    """项目记录（对应 projects 表）"""
    id: int
    name: str
    type: Optional[str] = None
    art_style: Optional[str] = None
    video_ratio: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: tuple) -> "ProjectRecord":
        return cls(
            id=row[0], name=row[1], type=row[2],
            art_style=row[3], video_ratio=row[4], created_at=row[5],
        )


# ─────────────────────────────────────────────────────────────────────────────
# Schema
# ─────────────────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    type        TEXT,
    art_style   TEXT,
    video_ratio TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id              TEXT PRIMARY KEY,
    type            TEXT NOT NULL,
    name            TEXT NOT NULL,
    state           INTEGER DEFAULT 0,
    project_id      INTEGER,
    episode         TEXT,
    stage           TEXT,
    params_json     TEXT,
    result_json     TEXT,
    error           TEXT,
    external_id     TEXT,
    retry_count     INTEGER DEFAULT 0,
    max_retries     INTEGER DEFAULT 3,
    created_at      TEXT DEFAULT (datetime('now')),
    started_at      TEXT,
    finished_at      TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS task_dependencies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         TEXT NOT NULL,
    depends_on_id   TEXT NOT NULL,
    UNIQUE(task_id, depends_on_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (depends_on_id) REFERENCES tasks(id)
);

CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_episode ON tasks(episode);
CREATE INDEX IF NOT EXISTS idx_tasks_stage  ON tasks(stage);
CREATE INDEX IF NOT EXISTS idx_tasks_state  ON tasks(state);
CREATE INDEX IF NOT EXISTS idx_deps_task    ON task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_deps_dep     ON task_dependencies(depends_on_id);

-- ───────────────────────────────────────────────────────────────────────────
-- 资产表（对标 Toonflow t_assets）
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS assets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    type            TEXT NOT NULL,         -- character / scene / prop
    intro           TEXT,                  -- 资产描述
    prompt          TEXT,                  -- 图片生成 prompt
    video_prompt    TEXT,                  -- 视频生成 prompt
    remark         TEXT,                   -- 备注
    episode         TEXT,                   -- 首次出现集数
    duration        INTEGER,                -- 预计时长（秒）
    file_path       TEXT,                  -- 参考图路径
    project_id      INTEGER,
    script_id       TEXT,
    segment_id      TEXT,                  -- 分段 ID
    shot_index      INTEGER,               -- 镜头索引
    state           INTEGER DEFAULT 0,     -- 0=待生成/1=生成中/2=成功/-1=失败
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

-- ───────────────────────────────────────────────────────────────────────────
-- 图片表（对标 Toonflow t_image）
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS images (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path       TEXT,
    type            TEXT,                   -- grid / single / asset / storyboard
    assets_id       INTEGER,
    script_id       TEXT,
    project_id      INTEGER,
    video_id        INTEGER,
    shot_index      INTEGER,               -- 镜头号
    state           INTEGER DEFAULT 0,     -- 0=待生成/1=生成中/2=成功/-1=失败
    error           TEXT,
    provider        TEXT,                   -- doubao / kling
    model           TEXT,                   -- doubao-seedream-5-0-260128
    created_at      TEXT DEFAULT (datetime('now'))
);

-- ───────────────────────────────────────────────────────────────────────────
-- 视频表（对标 Toonflow t_video）
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS videos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path       TEXT,
    resolution      TEXT,                   -- 1280x720 / 1920x1080
    prompt          TEXT,                   -- 视频生成 prompt
    first_frame     TEXT,                   -- 首帧图路径
    storyboard_imgs TEXT,                  -- JSON: [shot1_img, shot2_img, ...]
    model           TEXT,                   -- doubao-seedance-2-0-260128
    error_reason    TEXT,
    time_seconds    REAL,                  -- 生成耗时
    state           INTEGER DEFAULT 0,     -- 0=进行中/1=成功/-1=失败
    script_id       TEXT,
    config_id       INTEGER,
    project_id      INTEGER,
    created_at      TEXT DEFAULT (datetime('now')),
    finished_at     TEXT
);

-- ───────────────────────────────────────────────────────────────────────────
-- 视频配置表（对标 Toonflow t_videoConfig）
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS video_configs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id       TEXT,
    project_id      INTEGER,
    ai_config_id   INTEGER,
    audio_enabled   INTEGER DEFAULT 0,    -- 0=否/1=是
    manufacturer    TEXT,                  -- volcengine / kling / vidu / ...
    mode            TEXT,                  -- startEnd / multi / single
    start_frame     INTEGER,
    end_frame       INTEGER,
    images_json     TEXT,                  -- JSON: [img_path, ...]
    resolution      TEXT,                  -- 1280x720
    duration        INTEGER,               -- 秒
    prompt          TEXT,
    selected_result_id INTEGER,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

-- ───────────────────────────────────────────────────────────────────────────
-- 艺术风格表（对标 Toonflow t_artStyle）
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS art_styles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    category        TEXT,                   -- 常用风格 / IP风格 / 插画风格 / ...
    styles_json     TEXT NOT NULL          -- JSON: [{name, prompt, prompt_en, file_url}, ...]
);

-- ───────────────────────────────────────────────────────────────────────────
-- 提示词模板表（对标 Toonflow t_prompts）
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS prompts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE,   -- outlineScript-main / storyboard-shot / ...
    name            TEXT,
    type            TEXT,                   -- mainAgent / subAgent / system / tool
    parent_code     TEXT,                  -- 父模板 code
    default_value   TEXT NOT NULL,         -- 默认 prompt 模板
    custom_value    TEXT,                  -- 用户自定义覆盖
    description     TEXT,
    updated_at      TEXT DEFAULT (datetime('now'))
);

-- ───────────────────────────────────────────────────────────────────────────
-- 索引（新增表）
-- ───────────────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_assets_project  ON assets(project_id);
CREATE INDEX IF NOT EXISTS idx_assets_type    ON assets(type);
CREATE INDEX IF NOT EXISTS idx_assets_episode ON assets(episode);
CREATE INDEX IF NOT EXISTS idx_images_project  ON images(project_id);
CREATE INDEX IF NOT EXISTS idx_images_state    ON images(state);
CREATE INDEX IF NOT EXISTS idx_videos_project  ON videos(project_id);
CREATE INDEX IF NOT EXISTS idx_videos_state    ON videos(state);
CREATE INDEX IF NOT EXISTS idx_prompts_code   ON prompts(code);
CREATE INDEX IF NOT EXISTS idx_prompts_type   ON prompts(type);
"""

MIGRATION_SELECT_SQL = """
SELECT
    id, type, name, state, project_id, episode, stage,
    params_json, result_json, error, external_id,
    retry_count, max_retries, created_at, started_at, finished_at
FROM tasks ORDER BY created_at
"""


# ─────────────────────────────────────────────────────────────────────────────
# TaskDB
# ─────────────────────────────────────────────────────────────────────────────

class TaskDB:
    """
    SQLite 任务状态数据库

    对外接口（与 TaskManager 兼容）：
      create(task_type, name, params=None, max_retries=3, project_id=None,
             episode=None, stage=None) -> task_id
      get(task_id) -> TaskRecord | None
      update(task_id, state, result=None, error=None, external_id=None,
             increment_retry=False) -> bool
      list(task_type=None, state=None, limit=100) -> list[TaskRecord]
      summary() -> dict

    SQLite 独有接口：
      add_dependency(task_id, depends_on_id)
      get_blocked_tasks(task_id) -> list[str]
      list_by_project(project_id) -> list[TaskRecord]
      list_by_episode(episode) -> list[TaskRecord]
      build_dependency_graph(project_id=None) -> dict
      upsert_project(name, **kwargs) -> project_id
    """

    DEFAULT_DB = DEFAULT_DB

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path or self.DEFAULT_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._init_schema()

    # ─── 连接管理 ───────────────────────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def _init_schema(self) -> None:
        conn = self._get_conn()
        conn.executescript(SCHEMA_SQL)
        conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ─── 工具 ───────────────────────────────────────────────────────────────

    def _now(self) -> str:
        return datetime.now().isoformat()

    def _short_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def _row_to_record(self, row: sqlite3.Row) -> TaskRecord:
        return TaskRecord(
            id=row["id"], type=row["type"], name=row["name"],
            state=TaskState(row["state"]),
            project_id=row["project_id"], episode=row["episode"], stage=row["stage"],
            params_json=row["params_json"], result_json=row["result_json"],
            error=row["error"], external_id=row["external_id"],
            retry_count=row["retry_count"], max_retries=row["max_retries"],
            created_at=row["created_at"], started_at=row["started_at"],
            finished_at=row["finished_at"],
        )

    # ─── TaskManager 兼容接口 ───────────────────────────────────────────────

    def create(
        self,
        task_type: str,
        name: str,
        params: dict | None = None,
        max_retries: int = 3,
        project_id: int | None = None,
        episode: str | None = None,
        stage: str | None = None,
    ) -> str:
        """创建任务，返回 task_id"""
        task_id = self._short_id()
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO tasks
               (id, type, name, state, project_id, episode, stage,
                params_json, max_retries, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task_id, task_type, name, int(TaskState.PENDING),
                project_id, episode, stage,
                json.dumps(params or {}, ensure_ascii=False) if params else None,
                max_retries, self._now(),
            )
        )
        conn.commit()
        return task_id

    def get(self, task_id: str) -> Optional[TaskRecord]:
        """按 task_id 查询"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return self._row_to_record(row) if row else None

    def update(
        self,
        task_id: str,
        state: TaskState,
        result: dict | None = None,
        error: str | None = None,
        external_id: str | None = None,
        increment_retry: bool = False,
    ) -> bool:
        """更新任务状态"""
        conn = self._get_conn()

        updates = ["state = ?"]
        vals = [int(state)]

        if state == TaskState.RUNNING:
            updates.append("started_at = ?")
            vals.append(self._now())
        elif state in (TaskState.SUCCESS, TaskState.FAILED):
            updates.append("finished_at = ?")
            vals.append(self._now())

        if result is not None:
            updates.append("result_json = ?")
            vals.append(json.dumps(result, ensure_ascii=False))

        if error is not None:
            updates.append("error = ?")
            vals.append(error)

        if external_id is not None:
            updates.append("external_id = ?")
            vals.append(external_id)

        if increment_retry:
            updates.append("retry_count = retry_count + 1")
            updates.append("state = ?")
            vals.append(int(TaskState.RETRYING))

        vals.append(task_id)
        cur = conn.execute(
            f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?",
            vals
        )
        conn.commit()
        return cur.rowcount > 0

    def list(
        self,
        task_type: str | None = None,
        state: TaskState | None = None,
        limit: int = 100,
    ) -> list[TaskRecord]:
        """查询任务列表"""
        conn = self._get_conn()
        query = "SELECT * FROM tasks WHERE 1=1"
        params: list = []
        if task_type:
            query += " AND type = ?"
            params.append(task_type)
        if state is not None:
            query += " AND state = ?"
            params.append(int(state))
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        return [self._row_to_record(r) for r in rows]

    def summary(self) -> dict:
        """统计摘要"""
        conn = self._get_conn()
        total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        by_state = {}
        for row in conn.execute(
            "SELECT state, COUNT(*) FROM tasks GROUP BY state"
        ).fetchall():
            by_state[int(row[0])] = row[1]
        return {"total": total, "by_state": by_state}

    # ─── 依赖管理 ───────────────────────────────────────────────────────────

    def add_dependency(self, task_id: str, depends_on_id: str) -> None:
        """添加任务依赖（task_id 依赖 depends_on_id）"""
        conn = self._get_conn()
        conn.execute(
            "INSERT OR IGNORE INTO task_dependencies (task_id, depends_on_id) VALUES (?, ?)",
            (task_id, depends_on_id),
        )
        conn.commit()

    def get_blocked_tasks(self, task_id: str) -> list[str]:
        """获取依赖某 task 的所有任务 ID（blocked by task_id）"""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT task_id FROM task_dependencies WHERE depends_on_id = ?",
            (task_id,)
        ).fetchall()
        return [r[0] for r in rows]

    def get_dependencies(self, task_id: str) -> list[str]:
        """获取某 task 的所有依赖 ID"""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT depends_on_id FROM task_dependencies WHERE task_id = ?",
            (task_id,)
        ).fetchall()
        return [r[0] for r in rows]

    # ─── 项目管理 ───────────────────────────────────────────────────────────

    def upsert_project(
        self,
        name: str,
        type: str | None = None,
        art_style: str | None = None,
        video_ratio: str | None = None,
    ) -> int:
        """创建或更新项目，返回 project_id"""
        conn = self._get_conn()
        existing = conn.execute(
            "SELECT id FROM projects WHERE name = ?", (name,)
        ).fetchone()
        if existing:
            return existing[0]
        cur = conn.execute(
            """INSERT INTO projects (name, type, art_style, video_ratio)
               VALUES (?, ?, ?, ?)""",
            (name, type, art_style, video_ratio),
        )
        conn.commit()
        return cur.lastrowid

    def get_project(self, name: str | int) -> Optional[ProjectRecord]:
        """按 name 或 id 查询项目"""
        conn = self._get_conn()
        if isinstance(name, int):
            row = conn.execute(
                "SELECT * FROM projects WHERE id = ?", (name,)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM projects WHERE name = ?", (name,)
            ).fetchone()
        return ProjectRecord.from_row(row) if row else None

    def list_projects(self) -> list[ProjectRecord]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
        return [ProjectRecord.from_row(r) for r in rows]

    # ─── 查询扩展 ───────────────────────────────────────────────────────────

    def list_by_project(self, project_id: int) -> list[TaskRecord]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM tasks WHERE project_id = ? ORDER BY created_at",
            (project_id,)
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def list_by_episode(self, episode: str) -> list[TaskRecord]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM tasks WHERE episode = ? ORDER BY created_at",
            (episode,)
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def list_by_stage(self, stage: str) -> list[TaskRecord]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM tasks WHERE stage = ? ORDER BY created_at",
            (stage,)
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def build_dependency_graph(self, project_id: int | None = None) -> dict:
        """
        构建项目依赖 DAG。

        返回格式：
        {
          "nodes": [{"id": "...", "name": "...", "state": 0}, ...],
          "edges": [{"from": "dep_id", "to": "task_id"}, ...]
        }
        """
        conn = self._get_conn()
        if project_id is not None:
            tasks_rows = conn.execute(
                "SELECT * FROM tasks WHERE project_id = ?", (project_id,)
            ).fetchall()
        else:
            tasks_rows = conn.execute("SELECT * FROM tasks").fetchall()

        tasks = {r["id"]: {"id": r["id"], "name": r["name"], "state": int(r["state"])}
                 for r in tasks_rows}

        edges = []
        deps_rows = conn.execute(
            "SELECT task_id, depends_on_id FROM task_dependencies"
        ).fetchall()
        for task_id, depends_on_id in deps_rows:
            if task_id in tasks or depends_on_id in tasks:
                edges.append({"from": depends_on_id, "to": task_id})

        return {"nodes": list(tasks.values()), "edges": edges}

    # ─── 资产管理 ───────────────────────────────────────────────────────────

    def upsert_asset(
        self,
        name: str,
        asset_type: str,
        project_id: int | None = None,
        episode: str | None = None,
        intro: str | None = None,
        prompt: str | None = None,
        video_prompt: str | None = None,
        file_path: str | None = None,
        state: int = 0,
        segment_id: str | None = None,
        shot_index: int | None = None,
    ) -> int:
        """创建或更新资产，返回 asset_id"""
        conn = self._get_conn()
        existing = conn.execute(
            "SELECT id FROM assets WHERE name = ? AND type = ?",
            (name, asset_type),
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE assets SET intro=?, prompt=?, video_prompt=?,
                   file_path=?, state=?, segment_id=?, shot_index=?, updated_at=?
                   WHERE id=?""",
                (intro, prompt, video_prompt, file_path, state,
                 segment_id, shot_index, self._now(), existing[0]),
            )
            conn.commit()
            return existing[0]
        cur = conn.execute(
            """INSERT INTO assets
               (name, type, intro, prompt, video_prompt, project_id, episode,
                file_path, state, segment_id, shot_index)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, asset_type, intro, prompt, video_prompt, project_id,
             episode, file_path, state, segment_id, shot_index),
        )
        conn.commit()
        return cur.lastrowid

    def get_assets(
        self,
        project_id: int | None = None,
        asset_type: str | None = None,
        episode: str | None = None,
    ) -> list[dict]:
        """查询资产列表"""
        conn = self._get_conn()
        query = "SELECT * FROM assets WHERE 1=1"
        params: list = []
        if project_id is not None:
            query += " AND project_id = ?"
            params.append(project_id)
        if asset_type:
            query += " AND type = ?"
            params.append(asset_type)
        if episode:
            query += " AND episode = ?"
            params.append(episode)
        query += " ORDER BY id"
        return [dict(r) for r in conn.execute(query, params).fetchall()]

    def update_asset_state(self, asset_id: int, state: int, file_path: str | None = None) -> None:
        """更新资产状态和文件路径"""
        conn = self._get_conn()
        if file_path:
            conn.execute(
                "UPDATE assets SET state=?, file_path=?, updated_at=? WHERE id=?",
                (state, file_path, self._now(), asset_id),
            )
        else:
            conn.execute(
                "UPDATE assets SET state=?, updated_at=? WHERE id=?",
                (state, self._now(), asset_id),
            )
        conn.commit()

    # ─── 图片记录 ───────────────────────────────────────────────────────────

    def create_image(
        self,
        file_path: str | None = None,
        image_type: str = "storyboard",
        project_id: int | None = None,
        shot_index: int | None = None,
        state: int = 0,
        provider: str | None = None,
        model: str | None = None,
    ) -> int:
        """创建图片记录，返回 image_id"""
        conn = self._get_conn()
        cur = conn.execute(
            """INSERT INTO images
               (file_path, type, project_id, shot_index, state, provider, model)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (file_path, image_type, project_id, shot_index, state, provider, model),
        )
        conn.commit()
        return cur.lastrowid

    def update_image_state(self, image_id: int, state: int, file_path: str | None = None, error: str | None = None) -> None:
        """更新图片状态"""
        conn = self._get_conn()
        if file_path:
            conn.execute(
                "UPDATE images SET state=?, file_path=?, error=? WHERE id=?",
                (state, file_path, error, image_id),
            )
        else:
            conn.execute(
                "UPDATE images SET state=?, error=? WHERE id=?",
                (state, error, image_id),
            )
        conn.commit()

    def list_images(self, project_id: int | None = None, state: int | None = None) -> list[dict]:
        """查询图片列表"""
        conn = self._get_conn()
        query = "SELECT * FROM images WHERE 1=1"
        params: list = []
        if project_id is not None:
            query += " AND project_id = ?"
            params.append(project_id)
        if state is not None:
            query += " AND state = ?"
            params.append(state)
        return [dict(r) for r in conn.execute(query, params).fetchall()]

    # ─── 视频记录 ───────────────────────────────────────────────────────────

    def create_video(
        self,
        file_path: str | None = None,
        prompt: str | None = None,
        project_id: int | None = None,
        model: str | None = None,
        state: int = 0,
    ) -> int:
        """创建视频记录，返回 video_id"""
        conn = self._get_conn()
        cur = conn.execute(
            """INSERT INTO videos
               (file_path, prompt, project_id, model, state)
               VALUES (?, ?, ?, ?, ?)""",
            (file_path, prompt, project_id, model, state),
        )
        conn.commit()
        return cur.lastrowid

    def update_video(
        self,
        video_id: int,
        state: int | None = None,
        file_path: str | None = None,
        error_reason: str | None = None,
        time_seconds: float | None = None,
    ) -> None:
        """更新视频状态"""
        conn = self._get_conn()
        updates = []
        vals: list = []
        if state is not None:
            updates.append("state = ?")
            vals.append(state)
        if file_path is not None:
            updates.append("file_path = ?")
            vals.append(file_path)
        if error_reason is not None:
            updates.append("error_reason = ?")
            vals.append(error_reason)
        if time_seconds is not None:
            updates.append("time_seconds = ?")
            vals.append(time_seconds)
        if state in (1, -1):
            updates.append("finished_at = ?")
            vals.append(self._now())
        if updates:
            vals.append(video_id)
            conn.execute(f"UPDATE videos SET {', '.join(updates)} WHERE id=?", vals)
            conn.commit()

    def list_videos(self, project_id: int | None = None, state: int | None = None) -> list[dict]:
        """查询视频列表"""
        conn = self._get_conn()
        query = "SELECT * FROM videos WHERE 1=1"
        params: list = []
        if project_id is not None:
            query += " AND project_id = ?"
            params.append(project_id)
        if state is not None:
            query += " AND state = ?"
            params.append(state)
        return [dict(r) for r in conn.execute(query, params).fetchall()]

    # ─── 视频配置 ───────────────────────────────────────────────────────────

    def upsert_video_config(
        self,
        script_id: str,
        project_id: int | None = None,
        manufacturer: str | None = None,
        mode: str | None = None,
        images_json: str | None = None,
        resolution: str | None = None,
        duration: int | None = None,
        prompt: str | None = None,
        audio_enabled: int = 0,
    ) -> int:
        """创建或更新视频配置"""
        conn = self._get_conn()
        existing = conn.execute(
            "SELECT id FROM video_configs WHERE script_id = ?", (script_id,)
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE video_configs SET manufacturer=?, mode=?, images_json=?,
                   resolution=?, duration=?, prompt=?, audio_enabled=?,
                   updated_at=? WHERE id=?""",
                (manufacturer, mode, images_json, resolution, duration,
                 prompt, audio_enabled, self._now(), existing[0]),
            )
            conn.commit()
            return existing[0]
        cur = conn.execute(
            """INSERT INTO video_configs
               (script_id, project_id, manufacturer, mode, images_json,
                resolution, duration, prompt, audio_enabled)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (script_id, project_id, manufacturer, mode, images_json,
             resolution, duration, prompt, audio_enabled),
        )
        conn.commit()
        return cur.lastrowid

    # ─── 艺术风格 ───────────────────────────────────────────────────────────

    def upsert_art_style(self, name: str, category: str, styles_json: str) -> int:
        """创建或更新艺术风格"""
        conn = self._get_conn()
        existing = conn.execute(
            "SELECT id FROM art_styles WHERE name = ?", (name,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE art_styles SET category=?, styles_json=? WHERE id=?",
                (category, styles_json, existing[0]),
            )
            conn.commit()
            return existing[0]
        cur = conn.execute(
            "INSERT INTO art_styles (name, category, styles_json) VALUES (?, ?, ?)",
            (name, category, styles_json),
        )
        conn.commit()
        return cur.lastrowid

    def list_art_styles(self, category: str | None = None) -> list[dict]:
        """查询艺术风格"""
        conn = self._get_conn()
        if category:
            rows = conn.execute(
                "SELECT * FROM art_styles WHERE category = ?", (category,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM art_styles ORDER BY category, name").fetchall()
        return [dict(r) for r in rows]

    # ─── 提示词模板 ─────────────────────────────────────────────────────────

    def upsert_prompt(
        self,
        code: str,
        name: str | None = None,
        prompt_type: str | None = None,
        default_value: str = "",
        custom_value: str | None = None,
        parent_code: str | None = None,
        description: str | None = None,
    ) -> int:
        """创建或更新提示词模板"""
        conn = self._get_conn()
        existing = conn.execute(
            "SELECT id FROM prompts WHERE code = ?", (code,)
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE prompts SET name=?, type=?, custom_value=?,
                   parent_code=?, description=?, updated_at=? WHERE code=?""",
                (name, prompt_type, custom_value, parent_code,
                 description, self._now(), code),
            )
            conn.commit()
            return existing[0]
        cur = conn.execute(
            """INSERT INTO prompts
               (code, name, type, default_value, custom_value, parent_code, description)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (code, name, prompt_type, default_value, custom_value, parent_code, description),
        )
        conn.commit()
        return cur.lastrowid

    def get_prompt(self, code: str) -> dict | None:
        """获取提示词模板（custom_value 优先于 default_value）"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM prompts WHERE code = ?", (code,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["value"] = d.get("custom_value") or d.get("default_value")
        return d

    def list_prompts(self, prompt_type: str | None = None) -> list[dict]:
        """查询提示词模板列表"""
        conn = self._get_conn()
        if prompt_type:
            rows = conn.execute(
                "SELECT * FROM prompts WHERE type = ? ORDER BY code", (prompt_type,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM prompts ORDER BY code").fetchall()
        return [dict(r) for r in rows]

    def seed_default_prompts(self) -> None:
        """初始化默认提示词模板（对标 Toonflow t_prompts）"""
        defaults = [
            ("outlineScript-main",    "大纲故事线主 Agent",   "mainAgent",  "", None,
             "大纲故事线协调 Agent，协调 AI1(故事师)、AI2(大纲师)、director(导演) 三个子 Agent 工作"),
            ("outlineScript-a1",     "故事师",              "subAgent",   "outlineScript-main", "", None,
             "分析小说章节，生成故事线"),
            ("outlineScript-a2",       "大纲师",              "subAgent",   "outlineScript-main", "", None,
             "根据故事线生成大纲 JSON"),
            ("outlineScript-director","导演",               "subAgent",   "outlineScript-main", "", None,
             "审核故事线和大纲的质量"),
            ("storyboard-main",       "分镜协调 Agent",      "mainAgent",  "", None,
             "分镜协调 Agent，管理 segmentAgent 和 shotAgent"),
            ("storyboard-segment",    "片段师",              "subAgent",   "storyboard-main", "", None,
             "识别剧本关键片段，生成 segments"),
            ("storyboard-shot",       "分镜师",             "subAgent",   "storyboard-main", "", None,
             "生成电影级分镜提示词"),
            ("generateImagePrompts",  "宫格分镜提示词生成",  "tool",       "", "", None,
             "宫格分镜提示词生成工具"),
        ]
        for row in defaults:
            self.upsert_prompt(
                code=row[0], name=row[1], prompt_type=row[2],
                default_value=row[3], parent_code=row[4],
                description=row[6],
            )

    # ─── 迁移 ───────────────────────────────────────────────────────────────

    @staticmethod
    def migrate_from_json(
        tasks_dir: Path = TASKS_DIR,
        db_path: Path = DEFAULT_DB,
        dry_run: bool = False,
    ) -> dict:
        """
        将 .huage888/tasks/*.json 迁移到 SQLite。

        返回：{"migrated": N, "skipped": M, "errors": [...]}
        """
        if not tasks_dir.exists():
            return {"migrated": 0, "skipped": 0, "errors": [f"目录不存在: {tasks_dir}"]}

        db = TaskDB(db_path)
        migrated, skipped, errors = 0, 0, []

        # 确保 archived 目录存在
        if not dry_run:
            ARCHIVED_DIR.mkdir(parents=True, exist_ok=True)

        for json_file in sorted(tasks_dir.glob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))

                # 映射字段
                params = data.get("params", {})
                episode = params.get("episode")
                stage = params.get("stage")

                task_id = db.create(
                    task_type=data.get("type", "unknown"),
                    name=data.get("name", json_file.stem),
                    params=params,
                    max_retries=data.get("max_retries", 3),
                    episode=episode,
                    stage=stage,
                )

                state_map = {"pending": 0, "running": 1, "success": 2, "failed": -1}
                state_str = data.get("state", "pending")
                state = state_map.get(state_str, 0)

                update_kwargs: dict = {"state": TaskState(state)}
                if data.get("result"):
                    update_kwargs["result"] = data["result"]
                if data.get("error"):
                    update_kwargs["error"] = data["error"]

                db.update(task_id, **update_kwargs)

                if not dry_run:
                    # 归档原文件
                    shutil.move(str(json_file), str(ARCHIVED_DIR / json_file.name))

                migrated += 1

            except Exception as e:
                skipped += 1
                errors.append(f"{json_file.name}: {e}")

        db.close()
        return {"migrated": migrated, "skipped": skipped, "errors": errors}


# ─────────────────────────────────────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="huage888 任务数据库")
    sub = parser.add_subparsers(dest="cmd")

    # migrate
    p_migrate = sub.add_parser("migrate", help="迁移 JSON → SQLite")
    p_migrate.add_argument("--from", dest="tasks_dir", default=str(TASKS_DIR))
    p_migrate.add_argument("--to", dest="db_path", default=str(DEFAULT_DB))
    p_migrate.add_argument("--dry-run", action="store_true")

    # summary
    sub.add_parser("summary", help="统计摘要")

    # list
    p_list = sub.add_parser("list", help="列出任务")
    p_list.add_argument("--type")
    p_list.add_argument("--stage")
    p_list.add_argument("--episode")
    p_list.add_argument("--limit", type=int, default=20)

    # get
    p_get = sub.add_parser("get", help="查看任务详情")
    p_get.add_argument("task_id")

    # projects
    sub.add_parser("projects", help="列出项目")

    # dag
    p_dag = sub.add_parser("dag", help="输出依赖 DAG")
    p_dag.add_argument("--project-id", type=int)

    args = parser.parse_args()
    db = TaskDB()

    if args.cmd == "migrate":
        result = TaskDB.migrate_from_json(
            tasks_dir=Path(args.tasks_dir),
            db_path=Path(args.db_path),
            dry_run=args.dry_run,
        )
        print(f"迁移完成: {result}")

    elif args.cmd == "summary":
        s = db.summary()
        print(f"总任务数: {s['total']}")
        for st, cnt in s["by_state"].items():
            print(f"  {TaskState(st).name}: {cnt}")

    elif args.cmd == "list":
        if args.stage:
            tasks = db.list_by_stage(args.stage)
        elif args.episode:
            tasks = db.list_by_episode(args.episode)
        else:
            tasks = db.list(task_type=args.type, limit=args.limit)
        for t in tasks:
            print(f"  [{t.id}] {t.name} | {TaskState(t.state).name} | stage={t.stage} | ep={t.episode}")

    elif args.cmd == "get":
        t = db.get(args.task_id)
        if t:
            print(f"id:       {t.id}")
            print(f"name:     {t.name}")
            print(f"type:     {t.type}")
            print(f"state:    {TaskState(t.state).name}")
            print(f"stage:    {t.stage}")
            print(f"episode:  {t.episode}")
            print(f"params:   {t.params()}")
            print(f"result:   {t.result()}")
            print(f"error:    {t.error}")
            print(f"retry:    {t.retry_count}/{t.max_retries}")
            print(f"created:  {t.created_at}")
            print(f"started:  {t.started_at}")
            print(f"finished: {t.finished_at}")
        else:
            print(f"任务不存在: {args.task_id}")

    elif args.cmd == "projects":
        for p in db.list_projects():
            print(f"  [{p.id}] {p.name} | type={p.type} | style={p.art_style} | ratio={p.video_ratio}")

    elif args.cmd == "dag":
        dag = db.build_dependency_graph(args.project_id)
        print(json.dumps(dag, indent=2, ensure_ascii=False))

    else:
        parser.print_help()

    db.close()
