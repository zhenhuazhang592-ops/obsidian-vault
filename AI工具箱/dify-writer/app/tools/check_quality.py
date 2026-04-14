# check_quality tool
from app.tools.base import BaseTool


class CheckQualityTool(BaseTool):
    """Quality scoring for polished articles."""

    name = "check_quality"
    description = "Check article quality and return score + issues."

    def execute(
        self,
        article: str,
        framework: str = "痛点型",
        platform: str = "wechat",
        session_id: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Score article quality (0-100).

        Returns quality_score (float) and issues (list[str]).
        """
        if not article or len(article) < 100:
            return {
                "quality_score": 0.0,
                "issues": ["文章过短，无法评估"],
                "suggestions": [],
            }

        issues = []
        suggestions = []
        score = 100.0

        # Length check
        word_count = len(article)
        if word_count < 800:
            issues.append(f"文章过短（{word_count}字），公众号建议1500-3000字")
            score -= 20
        elif word_count > 5000:
            issues.append(f"文章过长（{word_count}字），建议精简")
            score -= 10

        # Framework-specific checks
        if framework == "痛点型":
            if "?" not in article and "？" not in article:
                issues.append("痛点型文章应包含问题引发读者思考")
                score -= 10
        elif framework == "清单型":
            if not any(c in article for c in ["1.", "2.", "一、", "（一）"]):
                issues.append("清单型文章应有明确的序号标记")
                score -= 15

        # Emoji density check (公众号不宜过多)
        import re
        emoji_count = len(re.findall(r"[\U0001F300-\U0001F9FF]", article))
        if emoji_count > 30:
            suggestions.append(f"emoji 使用过多（{emoji_count}个），建议精简")
            score -= 5

        # Repetition check (simple)
        words = article[:500]  # Check first 500 chars
        if len(set(words)) < len(words) * 0.3:
            issues.append("文章存在大量重复内容")
            score -= 15

        # Structure check
        if "\n\n" not in article[:200]:
            suggestions.append("建议添加段落空行提升可读性")

        score = max(0.0, min(100.0, score))

        return {
            "quality_score": score,
            "issues": issues,
            "suggestions": suggestions,
            "word_count": word_count,
        }
