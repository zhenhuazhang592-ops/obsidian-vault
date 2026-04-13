# core/seo_reporter.py - SEO报告生成器
# Phase 4: 4项评分 + 关键词图谱

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SEOReport:
    """SEO分析报告"""
    # 4项评分
    seo_score: float = 0.0      # SEO优化评分
    geo_score: float = 0.0       # GEO（AI引用优化）评分
    de_ai_score: float = 0.0     # 去AI味评分
    readability_score: float = 0.0  # 可读性评分

    # 关键词分析
    primary_keyword: str = ""
    primary_count: int = 0       # 核心关键词出现次数
    primary_density: float = 0.0  # 关键词密度 %
    secondary_keywords: list[str] = field(default_factory=list)
    long_tail_keywords: list[str] = field(default_factory=list)

    # 详细数据
    title_has_keyword: bool = False
    h2_has_keyword: list[bool] = field(default_factory=list)  # 每个H2是否含关键词
    first_100_has_keyword: bool = False  # 前100字是否含核心关键词
    keyword_placement_score: float = 0.0  # 关键词布局得分

    # GEO信号
    has_statistics: bool = False
    has_citations: bool = False
    has_definitive_statements: bool = False  # 明确陈述句
    geo_signals: list[str] = field(default_factory=list)

    # 详细建议
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "seo_score": round(self.seo_score, 1),
            "geo_score": round(self.geo_score, 1),
            "de_ai_score": round(self.de_ai_score, 1),
            "readability_score": round(self.readability_score, 1),
            "primary_keyword": self.primary_keyword,
            "primary_count": self.primary_count,
            "primary_density": round(self.primary_density, 2),
            "secondary_keywords": self.secondary_keywords,
            "long_tail_keywords": self.long_tail_keywords,
            "title_has_keyword": self.title_has_keyword,
            "h2_has_keyword": self.h2_has_keyword,
            "first_100_has_keyword": self.first_100_has_keyword,
            "keyword_placement_score": round(self.keyword_placement_score, 1),
            "geo_signals": self.geo_signals,
            "suggestions": self.suggestions,
        }

    def format_summary(self) -> str:
        """人类可读摘要"""
        lines = [
            "【SEO分析报告】",
            "",
            f"SEO评分：{self.seo_score:.0f}/100",
            f"GEO评分：{self.geo_score:.0f}/100",
            f"去AI味：{self.de_ai_score:.0f}/100",
            f"可读性：{self.readability_score:.0f}/100",
            "",
            f"核心关键词「{self.primary_keyword}」出现次数：{self.primary_count}次",
            f"关键词密度：{self.primary_density:.1f}%",
            "",
        ]
        if self.suggestions:
            lines.append("⚠️ 改进建议：")
            for s in self.suggestions:
                lines.append(f"  • {s}")
        return "\n".join(lines)


