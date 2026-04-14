# core/review_gate.py - 6维度质量评分门禁
# M3-3: LLM质量评分 + 软门禁（≥85通过，≤2次重试后交人类决策）

import json
from dataclasses import dataclass, field
from typing import Optional

from core.humanizer_engine import HumanizerEngine, HumanizerReport
from core.anti_slop_engine import AntiSlopEngine, AntiSlopReport
from core.llm_client import LLMClient, LLMCallError


# ────────────────────────────────────────────────────────────────
# 6维度评分 Report
# ────────────────────────────────────────────────────────────────

@dataclass
class DimensionScore:
    """单个维度评分"""
    name_zh: str      # 中文名
    name_en: str       # 英文名（用于雷达图）
    score: float       # 0-100
    reasoning: str     # 评分理由（1-2句）
    weight: float      # 权重


@dataclass
class QualityReport:
    """
    质量报告
    包含6维度评分 + 雷达图数据 + 门禁决策
    """
    # 6维度评分
    clarity: DimensionScore       # C-清晰度 20%
    organization: DimensionScore # O-组织 15%
    reference: DimensionScore     # R-可引用性 20%
    uniqueness: DimensionScore    # E-独特性 15%
    humanization: DimensionScore  # H-人性化 15%
    trust: DimensionScore         # T-信任度 15%

    # 综合
    weighted_score: float = 0.0   # 加权总分
    gate_passed: bool = False
    retry_count: int = 0
    needs_human_decision: bool = False

    # 引擎报告（快照）
    humanizer_report: dict = field(default_factory=dict)
    anti_slop_report: dict = field(default_factory=dict)

    # 详细意见
    opinions: list[str] = field(default_factory=list)

    # 雷达图数据
    radar_labels: list[str] = field(default_factory=lambda: [
        "C-清晰度", "O-组织", "R-可引用性", "E-独特性", "H-人性化", "T-信任度"
    ])
    radar_scores: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "weighted_score": round(self.weighted_score, 1),
            "gate_passed": self.gate_passed,
            "retry_count": self.retry_count,
            "needs_human_decision": self.needs_human_decision,
            "dimensions": {
                "clarity": {
                    "name_zh": self.clarity.name_zh,
                    "score": round(self.clarity.score, 1),
                    "reasoning": self.clarity.reasoning,
                    "weight": self.clarity.weight,
                },
                "organization": {
                    "name_zh": self.organization.name_zh,
                    "score": round(self.organization.score, 1),
                    "reasoning": self.organization.reasoning,
                    "weight": self.organization.weight,
                },
                "reference": {
                    "name_zh": self.reference.name_zh,
                    "score": round(self.reference.score, 1),
                    "reasoning": self.reference.reasoning,
                    "weight": self.reference.weight,
                },
                "uniqueness": {
                    "name_zh": self.uniqueness.name_zh,
                    "score": round(self.uniqueness.score, 1),
                    "reasoning": self.uniqueness.reasoning,
                    "weight": self.uniqueness.weight,
                },
                "humanization": {
                    "name_zh": self.humanization.name_zh,
                    "score": round(self.humanization.score, 1),
                    "reasoning": self.humanization.reasoning,
                    "weight": self.humanization.weight,
                },
                "trust": {
                    "name_zh": self.trust.name_zh,
                    "score": round(self.trust.score, 1),
                    "reasoning": self.trust.reasoning,
                    "weight": self.trust.weight,
                },
            },
            "radar_chart": {
                "labels": self.radar_labels,
                "scores": [round(s, 1) for s in self.radar_scores],
            },
            "humanizer_report_snapshot": self.humanizer_report,
            "anti_slop_report_snapshot": self.anti_slop_report,
            "opinions": self.opinions,
        }

    def format_summary(self) -> str:
        """人类可读的评分摘要"""
        lines = [
            "【6维度质量评分报告】",
            f"加权总分：{self.weighted_score:.1f} / 100",
            f"门禁状态：{'✅ 通过' if self.gate_passed else '❌ 未通过'}",
            "",
            "各维度评分：",
            f"  C-清晰度   (20%): {self.clarity.score:5.1f} — {self.clarity.reasoning}",
            f"  O-组织     (15%): {self.organization.score:5.1f} — {self.organization.reasoning}",
            f"  R-可引用性 (20%): {self.reference.score:5.1f} — {self.reference.reasoning}",
            f"  E-独特性   (15%): {self.uniqueness.score:5.1f} — {self.uniqueness.reasoning}",
            f"  H-人性化   (15%): {self.humanization.score:5.1f} — {self.humanization.reasoning}",
            f"  T-信任度   (15%): {self.trust.score:5.1f} — {self.trust.reasoning}",
        ]
        if self.opinions:
            lines.append("")
            lines.append("详细意见：")
            for op in self.opinions:
                lines.append(f"  • {op}")
        if self.needs_human_decision:
            lines.append("")
            lines.append("⚠️ 已达最大重试次数(2次)，请人工决策。")
        return "\n".join(lines)


