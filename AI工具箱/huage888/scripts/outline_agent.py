#!/usr/bin/env python3
"""
outline_agent.py — 大纲故事线 Agent（Python 实现）

对标 Toonflow OutlineScript：
- 主协调 Agent：接收用户任务，协调 SubAgent（AI1/AI2/director）
- 工具集：getChapter / getStoryline / saveStoryline / getOutline / saveOutline / updateOutline / generateAssets
- 事件流：EventEmitter（流式输出到前端/控制台）
- 数据层：TaskDB（novels / storylines / outlines / assets）

SubAgent 委托链：
  用户 → OutlineAgent（主）→ AI1（故事师）→ saveStoryline
                          → AI2（大纲师）→ saveOutline
                          → director（导演）→ updateOutline

用法：
  python3 scripts/outline_agent.py --project-id 1 --task "生成漠玫传第1集大纲"

  # Python API
  from scripts.outline_agent import OutlineAgent
  agent = OutlineAgent(project_id=1)
  result = agent.call("生成第1集大纲")
"""

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.task_db import TaskDB
from config.prompts_registry import PromptsRegistry

BASE_DIR = Path(__file__).parent.parent


# ─────────────────────────────────────────────────────────────────────────────
# 事件发射器（纯 Python 实现，兼容 Toonflow EventEmitter 模式）
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AgentEvent:
    """事件载荷"""
    event: str
    data: dict = field(default_factory=dict)


class SimpleEventEmitter:
    """
    简化版 EventEmitter。

    事件类型：
      - data:          流式文本片段
      - tool_call:      工具调用通知
      - tool_result:   工具执行结果
      - sub_agent:     SubAgent 开始/结束
      - transfer:      切换 SubAgent
      - refresh:        数据刷新（storyline/outline/assets）
      - response:       最终响应完成
      - error:         错误
    """

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}

    def on(self, event: str, handler: Callable[[AgentEvent], None]) -> "SimpleEventEmitter":
        self._handlers.setdefault(event, []).append(handler)
        return self

    def off(self, event: str, handler: Callable) -> None:
        if event in self._handlers:
            self._handlers[event] = [h for h in self._handlers[event] if h != handler]

    def emit(self, event: str, data: dict = None) -> None:
        payload = AgentEvent(event=event, data=data or {})
        for handler in self._handlers.get(event, []):
            try:
                handler(payload)
            except Exception as e:
                print(f"[Emitter] Handler error for {event}: {e}", file=sys.stderr)
        # 广播到所有 handlers（通配符 *）
        for handler in self._handlers.get("*", []):
            try:
                handler(payload)
            except Exception:
                pass

    def on_data(self, handler: Callable[[str], None]) -> "SimpleEventEmitter":
        """便捷方法：监听流式文本"""
        def wrapper(evt: AgentEvent):
            if evt.data.get("text"):
                handler(evt.data["text"])
        return self.on("data", wrapper)

    def on_tool_call(self, handler: Callable[[str, dict], None]) -> "SimpleEventEmitter":
        """便捷方法：监听工具调用"""
        def wrapper(evt: AgentEvent):
            handler(evt.data.get("name", ""), evt.data.get("args", {}))
        return self.on("tool_call", wrapper)


# ─────────────────────────────────────────────────────────────────────────────
# 工具定义
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ToolResult:
    """工具执行结果"""
    name: str
    ok: bool
    result: str
    error: str = ""


