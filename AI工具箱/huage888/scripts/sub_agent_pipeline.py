#!/usr/bin/env python3
"""
sub_agent_pipeline.py — Sub-Agent 动态嵌套执行器

对应 Toonflow 的 createSubAgentTool() → invokeSubAgent() 行为：
- 父 Agent 在执行过程中动态调用子 Agent
- 通过 emit("transfer") 通知切换
- 子 Agent 执行完后 emit("sub_agent_end")

核心差异 vs Toonflow：
- Toonflow：Node.js 进程内 u.ai.text.stream() 调用，流式推送
- huage888：Python CLI，qwen_pipeline 子进程调用，模拟流式推送

用法：
  from sub_agent_pipeline import SubAgentRunner, SUB_AGENT_TOOLS

  runner = SubAgentRunner(emitter=emitter, task_id="abc123", parent_agent="director")
  result = runner.invoke(
      child_agent="outline",
      task_description="基于以下剧本生成故事线...",
  )

工具权限映射（对应 Toonflow getSubAgentTools）：
  SUB_AGENT_TOOLS = {
      "storyline":   ["getChapter", "getStoryline", "saveStoryline"],
      "outline":     ["getOutline", "saveOutline", "generateAssets"],
      "storyboard":  ["getScript", "getAssets", "generateImagePrompts"],
      "director":    ["getOutline", "updateOutline", "getStoryline", "saveStoryline"],
  }
"""

import sys
from pathlib import Path
from typing import Callable, Optional

# ── 路径配置 ─────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
CONFIG_DIR = BASE_DIR / "config"

sys.path.insert(0, str(CONFIG_DIR))
sys.path.insert(0, str(SCRIPT_DIR))


# ── Sub-Agent 工具权限映射 ────────────────────────────────────────────────────

SUB_AGENT_TOOLS: dict[str, list[str]] = {
    # storyboard-agent 可调用的子 Agent
    "storyboard": [
        "storyline",   # 获取故事线
        "outline",    # 获取/生成大纲
    ],
    # director-agent 可调用的子 Agent
    "director": [
        "storyline",   # 获取故事线
        "outline",     # 获取/生成大纲
    ],
    # outline-agent 可调用的子 Agent
    "outline": [
        "storyline",   # 获取故事线上下文
    ],
    # storyline-agent 本身是叶子节点
    "storyline": [],
}


# ── SubAgentRunner ────────────────────────────────────────────────────────────

class SubAgentRunner:
    """
    Sub-Agent 嵌套执行器

    模拟 Toonflow 的 invokeSubAgent() 行为：
    1. emit("transfer", from=parent, to=child)     — 通知切换
    2. call_qwen_with_conversation(child, ...)    — 执行子 Agent
    3. emit("sub_agent_end", agent=child)        — 通知完成

    工具权限隔离（对应 Toonflow getSubAgentTools()）：
    - 每个 parent_agent 只能调用其 SUB_AGENT_TOOLS 中声明的子 Agent
    - 不在列表中的子 Agent 被拒绝
    """

    def __init__(
        self,
        emitter,
        task_id: str,
        parent_agent: str,
        conv_mgr=None,
        dry_run: bool = False,
    ):
        self.emitter = emitter
        self.task_id = task_id
        self.parent_agent = parent_agent
        self.conv_mgr = conv_mgr
        self.dry_run = dry_run

    def get_allowed_tools(self, child_agent: str) -> list[str]:
        """获取子 Agent 的工具权限列表（对应 Toonflow getSubAgentTools()）"""
        return SUB_AGENT_TOOLS.get(child_agent, [])

    def is_allowed(self, child_agent: str) -> bool:
        """检查 parent 是否被允许调用此子 Agent"""
        allowed = SUB_AGENT_TOOLS.get(self.parent_agent, [])
        return child_agent in allowed

    def invoke(
        self,
        child_agent: str,
        task_description: str,
        system_builder: Callable[[str], str] | None = None,
        session_id: str | None = None,
    ) -> str:
        """
        执行子 Agent 调用（模拟 Toonflow invokeSubAgent()）。

        Args:
            child_agent: 子 Agent 名称（必须在 SUB_AGENT_TOOLS 中）
            task_description: 子 Agent 的任务描述
            system_builder: 自定义 system prompt 构建函数（agent_name → prompt）
                           传 None 则使用默认 build_system_prompt
            session_id: 对话 session ID（传 None 则自动创建）

        Returns:
            子 Agent 的完整输出内容

        Raises:
            PermissionError: 子 Agent 不在允许列表中
        """
        if not self.is_allowed(child_agent):
            allowed = SUB_AGENT_TOOLS.get(self.parent_agent, [])
            raise PermissionError(
                f"Agent '{self.parent_agent}' 不被允许调用 '{child_agent}'。"
                f"允许列表: {allowed}"
            )

        # 1. emit("transfer") — 通知前端切换 Agent
        self.emitter.emit_transfer(
            task_id=self.task_id,
            from_agent=self.parent_agent,
            to_agent=child_agent,
        )
        print(
            f"  🔄 transfer: {self.parent_agent} → {child_agent}",
            file=sys.stderr,
        )

        # 2. 构建 session
        if self.conv_mgr is None:
            from conversation_manager import ConversationManager
            self.conv_mgr = ConversationManager()

        if session_id is None:
            session_id = self.conv_mgr.new_session(child_agent)

        # 3. 构建 system prompt
        if system_builder is None:
            from qwen_pipeline import build_system_prompt
            system_prompt = build_system_prompt(child_agent, skill_name=None)
        else:
            system_prompt = system_builder(child_agent)

        # 4. 构建完整 user（包含工具说明）
        allowed_tools = self.get_allowed_tools(child_agent)
        tools_info = ""
        if allowed_tools:
            tools_info = f"\n\n可用工具：{', '.join(allowed_tools)}"

        full_user = (
            f"<任务>\n{task_description}\n</任务>"
            f"{tools_info}"
        )

        if self.dry_run:
            print(f"  [DRY] sub-agent: {child_agent}", file=sys.stderr)
            print(f"  [DRY] user: {full_user[:100]}...", file=sys.stderr)
            return "[DRY] sub-agent response placeholder"

        # 5. 调用 API（带对话历史）
        from qwen_pipeline import call_qwen_with_conversation

        self.emitter.emit_sub_agent_start(
            task_id=self.task_id,
            agent=child_agent,
            task_description=task_description,
        )

        result = call_qwen_with_conversation(
            agent=child_agent,
            user=full_user,
            session_id=session_id,
            conv_mgr=self.conv_mgr,
            output_path=None,
            emitter=self.emitter,
            task_id=self.task_id,
            task_name=f"sub-{self.parent_agent}-{child_agent}",
        )

        # 6. 模拟流式输出（按块推送）
        chunk_size = 50
        for i in range(0, len(result), chunk_size):
            chunk = result[i : i + chunk_size]
            self.emitter.emit_sub_agent_stream(
                task_id=self.task_id,
                agent=child_agent,
                text=chunk,
            )

        # 7. emit("sub_agent_end")
        self.emitter.emit_sub_agent_end(
            task_id=self.task_id,
            agent=child_agent,
            full_response=result,
        )

        print(
            f"  ✅ sub_agent_end: {child_agent} ({len(result)} chars)",
            file=sys.stderr,
        )

        return result

    def can_invoke(self, child_agent: str) -> bool:
        """检查是否可调用（不抛异常的检查版本）"""
        return self.is_allowed(child_agent)


