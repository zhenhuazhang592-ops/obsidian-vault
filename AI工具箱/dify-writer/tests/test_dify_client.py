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

    def test_custom_values(self):
        """Test custom configuration values."""
        config = DifyConfig(
            api_key="custom-key",
            base_url="https://custom.dify.ai/v1",
            timeout=120.0,
        )
        assert config.api_key == "custom-key"
        assert config.base_url == "https://custom.dify.ai/v1"
        assert config.timeout == 120.0


class TestDifyClientInit:
    """Tests for DifyClient initialization."""

    def test_client_initialization(self):
        """Test client can be initialized with config."""
        config = DifyConfig(api_key="test-key")
        client = DifyClient(config)
        assert client.config == config
        assert client._client is None  # Not initialized until first use


class TestDifyClientSession:
    """Tests for DifyClient session management."""

    @pytest.mark.asyncio
    async def test_create_chatflow_session_success(self):
        """Test successful session creation."""
        config = DifyConfig(api_key="test-key")
        client = DifyClient(config)

        mock_response = {
            "data": {
                "session_id": "sess_abc123",
                "conversation_id": "conv_xyz789",
            }
        }

        with patch.object(client, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response),
            )
            mock_get_client.return_value = mock_client

            result = await client.create_chatflow_session(
                chatflow_id="chatflow_001",
                user_id="user_001",
                query="测试主题",
                inputs={"platform": "wechat"},
            )

            assert result["data"]["session_id"] == "sess_abc123"
            mock_client.post.assert_called_once()
            call_kwargs = mock_client.post.call_args[1]
            assert call_kwargs["json"]["chatflow_id"] == "chatflow_001"
            assert call_kwargs["json"]["user"] == "user_001"
            assert call_kwargs["json"]["query"] == "测试主题"

    @pytest.mark.asyncio
    async def test_create_session_without_query(self):
        """Test session creation without initial query."""
        config = DifyConfig(api_key="test-key")
        client = DifyClient(config)

        mock_response = {"data": {"session_id": "sess_no_query"}}

        with patch.object(client, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response),
            )
            mock_get_client.return_value = mock_client

            result = await client.create_chatflow_session(
                chatflow_id="chatflow_001",
                user_id="user_001",
            )

            assert result["data"]["session_id"] == "sess_no_query"
            call_kwargs = mock_client.post.call_args[1]
            assert "query" not in call_kwargs["json"]

    @pytest.mark.asyncio
    async def test_create_session_error(self):
        """Test session creation with API error."""
        config = DifyConfig(api_key="invalid-key")
        client = DifyClient(config)

        with patch.object(client, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response = MagicMock(status_code=401)
            mock_response.raise_for_status.side_effect = DifyClientError("401 Unauthorized")
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            with pytest.raises(DifyClientError) as exc_info:
                await client.create_chatflow_session(
                    chatflow_id="chatflow_001",
                    user_id="user_001",
                )
            assert "401" in str(exc_info.value)


class TestDifyClientSendMessage:
    """Tests for DifyClient message sending."""

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test successful message sending."""
        config = DifyConfig(api_key="test-key")
        client = DifyClient(config)

        mock_response = {
            "event": "message",
            "task_id": "task_001",
            "conversation_id": "conv_001",
            "message_id": "msg_001",
            "answer": "这是Dify的回复",
        }

        with patch.object(client, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response),
            )
            mock_get_client.return_value = mock_client

            result = await client.send_message(
                session_id="sess_001",
                message="测试消息",
            )

            assert result["answer"] == "这是Dify的回复"
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_with_conversation_id(self):
        """Test message sending with conversation_id."""
        config = DifyConfig(api_key="test-key")
        client = DifyClient(config)

        mock_response = {"event": "message", "answer": "ok"}

        with patch.object(client, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response),
            )
            mock_get_client.return_value = mock_client

            result = await client.send_message(
                session_id="sess_001",
                message="测试",
                conversation_id="conv_001",
            )

            call_kwargs = mock_client.post.call_args[1]
            assert call_kwargs["json"]["session_id"] == "sess_001"
            assert call_kwargs["json"]["conversation_id"] == "conv_001"


class TestDifyClientHITL:
    """Tests for DifyClient HITL operations."""

    @pytest.mark.asyncio
    async def test_get_hitl_status(self):
        """Test getting HITL status."""
        config = DifyConfig(api_key="test-key")
        client = DifyClient(config)

        mock_response = {
            "data": {
                "status": "waiting",
                "hitl_type": "strategy",
                "node_id": "hitl_001",
            }
        }

        with patch.object(client, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response),
            )
            mock_get_client.return_value = mock_client

            result = await client.get_hitl_status(session_id="sess_001")

            assert result["data"]["status"] == "waiting"
            assert result["data"]["hitl_type"] == "strategy"

    @pytest.mark.asyncio
    async def test_resume_from_hitl(self):
        """Test resuming from HITL."""
        config = DifyConfig(api_key="test-key")
        client = DifyClient(config)

        mock_response = {
            "data": {
                "status": "completed",
                "action": "approved",
            }
        }

        with patch.object(client, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response),
            )
            mock_get_client.return_value = mock_client

            result = await client.resume_from_hitl(
                session_id="sess_001",
                action="approve",
                data={"updates": {}},
            )

            assert result["data"]["status"] == "completed"


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