class OutlineToolSet:
    """
    OutlineAgent 的工具集。

    工具方法签名：
      def tool_xxx(args: dict) -> ToolResult
    """

    def __init__(self, project_id: int, db: TaskDB, emitter: SimpleEventEmitter):
        self.project_id = project_id
        self._db = db
        self._emitter = emitter

    def _emit_tool(self, name: str, args: dict) -> None:
        self._emitter.emit("tool_call", {"name": name, "args": args})

    def _emit_result(self, name: str, result: str, ok: bool = True) -> None:
        self._emitter.emit("tool_result", {"name": name, "result": result, "ok": ok})

    # ── 章节工具 ───────────────────────────────────────────────────────

    def get_chapter(self, args: dict) -> ToolResult:
        """获取小说章节原文"""
        self._emit_tool("getChapter", args)
        chapter_numbers = args.get("chapterNumbers", [])
        if not chapter_numbers:
            return ToolResult(name="getChapter", ok=False, result="", error="chapterNumbers 不能为空")

        chapters = self._db.get_novel_chapters(self.project_id, chapter_numbers)
        if not chapters:
            return ToolResult(name="getChapter", ok=False, result="无章节数据", error="")

        lines = []
        for ch in sorted(chapters, key=lambda x: x.get("chapter_index", 0)):
            lines.append(f"\n【第{ch.get('chapter_index')}章 {ch.get('chapter', '')}】\n")
            lines.append(ch.get("chapter_data", ""))
            lines.append("\n\n---\n")

        result = "".join(lines)
        self._emit_result("getChapter", result[:200])
        return ToolResult(name="getChapter", ok=True, result=result)

    # ── 故事线工具 ────────────────────────────────────────────────────

    def get_storyline(self, args: dict) -> ToolResult:
        """获取故事线"""
        self._emit_tool("getStoryline", args)
        sl = self._db.get_storyline(self.project_id)
        result = sl.get("content", "当前项目暂无故事线") if sl else "当前项目暂无故事线"
        self._emit_result("getStoryline", result[:200])
        return ToolResult(name="getStoryline", ok=True, result=result)

    def save_storyline(self, args: dict) -> ToolResult:
        """保存故事线"""
        self._emit_tool("saveStoryline", args)
        content = args.get("content", "")
        if not content:
            return ToolResult(name="saveStoryline", ok=False, result="", error="content 不能为空")

        self._db.save_storyline(self.project_id, content)
        self._emitter.emit("refresh", {"type": "storyline"})
        msg = f"故事线保存成功（{len(content)} 字）"
        self._emit_result("saveStoryline", msg)
        return ToolResult(name="saveStoryline", ok=True, result=msg)

    def delete_storyline(self, args: dict) -> ToolResult:
        """删除故事线"""
        self._emit_tool("deleteStoryline", args)
        ok = self._db.delete_storyline(self.project_id)
        self._emitter.emit("refresh", {"type": "storyline"})
        msg = "故事线删除成功" if ok else "当前项目没有故事线"
        self._emit_result("deleteStoryline", msg)
        return ToolResult(name="deleteStoryline", ok=ok, result=msg)

    # ── 大纲工具 ──────────────────────────────────────────────────────

    def get_outline(self, args: dict) -> ToolResult:
        """获取大纲"""
        self._emit_tool("getOutline", args)
        simplified = args.get("simplified", False)
        outlines = self._db.get_outlines(self.project_id)
        if not outlines:
            return ToolResult(name="getOutline", ok=True, result="当前项目暂无大纲")

        if simplified:
            lines = [f"第 {json.loads(o.get('data','{}')).get('episodeIndex', o.get('episode'))} 集"
                     for o in outlines]
            result = f"项目大纲（共 {len(outlines)} 集）:\n" + "\n".join(lines)
        else:
            parts = []
            for o in outlines:
                data = json.loads(o.get("data", "{}"))
                ep_idx = data.get("episodeIndex", o.get("episode", "?"))
                title = data.get("title", "")
                outline_text = data.get("outline", "")
                key_events = data.get("keyEvents", [])
                chars = [c.get("name") for c in data.get("characters", [])]
                scenes = [s.get("name") for s in data.get("scenes", [])]
                parts.append(
                    f"第 {ep_idx} 集：{title}\n"
                    f"剧情主干：{outline_text}\n"
                    f"起承转合：{' / '.join(key_events)}\n"
                    f"角色：{', '.join(chars)}\n"
                    f"场景：{', '.join(scenes)}"
                )
            result = f"项目大纲（共 {len(outlines)} 集）\n\n" + "\n\n".join(parts)

        self._emit_result("getOutline", result[:300])
        return ToolResult(name="getOutline", ok=True, result=result)

    def save_outline(self, args: dict) -> ToolResult:
        """保存大纲"""
        self._emit_tool("saveOutline", args)
        episodes = args.get("episodes", [])
        if not episodes:
            return ToolResult(name="saveOutline", ok=False, result="", error="episodes 不能为空")

        overwrite = args.get("overwrite", True)
        if overwrite:
            self._db.delete_outlines(self.project_id)

        count = 0
        for i, ep in enumerate(episodes):
            episode_num = i + 1
            self._db.save_outline(self.project_id, episode_num, ep)
            # 创建空剧本记录
            from scripts.task_db import TaskDB as _TDB
            _db2 = _TDB()
            # 获取刚插入的 outline_id
            outlines = _db2.get_outlines(self.project_id)
            if outlines:
                latest = max(outlines, key=lambda x: x.get("id", 0))
                _db2.save_script(self.project_id, f"第{episode_num}集", "", outline_id=latest.get("id"))
            count += 1

        self._emitter.emit("refresh", {"type": "outline"})
        msg = f"大纲保存成功：{count} 集"
        self._emit_result("saveOutline", msg)
        return ToolResult(name="saveOutline", ok=True, result=msg)

    def update_outline(self, args: dict) -> ToolResult:
        """更新单集大纲"""
        self._emit_tool("updateOutline", args)
        outline_id = args.get("id")
        data = args.get("data", {})
        if not outline_id or not data:
            return ToolResult(name="updateOutline", ok=False, result="", error="id 和 data 不能为空")

        outlines = self._db.get_outlines(self.project_id)
        for o in outlines:
            if o.get("id") == outline_id:
                self._db.save_outline(self.project_id, o.get("episode"), data)
                self._emitter.emit("refresh", {"type": "outline"})
                self._emit_result("updateOutline", f"大纲 ID {outline_id} 更新成功")
                return ToolResult(name="updateOutline", ok=True, result=f"大纲 ID {outline_id} 更新成功")

        return ToolResult(name="updateOutline", ok=False, result="", error=f"未找到大纲 ID: {outline_id}")

    def delete_outline(self, args: dict) -> ToolResult:
        """删除大纲"""
        self._emit_tool("deleteOutline", args)
        ids = args.get("ids", [])
        if not ids:
            return ToolResult(name="deleteOutline", ok=False, result="", error="ids 不能为空")
        self._db.delete_outlines(self.project_id)
        self._emitter.emit("refresh", {"type": "outline"})
        msg = f"大纲删除成功（{len(ids)} 集）"
        self._emit_result("deleteOutline", msg)
        return ToolResult(name="deleteOutline", ok=True, result=msg)

    # ── 资产工具 ──────────────────────────────────────────────────────

    def generate_assets(self, args: dict) -> ToolResult:
        """从大纲生成资产注册"""
        self._emit_tool("generateAssets", args)
        outlines = self._db.get_outlines(self.project_id)
        if not outlines:
            return ToolResult(name="generateAssets", ok=False, result="当前项目没有大纲，无法生成资产")

        inserted = updated = skipped = 0
        for o in outlines:
            data = json.loads(o.get("data", "{}"))
            for char in data.get("characters", []):
                r = self._db.upsert_asset(
                    project_id=self.project_id,
                    asset_type="character",
                    name=char.get("name", ""),
                    intro=char.get("description", ""),
                    prompt=char.get("description", ""),
                )
                if r == "inserted":
                    inserted += 1
                elif r == "updated":
                    updated += 1
                else:
                    skipped += 1

            for scene in data.get("scenes", []):
                r = self._db.upsert_asset(
                    project_id=self.project_id,
                    asset_type="scene",
                    name=scene.get("name", ""),
                    intro=scene.get("description", ""),
                    prompt=scene.get("description", ""),
                )
                if r == "inserted":
                    inserted += 1

            for prop in data.get("props", []):
                r = self._db.upsert_asset(
                    project_id=self.project_id,
                    asset_type="prop",
                    name=prop.get("name", ""),
                    intro=prop.get("description", ""),
                    prompt=prop.get("description", ""),
                )
                if r == "inserted":
                    inserted += 1

        self._emitter.emit("refresh", {"type": "assets"})
        msg = f"资产生成完成：新增 {inserted}，更新 {updated}，保持 {skipped}"
        self._emit_result("generateAssets", msg)
        return ToolResult(name="generateAssets", ok=True, result=msg)


