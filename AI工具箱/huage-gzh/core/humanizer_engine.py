# core/humanizer_engine.py - AI写作模式检测引擎
# 基于 29类AI写作模式（P0严重/P1明显/P2可优化）
# 来源: humanizer skill + avoid-ai-writing skill

import re
from dataclasses import dataclass, field
from typing import Optional


# ────────────────────────────────────────────────────────────────
# Severity Tiers
# ────────────────────────────────────────────────────────────────

class Severity:
    P0 = "P0"   # 必须修复：信任度杀手
    P1 = "P1"   # 发布前必须修复：明显AI腔
    P2 = "P2"   # 可优化：文体美化


@dataclass
class Detection:
    pattern_id: str
    pattern_name: str
    severity: str
    match: str
    suggestion: str
    line: int = 0


@dataclass
class HumanizerReport:
    """检测报告"""
    total_issues: int = 0
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    humanizer_score: float = 100.0  # 100 = 最像人写
    detections: list[Detection] = field(default_factory=list)

    def is_clean(self) -> bool:
        """是否通过检测（P0=0才通过）"""
        return self.p0_count == 0

    def to_dict(self) -> dict:
        return {
            "total_issues": self.total_issues,
            "p0_count": self.p0_count,
            "p1_count": self.p1_count,
            "p2_count": self.p2_count,
            "humanizer_score": round(self.humanizer_score, 1),
            "passed": self.is_clean(),
            "detections": [
                {
                    "pattern_id": d.pattern_id,
                    "pattern_name": d.pattern_name,
                    "severity": d.severity,
                    "match": d.match,
                    "suggestion": d.suggestion,
                    "line": d.line,
                }
                for d in self.detections
            ]
        }


# ────────────────────────────────────────────────────────────────
# Pattern Definitions
# ────────────────────────────────────────────────────────────────

