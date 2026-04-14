# agents/image_agent.py - 配图封面Agent
# Phase 4: 封面色系 + 配图风格 + 尺寸规范

import json
import re
from typing import Any, Optional

from core.base_agent import BaseAgent, AgentResult
from core.message_hub import MessageHub, Message, MessageType
from core.llm_client import LLMClient, LLMCallError


# ────────────────────────────────────────────────────────────────
# 配色方案库
# ────────────────────────────────────────────────────────────────

COLOR_PALETTES = {
    "暖色调": ["#F5E6D3", "#E8D5C4", "#D4A574", "#8B4513", "#CD853F"],
    "冷色调": ["#E8F4F8", "#D1E8F0", "#87CEEB", "#4682B4", "#5F9EA0"],
    "绿植系": ["#F0F7F0", "#D4E6D1", "#8FBC8F", "#228B22", "#2E8B57"],
    "文艺黑": ["#1A1A1A", "#2D2D2D", "#4A4A4A", "#808080", "#B0B0B0"],
    "莫兰迪": ["#D4C4B0", "#C9B8A0", "#B5A090", "#9B8B7A", "#7A6B5A"],
    "INS风": ["#F8F4F0", "#E8E0D8", "#D4C4B8", "#C4B4A8", "#B4A498"],
    "商务蓝": ["#F0F4F8", "#D8E4F0", "#B8D4E8", "#4A90D9", "#2C5F8A"],
}