# ─────────────────────────────────────────────────────────────────────────────
# 工具注册表（name → method）
# ─────────────────────────────────────────────────────────────────────────────

TOOL_METHODS = [
    "get_chapter",
    "get_storyline",
    "save_storyline",
    "delete_storyline",
    "get_outline",
    "save_outline",
    "update_outline",
    "delete_outline",
    "generate_assets",
]


# ─────────────────────────────────────────────────────────────────────────────
# SubAgent 调用
# ─────────────────────────────────────────────────────────────────────────────

def call_subagent(
    agent_type: str,        # "AI1" | "AI2" | "director"
    system_prompt: str,
    user_context: str,
    tools: OutlineToolSet,
    emitter: SimpleEventEmitter,
    model: str = "qwen-max",
    temperature: float = 0.7,
    max_tokens: int = 8192,
) -> str:
    """
    调用 SubAgent（故事师/大纲师/导演）。

    Args:
        agent_type:     SubAgent 类型
        system_prompt: 来自 t_prompts 表的 system prompt
        user_context:   构建好的上下文（含环境信息+任务）
        tools:         工具集实例
        emitter:       事件发射器
        model:         模型
        temperature:   温度
        max_tokens:    最大 token

    Returns:
        SubAgent 的完整响应文本
    """
    from config.qwen_pipeline import call_qwen_with_conversation

    emitter.emit("transfer", {"to": agent_type})

    # 构建工具描述（用于 system prompt）
    tool_descs = [
        "可用工具：",
        "  - getChapter(chapterNumbers: list[int])：获取章节原文",
        "  - getStoryline()：获取故事线",
        "  - saveStoryline(content: str)：保存故事线",
        "  - deleteStoryline()：删除故事线",
        "  - getOutline(simplified: bool)：获取大纲",
        "  - saveOutline(episodes: list[dict], overwrite: bool)：保存大纲",
        "  - updateOutline(id: int, data: dict)：更新单集大纲",
        "  - deleteOutline(ids: list[int])：删除大纲",
        "  - generateAssets()：从大纲生成资产",
    ]
    tool_section = "\n".join(tool_descs)

    full_system = f"{system_prompt}\n\n{tool_section}"

    # 调用 qwen-max
    print(f"\n[OutlineAgent] SubAgent → {agent_type}", file=sys.stderr)

    messages = [{"role": "user", "content": user_context}]
    response = call_qwen_with_conversation(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        system=full_system,
        no_emitter=False,
    )

    emitter.emit("sub_agent_end", {"agent": agent_type})
    return response


