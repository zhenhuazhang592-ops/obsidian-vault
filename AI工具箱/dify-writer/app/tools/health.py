# health tool
import os
import time
from datetime import datetime, timezone

from app.tools.base import BaseTool


class HealthTool(BaseTool):
    """MCP Server health status tool."""

    name = "health"
    description = "Get MCP Server health status."

    def execute(self, **kwargs) -> dict:
        """
        Return detailed process health (CPU, memory, uptime).
        Called via POST /tools with X-MCP-Key auth.
        """
        import psutil

        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()

        return {
            "status": "healthy",
            "uptime_seconds": time.time() - process.create_time(),
            "cpu_percent": process.cpu_percent(interval=0.1),
            "memory_mb": mem_info.rss / (1024 * 1024),
            "pid": os.getpid(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
