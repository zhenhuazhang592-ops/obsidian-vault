#!/usr/bin/env python3
"""分镜师 Agent —— 生成分镜提示词"""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from adapters.base import AdapterRegistry
from config.prompts_registry import get_prompt

import json as _json
_config = _json.loads(
    pathlib.Path(__file__).parent.parent.joinpath("config/jike_config.json").read_text()
)


class ShotAgent(BaseAgent):
    name = "shot"

    def __init__(self):
        super().__init__()
        self.cfg = _config
        adapter_name = self.cfg.get("text_adapter", "qwen")
        model_cfg = self.cfg["models"].get(adapter_name, {})
        self.adapter = AdapterRegistry.get(adapter_name, model_cfg)

    def handle_action(self, action: str, params: dict) -> dict:
        if action == "generate_shots":
            return self._generate_shots(
                params.get("segment", {}),
                params.get("assets", []),
            )
        return {"error": f"Unknown action: {action}"}

    def _generate_shots(self, segment: dict, assets: list[dict]) -> dict:
        system_prompt = get_prompt("storyboard-main")
        user_prompt = (
            get_prompt("storyboard-shot")
            + f"\n\n片段内容：\n{json.dumps(segment, ensure_ascii=False)}\n\n"
            + f"资产列表：\n{json.dumps(assets, ensure_ascii=False)}"
        )

        result = self.adapter.invoke(
            prompt=system_prompt + "\n\n" + user_prompt,
            schema={
                "type": "object",
                "properties": {
                    "shots": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "index": {"type": "integer"},
                                "title": {"type": "string"},
                                "fragment_content": {"type": "string"},
                                "prompt": {"type": "string"},
                                "motion_prompt": {"type": "string"},
                                "duration": {"type": "number"},
                                "assets_tags": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "type": {"type": "string"},
                                            "text": {"type": "string"},
                                        },
                                    },
                                },
                            },
                            "required": ["index", "title", "prompt"],
                        },
                    },
                },
                "required": ["shots"],
            },
        )

        return result


if __name__ == "__main__":
    ShotAgent().run()
