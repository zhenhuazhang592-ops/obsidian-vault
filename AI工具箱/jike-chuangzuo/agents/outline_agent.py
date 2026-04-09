#!/usr/bin/env python3
"""大纲师 Agent"""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from adapters.base import AdapterRegistry
from config.prompts_registry import get_prompt

import json as _json
_config = _json.loads(
    pathlib.Path(__file__).parent.parent.joinpath("config/jike_config.json").read_text()
)


class OutlineAgent(BaseAgent):
    name = "outline"

    def __init__(self):
        super().__init__()
        self.cfg = _config
        adapter_name = self.cfg.get("text_adapter", "qwen")
        model_cfg = self.cfg["models"].get(adapter_name, {})
        self.adapter = AdapterRegistry.get(adapter_name, model_cfg)

    def handle_action(self, action: str, params: dict) -> dict:
        if action == "generate":
            return self._generate_outline(params.get("storyline", {}))
        return {"error": f"Unknown action: {action}"}

    def _generate_outline(self, storyline: dict) -> dict:
        system_prompt = get_prompt("outline-main")
        user_prompt = (
            get_prompt("outline-ai2").format(
                storyline=json.dumps(storyline, ensure_ascii=False)
            )
        )

        result = self.adapter.invoke(
            prompt=system_prompt + "\n\n" + user_prompt,
            schema={
                "type": "object",
                "properties": {
                    "episodeIndex": {"type": "integer"},
                    "title": {"type": "string"},
                    "chapterRange": {"type": "array", "items": {"type": "integer"}},
                    "characters": {"type": "array"},
                    "props": {"type": "array"},
                    "coreConflict": {"type": "string"},
                    "outline": {"type": "string"},
                    "openingHook": {"type": "string"},
                    "keyEvents": {"type": "array", "items": {"type": "string"}},
                    "emotionalCurve": {"type": "string"},
                    "visualHighlights": {"type": "array", "items": {"type": "string"}},
                    "endingHook": {"type": "string"},
                    "classicQuotes": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "episodeIndex", "title", "characters", "props",
                    "coreConflict", "outline",
                ],
            },
        )

        return result


if __name__ == "__main__":
    OutlineAgent().run()
