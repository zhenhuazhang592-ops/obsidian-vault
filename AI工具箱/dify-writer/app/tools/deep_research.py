# deep_research tool with concurrent Tavily search
import asyncio
import json
import logging
from typing import Any

from app.tools.base import BaseTool

logger = logging.getLogger(__name__)


class DeepResearchTool(BaseTool):
    """Deep research using concurrent Tavily search."""

    name = "deep_research"
    description = "Research a topic using Tavily search. Returns structured research results."

    async def execute(
        self,
        topic: str,
        queries: list[str],
        platform: str = "wechat",
        session_id: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Execute deep research with concurrent query execution.

        Uses asyncio.gather for parallel Tavily queries (per Eng Review decision 4A-A).
        """
        if not queries:
            queries = [topic]

        results = await self._search_concurrent(queries)

        return {
            "topic": topic,
            "queries": queries,
            "sources": results,
            "summary": self._summarize(results),
            "source_count": len(results),
        }

    async def _search_concurrent(self, queries: list[str]) -> list[dict]:
        """
        Run all Tavily searches concurrently with asyncio.gather.
        Each query is a separate Tavily search, results are merged.
        """
        import os

        tavily_key = os.environ.get("TAVILY_API_KEY", "")

        async def search_one(query: str) -> dict:
            if tavily_key:
                try:
                    import aiohttp

                    async with aiohttp.ClientSession() as session:
                        payload = {
                            "api_key": tavily_key,
                            "query": query,
                            "max_results": 5,
                        }
                        async with session.post(
                            "https://api.tavily.com/search",
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=30),
                        ) as resp:
                            data = await resp.json()
                            return {
                                "query": query,
                                "results": data.get("results", [])[:5],
                                "status": "success",
                            }
                except Exception as e:
                    logger.warning(f"Tavily search failed for '{query}': {e}")
                    return {"query": query, "results": [], "status": "error", "error": str(e)}
            else:
                # Mock mode for development/testing
                return {
                    "query": query,
                    "results": [
                        {
                            "title": f"Research on {query}",
                            "url": f"https://example.com/{query}",
                            "content": f"Mock research content for {query}",
                        }
                    ],
                    "status": "mock",
                }

        results = await asyncio.gather(*[search_one(q) for q in queries])
        return list(results)

    def _summarize(self, results: list[dict]) -> str:
        """Generate a brief summary from search results."""
        total = sum(len(r.get("results", [])) for r in results)
        return f"Research completed: {total} sources across {len(results)} queries"
