# core/anti_slop_engine.py - 反AI写作规则引擎
# 基于 anti-slop-writing 40+规则 + 词汇黑名单（Tier1/2/3）
# Turnitin-aware: 2025年8月起Turnitin专门检测humanizer工具输出

import re
from dataclasses import dataclass, field
from typing import Optional


# ────────────────────────────────────────────────────────────────
# Vocabulary Banlist
# ────────────────────────────────────────────────────────────────

TIER1_BANLIST = {
    # Significance puffers
    "pivotal", "crucial", "vital", "key", "significant", "essential",
    "groundbreaking", "remarkable", "transformative", "profound",
    # Analytical verbs
    "underscore", "highlight", "showcase", "foster", "garner",
    "delve", "embark", "leverage", "facilitate", "utilize",
    # Poetic nouns
    "tapestry", "landscape", "realm", "paradigm", "ecosystem", "journey", "nexus", "interplay",
    # Promotional adjectives
    "vibrant", "rich", "comprehensive", "robust", "seamless", "innovative", "dynamic", "cutting-edge",
    # Copula avoidance
    "serves as", "stands as", "boasts",
    # Chinese-specific AI腔
    "非常重要的", "具有重大意义的", "让我们一起", "综上所述", "总而言之",
    "十分关键", "不可或缺", "不言而喻",
}

TIER2_BANLIST = {
    # High frequency but context-dependent
    "harness", "navigate", "elevate", "foster", "bolster",
    "intricate", "multifaceted", "meticulous", "pivotal",
    "underscore", "showcase", "garner",
    # Chinese AI腔
    "说白了", "坦白讲", "必须指出", "不得不提", "值得关注",
}

TIER3_BANLIST = {
    # High density时标记
    "significant", "innovative", "effective", "powerful",
    "creative", "successful", "advanced",
}


# ────────────────────────────────────────────────────────────────
# Structural Rules
# ────────────────────────────────────────────────────────────────

@dataclass
class AntiSlopReport:
    """反AI写作报告"""
    tier1_violations: int = 0
    tier2_violations: int = 0
    tier3_violations: int = 0
    structural_violations: int = 0
    anti_slop_score: float = 100.0
    violations: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tier1_violations": self.tier1_violations,
            "tier2_violations": self.tier2_violations,
            "tier3_violations": self.tier3_violations,
            "structural_violations": self.structural_violations,
            "anti_slop_score": round(self.anti_slop_score, 1),
            "violations": self.violations
        }


