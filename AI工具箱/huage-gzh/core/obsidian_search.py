# core/obsidian_search.py - Obsidian 知识库搜索
# Phase 2: 搜索 Obsidian Vault 中已发布文章的风格特征

import os
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Any


@dataclass
class ObsidianSearchResult:
    """单条知识库搜索结果"""
    file_path: str
    file_name: str
    matched_content: str   # 匹配片段
    relevance_score: float  # 0-1


@dataclass
class ObsidianSearchReport:
    """知识库搜索报告"""
    query: str
    results: list[ObsidianSearchResult]
    style_notes: list[str]    # 风格笔记（从 YAML frontmatter 提取）
    topic_tags: list[str]     # 相关话题标签
    total_files_searched: int

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "results": [
                {
                    "file_path": r.file_path,
                    "file_name": r.file_name,
                    "matched_content": r.matched_content[:300],
                    "relevance_score": round(r.relevance_score, 2),
                }
                for r in self.results
            ],
            "style_notes": self.style_notes,
            "topic_tags": self.topic_tags,
            "total_files_searched": self.total_files_searched,
        }


class ObsidianSearcher:
    """
    Obsidian Vault 搜索客户端。

    在已发布文章目录中搜索相关内容，提取风格特征和话题标签。

    使用方式：
        searcher = ObsidianSearcher(vault_path="/path/to/vault")
        report = searcher.search("AI Agent 工具链")
    """

    # 话题标签关键词映射
    TAG_KEYWORDS = {
        "AI": ["AI", "人工智能", "LLM", "GPT", "Claude", "Agent", "大模型"],
        "技术": ["Python", "编程", "开发", "代码", "Git", "API"],
        "效率": ["工具链", "效率", "自动化", "工作流", "Notion", "Obsidian"],
        "产品": ["产品", "设计", "用户", "需求", "MVP", "PMF"],
        "创业": ["创业", "融资", "YC", "投资", "增长", "商业"],
    }

    def __init__(self, vault_path: str | Path = None):
        self.vault_path = Path(vault_path) if vault_path else None

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        article_dir: str | Path = None,
    ) -> ObsidianSearchReport:
        """
        搜索知识库。

        Args:
            query: 搜索关键词
            max_results: 最大结果数
            article_dir: 文章目录（默认使用 vault_path 下的已发布文章）

        Returns:
            ObsidianSearchReport
        """
        import time
        start = time.time()

        # 确定搜索目录
        if article_dir:
            search_dir = Path(article_dir)
        elif self.vault_path:
            # 默认在 vault_path 下搜索"已发布文章"目录
            search_dir = self.vault_path / "已发布文章"
            if not search_dir.exists():
                search_dir = self.vault_path
        else:
            return self._empty_report(query, 0)

        if not search_dir.exists():
            return self._empty_report(query, 0, f"Directory not found: {search_dir}")

        query_lower = query.lower()
        results: list[ObsidianSearchResult] = []
        all_tags: set[str] = set()
        style_notes: list[str] = []
        files_searched = 0

        # 遍历所有 .md 文件
        for md_file in search_dir.glob("**/*.md"):
            files_searched += 1
            if files_searched > 500:  # 最多搜索 500 个文件
                break

            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception:
                continue

            # 检查是否匹配
            if not self._matches_query(content, query_lower):
                continue

            # 提取 frontmatter 标签
            tags = self._extract_tags(content)
            all_tags.update(tags)

            # 提取匹配片段
            matched = self._extract_matched_snippet(content, query_lower)

            # 计算相关性分数
            score = self._compute_relevance(content, query_lower)

            results.append(ObsidianSearchResult(
                file_path=str(md_file.relative_to(search_dir.parent) if search_dir.parent != md_file else md_file),
                file_name=md_file.stem,
                matched_content=matched,
                relevance_score=score,
            ))

        # 排序并限制结果数
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        results = results[:max_results]

        # 从匹配结果中提取风格笔记
        for r in results[:3]:
            style_note = self._extract_style_note(r.matched_content)
            if style_note:
                style_notes.append(style_note)

        return ObsidianSearchReport(
            query=query,
            results=results,
            style_notes=style_notes,
            topic_tags=list(all_tags)[:20],
            total_files_searched=files_searched,
        )

    def _matches_query(self, content: str, query_lower: str) -> bool:
        """检查内容是否匹配查询"""
        content_lower = content.lower()
        # 关键词匹配
        keywords = [k.strip() for k in query_lower.split() if len(k) > 1]
        return any(kw in content_lower for kw in keywords)

    def _extract_matched_snippet(self, content: str, query_lower: str, context_chars: int = 150) -> str:
        """提取包含查询词的片段"""
        # 去掉 frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2]

        keywords = [k.strip() for k in query_lower.split() if len(k) > 1]

        for kw in keywords:
            idx = content.lower().find(kw)
            if idx >= 0:
                start = max(0, idx - context_chars)
                end = min(len(content), idx + context_chars)
                snippet = content[start:end].strip()
                return ("..." if start > 0 else "") + snippet + ("..." if end < len(content) else "")

        return content[:context_chars * 2].strip()

    def _extract_tags(self, content: str) -> list[str]:
        """从 frontmatter 提取 tags"""
        tags = []
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 2:
                fm = parts[1]
                tag_match = re.findall(r'tags:\s*\[([^\]]+)\]', fm)
                for tm in tag_match:
                    tags.extend([t.strip().strip("'\"") for t in tm.split(",")])
        return tags

    def _extract_style_note(self, snippet: str) -> str:
        """从片段中提取风格特征描述"""
        # 提取包含"我的"、"我发现"、"坦白说"等第一人称表达
        first_person = re.findall(r'[""]([^""]*[""]?)', snippet)
        if first_person:
            return first_person[0][:100]
        return ""

    def _compute_relevance(self, content: str, query_lower: str) -> float:
        """计算相关性分数（0-1）"""
        content_lower = content.lower()
        score = 0.0

        # 标题匹配（权重高）
        lines = content.split("\n")
        for line in lines[:5]:
            if any(kw in line.lower() for kw in query_lower.split()):
                score += 0.3

        # 查询词出现次数
        keywords = [k.strip() for k in query_lower.split() if len(k) > 1]
        for kw in keywords:
            count = content_lower.count(kw)
            score += min(count * 0.05, 0.3)

        # frontmatter 中的 tags 匹配
        if content.startswith("---"):
            fm = content.split("---")[1]
            if any(kw in fm.lower() for kw in keywords):
                score += 0.2

        return min(score, 1.0)

    def _empty_report(self, query: str, files: int, error: str = "") -> ObsidianSearchReport:
        return ObsidianSearchReport(
            query=query,
            results=[],
            style_notes=[f"搜索不可用: {error}"] if error else [],
            topic_tags=[],
            total_files_searched=files,
        )


def search_articles(query: str, article_dir: str = None, max_results: int = 5) -> dict:
    """
    快捷函数：搜索已发布文章。

    Returns:
        dict，含 results/style_notes/topic_tags/total_files_searched
    """
    searcher = ObsidianSearcher()
    report = searcher.search(query, max_results=max_results, article_dir=article_dir)
    return report.to_dict()
