#!/usr/bin/env python3
"""故事师 Agent"""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from adapters.base import AdapterRegistry
from config.prompts_registry import get_prompt, format_prompt

# 加载配置
import json as _json
_config = _json.loads(
    pathlib.Path(__file__).parent.parent.joinpath("config/jike_config.json").read_text()
)


class StorylineAgent(BaseAgent):
    name = "storyline"

    def __init__(self):
        super().__init__()
        self.cfg = _config
        adapter_name = self.cfg.get("text_adapter", "qwen")
        model_cfg = self.cfg["models"].get(adapter_name, {})
        self.adapter = AdapterRegistry.get(adapter_name, model_cfg)

    def handle_action(self, action: str, params: dict) -> dict:
        if action == "generate":
            return self._generate_storyline(
                params.get("script_text", ""),
                params.get("chapter_range", [1, 9999]),
            )
        return {"error": f"Unknown action: {action}"}

    def _generate_storyline(self, script_text: str, chapter_range: list[int]) -> dict:
        system_prompt = get_prompt("storyline-main")
        user_prompt = (
            f"请分析以下剧本（章节 {chapter_range[0]}-{chapter_range[1]}），"
            f"生成故事线：\n\n{script_text[:8000]}"
        )

        result = self.adapter.invoke(
            prompt=system_prompt + "\n\n" + user_prompt,
            schema={
                "type": "object",
                "properties": {
                    "story_arc": {"type": "string"},
                    "key_events": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "characters": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "scenes": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["story_arc", "key_events", "characters", "scenes"],
            },
        )

        self.add_history("user", script_text[:500])
        self.add_history("assistant", json.dumps(result, ensure_ascii=False))
        return result


if __name__ == "__main__":
    StorylineAgent().run()
