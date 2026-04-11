# .claude/modules/session_store.py
"""会话持久化：SQLite sessions + messages 表 + FTS5 全文索引"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path.home() / ".claude" / "sessions.db"


class SessionStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self):
        """初始化数据库 schema"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                summary TEXT,
                token_count INTEGER DEFAULT 0,
                outcome TEXT DEFAULT 'unknown'
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_calls TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                content,
                content='messages',
                content_rowid='id'
            );

            CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
                INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
            END;
        """)
        conn.close()

    def begin_session(self, session_id: str) -> None:
        """标记新会话开始"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR IGNORE INTO sessions (session_id, started_at) VALUES (?, ?)",
            (session_id, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()

    def add_message(self, session_id: str, role: str, content: str,
                    tool_calls: Optional[list] = None) -> None:
        """写入单条消息"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """INSERT INTO messages (session_id, role, content, tool_calls, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, role, content, json.dumps(tool_calls) if tool_calls else None,
             datetime.now().isoformat())
        )
        conn.commit()
        conn.close()

    def end_session(self, session_id: str, summary: str,
                    token_count: int, outcome: str) -> None:
        """标记会话结束"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """UPDATE sessions SET ended_at=?, summary=?, token_count=?, outcome=?
               WHERE session_id=?""",
            (datetime.now().isoformat(), summary, token_count, outcome, session_id)
        )
        conn.commit()
        conn.close()

    def get_session(self, session_id: str) -> Optional[dict]:
        """获取会话元数据"""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row[0], "session_id": row[1], "started_at": row[2],
            "ended_at": row[3], "summary": row[4], "token_count": row[5], "outcome": row[6]
        }

    def get_session_messages(self, session_id: str) -> list[dict]:
        """获取会话所有消息"""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT role, content, tool_calls, created_at FROM messages WHERE session_id=? ORDER BY id",
            (session_id,)
        ).fetchall()
        conn.close()
        return [
            {"role": r[0], "content": r[1], "tool_calls": json.loads(r[2]) if r[2] else None, "created_at": r[3]}
            for r in rows
        ]

    def search_messages(self, query: str, limit: int = 50) -> list[dict]:
        """FTS5 搜索消息（snippets 不可用时降级）"""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute(
                """SELECT m.session_id, m.role, m.content, m.created_at,
                          snippets(messages_fts, 0, '>>>', '<<<', '...', 32) as snippet
                   FROM messages_fts
                   JOIN messages m ON messages_fts.rowid = m.id
                   WHERE messages_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (query, limit)
            ).fetchall()
            conn.close()
            return [
                {"session_id": r[0], "role": r[1], "content": r[2], "created_at": r[3], "snippet": r[4]}
                for r in rows
            ]
        except sqlite3.OperationalError:
            # snippets() 不可用时降级：直接返回匹配消息内容
            conn.close()
            return self._search_messages_fallback(query, limit)

    def _search_messages_fallback(self, query: str, limit: int) -> list[dict]:
        """FTS5 降级搜索（无 snippets）"""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            """SELECT m.session_id, m.role, m.content, m.created_at
               FROM messages m
               WHERE m.content LIKE ?
               ORDER BY m.id DESC
               LIMIT ?""",
            (f"%{query}%", limit)
        ).fetchall()
        conn.close()
        return [
            {"session_id": r[0], "role": r[1], "content": r[2], "created_at": r[3], "snippet": r[2][:200]}
            for r in rows
        ]

    def get_recent_sessions(self, limit: int = 10) -> list[dict]:
        """获取最近会话列表"""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            """SELECT session_id, started_at, ended_at, summary, outcome
               FROM sessions WHERE ended_at IS NOT NULL
               ORDER BY ended_at DESC LIMIT ?""",
            (limit,)
        ).fetchall()
        conn.close()
        return [
            {"session_id": r[0], "started_at": r[1], "ended_at": r[2], "summary": r[3], "outcome": r[4]}
            for r in rows
        ]