class HumanizerEngine:
    """
    29类AI写作模式检测器
    """

    def __init__(self):
        self._patterns = self._build_patterns()

    # ── 分数权重 ──────────────────────────────────────────────

    SCORE_WEIGHTS = {
        Severity.P0: 15,   # 每个P0扣15分
        Severity.P1: 5,    # 每个P1扣5分
        Severity.P2: 1,   # 每个P2扣1分
    }

    def detect(self, text: str) -> HumanizerReport:
        """检测文本中的AI写作模式"""
        lines = text.split("\n")
        report = HumanizerReport()
        seen_ids = set()  # 去重：同一模式只计一次

        for pattern_id, checker in self._patterns.items():
            matches = checker["check"](text, lines)
            for match_str, line_num in matches:
                if pattern_id not in seen_ids:
                    seen_ids.add(pattern_id)
                    detection = Detection(
                        pattern_id=pattern_id,
                        pattern_name=checker["name"],
                        severity=checker["severity"],
                        match=match_str[:80],  # 截断避免过长
                        suggestion=checker["suggestion"],
                        line=line_num,
                    )
                    report.detections.append(detection)

                    # 统计
                    if checker["severity"] == Severity.P0:
                        report.p0_count += 1
                    elif checker["severity"] == Severity.P1:
                        report.p1_count += 1
                    else:
                        report.p2_count += 1

        report.total_issues = len(report.detections)

        # 计算人性化分数
        deductions = (
            report.p0_count * 15 +
            report.p1_count * 5 +
            report.p2_count * 1
        )
        report.humanizer_score = max(0.0, 100.0 - deductions)

        return report

    def _build_patterns(self) -> dict:
        """构建所有29个检测模式"""
        return {

            # ═══════════════════════════════════════════════════════
            # P0 — 信任度杀手（Credibility Killers）
            # ═══════════════════════════════════════════════════════

            "P0-01-cutoff": {
                "name": "知识截止免责声明",
                "severity": Severity.P0,
                "suggestion": "删除 'as of my last update' 或主动查找最新信息",
                "check": self._check_cutoff,
            },
            "P0-02-chatbot": {
                "name": "Chatbot响应痕迹",
                "severity": Severity.P0,
                "suggestion": "删除 'I hope this helps', 'Great question!' 等Chatbot客套话",
                "check": self._check_chatbot,
            },
            "P0-03-vague-attribution": {
                "name": "模糊归属无来源",
                "severity": Severity.P0,
                "suggestion": "将 'Experts believe' 等改为具体人或机构名称",
                "check": self._check_vague_attribution,
            },
            "P0-04-significance-inflation": {
                "name": "重要性夸大",
                "severity": Severity.P0,
                "suggestion": "删除对常规事件的夸大描述，直接陈述事实",
                "check": self._check_significance_inflation,
            },

            # ═══════════════════════════════════════════════════════
            # P1 — 明显AI腔（Obvious AI Smell）
            # ═══════════════════════════════════════════════════════

            "P1-01-ai-highfreq": {
                "name": "AI高频词",
                "severity": Severity.P1,
                "suggestion": "替换: delve→探索, landscape→领域, tapestry→图景, crucial→关键",
                "check": self._check_ai_highfreq,
            },
            "P1-02-template-phrases": {
                "name": "模板短语",
                "severity": Severity.P1,
                "suggestion": "删除 'In today's rapidly evolving...' 等模板开头",
                "check": self._check_template_phrases,
            },
            "P1-03-lets-transition": {
                "name": "Let's过渡句式",
                "severity": Severity.P1,
                "suggestion": "删除 'Let's dive in', 'Let's explore...' 等",
                "check": self._check_lets_transition,
            },
            "P1-04-synonym-cycling": {
                "name": "同义词循环",
                "severity": Severity.P1,
                "suggestion": "同一概念保持用词一致，不要换同义词",
                "check": self._check_synonym_cycling,
            },
            "P1-05-copula-avoidance": {
                "name": "连系动词规避",
                "severity": Severity.P1,
                "suggestion": "替换: 'serves as'→is, 'features'→has, 'boasts'→has",
                "check": self._check_copula_avoidance,
            },
            "P1-06-negative-parallelism": {
                "name": "负面平行结构",
                "severity": Severity.P1,
                "suggestion": "删除 'Not only X, but also Y' 结构，直接陈述",
                "check": self._check_negative_parallelism,
            },

            # ═══════════════════════════════════════════════════════
            # P2 — 文体美化（Stylistic Polish）
            # ═══════════════════════════════════════════════════════

            "P2-01-generic-conclusion": {
                "name": "通用结论",
                "severity": Severity.P2,
                "suggestion": "删除 'The future looks bright' 等空泛结论，用具体事实",
                "check": self._check_generic_conclusion,
            },
            "P2-02-compulsive-three": {
                "name": "强制三连句",
                "severity": Severity.P2,
                "suggestion": "自然列出要点，不要总是凑成三",
                "check": self._check_compulsive_three,
            },
            "P2-03-uniform-paragraph": {
                "name": "段落长度统一",
                "severity": Severity.P2,
                "suggestion": "段落长度要有变化，不要每段都一样",
                "check": self._check_uniform_paragraph,
            },
            "P2-04-vertical-list": {
                "name": "垂直列表滥用",
                "severity": Severity.P2,
                "suggestion": "将 '1. 2. 3.' 列表改写为自然段落",
                "check": self._check_vertical_list,
            },
            "P2-05-em-dash-overuse": {
                "name": "Em Dash滥用",
                "severity": Severity.P2,
                "suggestion": "每500字最多1个em dash",
                "check": self._check_em_dash,
            },
            "P2-06-bolding-overuse": {
                "name": "Bold滥用",
                "severity": Severity.P2,
                "suggestion": "每section最多1处bold",
                "check": self._check_bold_overuse,
            },
            "P2-07-emoji-title": {
                "name": "标题Emoji",
                "severity": Severity.P2,
                "suggestion": "标题中删除emoji",
                "check": self._check_emoji_title,
            },
            "P2-08-curly-quote": {
                "name": "弯引号",
                "severity": Severity.P2,
                "suggestion": "将 “...” 替换为 \"...\"",
                "check": self._check_curly_quote,
            },
            "P2-09-transition-overuse": {
                "name": "过渡词滥用",
                "severity": Severity.P2,
                "suggestion": "删除Moreover/Furthermore，用And/Also代替",
                "check": self._check_transition_overuse,
            },
            "P2-10-fragmented-header": {
                "name": "标题后跟重复句",
                "severity": Severity.P2,
                "suggestion": "删除标题后面重复标题内容的句子",
                "check": self._check_fragmented_header,
            },
            "P2-11-persuasive-authority": {
                "name": "权威说服套路",
                "severity": Severity.P2,
                "suggestion": "删除 'At its core' 等空洞的权威表达",
                "check": self._check_persuasive_authority,
            },
        }

    # ── 检测函数 ────────────────────────────────────────────────

    def _check_cutoff(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P0-01: 知识截止免责声明"""
        matches = []
        patterns = [
            r"as of my last (update|knowledge|information)",
            r"my knowledge (?:is|was) current",
            r"i don't have (?:current|latest) information",
            r"(?:my|last) knowledge cutoff",
            r"up to (?:my|the) knowledge",
        ]
        for i, line in enumerate(lines, 1):
            for pat in patterns:
                if re.search(pat, line, re.IGNORECASE):
                    m = re.search(pat, line, re.IGNORECASE)
                    matches.append((m.group(), i))
        return matches

    def _check_chatbot(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P0-02: Chatbot响应痕迹"""
        matches = []
        patterns = [
            r"I hope this helps",
            r"Great question",
            r"Glad you asked",
            r"Certainly!",
            r"Here's how to",
            r"Let me help",
            r"I'd be happy to",
            r"Feel free to ask",
            r"You're welcome",
            r"Best regards",
            r"Hope this (?:works|helps|solves)",
        ]
        for i, line in enumerate(lines, 1):
            for pat in patterns:
                if re.search(pat, line, re.IGNORECASE):
                    m = re.search(pat, line, re.IGNORECASE)
                    matches.append((m.group(), i))
        return matches

    def _check_vague_attribution(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P0-03: 模糊归属"""
        matches = []
        patterns = [
            r"\bexperts? believe\b",
            r"\bstudies? show\b",
            r"\bresearch (?:suggests|indicates|shows)\b",
            r"\bit is (?:widely|generally|commonly) (?:known|believed|accepted)\b",
            r"\bmany (?:people|experts|researchers) (?:say|believe|think)\b",
            r"\baccording to (?:experts?|studies?|research)\b",
        ]
        for i, line in enumerate(lines, 1):
            for pat in patterns:
                if re.search(pat, line, re.IGNORECASE):
                    m = re.search(pat, line, re.IGNORECASE)
                    matches.append((m.group(), i))
        return matches

    def _check_significance_inflation(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P0-04: 重要性夸大"""
        matches = []
        patterns = [
            r"landmark",
            r"game-changing",
            r"revolutionary",
            r"groundbreaking",
            r"(?:truly|absolutely|completely) (?:remarkable|extraordinary)",
            r"(?:of (?:utmost|paramount) importance)",
            r"(?:a (?:major|pivotal) (?:milestone|breakthrough))",
            r"(?:without (?:any|any|reasonable) precedent)",
        ]
        for i, line in enumerate(lines, 1):
            for pat in patterns:
                if re.search(pat, line, re.IGNORECASE):
                    m = re.search(pat, line, re.IGNORECASE)
                    matches.append((m.group(), i))
        return matches

    def _word_pat(self, word: str) -> str:
        """
        将纯英文单词的正则转换为中英混合友好的形式。
        \b在Python3中对中文+英文失效（中文被当作文词字符），
        因此用前后瞻替代：(?<![a-zA-Z])word(?![a-zA-Z])
        """
        # 保持原始 \b 版本用于纯英文上下文，英文+中文混排时用替换版本
        return rf"(?<![a-zA-Z]){word}(?![a-zA-Z])"

    def _check_ai_highfreq(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P1-01: AI高频词"""
        matches = []
        # 使用中英混合友好的边界检测
        tier1 = [
            self._word_pat(r"delve[s]?"), self._word_pat(r"landscape"),
            self._word_pat(r"tapestry"), self._word_pat(r"pivotal"),
            self._word_pat(r"meticulous"), self._word_pat(r"intricate"),
            self._word_pat(r"vibrant"), self._word_pat(r"crucial"),
            self._word_pat(r"foster[s]?"), self._word_pat(r"garner[s]?"),
            self._word_pat(r"showcase[s]?"), self._word_pat(r"bolster[s]?"),
            self._word_pat(r"nuanced"), self._word_pat(r"multifaceted"),
            self._word_pat(r"comprehensive"), self._word_pat(r"robust"),
            self._word_pat(r"seamless"), self._word_pat(r"underscore[s]?"),
            self._word_pat(r"embark[s]?"), self._word_pat(r"leverage[s]?"),
            self._word_pat(r"facilitate[s]?"), self._word_pat(r"utilize[s]?"),
        ]
        for i, line in enumerate(lines, 1):
            for pat in tier1:
                if re.search(pat, line, re.IGNORECASE):
                    m = re.search(pat, line, re.IGNORECASE)
                    matches.append((m.group(), i))
        return matches

    def _check_template_phrases(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P1-02: 模板短语"""
        matches = []
        patterns = [
            r"In today's rapidly (?:evolving|changing)",
            r"the (?:ever-)?evolving (?:digital|technological|online)",
            r"(?:as|when) (?:it|we) (?:comes|grows) to",
            r"(?:it is|this is) worth (?:noting|mentioning|emphasizing)",
            r"(?:it should be|should be) noted (?:that|however)",
            r"(?:in this (?:article|post|piece|guide),? )?(?:we will|we shall|i will)",
            r"the following (?:article|post|piece|guide) (?:will|is to|aims to)",
        ]
        for i, line in enumerate(lines, 1):
            for pat in patterns:
                if re.search(pat, line, re.IGNORECASE):
                    m = re.search(pat, line, re.IGNORECASE)
                    matches.append((m.group(), i))
        return matches

    def _check_lets_transition(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P1-03: Let's过渡"""
        matches = []
        patterns = [
            r"\blet's (?:dive in|explore|take a look|examine|start|begin|delve)",
            r"\blet me (?:show|explain|walk you|tell you|share)",
            r"\bnow let(?:'s| us) (?:explore|dive|start|look|begin)",
        ]
        for i, line in enumerate(lines, 1):
            for pat in patterns:
                if re.search(pat, line, re.IGNORECASE):
                    m = re.search(pat, line, re.IGNORECASE)
                    matches.append((m.group(), i))
        return matches

    def _check_synonym_cycling(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P1-04: 同义词循环（同一段落中同一概念用多个同义词）"""
        matches = []
        # 检测同一段中重复用同义词描述同一概念
        # 如：solution → answer → resolution → remedy
        synonyms_groups = [
            ["solution", "answer", "resolution", "remedy", "fix"],
            ["challenge", "obstacle", "hurdle", "difficulty", "problem"],
            ["benefit", "advantage", "strength", "plus", "edge"],
            ["important", "crucial", "essential", "vital", "critical", "significant"],
        ]
        for i, line in enumerate(lines, 1):
            for group in synonyms_groups:
                found = [w for w in group if re.search(rf"\b{w}\b", line, re.IGNORECASE)]
                if len(found) >= 3:
                    matches.append((", ".join(found[:3]), i))
        return matches

    def _check_copula_avoidance(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P1-05: 连系动词规避"""
        matches = []
        patterns = [
            r"\bserves as\b",
            r"\bstands as\b",
            r"\bboasts\b",
            r"\bfeatures?\b(?!ing)",  # features (not featuring)
            r"\bplays a (?:pivotal|vital|crucial) role\b",
        ]
        for i, line in enumerate(lines, 1):
            for pat in patterns:
                if re.search(pat, line, re.IGNORECASE):
                    m = re.search(pat, line, re.IGNORECASE)
                    matches.append((m.group(), i))
        return matches

    def _check_negative_parallelism(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P1-06: 负面平行结构"""
        matches = []
        patterns = [
            r"not only (?:is|are|do|does|can|will)",
            r"(?:is|are|do|does|can|will) not only",
            r"but also\b",
            r"\bnot (?:just|mere) (?:a|an|about)",
        ]
        for i, line in enumerate(lines, 1):
            for pat in patterns:
                if re.search(pat, line, re.IGNORECASE):
                    m = re.search(pat, line, re.IGNORECASE)
                    matches.append((m.group(), i))
        return matches

    def _check_generic_conclusion(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P2-01: 通用结论"""
        matches = []
        patterns = [
            r"the future (?:looks|appears|seems) (?:bright|promising|rosy)",
            r"only time will tell",
            r"the (?:sky|world) is (?:the )?(?:limit|end)",
            r"(?:all|there is) (?:a|the) (?:good|great) (?:reason|side)",
            r"things (?:will|are going to) (?:only get|get) better",
        ]
        for i, line in enumerate(lines, 1):
            for pat in patterns:
                if re.search(pat, line, re.IGNORECASE):
                    m = re.search(pat, line, re.IGNORECASE)
                    matches.append((m.group(), i))
        return matches

    def _check_compulsive_three(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P2-02: 强制三连句"""
        matches = []
        # 检测 "第一、第二、第三" 且内容过于模板化
        for i, line in enumerate(lines, 1):
            if re.search(r"第一[、，]第二[、，]第三", line):
                matches.append(("第一、第二、第三（三连句）", i))
        return matches

    def _check_uniform_paragraph(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P2-03: 段落长度统一（启发式：连续5个段落长度相近）"""
        matches = []
        # 计算段落平均长度和方差
        paragraphs = re.split(r"\n\n+", text)
        if len(paragraphs) >= 5:
            lengths = [len(p) for p in paragraphs]
            avg = sum(lengths) / len(lengths)
            variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
            # 如果方差很小，说明段落长度太均匀
            if variance < 100 and avg > 50:
                matches.append((f"段落长度过于均匀（方差={variance:.0f}）", 0))
        return matches

    def _check_vertical_list(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P2-04: 垂直列表滥用（标题后紧跟大量列表项）"""
        matches = []
        # 计算全文中 "1. 2. 3." 格式的比例
        list_lines = sum(1 for l in lines if re.match(r"^\d+[.、]", l.strip()))
        total_lines = len(lines)
        if total_lines > 0 and list_lines / total_lines > 0.3:
            matches.append((f"列表占比过高：{list_lines}/{total_lines} 行", 0))
        return matches

    def _check_em_dash(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P2-05: Em Dash滥用"""
        matches = []
        dash_count = text.count("—") + text.count("--")
        word_count = len(text)
        if word_count > 0 and dash_count / (word_count / 500) > 1:
            matches.append((f"Em dash过多：{dash_count}个", 0))
        return matches

    def _check_bold_overuse(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P2-06: Bold滥用"""
        matches = []
        bold_count = len(re.findall(r"\*\*.+?\*\*", text))
        h2_count = len(re.findall(r"^## ", text, re.MULTILINE))
        if h2_count > 0 and bold_count > h2_count * 2:
            matches.append((f"Bold过多：{bold_count}处（建议≤{h2_count * 2}处）", 0))
        return matches

    def _check_emoji_title(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P2-07: 标题Emoji"""
        matches = []
        emoji = re.compile(r"[\U0001F300-\U0001F9FF\U0001F600-\U0001F64F]")
        for i, line in enumerate(lines, 1):
            if re.match(r"^#", line) and emoji.search(line):
                m = emoji.search(line)
                matches.append((m.group(), i))
        return matches

    def _check_curly_quote(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P2-08: 弯引号"""
        matches = []
        curly = ["\u201c", "\u201d", "\u2018", "\u2019"]  # " ' " '
        for i, line in enumerate(lines, 1):
            for q in curly:
                if q in line:
                    matches.append((f"弯引号: {q}", i))
                    break
        return matches

    def _check_transition_overuse(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P2-09: 过渡词滥用"""
        matches = []
        transitions = ["moreover", "furthermore", "additionally", "consequently", "therefore"]
        count = sum(len(re.findall(rf"\b{t}\b", text, re.IGNORECASE)) for t in transitions)
        if count > 3:
            matches.append((f"过渡词过多：{count}处", 0))
        return matches

    def _check_fragmented_header(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P2-10: 标题后跟重复句"""
        matches = []
        # 如果标题后面的第一句话重复了标题的关键词
        sections = re.split(r"^## ", text, flags=re.MULTILINE)[1:]
        for section in sections:
            section_lines = section.strip().split("\n")
            if not section_lines:
                continue
            first_body = section_lines[0].strip()
            header = section.split("\n")[0].strip()
            # 简单判断：标题在第一句中重复出现
            if len(header) > 5 and header[:6] in first_body[:20]:
                matches.append((f"重复: {header[:15]}...", 0))
        return matches

    def _check_persuasive_authority(self, text: str, lines: list[str]) -> list[tuple[str, int]]:
        """P2-11: 权威说服套路"""
        matches = []
        patterns = [
            r"\bat its core\b",
            r"\bat the end of the day\b",
            r"\bthe (?:very|absolute) bottom line\b",
            r"\b(?:it goes without saying|it goes without saying that)\b",
            r"\bmake no mistake\b",
            r"\b(?:it|this) (?:just|simply) goes to show(?: that)?\b",
            r"\b(?:the|the real) (?:question|issue|takeaway|take-away)",
        ]
        for i, line in enumerate(lines, 1):
            for pat in patterns:
                if re.search(pat, line, re.IGNORECASE):
                    m = re.search(pat, line, re.IGNORECASE)
                    matches.append((m.group(), i))
        return matches
