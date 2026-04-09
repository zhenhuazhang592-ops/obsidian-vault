#!/usr/bin/env python3
"""
conversation_context.py — huage888 多 Agent 会话上下文管理器（M3-3）

对标 Toonflow t_chatHistory 行为，升级点：
- 桥接 ConversationManager（文件层）+ TaskDB（数据库层）
- 多 Agent 上下文注入：同一 episode 跨 Agent 共享上下文
- Session 链路追踪：OutlineAgent → StoryboardAgent → VideoAgent
- 与 qwen_pipeline 深度集成：自动追加对话历史

用法：
  from conversation_context import ConversationContext

  ctx = ConversationContext()

  # 开启 episode 会话（跨 Agent 共享）
  ctx.begin_episode_session("漠玫传", "S01E01")

  # 追加 Agent 对话（自动写 DB + 写文件）
  ctx.append("outline", "assistant", "以下是结构化大纲...")
  ctx.append("storyboard", "user", "请基于大纲生成分镜...")

  # 构建注入到 qwen_pipeline 的上下文
  injected = ctx.build_injected_context(
      agent="storyboard",
      include_agents=["outline", "storyboard"],
      max_entries=20,
  )

  # Session 链路追溯
  chain = ctx.get_session_chain("storyboard")
"""

import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from conversation_manager import ConversationManager, ConversationEntry
from task_db import TaskDB


# ─────────────────────────────────────────────────────────────────────────────
# Agent 上下文注入顺序（Pipeline 依赖）
# ─────────────────────────────────────────────────────────────────────────────

# 先行的 Agent 应该先注入上下文（越近的越重要）
AGENT_DEPENDENCIES = {
    "outline":        [],
    "storyline":      [],
    "script":         ["outline"],
    "storyboard":    ["outline", "script"],
    "asset":          ["outline"],
    "video":          ["storyboard"],
    "director":       [],
    "art-designer":   ["director"],
    "prop-designer":  ["director"],
    "script-review":  ["script"],
    "art-review":     ["art-designer", "prop-designer"],
    "storyboard-review": ["storyboard"],
}

AGENT_LABELS = {
    "outline":        "大纲师",
    "storyline":      "故事线师",
    "script":         "剧本师",
    "storyboard":    "分镜师",
    "asset":         "资产师",
    "video":         "视频师",
    "director":      "导演",
    "art-designer":  "美术设计师",
    "prop-designer": "道具设计师",
    "script-review": "剧本审核",
    "art-review":    "资产审核",
    "storyboard-review": "分镜审核",
}


# ─────────────────────────────────────────────────────────────────────────────
# ConversationContext
# ─────────────────────────────────────────────────────────────────────────────

