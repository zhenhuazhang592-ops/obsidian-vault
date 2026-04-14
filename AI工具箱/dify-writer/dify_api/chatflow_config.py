"""
Dify Chatflow Configuration
Chatflow YAML 配置定义和验证
"""
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class NodeDefinition:
    """节点定义"""
    id: str
    type: str
    label: str
    prompt_ref: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    webhook_url: Optional[str] = None
    conditions: list = field(default_factory=list)
    max_iterations: Optional[int] = None


@dataclass
class EdgeDefinition:
    """边定义"""
    source: str
    target: str
    condition: Optional[dict] = None


@dataclass
class ChatflowConfig:
    """Chatflow 配置"""
    name: str
    description: str = ""
    version: str = "1.0.0"
    nodes: list[NodeDefinition] = field(default_factory=list)
    edges: list[EdgeDefinition] = field(default_factory=list)


def load_chatflow_yaml(path: str | Path) -> dict:
    """加载 Chatflow YAML 文件"""
    with open(path) as f:
        return yaml.safe_load(f)


def parse_node(node_data: dict) -> NodeDefinition:
    """解析节点定义"""
    return NodeDefinition(
        id=node_data["id"],
        type=node_data["type"],
        label=node_data.get("label", ""),
        prompt_ref=node_data.get("prompt_ref"),
        url=node_data.get("url"),
        method=node_data.get("method"),
        webhook_url=node_data.get("webhook_url"),
        conditions=node_data.get("conditions", []),
        max_iterations=node_data.get("max_iterations"),
    )


def parse_edge(edge_data: dict) -> EdgeDefinition:
    """解析边定义"""
    return EdgeDefinition(
        source=edge_data["source"],
        target=edge_data["target"],
        condition=edge_data.get("condition"),
    )


def validate_chatflow_yaml(path: str | Path) -> list[str]:
    """
    验证 Chatflow YAML 文件

    Returns:
        错误列表，空列表表示验证通过
    """
    errors = []

    with open(path) as f:
        data = yaml.safe_load(f)

    if not data:
        errors.append("YAML file is empty")
        return errors

    # 检查必需字段
    required_fields = ["name", "version", "nodes", "edges"]
    for field_name in required_fields:
        if field_name not in data:
            errors.append(f"Missing required field: {field_name}")

    if errors:
        return errors

    # 检查 nodes
    nodes = data.get("nodes", [])
    if not nodes:
        errors.append("No nodes defined")
        return errors

    node_ids = set()
    for node in nodes:
        if "id" not in node:
            errors.append("Node missing 'id' field")
            continue
        if "type" not in node:
            errors.append(f"Node '{node['id']}' missing 'type' field")
            continue

        node_id = node["id"]
        if node_id in node_ids:
            errors.append(f"Duplicate node id: {node_id}")
        node_ids.add(node_id)

        # 验证节点类型
        valid_types = [
            "llm", "agent", "hitl", "condition", "loop",
            "http-request", "parallel", "template", "code", "variable"
        ]
        if node["type"] not in valid_types:
            errors.append(f"Invalid node type '{node['type']}' for node '{node_id}'")

    # 检查 edges
    edges = data.get("edges", [])
    edge_targets = set()
    for edge in edges:
        if "source" not in edge:
            errors.append("Edge missing 'source' field")
            continue
        if "target" not in edge:
            errors.append("Edge missing 'target' field")
            continue

        source = edge["source"]
        target = edge["target"]

        if source not in node_ids:
            errors.append(f"Edge references non-existent source node: {source}")
        if target not in node_ids:
            errors.append(f"Edge references non-existent target node: {target}")

        edge_targets.add(target)

    # 检查孤立节点（没有作为target的节点 - 排除start类型的节点）
    for node_id in node_ids:
        if node_id not in edge_targets:
            # 可能是起始节点，检查是否有边以它为source
            has_outgoing = any(e["source"] == node_id for e in edges)
            if not has_outgoing and node_id not in ["end", "exit"]:
                errors.append(f"Orphan node (no incoming edges): {node_id}")

    return errors


def get_node_by_id(config: dict, node_id: str) -> Optional[dict]:
    """根据 ID 获取节点"""
    for node in config.get("nodes", []):
        if node.get("id") == node_id:
            return node
    return None


def get_hitl_nodes(config: dict) -> list[dict]:
    """获取所有 HITL 节点"""
    return [n for n in config.get("nodes", []) if n.get("type") == "hitl"]


def get_llm_nodes(config: dict) -> list[dict]:
    """获取所有 LLM 节点"""
    return [n for n in config.get("nodes", []) if n.get("type") == "llm"]


def get_http_request_nodes(config: dict) -> list[dict]:
    """获取所有 HTTP Request 节点"""
    return [n for n in config.get("nodes", []) if n.get("type") == "http-request"]


def get_loop_nodes(config: dict) -> list[dict]:
    """获取所有 Loop 节点"""
    return [n for n in config.get("nodes", []) if n.get("type") == "loop"]
