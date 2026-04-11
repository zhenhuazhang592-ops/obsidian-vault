# .claude/modules/session_search.py
"""FTS5 搜索 + LLM 摘要"""

from dataclasses import dataclass
from typing import Optional
from .session_store import SessionStore


@dataclass
class SessionHit:
    session_id: str
    summary: Optional[str]
    started_at: str
    outcome: str
    relevance_snippets: list[str]


class SessionSearch:
    def __init__(self, store: Optional[SessionStore] = None):
        self.store = store or SessionStore()

    def search(self, query: str, limit_sessions: int = 5) -> list[SessionHit]:
        """
        FTS5 搜索 + 按会话分组返回。
        LLM 摘要逻辑由调用方注入（避免直接依赖 LLM SDK）。
        """
        # 1. FTS5 搜索
        raw_hits = self.store.search_messages(query, limit=50)
        if not raw_hits:
            return []

        # 2. 按 session_id 分组
        session_ids = list(dict.fromkeys(h["session_id"] for h in raw_hits))[:limit_sessions]

        results = []
        for sid in session_ids:
            session_meta = self.store.get_session(sid)
            session_messages = self.store.get_session_messages(sid)

            # 取相关片段
            snippets = [h["snippet"] for h in raw_hits if h["session_id"] == sid]

            # 构建上下文片段（供 LLM 摘要）
            context = self._build_context(sid, session_messages, snippets)

            results.append(SessionHit(
                session_id=sid,
                summary=session_meta.get("summary") if session_meta else None,
                started_at=session_meta.get("started_at", "") if session_meta else "",
                outcome=session_meta.get("outcome", "unknown") if session_meta else "unknown",
                relevance_snippets=context
            ))

        return results

    def _build_context(self, session_id: str,
                       messages: list[dict], snippets: list[str]) -> list[str]:
        """从消息中构建相关上下文片段"""
        context = []
        for msg in messages[-10:]:  # 最近 10 条消息
            role = msg["role"]
            content = msg["content"][:500]  # 截断
            context.append(f"[{role.upper()}] {content}")
        return context

    def format_for_display(self, hits: list[SessionHit]) -> str:
        """格式化搜索结果为 markdown"""
        if not hits:
            return "**没有找到相关会话**"

        lines = []
        for i, hit in enumerate(hits, 1):
            lines.append(f"### 会话 {i}（{hit.started_at[:10]}）")
            if hit.summary:
                lines.append(f"**摘要：** {hit.summary}")
            lines.append(f"**结果：** {hit.outcome}")
            lines.append("")
            for snippet in hit.relevance_snippets[:3]:
                lines.append(f"> {snippet}")
            lines.append("")
        return "\n".join(lines)