class ConversationContext:
    """
    多 Agent 会话上下文管理器

    特性：
    - 双写：ConversationManager（文件）+ TaskDB.chat_history（DB）
    - episode 级 session 链路：跨 Agent 共享同一个 episode session
    - 自动上下文注入：build_injected_context() 生成可注入 qwen_pipeline 的字符串
    - Session 链追溯：get_session_chain() 查看多 Agent 调用链路
    """

    def __init__(self, db: Optional[TaskDB] = None, conv_mgr: Optional[ConversationManager] = None):
        self._db = db or TaskDB()
        self._conv = conv_mgr or ConversationManager()
        # 当前活跃的 episode session
        self._active_episode: Optional[str] = None
        self._active_project: Optional[str] = None
        # agent -> session_id 映射（同一 episode 内各 Agent 的 session）
        self._agent_sessions: dict[str, str] = {}

    # ─── Episode 会话管理 ────────────────────────────────────────────────────

    def begin_episode_session(
        self,
        project_name: str,
        episode: str,
        project_id: int | None = None,
    ) -> str:
        """
        开始一个 episode 会话（在 DB 中查找或创建 project_id）。

        返回 episode_session_id（用于跨 Agent 追踪）。
        """
        if project_id is None:
            proj = self._db.get_project(project_name)
            if not proj:
                proj_id = self._db.upsert_project(name=project_name)
            else:
                proj_id = proj.id
        else:
            proj_id = project_id

        self._active_project = project_name
        self._active_episode = episode
        self._agent_sessions = {}

        # 创建该 episode 的主 session（在 DB chat_history 中记录）
        self._db.append_chat(
            project_id=proj_id,
            agent_type="__episode__",
            role="system",
            content=json.dumps({
                "event": "episode_session_start",
                "project": project_name,
                "episode": episode,
            }, ensure_ascii=False),
        )

        return f"ep_{episode}_{proj_id}"

    def get_episode_session(self) -> tuple[str, str] | tuple[None, None]:
        """返回当前活跃的 (project_name, episode)"""
        return self._active_project, self._active_episode

    # ─── Agent Session 管理 ───────────────────────────────────────────────────

    def get_or_create_agent_session(
        self,
        agent: str,
        project_name: str | None = None,
        episode: str | None = None,
    ) -> str:
        """
        获取或创建指定 Agent 的 session_id。

        优先使用当前活跃 episode 的 session。
        """
        if agent in self._agent_sessions:
            return self._agent_sessions[agent]

        project = project_name or self._active_project
        ep = episode or self._active_episode

        if not project or not ep:
            # 无活跃 episode，创建独立 session
            sid = self._conv.new_session(agent)
            return sid

        # 按 project_name 查找 project_id
        proj = self._db.get_project(project)
        if proj:
            # 在 chat_history 中查找该 agent + episode 的最新 session
            history = self._db.get_chat_history(
                project_id=proj.id,
                agent_type=agent,
                limit=100,
            )
            # 找包含 episode 的记录
            for h in reversed(history):
                content = h.get("content", "")
                if ep in content:
                    sid = h.get("session_id") or self._conv.new_session(agent)
                    self._agent_sessions[agent] = sid
                    return sid

        sid = self._conv.new_session(agent)
        self._agent_sessions[agent] = sid
        return sid

    # ─── 对话追加（双写） ────────────────────────────────────────────────────

    def append(
        self,
        agent: str,
        role: str,
        content: str,
        project_name: str | None = None,
        episode: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """
        追加一条对话（双写：文件 + DB）。

        Args:
            agent:        Agent 类型（outline / storyboard / ...）
            role:         user / assistant / system
            content:      对话内容
            project_name: 项目名（用于 DB 记录）
            episode:      集数（用于 DB 记录）
            metadata:     额外元数据（如 tool_name, token_count 等）
        """
        # 1. 文件层（ConversationManager）
        sid = self.get_or_create_agent_session(agent, project_name, episode)
        self._conv.append(agent, sid, role, content)

        # 2. DB 层（TaskDB chat_history）
        project = project_name or self._active_project
        ep = episode or self._active_episode
        if project:
            proj = self._db.get_project(project)
            if proj:
                extra = json.dumps(metadata, ensure_ascii=False) if metadata else ""
                self._db.append_chat(
                    project_id=proj.id,
                    agent_type=agent,
                    role=role,
                    content=content + (f"\n[meta] {extra}" if extra else ""),
                    session_id=sid,
                )

    # ─── 上下文构建 ──────────────────────────────────────────────────────────

    def build_injected_context(
        self,
        agent: str,
        include_agents: list[str] | None = None,
        max_entries: int = 20,
        project_name: str | None = None,
        episode: str | None = None,
        include_outputs: bool = True,
    ) -> str:
        """
        构建可注入 qwen_pipeline 的多 Agent 上下文字符串。

        格式：
        <多Agent上下文>
        ## 先行Agent上下文: [Agent名]
        [对话历史片段]
        ## 当前Agent: [Agent名]
        [当前Agent对话历史]
        </多Agent上下文>

        include_outputs: 是否在上下文中包含该 episode 的输出文件路径摘要
        """
        project = project_name or self._active_project
        ep = episode or self._active_episode

        # 确定要包含的 Agent（默认：依赖链 + 当前 agent）
        if include_agents is None:
            deps = AGENT_DEPENDENCIES.get(agent, [])
            include_agents = deps + [agent]

        parts = ["<多Agent上下文>"]

        # 添加先行 Agent 的对话
        for a in include_agents:
            if a == agent:
                continue  # 当前 agent 单独处理
            label = AGENT_LABELS.get(a, a)

            # 从文件层读取
            sid = self._agent_sessions.get(a) or self._conv.list_sessions(a)
            session_id = sid[0] if isinstance(sid, list) and sid else None
            if session_id:
                entries = self._conv.get_session(a, session_id)
                if entries:
                    parts.append(f"\n## 先行Agent: {label} ({a})")
                    for e in entries[-max_entries:]:
                        truncated = e.content[:800]  # 截断
                        parts.append(f"[{e.role}]: {truncated}")

        # 添加当前 Agent 的对话
        label = AGENT_LABELS.get(agent, agent)
        current_sid = self._agent_sessions.get(agent)
        if current_sid:
            entries = self._conv.get_session(agent, current_sid)
            if entries:
                parts.append(f"\n## 当前Agent: {label} ({agent})")
                for e in entries[-max_entries:]:
                    truncated = e.content[:800]
                    parts.append(f"[{e.role}]: {truncated}")

        # 添加输出文件路径摘要
        if include_outputs and project and ep:
            proj = self._db.get_project(project)
            if proj:
                parts.append(f"\n## 输出文件摘要")
                parts.append(f"项目: {project} | 集数: {ep}")

                # 大纲
                ep_num = self._parse_episode_number(ep)
                outline = self._db.get_outline(proj.id, ep_num)
                if outline:
                    parts.append(f"大纲: 已生成 (outline_id={outline['id']})")

                # 分镜
                scripts = self._db.get_scripts(proj.id)
                if scripts:
                    parts.append(f"剧本: {len(scripts)} 个")

        parts.append("</多Agent上下文>\n")
        return "\n".join(parts)

    def build_summary_context(
        self,
        project_name: str,
        episode: str,
        agents: list[str] | None = None,
        max_entries: int = 5,
    ) -> str:
        """
        轻量摘要上下文（仅最后 N 条），用于快速回顾。
        """
        agents = agents or list(AGENT_LABELS.keys())
        parts = ["<会话摘要>"]

        proj = self._db.get_project(project_name)
        if not proj:
            return ""

        for a in agents:
            label = AGENT_LABELS.get(a, a)
            history = self._db.get_chat_history(
                project_id=proj.id,
                agent_type=a,
                limit=max_entries,
            )
            if history:
                parts.append(f"\n## {label} ({a}) 最后 {max_entries} 条：")
                for h in reversed(history[-max_entries:]):
                    truncated = h.get("content", "")[:300]
                    parts.append(f"[{h.get('role','')}]: {truncated}")

        parts.append("</会话摘要>\n")
        return "\n".join(parts)

    # ─── Session 链追溯 ───────────────────────────────────────────────────────

    def get_session_chain(
        self,
        agent: str,
        project_name: str | None = None,
        episode: str | None = None,
    ) -> list[dict]:
        """
        获取指定 Agent 的 session 调用链（跨 Agent 依赖追溯）。

        返回格式：
        [{"agent": "...", "session_id": "...", "entries_count": N,
          "first_ts": "...", "last_ts": "..."}]
        """
        project = project_name or self._active_project
        ep = episode or self._active_episode

        chain = []

        if not project:
            return chain

        proj = self._db.get_project(project)
        if not proj:
            return chain

        # 先获取当前 agent 的 sessions
        history = self._db.get_chat_history(
            project_id=proj.id,
            agent_type=agent,
            limit=1000,
        )
        session_ids = list(dict.fromkeys(h.get("session_id") for h in history if h.get("session_id")))

        for sid in session_ids:
            session_entries = [h for h in history if h.get("session_id") == sid]
            if not session_entries:
                continue
            ts_list = [h.get("created_at", "") for h in session_entries]
            chain.append({
                "agent": agent,
                "session_id": sid,
                "entries_count": len(session_entries),
                "first_ts": min(ts_list) if ts_list else "",
                "last_ts": max(ts_list) if ts_list else "",
                "role_counts": {
                    "user": sum(1 for h in session_entries if h.get("role") == "user"),
                    "assistant": sum(1 for h in session_entries if h.get("role") == "assistant"),
                    "system": sum(1 for h in session_entries if h.get("role") == "system"),
                },
            })

        # 递归获取依赖 Agent
        deps = AGENT_DEPENDENCIES.get(agent, [])
        for dep in deps:
            dep_chain = self.get_session_chain(dep, project, ep)
            chain.extend(dep_chain)

        return chain

    def print_session_chain(
        self,
        agent: str,
        project_name: str | None = None,
        episode: str | None = None,
    ) -> None:
        """打印 Session 调用链（供 CLI 使用）"""
        chain = self.get_session_chain(agent, project_name, episode)
        if not chain:
            print(f"  无 Session 记录")
            return

        # 按时间顺序（first_ts）
        chain.sort(key=lambda x: x["first_ts"] or "")

        seen = set()
        for item in chain:
            key = (item["agent"], item["session_id"])
            if key in seen:
                continue
            seen.add(key)
            label = AGENT_LABELS.get(item["agent"], item["agent"])
            print(f"  [{item['agent']}] {label}")
            print(f"    session: {item['session_id']}")
            print(f"    条目数: {item['entries_count']} "
                  f"(U={item['role_counts']['user']} "
                  f"A={item['role_counts']['assistant']} "
                  f"S={item['role_counts']['system']})")
            print(f"    时间: {item['first_ts'][:19] if item['first_ts'] else '?'} "
                  f"~ {item['last_ts'][:19] if item['last_ts'] else '?'}")


# ─────────────────────────────────────────────────────────────────────────────
# 工具
# ─────────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_episode_number(episode: str) -> int:
        import re
        m = re.search(r"E(\d+)", episode, re.IGNORECASE)
        return int(m.group(1)) if m else 1


# ─────────────────────────────────────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="huage888 多Agent会话上下文")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_begin = sub.add_parser("begin", help="开启 episode 会话")
    p_begin.add_argument("--project", required=True)
    p_begin.add_argument("--episode", required=True)

    p_append = sub.add_parser("append", help="追加对话")
    p_append.add_argument("--agent", required=True)
    p_append.add_argument("--role", required=True, choices=["user", "assistant", "system"])
    p_append.add_argument("--content", required=True)
    p_append.add_argument("--project")
    p_append.add_argument("--episode")

    p_context = sub.add_parser("context", help="构建注入上下文")
    p_context.add_argument("--agent", required=True)
    p_context.add_argument("--project", help="默认使用当前活跃项目")
    p_context.add_argument("--episode", help="默认使用当前活跃集数")
    p_context.add_argument("--agents", help="逗号分隔要包含的 Agent")
    p_context.add_argument("--max", type=int, default=20)

    p_chain = sub.add_parser("chain", help="查看 Session 调用链")
    p_chain.add_argument("--agent", required=True)
    p_chain.add_argument("--project")
    p_chain.add_argument("--episode")

    p_summary = sub.add_parser("summary", help="轻量摘要上下文")
    p_summary.add_argument("--project", required=True)
    p_summary.add_argument("--episode", required=True)
    p_summary.add_argument("--agents", help="逗号分隔 Agent，默认全部")
    p_summary.add_argument("--max", type=int, default=5)

    args = parser.parse_args()
    ctx = ConversationContext()

    if args.cmd == "begin":
        sid = ctx.begin_episode_session(args.project, args.episode)
        print(f"Episode 会话开启: {sid}")

    elif args.cmd == "append":
        ctx.append(args.agent, args.role, args.content, args.project, args.episode)
        print("OK")

    elif args.cmd == "context":
        agents = args.agents.split(",") if args.agents else None
        result = ctx.build_injected_context(
            agent=args.agent,
            include_agents=agents,
            max_entries=args.max,
            project_name=args.project,
            episode=args.episode,
        )
        print(result or "(无上下文)")

    elif args.cmd == "chain":
        ctx.print_session_chain(args.agent, args.project, args.episode)

    elif args.cmd == "summary":
        agents = args.agents.split(",") if args.agents else None
        result = ctx.build_summary_context(
            project_name=args.project,
            episode=args.episode,
            agents=agents,
            max_entries=args.max,
        )
        print(result or "(无摘要)")
