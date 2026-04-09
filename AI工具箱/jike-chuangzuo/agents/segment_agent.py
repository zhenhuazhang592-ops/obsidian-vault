#!/usr/bin/env python3
"""片段师 Agent —— 将剧本切割为叙事片段"""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from adapters.base import AdapterRegistry
from config.prompts_registry import get_prompt

import json as _json
_config = _json.loads(
    pathlib.Path(__file__).parent.parent.joinpath("config/jike_config.json").read_text()
)


class SegmentAgent(BaseAgent):
    name = "segment"

    def __init__(self):
        super().__init__()
        self.cfg = _config
        adapter_name = self.cfg.get("text_adapter", "qwen")
        model_cfg = self.cfg["models"].get(adapter_name, {})
        self.adapter = AdapterRegistry.get(adapter_name, model_cfg)

    def handle_action(self, action: str, params: dict) -> dict:
        if action == "segment":
            return self._segment_script(
                params.get("script", ""),
                params.get("num_segments", 4),
            )
        return {"error": f"Unknown action: {action}"}

    def _segment_script(self, script: str, num_segments: int = 4) -> dict:
        system_prompt = get_prompt("storyboard-main")
        user_prompt = (
            get_prompt("storyboard-segment")
            + f"\n\n请将以下剧本切割为 {num_segments} 个叙事片段：\n\n{script[:8000]}"
        )

        result = self.adapter.invoke(
            prompt=system_prompt + "\n\n" + user_prompt,
            schema={
                "type": "object",
                "properties": {
                    "segments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "index": {"type": "integer"},
                                "description": {"type": "string"},
                                "emotion": {"type": "string"},
                                "action": {"type": "string"},
                            },
                            "required": ["index", "description", "emotion"],
                        },
                    },
                },
                "required": ["segments"],
            },
        )

        return result


if __name__ == "__main__":
    SegmentAgent().run()
