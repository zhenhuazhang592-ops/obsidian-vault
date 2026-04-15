# Integration tests: MCP Server + Dify Client
"""
测试 MCP Server endpoints 与 Dify Client 的集成
使用 Mock Dify Server，不需要真实 Dify API Key
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from dify_api.client import DifyClient, DifyConfig, DifyClientError
from tests.mock_dify_server import MockDifyServer, get_mock_server, reset_mock_server


class TestDifyClientWithMockServer:
    """Test DifyClient using MockDifyServer."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset mock server before each test."""
        reset_mock_server()
        yield
        reset_mock_server()

    @pytest.mark.asyncio
    async def test_create_session_via_mock(self):
        """Test creating a chatflow session via mock server."""
        config = DifyConfig(api_key="test-key", base_url="https://mock.dify.ai/v1")
        client = DifyClient(config)

        mock_response_body = {
            "data": {
                "conversation_id": "conv_xyz789",
                "task_id": "task_abc123",
            }
        }

        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response_body),
                raise_for_status=MagicMock(),
            )

            result = await client.create_chatflow_session(
                chatflow_id="cf_001",
                user_id="user_001",
                query="写一篇关于AI的文章",
            )

            assert result["data"]["conversation_id"] == "conv_xyz789"
            mock_req.assert_called_once()
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["json"]["chatflow_id"] == "cf_001"
            assert call_kwargs["json"]["user"] == "user_001"
            assert call_kwargs["json"]["query"] == "写一篇关于AI的文章"

    @pytest.mark.asyncio
    async def test_resume_hitl_via_mock(self):
        """Test resuming from HITL via mock server."""
        config = DifyConfig(api_key="test-key", base_url="https://mock.dify.ai/v1")
        client = DifyClient(config)

        mock_response_body = {
            "data": {
                "status": "completed",
                "action": "approved",
            }
        }

        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response_body),
                raise_for_status=MagicMock(),
            )

            result = await client.resume_from_hitl(
                task_id="task_001",
                action="approve",
                data={"feedback": "ok"},
            )

            assert result["data"]["status"] == "completed"
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["json"]["task_id"] == "task_001"
            assert call_kwargs["json"]["action"] == "approve"
            assert client.metrics.hitl_triggered == 1

    @pytest.mark.asyncio
    async def test_get_conversation_messages_via_mock(self):
        """Test fetching conversation messages."""
        config = DifyConfig(api_key="test-key", base_url="https://mock.dify.ai/v1")
        client = DifyClient(config)

        mock_response_body = {"data": [{"message_id": "msg_001", "query": "hello"}]}

        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response_body),
                raise_for_status=MagicMock(),
            )

            messages = await client.get_conversation_messages(
                conversation_id="conv_001",
                user_id="user_001",
            )

        assert isinstance(messages, list)
        assert len(messages) == 1
        assert messages[0]["message_id"] == "msg_001"

    @pytest.mark.asyncio
    async def test_client_error_raises(self):
        """Test that DifyClientError is raised on HTTP error."""
        config = DifyConfig(api_key="test-key")
        client = DifyClient(config)

        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = DifyClientError("Connection failed")

            with pytest.raises(DifyClientError) as exc_info:
                await client.create_chatflow_session(
                    chatflow_id="cf_001",
                    user_id="user_001",
                )

            assert "Connection failed" in str(exc_info.value)


class TestMockDifyServer:
    """Tests for the MockDifyServer itself."""

    def test_mock_server_singleton(self):
        """Test that get_mock_server returns the same instance."""
        reset_mock_server()
        s1 = get_mock_server()
        s2 = get_mock_server()
        assert s1 is s2

    def test_mock_server_reset(self):
        """Test reset_mock_server clears state."""
        reset_mock_server()
        s1 = get_mock_server()
        reset_mock_server()
        s2 = get_mock_server()
        assert s1 is not s2

    @pytest.mark.asyncio
    async def test_mock_chat_messages_blocking(self):
        """Test mock server chat_messages in blocking mode."""
        reset_mock_server()
        server = get_mock_server()

        headers, body = await server.chat_messages(
            chatflow_id="cf_test",
            query="hello",
            user="test_user",
            response_mode="blocking",
        )

        assert "task_id" in body
        assert "conversation_id" in body

    @pytest.mark.asyncio
    async def test_mock_chat_messages_streaming_returns_generator(self):
        """Test mock server chat_messages in streaming mode returns generator."""
        reset_mock_server()
        server = get_mock_server()

        headers, generator = await server.chat_messages(
            chatflow_id="cf_test",
            query="hello",
            user="test_user",
            response_mode="streaming",
        )

        events = []
        async for event in generator.generate_events():
            events.append(event)

        assert len(events) > 0
        assert events[0].startswith("event: message")

    @pytest.mark.asyncio
    async def test_mock_resume(self):
        """Test mock server resume."""
        reset_mock_server()
        server = get_mock_server()

        result = await server.resume(
            task_id="task_test",
            action="approve",
            data={"feedback": "looks good"},
        )

        assert result["task_id"] == "task_test"

    @pytest.mark.asyncio
    async def test_mock_get_conversation_messages_returns_tuple(self):
        """Test mock server get_conversation_messages returns (headers, body)."""
        reset_mock_server()
        server = get_mock_server()

        # 先创建会话
        await server.chat_messages(
            chatflow_id="cf_test",
            query="hello",
            user="test_user",
        )

        headers, body = await server.get_conversation_messages(
            conversation_id="conv_test",
            user="test_user",
        )

        assert isinstance(headers, dict)
        assert "data" in body