# ────────────────────────────────────────────────────────────────
# ReviewGate 主类
# ────────────────────────────────────────────────────────────────

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "clarity_score": {
            "type": "number", "minimum": 0, "maximum": 100,
            "description": "C-清晰度：意图对齐、直接回答、受众匹配，0-100分"
        },
        "clarity_reasoning": {
            "type": "string",
            "description": "评分理由，1-2句话"
        },
        "organization_score": {
            "type": "number", "minimum": 0, "maximum": 100,
            "description": "O-组织：标题层级、段落chunking，0-100分"
        },
        "organization_reasoning": {
            "type": "string"
        },
        "reference_score": {
            "type": "number", "minimum": 0, "maximum": 100,
            "description": "R-可引用性：数据密度、引用质量，0-100分"
        },
        "reference_reasoning": {
            "type": "string"
        },
        "uniqueness_score": {
            "type": "number", "minimum": 0, "maximum": 100,
            "description": "E-独特性：独家数据、个人见解，0-100分"
        },
        "uniqueness_reasoning": {
            "type": "string"
        },
        "humanization_score": {
            "type": "number", "minimum": 0, "maximum": 100,
            "description": "H-人性化：去AI味评分、情感共鸣，0-100分"
        },
        "humanization_reasoning": {
            "type": "string"
        },
        "trust_score": {
            "type": "number", "minimum": 0, "maximum": 100,
            "description": "T-信任度：来源可信、信息准确，0-100分"
        },
        "trust_reasoning": {
            "type": "string"
        },
        "opinions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "详细改进意见列表（可空）"
        }
    },
    "required": [
        "clarity_score", "clarity_reasoning",
        "organization_score", "organization_reasoning",
        "reference_score", "reference_reasoning",
        "uniqueness_score", "uniqueness_reasoning",
        "humanization_score", "humanization_reasoning",
        "trust_score", "trust_reasoning",
    ]
}


REVIEW_PROMPT_TEMPLATE = """你是一个资深公众号内容质量评审专家。请对以下文章进行6维度质量评分。

## 评分维度（权重）

| 维度 | 说明 | 权重 |
|------|------|------|
| C-清晰度 | 意图对齐、直接回答、受众匹配 | 20% |
| O-组织 | 标题层级、段落chunking | 15% |
| R-可引用性 | 数据密度、引用质量 | 20% |
| E-独特性 | 独家数据、个人见解 | 15% |
| H-人性化 | 去AI味评分、情感共鸣 | 15% |
| T-信任度 | 来源可信、信息准确 | 15% |

## 文章内容

{article_content}

## 去AI味检测快照（参考）

Humanizer引擎检测结果：
- P0严重问题(P0必须修复): {p0_count}处
- P1明显AI腔: {p1_count}处
- P2可优化: {p2_count}处
- Humanizer评分: {humanizer_score}

AntiSlop引擎检测结果：
- Tier1禁用词: {tier1_count}处
- Tier2警告词: {tier2_count}处
- 结构问题: {structural_count}处
- AntiSlop评分: {anti_slop_score}

## 输出要求

请严格按照以下JSON格式输出评分结果，每个维度给出0-100的分数和1-2句评分理由：

{{
  "clarity_score": <0-100>,
  "clarity_reasoning": "<评分理由>",
  "organization_score": <0-100>,
  "organization_reasoning": "<评分理由>",
  "reference_score": <0-100>,
  "reference_reasoning": "<评分理由>",
  "uniqueness_score": <0-100>,
  "uniqueness_reasoning": "<评分理由>",
  "humanization_score": <0-100>,
  "humanization_reasoning": "<评分理由>",
  "trust_score": <0-100>,
  "trust_reasoning": "<评分理由>",
  "opinions": ["<改进建议1>", "<改进建议2>"]
}}

请直接输出JSON，不要有其他解释文字。"""


