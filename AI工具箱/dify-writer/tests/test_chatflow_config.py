# Tests: Chatflow YAML Configuration
import pytest
import yaml
from pathlib import Path

from dify_api.chatflow_config import (
    ChatflowConfig,
    NodeDefinition,
    EdgeDefinition,
    validate_chatflow_yaml,
)


class TestChatflowConfig:
    """Tests for ChatflowConfig dataclass."""

    def test_config_creation(self):
        """Test creating chatflow config."""
        config = ChatflowConfig(
            name="AI写作助手",
            description="9节点AI写作流水线",
            version="1.0.0",
        )

        assert config.name == "AI写作助手"
        assert config.description == "9节点AI写作流水线"
        assert config.version == "1.0.0"

    def test_config_with_nodes(self):
        """Test config with nodes."""
        nodes = [
            NodeDefinition(
                id="node_1",
                type="llm",
                label="意图解析",
            ),
            NodeDefinition(
                id="node_2",
                type="human-in-the-loop",
                label="策略确认",
            ),
        ]
        edges = [
            EdgeDefinition(
                source="node_1",
                target="node_2",
            )
        ]

        config = ChatflowConfig(
            name="测试",
            nodes=nodes,
            edges=edges,
        )

        assert len(config.nodes) == 2
        assert len(config.edges) == 1
        assert config.nodes[0].id == "node_1"
        assert config.edges[0].source == "node_1"


class TestNodeDefinition:
    """Tests for NodeDefinition dataclass."""

    def test_llm_node(self):
        """Test LLM node definition."""
        node = NodeDefinition(
            id="planning",
            type="llm",
            label="主题策划",
            prompt_ref="planning.md",
        )

        assert node.id == "planning"
        assert node.type == "llm"
        assert node.prompt_ref == "planning.md"

    def test_hitl_node(self):
        """Test HITL node definition."""
        node = NodeDefinition(
            id="hitl_1",
            type="human-in-the-loop",
            label="策略确认",
            webhook_url="/webhooks/dify/hitl",
        )

        assert node.type == "human-in-the-loop"
        assert node.webhook_url == "/webhooks/dify/hitl"

    def test_http_request_node(self):
        """Test HTTP Request node definition."""
        node = NodeDefinition(
            id="cover_api",
            type="http-request",
            label="封面生成API",
            url="https://ark.cn-beijing.volces.com/api/v3/images/generations",
            method="POST",
        )

        assert node.type == "http-request"
        assert node.method == "POST"

    def test_condition_node(self):
        """Test Condition node definition."""
        node = NodeDefinition(
            id="quality_check",
            type="condition",
            label="质量判断",
            conditions=[
                {"field": "score", "operator": ">=", "value": 85},
            ],
        )

        assert node.type == "condition"
        assert node.conditions[0]["value"] == 85

    def test_agent_node(self):
        """Test Agent node definition."""
        node = NodeDefinition(
            id="research",
            type="agent",
            label="深度研究",
        )

        assert node.type == "agent"


class TestEdgeDefinition:
    """Tests for EdgeDefinition dataclass."""

    def test_basic_edge(self):
        """Test basic edge definition."""
        edge = EdgeDefinition(
            source="node_1",
            target="node_2",
        )

        assert edge.source == "node_1"
        assert edge.target == "node_2"
        assert edge.condition is None

    def test_conditional_edge(self):
        """Test conditional edge definition."""
        edge = EdgeDefinition(
            source="quality_check",
            target="polish",
            condition={"field": "pass", "value": False},
        )

        assert edge.condition["field"] == "pass"
        assert edge.condition["value"] is False


