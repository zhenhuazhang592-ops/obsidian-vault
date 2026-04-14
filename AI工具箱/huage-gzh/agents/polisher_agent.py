# agents/polisher_agent.py - 润色优化Agent
# M3-4: 去AI味双引擎整合 + GEO优化 + SEO关键词强化

import re
from typing import Any, Optional

from core.base_agent import BaseAgent, AgentResult
from core.message_hub import MessageHub, Message, MessageType
from core.llm_client import LLMClient, LLMCallError
from core.humanizer_engine import HumanizerEngine, HumanizerReport
from core.anti_slop_engine import AntiSlopEngine, AntiSlopReport, generate_polish_suggestions


POLISH_PROMPT_TEMPLATE = """你是一个资深公众号文字润色编辑，擅长去除AI写作腔调、增强文章可读性。

## 原文

{original_content}

## 润色要求

请根据以下检测报告，对原文进行深度润色：

### 一、去AI味优先级修复

{major_issues}

### 二、SEO关键词强化

{seo_instructions}

### 三、GEO权威信号增强

请在润色时加入以下GEO（Generative Engine Optimization）信号：
- **具体数据**：把模糊描述改为具体数字（"很多人"→"超过500万用户"）
- **时间锚点**：标注事件发生的时间（"最近"→"2025年3月"）
- **来源标注**：用"据XXX报道"、"来自XXX的数据显示"等引出数据
- **专家引用**：适当位置加入"正如XX领域的专家XX所说"类似表达
- **术语精确**：使用行业标准术语替代口语化泛称

### 四、风格要求

1. **长短句交替**：保持20%短句（5字内）+ 70%中等句 + 10%长句
2. **口语化表达**：适当使用"其实"、"坦白说"、"说实话"、"搞定"等
3. **禁用词禁止出现**：
   - delve, landscape, tapestry, crucial, pivotal, robust, seamless, comprehensive
   - "非常关键"、"具有重大意义"、"让我们一起"、"综上所述"、"总而言之"
4. **个人化视角**：适当加入第一人称叙述和个人经历
5. **段落长度变化**：段落长度要有明显差异，避免整齐划一

## 输出

请直接输出润色后的完整文章正文（Markdown格式），不要有任何解释或说明。
直接输出，不要包裹```markdown标记。
"""


SEO_KEYWORD_PROMPT_TEMPLATE = """根据以下SEO关键词，对文章进行关键词强化润色：

核心关键词：{primary_keyword}
次要关键词：{secondary_keywords}
长尾关键词：{long_tail_keywords}

要求：
1. 在文章前100字内包含核心关键词
2. 在H2标题中自然融入次要关键词
3. 在正文中3-5次自然提及核心关键词（不要堆砌）
4. 至少在一个段落加入长尾关键词变体

请直接输出润色后的文章，不要有解释。
"""


