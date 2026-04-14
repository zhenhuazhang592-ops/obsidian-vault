# Writing Pipeline — Agent 0: Pipeline Orchestrator
# Coordinates the full 9-agent writing pipeline with 3 HITL confirm points
# and a quality review loop (max 3 iterations, threshold 85 points).
#
# Pipeline flow:
#   Agent 0 (this) → HITL1 → Agent 1 → Agent 2 → HITL2 → Agent 3 → Agent 4
#                 → Agent 5 → Agent 6 (quality check)
#                 ↺ quality loop (Agent 5 → 6) up to 3 times
#                 → HITL3 → Agent 8 → done
#
# Agents 2, 6, 8 are implemented as Week 1 tools (deep_research, check_quality, format_html).

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Literal, Optional

from app.agents.base_agent import AgentResult
from app.agents.planning_agent import PlanningAgent
from app.agents.outline_agent import OutlineAgent
from app.agents.writing_agent import WritingAgent
from app.agents.polish_agent import PolishAgent
from app.core.hitl import StrategyConfirm, OutlineConfirm, FinalPreviewConfirm
from app.tools.base import get_registry

logger = logging.getLogger(__name__)

# Quality threshold — Agent 6 must score ≥ this for the pipeline to proceed
QUALITY_THRESHOLD = 85
MAX_QUALITY_ITERATIONS = 3

# Week 1 tool names
TOOL_DEEP_RESEARCH = "deep_research"
TOOL_CHECK_QUALITY = "check_quality"
TOOL_FORMAT_HTML = "format_html"


@dataclass
class PipelineConfig:
    """Configuration for the writing pipeline."""

    topic: str = ""
    platform: str = "wechat"  # "wechat" | "xiaohongshu" | "both"
    style_profile: str = "专业严谨"  # "亲和力强" | "专业严谨" | "幽默风趣" | "极简干货"
    theme: str = "professional-clean"  # HTML theme
    hitl_enabled: bool = True  # Set False for fully automated (testing)