class AntiSlopEngine:
    """
    反AI写作规则引擎

    15条核心结构规则 + 词汇黑名单
    """

    def __init__(self):
        pass

    def _word_pat(self, word: str) -> str:
        """
        中英混合友好的词边界检测。
        \b在Python3对中文+英文失效，用前后瞻替代。
        """
        return rf"(?<![a-zA-Z]){re.escape(word)}(?![a-zA-Z])"

    def check(self, text: str) -> AntiSlopReport:
        """检查文本中的anti-slop违规"""
        report = AntiSlopReport()

        # 1. 词汇黑名单检测
        self._check_tier1(text, report)
        self._check_tier2(text, report)
        self._check_tier3(text, report)

        # 2. 结构规则检测
        self._check_sentence_burstiness(text, report)
        self._check_tricolon(text, report)
        self._check_negative_parallelism(text, report)
        self._check_fake_ranges(text, report)
        self._check_tackon_ing(text, report)
        self._check_formulaic_conclusion(text, report)
        self._check_compulsory_summary(text, report)
        self._check_paragraph_rhythm(text, report)
        self._check_vertical_list(text, report)
        self._check_em_dash(text, report)
        self._check_sentence_types(text, report)
        self._check_paragraph_predictability(text, report)
        self._check_syntactic_depth(text, report)
        self._check_function_word_diversity(text, report)
        self._check_vocabulary_diversity(text, report)

        # 计算总分
        deductions = (
            report.tier1_violations * 10 +
            report.tier2_violations * 3 +
            report.tier3_violations * 1 +
            report.structural_violations * 2
        )
        report.anti_slop_score = max(0.0, 100.0 - deductions)
        return report

    def _add_violation(self, report: AntiSlopReport, rule: str, severity: str,
                       match: str, suggestion: str, line: int = 0):
        report.violations.append({
            "rule": rule,
            "severity": severity,
            "match": match[:60],
            "suggestion": suggestion,
            "line": line,
        })

    # ── Tier 检测 ────────────────────────────────────────────

    def _check_tier1(self, text: str, report: AntiSlopReport):
        """Tier 1: 始终替换"""
        for word in TIER1_BANLIST:
            # 纯中文词：用简单的 in 检查
            if all(ord(c) >= 0x4e00 for c in word):
                if word in text:
                    report.tier1_violations += 1
                    self._add_violation(report, "TIER1", "critical",
                                       word, f"替换 '{word}' 为更自然的表达")
            else:
                # 英文词：使用中英混合友好的边界
                pat = self._word_pat(word)
                if re.search(pat, text, re.IGNORECASE):
                    report.tier1_violations += 1
                    self._add_violation(report, "TIER1", "critical",
                                       word, f"替换 '{word}' 为更自然的表达")

    def _check_tier2(self, text: str, report: AntiSlopReport):
        """Tier 2: 成对出现时标记"""
        for word in TIER2_BANLIST:
            if all(ord(c) >= 0x4e00 for c in word):
                if word in text:
                    report.tier2_violations += 1
                    self._add_violation(report, "TIER2", "warning",
                                       word, f"检查 '{word}' 是否自然")
            else:
                pat = self._word_pat(word)
                if re.search(pat, text, re.IGNORECASE):
                    report.tier2_violations += 1
                    self._add_violation(report, "TIER2", "warning",
                                       word, f"检查 '{word}' 是否自然")

    def _check_tier3(self, text: str, report: AntiSlopReport):
        """Tier 3: 高密度时标记"""
        words_found = []
        for w in TIER3_BANLIST:
            if all(ord(c) >= 0x4e00 for c in w):
                if w in text:
                    words_found.append(w)
            else:
                pat = self._word_pat(w)
                if re.search(pat, text, re.IGNORECASE):
                    words_found.append(w)
        if len(words_found) >= 3:
            report.tier3_violations = len(words_found)
            self._add_violation(report, "TIER3", "info",
                               f"高密度词: {', '.join(words_found[:3])}",
                               "降低同类词密度")

    # ── 15条结构规则 ──────────────────────────────────────────

    def _check_sentence_burstiness(self, text: str, report: AntiSlopReport):
        """规则1: 剧烈变化的句长"""
        lines = text.split("\n")
        # 简单检查：所有句子长度方差
        sentences = re.split(r'[。！？；\n]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) < 3:
            return
        lengths = [len(s) for s in sentences]
        avg = sum(lengths) / len(lengths)
        variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        # 方差太小（<50）说明句子长度太均匀
        if variance < 50:
            report.structural_violations += 1
            self._add_violation(report, "BURSTINESS", "warning",
                               f"句长方差={variance:.0f}（过小）",
                               "增加长短句交替：3-5字短句 + 25+字长句混合")

    def _check_tricolon(self, text: str, report: AntiSlopReport):
        """规则2: 打破三连句"""
        lines = text.split("\n")
        for i, line in enumerate(lines, 1):
            # 检测 "第一、第二、第三" 或 "1. 2. 3." 格式
            if re.search(r"第一[、，]第二[、，]第三", line):
                report.structural_violations += 1
                self._add_violation(report, "TRICOLON", "info",
                                   "三连句结构", "自然列出要点，不强制凑三")

    def _check_negative_parallelism(self, text: str, report: AntiSlopReport):
        """规则3: 杀死负面平行"""
        if re.search(r"not only (?:is|are|do|does|can|will)", text, re.IGNORECASE):
            report.structural_violations += 1
            self._add_violation(report, "NEGATIVE_PARALLELISM", "warning",
                               "Not only...but句式", "直接陈述，不要负面平行")

    def _check_fake_ranges(self, text: str, report: AntiSlopReport):
        """规则4: 杀死虚假范围"""
        for m in re.finditer(r"from (\w+) to (\w+)", text):
            range_str = m.group()
            # 简单启发式：范围太宽或无意义
            if len(m.group(1)) < 3 or len(m.group(2)) < 3:
                continue
            report.structural_violations += 1
            self._add_violation(report, "FAKE_RANGE", "info",
                               range_str, "检查是否是有意义的实际范围")

    def _check_tackon_ing(self, text: str, report: AntiSlopReport):
        """规则5: 不使用分词tack-on"""
        lines = text.split("\n")
        for i, line in enumerate(lines, 1):
            # 检测 "-ing 从句" 在句末
            if re.search(r"\w+ing[，,]?\s*$", line) and len(line) < 15:
                report.structural_violations += 1
                self._add_violation(report, "TACKON_ING", "info",
                                   line.strip(), "将分词结构改为独立句子或删除")

    def _check_formulaic_conclusion(self, text: str, report: AntiSlopReport):
        """规则6: 不使用公式化结论"""
        patterns = [
            r"Despite challenges?[,，]?\s*\w+ (?:continues?|remains?|keeps)",
            r"(?:In summary?|To summarize?|In conclusion?),?\s*\w+",
        ]
        for m in re.finditer("|".join(patterns), text, re.IGNORECASE):
            report.structural_violations += 1
            self._add_violation(report, "FORMULAIC_CONCLUSION", "info",
                               m.group()[:40], "删除公式化结论，用具体事实")

    def _check_compulsory_summary(self, text: str, report: AntiSlopReport):
        """规则7: 不使用强制性总结"""
        patterns = [r"overall\b", r"in conclusion\b", r"to sum up\b", r"all in all\b"]
        for i, line in enumerate(text.split("\n"), 1):
            for pat in patterns:
                if re.search(pat, line, re.IGNORECASE):
                    report.structural_violations += 1
                    self._add_violation(report, "COMPULSORY_SUMMARY", "info",
                                       line.strip()[:40], "删除总结性词语，直接给结论")

    def _check_paragraph_rhythm(self, text: str, report: AntiSlopReport):
        """规则8: 段落节奏（不规则段落长度）"""
        paragraphs = re.split(r"\n\n+", text)
        if len(paragraphs) < 3:
            return
        lengths = [len(p) for p in paragraphs]
        avg = sum(lengths) / len(lengths)
        variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        if variance < 100 and avg > 80:
            report.structural_violations += 1
            self._add_violation(report, "PARAGRAPH_RHYTHM", "info",
                               f"段落长度方差={variance:.0f}（过于均匀）",
                               "段落长度要有明显变化，不要整齐划一")

    def _check_vertical_list(self, text: str, report: AntiSlopReport):
        """规则9: 垂直列表限制"""
        list_items = len(re.findall(r"^\d+[.、]", text, re.MULTILINE))
        total_lines = len(text.split("\n"))
        if total_lines > 0 and list_items / total_lines > 0.25:
            report.structural_violations += 1
            self._add_violation(report, "VERTICAL_LIST", "info",
                               f"列表占比{list_items}/{total_lines}行",
                               "将部分列表改为自然段落叙述")

    def _check_em_dash(self, text: str, report: AntiSlopReport):
        """规则10: Em dash限制"""
        dash_count = text.count("—") + text.count("--")
        word_count = len(text)
        if word_count > 0 and dash_count > word_count / 300:
            report.structural_violations += 1
            self._add_violation(report, "EM_DASH", "info",
                               f"Em dash: {dash_count}个",
                               "每500字最多1个em dash")

    def _check_sentence_types(self, text: str, report: AntiSlopReport):
        """规则11: 句子类型变化"""
        sentences = re.split(r'[。！？\n]', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s) > 2]
        if len(sentences) < 5:
            return
        has_question = any('？' in s or '?' in s for s in sentences)
        has_exclamation = any('！' in s or '!' in s for s in sentences)
        has_fragment = sum(1 for s in sentences if len(s) < 10) / len(sentences)
        if not has_question and not has_exclamation and has_fragment < 0.1:
            report.structural_violations += 1
            self._add_violation(report, "SENTENCE_TYPES", "info",
                               "缺少句式变化",
                               "添加疑问句、感叹句或短句碎片，打破单调")

    def _check_paragraph_predictability(self, text: str, report: AntiSlopReport):
        """规则12: 打破段落可预测性"""
        # 检查是否每个段落都以 topic sentence 开头
        paragraphs = re.split(r"\n\n+", text)
        starts_with_topic = 0
        for p in paragraphs:
            lines = [l.strip() for l in p.strip().split("\n") if l.strip()]
            if not lines:
                continue
            first = lines[0]
            # 如果第一句是结论性陈述（过长且无标点结尾）
            if len(first) > 30 and not re.search(r'[。！？；]', first[-5:]):
                starts_with_topic += 1
        if paragraphs and starts_with_topic / len(paragraphs) > 0.7:
            report.structural_violations += 1
            self._add_violation(report, "PARAGRAPH_PREDICTABILITY", "info",
                               "段落过于规律",
                               "不要每段都以结论开头，变化段落结构")

    def _check_syntactic_depth(self, text: str, report: AntiSlopReport):
        """规则13: 句法深度变化"""
        # 浅层句：主语+谓语+宾语（<15字）
        # 深层句：从句或并列句（>25字）
        sentences = re.split(r'[。！？；\n]', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s) > 2]
        if len(sentences) < 5:
            return
        shallow = sum(1 for s in sentences if 5 <= len(s) <= 15)
        deep = sum(1 for s in sentences if len(s) > 25)
        ratio = deep / len(sentences) if sentences else 0
        # 如果深层句太少或太多
        if ratio < 0.1 or ratio > 0.5:
            report.structural_violations += 1
            self._add_violation(report, "SYNTAX_DEPTH", "info",
                               f"深层句占比{int(ratio*100)}%",
                               "浅层句+深层句交替，不要全是短句或长句")

    def _check_function_word_diversity(self, text: str, report: AntiSlopReport):
        """规则14: 功能词多样性"""
        # 统计 and/but/so/because/however 的使用频率
        func_words = {
            "and": len(re.findall(r'\band\b', text, re.IGNORECASE)),
            "but": len(re.findall(r'\bbut\b', text, re.IGNORECASE)),
            "so": len(re.findall(r'\bso\b', text, re.IGNORECASE)),
            "because": len(re.findall(r'\bbecause\b', text, re.IGNORECASE)),
            "however": len(re.findall(r'\bhowever\b', text, re.IGNORECASE)),
        }
        total = sum(func_words.values())
        if total > 0:
            for word, count in func_words.items():
                if count / total > 0.5:
                    report.structural_violations += 1
                    self._add_violation(report, "FUNCTION_WORD", "info",
                                       f"{word}占比{int(count/total*100)}%过高",
                                       "功能词使用要分散，不要过度依赖某一个")
                    break

    def _check_vocabulary_diversity(self, text: str, report: AntiSlopReport):
        """规则15: 词汇多样性（Type-Token Ratio）"""
        words = re.findall(r'[\u4e00-\u9fff]+', text)
        if len(words) < 10:
            return
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.4:
            report.structural_violations += 1
            self._add_violation(report, "VOCAB_DIVERSITY", "info",
                               f"词汇丰富度={unique_ratio:.2f}（过低）",
                               "增加同义表达，避免重复用词")

    # ── 快速检查（用于 CLI）─────────────────────────────────

    def quick_check(self, text: str) -> tuple[bool, str]:
        """
        快速检查文本是否通过anti-slop检测。

        Returns:
            (passed, reason)
        """
        if not text or len(text) < 50:
            return True, "文本过短，跳过检测"

        # 快速Tier1检查
        for word in TIER1_BANLIST:
            if all(ord(c) >= 0x4e00 for c in word):
                if word in text:
                    return False, f"发现禁用词: {word}"
            else:
                pat = rf"(?<![a-zA-Z]){re.escape(word)}(?![a-zA-Z])"
                if re.search(pat, text, re.IGNORECASE):
                    return False, f"发现禁用词: {word}"

        # 快速结构检查
        if re.search(r"not only (?:is|are|do)", text, re.IGNORECASE):
            return False, "发现负面平行结构: Not only..."

        return True, "通过anti-slop检测"