class PolisherAgent(BaseAgent):
    """润色优化Agent"""

    name = "Polisher"
    description = "去AI味双引擎整合 + GEO优化 + SEO关键词强化"

    def __init__(self, hub: MessageHub = None, llm_client: Optional[LLMClient] = None):
        super().__init__(hub)
        self.llm_client = llm_client
        self.humanizer = HumanizerEngine()
        self.anti_slop = AntiSlopEngine()

    def execute(self, input_data: Any) -> AgentResult:
        """
        执行润色优化

        输入: {
            "article": str,  # 文章正文
            "seo_keywords": dict,  # SEO关键词 {primary, secondary[], long_tail[]}
            "retry_count": int,  # 重试次数
        }

        输出: {
            "polished_article": str,
            "humanizer_report": dict,
            "anti_slop_report": dict,
            "polish_suggestions": str,
            "word_count": int,
            "is_template": bool,
        }
        """
        if not isinstance(input_data, dict):
            return AgentResult(success=False, error="输入必须是字典")

        article = input_data.get("article", "")
        seo_keywords = input_data.get("seo_keywords", {})
        retry_count = input_data.get("retry_count", 0)

        if not article:
            return AgentResult(success=False, error="文章内容不能为空")

        self.hub.publish(Message(
            type=MessageType.STATUS,
            agent=self.name,
            content={"status": "running", "agent": self.name,
                     "progress": f"润色第{retry_count + 1}次：运行双引擎检测"}
        ))

        # 1. 双引擎检测
        h_report = self.humanizer.detect(article)
        a_report = self.anti_slop.check(article)

        # 2. 生成润色建议
        suggestions_text = generate_polish_suggestions(a_report, h_report)

        # 3. 生成SEO关键词指令
        seo_instructions = self._build_seo_instructions(seo_keywords)

        # 4. LLM润色
        self.hub.publish(Message(
            type=MessageType.STATUS,
            agent=self.name,
            content={"status": "running", "agent": self.name,
                     "progress": "LLM润色中（可能需要10-20秒）..."}
        ))

        if self.llm_client:
            polished = self._polish_with_llm(
                article, suggestions_text, seo_instructions, seo_keywords
            )
            is_template = False
        else:
            polished = self._polish_template(article, suggestions_text)
            is_template = True

        # 5. 清理输出（去除可能的markdown包裹）
        polished = re.sub(r"^```markdown\s*", "", polished.strip())
        polished = re.sub(r"```\s*$", "", polished)

        word_count = len(polished.replace("#", "").replace("\n", "").replace(" ", "").replace("-", "").replace(">", ""))

        self.hub.publish(Message(
            type=MessageType.STATUS,
            agent=self.name,
            content={"status": "completed", "agent": self.name,
                     "progress": f"润色完成：{word_count}字"}
        ))

        return AgentResult(success=True, output={
            "polished_article": polished,
            "humanizer_report": h_report.to_dict(),
            "anti_slop_report": a_report.to_dict(),
            "polish_suggestions": suggestions_text,
            "word_count": word_count,
            "is_template": is_template,
        })

    def _build_seo_instructions(self, seo_keywords: dict) -> str:
        """构建SEO关键词强化指令"""
        if not seo_keywords:
            return "无特定SEO关键词要求，保持自然表达即可。"

        primary = seo_keywords.get("primary", "")
        secondary = seo_keywords.get("secondary", [])
        long_tail = seo_keywords.get("long_tail", [])

        lines = [f"核心关键词（必须自然出现）：{primary}"]
        if secondary:
            lines.append(f"次要关键词（融入H2标题）：{', '.join(secondary[:3])}")
        if long_tail:
            lines.append(f"长尾关键词变体：{', '.join(long_tail[:2])}")
        return "\n".join(lines)

    def _polish_with_llm(
        self,
        article: str,
        suggestions: str,
        seo_instructions: str,
        seo_keywords: dict,
    ) -> str:
        """使用LLM进行润色"""
        # 如果有SEO关键词，分两阶段：先SEO强化，再去AI味
        if seo_keywords.get("primary"):
            # 第一阶段：SEO关键词强化
            seo_prompt = SEO_KEYWORD_PROMPT_TEMPLATE.format(
                primary_keyword=seo_keywords.get("primary", ""),
                secondary_keywords=", ".join(seo_keywords.get("secondary", [])),
                long_tail_keywords=", ".join(seo_keywords.get("long_tail", [])),
            )
            article = self.llm_client.chat(
                prompt=f"{seo_prompt}\n\n## 原文\n\n{article}",
                temperature=0.4,
            )
            article = re.sub(r"^```markdown\s*", "", article.strip())
            article = re.sub(r"```\s*$", "", article)

        # 第二阶段：去AI味润色
        major_issues = suggestions
        prompt = POLISH_PROMPT_TEMPLATE.format(
            original_content=article[:5000],
            major_issues=major_issues,
            seo_instructions=seo_instructions,
        )

        return self.llm_client.chat(prompt=prompt, temperature=0.5)

    def _polish_template(self, article: str, suggestions: str) -> str:
        """
        模板降级润色（无LLM时使用）
        纯规则替换，效果有限但不会破坏文章
        """
        # 简单规则替换
        polished = article

        # Tier1禁用词替换
        tier1_replacements = {
            "pivotal": "关键",
            "crucial": "重要",
            "vital": "重要",
            "significant": "重要",
            "essential": "必要",
            "groundbreaking": "突破性",
            "delve": "深入",
            "landscape": "领域",
            "tapestry": "图景",
            "robust": "强健",
            "seamless": "顺畅",
            "comprehensive": "全面",
            "harness": "利用",
            "navigate": "应对",
            "foster": "培养",
            "underscore": "强调",
            "showcase": "展示",
            "garner": "获得",
        }
        for eng_word, cn_word in tier1_replacements.items():
            # 中英混合友好的边界检测
            pat = rf"(?<![a-zA-Z]){re.escape(eng_word)}(?![a-zA-Z])"
            pattern = re.compile(pat, re.IGNORECASE)
            polished = pattern.sub(cn_word, polished)

        # 中文禁用词替换
        cn_replacements = {
            "非常重要的": "重要",
            "具有重大意义的": "有意义",
            "让我们一起": "一起",
            "综上所述": "",
            "总而言之": "",
        }
        for cn_word, replacement in cn_replacements.items():
            polished = polished.replace(cn_word, replacement)

        # 添加润色说明
        if suggestions:
            polished += f"\n\n<!-- 润色建议：\n{suggestions[:500]} -->\n"

        return polished

    def _get_output_type(self) -> MessageType:
        return MessageType.POLISHED