# ─────────────────────────────────────────────────────────────────────────────
# OutlineAgent 主类
# ─────────────────────────────────────────────────────────────────────────────

class OutlineAgent:
    """
    大纲故事线 Agent（对标 Toonflow OutlineScript）

    核心职责：
    - 接收用户任务，协调 SubAgent（AI1 故事师 / AI2 大纲师 / director 导演）
    - 管理工具集（章节/故事线/大纲/资产）
    - 通过 EventEmitter 流式输出
    - 历史记录存入 task_db.chat_history

    工具调用流程：
      用户输入 → build_context() → qwen-max（主）
      → 检测工具调用 → 执行工具 → 返回结果 → qwen-max 继续
      → 响应完成
    """

    def __init__(
        self,
        project_id: int,
        db: TaskDB | None = None,
        emitter: SimpleEventEmitter | None = None,
        registry: PromptsRegistry | None = None,
    ):
        self.project_id = project_id
        self._db = db or TaskDB()
        self._emitter = emitter or SimpleEventEmitter()
        self._registry = registry or PromptsRegistry()
        self._tools = OutlineToolSet(project_id, self._db, self._emitter)
        self._history: list[dict] = []    # [{"role": "user/assistant", "content": str}]

    @property
    def emitter(self) -> SimpleEventEmitter:
        return self._emitter

    # ─────────────────────────────────────────────────────────────────
    # 上下文构建
    # ─────────────────────────────────────────────────────────────────

    def _build_environment_context(self) -> str:
        """构建环境信息上下文"""
        project = self._db.get_project(self.project_id)
        if not project:
            proj_info = "（未找到项目）"
        else:
            proj_info = (
                f"项目ID: {self.project_id}\n"
                f"项目名称: {project.get('name', '')}\n"
                f"小说类型: {project.get('type', '')}\n"
                f"目标画幅: {project.get('video_ratio', '')}\n"
            )

        # 章节列表
        chapters = self._db.get_novel_chapters(self.project_id)
        if chapters:
            ch_lines = [f"  第{ch.get('chapter_index')}章 {ch.get('chapter', '')}" for ch in chapters]
            ch_section = "\n".join(ch_lines)
        else:
            ch_section = "  （无章节数据）"

        # 故事线状态
        sl = self._db.get_storyline(self.project_id)
        sl_status = "已生成" if sl else "未生成"

        # 大纲状态
        outlines = self._db.get_outlines(self.project_id)
        outline_count = len(outlines)

        return f"""<环境信息>
{proj_info}

已加载章节列表:
{ch_section}

故事线状态: {sl_status}
大纲状态: 共 {outline_count} 集

可用工具:
- getChapter: 获取章节原文
- getStoryline/saveStoryline/deleteStoryline: 故事线操作
- getOutline/saveOutline/updateOutline/deleteOutline: 大纲操作
- generateAssets: 从大纲生成资产

SubAgent:
- AI1（故事师）：分析小说章节，生成故事线
- AI2（大纲师）：根据故事线生成剧集大纲
- director（导演）：审核故事线和大纲质量
</环境信息>"""

    def _build_conversation_history(self) -> str:
        """构建对话历史"""
        if not self._history:
            return "无对话历史"
        return "\n\n".join(f"{m['role']}: {m['content']}" for m in self._history[-10:])

    def _build_full_context(self, task: str) -> str:
        """构建完整上下文（主 Agent 用）"""
        env = self._build_environment_context()
        history = self._build_conversation_history()

        return f"""{env}

<对话历史>
{history}
</对话历史>

<当前任务>
{task}
</当前任务>"""

    # ─────────────────────────────────────────────────────────────────
    # SubAgent 调用
    # ─────────────────────────────────────────────────────────────────

    def invoke_subagent(self, agent_type: str, task: str) -> str:
        """委托 SubAgent（AI1/AI2/director）"""
        # 从 DB 读取 system prompt
        db_row = self._db.get_prompt(f"outlineScript-{agent_type.lower()}")
        if not db_row:
            return f"[ERROR] 未找到 SubAgent prompt: outlineScript-{agent_type.lower()}"

        system_prompt = db_row.get("value") or db_row.get("default_value") or ""
        if not system_prompt:
            system_prompt = db_row.get("description", f"你是{agent_type}，负责完成指定任务。")

        context = self._build_full_context(task)

        # 从 DEFAULT_AGENTS 读取参数
        params = self._registry.get("director")   # 同等参数配置

        return call_subagent(
            agent_type=agent_type,
            system_prompt=system_prompt,
            user_context=context,
            tools=self._tools,
            emitter=self._emitter,
            model=params.model,
            temperature=params.temperature,
            max_tokens=params.max_tokens,
        )

    # ─────────────────────────────────────────────────────────────────
    # 工具解析与执行（简化为单轮，复杂多轮由 SubAgent 处理）
    # ─────────────────────────────────────────────────────────────────

    def _parse_and_execute_tool(self, text: str) -> list[ToolResult]:
        """
        简单工具调用解析（关键词匹配）。

        对于复杂多轮工具调用，由 SubAgent 处理。
        这里处理明显的单轮工具调用场景。
        """
        results = []
        text_lower = text.lower()

        # saveStoryline 检测
        if "saveStoryline" in text or "save_storyline" in text_lower:
            import re
            m = re.search(r'"content"\s*:\s*"([^"]+)"', text, re.DOTALL)
            if not m:
                m = re.search(r"content[:：]\s*(.+?)(?:\n|$)", text, re.DOTALL)
            if m:
                results.append(self._tools.save_storyline({"content": m.group(1)}))

        # saveOutline 检测
        if "saveOutline" in text or "save_outline" in text_lower:
            results.append(self._tools.save_outline({"episodes": [], "overwrite": True}))

        return results

    # ─────────────────────────────────────────────────────────────────
    # 主入口
    # ─────────────────────────────────────────────────────────────────

    def call(self, user_message: str) -> str:
        """
        主入口：处理用户消息。

        工作流：
          1. 记录历史
          2. 构建上下文
          3. 调用 qwen-max（带工具说明）
          4. 流式输出到 emitter
          5. 返回完整响应
        """
        self._history.append({"role": "user", "content": user_message})

        context = self._build_full_context(user_message)

        # 工具说明（注入 system prompt）
        tool_section = """
你是一个智能大纲故事线协调 Agent。

当用户要求生成/更新大纲时，请按以下流程操作：
1. 如果用户提供了小说原文，先调用 getChapter 获取章节内容
2. 调用 AI1（故事师）生成故事线
3. 调用 AI2（大纲师）根据故事线生成大纲
4. 如需要，调用 director（导演）审核大纲

可用工具（直接调用即可）：
- getChapter(chapterNumbers: list[int])
- getStoryline() / saveStoryline(content: str) / deleteStoryline()
- getOutline(simplified: bool) / saveOutline(episodes: list[dict], overwrite: bool)
- updateOutline(id: int, data: dict) / deleteOutline(ids: list[int])
- generateAssets()
- AI1(taskDescription: str) — 调用故事师
- AI2(taskDescription: str) — 调用大纲师
- director(taskDescription: str) — 调用导演审核
"""

        full_system = f"{tool_section}\n\n{context}"

        # 获取主 Agent 参数
        params = self._registry.get("director")

        print(f"\n[OutlineAgent] 项目 {self.project_id} ← {user_message[:50]}...", file=sys.stderr)

        from config.qwen_pipeline import call_qwen_with_conversation
        messages = [{"role": "user", "content": full_system}]

        response = call_qwen_with_conversation(
            messages=messages,
            model=params.model,
            temperature=params.temperature,
            max_tokens=params.max_tokens,
            system=tool_section,
            no_emitter=False,
        )

        self._history.append({"role": "assistant", "content": response})

        # 保存到 DB
        for msg in self._history[-2:]:
            self._db.append_chat(
                self.project_id,
                agent_type="outline",
                role=msg["role"],
                content=msg["content"],
            )

        self._emitter.emit("response", {"content": response})
        return response


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cli():
    import argparse
    parser = argparse.ArgumentParser(description="大纲故事线 Agent（OutlineAgent）")
    parser.add_argument("--project-id", type=int, required=True, help="项目 ID")
    parser.add_argument("--task", required=True, help="用户任务描述")
    parser.add_argument("--subagent", choices=["AI1", "AI2", "director"], help="直接调用 SubAgent")
    args = parser.parse_args()

    agent = OutlineAgent(project_id=args.project_id)

    if args.subagent:
        result = agent.invoke_subagent(args.subagent, args.task)
        print(result)
    else:
        result = agent.call(args.task)
        print(result)


if __name__ == "__main__":
    _cli()
