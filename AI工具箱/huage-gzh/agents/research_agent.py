# ResearchAgent - 深度研究Agent
# 挖掘数据、案例、行业洞察，构建内容基础

import json
from typing import Any

from core.base_agent import BaseAgent, AgentResult
from core.message_hub import MessageHub, MessageType


class ResearchAgent(BaseAgent):
    """深度研究Agent"""

    name = "Research"
    description = "挖掘数据、案例、行业洞察，构建内容基础"

    DEFAULT_PROMPT = """你是一个专业的研究员，擅长深度内容和数据分析。

给定一个主题，你需要提供：

```json
{
  "key_statistics": [
    {"stat": "73%", "source": "来源", "claim": "数据说明"},
    {"stat": "5.2x", "source": "来源", "claim": "数据说明"}
  ],
  "case_studies": [
    {"company": "公司名", "case": "具体案例"},
    {"company": "公司名", "case": "具体案例"}
  ],
  "industry_insights": [
    "洞察1",
    "洞察2"
  ],
  "quotes_for_citation": [
    {"quote": "引言内容", "author": "作者", "source": "来源"}
  ]
}
```

请提供真实、有据可查的研究内容。"""

    def __init__(self, hub: MessageHub = None, api_client=None):
        super().__init__(hub)
        self.api_client = api_client

    def execute(self, input_data: Any) -> AgentResult:
        """
        执行深度研究

        输入: {
            "topic": str,  # 研究主题
            "outline": dict,  # 可选，大纲内容（参考重点）
            "api_client": object  # 可选，LLM API客户端
        }

        输出: {
            "key_statistics": list,
            "case_studies": list,
            "industry_insights": list,
            "quotes_for_citation": list
        }
        """
        if isinstance(input_data, str):
            topic = input_data
        else:
            topic = input_data.get("topic", "")

        if not topic:
            return AgentResult(success=False, error="研究主题不能为空")

        if self.api_client:
            return self._generate_with_llm(topic)

        return self._generate_template(topic)

    def _generate_template(self, topic: str) -> AgentResult:
        """生成研究模板"""
        output = {
            "key_statistics": [
                {
                    "stat": "【数据】",
                    "source": "【数据来源】",
                    "claim": f"【{topic}相关的核心数据】"
                }
            ],
            "case_studies": [
                {
                    "company": "【公司名】",
                    "case": f"【{topic}相关的具体案例】"
                }
            ],
            "industry_insights": [
                f"【关于{topic}的行业洞察1】",
                f"【关于{topic}的行业洞察2】"
            ],
            "quotes_for_citation": [
                {
                    "quote": "【有见地的引言】",
                    "author": "【作者】",
                    "source": "【来源】"
                }
            ]
        }

        return AgentResult(success=True, output=output)

    def _generate_with_llm(self, topic: str) -> AgentResult:
        """使用LLM生成研究内容"""
        prompt = self.DEFAULT_PROMPT + f"\n\n主题：{topic}"

        try:
            response = self.api_client.chat(prompt)
            output = json.loads(response)
            return AgentResult(success=True, output=output)
        except json.JSONDecodeError:
            return AgentResult(success=False, error="LLM输出格式错误")
        except Exception as e:
            return AgentResult(success=False, error=str(e))

    def _get_output_type(self) -> MessageType:
        return MessageType.RESEARCH
