# Tests: Dify API Client
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from dify_api.client import DifyClient, DifyConfig, DifyClientError


class TestDifyConfig:
    """Tests for DifyConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = DifyConfig(api_key="test-key")
        assert config.api_key == "test-key"
        assert config.base_url == "https://api.dify.ai/v1"
        assert config.timeout == 60.0
        assert config.max_retries == 3
        assert config.retry_base_delay == 1.0

    def test_custom_values(self):
        """Test custom configuration values."""
        config = DifyConfig(
            api_key="custom-key",
            base_url="https://custom.dify.ai/v1",
            timeout=120.0,
            max_retries=5,
            retry_base_delay=2.0,
        )
        assert config.api_key == "custom-key"
        assert config.base_url == "https://custom.dify.ai/v1"
        assert config.timeout == 120.0
        assert config.max_retries == 5
        assert config.retry_base_delay == 2.0


class TestDifyClientSession:
    """Tests for DifyClient session management."""

    @pytest.mark.asyncio
    async def test_create_chatflow_session_success(self):
        """Test successful session creation."""
        config = DifyConfig(api_key="test-key")
        client = DifyClient(config)

        mock_response = {
            "data": {
                "conversation_id": "conv_xyz789",
                "task_id": "task_abc123",
            }
        }

        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response),
            )

            result = await client.create_chatflow_session(
                chatflow_id="chatflow_001",
                user_id="user_001",
                query="测试主题",
                inputs={"platform": "wechat"},
            )

            assert result["data"]["conversation_id"] == "conv_xyz789"
            mock_req.assert_called_once()
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["json"]["chatflow_id"] == "chatflow_001"
            assert call_kwargs["json"]["user"] == "user_001"
            assert call_kwargs["json"]["query"] == "测试主题"

    @pytest.mark.asyncio
    async def test_create_session_without_query(self):
        """Test session creation without initial query."""
        config = DifyConfig(api_key="test-key")
        client = DifyClient(config)

        mock_response = {"data": {"conversation_id": "conv_no_query"}}

        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response),
            )

            result = await client.create_chatflow_session(
                chatflow_id="chatflow_001",
                user_id="user_001",
            )

            assert result["data"]["conversation_id"] == "conv_no_query"
            call_kwargs = mock_req.call_args[1]
            assert "query" not in call_kwargs["json"]

    @pytest.mark.asyncio
    async def test_create_session_error(self):
        """Test session creation with API error."""
        config = DifyConfig(api_key="invalid-key")
        client = DifyClient(config)

        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = DifyClientError("401 Unauthorized")

            with pytest.raises(DifyClientError) as exc_info:
                await client.create_chatflow_session(
                    chatflow_id="chatflow_001",
                    user_id="user_001",
                )
            assert "401" in str(exc_info.value)


class TestDifyClientHITL:
    """Tests for DifyClient HITL operations."""

    @pytest.mark.asyncio
    async def test_resume_from_hitl(self):
        """Test resuming from HITL with task_id."""
        config = DifyConfig(api_key="test-key")
        client = DifyClient(config)

        mock_response = {
            "data": {
                "status": "completed",
                "action": "approved",
            }
        }

        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response),
            )

            result = await client.resume_from_hitl(
                task_id="task_001",
                action="approve",
                data={"updates": {}},
            )

            assert result["data"]["status"] == "completed"
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["json"]["task_id"] == "task_001"
            assert call_kwargs["json"]["action"] == "approve"


class TestDifyClientClose:
    """Tests for DifyClient cleanup."""

    @pytest.mark.asyncio
    async def test_close_with_active_client(self):
        """Test closing client with active connection."""
        config = DifyConfig(api_key="test-key")
        client = DifyClient(config)

        mock_client = AsyncMock()
        client._client = mock_client

        await client.close()

        mock_client.aclose.assert_called_once()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_without_client(self):
        """Test closing client when not initialized."""
        config = DifyConfig(api_key="test-key")
        client = DifyClient(config)

        # Should not raise
        await client.close()
        assert client._client is None