class ImageAgent(BaseAgent):
    """
    配图封面Agent

    Phase 4 职责：
    - 封面设计（色系、尺寸、标题字体建议）
    - 内文配图风格建议
    - 配图位置规划
    """

    name = "Image"
    description = "封面设计 + 配图风格 + 尺寸规范"

    def __init__(self, hub: MessageHub = None, llm_client: Optional[LLMClient] = None):
        super().__init__(hub)
        self.llm_client = llm_client

    def execute(self, input_data: Any) -> AgentResult:
        """
        执行配图方案设计

        输入: {
            "topic": str,          # 文章主题
            "title": str,           # 文章标题（用于封面文案）
            "tone": str,           # 内容调性（轻松/专业/深度/文艺）
            "keywords": list[str],  # SEO关键词（用于提炼配图方向）
            "word_count": int,      # 文章字数（估算配图数量）
        }

        输出: {
            "cover": {
                "color_palette": str,     # 配色方案名
                "colors": list[str],      # 实际色值
                "size": str,              # 封面尺寸
                "headline": str,          # 封面标题建议
                "font_suggestion": str,    # 字体建议
                "layout": str,            # 布局类型
            },
            "image_ideas": [
                {
                    "location": str,      # 位置描述（如"H2-1之后"）
                    "description": str,   # 图片描述
                    "style": str,         # 风格
                    "purpose": str,       # 用途（增加视觉层次/解释概念/情感共鸣）
                }
            ],
            "size_guide": dict,    # 尺寸规格
        }
        """
        if isinstance(input_data, str):
            topic = input_data
            title = ""
            tone = ""
            keywords = []
            word_count = 0
        else:
            topic = input_data.get("topic", "")
            title = input_data.get("title", "")
            tone = input_data.get("tone", "轻松")
            keywords = input_data.get("keywords", [])
            word_count = input_data.get("word_count", 0)

        self.hub.publish(Message(
            type=MessageType.STATUS,
            agent=self.name,
            content={"status": "running", "agent": self.name,
                     "progress": f"设计配图方案: {topic}"}
        ))

        if self.llm_client:
            result = self._generate_with_llm(topic, title, tone, keywords, word_count)
        else:
            result = self._generate_template(topic, title, tone, keywords, word_count)

        self.hub.publish(Message(
            type=MessageType.STATUS,
            agent=self.name,
            content={"status": "completed", "agent": self.name,
                     "progress": "配图方案设计完成"}
        ))

        return AgentResult(success=True, output=result)

    def _generate_with_llm(
        self,
        topic: str,
        title: str,
        tone: str,
        keywords: list,
        word_count: int,
    ) -> dict:
        """使用LLM生成配图方案"""
        prompt = f"""为公众号文章设计配图方案。

主题：{topic}
标题：{title}
调性：{tone}
关键词：{', '.join(keywords)}
字数：约{word_count}字

请输出JSON格式的配图方案：
{{
  "cover": {{
    "color_palette": "配色方案名（从暖色调/冷色调/绿植系/文艺黑/莫兰迪/INS风/商务蓝中选择）",
    "colors": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5"],
    "size": "900x383",
    "headline": "封面标题（10字内，吸引眼球）",
    "font_suggestion": "字体建议",
    "layout": "centered_title | split_image | text_only"
  }},
  "image_ideas": [
    {{
      "location": "位置（如：开头场景描述处、H2-1之后）",
      "description": "图片内容描述",
      "style": "摄影风格/插画风格/信息图",
      "purpose": "增加视觉层次 | 解释概念 | 情感共鸣"
    }}
  ],
  "size_guide": {{
    "cover": "900x383",
    "inline": "800x450",
    "full_width": "900x500"
  }}
}}

配色方案库：暖色调适合生活/情感类；冷色调适合科技/商业类；绿植系适合自然/健康类；文艺黑适合深度思考类；莫兰迪适合生活方式类；INS风适合年轻化内容；商务蓝适合职场/商业类。"""

        try:
            result = self.llm_client.chat_json(
                prompt=prompt,
                schema={
                    "type": "object",
                    "properties": {
                        "cover": {
                            "type": "object",
                            "properties": {
                                "color_palette": {"type": "string"},
                                "colors": {"type": "array", "items": {"type": "string"}},
                                "size": {"type": "string"},
                                "headline": {"type": "string"},
                                "font_suggestion": {"type": "string"},
                                "layout": {"type": "string"},
                            }
                        },
                        "image_ideas": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "location": {"type": "string"},
                                    "description": {"type": "string"},
                                    "style": {"type": "string"},
                                    "purpose": {"type": "string"},
                                }
                            }
                        },
                        "size_guide": {"type": "object"},
                    }
                },
                temperature=0.7,
            )
            return result
        except LLMCallError:
            return self._generate_template(topic, title, tone, keywords, word_count)

    def _generate_template(
        self,
        topic: str,
        title: str,
        tone: str,
        keywords: list,
        word_count: int,
    ) -> dict:
        """模板降级生成配图方案"""
        # 根据关键词推断配色
        tone_keywords = " ".join(keywords).lower()
        if any(w in tone_keywords for w in ["职场", "商业", "科技", "金融"]):
            palette_name = "商务蓝"
        elif any(w in tone_keywords for w in ["情感", "生活", "心情", "日常"]):
            palette_name = "暖色调"
        elif any(w in tone_keywords for w in ["自然", "植物", "健康", "户外"]):
            palette_name = "绿植系"
        elif tone in ["深度", "思考", "哲学"]:
            palette_name = "文艺黑"
        elif tone in ["轻松", "年轻", "潮流"]:
            palette_name = "INS风"
        else:
            palette_name = "莫兰迪"

        colors = COLOR_PALETTES.get(palette_name, COLOR_PALETTES["莫兰迪"])

        # 估算配图数量：每300字一张
        num_images = max(1, min(5, word_count // 300))

        # 封面标题
        cover_headline = title[:10] if len(title) > 10 else title
        if not cover_headline and topic:
            cover_headline = topic[:10]

        image_ideas = []
        purposes = ["增加视觉层次", "解释概念", "情感共鸣"]
        styles = ["摄影风格", "插画风格", "信息图"]
        for i in range(num_images):
            image_ideas.append({
                "location": f"文章第{int((i + 1) * word_count / (num_images + 1))}字附近",
                "description": f"与「{topic}」相关的{styles[i % len(styles)]}配图",
                "style": styles[i % len(styles)],
                "purpose": purposes[i % len(purposes)],
            })

        return {
            "cover": {
                "color_palette": palette_name,
                "colors": colors,
                "size": "900x383",
                "headline": cover_headline,
                "font_suggestion": "思源黑体 / 苹方体",
                "layout": "centered_title",
            },
            "image_ideas": image_ideas,
            "size_guide": {
                "cover": "900x383",
                "inline": "800x450",
                "full_width": "900x500",
            },
        }

    def _get_output_type(self) -> MessageType:
        return MessageType.IMAGE
