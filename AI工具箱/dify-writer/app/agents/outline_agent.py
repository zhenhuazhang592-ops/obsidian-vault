# Outline Agent — Agent 3: 大纲规划师
# Reads: topic, platform, style_profile, framework, research, research_plan
# Writes: outline (dict with sections)
import json
import logging
import re

from app.agents.base_agent import AgentResult, BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位资深内容架构师，擅长为长文创作制定清晰、有逻辑的大纲。

你将收到：主题、目标平台、内容框架、调研资料。
你的任务：制定完整的文章大纲，包含多级结构。

输出要求（严格 JSON）：
{
  "outline": {
    "title": "文章标题（主标题）",
    "subtitle": "副标题（可选）",
    "framework": "对应框架类型",
    "sections": [
      {
        "id": "s1",
        "title": "章节标题",
        "purpose": "本节目的（20字内）",
        "key_points": ["核心观点1", "核心观点2", "核心观点3"],
        "word_count_hint": "建议字数",
        "tone_hint": "语气提示"
      }
    ],
    "total_word_count": "预计总字数范围",
    "structure_note": "结构说明"
  }
}
"""


class OutlineAgent(BaseAgent):
    """
    Agent 3 — 大纲规划师。

    在 HITL2 大纲确认之后调用（research 已完成后）。
    基于 research 和 framework 生成完整文章大纲。
    """

    name = "outline_agent"
    description = "基于调研资料和框架生成文章大纲"
    model = "claude-sonnet-4-6"
    max_tokens = 2048

    def execute(self, context: dict) -> AgentResult:
        topic = context.get("topic", "")
        platform = context.get("platform", "wechat")
        framework = context.get("framework", "痛点型")
        research = context.get("research", {})
        research_summary = research.get("summary", "暂无调研资料")
        style = context.get("style_profile", "专业严谨")

        if not topic:
            return AgentResult(
                success=False,
                error="topic is required",
                agent_name=self.name,
            )

        platform_text = "微信公众号" if platform == "wechat" else "小红书"

        # Build research context
        research_context = ""
        if research:
            sources = research.get("sources", [])
            if sources:
                research_lines = []
                for s in sources[:5]:
                    title = s.get("title", "")
                    content = s.get("content", "")[:200]
                    if title:
                        research_lines.append(f"- {title}：{content}")
                research_context = "\n".join(research_lines)

        user_prompt = f"""## 创作任务

主题：{topic}
目标平台：{platform_text}
内容框架：{framework}
风格定位：{style}

## 调研资料摘要
{research_context or research_summary}

请制定完整文章大纲，输出严格 JSON。"""

        try:
            response = self._call_llm(SYSTEM_PROMPT, user_prompt)
            data = self._extract_json(response)

            outline = data.get("outline", {})
            context["outline"] = outline

            logger.info(
                f"[{self.name}] generated outline with {len(outline.get('sections', []))} sections"
            )

            return AgentResult(
                success=True,
                data={"outline": outline},
                agent_name=self.name,
            )

        except Exception as e:
            logger.exception(f"[{self.name}] failed")
            return AgentResult(
                success=False,
                error=str(e),
                agent_name=self.name,
            )
