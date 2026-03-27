"""Claude API 客户端 — 用于生成分镜 Prompt"""

import os
from anthropic import Anthropic


class ClaudeClient:
    """Claude API 封装，用于生成符合 Schema 约束的 Prompt"""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url or os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        if not self.api_key:
            raise ValueError("需要设置 ANTHROPIC_API_KEY 环境变量")
        self.client = Anthropic(api_key=self.api_key, base_url=self.base_url)

    def generate_shot_prompts(
        self,
        system_prompt: str,
        shot_context: str,
        model: str = "claude-3-5-sonnet-20241022"
    ) -> dict:
        """
        生成单镜的 image_prompt 和 video_prompt

        Args:
            system_prompt: 系统提示（含约束规则）
            shot_context: 镜头上下文（script/char/loc/emotion等）
            model: Claude 模型

        Returns:
            {"image_prompt": str, "video_prompt": str}
        """
        message = self.client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": shot_context
            }]
        )

        # 解析返回（假设格式：IMAGE: xxx\nVIDEO: xxx）
        text = message.content[0].text
        lines = text.strip().split("\n")
        result = {"image_prompt": "", "video_prompt": ""}

        for line in lines:
            if line.startswith("IMAGE:"):
                result["image_prompt"] = line.replace("IMAGE:", "").strip()
            elif line.startswith("VIDEO:"):
                result["video_prompt"] = line.replace("VIDEO:", "").strip()

        return result