# ── 便捷函数 ─────────────────────────────────────────────────────────────────

def create_sub_agent_tool(
    runner: SubAgentRunner,
    agent_name: str,
    description: str,
) -> dict:
    """
    创建 Sub-Agent 工具定义（JSON 格式，对应 Toonflow createSubAgentTool()）。

    返回一个 JSON 格式的工具定义，可嵌入 agent markdown 文件中。

    用法（嵌入 agents/director.md）：
        ## 可用工具（Sub-Agent 调用）
        {sub_agent_tool_def}
    """
    import json

    tool_def = {
        "tool_call": agent_name,
        "description": description,
        "invoke": f"runner.invoke('{agent_name}', task_description=task)",
        "allowed_from": [
            parent for parent, children in SUB_AGENT_TOOLS.items()
            if agent_name in children
        ],
    }
    return tool_def


def build_all_tool_defs() -> str:
    """生成所有 Sub-Agent 工具的 Markdown 说明，供嵌入 agent 文件"""
    lines = [
        "## 可用 Sub-Agent 工具",
        "",
        "当需要生成子任务时，可使用以下工具调用嵌套 Agent：",
        "",
    ]

    for parent, children in SUB_AGENT_TOOLS.items():
        if not children:
            continue
        lines.append(f"### 调用 {parent} 的子 Agent")
        for child in children:
            tool = create_sub_agent_tool(
                runner=None,  # 占位
                agent_name=child,
                description=f"调用 {child} agent 执行子任务",
            )
            import json
            lines.append(f"```json\n{json.dumps(tool, indent=2, ensure_ascii=False)}\n```")
            lines.append("")

    return "\n".join(lines)


# ── CLI 测试 ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sub-Agent 嵌套执行器测试")
    parser.add_argument("--parent", required=True, help="父 Agent")
    parser.add_argument("--child", required=True, help="子 Agent")
    parser.add_argument("--task", required=True, help="任务描述")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from event_emitter import EventEmitter, ConsoleSink

    emitter = EventEmitter(sinks=[ConsoleSink(color=True)])
    runner = SubAgentRunner(
        emitter=emitter,
        task_id="test-001",
        parent_agent=args.parent,
        dry_run=args.dry_run,
    )

    try:
        result = runner.invoke(
            child_agent=args.child,
            task_description=args.task,
        )
        print(f"\n结果（前100字）：{result[:100]}...")
    except PermissionError as e:
        print(f"权限拒绝: {e}")
        sys.exit(1)
