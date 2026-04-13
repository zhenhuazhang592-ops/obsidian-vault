# core/tavily_client.py - Tavily 深度搜索客户端
# Phase 2: 集成 Tavily API 进行网络深度搜索

import os
import json
import time
from typing import Any
from dataclasses import dataclass


@dataclass
class TavilySearchResult:
    """单条搜索结果"""
    url: str
    title: str
    content: str
    published_date: str = ""


@dataclass
class TavilySearchReport:
    """完整搜索报告"""
    query: str
    results: list[TavilySearchResult]
    key_findings: list[str]
    statistics: list[dict]   # [{"stat": "...", "source": "...", "claim": "..."}]
    search_time: float

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "results": [
                {"url": r.url, "title": r.title, "content": r.content[:200], "published_date": r.published_date}
                for r in self.results
            ],
            "key_findings": self.key_findings,
            "statistics": self.statistics,
            "search_time": round(self.search_time, 2),
        }


class TavilyClient:
    """
    Tavily Search API 客户端。

    使用方式：
        client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
        report = client.search("AI Agent 工具链", max_results=5)
    """

    BASE_URL = "https://api.tavily.com/search"

    def __init__(self, api_key: str = None, timeout: int = 30):
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY", "")
        self.timeout = timeout

    def is_available(self) -> bool:
        """检查 API key 是否配置"""
        return bool(self.api_key)

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        search_depth: str = "advanced",
    ) -> TavilySearchReport:
        """
        执行 Tavily 深度搜索。

        Args:
            query: 搜索查询
            max_results: 最大结果数（1-20）
            search_depth: "basic" | "advanced"

        Returns:
            TavilySearchReport
        """
        start = time.time()

        if not self.is_available():
            return self._empty_report(query, start, "API key not configured")

        try:
            import urllib.request
            import urllib.parse

            payload = json.dumps({
                "query": query,
                "max_results": min(max_results, 20),
                "search_depth": search_depth,
                "include_answer": True,
                "include_raw_content": False,
                "include_images": False,
            }).encode("utf-8")

            req = urllib.request.Request(
                self.BASE_URL,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            results = [
                TavilySearchResult(
                    url=r.get("url", ""),
                    title=r.get("title", ""),
                    content=r.get("content", ""),
                    published_date=r.get("published_date", ""),
                )
                for r in data.get("results", [])
            ]

            # 从答案中提取关键发现
            answer = data.get("answer", "")
            findings = []
            if answer:
                findings = [f.strip() for f in answer.split(".") if f.strip()][:5]

            # 统计：取搜索结果中包含数字的描述
            statistics = []
            for r in results[:3]:
                if any(c.isdigit() for c in r.content):
                    # 提取含数字的短句作为统计数据
                    import re
                    numbers = re.findall(r'[\d.,]+%?', r.content)
                    if numbers:
                        statistics.append({
                            "stat": numbers[0],
                            "source": r.url,
                            "claim": r.title,
                        })

            search_time = time.time() - start
            return TavilySearchReport(
                query=query,
                results=results,
                key_findings=findings,
                statistics=statistics,
                search_time=search_time,
            )

        except Exception as e:
            return self._empty_report(query, start, str(e))

    def _empty_report(self, query: str, start: float, error: str) -> TavilySearchReport:
        """返回空报告（API 不可用时）"""
        return TavilySearchReport(
            query=query,
            results=[],
            key_findings=[f"搜索不可用: {error}"],
            statistics=[],
            search_time=time.time() - start,
        )


def search_topic(topic: str, api_key: str = None, max_results: int = 5) -> dict:
    """
    快捷函数：对主题进行深度搜索。

    Returns:
        dict，含 results/key_findings/statistics
    """
    client = TavilyClient(api_key=api_key)
    report = client.search(topic, max_results=max_results)
    return report.to_dict()
