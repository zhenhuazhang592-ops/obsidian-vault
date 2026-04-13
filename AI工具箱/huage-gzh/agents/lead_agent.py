# agents/lead_agent.py - 创作链路主导Agent
# Phase 1: 串联 Planner → Research → Outline → Writer → Polish → Review → Image → Format
#           持有 6 个用户确认节点，驱动完整流程

import time
import json
from pathlib import Path
from typing import Any, Optional

from core.base_agent import BaseAgent, AgentResult
from core.message_hub import MessageHub, Message, MessageType
from core.llm_client import LLMClient, LLMCallError
from core.confirm_nodes import (
    ConfirmResult,
    PlanConfirmNode,
    OutlineConfirmNode,
    QualityConfirmNode,
    ResearchConfirmNode,
    ImageConfirmNode,
)


# ────────────────────────────────────────────────────────────────
# LeadAgent - 创作链路主导者
# ────────────────────────────────────────────────────────────────

class LeadAgent:
    """
    漠玫创作系统的主导Agent。
    负责任务编排、Agent调度、用户确认节点驱动。

    Phase 1 职责：
    - 串联已实现的 Agent（Planner/Outline/Writer/Polisher）
    - 驱动 6 个确认节点
    - 管理 MessageHub session
    - 提供干运行（dry-run）模式

    Phase 2 扩展：
    - 新增 ResearchAgent / ImageAgent
    - 集成 Tavily 搜索 + Obsidian 知识库

    Phase 3+ 扩展：
    - SEO/GEO 评分报告
    - 多平台发布
    """

    name = "Lead"
    description = "漠玫创作系统主导Agent，编排完整创作链路"

    # 流水线阶段定义
    STAGES = [
        ("planner", "主题策划", MessageType.PLAN),
        ("research", "深度研究", MessageType.RESEARCH),
        ("outline", "大纲规划", MessageType.OUTLINE),
        ("writer", "内容写作", MessageType.DRAFT),
        ("polish", "润色优化", MessageType.POLISHED),
        ("review", "质量审查", MessageType.REVIEW),
        ("image", "配图封面", MessageType.IMAGE),
        ("format", "排版输出", MessageType.FORMATTED),
    ]

    def __init__(
        self,
        hub: MessageHub = None,
        llm_client: Optional[LLMClient] = None,
        dry_run: bool = False,
        tavily_api_key: str = None,
        obsidian_vault_path: str = None,
    ):
        self.hub = hub or MessageHub()
        self.llm_client = llm_client
        self.dry_run = dry_run
        self.tavily_api_key = tavily_api_key
        self.obsidian_vault_path = obsidian_vault_path

        # 确认节点
        self.plan_confirm = PlanConfirmNode()
        self.outline_confirm = OutlineConfirmNode()
        self.quality_confirm = QualityConfirmNode()
        self.research_confirm = ResearchConfirmNode()
        self.image_confirm = ImageConfirmNode()

        # Agent 实例（延迟初始化）
        self._agents: dict[str, Any] = {}

        # 流水线上下文（跨阶段传递）
        self.context: dict[str, Any] = {}

    # ──────────────────────────────────────────────────────────────
    # Agent 懒加载
    # ──────────────────────────────────────────────────────────────

    def _get_agent(self, name: str):
        """懒加载 Agent 实例"""
        if name not in self._agents:
            if name == "planner":
                from agents.planner_agent import PlannerAgent
                self._agents[name] = PlannerAgent(hub=self.hub, llm_client=self.llm_client)
            elif name == "outline":
                from agents.outline_agent import OutlineAgent
                self._agents[name] = OutlineAgent(hub=self.hub, llm_client=self.llm_client)
            elif name == "writer":
                from agents.writer_agent import WriterAgent
                self._agents[name] = WriterAgent(hub=self.hub, llm_client=self.llm_client)
            elif name == "polisher":
                from agents.polisher_agent import PolisherAgent
                self._agents[name] = PolisherAgent(hub=self.hub, llm_client=self.llm_client)
            elif name == "research":
                from agents.research_agent import ResearchAgent
                self._agents[name] = ResearchAgent(
                    hub=self.hub,
                    llm_client=self.llm_client,
                    tavily_api_key=self.tavily_api_key,
                    obsidian_vault_path=self.obsidian_vault_path,
                )
            else:
                raise ValueError(f"Unknown agent: {name}")
        return self._agents[name]

    # ──────────────────────────────────────────────────────────────
    # 干线运行
    # ──────────────────────────────────────────────────────────────

    def run(self, topic: str, *, output_dir: str = None, article_dir: str = None) -> dict[str, Any]:
        """
        执行完整创作链路。

        Args:
            topic: 文章主题
            output_dir: 输出目录，默认 ./outputs/{timestamp}
            article_dir: 已发布文章目录（用于 ResearchAgent Obsidian 搜索）

        Returns:
            完整流水线结果，包含所有阶段的输出
        """
        session_id = f"lead-{int(time.time())}"
        self.hub.set_session(session_id)

        if self.dry_run:
            print(f"\n🔍 [干运行模式] 主题: {topic}")
            print(f"   将按顺序执行各阶段 Agent（不调用 LLM）")
            print()

        # 初始化上下文
        self.context["article_dir"] = article_dir

        # 初始化输出目录
        if output_dir is None:
            output_dir = f"./outputs/{int(time.time())}"
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # ── Stage 1: 主题策划 ─────────────────────────────────
        stage, stage_name, _ = self.STAGES[0]
        self._emit_status(stage, "running", f"开始策划: {topic}")

        planner = self._get_agent("planner")
        plan_result = planner.run({"topic": topic, "num_options": 3})

        if not plan_result.success:
            return self._error_result(stage, plan_result.error)

        plan_output = plan_result.output
        self.context["plan"] = plan_output

        # 确认节点①
        self._emit_status(stage, "waiting_confirm", "等待用户确认策划方案")
        confirm = self.plan_confirm.confirm(plan_output)
        if confirm.action == "revise":
            plan_output = confirm.revised_data
            self.context["plan"] = plan_output

        # ── Stage 2: 深度研究 ─────────────────────────────────
        stage, stage_name, _ = self.STAGES[1]
        self._emit_status(stage, "running", "开始深度研究")

        try:
            researcher = self._get_agent("research")
            research_result = researcher.run({
                "topic": plan_output.get("topic", topic),
                "unique_angle": plan_output.get("unique_angle", ""),
                "article_dir": self.context.get("article_dir"),
            })

            if research_result.success:
                research_output = research_result.output
                self.context["research"] = research_output

                # 确认节点②
                self._emit_status(stage, "waiting_confirm", "等待用户确认研究结果")
                confirm = self.research_confirm.confirm(research_output)
        except Exception as e:
            # ResearchAgent 尚不存在或出错，跳过研究阶段
            self._emit_status(stage, "skipped", f"研究阶段跳过: {e}")
            research_output = {"source": "skipped", "findings": [], "seo_keywords": {}}

        # ── Stage 3: 大纲规划 ─────────────────────────────────
        stage, stage_name, _ = self.STAGES[2]
        self._emit_status(stage, "running", "开始大纲规划")

        outline_agent = self._get_agent("outline")
        outline_result = outline_agent.run({
            "topic": plan_output.get("topic", topic),
            "target_audience": plan_output.get("target_audience", {}),
            "research": research_output,
            "num_h2": 7,
        })

        if not outline_result.success:
            return self._error_result(stage, outline_result.error)

        outline_output = outline_result.output
        self.context["outline"] = outline_output

        # 确认节点③
        self._emit_status(stage, "waiting_confirm", "等待用户确认大纲")
        confirm = self.outline_confirm.confirm(outline_output)
        if confirm.action == "revise":
            outline_output = confirm.revised_data
            self.context["outline"] = outline_output

        # ── Stage 4: 内容写作 ─────────────────────────────────
        stage, stage_name, _ = self.STAGES[3]
        self._emit_status(stage, "running", "开始内容写作")

        writer = self._get_agent("writer")
        writer_result = writer.run({
            "outline": outline_output,
            "target_audience": plan_output.get("target_audience", {}),
            "style_instructions": self.context.get("style_instructions", ""),
            "research": self.context.get("research"),
        })

        if not writer_result.success:
            return self._error_result(stage, writer_result.error)

        writer_output = writer_result.output
        self.context["draft"] = writer_output

        # ── Stage 5-6: 润色优化 + 质量审查循环 ─────────────────
        stage_polish, _, _ = self.STAGES[4]
        stage_review, _, _ = self.STAGES[5]

        retry_count = 0
        current_content = writer_output.get("content", "")
        seo_keywords = outline_output.get("seo_keywords", {})

        while True:
            self._emit_status(stage_polish, "running", f"开始第{retry_count + 1}次润色")

            polisher = self._get_agent("polisher")
            polish_result = polisher.run({
                "article": current_content,
                "seo_keywords": seo_keywords,
                "retry_count": retry_count,
            })

            if not polish_result.success:
                return self._error_result(stage_polish, polish_result.error)

            polished_article = polish_result.output["polished_article"]
            h_report_dict = polish_result.output["humanizer_report"]
            a_report_dict = polish_result.output["anti_slop_report"]

            # 质量审查
            self._emit_status(stage_review, "running", "开始质量审查")
            from core.review_gate import review_article
            gate_passed, q_report = review_article(
                polished_article,
                llm_client=self.llm_client,
                retry_count=retry_count,
            )

            # 确认节点④
            self._emit_status(stage_review, "waiting_confirm", f"等待用户确认质量报告（第{retry_count + 1}次）")
            confirm = self.quality_confirm.confirm(q_report, retry_count)

            if confirm.action == "accept":
                current_content = polished_article
                self.context["quality_report"] = q_report
                break

            elif confirm.action == "repolish":
                current_content = polished_article
                retry_count += 1
                if retry_count > 2:
                    self._emit_status(stage_review, "max_retries", "已达最大润色次数，进入排版")
                    self.context["quality_report"] = q_report
                    break

            else:  # quit
                return self._success_result(output_path, reason="user_quit")

        # ── Stage 7: 配图封面 ────────────────────────────────
        stage, stage_name, _ = self.STAGES[6]
        self._emit_status(stage, "skipped", "配图封面（Phase 2）")
        image_output = {"status": "pending", "cover": {}, "image_ideas": []}
        self.context["image"] = image_output

        # 确认节点⑤（Phase 2 实现）
        # confirm = self.image_confirm.confirm(image_output)

        # ── Stage 8: 排版输出 ────────────────────────────────
        stage, stage_name, _ = self.STAGES[7]
        self._emit_status(stage, "running", "保存输出文件")

        self._save_outputs(output_path, current_content, writer_output, q_report)

        return self._success_result(output_path)

    # ──────────────────────────────────────────────────────────────
    # 工具方法
    # ──────────────────────────────────────────────────────────────

    def _emit_status(self, stage: str, status: str, message: str = ""):
        """向 MessageHub 发送状态消息"""
        print(f"  [{stage.upper()}] {status.upper()} {message}")
        self.hub.publish(Message(
            type=MessageType.STATUS,
            agent=self.name,
            content={
                "stage": stage,
                "status": status,
                "message": message,
                "timestamp": time.time(),
            }
        ))

    def _error_result(self, stage: str, error: str) -> dict:
        """生成错误结果"""
        self._emit_status(stage, "failed", error)
        self.hub.publish(Message(
            type=MessageType.ERROR,
            agent=self.name,
            content={"stage": stage, "error": error}
        ))
        return {
            "success": False,
            "stage": stage,
            "error": error,
            "context": self.context,
        }

    def _success_result(self, output_path: Path, reason: str = "completed") -> dict:
        """生成成功结果"""
        self._emit_status("lead", "completed", reason)
        return {
            "success": True,
            "reason": reason,
            "output_dir": str(output_path),
            "context": self.context,
        }

    def _save_outputs(
        self,
        output_path: Path,
        polished_content: str,
        writer_output: dict,
        q_report,
    ):
        """保存所有输出文件"""
        # 润色稿
        polished_path = output_path / "polished.md"
        polished_path.write_text(polished_content, encoding="utf-8")

        # 初稿
        draft_content = writer_output.get("content", "")
        if draft_content and draft_content != polished_content:
            draft_path = output_path / "draft.md"
            draft_path.write_text(draft_content, encoding="utf-8")

        # 质量报告
        q_path = output_path / "quality_report.json"
        q_path.write_text(json.dumps(q_report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

        # 元数据
        meta = {
            "title": writer_output.get("title", "无标题"),
            "plan": self.context.get("plan", {}),
            "outline": self.context.get("outline", {}),
            "quality_report": q_report.to_dict(),
            "polish_retry_count": q_report.retry_count,
            "session_id": self.hub._session_id,
        }
        meta_path = output_path / "meta.json"
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"\n💾 输出已保存: {output_path}")

    def get_pipeline_status(self) -> dict:
        """获取当前流水线状态（供调试用）"""
        return self.hub.get_status()

    def set_style_instructions(self, instructions: str):
        """设置风格写作指令（供 CLI 外部调用）"""
        self.context["style_instructions"] = instructions