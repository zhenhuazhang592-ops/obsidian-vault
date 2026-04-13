# core/confirm_nodes.py - 用户确认节点
# Phase 1: 标准化确认节点，支撑 6 个交互确认点

from typing import Any, Protocol
from dataclasses import dataclass


@dataclass
class ConfirmResult:
    """确认结果"""
    action: str          # "accept" | "revise" | "quit"
    revised_data: dict   # 如果 action == "revise"，包含修改后的数据
    retry_count: int = 0  # 当前重试次数


class ConfirmNode(Protocol):
    """确认节点协议"""
    def print_summary(self, output: Any) -> None:
        """打印摘要供用户审阅"""
        ...

    def confirm(self, output: Any) -> ConfirmResult:
        """执行确认流程"""
        ...


# ────────────────────────────────────────────────────────────────
# PlanConfirmNode — 主题策划确认节点
# ────────────────────────────────────────────────────────────────

class PlanConfirmNode:
    """主题策划确认节点"""

    def print_summary(self, plan: dict) -> None:
        import json
        print()
        print("=" * 60)
        print("📋 主题策划方案")
        print("=" * 60)

        is_template = plan.get("is_template", False)
        if is_template:
            llm_error = plan.get("llm_error", "")
            print("⚠️  模板模式（未配置 LLM）")
            if llm_error:
                print(f"   LLM 错误：{llm_error}")
            print()

        print(f"📌 主题：{plan.get('topic', '')}")
        print()

        ta = plan.get("target_audience", {})
        if isinstance(ta, dict):
            print(f"👤 目标读者：{ta.get('persona', '')}")
            pps = ta.get('pain_points', [])
            if pps:
                print(f"   痛点：{', '.join(str(p) for p in pps)}")

        print(f"🔍 独特角度：{plan.get('unique_angle', '')}")
        print(f"💡 内容承诺：{plan.get('content_promise', '')}")
        print(f"🎯 内容调性：{plan.get('tone', '')}")

        titles = plan.get("title_options", [])
        if titles:
            print()
            print("📣 标题选项：")
            for i, t in enumerate(titles, 1):
                print(f"   {i}. {t}")

    def confirm(self, plan: dict) -> ConfirmResult:
        """
        用户确认/修改策划方案。

        操作选项：
          直接回车 — 接受当前方案
          r        — 重新生成（需要配置 DASHSCOPE_API_KEY）
          m        — 修改主题
          q        — 退出

        Returns:
            ConfirmResult(action="accept"|"revise"|"quit", revised_data=plan, retry_count=0)
        """
        self.print_summary(plan)
        print()
        print("─" * 40)
        print("操作选项：")
        print("  直接回车 — 接受当前方案")
        print("  r       — 重新生成（需要配置 DASHSCOPE_API_KEY）")
        print("  m       — 修改主题")
        print("  q       — 退出")
        print()

        import sys
        choice = input("请选择 [直接回车接受]: ").strip().lower()

        if choice == "q":
            print("\n已退出。")
            sys.exit(0)
        elif choice == "r":
            print("\n重新生成需要配置 LLM，请设置 DASHSCOPE_API_KEY 环境变量。")
            print("当前使用模板方案，继续进行...")
            return ConfirmResult(action="accept", revised_data=plan)
        elif choice == "m":
            new_topic = input("请输入新主题: ").strip()
            if new_topic:
                plan = dict(plan)  # 浅拷贝
                plan["topic"] = new_topic
                print(f"✅ 主题已更新: {new_topic}")
            return ConfirmResult(action="accept", revised_data=plan)
        else:
            return ConfirmResult(action="accept", revised_data=plan)


# ────────────────────────────────────────────────────────────────
# OutlineConfirmNode — 大纲规划确认节点
# ────────────────────────────────────────────────────────────────

class OutlineConfirmNode:
    """大纲规划确认节点"""

    def print_summary(self, outline: dict) -> None:
        print()
        print("=" * 60)
        print("📐 文章大纲")
        print("=" * 60)

        is_template = outline.get("is_template", False)
        if is_template:
            print("⚠️  模板模式（未配置 LLM）")
            print()

        title = outline.get("title", "")
        seo = outline.get("seo_keywords", {})
        print(f"📌 标题：{title}")
        print(f"🔑 核心关键词：{seo.get('primary', '')}")
        print(f"   次要关键词：{', '.join(seo.get('secondary', []))}")
        print()

        hook = outline.get("opening_hook", "")
        if hook:
            print(f"🪝 开头钩子：{hook}")
            print()

        outline_items = outline.get("outline", [])
        for i, item in enumerate(outline_items, 1):
            h2 = item.get("h2", "")
            points = item.get("key_points", [])
            wt = item.get("word_target", 0)
            print(f"  {i}. {h2}  (~{wt}字)")
            for p in points:
                print(f"     - {p}")
            print()

    def confirm(self, outline: dict) -> ConfirmResult:
        """
        用户确认/修改大纲。

        操作选项：
          直接回车 — 接受当前大纲，继续写作
          q        — 退出

        Returns:
            ConfirmResult(action="accept"|"quit", revised_data=outline, retry_count=0)
        """
        self.print_summary(outline)
        print()
        print("─" * 40)
        print("操作选项：")
        print("  直接回车 — 接受当前大纲，继续写作")
        print("  q        — 退出")
        print()

        import sys
        choice = input("请选择 [直接回车继续]: ").strip().lower()

        if choice == "q":
            print("\n已退出。")
            sys.exit(0)

        return ConfirmResult(action="accept", revised_data=outline)


# ────────────────────────────────────────────────────────────────
# QualityConfirmNode — 质量报告确认节点
# ────────────────────────────────────────────────────────────────

