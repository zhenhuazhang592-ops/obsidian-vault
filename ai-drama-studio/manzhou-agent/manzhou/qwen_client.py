"""Qwen API 客户端 — 用于生成分镜 Prompt"""

import os
import json
import re
from openai import OpenAI

from .schema import ShotScript
from .prompt_builder import PromptBuilder


class QwenClient:
    """Qwen3-Max API 封装，用于生成符合 Schema 约束的 Prompt"""

    def __init__(self, api_key: str = None, model: str = "qwen-max"):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("需要设置 DASHSCOPE_API_KEY 环境变量")
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        self.model = model

    def generate_shot_prompts(
        self,
        system_prompt: str,
        shot_context: str,
    ) -> dict:
        """
        生成单镜的 image_prompt 和 video_prompt

        Args:
            system_prompt: 系统提示（含约束规则）
            shot_context: 镜头上下文

        Returns:
            {"image_prompt": str, "video_prompt": str}
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": shot_context},
            ],
            max_tokens=1024,
            temperature=0.7,
        )

        text = response.choices[0].message.content

        # 尝试 JSON 解析
        result = self._parse_response(text)
        return result

    def _parse_response(self, text: str) -> dict:
        """解析模型返回，优先 JSON，其次结构化文本"""
        result = {"image_prompt": "", "video_prompt": ""}

        # 1. 尝试 JSON 解析（找 ```json 包裹的内容）
        import re as _re
        json_match = _re.search(r'```json\s*(\{.*?\})\s*```', text, _re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                if "image_prompt" in data and "video_prompt" in data:
                    return data
            except json.JSONDecodeError:
                pass

        # 2. 按行解析 IMAGE: / VIDEO: / IMAGE_URL: / VIDEO_URL: 格式
        lines = text.split("\n")
        capture_key = None
        for line in lines:
            line = line.strip()
            # 去掉可能的 ** 包裹
            line = _re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
            if _re.match(r'^(IMAGE|VIDEO)[\s:](.*)', line):
                m = _re.match(r'^(IMAGE|VIDEO)[\s:]+(.*)', line)
                capture_key = "image_prompt" if m.group(1) == "IMAGE" else "video_prompt"
                result[capture_key] = m.group(2).strip()
            elif capture_key and line and not line.startswith("{"):
                # 续接上一行（多行内容）
                if _re.match(r'^[^\s【\[\(（]', line) or line.startswith("画面") or line.startswith("视频"):
                    result[capture_key] += " " + line

        # 3. 清理 markdown 格式
        for key in result:
            result[key] = (
                result[key]
                .replace('```', '')
                .replace('`', '')
                .strip()
            )

        return result

    def batch_generate_episode_prompts(
        self,
        shots: list[ShotScript],
        prompt_builder: PromptBuilder,
    ) -> list[dict]:
        """
        批量生成整集所有镜头的 Prompt

        Args:
            shots: 分镜列表
            prompt_builder: Prompt构建器（已加载约束）

        Returns:
            [{"shot_id": "P01", "image_prompt": "...", "video_prompt": "...", "validation": {...}}, ...]
        """
        from .schema_validator import SchemaValidator

        results = []
        validator = SchemaValidator(
            prompt_builder.ip_profile,
            prompt_builder.step45_output
        )

        for shot in shots:
            # 构建上下文
            context = prompt_builder.build_shot_user_prompt(shot)
            system = prompt_builder.build_shot_system_prompt([shot])

            # 生成
            generated = self.generate_shot_prompts(system, context)

            # 克隆 shot 并填入生成的 Prompt
            filled_shot = ShotScript(
                shot_id=shot.shot_id,
                duration_sec=shot.duration_sec,
                location_id=shot.location_id,
                character_ids=shot.character_ids,
                script=shot.script,
                dialogue=shot.dialogue,
                image_prompt=generated.get("image_prompt", ""),
                video_prompt=generated.get("video_prompt", ""),
                emotion_level=shot.emotion_level,
                beat_position=shot.beat_position,
                shot_type=shot.shot_type,
                camera_action=shot.camera_action,
            )

            # Schema 校验
            validation = validator.validate_shot(filled_shot)

            results.append({
                "shot_id": shot.shot_id,
                "image_prompt": generated.get("image_prompt", ""),
                "video_prompt": generated.get("video_prompt", ""),
                "validation": {
                    "d1_score": validation.d1_score,
                    "d2_score": validation.d2_score,
                    "d3_score": validation.d3_score,
                    "is_passed": validation.is_passed,
                    "errors": [
                        {"field": e.field, "severity": e.severity, "msg": e.expected}
                        for e in validation.errors
                    ],
                },
            })

        return results
