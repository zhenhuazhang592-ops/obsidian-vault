# Tests: Dify Webhook Handler
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from dify_api.webhook import (
    HITLHandler,
    HITLPayload,
    HITLResponse,
)


class TestHITLPayload:
    """Tests for HITLPayload dataclass."""

    def test_payload_creation(self):
        """Test creating HITL payload."""
        payload = HITLPayload(
            session_id="sess_001",
            conversation_id="conv_001",
            hitl_type="strategy",
            user_response="确认，开始执行",
            context={"topic": "测试主题"},
        )

        assert payload.session_id == "sess_001"
        assert payload.conversation_id == "conv_001"
        assert payload.hitl_type == "strategy"
        assert payload.user_response == "确认，开始执行"
        assert payload.context["topic"] == "测试主题"


class TestHITLResponse:
    """Tests for HITLResponse dataclass."""

    def test_approved_response(self):
        """Test approved HITL response."""
        response = HITLResponse(
            approved=True,
            updates={"framework": "痛点型"},
            feedback="",
        )

        assert response.approved is True
        assert response.updates["framework"] == "痛点型"
        assert response.feedback == ""

    def test_rejected_response(self):
        """Test rejected HITL response."""
        response = HITLResponse(
            approved=False,
            updates={},
            feedback="主题需要修改，请调整为AI编程",
        )

        assert response.approved is False
        assert response.feedback == "主题需要修改，请调整为AI编程"


class TestHITLHandlerInit:
    """Tests for HITLHandler initialization."""

    def test_handler_without_pipeline(self):
        """Test handler initialized without pipeline."""
        handler = HITLHandler()
        assert handler.pipeline is None

    def test_handler_with_pipeline(self):
        """Test handler initialized with pipeline."""
        mock_pipeline = MagicMock()
        handler = HITLHandler(pipeline=mock_pipeline)
        assert handler.pipeline == mock_pipeline


class TestHITLHandlerSetPipeline:
    """Tests for HITLHandler.set_pipeline()."""

    def test_set_pipeline(self):
        """Test setting pipeline after initialization."""
        handler = HITLHandler()
        mock_pipeline = MagicMock()

        handler.set_pipeline(mock_pipeline)

        assert handler.pipeline == mock_pipeline


class TestHITLHandlerBuildConfirmCard:
    """Tests for HITLHandler.build_confirm_card()."""

    def test_strategy_confirm_card(self):
        """Test strategy confirmation card content."""
        handler = HITLHandler()
        context = {
            "topic": "AI编程的未来",
            "platform": "wechat",
            "framework": "痛点型",
            "theme": "professional-clean",
        }

        card = handler.build_confirm_card("strategy", context)

        assert "AI编程的未来" in card
        assert "wechat" in card
        assert "痛点型" in card

    def test_outline_confirm_card(self):
        """Test outline confirmation card content."""
        handler = HITLHandler()
        context = {
            "topic": "AI编程的未来",
            "outline": {
                "title": "AI编程浪潮下我们该何去何从",
                "sections": [
                    {"title": "开头", "word_count": 150},
                    {"title": "痛点放大", "word_count": 300},
                ],
            },
        }

        card = handler.build_confirm_card("outline", context)

        assert "AI编程浪潮下我们该何去何从" in card
        assert "开头" in card
        assert "痛点放大" in card

    def test_final_preview_confirm_card(self):
        """Test final preview confirmation card content."""
        handler = HITLHandler()
        context = {
            "topic": "AI编程的未来",
            "quality_score": 88,
            "word_count": 2500,
            "inline_images": [
                {"position": "第3段后", "url": "https://example.com/img1.jpg"}
            ],
        }

        card = handler.build_confirm_card("final_preview", context)

        assert "创作完成" in card
        assert "88" in card


class TestHITLHandlerAsyncHandle:
    """Tests for HITLHandler.handle() (async)."""

    @pytest.mark.asyncio
    async def test_handle_without_pipeline_raises(self):
        """Test handle when pipeline not set raises RuntimeError."""
        handler = HITLHandler()
        payload = {
            "session_id": "sess_001",
            "conversation_id": "conv_001",
            "user_response": "确认",
        }

        with pytest.raises(RuntimeError, match="Pipeline not set"):
            await handler.handle("strategy", payload)

    @pytest.mark.asyncio
    async def test_handle_with_pipeline_approve(self):
        """Test handle with pipeline approval."""
        mock_pipeline = AsyncMock()
        mock_pipeline.deliver_hitl_response = AsyncMock(return_value={
            "_hitl_last": {"approved": True, "feedback": ""},
        })

        handler = HITLHandler(pipeline=mock_pipeline)
        payload = {
            "session_id": "sess_001",
            "conversation_id": "conv_001",
            "user_response": "确认，开始",
        }

        response = await handler.handle("strategy", payload)

        assert response.approved is True
        mock_pipeline.deliver_hitl_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_with_pipeline_reject(self):
        """Test handle with pipeline rejection."""
        mock_pipeline = AsyncMock()
        mock_pipeline.deliver_hitl_response = AsyncMock(return_value={
            "_hitl_last": {"approved": False, "feedback": "需要修改主题"},
        })

        handler = HITLHandler(pipeline=mock_pipeline)
        payload = {
            "session_id": "sess_001",
            "conversation_id": "conv_001",
            "user_response": "主题改为AI编程趋势",
        }

        response = await handler.handle("strategy", payload)

        assert response.approved is False
        assert "需要修改主题" in response.feedback
