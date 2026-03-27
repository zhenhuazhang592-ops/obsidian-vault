"""
CDP资产库 SQLite 持久化层
基于漫舟CDP JSON规范，支持角色/场景/道具的全生命周期管理。
兼容 cdp-global-schema.json 和 cdp-global.json 格式导入/导出。
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

# ─────────────────────────────────────────────────────────────
# 连接管理（线程安全）
# ─────────────────────────────────────────────────────────────

_local = threading.local()


def _get_conn(db_path: str) -> sqlite3.Connection:
    """获取当前线程的数据库连接（线程隔离）"""
    tid = threading.current_thread().ident
    key = f"_conn_{tid}"

    if not hasattr(_local, key):
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # 每次执行后自动提交（关闭 autocommit 时）
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        setattr(_local, key, conn)

    return getattr(_local, key)


def _close_conn(db_path: str) -> None:
    """关闭当前线程的数据库连接"""
    tid = threading.current_thread().ident
    key = f"_conn_{tid}"
    if hasattr(_local, key):
        getattr(_local, key).close()
        delattr(_local, key)


def _exe(
    conn: sqlite3.Connection,
    sql: str,
    params: tuple = (),
    *,
    commit: bool = True,
) -> sqlite3.Cursor:
    """执行SQL并返回游标"""
    cur = conn.execute(sql, params)
    if commit:
        conn.commit()
    return cur


def _fetchone(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> Optional[dict]:
    """查询单条"""
    row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


def _fetchall(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    """查询多条"""
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────
# JSON 序列化辅助
# ─────────────────────────────────────────────────────────────

def _dumps(val: Any) -> str:
    return json.dumps(val, ensure_ascii=False, separators=(",", ":"))


def _loads(val: str | None) -> Any:
    if val is None or val == "":
        return None
    return json.loads(val)


def _ts() -> float:
    return time.time()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "+08:00")


# ─────────────────────────────────────────────────────────────
# 字段映射：CDP JSON  →  SQLite 列
# ─────────────────────────────────────────────────────────────

# Characters
_CHAR_JSON_TO_COL: dict[str, str] = {
    "id":            "character_id",
    "name":          "character_name",
    "role":          "character_type",
    "dna":           "metadata",         # 展开存 metadata
    "visual_anchors": "metadata",        # 同上
    "aliases":       "metadata",
    "appearance":    "appearance",
    "reference_images": "grid_image",
    "usage_count":   "usage_count",
    "last_used":     "last_used",
    "projects":      "projects",
}


def _char_from_row(row: dict) -> dict:
    """将数据库行还原为 cdp-global.json 的字符对象格式"""
    meta = _loads(row.get("metadata")) or {}
    result = {
        "id":             row["character_id"],
        "name":           row["character_name"],
        "role":           row["character_type"],
        "aliases":        meta.get("aliases", []),
        "dna": {
            "identity":   meta.get("identity"),
            "appearance": row.get("appearance") or meta.get("appearance"),
            "clothing":  meta.get("clothing"),
            "expression": meta.get("expression"),
            "gesture":    meta.get("gesture"),
            "perspective": meta.get("perspective"),
        },
        "visual_anchors":   meta.get("visual_anchors", []),
        "reference_images": _loads(row.get("single_images")) or [],
        "usage_count":    row["usage_count"],
        "last_used":      row["last_used"],
        "projects":       _loads(row.get("projects")) or [],
        # SQLite 内部字段（可选暴露）
        "_voice":         row.get("voice"),
        "_gender":        row.get("gender"),
    }
    return {k: v for k, v in result.items() if v is not None and v != []}


def _char_meta_from_json(char: dict) -> tuple[str, str, str, str]:
    """
    从 CDP JSON char 对象提取 metadata、appearance、single_images、voice。
    返回 (metadata_json, appearance, single_images_json, voice)
    """
    dna = char.get("dna", {}) or {}

    # aliases / visual_anchors / dna 全部合并进 metadata
    meta_keys = ["aliases", "visual_anchors", "identity",
                 "clothing", "expression", "gesture", "perspective"]
    meta = {}
    for k in meta_keys:
        val = dna.get(k) if k in dna else char.get(k)
        if val is not None:
            meta[k] = val

    # aliases 顶层也有
    if char.get("aliases"):
        meta["aliases"] = char["aliases"]

    # reference_images → single_images
    ref_images = char.get("reference_images") or []
    single_images = {}
    for idx, img in enumerate(ref_images):
        single_images[f"P{idx+1:02d}"] = img

    # appearance 可能存在于顶层
    appearance = char.get("appearance") or dna.get("appearance") or ""

    return _dumps(meta), appearance, _dumps(single_images), char.get("voice", "")


# Locations
def _loc_from_row(row: dict) -> dict:
    meta = _loads(row.get("metadata")) or {}
    lighting_raw = row.get("lighting") or ""
    # lighting 可能是纯字符串（"夜间冷白荧光..."）也可能是 JSON 字符串
    try:
        lighting = _loads(lighting_raw) if lighting_raw.startswith("{") or lighting_raw.startswith("[") else lighting_raw
    except Exception:
        lighting = lighting_raw
    result = {
        "id":               row["location_id"],
        "name":             row["location_name"],
        "category":         row["location_type"],
        "lighting":         lighting if isinstance(lighting, str) else meta.get("lighting"),
        "props":            meta.get("props", []),
        "aliases":          meta.get("aliases", []),
        "reference_images": _loads(row.get("scene_image")) or [],
        "usage_count":      row["usage_count"],
        "last_used":        row["last_used"],
        "projects":         _loads(row.get("projects")) or [],
    }
    return {k: v for k, v in result.items() if v is not None and v != []}


def _loc_meta_from_json(loc: dict) -> tuple[str, str, str]:
    """
    从 CDP JSON loc 对象提取 metadata、lighting、scene_image。
    返回 (metadata_json, lighting_json, scene_image_json)
    """
    # lighting 可能是 str 或 null
    lighting_val = loc.get("lighting")
    lighting_str = lighting_val if isinstance(lighting_val, str) else _dumps(lighting_val or {})

    meta_keys = ["aliases", "props"]
    meta = {}
    for k in meta_keys:
        val = loc.get(k)
        if val is not None:
            meta[k] = val

    ref_images = loc.get("reference_images") or []
    return _dumps(meta), lighting_str, _dumps(ref_images)


# Items
def _item_from_row(row: dict) -> dict:
    meta = _loads(row.get("metadata")) or {}
    result = {
        "id":               row["item_id"],
        "name":             row["item_name"],
        "category":         row["item_type"],
        "narrative_weight": row.get("narrative_role"),   # narrative_role → narrative_weight
        "appearance":       row.get("metadata") and meta.get("appearance"),
        "reference_images": _loads(row.get("image")) or [],
        "usage_count":      row["usage_count"],
        "last_used":        row["last_used"],
        "projects":         _loads(row.get("projects")) or [],
    }
    return {k: v for k, v in result.items() if v is not None}


def _item_meta_from_json(item: dict) -> tuple[str, str]:
    """从 CDP JSON item 对象提取 metadata、image。返回 (metadata_json, image_json)"""
    meta = {}
    for k in ("appearance",):
        if item.get(k):
            meta[k] = item[k]

    ref_images = item.get("reference_images") or []
    return _dumps(meta), _dumps(ref_images)


# ─────────────────────────────────────────────────────────────
# 主类
# ─────────────────────────────────────────────────────────────

class SQLiteCDP:
    """
    CDP 资产库 SQLite 持久化层。

    支持：
    - Characters / Locations / Items / Projects / UsageLog 全 CRUD
    - 从 cdp-global.json / cdp-global-schema.json 导入
    - 导出为 CDP JSON 格式
    - usage_count 追踪（效果分析飞轮底座）
    - 线程安全（threading.local 连接隔离）
    """

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "./data/manzhou_cdp.db") -> None:
        self.db_path = str(Path(db_path).resolve())
        self._init_db()

    # ── 初始化 ─────────────────────────────────────────────

    def _init_db(self) -> None:
        conn = _get_conn(self.db_path)
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='_meta'"
        )
        if not cur.fetchone():
            self._create_tables(conn)
            conn.execute(
                "INSERT INTO _meta (key, value) VALUES ('version', ?)",
                (str(self.SCHEMA_VERSION),),
            )
            conn.commit()
        else:
            self._migrate(conn)

    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """创建所有表"""
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS _meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS characters (
            character_id  TEXT PRIMARY KEY,
            character_name TEXT NOT NULL,
            character_type TEXT,
            gender         TEXT,
            appearance     TEXT,
            voice          TEXT,
            personality    TEXT,
            grid_image     TEXT,
            single_images  TEXT,
            usage_count    INTEGER DEFAULT 0,
            last_used      TEXT,
            projects       TEXT,
            metadata       TEXT,
            created_at     REAL DEFAULT (unixepoch('now')),
            updated_at     REAL DEFAULT (unixepoch('now'))
        );

        CREATE TABLE IF NOT EXISTS locations (
            location_id    TEXT PRIMARY KEY,
            location_name  TEXT NOT NULL,
            location_type  TEXT,
            scene_image    TEXT,
            lighting       TEXT,
            atmosphere     TEXT,
            usage_count    INTEGER DEFAULT 0,
            last_used      TEXT,
            projects       TEXT,
            metadata       TEXT,
            created_at     REAL DEFAULT (unixepoch('now')),
            updated_at     REAL DEFAULT (unixepoch('now'))
        );

        CREATE TABLE IF NOT EXISTS items (
            item_id         TEXT PRIMARY KEY,
            item_name       TEXT NOT NULL,
            item_type       TEXT,
            narrative_role  TEXT,
            image           TEXT,
            usage_count     INTEGER DEFAULT 0,
            last_used       TEXT,
            projects        TEXT,
            metadata        TEXT,
            created_at      REAL DEFAULT (unixepoch('now')),
            updated_at      REAL DEFAULT (unixepoch('now'))
        );

        CREATE TABLE IF NOT EXISTS usage_log (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type      TEXT NOT NULL,
            entity_id        TEXT NOT NULL,
            project_name     TEXT NOT NULL,
            episode          INTEGER,
            shot_id          TEXT,
            usage_count_inc  INTEGER DEFAULT 1,
            timestamp        REAL DEFAULT (unixepoch('now')),
            metadata         TEXT
        );

        CREATE TABLE IF NOT EXISTS projects (
            project_name    TEXT PRIMARY KEY,
            description     TEXT,
            total_episodes  INTEGER DEFAULT 0,
            total_shots     INTEGER DEFAULT 0,
            created_at      REAL DEFAULT (unixepoch('now')),
            updated_at      REAL DEFAULT (unixepoch('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_char_project  ON characters(character_id);
        CREATE INDEX IF NOT EXISTS idx_loc_project   ON locations(location_id);
        CREATE INDEX IF NOT EXISTS idx_item_project  ON items(item_id);
        CREATE INDEX IF NOT EXISTS idx_usage_entity  ON usage_log(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_usage_proj    ON usage_log(project_name);
        """)

    def _migrate(self, conn: sqlite3.Connection) -> None:
        """数据库迁移（检查版本）"""
        row = _fetchone(conn, "SELECT value FROM _meta WHERE key='version'")
        version = int(row["value"]) if row else 0
        if version < self.SCHEMA_VERSION:
            # 当前 v1，后续扩展在这里处理
            conn.execute(
                "INSERT OR REPLACE INTO _meta (key, value) VALUES ('version', ?)",
                (str(self.SCHEMA_VERSION),),
            )
            conn.commit()

    # ── Character CRUD ─────────────────────────────────────

    def add_character(self, char_data: dict) -> bool:
        """
        添加角色。char_data 可接受以下格式：
        - cdp-global.json 格式（id/name/role/dna/...）
        - SQLite 直接格式（character_id/character_name/...）
        Returns True 成功，False（如已存在则静默返回 False）
        """
        conn = _get_conn(self.db_path)
        char_id = char_data.get("id") or char_data.get("character_id")
        if not char_id:
            return False

        # 幂等：已存在则跳过
        if _fetchone(conn, "SELECT 1 FROM characters WHERE character_id=?", (char_id,)):
            return False

        name = char_data.get("name") or char_data.get("character_name") or char_id
        char_type = char_data.get("role") or char_data.get("character_type") or ""
        gender = char_data.get("gender") or ""
        appearance = char_data.get("appearance") or ""
        voice = char_data.get("voice") or ""
        personality = char_data.get("personality") or ""
        grid_image = char_data.get("grid_image") or ""
        projects = _dumps(char_data.get("projects") or [])

        # 解析 reference_images / single_images
        ref_images = char_data.get("reference_images") or char_data.get("single_images") or []
        single_images = {}
        for idx, img in enumerate(ref_images):
            single_images[f"P{idx+1:02d}"] = img

        # usage_count / last_used
        usage_count = int(char_data.get("usage_count", 0))
        last_used = char_data.get("last_used") or ""
        if not last_used and usage_count > 0:
            last_used = _now_iso()

        # metadata（合并 dna / aliases / visual_anchors）
        dna = char_data.get("dna") or {}
        meta = dict(dna)
        for k in ("aliases", "visual_anchors"):
            if k in char_data:
                meta[k] = char_data[k]
        metadata = _dumps(meta)

        _exe(
            conn,
            """INSERT INTO characters
               (character_id, character_name, character_type, gender, appearance,
                voice, personality, grid_image, single_images, usage_count,
                last_used, projects, metadata, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, unixepoch('now'))""",
            (char_id, name, char_type, gender, appearance, voice, personality,
             grid_image, _dumps(single_images), usage_count, last_used,
             projects, metadata),
        )
        return True

    def get_character(self, char_id: str) -> dict | None:
        conn = _get_conn(self.db_path)
        row = _fetchone(conn, "SELECT * FROM characters WHERE character_id=?", (char_id,))
        return _char_from_row(row) if row else None

    def list_characters(
        self,
        project: str = "",
        char_type: str = "",
    ) -> list[dict]:
        conn = _get_conn(self.db_path)
        sql = "SELECT * FROM characters WHERE 1=1"
        params: list = []

        if char_type:
            sql += " AND character_type=?"
            params.append(char_type)
        if project:
            sql += " AND projects LIKE ?"
            params.append(f"%{project}%")

        sql += " ORDER BY usage_count DESC, character_id"
        return [_char_from_row(r) for r in _fetchall(conn, sql, tuple(params))]

    def update_character(self, char_id: str, data: dict) -> bool:
        conn = _get_conn(self.db_path)
        if not _fetchone(conn, "SELECT 1 FROM characters WHERE character_id=?", (char_id,)):
            return False

        allowed = {
            "character_name", "character_type", "gender", "appearance",
            "voice", "personality", "grid_image", "single_images",
            "usage_count", "last_used", "projects", "metadata",
        }
        sets, params = [], []
        for k, v in data.items():
            col = k if k in allowed else None
            if col is None:
                continue
            if col in ("projects", "single_images", "metadata") and isinstance(v, (list, dict)):
                v = _dumps(v)
            sets.append(f"{col}=?")
            params.append(v)
        if not sets:
            return False

        params.append(char_id)
        _exe(conn, f"UPDATE characters SET {','.join(sets)}, updated_at=unixepoch('now') WHERE character_id=?", tuple(params))
        return True

    def delete_character(self, char_id: str) -> bool:
        conn = _get_conn(self.db_path)
        cur = _exe(conn, "DELETE FROM characters WHERE character_id=?", (char_id,))
        return cur.rowcount > 0

    def find_character(self, name: str, project: str = "") -> dict | None:
        conn = _get_conn(self.db_path)
        sql = """SELECT * FROM characters
                 WHERE character_name LIKE ? OR character_name LIKE ?"""
        params: tuple = (f"%{name}%", f"{name}%")
        if project:
            sql += " AND projects LIKE ?"
            params = (f"%{name}%", f"{name}%", f"%{project}%")
        sql += " LIMIT 1"
        row = _fetchone(conn, sql, params)
        return _char_from_row(row) if row else None

    def record_usage(
        self,
        entity_type: str,
        entity_id: str,
        project: str,
        episode: int | None = None,
        shot_id: str = "",
        **meta: Any,
    ) -> None:
        """
        记录一次使用，同时：
        1. 写入 usage_log 表
        2. 更新对应实体的 usage_count + last_used
        """
        conn = _get_conn(self.db_path)
        ts = time.time()

        # 写日志
        _exe(
            conn,
            """INSERT INTO usage_log
               (entity_type, entity_id, project_name, episode, shot_id, timestamp, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (entity_type, entity_id, project, episode, shot_id, ts, _dumps(meta)),
        )

        # 更新实体 usage_count
        table = {"character": "characters", "location": "locations", "item": "items"}.get(
            entity_type, "characters"
        )
        id_col = {
            "character": "character_id",
            "location": "location_id",
            "item": "item_id",
        }.get(entity_type, "character_id")

        now_iso = _now_iso()
        conn.execute(
            f"""UPDATE {table} SET
                usage_count = usage_count + 1,
                last_used = ?,
                updated_at = unixepoch('now')
                WHERE {id_col}=?""",
            (now_iso, entity_id),
        )
        # 更新 projects 列表
        self._upsert_project_ref(conn, table, id_col, entity_id, project)
        conn.commit()

    def _upsert_project_ref(
        self, conn: sqlite3.Connection,
        table: str, id_col: str, entity_id: str, project: str,
    ) -> None:
        """确保实体的 projects JSON 中包含该 project 名"""
        row = conn.execute(f"SELECT projects FROM {table} WHERE {id_col}=?", (entity_id,)).fetchone()
        if not row:
            return
        projects: list = _loads(row[0]) or []
        if project and project not in projects:
            projects.append(project)
            conn.execute(
                f"UPDATE {table} SET projects=? WHERE {id_col}=?",
                (_dumps(projects), entity_id),
            )

    def get_top_characters(self, project: str = "", limit: int = 10) -> list[dict]:
        conn = _get_conn(self.db_path)
        sql = "SELECT * FROM characters"
        params: tuple = ()
        if project:
            sql += " WHERE projects LIKE ?"
            params = (f"%{project}%",)
        sql += f" ORDER BY usage_count DESC LIMIT {limit}"
        return [_char_from_row(r) for r in _fetchall(conn, sql, params)]

    # ── Location CRUD ──────────────────────────────────────

    def add_location(self, loc_data: dict) -> bool:
        conn = _get_conn(self.db_path)
        loc_id = loc_data.get("id") or loc_data.get("location_id")
        if not loc_id:
            return False
        if _fetchone(conn, "SELECT 1 FROM locations WHERE location_id=?", (loc_id,)):
            return False

        name = loc_data.get("name") or loc_data.get("location_name") or loc_id
        loc_type = loc_data.get("category") or loc_data.get("location_type") or ""
        atmosphere = loc_data.get("atmosphere") or ""

        # lighting 可能是 str，直接存；也可能是 dict
        lighting_val = loc_data.get("lighting")
        lighting_str = lighting_val if isinstance(lighting_val, str) else _dumps(lighting_val or {})

        # reference_images → scene_image
        ref_images = loc_data.get("reference_images") or []
        scene_image = _dumps(ref_images)

        usage_count = int(loc_data.get("usage_count", 0))
        last_used = loc_data.get("last_used") or ""
        if not last_used and usage_count > 0:
            last_used = _now_iso()

        projects = _dumps(loc_data.get("projects") or [])

        # metadata
        meta = {}
        for k in ("aliases", "props"):
            if loc_data.get(k):
                meta[k] = loc_data[k]
        metadata = _dumps(meta)

        _exe(
            conn,
            """INSERT INTO locations
               (location_id, location_name, location_type, scene_image, lighting,
                atmosphere, usage_count, last_used, projects, metadata, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, unixepoch('now'))""",
            (loc_id, name, loc_type, scene_image, lighting_str, atmosphere,
             usage_count, last_used, projects, metadata),
        )
        return True

    def get_location(self, loc_id: str) -> dict | None:
        conn = _get_conn(self.db_path)
        row = _fetchone(conn, "SELECT * FROM locations WHERE location_id=?", (loc_id,))
        return _loc_from_row(row) if row else None

    def list_locations(self, project: str = "") -> list[dict]:
        conn = _get_conn(self.db_path)
        sql = "SELECT * FROM locations"
        params: tuple = ()
        if project:
            sql += " WHERE projects LIKE ?"
            params = (f"%{project}%",)
        sql += " ORDER BY usage_count DESC, location_id"
        return [_loc_from_row(r) for r in _fetchall(conn, sql, params)]

    def update_location(self, loc_id: str, data: dict) -> bool:
        conn = _get_conn(self.db_path)
        if not _fetchone(conn, "SELECT 1 FROM locations WHERE location_id=?", (loc_id,)):
            return False
        allowed = {
            "location_name", "location_type", "scene_image", "lighting",
            "atmosphere", "usage_count", "last_used", "projects", "metadata",
        }
        sets, params = [], []
        for k, v in data.items():
            if k not in allowed:
                continue
            if k in ("projects", "metadata") and isinstance(v, (list, dict)):
                v = _dumps(v)
            sets.append(f"{k}=?")
            params.append(v)
        if not sets:
            return False
        params.append(loc_id)
        _exe(conn, f"UPDATE locations SET {','.join(sets)}, updated_at=unixepoch('now') WHERE location_id=?", tuple(params))
        return True

    def delete_location(self, loc_id: str) -> bool:
        conn = _get_conn(self.db_path)
        cur = _exe(conn, "DELETE FROM locations WHERE location_id=?", (loc_id,))
        return cur.rowcount > 0

    def find_location(self, name: str, project: str = "") -> dict | None:
        conn = _get_conn(self.db_path)
        sql = """SELECT * FROM locations
                 WHERE location_name LIKE ? OR location_name LIKE ?"""
        params: tuple = (f"%{name}%", f"{name}%")
        if project:
            sql += " AND projects LIKE ?"
            params = (f"%{name}%", f"{name}%", f"%{project}%")
        sql += " LIMIT 1"
        row = _fetchone(conn, sql, params)
        return _loc_from_row(row) if row else None

    # ── Item CRUD ───────────────────────────────────────────

    def add_item(self, item_data: dict) -> bool:
        conn = _get_conn(self.db_path)
        item_id = item_data.get("id") or item_data.get("item_id")
        if not item_id:
            return False
        if _fetchone(conn, "SELECT 1 FROM items WHERE item_id=?", (item_id,)):
            return False

        name = item_data.get("name") or item_data.get("item_name") or item_id
        item_type = item_data.get("category") or item_data.get("item_type") or ""
        narrative_role = item_data.get("narrative_weight") or item_data.get("narrative_role") or ""

        ref_images = item_data.get("reference_images") or []
        image = _dumps(ref_images)

        usage_count = int(item_data.get("usage_count", 0))
        last_used = item_data.get("last_used") or ""
        if not last_used and usage_count > 0:
            last_used = _now_iso()

        projects = _dumps(item_data.get("projects") or [])

        meta = {}
        for k in ("appearance",):
            if item_data.get(k):
                meta[k] = item_data[k]
        metadata = _dumps(meta)

        _exe(
            conn,
            """INSERT INTO items
               (item_id, item_name, item_type, narrative_role, image,
                usage_count, last_used, projects, metadata, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, unixepoch('now'))""",
            (item_id, name, item_type, narrative_role, image,
             usage_count, last_used, projects, metadata),
        )
        return True

    def get_item(self, item_id: str) -> dict | None:
        conn = _get_conn(self.db_path)
        row = _fetchone(conn, "SELECT * FROM items WHERE item_id=?", (item_id,))
        return _item_from_row(row) if row else None

    def list_items(self, project: str = "", item_type: str = "") -> list[dict]:
        conn = _get_conn(self.db_path)
        sql = "SELECT * FROM items WHERE 1=1"
        params: list = []
        if item_type:
            sql += " AND item_type=?"
            params.append(item_type)
        if project:
            sql += " AND projects LIKE ?"
            params.append(f"%{project}%")
        sql += " ORDER BY usage_count DESC, item_id"
        return [_item_from_row(r) for r in _fetchall(conn, sql, tuple(params))]

    def update_item(self, item_id: str, data: dict) -> bool:
        conn = _get_conn(self.db_path)
        if not _fetchone(conn, "SELECT 1 FROM items WHERE item_id=?", (item_id,)):
            return False
        allowed = {
            "item_name", "item_type", "narrative_role", "image",
            "usage_count", "last_used", "projects", "metadata",
        }
        sets, params = [], []
        for k, v in data.items():
            if k not in allowed:
                continue
            if k in ("projects", "metadata") and isinstance(v, (list, dict)):
                v = _dumps(v)
            sets.append(f"{k}=?")
            params.append(v)
        if not sets:
            return False
        params.append(item_id)
        _exe(conn, f"UPDATE items SET {','.join(sets)}, updated_at=unixepoch('now') WHERE item_id=?", tuple(params))
        return True

    def delete_item(self, item_id: str) -> bool:
        conn = _get_conn(self.db_path)
        cur = _exe(conn, "DELETE FROM items WHERE item_id=?", (item_id,))
        return cur.rowcount > 0

    def find_item(self, name: str, project: str = "") -> dict | None:
        conn = _get_conn(self.db_path)
        sql = """SELECT * FROM items
                 WHERE item_name LIKE ? OR item_name LIKE ?"""
        params: tuple = (f"%{name}%", f"{name}%")
        if project:
            sql += " AND projects LIKE ?"
            params = (f"%{name}%", f"{name}%", f"%{project}%")
        sql += " LIMIT 1"
        row = _fetchone(conn, sql, params)
        return _item_from_row(row) if row else None

    # ── Project CRUD ───────────────────────────────────────

    def add_project(self, project_name: str, description: str = "") -> bool:
        conn = _get_conn(self.db_path)
        _exe(
            conn,
            """INSERT OR IGNORE INTO projects (project_name, description)
               VALUES (?, ?)""",
            (project_name, description),
        )
        return True

    def get_project(self, project_name: str) -> dict | None:
        conn = _get_conn(self.db_path)
        return _fetchone(conn, "SELECT * FROM projects WHERE project_name=?", (project_name,))

    def list_projects(self) -> list[dict]:
        conn = _get_conn(self.db_path)
        return _fetchall(conn, "SELECT * FROM projects ORDER BY project_name")

    def update_project_stats(self, project_name: str, episodes: int, shots: int) -> None:
        conn = _get_conn(self.db_path)
        self.add_project(project_name)
        _exe(
            conn,
            """UPDATE projects SET
                total_episodes=?, total_shots=?, updated_at=unixepoch('now')
                WHERE project_name=?""",
            (episodes, shots, project_name),
        )

    # ── 导入 / 导出 ─────────────────────────────────────────

    def import_from_json(self, json_path: str, project: str = "") -> dict:
        """
        从 CDP JSON 文件导入。
        兼容：
        - cdp-global.json（完整示例）
        - cdp-global-schema.json（模板）
        - 格子间女人-cdp-migration.json

        Returns: {"characters": n, "locations": n, "items": n, "skipped": n, "errors": [str]}
        """
        result: dict = {"characters": 0, "locations": 0, "items": 0, "skipped": 0, "errors": []}

        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            result["errors"].append(f"读取文件失败: {e}")
            return result

        meta = data.get("meta", {}) or {}
        json_project = meta.get("project") or project or "default"

        self.add_project(json_project, description=meta.get("migration_note", ""))

        # Characters
        for char in data.get("characters") or []:
            try:
                # schema 模板中 id 为 null 跳过
                char_id = char.get("id") or char.get("character_id")
                if not char_id:
                    result["skipped"] += 1
                    continue
                ok = self.add_character(char)
                if ok:
                    result["characters"] += 1
                else:
                    result["skipped"] += 1
            except Exception as e:
                result["errors"].append(f"角色导入失败 {char.get('id')}: {e}")

        # Locations
        for loc in data.get("locations") or []:
            try:
                loc_id = loc.get("id") or loc.get("location_id")
                if not loc_id:
                    result["skipped"] += 1
                    continue
                ok = self.add_location(loc)
                if ok:
                    result["locations"] += 1
                else:
                    result["skipped"] += 1
            except Exception as e:
                result["errors"].append(f"场景导入失败 {loc.get('id')}: {e}")

        # Items
        for item in data.get("items") or []:
            try:
                item_id = item.get("id") or item.get("item_id")
                if not item_id:
                    result["skipped"] += 1
                    continue
                ok = self.add_item(item)
                if ok:
                    result["items"] += 1
                else:
                    result["skipped"] += 1
            except Exception as e:
                result["errors"].append(f"道具导入失败 {item.get('id')}: {e}")

        return result

    def export_to_json(self, json_path: str, project: str = "") -> bool:
        """
        导出为 CDP JSON 格式（兼容 cdp-global.json）。
        如 project 为空则导出全部。
        """
        conn = _get_conn(self.db_path)

        # Characters
        if project:
            rows = _fetchall(conn, "SELECT * FROM characters WHERE projects LIKE ?", (f"%{project}%",))
        else:
            rows = _fetchall(conn, "SELECT * FROM characters")
        characters = [_char_from_row(r) for r in rows]

        # Locations
        if project:
            rows = _fetchall(conn, "SELECT * FROM locations WHERE projects LIKE ?", (f"%{project}%",))
        else:
            rows = _fetchall(conn, "SELECT * FROM locations")
        locations = [_loc_from_row(r) for r in rows]

        # Items
        if project:
            rows = _fetchall(conn, "SELECT * FROM items WHERE projects LIKE ?", (f"%{project}%",))
        else:
            rows = _fetchall(conn, "SELECT * FROM items")
        items = [_item_from_row(r) for r in rows]

        output = {
            "version": "1.0.0",
            "meta": {
                "created": _now_iso(),
                "project": project or "all",
                "type": "global_asset_library",
                "append": False,
            },
            "characters": characters,
            "locations": locations,
            "items": items,
        }

        try:
            os.makedirs(os.path.dirname(json_path) or ".", exist_ok=True)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    # ── 统计 ───────────────────────────────────────────────

    def get_stats(self, project: str = "") -> dict:
        """返回统计摘要 + Top角色 + 最近使用"""
        conn = _get_conn(self.db_path)

        def count(table: str) -> int:
            r = _fetchone(conn, f"SELECT COUNT(*) as n FROM {table}")
            return r["n"] if r else 0

        total_chars = count("characters")
        total_locs = count("locations")
        total_items = count("items")
        total_logs = count("usage_log")

        # top characters
        if project:
            top_chars = _fetchall(
                conn,
                "SELECT * FROM characters WHERE projects LIKE ? ORDER BY usage_count DESC LIMIT 5",
                (f"%{project}%",),
            )
        else:
            top_chars = _fetchall(conn, "SELECT * FROM characters ORDER BY usage_count DESC LIMIT 5")
        top_characters = [_char_from_row(r) for r in top_chars]

        # recently used（在 usage_log 中）
        if project:
            recent = _fetchall(
                conn,
                """SELECT * FROM usage_log
                   WHERE project_name=? ORDER BY timestamp DESC LIMIT 10""",
                (project,),
            )
        else:
            recent = _fetchall(conn, "SELECT * FROM usage_log ORDER BY timestamp DESC LIMIT 10")

        recently_used = [
            {
                "entity_type": r["entity_type"],
                "entity_id":   r["entity_id"],
                "project":     r["project_name"],
                "episode":     r["episode"],
                "shot_id":     r["shot_id"],
                "timestamp":   r["timestamp"],
            }
            for r in recent
        ]

        return {
            "total_characters":  total_chars,
            "total_locations":   total_locs,
            "total_items":       total_items,
            "total_usage_log":   total_logs,
            "top_characters":    top_characters,
            "recently_used":     recently_used,
        }

    # ── 上下文管理 ─────────────────────────────────────────

    def close(self) -> None:
        """显式关闭连接（可选，程序退出时调用）"""
        _close_conn(self.db_path)

    def __enter__(self) -> "SQLiteCDP":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


# ─────────────────────────────────────────────────────────────
# 自测代码（__main__）
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tmp.name
    tmp.close()

    print("=" * 60)
    print("CDP SQLite 持久化层 — 自测")
    print("=" * 60)

    # 1. 初始化
    cdp = SQLiteCDP(db_path)
    print(f"[OK] 数据库初始化: {db_path}")

    # 2. 添加项目
    cdp.add_project("格子间女人", "漫舟AI漫剧首部作品")
    print("[OK] add_project")

    # 3. 导入示例数据（从实际 CDP JSON）
    base = "/Users/huage/Obsidian Vault/AI漫剧生产/漫舟进化/P0-资产库"
    json_path = f"{base}/格子间女人-cdp-migration.json"
    if os.path.exists(json_path):
        r = cdp.import_from_json(json_path, project="格子间女人")
        print(f"[OK] import_from_json → {r}")
    else:
        # 用内嵌示例
        sample_chars = [
            {
                "id": "char_test1", "name": "测试角色A",
                "role": "protagonist", "gender": "female",
                "dna": {"identity": "测试身份", "clothing": "正装"},
                "aliases": ["TA"], "visual_anchors": ["短发"],
                "reference_images": [], "usage_count": 2,
                "last_used": _now_iso(), "projects": ["测试项目"],
            },
            {
                "id": "char_test2", "name": "测试角色B",
                "role": "supporting", "gender": "male",
                "dna": {"identity": "另一个测试身份"},
                "reference_images": [], "usage_count": 1,
                "projects": ["测试项目"],
            },
        ]
        for c in sample_chars:
            cdp.add_character(c)
        print("[OK] add_character (内嵌示例)")

        cdp.add_location({
            "id": "loc_test1", "name": "测试场景",
            "category": "interior", "lighting": "暖色调",
            "reference_images": [], "usage_count": 1,
            "projects": ["测试项目"],
        })
        cdp.add_item({
            "id": "item_test1", "name": "测试道具",
            "category": "key", "narrative_weight": "high",
            "reference_images": [], "usage_count": 0,
            "projects": ["测试项目"],
        })
        print("[OK] add_location / add_item")

    # 4. CRUD 查询
    print("\n--- 列表查询 ---")
    chars = cdp.list_characters()
    print(f"[OK] list_characters → {len(chars)} 个")
    for c in chars[:3]:
        print(f"    {c.get('id', c.get('character_id'))} | {c.get('name', c.get('character_name'))} | usage={c.get('usage_count', 0)}")

    locs = cdp.list_locations()
    print(f"[OK] list_locations → {len(locs)} 个")

    items = cdp.list_items()
    print(f"[OK] list_items → {len(items)} 个")

    # 5. find_character
    found = cdp.find_character("谭斌")
    print(f"\n[OK] find_character('谭斌') → {found['id'] if found else 'None'}")

    # 6. record_usage
    cdp.record_usage("character", "char_01", "格子间女人", episode=1, shot_id="S01")
    cdp.record_usage("character", "char_01", "格子间女人", episode=1, shot_id="S02")
    cdp.record_usage("location", "loc_01", "格子间女人", episode=1, shot_id="S01")
    print("[OK] record_usage x3")

    char_01 = cdp.get_character("char_01")
    print(f"[OK] get_character('char_01') → usage_count={char_01.get('usage_count', '?')}")

    # 7. update
    cdp.update_character("char_01", {"personality": "理性冷静+自嘲幽默"})
    print("[OK] update_character")

    # 8. 统计
    stats = cdp.get_stats()
    print(f"\n[OK] get_stats → "
          f"chars={stats['total_characters']}, "
          f"locs={stats['total_locations']}, "
          f"items={stats['total_items']}, "
          f"logs={stats['total_usage_log']}")
    if stats["top_characters"]:
        top = stats["top_characters"][0]
        print(f"    Top角色: {top.get('name')} (usage={top.get('usage_count')})")
    if stats["recently_used"]:
        print(f"    最近使用: {stats['recently_used'][0]}")

    # 9. 导出
    export_path = db_path.replace(".db", "_export.json")
    ok = cdp.export_to_json(export_path, project="格子间女人")
    print(f"\n[OK] export_to_json → {'成功' if ok else '失败'} ({export_path})")

    # 10. 项目列表
    projects = cdp.list_projects()
    print(f"[OK] list_projects → {[p['project_name'] for p in projects]}")

    # 11. delete（测试删除测试数据）
    cdp.delete_character("char_test1")
    cdp.delete_location("loc_test1")
    cdp.delete_item("item_test1")
    print("[OK] delete_character / location / item")

    cdp.close()
    print("\n" + "=" * 60)
    print("自测完成")
    print("=" * 60)