class ReviewGate:
    """
    质量门禁
    6维度LLM评分 + 软门禁（≥85通过，≤2次重试后交人类）
    """

    GATE_THRESHOLD = 85.0   # 通过分数线
    MAX_RETRIES = 2         # 最大润色重试次数

    # 权重
    WEIGHTS = {
        "clarity": 0.20,
        "organization": 0.15,
        "reference": 0.20,
        "uniqueness": 0.15,
        "humanization": 0.15,
        "trust": 0.15,
    }

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client
        self.humanizer = HumanizerEngine()
        self.anti_slop = AntiSlopEngine()

    def review(
        self,
        article_content: str,
        *,
        retry_count: int = 0,
        humanizer_report: Optional[HumanizerReport] = None,
        anti_slop_report: Optional[AntiSlopReport] = None,
    ) -> tuple[bool, QualityReport]:
        """
        评审一篇文章。

        Args:
            article_content: 文章正文（不含标题）
            retry_count: 当前重试次数（第几次润色后送审）
            humanizer_report: 可选，传入已有检测报告避免重复检测
            anti_slop_report: 可选，传入已有检测报告

        Returns:
            (gate_passed, quality_report)
        """
        # 1. 双引擎检测（如果没传入就现算）
        h_report = humanizer_report or self.humanizer.detect(article_content)
        a_report = anti_slop_report or self.anti_slop.check(article_content)

        # 2. LLM评分
        if self.llm_client:
            scores = self._llm_score(article_content, h_report, a_report)
        else:
            scores = self._rule_based_score(article_content, h_report, a_report)

        # 3. 构建 QualityReport
        dim_clarity = DimensionScore("C-清晰度", "Clarity",
                                      scores["clarity_score"], scores["clarity_reasoning"], 0.20)
        dim_org = DimensionScore("O-组织", "Organization",
                                  scores["organization_score"], scores["organization_reasoning"], 0.15)
        dim_ref = DimensionScore("R-可引用性", "Referenceability",
                                  scores["reference_score"], scores["reference_reasoning"], 0.20)
        dim_unique = DimensionScore("E-独特性", "Uniqueness",
                                     scores["uniqueness_score"], scores["uniqueness_reasoning"], 0.15)
        dim_human = DimensionScore("H-人性化", "Humanization",
                                    scores["humanization_score"], scores["humanization_reasoning"], 0.15)
        dim_trust = DimensionScore("T-信任度", "Trustworthiness",
                                    scores["trust_score"], scores["trust_reasoning"], 0.15)

        weighted = (
            dim_clarity.score * 0.20 +
            dim_org.score * 0.15 +
            dim_ref.score * 0.20 +
            dim_unique.score * 0.15 +
            dim_human.score * 0.15 +
            dim_trust.score * 0.15
        )

        # 门禁决策
        gate_passed = weighted >= self.GATE_THRESHOLD
        needs_human = (retry_count >= self.MAX_RETRIES) and not gate_passed

        report = QualityReport(
            clarity=dim_clarity,
            organization=dim_org,
            reference=dim_ref,
            uniqueness=dim_unique,
            humanization=dim_human,
            trust=dim_trust,
            weighted_score=weighted,
            gate_passed=gate_passed,
            retry_count=retry_count,
            needs_human_decision=needs_human,
            humanizer_report=h_report.to_dict(),
            anti_slop_report=a_report.to_dict(),
            opinions=scores.get("opinions", []),
            radar_scores=[
                dim_clarity.score,
                dim_org.score,
                dim_ref.score,
                dim_unique.score,
                dim_human.score,
                dim_trust.score,
            ],
        )

        return gate_passed, report

    def _llm_score(
        self,
        article_content: str,
        h_report: HumanizerReport,
        a_report: AntiSlopReport,
    ) -> dict:
        """通过LLM进行6维度评分"""
        prompt = REVIEW_PROMPT_TEMPLATE.format(
            article_content=article_content[:4000],  # 限制长度
            p0_count=h_report.p0_count,
            p1_count=h_report.p1_count,
            p2_count=h_report.p2_count,
            humanizer_score=h_report.humanizer_score,
            tier1_count=a_report.tier1_violations,
            tier2_count=a_report.tier2_violations,
            structural_count=a_report.structural_violations,
            anti_slop_score=a_report.anti_slop_score,
        )

        try:
            result = self.llm_client.chat_json(
                prompt=prompt,
                schema=REVIEW_SCHEMA,
                temperature=0.3,
            )
            return result
        except LLMCallError:
            # LLM失败时降级到规则评分
            return self._rule_based_score(article_content, h_report, a_report)

    def _rule_based_score(
        self,
        article_content: str,
        h_report: HumanizerReport,
        a_report: AntiSlopReport,
    ) -> dict:
        """
        规则降级评分（无LLM时使用）
        基于引擎报告的分数推算
        """
        import re

        # 基础分（从humanizer和anti_slop分数映射）
        humanizer_base = h_report.humanizer_score  # 已经是0-100
        anti_slop_base = a_report.anti_slop_score   # 已经是0-100

        # H-人性化 ≈ humanizer_score（占humanization维度的主要权重）
        humanization_score = humanizer_base

        # O-组织：段落结构、垂直列表等
        # 结构问题越多，组织分越低
        struct_issues = a_report.structural_violations
        org_score = max(40, 100 - struct_issues * 5)

        # E-独特性：只能从文本本身判断，这里用词汇丰富度代替
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', article_content)
        if chinese_chars:
            words = chinese_chars
            unique_ratio = len(set(words)) / max(len(words), 1)
            uniqueness_score = max(40, min(95, 60 + unique_ratio * 35))
        else:
            uniqueness_score = 60

        # R-可引用性：无法准确评估，给一个中等偏上的分
        reference_score = 70

        # T-信任度：无法准确评估，给一个中等分
        trust_score = 72

        # C-清晰度：用句子长度方差模拟（方差适中=清晰）
        sentences = re.split(r'[。！？；\n]', article_content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s) > 2]
        if len(sentences) >= 3:
            lengths = [len(s) for s in sentences]
            avg = sum(lengths) / len(lengths)
            variance = sum((l - avg) ** 2 for l in lengths) / max(len(lengths), 1)
            # 方差在100-400之间比较理想
            if 100 <= variance <= 400:
                clarity_score = 80
            elif variance < 100:
                clarity_score = 65  # 太平淡
            else:
                clarity_score = 75  # 变化太大
        else:
            clarity_score = 65

        # opinions
        opinions = []
        if h_report.p0_count > 0:
            opinions.append(f"Humanizer检测到{h_report.p0_count}处P0严重问题，需优先修复。")
        if a_report.tier1_violations > 0:
            opinions.append(f"发现{a_report.tier1_violations}处禁用词(Tier1)，必须替换。")
        if a_report.structural_violations > 2:
            opinions.append(f"存在{a_report.structural_violations}处结构问题，建议优化段落组织。")
        if humanization_score < 70:
            opinions.append("文章整体AI腔较重，建议增加口语化表达和个人经历。")

        return {
            "clarity_score": clarity_score,
            "clarity_reasoning": "基于句长方差评估，节奏适中。" if clarity_score >= 75 else "句子长度变化不足或过大，建议调整。",
            "organization_score": org_score,
            "organization_reasoning": f"结构问题{a_report.structural_violations}处，组织分偏低。" if org_score < 75 else "段落结构基本合理。",
            "reference_score": reference_score,
            "reference_reasoning": "缺乏引用数据支撑，建议增加具体案例和数据。",
            "uniqueness_score": uniqueness_score,
            "uniqueness_reasoning": "词汇丰富度一般，建议增加独家视角和个人见解。" if uniqueness_score < 75 else "有一定独特性表达。",
            "humanization_score": humanization_score,
            "humanization_reasoning": f"Humanizer评分{humanizer_base:.0f}，AI腔明显。" if humanization_score < 75 else f"Humanizer评分{humanizer_base:.0f}，较为自然。",
            "trust_score": trust_score,
            "trust_reasoning": "信息基本准确，但缺乏来源标注。",
            "opinions": opinions or ["无强烈改进建议。"],
        }


def review_article(
    article_content: str,
    llm_client: Optional[LLMClient] = None,
    retry_count: int = 0,
) -> tuple[bool, QualityReport]:
    """
    快捷函数：评审一篇文章。

    门禁规则：
    - 加权总分 ≥ 85 → 通过
    - 加权总分 < 85 → 返回Polisher重写（最多2次）
    - 2次重写后仍 < 85 → 标记 needs_human_decision = True

    Args:
        article_content: 文章正文
        llm_client: LLM客户端（可选，不提供时使用规则评分）
        retry_count: 当前重试次数

    Returns:
        (gate_passed, quality_report)
    """
    gate = ReviewGate(llm_client)
    return gate.review(article_content, retry_count=retry_count)