# ────────────────────────────────────────────────────────────────
# 辅助：生成润色建议
# ────────────────────────────────────────────────────────────────

def generate_polish_suggestions(anti_slop_report: AntiSlopReport,
                                humanizer_report: HumanizerReport) -> str:
    """基于两份报告生成润色建议"""
    lines = ["【润色建议】"]

    # Tier1优先
    if anti_slop_report.tier1_violations > 0:
        lines.append(f"\n⚠️  必须替换（{anti_slop_report.tier1_violations}处）:")
        for v in anti_slop_report.violations:
            if v["severity"] == "critical":
                lines.append(f"  - {v['match']}: {v['suggestion']}")

    # P0 AI模式
    p0_issues = [d for d in humanizer_report.detections if d.severity == "P0"]
    if p0_issues:
        lines.append(f"\n🚨 P0严重问题（必须修复）:")
        for d in p0_issues:
            lines.append(f"  - [{d.pattern_id}] {d.match}: {d.suggestion}")

    # P1明显AI腔
    p1_issues = [d for d in humanizer_report.detections if d.severity == "P1"]
    if p1_issues:
        lines.append(f"\n⚡ P1明显AI腔（建议修复）:")
        for d in p1_issues[:5]:  # 只显示前5个
            lines.append(f"  - [{d.pattern_id}] {d.match}: {d.suggestion}")

    if anti_slop_report.structural_violations > 0:
        lines.append(f"\n📐 结构问题（{anti_slop_report.structural_violations}处）:")
        structural_only = [v for v in anti_slop_report.violations
                         if v["rule"] not in ("TIER1", "TIER2", "TIER3")]
        for v in structural_only[:5]:
            lines.append(f"  - [{v['rule']}] {v['suggestion']}")

    return "\n".join(lines)