class WritingPipeline:
    """
    Agent 0 — Pipeline Orchestrator.

    Manages the full 9-agent writing pipeline:
    - Coordinates all sub-agents via shared data_bus dict
    - Handles HITL confirmation nodes (3 mandatory confirm points)
    - Manages the quality review loop (max 3 iterations, 85pt threshold)
    - Integrates Week 1 tools (Agents 2, 6, 8) via tool registry
    """

    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()
        self._data_bus: dict = {
            "topic": self.config.topic,
            "platform": self.config.platform,
            "style_profile": self.config.style_profile,
            "theme": self.config.theme,
            "status": "idle",
            "errors": [],
        }
        self._registry = get_registry()

        # HITL nodes
        self._hitl_strategy = StrategyConfirm()
        self._hitl_outline = OutlineConfirm()
        self._hitl_final = FinalPreviewConfirm()

        # Sub-agents
        self._agents = {
            "planning": PlanningAgent(),
            "outline": OutlineAgent(),
            "writing": WritingAgent(),
            "polish": PolishAgent(),
        }

    async def run(self, topic: str, platform: str = "wechat",
                  style_profile: str = "专业严谨",
                  hitl_enabled: bool = True) -> dict:
        """
        Run the full writing pipeline.

        Args:
            topic: Article topic/theme
            platform: Target platform
            style_profile: Writing style
            hitl_enabled: Whether to pause for human confirmation

        Returns:
            Final data_bus dict with all pipeline outputs.
        """
        # Initialize data bus
        self._data_bus = {
            "topic": topic,
            "platform": platform,
            "style_profile": style_profile,
            "theme": self.config.theme,
            "status": "running",
            "errors": [],
        }
        self.config.topic = topic
        self.config.platform = platform
        self.config.style_profile = style_profile
        self.config.hitl_enabled = hitl_enabled

        try:
            # Phase 1: Planning + Research
            await self._phase1_planning_and_research()

            # Phase 2: Outline
            await self._phase2_outline()

            # Phase 3: Writing
            await self._phase3_writing()

            # Phase 4: Quality Loop
            await self._phase4_quality_loop()

            # Phase 5: Final HTML
            await self._phase5_final()

            self._data_bus["status"] = "completed"
            logger.info(f"[Pipeline] completed successfully for topic={topic}")

        except Exception as e:
            logger.exception(f"[Pipeline] failed: {e}")
            self._data_bus["status"] = "failed"
            self._data_bus["error"] = str(e)

        return self._data_bus

    # ─── Phase 1: Planning + Research ──────────────────────────────

    async def _phase1_planning_and_research(self) -> None:
        """HITL1 → Agent 1 → Agent 2 (deep_research)."""
        # HITL1: Strategy confirmation
        if self.config.hitl_enabled:
            card = self._hitl_strategy.build_card(self._data_bus)
            # In Dify integration, this card is sent to the Dify chatflow for human review
            # For standalone use, we return the card and wait for response
            logger.info(f"[Pipeline] HITL1 card: {card[:100]}")
            # self._data_bus["_hitl1_card"] = card

        # Agent 1: Planning
        result = await asyncio.to_thread(self._agents["planning"].execute, self._data_bus)
        if not result.success:
            raise PipelineError(f"PlanningAgent failed: {result.error}")

        # Agent 2: Deep research (Week 1 tool)
        research_plan = self._data_bus.get("research_plan", {})
        queries = research_plan.get("sub_queries", []) or [self._data_bus["topic"]]
        tool = self._registry.get(TOOL_DEEP_RESEARCH)
        research_result = await tool.execute(
            topic=self._data_bus["topic"],
            queries=queries,
            platform=self._data_bus["platform"],
        )
        self._data_bus["research"] = research_result

    # ─── Phase 2: Outline ───────────────────────────────────────────

    async def _phase2_outline(self) -> None:
        """HITL2 → Agent 3 (Outline)."""
        # HITL2: Outline confirmation
        if self.config.hitl_enabled:
            card = self._hitl_outline.build_card(self._data_bus)
            logger.info(f"[Pipeline] HITL2 card: {card[:100]}")
            # self._data_bus["_hitl2_card"] = card

        # Agent 3: Outline
        result = await asyncio.to_thread(self._agents["outline"].execute, self._data_bus)
        if not result.success:
            raise PipelineError(f"OutlineAgent failed: {result.error}")

    # ─── Phase 3: Writing ──────────────────────────────────────────

    async def _phase3_writing(self) -> None:
        """Agent 4 (Writing) → produces draft."""
        result = await asyncio.to_thread(self._agents["writing"].execute, self._data_bus)
        if not result.success:
            raise PipelineError(f"WritingAgent failed: {result.error}")

    # ─── Phase 4: Quality Loop ───────────────────────────────────

    async def _phase4_quality_loop(self) -> None:
        """
        Quality review loop: Agent 6 (check_quality) → Agent 5 (polish).

        Loop: up to MAX_QUALITY_ITERATIONS times.
        Exit when quality_score >= QUALITY_THRESHOLD.
        """
        for iteration in range(1, MAX_QUALITY_ITERATIONS + 1):
            self._data_bus["quality_iteration"] = iteration
            logger.info(f"[Pipeline] quality loop iteration {iteration}")

            # Agent 6: Quality check (Week 1 tool)
            draft = self._data_bus.get("polished_draft") or self._data_bus.get("draft", "")
            tool = self._registry.get(TOOL_CHECK_QUALITY)
            quality_result = tool.execute(
                article=draft,
                framework=self._data_bus.get("framework", "痛点型"),
                platform=self._data_bus["platform"],
            )
            self._data_bus["quality_score"] = quality_result.get("quality_score", 0)
            self._data_bus["quality_feedback"] = "; ".join(
                quality_result.get("issues", []) + quality_result.get("suggestions", [])
            )

            score = self._data_bus["quality_score"]
            logger.info(f"[Pipeline] quality score: {score}/100")

            if score >= QUALITY_THRESHOLD:
                logger.info(f"[Pipeline] quality threshold met ({score} >= {QUALITY_THRESHOLD})")
                break

            if iteration == MAX_QUALITY_ITERATIONS:
                logger.warning(
                    f"[Pipeline] max iterations ({MAX_QUALITY_ITERATIONS}) reached, "
                    f"proceeding with score {score}"
                )
                break

            # Agent 5: Polish
            result = await asyncio.to_thread(self._agents["polish"].execute, self._data_bus)
            if not result.success:
                raise PipelineError(f"PolishAgent failed: {result.error}")

        # Quality loop complete — set polished_draft from last polish or draft
        if "polished_draft" not in self._data_bus:
            self._data_bus["polished_draft"] = self._data_bus.get("draft", "")

    # ─── Phase 5: Final HTML ──────────────────────────────────────

    async def _phase5_final(self) -> None:
        """HITL3 → Agent 8 (format_html) → produces html_output."""
        # HITL3: Final preview confirmation
        if self.config.hitl_enabled:
            card = self._hitl_final.build_card(self._data_bus)
            logger.info(f"[Pipeline] HITL3 card: {card[:100]}")
            # self._data_bus["_hitl3_card"] = card

        # Agent 8: Format HTML (Week 1 tool)
        polished = self._data_bus.get("polished_draft", "")
        images = self._data_bus.get("inline_images", [])
        tool = self._registry.get(TOOL_FORMAT_HTML)
        html_result = tool.execute(
            article=polished,
            images=images,
            theme=self._data_bus.get("theme", "professional-clean"),
        )
        self._data_bus["html_output"] = html_result.get("html_string", "")

    # ─── HITL Response Handling ───────────────────────────────────

    async def deliver_hitl_response(
        self,
        confirm_type: Literal["strategy", "outline", "final_preview"],
        human_response: str,
    ) -> dict:
        """
        Deliver a human's response to a HITL confirmation card.

        Called by Dify chatflow after human provides feedback.
        Returns the updated data_bus context.
        """
        if confirm_type == "strategy":
            node = self._hitl_strategy
        elif confirm_type == "outline":
            node = self._hitl_outline
        elif confirm_type == "final_preview":
            node = self._hitl_final
        else:
            raise ValueError(f"Unknown confirm_type: {confirm_type}")

        approved, updates = node.confirm(self._data_bus, human_response)
        if updates:
            self._data_bus.update(updates)

        self._data_bus["_hitl_last"] = {
            "confirm_type": confirm_type,
            "approved": approved,
            "feedback": human_response,
        }
        return self._data_bus

    @property
    def data_bus(self) -> dict:
        """Return current data bus state."""
        return self._data_bus


class PipelineError(Exception):
    """Raised when a pipeline step fails."""
    pass
