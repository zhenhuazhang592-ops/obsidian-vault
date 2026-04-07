#!/usr/bin/env python3
"""
conversation_manager.py — huage888 对话历史管理器

对应 Toonflow t_chatHistory 表的行为：
- 每个 Agent（outline / storyboard / director 等）独立存储对话
- 每个 session_id 是一段完整的对话上下文
- 支持父子 session 关联（Sub-Agent 嵌套时 child 继承 parent）

存储格式：.huage888/conversations/{agent}/{session_id}.jsonl
每行：{"role","content","timestamp","session_id","parent_session_id"}

用法：
  from conversation_manager import ConversationManager, ConversationEntry

  mgr = ConversationManager()

  # 新建 session
  session_id = mgr.new_session("outline")

  # 追加对话
  mgr.append("outline", session_id, "user", "请生成大纲...")
  mgr.append("outline", session_id, "assistant", "以下是结构化大纲...")

  # 读取历史
  entries = mgr.get_session("outline", session_id)

  # 构建 context 注入到 prompt
  ctx = mgr.build_context("outline", session_id, max_entries=10)

  # 按关键词搜索
  results = mgr.search("outline", "漠玫")
"""

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# 数据模型
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ConversationEntry:
    """单条对话记录"""
    role: str           # user / assistant / system
    content: str
    timestamp: str      # ISO format
    session_id: str
    parent_session_id: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ConversationEntry":
        return cls(
            role=d["role"],
            content=d["content"],
            timestamp=d["timestamp"],
            session_id=d["session_id"],
            parent_session_id=d.get("parent_session_id"),
        )


# ─────────────────────────────────────────────────────────────────────────────
# ConversationManager
# ─────────────────────────────────────────────────────────────────────────────

