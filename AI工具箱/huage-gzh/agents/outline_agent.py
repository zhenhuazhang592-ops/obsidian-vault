# agents/outline_agent.py - 大纲规划Agent
# M2: 真实LLM调用 + SEO关键词布局

import json
import re
from typing import Any, Optional

from core.base_agent import BaseAgent, AgentResult
from core.message_hub import MessageHub, Message, MessageType
from core.llm_client import LLMClient, LLMCallError


def sanitize_topic(topic: str) -> str:
    sanitized = re.sub(r'[^\w\s\u4e00-\u9fff\-、，。！？]', '', topic)
    return sanitized[:100].strip()


OUTLINE_PROMPT = """你是一个资深公众号内容策划，擅长结构设计和SEO优化。

给定一个主题策划案，设计一套完整的大纲。

```json
{
  "title": "最终标题（吸引点击）",
  "seo_keywords": {
    "primary": "核心关键词（1个）",
    "secondary": ["次要关键词1", "次要关键词2", "次要关键词3"],
    "long_tail": ["长尾关键词1", "长尾关键词2", "长尾关键词3"]
  },
  "outline": [
    {
      "h2": "H2标题",
      "key_points": ["要点1", "要点2", "要点3"],
      "word_target": 400
    }
  ],
  "estimated_word_count": int,
  "opening_hook": "开头钩子（一句话抓住读者）"
}
```

要求：
- 大纲要有起承转合（开头痛点 → 核心内容 → 实战案例 → 总结行动）
- 每个H2要有具体的关键要点，不要泛泛而谈
- SEO关键词要自然融入标题和H2中，不要堆砌
- estimated_word_count 是全文总字数估算（一般1500-3000字）
- opening_hook 开头钩子要直接戳痛点或制造悬念
"""


