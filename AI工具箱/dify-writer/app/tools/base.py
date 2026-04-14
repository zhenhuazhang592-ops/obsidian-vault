# Tool registry and base tool class
from abc import ABC, abstractmethod
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


class BaseTool(ABC):
    """Base class for MCP tools."""

    name: str = ""
    description: str = ""

    @abstractmethod
    async def execute(self, **kwargs) -> dict:
        """Execute the tool with given arguments."""
        ...


class ToolRegistry:
    """Registry for MCP tools."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if not tool.name:
            raise ValueError("Tool must have a name")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise KeyError(f"Tool not found: {name}")
        return self._tools[name]

    def list_tools(self) -> list[dict]:
        return [
            {"name": t.name, "description": t.description}
            for t in self._tools.values()
        ]

    def has(self, name: str) -> bool:
        return name in self._tools


# Global registry instance
_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _register_tools()
    return _registry


def _register_tools() -> None:
    """Register all MCP tools. Called once at startup."""
    from app.tools import (
        deep_research,
        extract_author_style,
        check_quality,
        generate_cover,
        generate_inline_images,
        adapt_to_xhs,
        format_html,
        monitor_obsidian_topics,
        record_performance,
        health,
    )

    registry = _registry
    for tool in [
        deep_research.DeepResearchTool(),
        extract_author_style.ExtractAuthorStyleTool(),
        check_quality.CheckQualityTool(),
        generate_cover.GenerateCoverTool(),
        generate_inline_images.GenerateInlineImagesTool(),
        adapt_to_xhs.AdaptToXHSTool(),
        format_html.FormatHtmlTool(),
        monitor_obsidian_topics.MonitorObsidianTopicsTool(),
        record_performance.RecordPerformanceTool(),
        health.HealthTool(),
    ]:
        registry.register(tool)
