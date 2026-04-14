# Tests: DifyClient Metrics
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from dify_api.client import DifyClient, DifyConfig, DifyMetrics


class TestDifyMetrics:
    """Tests for DifyMetrics."""

    def test_metrics_initial_state(self):
        """Test initial metrics state."""
        metrics = DifyMetrics()
        assert metrics.requests_total == 0
        assert metrics.requests_success == 0
        assert metrics.requests_error == 0
        assert metrics.requests_retry == 0
        assert metrics.hitl_triggered == 0
        assert metrics.last_request_at is None

    def test_metrics_to_dict(self):
        """Test metrics export."""
        metrics = DifyMetrics()
        metrics.requests_total = 5
        metrics.hitl_triggered = 2
        d = metrics.to_dict()
        assert d["requests_total"] == 5
        assert d["hitl_triggered"] == 2
        assert d["method_counts"] == {}

    def test_metrics_reset(self):
        """Test metrics reset."""
        metrics = DifyMetrics()
        metrics.requests_total = 10
        metrics.reset()
        assert metrics.requests_total == 0


class TestDifyClientInit:
    """Tests for DifyClient initialization."""

    def test_client_initialization(self):
        """Test client can be initialized with config."""
        config = DifyConfig(api_key="test-key")
        client = DifyClient(config)
        assert client.config == config
        assert client._client is None
        assert isinstance(client.metrics, DifyMetrics)
