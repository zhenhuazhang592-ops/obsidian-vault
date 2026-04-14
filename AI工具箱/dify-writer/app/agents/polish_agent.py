# Polish Agent — Agent 5: 润色优化师
# Reads: draft, style_profile, framework, quality_score, quality_feedback
# Writes: polished_draft, quality_score, quality_feedback
import json
import logging

from app.agents.base_agent import AgentResult, BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位资深文字编辑，擅长润色和优化文章，提升可读性和感染力。

你将收到：文章草稿、风格定位、内容框架、上轮质量评分和反馈。
你的任务：润色优化文章，解决质量反馈中的问题。

润色原则：
1. 保持原文核心观点和数据不变
2. 改善语言流畅性，消除AI腔
3. 强化开头吸引力（前3段最关键）
4. 精简冗余表述
5. 增强结尾行动指引（如适用）
6. 保持风格一致

输出：润色后的完整文章（纯文本，Markdown 格式）
不要输出 JSON，不要解释，直接输出润色后的文章。
"""


class PolishAgent(BaseAgent):
    """
    Agent 5 — 润色优化师。

    在 Quality Loop（Agent 6）评分 < 85 时调用。
    接收质量反馈，对草稿进行针对性优化。
    """

    name = "polish_agent"
    description = "润色优化文章草稿，解决质量问题"
    model = "claude-sonnet-4-6"
    max_tokens = 8192
    temperature = 0.65

    def execute(self, context: dict) -> AgentResult:
        draft = context.get("draft", "")
        style = context.get("style_profile", "专业严谨")
        framework = context.get("framework", "痛点型")
        quality_score = context.get("quality_score", 0)
        quality_feedback = context.get("quality_feedback", "")
        iteration = context.get("quality_iteration", 1)

        if not draft:
            return AgentResult(
                success=False,
                error="draft is required",
                agent_name=self.name,
            )

        # Truncate for prompt
        draft_preview = draft[:3000] + "..." if len(draft) > 3000 else draft

        user_prompt = f"""## 润色任务

风格定位：{style}
内容框架：{framework}
上轮质量评分：{quality_score}/100
上轮质量反馈：{quality_feedback or "无反馈"}
润色轮次：第 {iteration} 轮

## 文章草稿
{draft_preview}

请润色优化这篇草稿。直接输出润色后的文章，不要 JSON。"""

        try:
            response = self._call_llm(SYSTEM_PROMPT, user_prompt)
            polished = response.strip()

            context["polished_draft"] = polished
            # Clear quality score for re-check
            context["quality_score"] = 0
            context["quality_feedback"] = ""

            logger.info(
                f"[{self.name}] polished draft ({len(polished)} chars), iteration={iteration}"
            )

            return AgentResult(
                success=True,
                data={
                    "polished_draft": polished,
                    "word_count": len(polished),
                    "iteration": iteration,
                },
                agent_name=self.name,
            )

        except Exception as e:
            logger.exception(f"[{self.name}] failed")
            return AgentResult(
                success=False,
                error=str(e),
                agent_name=self.name,
            )