class SEOReporter:
    """
    SEO报告生成器

    4项评分体系：
    1. SEO评分 — 关键词布局、密度、位置
    2. GEO评分 — AI引用优化（数据、引用、定义性陈述）
    3. 去AI味评分 — 源自HumanizerEngine
    4. 可读性评分 — 句长、段落长度、词汇难度
    """

    def __init__(self):
        pass

    def report(
        self,
        article_content: str,
        title: str = "",
        seo_keywords: Optional[dict] = None,
        humanizer_score: float = 100.0,
        anti_slop_score: float = 100.0,
    ) -> SEOReport:
        """
        生成完整SEO报告。

        Args:
            article_content: 文章正文（不含标题）
            title: 文章标题
            seo_keywords: {"primary": str, "secondary": [], "long_tail": []}
            humanizer_score: 来自HumanizerEngine的评分 (0-100)
            anti_slop_score: 来自AntiSlopEngine的评分 (0-100)
        """
        seo_keywords = seo_keywords or {}
        primary = seo_keywords.get("primary", "")
        secondary = seo_keywords.get("secondary", [])
        long_tail = seo_keywords.get("long_tail", [])

        full_text = f"{title}\n{article_content}" if title else article_content
        report = SEOReport(
            primary_keyword=primary,
            secondary_keywords=secondary,
            long_tail_keywords=long_tail,
        )

        # 1. 关键词分析
        self._analyze_keywords(report, full_text, primary, secondary, long_tail)

        # 2. GEO信号检测
        self._analyze_geo_signals(report, article_content)

        # 3. 可读性评分
        self._analyze_readability(report, article_content)

        # 4. 计算4项总分
        self._compute_scores(report, humanizer_score, anti_slop_score)

        return report

    def _analyze_keywords(
        self,
        report: SEOReport,
        full_text: str,
        primary: str,
        secondary: list,
        long_tail: list,
    ):
        """关键词布局分析"""
        if not primary:
            report.suggestions.append("未设置核心关键词")
            return

        # 统计核心关键词出现次数
        primary_pat = rf"(?<![a-zA-Z]){re.escape(primary)}(?![a-zA-Z])"
        primary_matches = re.findall(primary_pat, full_text, re.IGNORECASE)
        report.primary_count = len(primary_matches)

        # 关键词密度 = 关键词字数 / 总字数 * 100
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', full_text)
        total_chars = sum(len(c) for c in chinese_chars)
        if total_chars > 0 and primary:
            report.primary_density = (report.primary_count * len(primary) / total_chars) * 100

        # 标题是否含关键词
        report.title_has_keyword = bool(re.search(primary_pat, report.title_has_keyword or "", re.IGNORECASE))

        # H2是否含关键词
        h2_sections = re.split(r"^##\s+", full_text, flags=re.MULTILINE)[1:]
        for section in h2_sections:
            header_line = section.split("\n")[0] if section else ""
            has_kw = bool(re.search(primary_pat, header_line, re.IGNORECASE))
            report.h2_has_keyword.append(has_kw)

        # 前100字是否含关键词
        first_100 = full_text[:100]
        report.first_100_has_keyword = bool(re.search(primary_pat, first_100, re.IGNORECASE))

        # 关键词布局得分
        placement_score = 0
        if report.title_has_keyword:
            placement_score += 25
        if report.first_100_has_keyword:
            placement_score += 25
        h2_with_kw = sum(1 for x in report.h2_has_keyword if x)
        if report.h2_has_keyword:
            placement_score += 25 * (h2_with_kw / len(report.h2_has_keyword))
        # 密度合理（1-2%）
        if 0.8 <= report.primary_density <= 3.0:
            placement_score += 25
        elif 0.5 <= report.primary_density < 0.8 or 3.0 < report.primary_density <= 5.0:
            placement_score += 12
        report.keyword_placement_score = placement_score

        # 生成建议
        if report.primary_count == 0:
            report.suggestions.append(f"核心关键词「{primary}」未在文章中出现")
        elif report.primary_count < 3:
            report.suggestions.append(f"核心关键词「{primary}」出现次数偏少（{report.primary_count}次，建议3-5次）")
        if report.primary_density < 0.5:
            report.suggestions.append(f"关键词密度偏低（{report.primary_density:.1f}%，建议1-2%）")
        elif report.primary_density > 4.0:
            report.suggestions.append(f"关键词密度偏高（{report.primary_density:.1f}%，可能有堆砌嫌疑）")
        if not report.title_has_keyword:
            report.suggestions.append("标题中未包含核心关键词")
        if not report.first_100_has_keyword:
            report.suggestions.append("文章前100字中未包含核心关键词")
        if report.h2_has_keyword and not any(report.h2_has_keyword):
            report.suggestions.append("H2标题中未融入核心关键词")

    def _analyze_geo_signals(self, report: SEOReport, article_content: str):
        """GEO（AI引用优化）信号检测"""
        # 具体数据检测
        statistics_patterns = [
            r'\d+%', r'\d+倍', r'\d+万', r'\d+亿',
            r'\d+年', r'\d+月', r'\d+日',
            r'据\d+年', r'超过\d+',
        ]
        report.has_statistics = any(
            re.search(pat, article_content)
            for pat in statistics_patterns
        )

        # 引用检测
        citation_patterns = [
            r'据[^\s]{2,10}报道', r'来自[^\s]{2,10}的数据显示',
            r'[^\s]{2,10}指出', r'[^\s]{2,10}表示',
            r'正如[^\s]{2,10}所说', r'根据[^\s]{2,10}',
        ]
        report.has_citations = any(
            re.search(pat, article_content)
            for pat in citation_patterns
        )

        # 明确陈述句（定义性陈述）
        definitive_patterns = [
            r'是[^\s]{1,20}的', r'不是[^\s]{1,20}的',
            r'指[^\s]{1,20}', r'称为[^\s]{1,20}',
        ]
        report.has_definitive_statements = sum(
            len(re.findall(pat, article_content))
            for pat in definitive_patterns
        ) >= 2

        # 收集GEO信号
        if report.has_statistics:
            report.geo_signals.append("包含具体数据")
        if report.has_citations:
            report.geo_signals.append("包含引用标注")
        if report.has_definitive_statements:
            report.geo_signals.append("包含定义性陈述")

        # GEO评分（基于信号数量）
        geo_signals_count = len(report.geo_signals)
        report.geo_score = min(100, 40 + geo_signals_count * 20)

    def _analyze_readability(self, report: SEOReport, article_content: str):
        """可读性分析"""
        # 句子长度分析
        sentences = re.split(r'[。！？；\n]', article_content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s) > 2]

        if sentences:
            lengths = [len(s) for s in sentences]
            avg_len = sum(lengths) / len(lengths)
            # 理想平均句长：15-25字
            if 10 <= avg_len <= 30:
                readability = 85
            elif 5 <= avg_len < 10:
                readability = 70
            else:
                readability = 75
        else:
            readability = 60

        # 段落长度变化
        paragraphs = re.split(r'\n\n+', article_content)
        if len(paragraphs) >= 3:
            para_lengths = [len(p) for p in paragraphs]
            avg_para = sum(para_lengths) / len(para_lengths)
            variance = sum((l - avg_para) ** 2 for l in para_lengths) / len(para_lengths)
            if variance > 100:
                readability += 5
            elif variance < 50:
                readability -= 10

        report.readability_score = min(100, readability)

    def _compute_scores(
        self,
        report: SEOReport,
        humanizer_score: float,
        anti_slop_score: float,
    ):
        """计算4项总分"""
        # SEO评分 = 关键词布局得分（0-100）
        report.seo_score = report.keyword_placement_score

        # 去AI味 = humanizer和anti_slop的平均
        report.de_ai_score = (humanizer_score + anti_slop_score) / 2


def generate_seo_report(
    article_content: str,
    title: str = "",
    seo_keywords: Optional[dict] = None,
    humanizer_score: float = 100.0,
    anti_slop_score: float = 100.0,
) -> SEOReport:
    """
    快捷函数：生成SEO报告。
    """
    reporter = SEOReporter()
    return reporter.report(
        article_content=article_content,
        title=title,
        seo_keywords=seo_keywords,
        humanizer_score=humanizer_score,
        anti_slop_score=anti_slop_score,
    )
