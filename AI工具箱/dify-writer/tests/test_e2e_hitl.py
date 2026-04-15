# E2E tests: Full HITL flow
"""
端到端 HITL 流程测试
测试从 Dify HITL 触发 → MCP Server Webhook → Resume 的完整流程
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from dify_api.client import DifyClient, DifyConfig
from dify_api.webhook import HITLHandler, get_handler, set_pipeline


class TestHITLEndToEndFlow:
    """Test the complete HITL flow."""

    @pytest.fixture
    def mock_pipeline(self):
        """Mock pipeline that tracks deliver_hitl_response calls."""
        pipeline = MagicMock()
        pipeline.deliver_hitl_response = AsyncMock(
            return_value={
                "_hitl_last": {
                    "approved": True,
                    "feedback": "ok",
                    "strategy": "ok",
                }
            }
        )
        pipeline.get_status = AsyncMock(
            return_value={"status": "running", "phase": "writing"}
        )
        return pipeline

    @pytest.mark.asyncio
    async def test_hitl_approve_flow(self, mock_pipeline):
        """
        Full HITL approval flow:
        1. Dify triggers /hitl with hitl_type=strategy
        2. Handler calls pipeline.deliver_hitl_response
        3. Returns approved=True
        """
        set_pipeline(mock_pipeline)

        # Simulate Dify calling /hitl with user approval
        payload = {
            "hitl_type": "strategy",
            "session_id": "sess_001",
            "user_response": "开始",
            "action": "approve",
            "context": {
                "topic": "AI写作趋势",
                "platform": "wechat",
            },
        }

        handler = get_handler()
        result = await handler.handle("strategy", payload)

        assert result.approved is True
        assert "feedback" in dir(result) or hasattr(result, "feedback")

        mock_pipeline.deliver_hitl_response.assert_called_once_with(
            confirm_type="strategy",
            human_response="开始",
        )

    @pytest.mark.asyncio
    async def test_hitl_reject_flow(self, mock_pipeline):
        """Test HITL rejection flow."""
        mock_pipeline.deliver_hitl_response = AsyncMock(
            return_value={
                "_hitl_last": {
                    "approved": False,
                    "feedback": "需要调整大纲结构",
                }
            }
        )
        set_pipeline(mock_pipeline)

        payload = {
            "hitl_type": "outline",
            "session_id": "sess_001",
            "user_response": "需要调整",
            "action": "reject",
        }

        handler = get_handler()
        result = await handler.handle("outline", payload)

        assert result.approved is False
        assert result.feedback == "需要调整大纲结构"

    @pytest.mark.asyncio
    async def test_hitl_without_pipeline_raises(self):
        """Test that HITL handler raises if pipeline is not set."""
        handler = get_handler()
        handler.pipeline = None

        payload = {"hitl_type": "strategy", "session_id": "sess_001"}

        from fastapi import HTTPException
        with pytest.raises((RuntimeError, HTTPException)):
            await handler.handle("strategy", payload)


class TestBuildConfirmCard:
    """Test confirm card generation."""

    def test_strategy_confirm_card(self):
        """Test strategy confirm card content."""
        handler = HITLHandler()
        card = handler.build_confirm_card(
            "strategy",
            {
                "topic": "AI写作趋势",
                "platform": "wechat",
                "framework": "PMP四步法",
                "theme": "科技前沿",
            },
        )

        assert "创作策略确认" in card
        assert "AI写作趋势" in card
        assert "wechat" in card
        assert "PMP四步法" in card

    def test_outline_confirm_card(self):
        """Test outline confirm card content."""
        handler = HITLHandler()
        card = handler.build_confirm_card(
            "outline",
            {
                "outline": {
                    "title": "AI写作的未来",
                    "sections": [
                        {"title": "背景介绍"},
                        {"title": "核心技术"},
                        {"title": "应用场景"},
                    ],
                }
            },
        )

        assert "大纲确认" in card
        assert "AI写作的未来" in card
        assert "背景介绍" in card
        assert "核心技术" in card

    def test_final_preview_confirm_card(self):
        """Test final preview confirm card content."""
        handler = HITLHandler()
        card = handler.build_confirm_card(
            "final_preview",
            {
                "quality_score": 88,
                "word_count": 3200,
                "inline_images": ["img1.jpg", "img2.jpg", "img3.jpg"],
            },
        )

        assert "创作完成" in card
        assert "88" in card
        assert "3200" in card

    def test_unknown_hitl_type(self):
        """Test unknown HITL type returns fallback."""
        handler = HITLHandler()
        card = handler.build_confirm_card("unknown_type", {})
        assert "未知确认类型" in card


class TestDifyClientHITLTrigger:
    """Test that DifyClient properly tracks HITL metrics."""

    @pytest.mark.asyncio
    async def test_hitl_metrics_incremented_on_resume(self):
        """Test that hitl_triggered metric increments when resume_from_hitl is called."""
        config = DifyConfig(api_key="test-key")
        client = DifyClient(config)

        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"data": {"status": "completed"}}),
            )

            await client.resume_from_hitl(
                task_id="task_hitl_001",
                action="approve",
            )

        assert client.metrics.hitl_triggered == 1

    @pytest.mark.asyncio
    async def test_multiple_hitl_sessions_counted(self):
        """Test multiple HITL resumes are all counted."""
        config = DifyConfig(api_key="test-key")
        client = DifyClient(config)

        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"data": {}}),
            )

            # Simulate 3 HITL confirmations (strategy, outline, final_preview)
            for _ in range(3):
                await client.resume_from_hitl(task_id="task_001", action="approve")

        assert client.metrics.hitl_triggered == 3
