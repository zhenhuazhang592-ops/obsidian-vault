# Writing Agent — Agent 4: 内容写作师
# Reads: topic, outline, research, framework, style_profile
# Writes: draft (str)
import json
import logging

from app.agents.base_agent import AgentResult, BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位资深公众号/小红书内容创作者，擅长写读者爱读、有价值的长文。

你将收到：完整大纲、调研资料、内容框架。
你的任务：基于大纲，逐节写出完整文章内容。

写作要求：
- 严格按照大纲结构，不要偏离
- 每个章节要有实质性内容（300-500字）
- 语言流畅，避免AI写作腔
- 适当使用小标题分隔
- 痛点型文章：开头要引发共鸣，结尾要有行动指引
- 清单型文章：每个条目要有干货，不能水文
- 故事型文章：有叙事弧度，有细节描写

输出：纯文本文章内容（Markdown 格式）
不要输出 JSON，不要解释，直接写文章。
"""


class WritingAgent(BaseAgent):
    """
    Agent 4 — 内容写作师。

    在 Agent 3 (Outline) 完成之后调用。
    基于大纲和调研资料写出完整文章草稿。
    """

    name = "writing_agent"
    description = "基于大纲和调研资料撰写完整文章草稿"
    model = "claude-sonnet-4-6"
    max_tokens = 8192
    temperature = 0.75

    def execute(self, context: dict) -> AgentResult:
        topic = context.get("topic", "")
        outline = context.get("outline", {})
        framework = context.get("framework", "痛点型")
        research = context.get("research", {})
        style = context.get("style_profile", "专业严谨")

        if not outline:
            return AgentResult(
                success=False,
                error="outline is required",
                agent_name=self.name,
            )

        # Build outline text
        sections = outline.get("sections", [])
        outline_text = self._format_outline(outline)

        # Build research context
        research_context = ""
        sources = research.get("sources", [])
        if sources:
            research_lines = []
            for s in sources[:5]:
                title = s.get("title", "")
                content = s.get("content", "")[:300]
                if title:
                    research_lines.append(f"### {title}\n{content}\n")
            research_context = "\n".join(research_lines)

        user_prompt = f"""## 创作任务

主题：{topic}
内容框架：{framework}
风格定位：{style}

## 文章大纲
{outline_text}

## 调研资料
{research_context or "（无额外调研资料）"}

请严格按照大纲撰写文章。直接输出文章内容，不要 JSON。"""

        try:
            response = self._call_llm(SYSTEM_PROMPT, user_prompt)
            draft = response.strip()

            context["draft"] = draft

            logger.info(
                f"[{self.name}] wrote draft ({len(draft)} chars) for topic={topic}"
            )

            return AgentResult(
                success=True,
                data={"draft": draft, "word_count": len(draft)},
                agent_name=self.name,
            )

        except Exception as e:
            logger.exception(f"[{self.name}] failed")
            return AgentResult(
                success=False,
                error=str(e),
                agent_name=self.name,
            )

    def _format_outline(self, outline: dict) -> str:
        sections = outline.get("sections", [])
        lines = []
        for sec in sections:
            title = sec.get("title", "未命名")
            purpose = sec.get("purpose", "")
            points = sec.get("key_points", [])
            lines.append(f"### {title}")
            if purpose:
                lines.append(f"目的：{purpose}")
            for i, pt in enumerate(points, 1):
                lines.append(f"  {i}. {pt}")
            lines.append("")
        return "\n".join(lines)
