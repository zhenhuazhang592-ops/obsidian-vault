# StyleFingerprintEngine - 风格指纹引擎
# 从已发布文章提取风格特征，生成个性化写作指令
# Phase 3 核心模块

import re
import json
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class SentenceMetrics:
    """句长指标"""
    avg_length: float = 0        # 平均句长
    variance: float = 0         # 句长方差（burstiness核心）
    short_ratio: float = 0      # 短句比例（<10字）
    long_ratio: float = 0        # 长句比例（>30字）
    max_length: int = 0          # 最长句
    min_length: int = 0          # 最短句


@dataclass
class VocabMetrics:
    """词汇指标"""
    unique_ratio: float = 0     # 词汇丰富度（unique/total）
    avg_word_length: float = 0   # 平均词长
    common_words: list = field(default_factory=list)   # 高频词
    rare_markers: list = field(default_factory=list)   # 特色词


@dataclass
class StructureMetrics:
    """结构指标"""
    h2_count: int = 0           # H2段落数
    quote_ratio: float = 0      # 引用比例
    list_ratio: float = 0        # 列表比例
    code_ratio: float = 0       # 代码块比例
    callout_count: int = 0      # 强调块数量


@dataclass
class FormatMetrics:
    """格式指标"""
    has_emoji: bool = False      # 表情使用
    emoji_count: int = 0
    has_divider: bool = False    # 分隔线
    has_table: bool = False     # 表格
    image_caption_style: str = "" # 配图说明风格


@dataclass
class ToneMetrics:
    """语气指标"""
    first_person: float = 0     # 第一人称比例（我/我们）
    question_ratio: float = 0   # 疑问句比例
    exclamation_ratio: float = 0 # 感叹句比例
    colloquial_markers: list = field(default_factory=list)  # 口语化词


