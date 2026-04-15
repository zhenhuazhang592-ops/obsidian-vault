# Planning Agent — Agent 1: 主题策划师
# Reads: topic, platform, style_profile
# Writes: research_plan, framework, framework_reason, platform_config
import json
import logging
from typing import Any

from app.agents.base_agent import AgentResult, BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位资深内容策划师，擅长为公众号/小红书创作者制定精准的创作策略。

你的任务是根据给定主题、平台和风格定位，制定创作策略并输出结构化的策划案。

输出要求（严格 JSON）：
{
  "research_plan": {
    "primary_query": "核心搜索query",
    "sub_queries": ["补充query1", "补充query2", "补充query3"],
    "search_depth": "normal|deep",
    "key_aspects": ["关键角度1", "关键角度2"]
  },
  "framework": "痛点型|故事型|清单型|对比型|热点解读型",
  "framework_reason": "选择该框架的核心原因（1-2句话）",
  "platform_config": {
    "title_hint": "标题风格提示（平台适配）",
    "content_length": "1500-2000字|2000-3000字|3000-4000字",
    "emoji_density": "low|medium|high",
    "hashtag_hint": ["推荐标签1", "推荐标签2", "推荐标签3"]
  },
  "style_profile": "亲和力强|专业严谨|幽默风趣|极简干货",
  "style_note": "风格微调说明（针对该主题）",
  "angle_suggestion": "差异化切入角度建议"
}
"""


class PlanningAgent(BaseAgent):
    """
    Agent 1 — 主题策划师。

    在 HITL1 策略确认之后调用。
    分析主题并产出：research_plan, framework, platform_config。
    """

    name = "planning_agent"
    description = "分析主题，制定创作策略和调研计划"
    model = "claude-sonnet-4-6"
    max_tokens = 2048

    def execute(self, context: dict) -> AgentResult:
        topic = context.get("topic", "")
        platform = context.get("platform", "wechat")
        style = context.get("style_profile", "专业严谨")

        if not topic:
            return AgentResult(
                success=False,
                error="topic is required",
                agent_name=self.name,
            )

        platform_labels = {
            "wechat": "微信公众号",
            "xiaohongshu": "小红书",
            "both": "微信公众号 + 小红书双平台",
        }
        platform_text = platform_labels.get(platform, platform)

        user_prompt = f"""主题：{topic}
目标平台：{platform_text}
风格定位：{style}

请制定创作策略，输出严格 JSON。"""

        try:
            response = self._call_llm(SYSTEM_PROMPT, user_prompt)
            data = self._extract_json(response)

            # Merge into context
            research_plan = data.get("research_plan", {})
            context["research_plan"] = research_plan
            context["framework"] = data.get("framework", "痛点型")
            context["framework_reason"] = data.get("framework_reason", "")
            context["platform_config"] = data.get("platform_config", {})
            context["style_note"] = data.get("style_note", "")
            context["angle_suggestion"] = data.get("angle_suggestion", "")

            logger.info(f"[{self.name}] framework={data.get('framework')} topic={topic}")

            return AgentResult(
                success=True,
                data=data,
                agent_name=self.name,
            )

        except Exception as e:
            logger.exception(f"[{self.name}] failed")
            return AgentResult(
                success=False,
                error=str(e),
                agent_name=self.name,
            )
