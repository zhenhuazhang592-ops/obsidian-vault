# agents/planner_agent.py - 主题策划Agent
# M2: 真实LLM调用 + 输入安全 + 模板模式标记

import json
import re
from typing import Any, Optional

from core.base_agent import BaseAgent, AgentResult
from core.message_hub import MessageHub, Message, MessageType
from core.llm_client import LLMClient, LLMCallError


def sanitize_topic(topic: str) -> str:
    """
    清理用户输入的 topic，防止注入。

    移除特殊字符，限制长度。
    """
    # 移除可能的 prompt 注入字符
    sanitized = re.sub(r'[^\w\s\u4e00-\u9fff\-、，。！？：；""''（）【】]', '', topic)
    # 限制长度为 100 字
    return sanitized[:100].strip()


PLANNER_PROMPT = """你是一个资深公众号运营专家，擅长主题策划。

给定一个主题方向，输出一个完整的策划方案。

```json
{
  "topic": "具体选题（精炼一句话）",
  "target_audience": {
    "persona": "读者画像，2-3句话",
    "pain_points": ["痛点1", "痛点2", "痛点3"],
    "reading_habit": "阅读习惯描述"
  },
  "unique_angle": "独特切入角度（为什么是现在写这个？）",
  "content_promise": "读者读完能获得什么",
  "tone": "内容调性（技术干货/情感共鸣/实战经验等）",
  "title_options": ["标题选项1", "标题选项2", "标题选项3"]
}
```

要求：
- 选题要有时间敏感性（为什么现在写）
- 痛点要具体，不要泛泛而谈
- 角度要有个人见解，不是网上随便能找到的
- 标题要符合公众号风格，有吸引力
"""


class PlannerAgent(BaseAgent):
    """主题策划Agent"""

    name = "Planner"
    description = "明确创作方向、受众画像、独特角度"

    def __init__(self, hub: MessageHub = None, llm_client: Optional[LLMClient] = None):
        super().__init__(hub)
        self.llm_client = llm_client

    def execute(self, input_data: Any) -> AgentResult:
        """
        执行主题策划

        输入: {
            "topic": str,  # 主题方向关键词
            "num_options": int,  # 输出多少个备选角度，默认3（目前只支持1）
        }

        输出: {
            "is_template": bool,  # True=模板模式，False=真实LLM生成
            "topic": str,
            "target_audience": dict,
            "unique_angle": str,
            "content_promise": str,
            "tone": str,
            "title_options": list[str],
            "llm_error": str,  # 如果是模板模式但有LLM错误
        }
        """
        if isinstance(input_data, str):
            topic = input_data
            num_options = 3
        else:
            topic = input_data.get("topic", "") if isinstance(input_data, dict) else ""
            num_options = input_data.get("num_options", 3) if isinstance(input_data, dict) else 3

        # 清理输入
        topic = sanitize_topic(topic or "")

        if not topic:
            return AgentResult(success=False, error="主题不能为空")

        # 发布开始状态
        self.hub.publish(Message(
            type=MessageType.STATUS,
            agent=self.name,
            content={"status": "running", "agent": self.name,
                     "progress": f"策划主题: {topic}"}
        ))

        # 有 LLM 客户端就调用，否则降级到模板
        if self.llm_client:
            return self._generate_with_llm(topic)
        else:
            return self._generate_template(topic)

    def _generate_template(self, topic: str) -> AgentResult:
        """生成策划模板（降级模式，无 LLM）"""
        output = {
            "is_template": True,
            "topic": topic,
            "target_audience": {
                "persona": "【请填写：目标读者画像，如：3-5年经验的中级开发者】",
                "pain_points": [
                    "【痛点1：如：多Agent协作混乱】",
                    "【痛点2：如：上下文丢失】",
                    "【痛点3：如：成本失控】"
                ],
                "reading_habit": "【阅读习惯：如：通勤/午休快速阅读，偏好实操性内容】"
            },
            "unique_angle": f"【从什么独特角度切入「{topic}」】",
            "content_promise": f"【读者读完能获得什么】",
            "tone": "技术干货，但有个人见解，不刻板",
            "title_options": [
                f"《{topic}：我从实战中总结的完整方案》",
                f"《{topic}？这一篇够了》",
                f"《关于{topic}，我有些不一样看法》"
            ],
            "llm_error": None
        }

        self.hub.publish(Message(
            type=MessageType.STATUS,
            agent=self.name,
            content={"status": "completed", "agent": self.name,
                     "progress": "模板模式（未配置LLM）"}
        ))

        return AgentResult(success=True, output=output)

    def _generate_with_llm(self, topic: str) -> AgentResult:
        """使用 LLM 生成策划"""
        try:
            schema = {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "target_audience": {
                        "type": "object",
                        "properties": {
                            "persona": {"type": "string"},
                            "pain_points": {"type": "array", "items": {"type": "string"}},
                            "reading_habit": {"type": "string"}
                        },
                        "required": ["persona", "pain_points", "reading_habit"]
                    },
                    "unique_angle": {"type": "string"},
                    "content_promise": {"type": "string"},
                    "tone": {"type": "string"},
                    "title_options": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["topic", "target_audience", "unique_angle",
                             "content_promise", "tone", "title_options"]
            }

            result = self.llm_client.chat_json(
                prompt=f"{PLANNER_PROMPT}\n\n主题：{topic}",
                schema=schema,
                temperature=0.7
            )

            # 确保必要字段存在
            result["is_template"] = False
            result["llm_error"] = None

            self.hub.publish(Message(
                type=MessageType.STATUS,
                agent=self.name,
                content={"status": "completed", "agent": self.name,
                         "progress": "LLM策划完成"}
            ))

            return AgentResult(success=True, output=result)

        except LLMCallError as e:
            # LLM 调用失败，降级到模板并注明原因
            result = self._generate_template(topic)
            result.output["llm_error"] = str(e)
            result.output["is_template"] = True
            return result

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"PlannerAgent异常: {str(e)}"
            )

    def _get_output_type(self) -> MessageType:
        return MessageType.PLAN
