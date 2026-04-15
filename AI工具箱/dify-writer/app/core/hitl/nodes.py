# HITL confirmation node implementations
# Human-in-the-Loop nodes for 3 mandatory confirm points:
#   HITL1 — Strategy confirmation (Agent 0 → Agent 1)
#   HITL2 — Outline confirmation (Agent 1 → Agent 3)
#   HITL3 — Final preview (Agent 5 → Agent 8)

from abc import ABC, abstractmethod
from typing import Literal


class HITLNode(ABC):
    """Base class for all HITL confirmation nodes."""

    name: str = ""
    confirm_type: str = ""  # "strategy" | "outline" | "final_preview"

    @abstractmethod
    def build_card(self, context: dict) -> str:
        """Build the confirmation card text shown to the human."""

    @abstractmethod
    def parse_response(self, response: str) -> tuple[bool, str]:
        """
        Parse human response.
        Returns (approved: bool, reason_or_feedback: str).
        """

    def confirm(self, context: dict, human_response: str) -> tuple[bool, dict]:
        """
        Main entry: receive context + human response, return (approved, updates).

        The updates dict can contain revised fields that the human changed
        in their response (e.g. revised topic, revised framework).
        """
        approved, feedback = self.parse_response(human_response)
        updates = self.extract_updates(context, human_response) if approved else {}
        return approved, updates

    def extract_updates(self, context: dict, response: str) -> dict:
        """Extract field revisions from the human's response."""
        return {}


class StrategyConfirm(HITLNode):
    """
    HITL1 — Strategy confirmation card.

    Shown before Agent 1 (Planning) starts.
    Human confirms: topic, platform, framework, and style_profile.
    """

    name = "strategy_confirm"
    confirm_type = "strategy"

    def build_card(self, context: dict) -> str:
        topic = context.get("topic", "未设定")
        platform = context.get("platform", "wechat")
        platform_label = {"wechat": "公众号", "xiaohongshu": "小红书", "both": "公众号 + 小红书"}.get(platform, platform)
        framework = context.get("framework", "痛点型")
        style = context.get("style_profile", "专业严谨")

        return f"""📋 **创作策略确认**

**主题**：{topic}
**发布平台**：{platform_label}
**写作框架**：{framework}
**风格定位**：{style}

确认开始创作？回复"确认"继续，或直接修改上述参数。"""

    def parse_response(self, response: str) -> tuple[bool, str]:
        response = response.strip()
        confirm_keywords = ["确认", "开始", "好", "可以", "继续", "ok", "yes", "y"]
        if any(response.lower().startswith(kw) for kw in confirm_keywords):
            return True, ""
        return False, response


class OutlineConfirm(HITLNode):
    """
    HITL2 — Outline confirmation card.

    Shown after Agent 1 (Planning) completes.
    Human reviews the generated outline before Agent 3 (Writing) starts.
    """

    name = "outline_confirm"
    confirm_type = "outline"

    def build_card(self, context: dict) -> str:
        outline = context.get("outline", {})
        framework = context.get("framework", "痛点型")
        topic = context.get("topic", "未设定")

        sections = outline.get("sections", [])
        sections_text = ""
        if sections:
            for i, sec in enumerate(sections[:6], 1):
                title = sec.get("title", "未命名")
                points = sec.get("points", [])
                points_text = "\n".join(f"  {i+1}. {p}" for i, p in enumerate(points[:3]))
                sections_text += f"\n{i}. **{title}**\n{points_text}"
        else:
            sections_text = "\n（大纲暂无详细内容）"

        return f"""📝 **大纲确认**

**主题**：{topic}
**框架**：{framework}

**大纲预览**：
{sections_text}

回复"确认"继续写作，或提出修改意见。"""

    def parse_response(self, response: str) -> tuple[bool, str]:
        response = response.strip()
        confirm_keywords = ["确认", "好", "可以", "开始写作", "ok", "yes", "y"]
        if any(response.lower().startswith(kw) for kw in confirm_keywords):
            return True, ""
        return False, response


class FinalPreviewConfirm(HITLNode):
    """
    HITL3 — Final preview confirmation.

    Shown after Agent 5 (Polish) completes.
    Human reviews the polished article before final HTML generation.
    """

    name = "final_preview_confirm"
    confirm_type = "final_preview"

    def build_card(self, context: dict) -> str:
        polished = context.get("polished_draft", "")
        quality_score = context.get("quality_score", 0)
        quality_feedback = context.get("quality_feedback", "")

        preview = polished[:500] + "..." if len(polished) > 500 else polished

        return f"""✅ **最终预览确认**

**质量评分**：{quality_score}/100
**反馈**：{quality_feedback or "无"}

**文章预览（前500字）**：
{preview}

确认生成最终 HTML？回复"确认"生成，或提出修改意见。"""

    def parse_response(self, response: str) -> tuple[bool, str]:
        response = response.strip()
        confirm_keywords = ["确认", "生成", "好", "可以", "ok", "yes", "y"]
        if any(response.lower().startswith(kw) for kw in confirm_keywords):
            return True, ""
        return False, response
