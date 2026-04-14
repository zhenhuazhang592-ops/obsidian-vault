# agents/writer_agent.py - 内容写作Agent
# M2: 真实LLM调用 + 风格指纹注入

import json
import re
from typing import Any, Optional

from core.base_agent import BaseAgent, AgentResult
from core.message_hub import MessageHub, Message, MessageType
from core.llm_client import LLMClient, LLMCallError


WRITER_PROMPT = """你是一个资深公众号作者，擅长写技术干货文章。

给定一个大纲，写出一篇完整的公众号文章正文。

## 风格要求（必须严格遵守）

1. **长短句交替**：20%短句（5字内）+ 70%中等句 + 10%长句。不要全是同长度的句子。
2. **打破三连句**：不要总是"第一、第二、第三"。自然列出要点。
3. **口语化**：使用"其实"、"坦白说"、"说实话"、"搞定"、"捋一捋"等口语词。不要刻板。
4. **禁用词**：绝对不要用以下词：
   - delve, landscape, tapestry, crucial, pivotal, robust, seamless, comprehensive
   - "非常关键"、"具有重大意义"、"让我们一起"、"综上所述"、"总而言之"
5. **第一人称**：适当使用"我"、"我们"，不要全是客观叙述。
6. **不规则段落**：段落长度要有变化，不要每段都一样长。

## 文章格式

- 开头：直接戳痛点或制造悬念（1-2段）
- H2：每个H2一段引入，然后展开关键要点
- 结尾：总结 + 开放问题，不写"希望对你有帮助"之类的客套话

## 大纲

```json
{outline_json}
```

## 风格写作指令（参考）

{style_instructions}

请根据以上要求，写出完整文章正文。
直接输出Markdown，不需要任何解释。
"""


class WriterAgent(BaseAgent):
    """内容写作Agent"""

    name = "Writer"
    description = "根据大纲写完整正文"

    def __init__(self, hub: MessageHub = None, llm_client: Optional[LLMClient] = None):
        super().__init__(hub)
        self.llm_client = llm_client

    def execute(self, input_data: Any) -> AgentResult:
        """
        执行内容写作

        输入: {
            "outline": dict,  # 大纲
            "research": dict,  # 研究内容
            "style_instructions": str,  # 风格写作指令
            "style_fingerprint": dict,  # 风格指纹
            "target_audience": dict,  # 受众画像
        }

        输出: {
            "is_template": bool,
            "title": str,
            "content": str,
            "word_count": int,
            "h2_count": int
        }
        """
        if not isinstance(input_data, dict):
            return AgentResult(success=False, error="输入必须是字典")

        outline = input_data.get("outline", {})
        style_instructions = input_data.get("style_instructions", "")
        style_fingerprint = input_data.get("style_fingerprint", {})
        target_audience = input_data.get("target_audience", {})

        if not outline:
            return AgentResult(success=False, error="大纲不能为空")

        # 发布状态
        self.hub.publish(Message(
            type=MessageType.STATUS,
            agent=self.name,
            content={"status": "running", "agent": self.name,
                     "progress": "开始写作正文"}
        ))

        if self.llm_client:
            return self._write_with_llm(outline, style_instructions, style_fingerprint, target_audience)
        else:
            return self._write_template(outline, style_instructions)

    def _write_template(self, outline: dict, style_instructions: str = "") -> AgentResult:
        """生成正文模板（降级模式）"""
        title = outline.get("title", "无标题")
        outline_items = outline.get("outline", [])
        opening_hook = outline.get("opening_hook", "")

        lines = [f"# {title}\n"]

        if opening_hook:
            lines.append(f"{opening_hook}\n")

        # 生成每个H2的骨架
        for i, item in enumerate(outline_items):
            h2 = item.get("h2", "")
            key_points = item.get("key_points", [])
            word_target = item.get("word_target", 300)

            lines.append(f"\n## {h2}\n")

            # 生成关键要点（只列出来，没有展开）
            for point in key_points:
                lines.append(f"- {point}。\n")

            # 填充字数提醒（模板模式）
            lines.append(f"\n<!-- 目标字数：{word_target}字 -->\n")

        # 结尾
        lines.append("\n---\n")
        lines.append("\n看完你有什么想法？欢迎评论区聊聊。\n")

        content = "".join(lines)
        h2_count = len(outline_items)
        word_count = len(content.replace("#", "").replace("\n", "").replace(" ", "").replace("-", ""))

        self.hub.publish(Message(
            type=MessageType.STATUS,
            agent=self.name,
            content={"status": "completed", "agent": self.name,
                     "progress": "模板模式（未配置LLM）"}
        ))

        return AgentResult(success=True, output={
            "is_template": True,
            "title": title,
            "content": content,
            "word_count": word_count,
            "h2_count": h2_count
        })

    def _write_with_llm(
        self,
        outline: dict,
        style_instructions: str,
        style_fingerprint: dict,
        target_audience: dict
    ) -> AgentResult:
        """使用 LLM 生成正文"""
        try:
            outline_json = json.dumps(outline, ensure_ascii=False, indent=2)

            # 如果有风格指纹，提取口语化词注入 prompt
            colloquial = ""
            if style_fingerprint:
                markers = style_fingerprint.get("tone", {}).get("colloquial_markers", [])
                if markers:
                    colloquial = f"\n本文已有口语化倾向词：{', '.join(markers[:5])}。在写作时适当使用。"

            # 如果有受众画像，注入 pain_points
            pain_context = ""
            if target_audience:
                persona = target_audience.get("persona", "")
                pain_points = target_audience.get("pain_points", [])
                if pain_points:
                    pain_context = f"\n读者画像：{persona}\n读者痛点：{', '.join(pain_points)}"

            prompt = WRITER_PROMPT.format(
                outline_json=outline_json,
                style_instructions=style_instructions + colloquial + pain_context
            )

            # 发布正在写作的状态
            self.hub.publish(Message(
                type=MessageType.STATUS,
                agent=self.name,
                content={"status": "running", "agent": self.name,
                         "progress": "LLM写作中（可能需要10-30秒）..."}
            ))

            content = self.llm_client.chat(
                prompt=prompt,
                temperature=0.75
            )

            # 清理 LLM 输出（去除可能的 ```markdown 包裹）
            content = re.sub(r"^```markdown\s*", "", content.strip())
            content = re.sub(r"```\s*$", "", content)

            # 提取标题（如果 LLM 没有按要求输出）
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            title = title_match.group(1) if title_match else outline.get("title", "无标题")

            h2_count = len(re.findall(r"^##\s+", content, re.MULTILINE))
            word_count = len(content.replace("#", "").replace("\n", "").replace(" ", "").replace("-", "").replace(">", ""))

            self.hub.publish(Message(
                type=MessageType.STATUS,
                agent=self.name,
                content={"status": "completed", "agent": self.name,
                         "progress": f"写作完成：{word_count}字，{h2_count}个H2"}
            ))

            return AgentResult(success=True, output={
                "is_template": False,
                "title": title,
                "content": content,
                "word_count": word_count,
                "h2_count": h2_count
            })

        except LLMCallError as e:
            result = self._write_template(outline, style_instructions)
            result.output["is_template"] = True
            return result

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"WriterAgent异常: {str(e)}"
            )

    def _get_output_type(self) -> MessageType:
        return MessageType.DRAFT
