#!/usr/bin/env python3
"""导演审核 Agent"""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from adapters.base import AdapterRegistry
from config.prompts_registry import get_prompt

import json as _json
_config = _json.loads(
    pathlib.Path(__file__).parent.parent.joinpath("config/jike_config.json").read_text()
)


class DirectorAgent(BaseAgent):
    name = "director"

    def __init__(self):
        super().__init__()
        self.cfg = _config
        adapter_name = self.cfg.get("text_adapter", "qwen")
        model_cfg = self.cfg["models"].get(adapter_name, {})
        self.adapter = AdapterRegistry.get(adapter_name, model_cfg)

    def handle_action(self, action: str, params: dict) -> dict:
        if action == "review_outline":
            return self._review_outline(params.get("outline", {}))
        if action == "review_storyline":
            return self._review_storyline(params.get("storyline", {}))
        return {"error": f"Unknown action: {action}"}

    def _review_outline(self, outline: dict) -> dict:
        system_prompt = get_prompt("outline-director")
        user_prompt = (
            "请审核以下大纲：\n\n"
            + json.dumps(outline, ensure_ascii=False, indent=2)
        )

        result = self.adapter.invoke(
            prompt=system_prompt + "\n\n" + user_prompt,
            schema={
                "type": "object",
                "properties": {
                    "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
                    "scores": {
                        "type": "object",
                        "properties": {
                            "completeness": {"type": "number"},
                            "rhythm": {"type": "number"},
                            "character_motivation": {"type": "number"},
                            "visual_feasibility": {"type": "number"},
                            "emotional_curve": {"type": "number"},
                            "commercial_value": {"type": "number"},
                        },
                    },
                    "suggestions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["verdict", "scores", "suggestions"],
            },
        )

        return result


if __name__ == "__main__":
    DirectorAgent().run()