class OutlineAgent(BaseAgent):
    """大纲规划Agent"""

    name = "Outline"
    description = "结构设计 + SEO关键词布局"

    def __init__(self, hub: MessageHub = None, llm_client: Optional[LLMClient] = None):
        super().__init__(hub)
        self.llm_client = llm_client

    def execute(self, input_data: Any) -> AgentResult:
        """
        执行大纲规划

        输入: {
            "topic": str,
            "target_audience": dict,
            "style_instructions": str,    # 风格写作指令
            "num_h2": int,                 # H2数量，默认7
            "research": dict,              # 研究报告（Phase 2 新增）
        }

        输出: {
            "is_template": bool,
            "title": str,
            "seo_keywords": dict,
            "outline": list[dict],
            "estimated_word_count": int,
            "opening_hook": str,
        }
        """
        if not isinstance(input_data, dict):
            topic = str(input_data) if input_data else ""
            return AgentResult(success=False, error="大纲规划需要 dict 输入")

        topic = sanitize_topic(input_data.get("topic", ""))
        target_audience = input_data.get("target_audience", {})
        style_instructions = input_data.get("style_instructions", "")
        num_h2 = input_data.get("num_h2", 7)
        research = input_data.get("research", {})

        if not topic:
            return AgentResult(success=False, error="主题不能为空")

        # 发布状态
        self.hub.publish(Message(
            type=MessageType.STATUS,
            agent=self.name,
            content={"status": "running", "agent": self.name,
                     "progress": f"设计大纲: {topic}"}
        ))

        if self.llm_client:
            return self._generate_with_llm(topic, target_audience, style_instructions, num_h2, research)
        else:
            return self._generate_template(topic, num_h2, research)

    def _generate_template(self, topic: str, num_h2: int, research: dict = None) -> AgentResult:
        """生成大纲模板（降级模式）"""
        primary_kw = topic

        h2_templates = [
            {"h2": f"一、为什么{topic}值得关注？", "key_points": ["背景", "现状", "核心价值"], "word_target": 350},
            {"h2": f"二、{topic}的第一核心要点", "key_points": ["要点1", "要点2", "案例"], "word_target": 400},
            {"h2": f"三、{topic}的第二核心要点", "key_points": ["要点1", "要点2", "案例"], "word_target": 400},
            {"h2": f"四、{topic}的第三核心要点", "key_points": ["要点1", "要点2", "案例"], "word_target": 400},
            {"h2": "五、常见错误与避坑指南", "key_points": ["错误1", "错误2", "正确做法"], "word_target": 300},
            {"h2": f"六、如何开始{topic}？", "key_points": ["步骤1", "步骤2", "步骤3"], "word_target": 250},
            {"h2": "七、总结与行动建议", "key_points": ["核心回顾", "行动建议", "延伸阅读"], "word_target": 200},
        ]

        output = {
            "is_template": True,
            "title": f"《{topic}：实战完整指南》",
            "seo_keywords": self._merge_seo_keywords(primary_kw, research),
            "outline": h2_templates[:num_h2],
            "estimated_word_count": num_h2 * 300 + 500,
            "opening_hook": f"你知道吗，{topic}其实没有想象中那么难。"
        }

        if research:
            findings = research.get("findings", [])
            if findings:
                output["seo_keywords"] = self._merge_seo_keywords(topic, research)

        self.hub.publish(Message(
            type=MessageType.STATUS,
            agent=self.name,
            content={"status": "completed", "agent": self.name,
                     "progress": "模板模式（未配置LLM）"}
        ))

        return AgentResult(success=True, output=output)

    def _generate_with_llm(
        self,
        topic: str,
        target_audience: dict,
        style_instructions: str,
        num_h2: int,
        research: dict = None,
    ) -> AgentResult:
        """使用 LLM 生成大纲"""
        try:
            schema = {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "seo_keywords": {
                        "type": "object",
                        "properties": {
                            "primary": {"type": "string"},
                            "secondary": {"type": "array", "items": {"type": "string"}},
                            "long_tail": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["primary", "secondary", "long_tail"]
                    },
                    "outline": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "h2": {"type": "string"},
                                "key_points": {"type": "array", "items": {"type": "string"}},
                                "word_target": {"type": "number"}
                            },
                            "required": ["h2", "key_points", "word_target"]
                        }
                    },
                    "estimated_word_count": {"type": "number"},
                    "opening_hook": {"type": "string"}
                },
                "required": ["title", "seo_keywords", "outline", "estimated_word_count", "opening_hook"]
            }

            # 构造 prompt，注入受众、风格和研究信息
            persona = target_audience.get("persona", "一般读者")
            pain_points = ", ".join(target_audience.get("pain_points", []))
            tone = target_audience.get("tone", "技术干货")

            # 研究上下文
            research_context = ""
            if research:
                findings = research.get("findings", [])
                if findings:
                    research_context = f"\n## 研究发现（来自 Tavily + Obsidian）：\n" + "\n".join(f"- {f}" for f in findings[:5])
                seo_kw = research.get("seo_keywords", {})
                if seo_kw:
                    research_context += f"\nSEO关键词：primary={seo_kw.get('primary', topic)}, secondary={seo_kw.get('secondary', [])}"

            prompt = f"""{OUTLINE_PROMPT}

背景信息：
- 主题：{topic}
- 目标读者：{persona}
- 读者痛点：{pain_points}
- 内容调性：{tone}

{research_context}

{f"风格写作指令：\n{style_instructions}" if style_instructions else ""}

请生成 {num_h2} 个H2的大纲。"""

            result = self.llm_client.chat_json(
                prompt=prompt,
                schema=schema,
                temperature=0.7
            )

            result["is_template"] = False

            self.hub.publish(Message(
                type=MessageType.STATUS,
                agent=self.name,
                content={"status": "completed", "agent": self.name,
                         "progress": "LLM大纲生成完成"}
            ))

            return AgentResult(success=True, output=result)

        except LLMCallError as e:
            result = self._generate_template(topic, num_h2, research)
            result.output["is_template"] = True
            return result

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"OutlineAgent异常: {str(e)}"
            )

    def _merge_seo_keywords(self, primary: str, research: dict = None) -> dict:
        """融合研究报告中的 SEO keywords"""
        default = {
            "primary": primary,
            "secondary": [f"{primary}技巧", f"{primary}方法"],
            "long_tail": [f"如何{primary}", f"{primary}入门"],
        }
        if not research:
            return default

        seo = research.get("seo_keywords", {})
        if not seo:
            return default

        return {
            "primary": seo.get("primary", primary),
            "secondary": seo.get("secondary", default["secondary"]),
            "long_tail": seo.get("long_tail", default["long_tail"]),
        }

    def _get_output_type(self) -> MessageType:
        return MessageType.OUTLINE
