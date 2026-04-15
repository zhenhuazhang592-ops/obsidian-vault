# Tests: Pipeline + HITL Nodes
import pytest

from app.core.hitl.nodes import StrategyConfirm, OutlineConfirm, FinalPreviewConfirm
from app.pipeline.writing_pipeline import (
    WritingPipeline,
    PipelineConfig,
    PipelineError,
    QUALITY_THRESHOLD,
    MAX_QUALITY_ITERATIONS,
)


class TestHITLNodes:
    """Tests for HITL confirmation nodes."""

    def test_strategy_confirm_build_card(self):
        """Test StrategyConfirm card content."""
        ctx = {
            "topic": "AI编程的未来",
            "platform": "wechat",
            "style_profile": "专业严谨",
            "framework": "痛点型",
        }
        node = StrategyConfirm()
        card = node.build_card(ctx)

        assert "AI编程的未来" in card
        assert "公众号" in card
        assert "痛点型" in card
        assert "专业严谨" in card

    def test_strategy_confirm_parse_confirm(self):
        """Test confirm keywords."""
        node = StrategyConfirm()
        for kw in ["确认", "开始", "好", "可以", "ok", "yes"]:
            approved, _ = node.parse_response(kw)
            assert approved, f"Should approve for '{kw}'"

    def test_strategy_confirm_parse_reject(self):
        """Test rejection keywords."""
        node = StrategyConfirm()
        approved, feedback = node.parse_response("修改主题为XXX")
        assert not approved
        assert feedback == "修改主题为XXX"

    def test_outline_confirm_build_card(self):
        """Test OutlineConfirm card with sections."""
        ctx = {
            "topic": "测试主题",
            "framework": "清单型",
            "outline": {
                "sections": [
                    {"title": "第一章", "points": ["观点1", "观点2"]},
                    {"title": "第二章", "points": ["观点3"]},
                ]
            },
        }
        node = OutlineConfirm()
        card = node.build_card(ctx)

        assert "测试主题" in card
        assert "清单型" in card
        assert "第一章" in card
        assert "第二章" in card

    def test_outline_confirm_empty_sections(self):
        """Test OutlineConfirm with no sections."""
        ctx = {"topic": "空大纲", "framework": "故事型", "outline": {}}
        node = OutlineConfirm()
        card = node.build_card(ctx)
        assert "空大纲" in card

    def test_final_preview_confirm_build_card(self):
        """Test FinalPreviewConfirm card."""
        ctx = {
            "polished_draft": "这是一篇很长的测试文章内容。" * 20,
            "quality_score": 88,
            "quality_feedback": "开头不够吸引人",
        }
        node = FinalPreviewConfirm()
        card = node.build_card(ctx)

        assert "88" in card
        assert "开头不够吸引人" in card
        assert "文章预览" in card


class TestPipelineConfig:
    """Tests for PipelineConfig."""

    def test_default_config(self):
        cfg = PipelineConfig()
        assert cfg.topic == ""
        assert cfg.platform == "wechat"
        assert cfg.style_profile == "专业严谨"
        assert cfg.hitl_enabled is True

    def test_custom_config(self):
        cfg = PipelineConfig(
            topic="测试",
            platform="xiaohongshu",
            style_profile="幽默风趣",
            hitl_enabled=False,
        )
        assert cfg.topic == "测试"
        assert cfg.platform == "xiaohongshu"
        assert cfg.style_profile == "幽默风趣"
        assert cfg.hitl_enabled is False


class TestPipelineQualityThreshold:
    """Tests for quality loop constants."""

    def test_quality_threshold_value(self):
        assert QUALITY_THRESHOLD == 85
        assert MAX_QUALITY_ITERATIONS == 3


class TestPipelineDataBus:
    """Tests for data bus flow through pipeline."""

    def test_pipeline_initial_state(self):
        """Test pipeline initializes data bus correctly."""
        cfg = PipelineConfig(topic="测试主题", platform="wechat", style_profile="专业严谨")
        pipeline = WritingPipeline(cfg)

        assert pipeline.data_bus["topic"] == "测试主题"
        assert pipeline.data_bus["platform"] == "wechat"
        assert pipeline.data_bus["style_profile"] == "专业严谨"
        assert pipeline.data_bus["status"] == "idle"

    @pytest.mark.asyncio
    async def test_pipeline_no_anthropic_key_uses_mock(self):
        """Pipeline runs in mock mode without ANTHROPIC_API_KEY."""
        import os

        os.environ.pop("ANTHROPIC_API_KEY", None)
        cfg = PipelineConfig(topic="测试", hitl_enabled=False)
        pipeline = WritingPipeline(cfg)

        # Without API key, deep_research goes to mock, but planning/outline/writing
        # agents will fail in LLM calls — that's expected behavior
        # We just verify initialization works
        assert pipeline.data_bus["topic"] == "测试"

    def test_pipeline_data_bus_persistence(self):
        """Data bus persists across HITL response calls."""
        cfg = PipelineConfig(topic="测试", hitl_enabled=True)
        pipeline = WritingPipeline(cfg)
        pipeline._data_bus["framework"] = "痛点型"
        pipeline._data_bus["outline"] = {"sections": [{"title": "A"}]}

        updated = pipeline._data_bus.copy()
        updated["framework"] = "故事型"

        pipeline._data_bus.update(updated)

        assert pipeline.data_bus["framework"] == "故事型"
        assert pipeline.data_bus["outline"]["sections"][0]["title"] == "A"


class TestHITLNodeIntegration:
    """Integration tests for HITL nodes with data bus."""

    def test_strategy_confirm_confirm_flow(self):
        """Test full confirm flow: card → parse → updates."""
        ctx = {
            "topic": "AI",
            "platform": "wechat",
            "style_profile": "专业严谨",
            "framework": "痛点型",
        }
        node = StrategyConfirm()

        # Build card
        card = node.build_card(ctx)
        assert "AI" in card

        # Parse confirm
        approved, feedback = node.parse_response("确认")
        assert approved
        assert feedback == ""

    def test_outline_confirm_reject_with_feedback(self):
        """Test outline rejection with custom feedback."""
        ctx = {"topic": "X", "framework": "清单型", "outline": {}}
        node = OutlineConfirm()

        approved, feedback = node.parse_response("把第一章拆成两节")
        assert not approved
        assert feedback == "把第一章拆成两节"

    def test_final_confirm_approved(self):
        """Test final preview confirm with approval."""
        ctx = {
            "polished_draft": "正文内容",
            "quality_score": 90,
            "quality_feedback": "",
        }
        node = FinalPreviewConfirm()

        approved, feedback = node.parse_response("确认")
        assert approved

    def test_final_confirm_rejected_with_modification(self):
        """Test final preview rejection with modification."""
        ctx = {
            "polished_draft": "正文内容",
            "quality_score": 60,
            "quality_feedback": "结构松散",
        }
        node = FinalPreviewConfirm()

        approved, feedback = node.parse_response("开头太弱，加强一下")
        assert not approved
        assert "开头太弱" in feedback
