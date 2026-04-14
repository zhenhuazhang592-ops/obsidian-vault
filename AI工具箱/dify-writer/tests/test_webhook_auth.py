# Tests: Webhook Bearer Token Authentication
"""
测试 Webhook 端点的 Bearer Token 认证
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os

from fastapi import HTTPException


class TestWebhookAuth:
    """Test webhook Bearer token authentication."""

    @pytest.mark.asyncio
    async def test_hitl_endpoint_rejects_missing_token(self):
        """Test that /hitl without token is rejected when token is configured."""
        # 临时设置环境变量
        with patch.dict(os.environ, {"DIFY_WEBHOOK_BEARER_TOKEN": "secret123"}):
            # 重新导入以读取新的 env
            import importlib
            import dify_api.webhook as webhook_module
            importlib.reload(webhook_module)

            from dify_api.webhook import handle_hitl_callback

            payload = {"hitl_type": "strategy"}

            with pytest.raises(HTTPException) as exc_info:
                await handle_hitl_callback(payload, authorization=None)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_hitl_endpoint_rejects_wrong_token(self):
        """Test that /hitl with wrong token is rejected."""
        with patch.dict(os.environ, {"DIFY_WEBHOOK_BEARER_TOKEN": "secret123"}):
            import importlib
            import dify_api.webhook as webhook_module
            importlib.reload(webhook_module)

            from dify_api.webhook import handle_hitl_callback

            payload = {"hitl_type": "strategy"}

            with pytest.raises(HTTPException) as exc_info:
                await handle_hitl_callback(payload, authorization="Bearer wrongtoken")

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_hitl_endpoint_accepts_valid_token(self):
        """Test that /hitl with correct token passes."""
        with patch.dict(os.environ, {"DIFY_WEBHOOK_BEARER_TOKEN": "secret123"}):
            import importlib
            import dify_api.webhook as webhook_module
            importlib.reload(webhook_module)

            from dify_api.webhook import handle_hitl_callback

            # Mock the handler
            payload = {
                "hitl_type": "strategy",
                "action": "get_card",
                "context": {},
            }

            mock_result = {"card": "测试卡片"}
            with patch.object(webhook_module.get_handler(), "build_confirm_card", return_value="测试卡片"):
                result = await handle_hitl_callback(payload, authorization="Bearer secret123")

            assert result == {"card": "测试卡片"}

    @pytest.mark.asyncio
    async def test_hitl_endpoint_no_auth_when_token_not_set(self):
        """Test that /hitl allows no token when DIFY_WEBHOOK_BEARER_TOKEN is not set."""
        # 确保环境变量不存在
        env_without_token = {k: v for k, v in os.environ.items() if k != "DIFY_WEBHOOK_BEARER_TOKEN"}
        with patch.dict(os.environ, env_without_token, clear=False):
            try:
                del os.environ["DIFY_WEBHOOK_BEARER_TOKEN"]
            except KeyError:
                pass

            import importlib
            import dify_api.webhook as webhook_module
            importlib.reload(webhook_module)

            from dify_api.webhook import handle_hitl_callback

            payload = {
                "hitl_type": "strategy",
                "action": "get_card",
                "context": {},
            }

            with patch.object(webhook_module.get_handler(), "build_confirm_card", return_value="测试卡片"):
                result = await handle_hitl_callback(payload, authorization=None)

            assert result == {"card": "测试卡片"}


class TestSessionStatusEndpoint:
    """Test /sessions/{session_id}/status endpoint."""

    @pytest.mark.asyncio
    async def test_session_status_returns_503_when_pipeline_not_set(self):
        """Test that /sessions/status returns 503 when pipeline is None."""
        from dify_api.webhook import HITLHandler, get_session_status
        from fastapi import HTTPException

        handler = HITLHandler(pipeline=None)

        with patch("dify_api.webhook.get_handler", return_value=handler):
            with pytest.raises(HTTPException) as exc_info:
                await get_session_status("sess_001")

            assert exc_info.value.status_code == 503
            assert "Pipeline not configured" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_session_status_returns_pipeline_status(self):
        """Test that /sessions/status returns pipeline status."""
        from dify_api.webhook import HITLHandler, get_session_status

        mock_pipeline = MagicMock()
        mock_pipeline.get_status = AsyncMock(
            return_value={"status": "running", "phase": "writing", "quality_score": 82}
        )
        handler = HITLHandler(pipeline=mock_pipeline)

        with patch("dify_api.webhook.get_handler", return_value=handler):
            result = await get_session_status("sess_001")

        assert result["status"] == "running"
        assert result["phase"] == "writing"
        assert result["quality_score"] == 82
