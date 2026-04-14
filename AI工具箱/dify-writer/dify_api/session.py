"""
Dify 会话管理
管理 Chatflow 会话状态
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Literal
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SessionState:
    """会话状态"""
    session_id: str
    conversation_id: str
    user_id: str
    chatflow_id: str
    status: Literal["running", "waiting_hitl", "completed", "failed"]
    current_node: str
    hitl_type: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    context: dict = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


class SessionManager:
    """
    Dify Chatflow 会话管理器

    职责：
    - 创建/存储会话状态
    - 管理 HITL 等待状态
    - 持久化到磁盘
    """

    def __init__(self, storage_dir: Path = Path("~/.cache/dify-writer/sessions")):
        self.storage_dir = storage_dir.expanduser()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, SessionState] = {}
        self._lock = asyncio.Lock()

    def _session_path(self, session_id: str) -> Path:
        """会话文件路径"""
        return self.storage_dir / f"{session_id}.json"

    async def create_session(
        self,
        session_id: str,
        conversation_id: str,
        user_id: str,
        chatflow_id: str,
        initial_context: Optional[dict] = None,
    ) -> SessionState:
        """创建新会话"""
        async with self._lock:
            state = SessionState(
                session_id=session_id,
                conversation_id=conversation_id,
                user_id=user_id,
                chatflow_id=chatflow_id,
                status="running",
                current_node="intent_parsing",
                context=initial_context or {},
            )
            self._sessions[session_id] = state
            await self._persist(state)
            logger.info(f"[Session] Created: {session_id}")
            return state

    async def get_session(self, session_id: str) -> Optional[SessionState]:
        """获取会话状态"""
        async with self._lock:
            # 先从内存查找
            if session_id in self._sessions:
                return self._sessions[session_id]

            # 从磁盘加载
            path = self._session_path(session_id)
            if path.exists():
                try:
                    data = json.loads(path.read_text())
                    state = SessionState(**data)
                    self._sessions[session_id] = state
                    return state
                except Exception as e:
                    logger.warning(f"[Session] Failed to load {session_id}: {e}")
            return None

    async def update_session(
        self,
        session_id: str,
        status: Optional[str] = None,
        current_node: Optional[str] = None,
        hitl_type: Optional[str] = None,
        context_updates: Optional[dict] = None,
    ) -> Optional[SessionState]:
        """更新会话状态"""
        async with self._lock:
            state = await self.get_session(session_id)
            if not state:
                return None

            if status is not None:
                state.status = status
            if current_node is not None:
                state.current_node = current_node
            if hitl_type is not None:
                state.hitl_type = hitl_type
            if context_updates:
                state.context.update(context_updates)

            state.updated_at = datetime.now().isoformat()
            await self._persist(state)
            return state

    async def set_hitl_waiting(
        self,
        session_id: str,
        hitl_type: str,
        current_node: str,
    ) -> Optional[SessionState]:
        """设置 HITL 等待状态"""
        return await self.update_session(
            session_id=session_id,
            status="waiting_hitl",
            current_node=current_node,
            hitl_type=hitl_type,
        )

    async def resume_from_hitl(
        self,
        session_id: str,
    ) -> Optional[SessionState]:
        """从 HITL 恢复"""
        return await self.update_session(
            session_id=session_id,
            status="running",
            hitl_type=None,
        )

    async def complete_session(self, session_id: str) -> Optional[SessionState]:
        """标记会话完成"""
        return await self.update_session(
            session_id=session_id,
            status="completed",
        )

    async def fail_session(self, session_id: str) -> Optional[SessionState]:
        """标记会话失败"""
        return await self.update_session(
            session_id=session_id,
            status="failed",
        )

    async def _persist(self, state: SessionState):
        """持久化到磁盘"""
        path = self._session_path(state.session_id)
        path.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2))

    async def list_sessions(self, user_id: Optional[str] = None) -> list[SessionState]:
        """列出所有会话"""
        sessions = []
        for path in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                state = SessionState(**data)
                if user_id is None or state.user_id == user_id:
                    sessions.append(state)
            except Exception:
                continue
        return sorted(sessions, key=lambda s: s.updated_at, reverse=True)

    async def delete_session(self, session_id: str):
        """删除会话"""
        async with self._lock:
            self._sessions.pop(session_id, None)
            path = self._session_path(session_id)
            if path.exists():
                path.unlink()
            logger.info(f"[Session] Deleted: {session_id}")