class TestValidateChatflowYaml:
    """Tests for YAML validation."""

    def test_valid_yaml_structure(self, tmp_path):
        """Test validating a correct YAML structure."""
        yaml_content = """
name: AI写作助手
description: 9节点流水线
version: 1.0.0
nodes:
  - id: start
    type: llm
    label: 开始
  - id: end_node
    type: llm
    label: 结束
edges:
  - source: start
    target: end_node
"""
        yaml_file = tmp_path / "chatflow.yaml"
        yaml_file.write_text(yaml_content)

        errors = validate_chatflow_yaml(yaml_file)
        assert len(errors) == 0

    def test_missing_required_fields(self, tmp_path):
        """Test YAML with missing required fields."""
        yaml_content = """
name: AI写作助手
nodes:
  - id: start
"""
        yaml_file = tmp_path / "chatflow.yaml"
        yaml_file.write_text(yaml_content)

        errors = validate_chatflow_yaml(yaml_file)

        # Should have errors about missing version, edges
        assert len(errors) > 0

    def test_invalid_node_type(self, tmp_path):
        """Test YAML with invalid node type."""
        yaml_content = """
name: AI写作助手
version: 1.0.0
nodes:
  - id: start
    type: invalid_type
edges: []
"""
        yaml_file = tmp_path / "chatflow.yaml"
        yaml_file.write_text(yaml_content)

        errors = validate_chatflow_yaml(yaml_file)

        # Should flag invalid type
        assert any("type" in e.lower() for e in errors)

    def test_orphan_nodes(self, tmp_path):
        """Test YAML with nodes not connected to graph."""
        yaml_content = """
name: AI写作助手
version: 1.0.0
nodes:
  - id: orphan
    type: llm
  - id: start
    type: llm
  - id: end_node
    type: llm
edges:
  - source: start
    target: end_node
"""
        yaml_file = tmp_path / "chatflow.yaml"
        yaml_file.write_text(yaml_content)

        errors = validate_chatflow_yaml(yaml_file)

        # Should warn about orphan node
        assert any("orphan" in e for e in errors)


class TestChatflowYamlIntegration:
    """Integration tests with actual chatflow YAML."""

    def test_load_actual_chatflow(self):
        """Test loading the actual chatflow.yaml."""
        chatflow_path = Path(__file__).parent.parent / "dify-chatflow.yaml"

        if not chatflow_path.exists():
            pytest.skip("chatflow.yaml not found")

        with open(chatflow_path) as f:
            data = yaml.safe_load(f)

        assert data is not None
        assert "nodes" in data
        assert "edges" in data

        # Verify key nodes exist
        node_ids = [n["id"] for n in data["nodes"]]
        assert "intent_parsing" in node_ids
        assert "planning" in node_ids
        assert "writing" in node_ids
        assert "polish" in node_ids

        # Verify HITL nodes exist (type is human-in-the-loop)
        hitl_nodes = [n for n in data["nodes"] if n.get("type") == "human-in-the-loop"]
        assert len(hitl_nodes) >= 3  # 3 HITL确认点

    def test_all_prompts_exist(self):
        """Test all referenced prompts exist."""
        chatflow_path = Path(__file__).parent.parent / "dify-chatflow.yaml"

        if not chatflow_path.exists():
            pytest.skip("chatflow.yaml not found")

        with open(chatflow_path) as f:
            data = yaml.safe_load(f)

        prompt_dir = Path(__file__).parent.parent / "dify-prompts"
        for node in data["nodes"]:
            if "prompt_ref" in node:
                prompt_path = prompt_dir / node["prompt_ref"]
                assert prompt_path.exists(), f"Prompt {node['prompt_ref']} not found"

    def test_quality_loop_config(self):
        """Test quality loop configuration."""
        chatflow_path = Path(__file__).parent.parent / "dify-chatflow.yaml"

        if not chatflow_path.exists():
            pytest.skip("chatflow.yaml not found")

        with open(chatflow_path) as f:
            data = yaml.safe_load(f)

        # Find quality condition node
        quality_nodes = [
            n for n in data["nodes"]
            if n.get("type") == "condition" and "quality" in n.get("id", "")
        ]

        assert len(quality_nodes) > 0

        # Verify loop configuration exists
        assert "quality_loop" in data
        assert data["quality_loop"]["max_iterations"] >= 3