@dataclass
class StyleFingerprint:
    """风格指纹完整结构"""
    sentence: SentenceMetrics = field(default_factory=SentenceMetrics)
    vocabulary: VocabMetrics = field(default_factory=VocabMetrics)
    structure: StructureMetrics = field(default_factory=StructureMetrics)
    format: FormatMetrics = field(default_factory=FormatMetrics)
    tone: ToneMetrics = field(default_factory=ToneMetrics)

    def to_dict(self) -> dict:
        return {
            "sentence": self.sentence.__dict__,
            "vocabulary": self.vocabulary.__dict__,
            "structure": self.structure.__dict__,
            "format": self.format.__dict__,
            "tone": self.tone.__dict__
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'StyleFingerprint':
        return cls(
            sentence=SentenceMetrics(**d.get("sentence", {})),
            vocabulary=VocabMetrics(**d.get("vocabulary", {})),
            structure=StructureMetrics(**d.get("structure", {})),
            format=FormatMetrics(**d.get("format", {})),
            tone=ToneMetrics(**d.get("tone", {}))
        )


class StyleFingerprintEngine:
    """风格指纹引擎"""

    def __init__(self, article_dir: str = None):
        self.article_dir = Path(article_dir) if article_dir else None
        self._chinese_patterns = {
            "short_sentence": re.compile(r'[^。！？；\n]{1,9}[。！？；\n]'),
            "long_sentence": re.compile(r'[^。！？；\n]{30,}[。！？；]'),
            "emoji": re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF]'),
            "chinese_word": re.compile(r'[\u4e00-\u9fff]+'),
            "first_person": re.compile(r'\b(我|我们|我的|我们的)\b'),
            "colloquial": re.compile(r'\b(说实话|坦白说|其实|说实话的|真的|基本上|大概|可能|应该)\b'),
        }

    def analyze_file(self, file_path: Path) -> StyleFingerprint:
        """分析单篇文章"""
        content = file_path.read_text(encoding='utf-8')
        return self.analyze_text(content)

    def analyze_text(self, text: str) -> StyleFingerprint:
        """分析文本，提取风格指纹"""
        # 移除frontmatter
        if text.startswith('---'):
            parts = text.split('---', 2)
            if len(parts) >= 3:
                text = parts[2]

        sentences = self._split_sentences(text)
        words = self._extract_words(text)

        return StyleFingerprint(
            sentence=self._extract_sentence_metrics(sentences),
            vocabulary=self._extract_vocab_metrics(words),
            structure=self._extract_structure_metrics(text),
            format=self._extract_format_metrics(text),
            tone=self._extract_tone_metrics(text, sentences)
        )

    def analyze_articles(self, article_dir: Path = None) -> StyleFingerprint:
        """批量分析目录下所有已发布文章"""
        dir_path = article_dir or self.article_dir
        if not dir_path or not dir_path.exists():
            return StyleFingerprint()

        fingerprints = []
        for file in dir_path.glob("*.md"):
            try:
                fp = self.analyze_file(file)
                fingerprints.append(fp)
            except Exception:
                continue

        if not fingerprints:
            return StyleFingerprint()

        # 合并多个指纹（取平均/主流值）
        return self._merge_fingerprints(fingerprints)

    def generate_writing_instructions(self, fingerprint: StyleFingerprint) -> str:
        """根据风格指纹生成个性化写作指令"""
        instructions = []

        # 句长要求
        instructions.append("【句长控制】")
        instructions.append(f"- 平均句长: {fingerprint.sentence.avg_length:.0f}字")
        instructions.append(f"- 短句(<10字)比例: {fingerprint.sentence.short_ratio:.0%}")
        instructions.append(f"- 长句(>30字)比例: {fingerprint.sentence.long_ratio:.0%}")
        instructions.append(f"- burstiness方差: {fingerprint.sentence.variance:.1f}")

        # 词汇要求
        if fingerprint.vocabulary.rare_markers:
            instructions.append(f"\n【特色词汇】: {', '.join(fingerprint.vocabulary.rare_markers[:10])}")

        # 结构要求
        instructions.append(f"\n【段落结构】")
        instructions.append(f"- H2数量: {fingerprint.structure.h2_count}个")
        instructions.append(f"- 引用块比例: {fingerprint.structure.quote_ratio:.0%}")
        instructions.append(f"- 列表比例: {fingerprint.structure.list_ratio:.0%}")

        # 语气要求
        instructions.append(f"\n【语气风格】")
        instructions.append(f"- 第一人称使用: {fingerprint.tone.first_person:.0%}")
        if fingerprint.tone.colloquial_markers:
            instructions.append(f"- 口语化词: {', '.join(fingerprint.tone.colloquial_markers[:5])}")

        # 格式要求
        instructions.append(f"\n【格式规范】")
        instructions.append(f"- 表情使用: {'是' if fingerprint.format.has_emoji else '否'}")
        instructions.append(f"- 配图说明: {fingerprint.format.image_caption_style or '标准格式'}")

        return "\n".join(instructions)

    def _split_sentences(self, text: str) -> list[str]:
        """拆分句子"""
        sentences = re.split(r'[。！？；\n]', text)
        return [s.strip() for s in sentences if s.strip()]

    def _extract_words(self, text: str) -> list[str]:
        """提取中文词"""
        words = self._chinese_patterns["chinese_word"].findall(text)
        return words

    def _extract_sentence_metrics(self, sentences: list[str]) -> SentenceMetrics:
        """提取句长指标"""
        lengths = [len(s) for s in sentences]
        if not lengths:
            return SentenceMetrics()

        avg = sum(lengths) / len(lengths)
        variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        short = sum(1 for l in lengths if l < 10) / len(lengths)
        long = sum(1 for l in lengths if l > 30) / len(lengths)

        return SentenceMetrics(
            avg_length=avg,
            variance=variance,
            short_ratio=short,
            long_ratio=long,
            max_length=max(lengths) if lengths else 0,
            min_length=min(lengths) if lengths else 0
        )

    def _extract_vocab_metrics(self, words: list[str]) -> VocabMetrics:
        """提取词汇指标"""
        if not words:
            return VocabMetrics()

        unique = len(set(words))
        total = len(words)
        avg_len = sum(len(w) for w in words) / total if words else 0

        counter = Counter(words)
        common = [w for w, _ in counter.most_common(20)]

        # 检测特色词（出现频率适中的词）
        rare = [w for w, c in counter.items() if 2 <= c <= 5][:10]

        return VocabMetrics(
            unique_ratio=unique / total if total else 0,
            avg_word_length=avg_len,
            common_words=common[:10],
            rare_markers=rare
        )

    def _extract_structure_metrics(self, text: str) -> StructureMetrics:
        """提取结构指标"""
        h2_count = len(re.findall(r'^##\s', text, re.MULTILINE))
        quote_count = len(re.findall(r'^>\s', text, re.MULTILINE))
        list_count = len(re.findall(r'^\d+\.\s', text, re.MULTILINE))
        code_count = len(re.findall(r'```', text))

        total = max(1, h2_count)

        return StructureMetrics(
            h2_count=h2_count,
            quote_ratio=quote_count / total,
            list_ratio=list_count / total,
            code_ratio=code_count / 2 / total
        )

    def _extract_format_metrics(self, text: str) -> FormatMetrics:
        """提取格式指标"""
        emoji_count = len(self._chinese_patterns["emoji"].findall(text))
        has_divider = '---' in text or '***' in text
        has_table = '|' in text and '---' in text
        has_emoji = emoji_count > 0

        # 配图说明风格
        img_captions = re.findall(r'（配图[：:]([^）]+)）', text)
        caption_style = img_captions[0] if img_captions else ""

        return FormatMetrics(
            has_emoji=has_emoji,
            emoji_count=emoji_count,
            has_divider=has_divider,
            has_table=has_table,
            image_caption_style=caption_style
        )

    def _extract_tone_metrics(self, text: str, sentences: list[str]) -> ToneMetrics:
        """提取语气指标"""
        fp_matches = self._chinese_patterns["first_person"].findall(text)
        fp_ratio = len(fp_matches) / max(1, len(sentences))

        question_count = sum(1 for s in sentences if '？' in s or '?' in s)
        question_ratio = question_count / max(1, len(sentences))

        exclamation_count = sum(1 for s in sentences if '！' in s)
        exclamation_ratio = exclamation_count / max(1, len(sentences))

        colloquial = self._chinese_patterns["colloquial"].findall(text)

        return ToneMetrics(
            first_person=fp_ratio,
            question_ratio=question_ratio,
            exclamation_ratio=exclamation_ratio,
            colloquial_markers=list(set(colloquial))[:10]
        )

    def _merge_fingerprints(self, fingerprints: list[StyleFingerprint]) -> StyleFingerprint:
        """合并多个风格指纹"""
        if len(fingerprints) == 1:
            return fingerprints[0]

        # 简单策略：取平均值或第一个非零值
        merged = StyleFingerprint()

        # Sentence
        avg_sentence = SentenceMetrics(
            avg_length=sum(f.sentence.avg_length for f in fingerprints) / len(fingerprints),
            variance=sum(f.sentence.variance for f in fingerprints) / len(fingerprints),
            short_ratio=sum(f.sentence.short_ratio for f in fingerprints) / len(fingerprints),
            long_ratio=sum(f.sentence.long_ratio for f in fingerprints) / len(fingerprints),
            max_length=max(f.sentence.max_length for f in fingerprints),
            min_length=min(f.sentence.min_length for f in fingerprints),
        )
        merged.sentence = avg_sentence

        # Vocab - 取第一个的common_words
        merged.vocabulary = fingerprints[0].vocabulary

        # Structure - 取平均
        avg_struct = StructureMetrics(
            h2_count=sum(f.structure.h2_count for f in fingerprints) // len(fingerprints),
            quote_ratio=sum(f.structure.quote_ratio for f in fingerprints) / len(fingerprints),
            list_ratio=sum(f.structure.list_ratio for f in fingerprints) / len(fingerprints),
            code_ratio=sum(f.structure.code_ratio for f in fingerprints) / len(fingerprints),
            callout_count=sum(f.structure.callout_count for f in fingerprints) // len(fingerprints),
        )
        merged.structure = avg_struct

        # Format - 只要有一个有就算有
        merged.format = FormatMetrics(
            has_emoji=any(f.format.has_emoji for f in fingerprints),
            emoji_count=max(f.format.emoji_count for f in fingerprints),
            has_divider=any(f.format.has_divider for f in fingerprints),
            has_table=any(f.format.has_table for f in fingerprints),
            image_caption_style=fingerprints[0].format.image_caption_style,
        )

        # Tone - 取平均
        avg_tone = ToneMetrics(
            first_person=sum(f.tone.first_person for f in fingerprints) / len(fingerprints),
            question_ratio=sum(f.tone.question_ratio for f in fingerprints) / len(fingerprints),
            exclamation_ratio=sum(f.tone.exclamation_ratio for f in fingerprints) / len(fingerprints),
            colloquial_markers=fingerprints[0].tone.colloquial_markers,
        )
        merged.tone = avg_tone

        return merged


if __name__ == "__main__":
    # 测试
    engine = StyleFingerprintEngine()

    test_text = """
这是第一句话。这是第二句话，这句话比较长一些。坦白说，我觉得这个很重要。

## 第一个段落

这是第三个句子。华哥说这是一个测试。
"""

    fp = engine.analyze_text(test_text)
    print(json.dumps(fp.to_dict(), ensure_ascii=False, indent=2))

    instructions = engine.generate_writing_instructions(fp)
    print("\n--- Writing Instructions ---")
    print(instructions)
