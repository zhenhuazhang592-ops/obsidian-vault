# extract_author_style tool
import os
import re
from collections import Counter
from pathlib import Path

from app.tools.base import BaseTool


class ExtractAuthorStyleTool(BaseTool):
    """Extract writing style profile from Obsidian vault articles."""

    name = "extract_author_style"
    description = "Extract author's writing style from Obsidian vault articles."

    def execute(
        self,
        vault_path: str,
        n: int = 3,
        **kwargs,
    ) -> dict:
        """
        Extract StyleProfile from n articles in vault.

        Fallback (n < 3): tone=formal, avg_sentence_length=25, other fields empty.
        """
        if n < 3:
            return {
                "tone": "formal",
                "avg_sentence_length": 25.0,
                "emoji_density": 0.0,
                "favorite_phrases": [],
                "structure_preference": "mixed",
                "paragraph_length_avg": 150,
                "_warning": f"insufficient articles (n={n}), using defaults",
            }

        articles = self._find_articles(vault_path, n)
        if not articles:
            return {
                "tone": "formal",
                "avg_sentence_length": 25.0,
                "emoji_density": 0.0,
                "favorite_phrases": [],
                "structure_preference": "mixed",
                "paragraph_length_avg": 150,
                "_warning": f"no articles found in {vault_path}, using defaults",
            }

        texts = [self._read_article(a) for a in articles]
        combined = "\n".join(texts)

        return {
            "tone": self._detect_tone(combined),
            "avg_sentence_length": self._avg_sentence_length(texts),
            "emoji_density": self._emoji_density(combined, len(combined)),
            "favorite_phrases": self._favorite_phrases(combined, top_n=20),
            "structure_preference": self._detect_structure(texts),
            "paragraph_length_avg": self._avg_paragraph_length(texts),
        }

    def _find_articles(self, vault_path: str, n: int) -> list[Path]:
        """Find markdown articles in vault."""
        vault = Path(vault_path)
        if not vault.exists():
            return []
        md_files = sorted(vault.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        return md_files[:n]

    def _read_article(self, path: Path) -> str:
        """Read article content, skipping frontmatter."""
        try:
            with open(path) as f:
                content = f.read()
            # Strip Obsidian frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    content = parts[2]
            return content.strip()
        except OSError:
            return ""

    def _detect_tone(self, text: str) -> str:
        """Detect writing tone."""
        casual_words = ["但是", "其实", "不过", "感觉", "觉得", "应该", "可能", "大概"]
        formal_words = ["因此", "然而", "此外", "综上所述", "由此可见", "根据", "表明"]
        sharp_words = ["绝对", "必须", "不容置疑", "毫无疑问", "必然", "一定"]

        text_lower = text.lower()
        casual_count = sum(1 for w in casual_words if w in text_lower)
        formal_count = sum(1 for w in formal_words if w in text_lower)
        sharp_count = sum(1 for w in sharp_words if w in text_lower)

        if sharp_count > casual_count + formal_count:
            return "sharp"
        elif casual_count > formal_count:
            return "casual"
        elif formal_count > casual_count:
            return "formal"
        return "gentle"

    def _avg_sentence_length(self, texts: list[str]) -> float:
        """Estimate average sentence length in characters."""
        sentences = re.split(r"[。！？.!?]", "\n".join(texts))
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return 25.0
        return sum(len(s) for s in sentences) / len(sentences)

    def _emoji_density(self, text: str, total_len: int) -> float:
        """Calculate emoji usage per thousand characters."""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE,
        )
        emojis = emoji_pattern.findall(text)
        return len("".join(emojis)) / (total_len / 1000) if total_len > 0 else 0.0

    def _favorite_phrases(self, text: str, top_n: int = 20) -> list[str]:
        """Extract most frequent 2-4 character phrases."""
        # Chinese phrase extraction: 2-4 character ngrams
        words = re.findall(r"[\u4e00-\u9fa5]{2,4}", text)
        if not words:
            return []
        # Count consecutive pairs
        pairs = ["".join(pair) for pair in zip(words[:-1], words[1:])]
        counter = Counter(pairs)
        return [phrase for phrase, _ in counter.most_common(top_n)]

    def _detect_structure(self, texts: list[str]) -> str:
        """Detect article structure preference."""
        structures = {"list": 0, "story": 0, "mixed": 0}
        list_markers = ["\n- ", "\n1. ", "\n一、", "\n（一）", "第一", "第二"]
        story_markers = ["然后", "接着", "于是", "不久", "原来", "那天", "记得"]

        for text in texts:
            has_list = any(m in text for m in list_markers)
            has_story = any(m in text for m in story_markers)
            if has_list and has_story:
                structures["mixed"] += 1
            elif has_list:
                structures["list"] += 1
            elif has_story:
                structures["story"] += 1

        return max(structures, key=structures.get)  # type: ignore

    def _avg_paragraph_length(self, texts: list[str]) -> float:
        """Average paragraph length in characters."""
        paragraphs = []
        for text in texts:
            paras = [p.strip() for p in text.split("\n\n") if p.strip()]
            paragraphs.extend(paras)
        if not paragraphs:
            return 150.0
        return sum(len(p) for p in paragraphs) / len(paragraphs)
