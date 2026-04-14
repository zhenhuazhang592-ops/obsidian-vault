# Tests: DifyClient Retry Logic
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from dify_api.client import DifyClient, DifyConfig, DifyClientError


class TestDifyClientRetry:
    """Tests for retry logic with 429 exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_on_429(self):
        """Test retry with 429 response and exponential backoff."""
        config = DifyConfig(api_key="test-key", max_retries=3, retry_base_delay=0.05)
        client = DifyClient(config)

        # Build proper httpx.HTTPStatusError for 429s
        def make_429():
            resp = MagicMock(status_code=429)
            return httpx.HTTPStatusError("rate limited", request=MagicMock(), response=resp)

        responses = [
            make_429(),
            make_429(),
            MagicMock(status_code=200, json=MagicMock(return_value={"data": {"ok": True}})),
        ]

        with patch.object(client, "_get_client") as mock_get:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(side_effect=responses)
            mock_get.return_value = mock_httpx_client

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                result = await client._request_with_retry("POST", "/chat-messages", json={})

        assert result.status_code == 200
        # 2 retries + 1 success
        assert mock_httpx_client.request.call_count == 3
        assert client.metrics.requests_retry == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_4xx_other_than_429(self):
        """Test that 4xx errors other than 429 are not retried."""
        config = DifyConfig(api_key="test-key", max_retries=3)
        client = DifyClient(config)

        # httpx.HTTPStatusError must be raised by raise_for_status
        mock_response = MagicMock(status_code=401)
        exc = httpx.HTTPStatusError(
            "401",
            request=MagicMock(),
            response=mock_response,
        )
        mock_response.raise_for_status.side_effect = exc

        with patch.object(client, "_get_client") as mock_get:
            mock_httpx_client = AsyncMock()
            mock_httpx_client.request = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_httpx_client

            with pytest.raises(DifyClientError):
                await client._request_with_retry("POST", "/chat-messages", json={})

        # No retry for 401
        assert mock_httpx_client.request.call_count == 1
        assert client.metrics.requests_error == 1