class QualityConfirmNode:
    """质量报告确认节点"""

    def print_summary(self, q_report, retry_count: int = 0) -> None:
        print()
        print("=" * 60)
        print("🔍 质量评分报告（第{}次润色后）".format(retry_count + 1))
        print("=" * 60)
        print(q_report.format_summary())
        print()
        print("=" * 60)
        print(f"雷达图数据：{q_report.radar_labels}")
        print(f"维度分数：{[round(s, 1) for s in q_report.radar_scores]}")
        print()

    def confirm(self, q_report, retry_count: int = 0) -> ConfirmResult:
        """
        用户确认质量报告。

        操作选项（动态，根据质量状态）：
          达标（≥85）：直接回车进入排版，r强制重新润色
          未达标（<85）：直接回车触发自动重新润色
          达最大次数（2次）：人工决策

        Returns:
            ConfirmResult(action="accept"|"repolish"|"quit", retry_count=current)
        """
        import sys

        print()
        print("─" * 40)
        print("操作选项：")

        if q_report.gate_passed:
            print("  ✅ 质量达标 — 直接回车进入排版输出")
            print("  r           — 强制重新润色（手动优化）")
        elif q_report.needs_human_decision:
            print("  ⚠️  已达最大重试次数(2次)，需人工决策")
            print("  直接回车 — 接受当前版本，进入排版")
            print("  r        — 强制重新润色")
            print("  q        — 退出，保存当前版本")
        else:
            remaining = 2 - q_report.retry_count
            print(f"  ⚠️  质量未达标（{q_report.weighted_score:.1f} < 85），将自动重新润色")
            print(f"  剩余自动润色次数：{remaining}次")
            print("  直接回车 — 继续自动润色流程")
            print("  q        — 退出，保存当前版本")

        print()
        choice = input("请选择 [直接回车]: ").strip().lower()

        if choice == "q":
            return ConfirmResult(action="quit", revised_data={}, retry_count=retry_count)
        elif choice == "r":
            return ConfirmResult(action="repolish", revised_data={}, retry_count=retry_count)
        else:
            if q_report.gate_passed or q_report.needs_human_decision:
                return ConfirmResult(action="accept", revised_data={}, retry_count=retry_count)
            else:
                return ConfirmResult(action="repolish", revised_data={}, retry_count=retry_count)


# ────────────────────────────────────────────────────────────────
# ResearchConfirmNode — 研究结果确认节点
# ────────────────────────────────────────────────────────────────

class ResearchConfirmNode:
    """深度研究结果确认节点"""

    def print_summary(self, research_output: dict) -> None:
        print()
        print("=" * 60)
        print("🔬 深度研究报告")
        print("=" * 60)

        source = research_output.get("source", "unknown")
        print(f"📚 信息来源：{source}")
        print()

        findings = research_output.get("findings", [])
        if findings:
            print(f"📊 关键发现（{len(findings)}条）：")
            for i, f in enumerate(findings[:5], 1):
                print(f"  {i}. {f}")
            if len(findings) > 5:
                print(f"  ... 还有 {len(findings) - 5} 条")
            print()

        seo_keywords = research_output.get("seo_keywords", {})
        if seo_keywords:
            print(f"🔑 SEO关键词：")
            print(f"   核心词：{seo_keywords.get('primary', '')}")
            print(f"   长尾词：{', '.join(seo_keywords.get('secondary', []))}")
            print()

    def confirm(self, research_output: dict) -> ConfirmResult:
        """
        用户确认研究结果。

        操作选项：
          直接回车 — 接受研究结果，继续大纲规划
          q        — 退出

        Returns:
            ConfirmResult(action="accept"|"quit", revised_data=research_output, retry_count=0)
        """
        self.print_summary(research_output)
        print()
        print("─" * 40)
        print("操作选项：")
        print("  直接回车 — 接受研究结果，继续大纲规划")
        print("  q        — 退出")
        print()

        import sys
        choice = input("请选择 [直接回车继续]: ").strip().lower()

        if choice == "q":
            print("\n已退出。")
            sys.exit(0)

        return ConfirmResult(action="accept", revised_data=research_output)


# ────────────────────────────────────────────────────────────────
# ImageConfirmNode — 配图方案确认节点
# ────────────────────────────────────────────────────────────────

class ImageConfirmNode:
    """配图封面确认节点"""

    def print_summary(self, image_output: dict) -> None:
        print()
        print("=" * 60)
        print("🖼️  配图封面方案")
        print("=" * 60)

        cover = image_output.get("cover", {})
        if cover:
            print(f"🎨 封面色系：{cover.get('color_palette', '')}")
            print(f"📐 封面尺寸：{cover.get('size', '')}")
            print(f"📝 封面文案：{cover.get('headline', '')}")
            print()

        image_ideas = image_output.get("image_ideas", [])
        if image_ideas:
            print(f"🖼️  内文配图建议（{len(image_ideas)}张）：")
            for i, idea in enumerate(image_ideas[:3], 1):
                print(f"  {i}. {idea.get('description', idea.get('location', '图片' + str(i)))}")
            print()

    def confirm(self, image_output: dict) -> ConfirmResult:
        """
        用户确认配图方案。

        操作选项：
          直接回车 — 接受配图方案，继续排版输出
          q        — 退出

        Returns:
            ConfirmResult(action="accept"|"quit", revised_data=image_output, retry_count=0)
        """
        self.print_summary(image_output)
        print()
        print("─" * 40)
        print("操作选项：")
        print("  直接回车 — 接受配图方案，继续排版输出")
        print("  q        — 退出")
        print()

        import sys
        choice = input("请选择 [直接回车继续]: ").strip().lower()

        if choice == "q":
            print("\n已退出。")
            sys.exit(0)

        return ConfirmResult(action="accept", revised_data=image_output)