class ConversationManager:
    """
    对话历史管理器

    对外接口：
    - new_session(agent, parent_session_id=None) -> session_id
    - append(agent, session_id, role, content, parent_session_id=None)
    - get_session(agent, session_id) -> list[ConversationEntry]
    - get_recent(agent, limit=10) -> list[dict]
    - search(agent, keyword) -> list[dict]
    - build_context(agent, session_id, max_entries=10) -> str
    """

    DEFAULT_DIR = ".huage888/conversations"

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir or self.DEFAULT_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ─── 内部 ────────────────────────────────────────────────────────────────

    def _session_path(self, agent: str, session_id: str) -> Path:
        """会话文件路径：.huage888/conversations/{agent}/{session_id}.jsonl"""
        return self.base_dir / agent / f"{session_id}.jsonl"

    def _ensure_agent_dir(self, agent: str) -> Path:
        """确保 agent 目录存在"""
        d = self.base_dir / agent
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _now(self) -> str:
        return datetime.now().isoformat()

    # ─── 对外接口 ────────────────────────────────────────────────────────────

    def new_session(
        self,
        agent: str,
        parent_session_id: str | None = None,
    ) -> str:
        """
        创建新 session，返回 session_id。

        parent_session_id: 若指定，则此 session 是父 session 的子对话
                          （用于 Sub-Agent 嵌套时的上下文追溯）
        """
        sid = str(uuid.uuid4())[:8]
        self._ensure_agent_dir(agent)
        # 空文件占位（确保目录结构可见）
        self._session_path(agent, sid).touch()
        return sid

    def append(
        self,
        agent: str,
        session_id: str,
        role: str,
        content: str,
        parent_session_id: str | None = None,
    ) -> None:
        """
        追加一条对话记录到指定 session。

        role: "user" | "assistant" | "system"
        """
        if role not in ("user", "assistant", "system"):
            raise ValueError(f"Invalid role: {role!r} (must be user/assistant/system)")

        path = self._session_path(agent, session_id)
        self._ensure_agent_dir(agent)

        entry = ConversationEntry(
            role=role,
            content=content,
            timestamp=self._now(),
            session_id=session_id,
            parent_session_id=parent_session_id,
        )

        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    def get_session(
        self,
        agent: str,
        session_id: str,
    ) -> list[ConversationEntry]:
        """
        读取指定 session 的全部对话记录。
        """
        path = self._session_path(agent, session_id)
        if not path.exists():
            return []

        entries = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(ConversationEntry.from_dict(json.loads(line)))
                except json.JSONDecodeError:
                    continue
        return entries

    def get_recent(
        self,
        agent: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        读取最近 N 条对话（跨所有 session，按时间倒序）。
        """
        agent_dir = self.base_dir / agent
        if not agent_dir.exists():
            return []

        all_entries: list[tuple[str, dict]] = []  # (timestamp, entry_dict)

        for session_file in agent_dir.glob("*.jsonl"):
            with session_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        all_entries.append((d["timestamp"], d))
                    except (json.JSONDecodeError, KeyError):
                        continue

        # 按时间倒序，取最近 limit 条
        all_entries.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in all_entries[:limit]]

    def search(
        self,
        agent: str,
        keyword: str,
        limit: int = 50,
    ) -> list[dict]:
        """
        按关键词搜索对话记录（content 包含 keyword，大小写不敏感）。
        """
        agent_dir = self.base_dir / agent
        if not agent_dir.exists():
            return []

        results = []
        kw_lower = keyword.lower()

        for session_file in agent_dir.glob("*.jsonl"):
            with session_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        if kw_lower in d["content"].lower():
                            results.append(d)
                    except (json.JSONDecodeError, KeyError):
                        continue

        return results[:limit]

    def build_context(
        self,
        agent: str,
        session_id: str,
        max_entries: int = 10,
    ) -> str:
        """
        将历史对话构建为可注入 prompt 的字符串。

        格式：
        <对话历史>
        [user]: xxx
        [assistant]: xxx
        [user]: xxx
        </对话历史>

        max_entries=0 时返回空字符串（跳过历史注入）。
        """
        if max_entries <= 0:
            return ""

        entries = self.get_session(agent, session_id)
        if not entries:
            return ""

        # 保留最近 max_entries 条
        recent = entries[-max_entries:]

        lines = ["<对话历史>"]
        for e in recent:
            lines.append(f"[{e.role}]: {e.content[:500]}")  # 截断防 token 膨胀
        lines.append("</对话历史>\n")

        return "\n".join(lines)

    def list_sessions(self, agent: str) -> list[str]:
        """列出指定 agent 的所有 session_id（按修改时间倒序）"""
        agent_dir = self.base_dir / agent
        if not agent_dir.exists():
            return []
        files = sorted(
            agent_dir.glob("*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return [f.stem for f in files]

    def delete_session(self, agent: str, session_id: str) -> bool:
        """删除指定 session"""
        path = self._session_path(agent, session_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def count_entries(self, agent: str, session_id: str) -> int:
        """统计 session 中的对话条数"""
        path = self._session_path(agent, session_id)
        if not path.exists():
            return 0
        with path.open("r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())


# ─────────────────────────────────────────────────────────────────────────────
# CLI 入口（测试用）
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="对话历史管理器")
    sub = parser.add_subparsers(dest="cmd")

    p_new = sub.add_parser("new-session", help="创建新 session")
    p_new.add_argument("--agent", required=True)

    p_append = sub.add_parser("append", help="追加对话")
    p_append.add_argument("--agent", required=True)
    p_append.add_argument("--session", required=True)
    p_append.add_argument("--role", required=True, choices=["user", "assistant", "system"])
    p_append.add_argument("--content", required=True)

    p_history = sub.add_parser("history", help="查看历史")
    p_history.add_argument("--agent", required=True)
    p_history.add_argument("--session", required=True)

    p_context = sub.add_parser("context", help="构建 context")
    p_context.add_argument("--agent", required=True)
    p_context.add_argument("--session", required=True)
    p_context.add_argument("--max", type=int, default=10)

    p_search = sub.add_parser("search", help="搜索")
    p_search.add_argument("--agent", required=True)
    p_search.add_argument("--keyword", required=True)

    p_list = sub.add_parser("sessions", help="列出 session")
    p_list.add_argument("--agent", required=True)

    args = parser.parse_args()
    mgr = ConversationManager()

    if args.cmd == "new-session":
        sid = mgr.new_session(args.agent)
        print(f"session_id: {sid}")

    elif args.cmd == "append":
        mgr.append(args.agent, args.session, args.role, args.content)
        print("OK")

    elif args.cmd == "history":
        entries = mgr.get_session(args.agent, args.session)
        for e in entries:
            print(f"[{e.role}] {e.content[:200]}")

    elif args.cmd == "context":
        ctx = mgr.build_context(args.agent, args.session, args.max)
        print(ctx or "(无历史)")

    elif args.cmd == "search":
        results = mgr.search(args.agent, args.keyword)
        print(f"找到 {len(results)} 条:")
        for r in results:
            print(f"  [{r['session_id']}] {r['content'][:100]}")

    elif args.cmd == "sessions":
        sessions = mgr.list_sessions(args.agent)
        print(f"共 {len(sessions)} 个 session:")
        for s in sessions[:20]:
            print(f"  {s}")

    else:
        parser.print_help()
